/**
 * webview_firewall.js
 * 
 * Core Frida Module: Strict WebView Domain Whitelist Firewall.
 * Stage: Java (Dalvik/ART runtime)
 * 
 * Intercepts WebViewClient.shouldOverrideUrlLoading, validates destination URLs against
 * allowed_domains, and blocks unauthorized external URLs while displaying a native Toast.
 */

(function (root) {
    'use strict';

    const MODULE_NAME = 'webview_firewall';
    const DEFAULT_BLOCKED_MESSAGE = 'הגישה לקישור זה נחסמה';

    function setupWebViewFirewall(config, logger, safeUtils) {
        const allowedDomains = config.allowed_domains || /*__ALLOWED_DOMAINS__*/ [];
        const blockedMessage = config.blocked_message || /*__BLOCKED_MESSAGE__*/ DEFAULT_BLOCKED_MESSAGE;

        if (!allowedDomains || !allowedDomains.length) {
            logger.debug('No allowed_domains configured; WebView firewall passive.');
            return;
        }

        logger.info(`WebView Firewall active. Whitelisted domains: [${allowedDomains.join(', ')}]`);

        function isUrlAllowed(urlStr) {
            if (!urlStr) return true;
            try {
                const urlLower = urlStr.toLowerCase().trim();
                if (urlLower.startsWith('about:') || urlLower.startsWith('data:') || urlLower.startsWith('blob:') || urlLower.startsWith('file:')) {
                    return true;
                }

                const Uri = Java.use('android.net.Uri');
                const parsed = Uri.parse(urlStr);
                const host = parsed.getHost();
                if (!host) return true;

                const hostStr = host.toLowerCase().trim();
                for (let i = 0; i < allowedDomains.length; i++) {
                    const allowed = allowedDomains[i].toLowerCase().trim();
                    if (hostStr === allowed || hostStr.endsWith('.' + allowed)) {
                        return true;
                    }
                }
                return false;
            } catch (e) {
                logger.warn(`Error parsing URL '${urlStr}': ${e.message}`);
                return true;
            }
        }

        function showBlockedToast(context) {
            try {
                Java.scheduleOnMainThread(function () {
                    try {
                        const ActivityThread = Java.use('android.app.ActivityThread');
                        const Toast = Java.use('android.widget.Toast');
                        const StringCls = Java.use('java.lang.String');

                        const currentApp = ActivityThread.currentApplication();
                        const ctx = context || (currentApp ? currentApp.getApplicationContext() : null);

                        if (ctx) {
                            const msg = StringCls.$new(blockedMessage);
                            Toast.makeText(ctx, msg, Toast.LENGTH_SHORT.value).show();
                        }
                    } catch (_) {}
                });
            } catch (_) {}
        }

        safeUtils.safeJavaUse('android.webkit.WebViewClient', function (WebViewClient) {
            // Overload 1: shouldOverrideUrlLoading(WebView, String) (API < 24)
            try {
                WebViewClient.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'java.lang.String').implementation = function (view, url) {
                    if (!isUrlAllowed(url)) {
                        logger.warn(`Blocked navigation to unauthorized URL: ${url}`);
                        const ctx = view ? view.getContext() : null;
                        showBlockedToast(ctx);
                        return true;
                    }
                    return this.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'java.lang.String').call(this, view, url);
                };
            } catch (_) {}

            // Overload 2: shouldOverrideUrlLoading(WebView, WebResourceRequest) (API 24+)
            try {
                WebViewClient.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'android.webkit.WebResourceRequest').implementation = function (view, request) {
                    if (request !== null) {
                        const uri = request.getUrl();
                        const url = uri ? uri.toString() : null;
                        if (url && !isUrlAllowed(url)) {
                            logger.warn(`Blocked navigation to unauthorized URL: ${url}`);
                            const ctx = view ? view.getContext() : null;
                            showBlockedToast(ctx);
                            return true;
                        }
                    }
                    return this.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'android.webkit.WebResourceRequest').call(this, view, request);
                };
            } catch (_) {}

            logger.info('WebViewClient navigation interceptors hooked.');
        }, logger);
    }

    // --- MODULE DEFINITION ---
    const HookModule = {
        name: MODULE_NAME,
        description: 'Strict WebView Domain Whitelist Firewall',
        stage: 'java',
        defaultEnabled: false,

        initJava: function (config, context) {
            const logger = context.logger || console;
            const safeUtils = context.safeUtils;
            setupWebViewFirewall(config, logger, safeUtils);
        }
    };

    if (root.__FRIDA_CORE__) {
        root.__FRIDA_CORE__.register(HookModule);
    }

})(typeof globalThis !== 'undefined' ? globalThis : this);

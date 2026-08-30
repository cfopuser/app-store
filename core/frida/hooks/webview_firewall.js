/**
 * Strict WebView Domain Whitelist Firewall Hook Module
 * Intercepts WebViewClient navigation, validates destination URLs against allowed_domains,
 * and blocks unauthorized external URLs while displaying a native Toast.
 */

Java.perform(function () {
    console.log("[*] [Frida] Injecting WebView Domain Firewall...");

    var ALLOWED_DOMAINS = /*__ALLOWED_DOMAINS__*/ [];
    var BLOCKED_MESSAGE = /*__BLOCKED_MESSAGE__*/ "הגישה לקישור זה נחסמה";

    if (!ALLOWED_DOMAINS || ALLOWED_DOMAINS.length === 0) {
        console.log("[i] [Frida] No WebView allowed_domains configured. Firewall passive.");
        return;
    }

    console.log("[+] [Frida] WebView Firewall active. Allowed domains: " + JSON.stringify(ALLOWED_DOMAINS));

    function isUrlAllowed(urlStr) {
        if (!urlStr) return true;
        try {
            var urlLower = urlStr.toLowerCase().trim();
            if (urlLower.startsWith("about:") || urlLower.startsWith("data:") || urlLower.startsWith("blob:") || urlLower.startsWith("file:")) {
                return true;
            }

            var Uri = Java.use('android.net.Uri');
            var parsed = Uri.parse(urlStr);
            var host = parsed.getHost();
            if (!host) return true;

            var hostStr = host.toLowerCase().trim();

            for (var i = 0; i < ALLOWED_DOMAINS.length; i++) {
                var allowed = ALLOWED_DOMAINS[i].toLowerCase().trim();
                if (hostStr === allowed || hostStr.endsWith("." + allowed)) {
                    return true;
                }
            }

            return false;
        } catch (e) {
            console.log("[-] [Frida] Error parsing URL in firewall: " + e);
            return true;
        }
    }

    function showBlockedToast(context) {
        try {
            var ActivityThread = Java.use('android.app.ActivityThread');
            var Handler = Java.use('android.os.Handler');
            var Looper = Java.use('android.os.Looper');
            var Toast = Java.use('android.widget.Toast');
            var StringCls = Java.use('java.lang.String');

            var currentApp = ActivityThread.currentApplication();
            var ctx = context || currentApp.getApplicationContext();

            if (ctx) {
                var mainHandler = Handler.$new(Looper.getMainLooper());
                var Runnable = Java.registerClass({
                    name: 'com.frida.ToastRunnable' + Math.floor(Math.random() * 100000),
                    implements: [Java.use('java.lang.Runnable')],
                    methods: {
                        run: function () {
                            try {
                                var msg = StringCls.$new(BLOCKED_MESSAGE);
                                Toast.makeText(ctx, msg, Toast.LENGTH_SHORT.value).show();
                            } catch (tErr) {}
                        }
                    }
                });
                mainHandler.post(Runnable.$new());
            }
        } catch (e) {
            console.log("[-] [Frida] Could not display blocked toast: " + e);
        }
    }

    try {
        var WebViewClient = Java.use('android.webkit.WebViewClient');

        // Overload 1: shouldOverrideUrlLoading(WebView, String) (Deprecated in API 24)
        try {
            WebViewClient.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'java.lang.String').implementation = function (view, url) {
                if (!isUrlAllowed(url)) {
                    console.log("[!] [Frida] Blocked navigation to URL: " + url);
                    var ctx = view ? view.getContext() : null;
                    showBlockedToast(ctx);
                    return true; // Cancel navigation
                }
                return this.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'java.lang.String').call(this, view, url);
            };
            console.log("[+] [Frida] WebViewClient.shouldOverrideUrlLoading(WebView, String) hooked");
        } catch (e1) {}

        // Overload 2: shouldOverrideUrlLoading(WebView, WebResourceRequest) (API 24+)
        try {
            WebViewClient.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'android.webkit.WebResourceRequest').implementation = function (view, request) {
                if (request !== null) {
                    var uri = request.getUrl();
                    var url = uri ? uri.toString() : null;
                    if (url && !isUrlAllowed(url)) {
                        console.log("[!] [Frida] Blocked navigation to URL: " + url);
                        var ctx = view ? view.getContext() : null;
                        showBlockedToast(ctx);
                        return true; // Cancel navigation
                    }
                }
                return this.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'android.webkit.WebResourceRequest').call(this, view, request);
            };
            console.log("[+] [Frida] WebViewClient.shouldOverrideUrlLoading(WebView, WebResourceRequest) hooked");
        } catch (e2) {}

    } catch (e) {}
});

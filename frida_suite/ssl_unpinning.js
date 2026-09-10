/**
 * ssl_unpinning.js
 * 
 * Production-grade Universal SSL / TLS Pinning Bypass for Android.
 * Covers:
 * 1. Java TrustManager & SSLContext (OpenSSL, Conscrypt, TrustManagerImpl)
 * 2. Network Security Config (NSC) (Android 7.0+ / API 24+)
 * 3. Third-party HTTP libraries: OkHttp v3/v4, Apache HttpClient, Volley, Retrofit, Cronet
 * 4. Native BoringSSL / OpenSSL hooks (libssl.so, libcrypto.so)
 */

(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.SslUnpinning = factory();
    }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    const MODULE_NAME = 'SslUnpinning';

    function bypassJavaSsl(logger) {
        // 1. In-Memory Universal TrustManager
        try {
            const X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
            const SSLContext = Java.use('javax.net.ssl.SSLContext');

            const TrustAllManager = Java.registerClass({
                name: 're.frida.bypass.TrustAllManager',
                implements: [X509TrustManager],
                methods: {
                    checkClientTrusted: function (chain, authType) {},
                    checkServerTrusted: function (chain, authType) {},
                    getAcceptedIssuers: function () {
                        return [];
                    }
                }
            });

            const TrustManagers = [TrustAllManager.$new()];

            // SSLContext.init(KeyManager[], TrustManager[], SecureRandom)
            const sslContextInit = SSLContext.init;
            SSLContext.init.overload(
                '[Ljavax.net.ssl.KeyManager;',
                '[Ljavax.net.ssl.TrustManager;',
                'java.security.SecureRandom'
            ).implementation = function (keyManager, trustManager, secureRandom) {
                logger.debug('[SSLContext.init] Overriding TrustManagers with TrustAllManager');
                sslContextInit.call(this, keyManager, TrustManagers, secureRandom);
            };
            logger.debug('Hooked SSLContext.init');
        } catch (e) {
            logger.debug(`SSLContext.init hook skipped: ${e.message}`);
        }

        // 2. TrustManagerImpl (AOSP & Conscrypt)
        try {
            const TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
            
            // List<X509Certificate> checkTrustedRecursive(X509Certificate[] certs, ...)
            try {
                TrustManagerImpl.checkTrustedRecursive.implementation = function (certs, host, clientAuth, untrustedChain, trustedChain, hostName) {
                    logger.debug(`[TrustManagerImpl.checkTrustedRecursive] Bypassed for host: ${host}`);
                    const ArrayList = Java.use('java.util.ArrayList');
                    return ArrayList.$new();
                };
            } catch (_) {}

            try {
                TrustManagerImpl.checkServerTrusted.overload(
                    '[Ljava.security.cert.X509Certificate;',
                    'java.lang.String',
                    'java.lang.String'
                ).implementation = function (certs, authType, host) {
                    logger.debug(`[TrustManagerImpl.checkServerTrusted] Bypassed for host: ${host}`);
                    const ArrayList = Java.use('java.util.ArrayList');
                    return ArrayList.$new();
                };
            } catch (_) {}

            try {
                TrustManagerImpl.checkServerTrusted.overload(
                    '[Ljava.security.cert.X509Certificate;',
                    'java.lang.String'
                ).implementation = function (certs, authType) {
                    logger.debug('[TrustManagerImpl.checkServerTrusted] Bypassed');
                };
            } catch (_) {}
            logger.debug('Hooked com.android.org.conscrypt.TrustManagerImpl');
        } catch (e) {
            logger.debug(`TrustManagerImpl hook skipped: ${e.message}`);
        }

        // 3. Android Network Security Configuration (API 24+)
        try {
            const NetworkSecurityTrustManager = Java.use('android.security.net.config.NetworkSecurityTrustManager');
            try {
                NetworkSecurityTrustManager.checkPins.implementation = function (pins) {
                    logger.debug('[NetworkSecurityTrustManager.checkPins] Bypassed pin check');
                };
            } catch (_) {}
            logger.debug('Hooked NetworkSecurityTrustManager');
        } catch (e) {
            logger.debug(`NetworkSecurityTrustManager hook skipped: ${e.message}`);
        }

        // 4. OkHttp v3 and v4 CertificatePinner
        const okHttpPinners = [
            'okhttp3.CertificatePinner',
            'com.squareup.okhttp.CertificatePinner'
        ];
        okHttpPinners.forEach(className => {
            try {
                const Pinner = Java.use(className);

                // OkHttp 3 / standard Java check
                try {
                    Pinner.check.overload('java.lang.String', 'java.util.List').implementation = function (hostname, peerCertificates) {
                        logger.debug(`[${className}.check(String, List)] Suppressed pinning for: ${hostname}`);
                    };
                } catch (_) {}

                // OkHttp 4 Kotlin bytecode check$okhttp
                try {
                    Pinner['check$okhttp'].implementation = function (hostname, peerCertificates) {
                        logger.debug(`[${className}.check$okhttp] Suppressed pinning for: ${hostname}`);
                    };
                } catch (_) {}

                // CertificatePinner.check(String, Certificate[])
                try {
                    Pinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function (hostname, peerCertificates) {
                        logger.debug(`[${className}.check(String, Cert[])] Suppressed pinning for: ${hostname}`);
                    };
                } catch (_) {}
                logger.info(`Hooked ${className}`);
            } catch (_) {}
        });

        // 5. Apache HttpClient & AndroidHttpClient
        try {
            const AbstractVerifier = Java.use('org.apache.http.conn.ssl.AbstractVerifier');
            AbstractVerifier.verify.overload('java.lang.String', '[Ljava.lang.String;', '[Ljava.lang.String;', 'boolean').implementation = function () {
                logger.debug('[Apache.AbstractVerifier] Hostname verification bypassed');
            };
        } catch (_) {}

        // 6. Cronet engine pinning
        try {
            // CronetUrlRequest / Cronet Engine
            const CronetEngine = Java.use('org.chromium.net.CronetEngine$Builder');
            if (CronetEngine.enablePublicKeyPinningBypassForLocalTrustAnchors) {
                CronetEngine.enablePublicKeyPinningBypassForLocalTrustAnchors.implementation = function (val) {
                    return this.enablePublicKeyPinningBypassForLocalTrustAnchors(true);
                };
            }
        } catch (_) {}

        // 7. Dynamic fallback on SSLPeerUnverifiedException
        try {
            const SSLPeerUnverifiedException = Java.use('javax.net.ssl.SSLPeerUnverifiedException');
            SSLPeerUnverifiedException.$init.overload('java.lang.String').implementation = function (str) {
                logger.debug(`[SSLPeerUnverifiedException] Dynamic capture: ${str}`);
                return this.$init(str);
            };
        } catch (_) {}
    }

    function bypassNativeSsl(logger) {
        // Native hooks for libssl.so and libcrypto.so (BoringSSL / OpenSSL)
        const sslLibs = ['libssl.so', 'libcrypto.so', 'libboringssl.so'];
        let hookedNative = false;

        sslLibs.forEach(libName => {
            const mod = Process.findModuleByName(libName);
            if (!mod) return;

            // 1. SSL_CTX_set_custom_verify(SSL_CTX *ctx, int mode, ssl_custom_verify_result_t (*callback)(SSL *ssl, uint8_t *out_alert))
            const setCustomVerifyPtr = Module.findExportByName(libName, 'SSL_CTX_set_custom_verify');
            if (setCustomVerifyPtr) {
                try {
                    Interceptor.attach(setCustomVerifyPtr, {
                        onEnter: function (args) {
                            logger.debug(`[${libName}!SSL_CTX_set_custom_verify] Neutralizing custom verify callback`);
                            // Replace custom callback with NULL (ptr(0)) so BoringSSL uses standard or no verify
                            args[2] = ptr(0);
                        }
                    });
                    hookedNative = true;
                } catch (e) {
                    logger.debug(`Failed hooking SSL_CTX_set_custom_verify in ${libName}: ${e.message}`);
                }
            }

            // 2. SSL_set_custom_verify
            const sslSetCustomVerify = Module.findExportByName(libName, 'SSL_set_custom_verify');
            if (sslSetCustomVerify) {
                try {
                    Interceptor.attach(sslSetCustomVerify, {
                        onEnter: function (args) {
                            logger.debug(`[${libName}!SSL_set_custom_verify] Neutralizing custom verify callback`);
                            args[2] = ptr(0);
                        }
                    });
                    hookedNative = true;
                } catch (e) {
                    logger.debug(`Failed hooking SSL_set_custom_verify in ${libName}: ${e.message}`);
                }
            }

            // 3. SSL_get_verify_result(const SSL *ssl) -> X509_V_OK (0)
            const getVerifyResult = Module.findExportByName(libName, 'SSL_get_verify_result');
            if (getVerifyResult) {
                try {
                    Interceptor.attach(getVerifyResult, {
                        onLeave: function (retval) {
                            if (!retval.isNull()) {
                                logger.debug(`[${libName}!SSL_get_verify_result] Overriding verify result to X509_V_OK (0)`);
                                retval.replace(ptr(0));
                            }
                        }
                    });
                    hookedNative = true;
                } catch (e) {
                    logger.debug(`Failed hooking SSL_get_verify_result in ${libName}: ${e.message}`);
                }
            }
        });

        if (hookedNative) {
            logger.info('Native BoringSSL / OpenSSL unpinning hooks active.');
        }
    }

    return {
        name: MODULE_NAME,
        init: function (options, logger) {
            options = options || {};
            logger = logger || console;

            logger.info(`[${MODULE_NAME}] Initializing Universal SSL Unpinning...`);

            // Native hooks
            try {
                bypassNativeSsl(logger);
            } catch (e) {
                logger.error(`[${MODULE_NAME}] Native SSL unpinning error: ${e.message}`);
            }

            // Java hooks
            if (typeof Java !== 'undefined' && Java.available) {
                const runner = function () {
                    try {
                        bypassJavaSsl(logger);
                        logger.info(`[${MODULE_NAME}] Java SSL unpinning successfully deployed.`);
                    } catch (err) {
                        logger.error(`[${MODULE_NAME}] Java SSL unpinning failed: ${err.message}`);
                    }
                };

                if (Java.performWhenReady) {
                    Java.performWhenReady(runner);
                } else {
                    Java.perform(runner);
                }
            } else {
                logger.debug(`[${MODULE_NAME}] Java runtime not yet ready; polling...`);
                const interval = setInterval(function () {
                    if (typeof Java !== 'undefined' && Java.available) {
                        clearInterval(interval);
                        Java.perform(function () {
                            bypassJavaSsl(logger);
                            logger.info(`[${MODULE_NAME}] Java SSL unpinning deployed after delay.`);
                        });
                    }
                }, 50);
            }
        }
    };
});

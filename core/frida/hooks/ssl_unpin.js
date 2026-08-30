/**
 * Universal SSL Unpinning Hook Module
 * Sourced & expanded from HTTP Toolkit / Tim Perry & Objection community unpinning scripts.
 * Gracefully attempts hooks in individual try-catch blocks.
 */

Java.perform(function () {
    console.log("[*] [Frida] Injecting Universal SSL Unpinning...");

    // 1. Android TrustManagerImpl (Android 7.0+)
    try {
        var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.checkTrustedRecursive.implementation = function (certs, host, clientAuth, untrustedChain, trustAnchorChain, used) {
            var ArrayList = Java.use('java.util.ArrayList');
            return ArrayList.$new();
        };
        console.log("[+] [Frida] TrustManagerImpl.checkTrustedRecursive bypassed");
    } catch (e) {
        // Fallback or not present
    }

    try {
        var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String', 'java.lang.String').implementation = function (certs, authType, host) {
            var ArrayList = Java.use('java.util.ArrayList');
            return ArrayList.$new();
        };
        console.log("[+] [Frida] TrustManagerImpl.checkServerTrusted (3 args) bypassed");
    } catch (e) {
    }

    // 2. OkHttp 3 & 4 CertificatePinner
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        
        try {
            CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function (hostname, peerCertificates) {
                return;
            };
            console.log("[+] [Frida] OkHttp3 CertificatePinner.check(String, List) bypassed");
        } catch (err) {}

        try {
            CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function (hostname, peerCertificates) {
                return;
            };
            console.log("[+] [Frida] OkHttp3 CertificatePinner.check(String, Certificate[]) bypassed");
        } catch (err) {}

        try {
            CertificatePinner['check$okhttp'].implementation = function (hostname, cleanListFn) {
                return;
            };
            console.log("[+] [Frida] OkHttp4 CertificatePinner.check$okhttp bypassed");
        } catch (err) {}

    } catch (e) {
    }

    // 3. Conscrypt verifyChain & Platform
    try {
        var ConscryptPlatform = Java.use('com.android.org.conscrypt.Platform');
        ConscryptPlatform.checkServerTrusted.overload('javax.net.ssl.X509TrustManager', '[Ljava.security.cert.X509Certificate;', 'java.lang.String', 'com.android.org.conscrypt.OpenSSLSocketImpl').implementation = function (tm, chain, authType, socket) {
            return;
        };
        console.log("[+] [Frida] Conscrypt Platform.checkServerTrusted bypassed");
    } catch (e) {
    }

    try {
        var ConscryptEngine = Java.use('org.conscrypt.ConscryptEngine');
        ConscryptEngine.verifyCertificateChain.implementation = function () {
            return;
        };
    } catch (e) {}

    // 4. TrustKit
    try {
        var TrustKit = Java.use('com.datatheorem.android.trustkit.pinning.OkHostnameVerifier');
        TrustKit.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function (host, session) {
            return true;
        };
        console.log("[+] [Frida] TrustKit OkHostnameVerifier bypassed");
    } catch (e) {}

    try {
        var PinningTrustManager = Java.use('com.datatheorem.android.trustkit.pinning.PinningTrustManager');
        PinningTrustManager.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = function (chain, authType) {
            return;
        };
        console.log("[+] [Frida] TrustKit PinningTrustManager bypassed");
    } catch (e) {}

    // 5. OpenSSLSocketImpl
    try {
        var OpenSSLSocketImpl = Java.use('com.android.org.conscrypt.OpenSSLSocketImpl');
        OpenSSLSocketImpl.verifyCertificateChain.implementation = function (certRefs, authMethod) {
            return;
        };
    } catch (e) {}

    // 6. NetworkSecurityTrustManager
    try {
        var NetworkSecurityTrustManager = Java.use('android.security.net.config.NetworkSecurityTrustManager');
        NetworkSecurityTrustManager.checkPins.implementation = function (chain) {
            return;
        };
        console.log("[+] [Frida] NetworkSecurityTrustManager.checkPins bypassed");
    } catch (e) {}

    // 7. WebView SSL Error auto-proceed
    try {
        var WebViewClient = Java.use('android.webkit.WebViewClient');
        WebViewClient.onReceivedSslError.implementation = function (view, handler, error) {
            handler.proceed();
        };
        console.log("[+] [Frida] WebViewClient.onReceivedSslError auto-proceed enabled");
    } catch (e) {}

    // 8. Universal X509TrustManager checkServerTrusted override
    try {
        var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        if (X509TrustManager.checkServerTrusted) {
            try {
                X509TrustManager.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = function (chain, authType) {
                    return;
                };
            } catch (xErr) {}
        }
    } catch (e) {}
});


/**
 * Dynamic Signature Spoofing Hook Module
 * Sourced & adapted from lemon4ex/frida-signature-bypass.
 * Intercepts PackageManager.getPackageInfo and spoofs signatures / SigningInfo.
 */

Java.perform(function () {
    console.log("[*] [Frida] Injecting Dynamic Signature Spoofing...");

    var GET_SIGNATURES = 0x00000040;
    var GET_SIGNING_CERTIFICATES = 0x08000000;

    // Optional config injected by builder.py
    var ORIGINAL_SIG_HEX = /*__ORIGINAL_SIGNATURE_HEX__*/ null;
    var ORIGINAL_SIG_BASE64 = /*__ORIGINAL_SIGNATURE_BASE64__*/ null;

    function createMockSignature() {
        var Signature = Java.use('android.content.pm.Signature');
        if (ORIGINAL_SIG_HEX) {
            return Signature.$new(ORIGINAL_SIG_HEX);
        } else if (ORIGINAL_SIG_BASE64) {
            var Base64 = Java.use('android.util.Base64');
            var bytes = Base64.decode(ORIGINAL_SIG_BASE64, 0);
            return Signature.$new(bytes);
        }
        return null;
    }

    // Hook SigningInfo class methods directly if present (API 28+)
    try {
        var SigningInfo = Java.use('android.content.pm.SigningInfo');
        var mockSig = createMockSignature();
        if (mockSig !== null) {
            var sigArray = Java.array('android.content.pm.Signature', [mockSig]);
            try {
                SigningInfo.getApkContentsSigners.implementation = function () {
                    return sigArray;
                };
            } catch (sErr1) {}
            try {
                SigningInfo.getSigningCertificateHistory.implementation = function () {
                    return sigArray;
                };
            } catch (sErr2) {}
            console.log("[+] [Frida] SigningInfo getters hooked with mock certificate");
        }
    } catch (siErr) {}

    try {
        var AppPkgMgr = Java.use('android.app.ApplicationPackageManager');

        // Overload 1: getPackageInfo(String, int)
        try {
            AppPkgMgr.getPackageInfo.overload('java.lang.String', 'int').implementation = function (pkgName, flags) {
                var pkgInfo = this.getPackageInfo.overload('java.lang.String', 'int').call(this, pkgName, flags);
                if (pkgInfo !== null) {
                    var mockSig = createMockSignature();
                    if (mockSig !== null) {
                        var sigArray = Java.array('android.content.pm.Signature', [mockSig]);
                        if ((flags & GET_SIGNATURES) !== 0 || pkgInfo.signatures.value !== null) {
                            pkgInfo.signatures.value = sigArray;
                        }
                    }
                }
                return pkgInfo;
            };
            console.log("[+] [Frida] ApplicationPackageManager.getPackageInfo(String, int) signature spoof active");
        } catch (e1) {}

        // Overload 2: getPackageInfo(String, PackageInfoFlags) (API 33+)
        try {
            var PackageInfoFlags = Java.use('android.content.pm.PackageManager$PackageInfoFlags');
            AppPkgMgr.getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').implementation = function (pkgName, flagsObj) {
                var pkgInfo = this.getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').call(this, pkgName, flagsObj);
                if (pkgInfo !== null) {
                    var mockSig = createMockSignature();
                    if (mockSig !== null) {
                        var sigArray = Java.array('android.content.pm.Signature', [mockSig]);
                        if (pkgInfo.signatures.value !== null) {
                            pkgInfo.signatures.value = sigArray;
                        }
                    }
                }
                return pkgInfo;
            };
        } catch (e2) {}

    } catch (e) {}
});

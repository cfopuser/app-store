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

    try {
        var AppPkgMgr = Java.use('android.app.ApplicationPackageManager');

        // Overload 1: getPackageInfo(String, int)
        try {
            AppPkgMgr.getPackageInfo.overload('java.lang.String', 'int').implementation = function (pkgName, flags) {
                var pkgInfo = this.getPackageInfo.overload('java.lang.String', 'int').call(this, pkgName, flags);
                if (pkgInfo !== null && ((flags & GET_SIGNATURES) !== 0 || (flags & GET_SIGNING_CERTIFICATES) !== 0)) {
                    var mockSig = createMockSignature();
                    if (mockSig !== null) {
                        var sigArray = Java.array('android.content.pm.Signature', [mockSig]);
                        if ((flags & GET_SIGNATURES) !== 0) {
                            pkgInfo.signatures.value = sigArray;
                        }
                        if ((flags & GET_SIGNING_CERTIFICATES) !== 0 && pkgInfo.signingInfo.value !== null) {
                            try {
                                var SigningInfo = Java.use('android.content.pm.SigningInfo');
                                var signingInfo = pkgInfo.signingInfo.value;
                                signingInfo.getApkContentsSigners.implementation = function () {
                                    return sigArray;
                                };
                                signingInfo.getSigningCertificateHistory.implementation = function () {
                                    return sigArray;
                                };
                            } catch (sErr) {}
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

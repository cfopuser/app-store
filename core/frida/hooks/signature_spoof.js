/**
 * signature_spoof.js
 * 
 * Core Frida Module: Dynamic APK Signature Certificate Spoofing.
 * Stage: Java (Dalvik/ART runtime)
 * 
 * Intercepts ApplicationPackageManager.getPackageInfo (both int flags and PackageInfoFlags)
 * and SigningInfo getters to return the target app's original signature bytes.
 */

(function (root) {
    'use strict';

    const MODULE_NAME = 'signature_spoof';

    const GET_SIGNATURES = 0x00000040;
    const GET_SIGNING_CERTIFICATES = 0x08000000;

    function createMockSignature(config) {
        try {
            const sigHex = config.original_signature_hex || config.signature_hex || /*__ORIGINAL_SIGNATURE_HEX__*/ null;
            const sigB64 = config.original_signature_base64 || config.signature_base64 || /*__ORIGINAL_SIGNATURE_BASE64__*/ null;

            const Signature = Java.use('android.content.pm.Signature');
            if (sigHex) {
                return Signature.$new(sigHex);
            } else if (sigB64) {
                const Base64 = Java.use('android.util.Base64');
                const bytes = Base64.decode(sigB64, 0);
                return Signature.$new(bytes);
            }
        } catch (_) {}
        return null;
    }

    function setupSignatureSpoof(config, logger, safeUtils) {
        const mockSig = createMockSignature(config);
        if (!mockSig) {
            logger.debug('No original signature provided; signature spoofing passive.');
            return;
        }

        const sigArray = Java.array('android.content.pm.Signature', [mockSig]);

        // 1. Hook SigningInfo class methods directly if present (API 28+)
        safeUtils.safeJavaUse('android.content.pm.SigningInfo', function (SigningInfo) {
            try {
                SigningInfo.getApkContentsSigners.implementation = function () {
                    return sigArray;
                };
            } catch (_) {}
            try {
                SigningInfo.getSigningCertificateHistory.implementation = function () {
                    return sigArray;
                };
            } catch (_) {}
            logger.debug('SigningInfo getters hooked with mock certificate');
        }, logger);

        // 2. Hook ApplicationPackageManager.getPackageInfo
        safeUtils.safeJavaUse('android.app.ApplicationPackageManager', function (AppPkgMgr) {
            // Overload 1: getPackageInfo(String, int)
            try {
                AppPkgMgr.getPackageInfo.overload('java.lang.String', 'int').implementation = function (pkgName, flags) {
                    const pkgInfo = this.getPackageInfo.overload('java.lang.String', 'int').call(this, pkgName, flags);
                    if (pkgInfo !== null) {
                        if ((flags & GET_SIGNATURES) !== 0 || pkgInfo.signatures.value !== null) {
                            pkgInfo.signatures.value = sigArray;
                        }
                    }
                    return pkgInfo;
                };
            } catch (_) {}

            // Overload 2: getPackageInfo(String, PackageInfoFlags) (API 33+)
            try {
                const PackageInfoFlags = Java.use('android.content.pm.PackageManager$PackageInfoFlags');
                AppPkgMgr.getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').implementation = function (pkgName, flagsObj) {
                    const pkgInfo = this.getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').call(this, pkgName, flagsObj);
                    if (pkgInfo !== null && pkgInfo.signatures.value !== null) {
                        pkgInfo.signatures.value = sigArray;
                    }
                    return pkgInfo;
                };
            } catch (_) {}

            logger.info('ApplicationPackageManager signature spoofing active.');
        }, logger);
    }

    // --- MODULE DEFINITION ---
    const HookModule = {
        name: MODULE_NAME,
        description: 'Dynamic APK Signature Certificate Spoofing',
        stage: 'java',
        defaultEnabled: true,

        initJava: function (config, context) {
            const logger = context.logger || console;
            const safeUtils = context.safeUtils;
            setupSignatureSpoof(config, logger, safeUtils);
        }
    };

    if (root.__FRIDA_CORE__) {
        root.__FRIDA_CORE__.register(HookModule);
    }

})(typeof globalThis !== 'undefined' ? globalThis : this);

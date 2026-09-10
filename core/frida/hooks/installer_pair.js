/**
 * installer_pair.js
 * 
 * Core Frida Module: Google Play Installer Spoofing & PAIR License Bypass.
 * Stage: Java (Dalvik/ART runtime)
 * 
 * Incorporates:
 * - ApplicationPackageManager.getInstallerPackageName -> com.android.vending
 * - PackageManager.getInstallSourceInfo (API 30+) getters spoofing
 * - PAIR IP SignatureCheck & LicenseClient bypass (pairipfix)
 * - PAIR IP LicenseActivity suppression
 * - Kotlin ArraysKt & CollectionsKt installer array bypass
 */

(function (root) {
    'use strict';

    const MODULE_NAME = 'installer_pair';
    const DEFAULT_PLAY_STORE_PKG = 'com.android.vending';

    function setupInstallerSpoofing(pkgName, logger, safeUtils) {
        // 1. ApplicationPackageManager.getInstallerPackageName
        safeUtils.safeJavaUse('android.app.ApplicationPackageManager', function (AppPkgMgr) {
            try {
                AppPkgMgr.getInstallerPackageName.overload('java.lang.String').implementation = function () {
                    return pkgName;
                };
                logger.debug(`ApplicationPackageManager.getInstallerPackageName hooked -> ${pkgName}`);
            } catch (_) {}
        }, logger);

        // 2. InstallSourceInfo (Android 11+ / API 30+)
        safeUtils.safeJavaUse('android.content.pm.InstallSourceInfo', function (InstallSourceInfo) {
            try {
                InstallSourceInfo.getInstallingPackageName.implementation = function () { return pkgName; };
            } catch (_) {}
            try {
                InstallSourceInfo.getInitiatingPackageName.implementation = function () { return pkgName; };
            } catch (_) {}
            try {
                InstallSourceInfo.getOriginatingPackageName.implementation = function () { return pkgName; };
            } catch (_) {}
            logger.debug(`InstallSourceInfo getters hooked -> ${pkgName}`);
        }, logger);
    }

    function setupPairIpBypass(logger, safeUtils) {
        // 1. PAIR IP SignatureCheck
        safeUtils.safeJavaUse('com.pairip.SignatureCheck', function (SigCheck) {
            try {
                SigCheck.verifyIntegrity.overload('android.content.Context').implementation = function () {
                    logger.debug('PAIR SignatureCheck.verifyIntegrity bypassed');
                };
            } catch (_) {}
            try {
                SigCheck.verifySignatureMatches.overload('java.lang.String').implementation = function () {
                    return true;
                };
            } catch (_) {}
        }, logger);

        // 2. PAIR IP LicenseClient
        safeUtils.safeJavaUse('com.pairip.licensecheck.LicenseClient', function (LicenseClient) {
            try { LicenseClient.initializeLicenseCheck.implementation = function () {}; } catch (_) {}
            try { LicenseClient.performLocalInstallerCheck.implementation = function () { return true; }; } catch (_) {}

            try {
                const CheckState = Java.use('com.pairip.licensecheck.LicenseClient$LicenseCheckState');
                if (CheckState.FULL_CHECK_OK) {
                    LicenseClient.licenseCheckState.value = CheckState.FULL_CHECK_OK.value;
                }
            } catch (_) {}

            try {
                LicenseClient.checkLicense.overload('android.content.Context').implementation = function () {};
            } catch (_) {}

            try {
                LicenseClient.checkLicense.overload(
                    'android.content.Context', 'com.pairip.licensecheck.LicenseClient$LicenseListener'
                ).implementation = function (ctx, listener) {
                    if (listener) {
                        try { listener.onLicenseValid(); } catch (_) {}
                    }
                };
            } catch (_) {}

            try { LicenseClient.startPaywallActivity.implementation = function () {}; } catch (_) {}
            try { LicenseClient.startErrorDialogActivity.implementation = function () {}; } catch (_) {}
        }, logger);

        // 3. LicenseClientV3
        safeUtils.safeJavaUse('com.pairip.licensecheck3.LicenseClientV3', function (LicenseClientV3) {
            try {
                LicenseClientV3.processResponse.overload('int', 'android.os.Bundle').implementation = function () {};
            } catch (_) {}
        }, logger);

        // 4. LicenseActivity suppression
        safeUtils.safeJavaUse('com.pairip.licensecheck.LicenseActivity', function (LicenseActivity) {
            ['closeApp', 'exitApp', 'showErrorDialog', 'showPaywallAndCloseApp'].forEach(method => {
                try {
                    if (LicenseActivity[method]) {
                        LicenseActivity[method].implementation = function () {
                            try { this.finish(); } catch (_) {}
                        };
                    }
                } catch (_) {}
            });

            ['onCreate', 'onStart', 'onResume'].forEach(method => {
                try {
                    LicenseActivity[method].implementation = function () {
                        try { this.finish(); } catch (_) {}
                    };
                } catch (_) {}
            });
        }, logger);

        // 5. Response Validators
        ['com.pairip.licensecheck.LicenseResponseHelper', 'com.pairip.licensecheck.ResponseValidator', 'com.pairip.licensecheck3.ResponseValidator'].forEach(cls => {
            safeUtils.safeJavaUse(cls, function (Validator) {
                try { Validator.validateResponse.implementation = function () {}; } catch (_) {}
                try { Validator.getRepeatedCheckMetadata.implementation = function () { return null; }; } catch (_) {}
                try { Validator.verifySignature.implementation = function () {}; } catch (_) {}
            }, logger);
        });

        // 6. LicenseContentProvider
        safeUtils.safeJavaUse('com.pairip.licensecheck.LicenseContentProvider', function (Provider) {
            Provider.onCreate.implementation = function () { return true; };
        }, logger);
    }

    function setupKotlinArrayBypass(pkgName, logger, safeUtils) {
        safeUtils.safeJavaUse('kotlin.collections.ArraysKt___ArraysKt', function (ArraysKt) {
            try {
                ArraysKt.contains.overload('[Ljava.lang.Object;', 'java.lang.Object').implementation = function (arr, element) {
                    if (element !== null) {
                        const elStr = element.toString();
                        if (elStr === pkgName || elStr.indexOf('vending') !== -1 || elStr.indexOf('amazon') !== -1) {
                            return true;
                        }
                    }
                    if (arr !== null && arr.length !== undefined) {
                        for (let i = 0; i < arr.length; i++) {
                            if (arr[i] !== null && arr[i].toString().indexOf('vending') !== -1) {
                                return true;
                            }
                        }
                    }
                    return this.contains.overload('[Ljava.lang.Object;', 'java.lang.Object').call(this, arr, element);
                };
            } catch (_) {}
        }, logger);

        safeUtils.safeJavaUse('kotlin.collections.CollectionsKt___CollectionsKt', function (CollectionsKt) {
            try {
                CollectionsKt.contains.overload('java.lang.Iterable', 'java.lang.Object').implementation = function (coll, element) {
                    if (element !== null) {
                        const elStr = element.toString();
                        if (elStr === pkgName || elStr.indexOf('vending') !== -1 || elStr.indexOf('amazon') !== -1) {
                            return true;
                        }
                    }
                    return this.contains.overload('java.lang.Iterable', 'java.lang.Object').call(this, coll, element);
                };
            } catch (_) {}
        }, logger);
    }

    // --- MODULE DEFINITION ---
    const HookModule = {
        name: MODULE_NAME,
        description: 'Google Play Installer Spoofing & PAIR IP License Bypass',
        stage: 'java',
        defaultEnabled: true,

        initJava: function (config, context) {
            const logger = context.logger || console;
            const safeUtils = context.safeUtils;
            const targetPkg = config.installer_package || DEFAULT_PLAY_STORE_PKG;

            logger.info(`Initializing Installer Spoofing (target: ${targetPkg})...`);
            setupInstallerSpoofing(targetPkg, logger, safeUtils);

            if (config.bypass_pair_license !== false) {
                setupPairIpBypass(logger, safeUtils);
            }

            setupKotlinArrayBypass(targetPkg, logger, safeUtils);
            logger.info('Installer & PAIR bypasses active.');
        }
    };

    if (root.__FRIDA_CORE__) {
        root.__FRIDA_CORE__.register(HookModule);
    }

})(typeof globalThis !== 'undefined' ? globalThis : this);

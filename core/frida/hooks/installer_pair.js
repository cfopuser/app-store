/**
 * installer_pair.js
 * 
 * Core Frida Module: Google Play Installer Spoofing & PAIR License Bypass (pairipfix).
 * Stage: Java (Dalvik/ART runtime)
 * 
 * Incorporates:
 * - Play Store Intent Navigation Firewall (drops market:// and Play Store redirect intents)
 * - ApplicationPackageManager.getInstallerPackageName -> com.android.vending
 * - ApplicationPackageManager.getInstallSourceInfo (API 30+) mock & getters spoofing
 * - IPackageManager IPC proxy spoofing
 * - Full PAIR IP (com.pairip.*) SignatureCheck, LicenseClient, LicenseClientV3 bypass
 * - PAIR IP LicenseActivity suppression
 * - Kotlin ArraysKt & CollectionsKt installer array bypass
 * - Anti-exit guard for PAIR lifecycle routines
 */

(function (root) {
    'use strict';

    const MODULE_NAME = 'installer_pair';
    const DEFAULT_PLAY_STORE_PKG = 'com.android.vending';

    function isPlayStoreRedirectIntent(intent) {
        if (!intent) return false;
        try {
            const data = intent.getData();
            const dataStr = data ? data.toString() : '';
            const pkg = intent.getPackage();
            const component = intent.getComponent();
            const compStr = component ? component.flattenToString() : '';

            if (dataStr.indexOf('market://') !== -1 || dataStr.indexOf('play.google.com') !== -1) {
                return true;
            }
            if (pkg === 'com.android.vending') {
                return true;
            }
            if (compStr.indexOf('com.pairip.licensecheck') !== -1 || 
                compStr.indexOf('LicenseActivity') !== -1 || 
                compStr.indexOf('com.android.vending') !== -1) {
                return true;
            }
        } catch (_) {}
        return false;
    }

    function setupIntentFirewall(logger, safeUtils) {
        // 1. Hook Activity.startActivity
        safeUtils.safeJavaUse('android.app.Activity', function (Activity) {
            ['startActivity', 'startActivityForResult'].forEach(methodName => {
                try {
                    const overloads = Activity[methodName].overloads;
                    for (let i = 0; i < overloads.length; i++) {
                        overloads[i].implementation = function () {
                            const args = Array.prototype.slice.call(arguments);
                            for (let j = 0; j < args.length; j++) {
                                if (args[j] && isPlayStoreRedirectIntent(args[j])) {
                                    logger.info(`[IntentFirewall] Blocked Play Store redirect via Activity.${methodName}`);
                                    return;
                                }
                            }
                            return overloads[i].apply(this, args);
                        };
                    }
                } catch (_) {}
            });
            logger.debug('Activity startActivity intent firewall active');
        }, logger);

        // 2. Hook ContextWrapper.startActivity
        safeUtils.safeJavaUse('android.content.ContextWrapper', function (ContextWrapper) {
            try {
                const overloads = ContextWrapper.startActivity.overloads;
                for (let i = 0; i < overloads.length; i++) {
                    overloads[i].implementation = function () {
                        const args = Array.prototype.slice.call(arguments);
                        for (let j = 0; j < args.length; j++) {
                            if (args[j] && isPlayStoreRedirectIntent(args[j])) {
                                logger.info('[IntentFirewall] Blocked Play Store redirect via ContextWrapper.startActivity');
                                return;
                            }
                        }
                        return overloads[i].apply(this, args);
                    };
                }
            } catch (_) {}
        }, logger);

        // 3. Hook Instrumentation.execStartActivity
        safeUtils.safeJavaUse('android.app.Instrumentation', function (Instrumentation) {
            try {
                const overloads = Instrumentation.execStartActivity.overloads;
                for (let i = 0; i < overloads.length; i++) {
                    overloads[i].implementation = function () {
                        const args = Array.prototype.slice.call(arguments);
                        for (let j = 0; j < args.length; j++) {
                            if (args[j] && isPlayStoreRedirectIntent(args[j])) {
                                logger.info('[IntentFirewall] Blocked Play Store redirect via Instrumentation.execStartActivity');
                                try {
                                    const ActivityResult = Java.use('android.app.Instrumentation$ActivityResult');
                                    return ActivityResult.$new(0, null);
                                } catch (_) {
                                    return null;
                                }
                            }
                        }
                        return overloads[i].apply(this, args);
                    };
                }
            } catch (_) {}
        }, logger);
    }

    function setupInstallerSpoofing(pkgName, logger, safeUtils) {
        // 1. ApplicationPackageManager
        safeUtils.safeJavaUse('android.app.ApplicationPackageManager', function (AppPkgMgr) {
            // getInstallerPackageName(String)
            try {
                AppPkgMgr.getInstallerPackageName.overload('java.lang.String').implementation = function () {
                    return pkgName;
                };
                logger.debug(`ApplicationPackageManager.getInstallerPackageName hooked -> ${pkgName}`);
            } catch (_) {}

            // getInstallSourceInfo(String) (API 30+)
            try {
                AppPkgMgr.getInstallSourceInfo.overload('java.lang.String').implementation = function (targetPkg) {
                    try {
                        const res = this.getInstallSourceInfo.overload('java.lang.String').call(this, targetPkg);
                        if (res !== null) {
                            return res;
                        }
                    } catch (_) {}

                    try {
                        const InstallSourceInfo = Java.use('android.content.pm.InstallSourceInfo');
                        return InstallSourceInfo.$new(pkgName, null, null, pkgName);
                    } catch (_) {
                        return null;
                    }
                };
                logger.debug(`ApplicationPackageManager.getInstallSourceInfo hooked -> ${pkgName}`);
            } catch (_) {}
        }, logger);

        // 2. InstallSourceInfo Getters (Android 11+ / API 30+)
        safeUtils.safeJavaUse('android.content.pm.InstallSourceInfo', function (InstallSourceInfo) {
            const getters = [
                'getInstallingPackageName',
                'getInitiatingPackageName',
                'getOriginatingPackageName',
                'getUpdateOwnerPackageName'
            ];
            getters.forEach(getter => {
                try {
                    if (InstallSourceInfo[getter]) {
                        InstallSourceInfo[getter].implementation = function () { return pkgName; };
                    }
                } catch (_) {}
            });

            try {
                if (InstallSourceInfo.getPackageSource) {
                    InstallSourceInfo.getPackageSource.implementation = function () { return 1; }; // PACKAGE_SOURCE_STORE
                }
            } catch (_) {}

            logger.debug(`InstallSourceInfo getters hooked -> ${pkgName}`);
        }, logger);

        // 3. IPackageManager Proxy
        safeUtils.safeJavaUse('android.content.pm.IPackageManager$Stub$Proxy', function (IPkgProxy) {
            try {
                if (IPkgProxy.getInstallerPackageName) {
                    IPkgProxy.getInstallerPackageName.implementation = function () { return pkgName; };
                }
            } catch (_) {}
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
                LicenseClient.checkLicense.overload('android.content.Context').implementation = function () {
                    logger.debug('PAIR LicenseClient.checkLicense(Context) neutralized');
                };
            } catch (_) {}

            try {
                LicenseClient.checkLicense.overload(
                    'android.content.Context', 'com.pairip.licensecheck.LicenseClient$LicenseListener'
                ).implementation = function (ctx, listener) {
                    logger.debug('PAIR LicenseClient.checkLicense with listener -> triggering onLicenseValid');
                    if (listener) {
                        try { listener.onLicenseValid(); } catch (_) {}
                    }
                };
            } catch (_) {}

            ['isLicenseValid', 'isCheckPassed', 'isLicensed', 'performLocalInstallerCheck'].forEach(m => {
                try {
                    if (LicenseClient[m]) {
                        LicenseClient[m].implementation = function () {
                            return true;
                        };
                    }
                } catch (_) {}
            });

            ['startPaywallActivity', 'startErrorDialogActivity', 'showErrorDialog', 'closeApp', 'exitApp'].forEach(m => {
                try {
                    if (LicenseClient[m]) {
                        LicenseClient[m].implementation = function () {
                            logger.debug(`PAIR LicenseClient.${m} suppressed`);
                        };
                    }
                } catch (_) {}
            });
        }, logger);

        // 3. LicenseClientV3
        safeUtils.safeJavaUse('com.pairip.licensecheck3.LicenseClientV3', function (LicenseClientV3) {
            try {
                LicenseClientV3.processResponse.overload('int', 'android.os.Bundle').implementation = function () {};
            } catch (_) {}
            ['checkLicense', 'requestLicense', 'startPaywallActivity', 'startErrorDialogActivity', 'closeApp', 'exitApp'].forEach(m => {
                try {
                    if (LicenseClientV3[m]) {
                        LicenseClientV3[m].implementation = function () {
                            logger.debug(`PAIR LicenseClientV3.${m} suppressed`);
                        };
                    }
                } catch (_) {}
            });
        }, logger);

        // 4. LicenseActivity suppression
        safeUtils.safeJavaUse('com.pairip.licensecheck.LicenseActivity', function (LicenseActivity) {
            ['closeApp', 'exitApp', 'showErrorDialog', 'showPaywallAndCloseApp'].forEach(method => {
                try {
                    if (LicenseActivity[method]) {
                        LicenseActivity[method].implementation = function () {
                            logger.debug(`PAIR LicenseActivity.${method} suppressed`);
                        };
                    }
                } catch (_) {}
            });

            ['onCreate', 'onStart', 'onResume'].forEach(method => {
                try {
                    if (LicenseActivity[method]) {
                        LicenseActivity[method].implementation = function () {
                            try { this.finish(); } catch (_) {}
                        };
                    }
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
            try {
                Provider.onCreate.implementation = function () { return true; };
            } catch (_) {}
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
            setupIntentFirewall(logger, safeUtils);
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

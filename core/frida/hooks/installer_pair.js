/**
 * Google Play Installer Spoofing & PAIR License Bypass Module
 * Incorporates proven hooks from ahmedmani/pairipfix, Google Play installer spoofing,
 * and Kotlin installer array whitelist bypasses.
 */

Java.perform(function () {
    console.log("[*] [Frida] Injecting Installer Spoofing & PAIR License Bypasses (pairipfix)...");

    var PLAY_STORE_PKG = "com.android.vending";

    // 1. ApplicationPackageManager.getInstallerPackageName
    try {
        var AppPkgMgr = Java.use('android.app.ApplicationPackageManager');
        AppPkgMgr.getInstallerPackageName.overload('java.lang.String').implementation = function (pkgName) {
            return PLAY_STORE_PKG;
        };
        console.log("[+] [Frida] ApplicationPackageManager.getInstallerPackageName hooked -> " + PLAY_STORE_PKG);
    } catch (e) {}

    // 2. PackageManager.getInstallSourceInfo & InstallSourceInfo getters (Android 11 / API 30+)
    try {
        var InstallSourceInfo = Java.use('android.content.pm.InstallSourceInfo');
        try {
            InstallSourceInfo.getInstallingPackageName.implementation = function () {
                return PLAY_STORE_PKG;
            };
        } catch (mErr1) {}
        try {
            InstallSourceInfo.getInitiatingPackageName.implementation = function () {
                return PLAY_STORE_PKG;
            };
        } catch (mErr2) {}
        try {
            InstallSourceInfo.getOriginatingPackageName.implementation = function () {
                return PLAY_STORE_PKG;
            };
        } catch (mErr3) {}
        console.log("[+] [Frida] InstallSourceInfo getters hooked -> " + PLAY_STORE_PKG);
    } catch (e) {}

    // 3. PAIR IP - SignatureCheck Bypass (pairipfix SignatureBypass)
    try {
        var SigCheck = Java.use('com.pairip.SignatureCheck');
        try {
            SigCheck.verifyIntegrity.overload('android.content.Context').implementation = function (ctx) {
                console.log("[+] [Frida] PAIR SignatureCheck.verifyIntegrity bypassed");
                return;
            };
        } catch (sc1) {}
        try {
            SigCheck.verifySignatureMatches.overload('java.lang.String').implementation = function (sig) {
                console.log("[+] [Frida] PAIR SignatureCheck.verifySignatureMatches returned true");
                return true;
            };
        } catch (sc2) {}
    } catch (e) {}

    // 4. PAIR IP - LicenseClient Bypass (pairipfix LicenseClientBypass)
    try {
        var LicenseClient = Java.use('com.pairip.licensecheck.LicenseClient');

        // initializeLicenseCheck -> do nothing
        try {
            LicenseClient.initializeLicenseCheck.implementation = function () {
                console.log("[+] [Frida] PAIR LicenseClient.initializeLicenseCheck bypassed");
                return;
            };
        } catch (lc0) {}

        // performLocalInstallerCheck -> return true
        try {
            LicenseClient.performLocalInstallerCheck.implementation = function () {
                console.log("[+] [Frida] PAIR LicenseClient.performLocalInstallerCheck -> true");
                return true;
            };
        } catch (lc1) {}

        // Set licenseCheckState = FULL_CHECK_OK
        try {
            var CheckState = Java.use('com.pairip.licensecheck.LicenseClient$LicenseCheckState');
            if (CheckState.FULL_CHECK_OK) {
                LicenseClient.licenseCheckState.value = CheckState.FULL_CHECK_OK.value;
                console.log("[+] [Frida] PAIR LicenseClient.licenseCheckState set to FULL_CHECK_OK");
            }
        } catch (lc2) {}

        // checkLicense(Context) -> return void
        try {
            LicenseClient.checkLicense.overload('android.content.Context').implementation = function (ctx) {
                console.log("[+] [Frida] PAIR LicenseClient.checkLicense(Context) bypassed");
                return;
            };
        } catch (lc3) {}

        // checkLicense(Context, LicenseListener) -> onLicenseValid()
        try {
            LicenseClient.checkLicense.overload('android.content.Context', 'com.pairip.licensecheck.LicenseClient$LicenseListener').implementation = function (ctx, listener) {
                console.log("[+] [Frida] PAIR LicenseClient.checkLicense(Context, Listener) bypassed");
                if (listener) {
                    try { listener.onLicenseValid(); } catch (lErr) {}
                }
                return;
            };
        } catch (lc4) {}

        // Block paywall / error dialog activities
        try {
            LicenseClient.startPaywallActivity.implementation = function () {
                console.log("[+] [Frida] PAIR LicenseClient.startPaywallActivity blocked");
                return;
            };
        } catch (lc5) {}

        try {
            LicenseClient.startErrorDialogActivity.implementation = function () {
                console.log("[+] [Frida] PAIR LicenseClient.startErrorDialogActivity blocked");
                return;
            };
        } catch (lc6) {}
    } catch (e) {}

    // 5. PAIR IP - LicenseClientV3 (pairipfix)
    try {
        var LicenseClientV3 = Java.use('com.pairip.licensecheck3.LicenseClientV3');
        try {
            LicenseClientV3.processResponse.overload('int', 'android.os.Bundle').implementation = function (code, bundle) {
                console.log("[+] [Frida] PAIR LicenseClientV3.processResponse bypassed");
                return;
            };
        } catch (v3Err) {}
    } catch (e) {}

    // 6. PAIR IP - LicenseActivity Bypass (pairipfix LicenseActivityBypass)
    try {
        var LicenseActivity = Java.use('com.pairip.licensecheck.LicenseActivity');
        var activityMethods = [
            'closeApp',
            'exitApp',
            'showErrorDialog',
            'showPaywallAndCloseApp'
        ];
        activityMethods.forEach(function (methodName) {
            try {
                if (LicenseActivity[methodName]) {
                    LicenseActivity[methodName].implementation = function () {
                        console.log("[+] [Frida] LicenseActivity." + methodName + " blocked");
                        try { this.finish(); } catch (fErr) {}
                        return;
                    };
                }
            } catch (aErr) {}
        });

        // logAndShowErrorDialog overloads
        try {
            LicenseActivity.logAndShowErrorDialog.overload('java.lang.String').implementation = function (msg) {
                console.log("[+] [Frida] LicenseActivity.logAndShowErrorDialog blocked: " + msg);
                try { this.finish(); } catch (fErr) {}
                return;
            };
        } catch (ld1) {}
        try {
            LicenseActivity.logAndShowErrorDialog.overload('java.lang.String', 'java.lang.Exception').implementation = function (msg, exc) {
                console.log("[+] [Frida] LicenseActivity.logAndShowErrorDialog with exc blocked: " + msg);
                try { this.finish(); } catch (fErr) {}
                return;
            };
        } catch (ld2) {}
    } catch (e) {}

    // 7. PAIR IP - LicenseResponseHelper & ResponseValidator (pairipfix LicenseResponseBypass)
    var validatorClasses = [
        'com.pairip.licensecheck.LicenseResponseHelper',
        'com.pairip.licensecheck.ResponseValidator',
        'com.pairip.licensecheck3.ResponseValidator'
    ];
    validatorClasses.forEach(function (clsName) {
        try {
            var Cls = Java.use(clsName);
            try {
                Cls.validateResponse.implementation = function () {
                    console.log("[+] [Frida] " + clsName + ".validateResponse bypassed");
                    return;
                };
            } catch (vErr1) {}
            try {
                Cls.getRepeatedCheckMetadata.implementation = function () {
                    return null;
                };
            } catch (vErr2) {}
            try {
                Cls.verifySignature.implementation = function () {
                    console.log("[+] [Frida] " + clsName + ".verifySignature bypassed");
                    return;
                };
            } catch (vErr3) {}
        } catch (clsErr) {}
    });

    // 8. PAIR IP - LicenseContentProvider onCreate Bypass
    try {
        var LicenseProvider = Java.use('com.pairip.licensecheck.LicenseContentProvider');
        LicenseProvider.onCreate.implementation = function () {
            console.log("[+] [Frida] PAIR LicenseContentProvider.onCreate bypassed");
            return true;
        };
    } catch (e) {}

    // 9. Kotlin ArraysKt.contains / CollectionsKt.contains Bypass for Installers
    try {
        var ArraysKt = Java.use('kotlin.collections.ArraysKt___ArraysKt');
        ArraysKt.contains.overload('[Ljava.lang.Object;', 'java.lang.Object').implementation = function (arr, element) {
            try {
                if (element !== null) {
                    var elStr = element.toString();
                    if (elStr === PLAY_STORE_PKG || elStr.indexOf('vending') !== -1 || elStr.indexOf('amazon') !== -1) {
                        return true;
                    }
                }
                if (arr !== null && arr.length !== undefined) {
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i] !== null && arr[i].toString().indexOf('vending') !== -1) {
                            return true;
                        }
                    }
                }
            } catch (err) {}
            return this.contains.overload('[Ljava.lang.Object;', 'java.lang.Object').call(this, arr, element);
        };
        console.log("[+] [Frida] ArraysKt.contains hooked for installer verification");
    } catch (e) {}

    try {
        var CollectionsKt = Java.use('kotlin.collections.CollectionsKt___CollectionsKt');
        CollectionsKt.contains.overload('java.lang.Iterable', 'java.lang.Object').implementation = function (coll, element) {
            try {
                if (element !== null) {
                    var elStr = element.toString();
                    if (elStr === PLAY_STORE_PKG || elStr.indexOf('vending') !== -1 || elStr.indexOf('amazon') !== -1) {
                        return true;
                    }
                }
            } catch (err) {}
            return this.contains.overload('java.lang.Iterable', 'java.lang.Object').call(this, coll, element);
        };
        console.log("[+] [Frida] CollectionsKt.contains hooked for installer verification");
    } catch (e) {}
});

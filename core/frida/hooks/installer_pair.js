/**
 * Google Play Installer Spoofing & PAIR License Bypass Module
 * Spoofs installer package name to 'com.android.vending', bypasses PAIR license checks, and Kotlin installer list contains checks.
 */

Java.perform(function () {
    console.log("[*] [Frida] Injecting Installer Spoofing & PAIR License Bypasses...");

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

    // 3. PAIR License Checks Bypass
    try {
        var LicenseClient = Java.use('com.pairip.licensecheck.LicenseClient');
        LicenseClient.checkLicense.overload('android.content.Context', 'com.pairip.licensecheck.LicenseClient$LicenseListener').implementation = function (ctx, listener) {
            console.log("[+] [Frida] PAIR LicenseClient.checkLicense bypassed");
            if (listener) {
                try {
                    listener.onLicenseValid();
                } catch (lErr) {}
            }
            return;
        };
    } catch (e) {}

    try {
        var LicenseProvider = Java.use('com.pairip.licensecheck.LicenseContentProvider');
        LicenseProvider.onCreate.implementation = function () {
            console.log("[+] [Frida] PAIR LicenseContentProvider.onCreate bypassed");
            return true;
        };
    } catch (e) {}

    // 4. Kotlin ArraysKt.contains / CollectionsKt.contains Bypass for Installers
    try {
        var ArraysKt = Java.use('kotlin.collections.ArraysKt___ArraysKt');
        ArraysKt.contains.overload('[Ljava.lang.Object;', 'java.lang.Object').implementation = function (arr, element) {
            if (element !== null && typeof element === 'object') {
                var elStr = element.toString();
                if (elStr === PLAY_STORE_PKG || elStr.indexOf('vending') !== -1 || elStr.indexOf('amazon') !== -1) {
                    return true;
                }
            }
            return this.contains.overload('[Ljava.lang.Object;', 'java.lang.Object').call(this, arr, element);
        };
        console.log("[+] [Frida] ArraysKt.contains hooked for installer verification");
    } catch (e) {}
});

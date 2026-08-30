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

    // 2. PackageManager.getInstallSourceInfo (Android 11 / API 30+)
    try {
        var AppPkgMgr = Java.use('android.app.ApplicationPackageManager');
        var InstallSourceInfo = Java.use('android.content.pm.InstallSourceInfo');

        AppPkgMgr.getInstallSourceInfo.overload('java.lang.String').implementation = function (pkgName) {
            try {
                // Try constructing InstallSourceInfo(initiatingPackageName, initiatingPackageSigningInfo, originatingPackageName, installingPackageName)
                var constructors = InstallSourceInfo.class.getDeclaredConstructors();
                for (var i = 0; i < constructors.length; i++) {
                    var c = constructors[i];
                    var paramTypes = c.getParameterTypes();
                    if (paramTypes.length >= 3) {
                        c.setAccessible(true);
                        var args = [];
                        for (var j = 0; j < paramTypes.length; j++) {
                            var pType = paramTypes[j].getName();
                            if (pType === 'java.lang.String') {
                                args.push(PLAY_STORE_PKG);
                            } else {
                                args.push(null);
                            }
                        }
                        var info = c.newInstance(Java.to(args, 'java.lang.Object[]'));
                        return Java.cast(info, InstallSourceInfo);
                    }
                }
            } catch (instErr) {
                // Fallback: call original and hook getter methods on returned object
            }

            var origInfo = this.getInstallSourceInfo.overload('java.lang.String').call(this, pkgName);
            if (origInfo !== null) {
                try {
                    origInfo.getInstallingPackageName.implementation = function () { return PLAY_STORE_PKG; };
                    origInfo.getInitiatingPackageName.implementation = function () { return PLAY_STORE_PKG; };
                    origInfo.getOriginatingPackageName.implementation = function () { return PLAY_STORE_PKG; };
                } catch (gErr) {}
            }
            return origInfo;
        };
        console.log("[+] [Frida] ApplicationPackageManager.getInstallSourceInfo hooked");
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

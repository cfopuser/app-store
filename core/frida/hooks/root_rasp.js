/**
 * Universal Root & RASP Bypass Hook Module
 * Covers RootBeer, FreeRASP / Talsec, Magisk / SU file checks, Build props, and command execution.
 */

Java.perform(function () {
    console.log("[*] [Frida] Injecting Root & RASP Bypasses...");

    // 1. RootBeer Library Bypass
    try {
        var RootBeer = Java.use('com.scottyab.rootbeer.RootBeer');
        var rootbeerMethods = [
            'isRooted',
            'isRootedWithoutBusyBoxCheck',
            'isRootedWithBusyBoxCheck',
            'checkSuExists',
            'checkForBinary',
            'checkForDangerousProps',
            'checkForRWPaths',
            'checkSuBinary',
            'checkBusyBoxBinary',
            'checkMagiskBinary',
            'checkTestKeys',
            'checkRootManagementApps',
            'checkPotentiallyDangerousApps',
            'checkRootCloakingApps',
            'isRootedWithBusyBoxCheck'
        ];

        rootbeerMethods.forEach(function (methodName) {
            try {
                if (RootBeer[methodName]) {
                    RootBeer[methodName].implementation = function () {
                        return false;
                    };
                }
            } catch (err) {}
        });
        console.log("[+] [Frida] RootBeer checks disarmed");
    } catch (e) {}

    // 2. Talsec / FreeRASP Library Bypass
    try {
        var Talsec = Java.use('com.aheadtec.talsec.security.Talsec');
        try {
            Talsec.start.implementation = function () {
                console.log("[+] [Frida] Talsec.start() suppressed");
                return;
            };
        } catch (err) {}
    } catch (e) {}

    // FreeRASP Flutter / Bridge Method Call Bypass
    try {
        var flutterClasses = [
            'com.aheadtec.talsec.security.TalsecPlugin',
            'com.aheadtec.talsec.security.c'
        ];
        flutterClasses.forEach(function (clsName) {
            try {
                var Cls = Java.use(clsName);
                if (Cls.onMethodCall) {
                    Cls.onMethodCall.implementation = function (call, result) {
                        var method = call.method.value || (call.method ? call.method.toString() : '');
                        var ArrayList = Java.use('java.util.ArrayList');
                        var BooleanCls = Java.use('java.lang.Boolean');

                        if (method === 'checkForIssues') {
                            result.success(ArrayList.$new());
                            return;
                        } else if (method === 'isRealDevice') {
                            result.success(BooleanCls.TRUE.value);
                            return;
                        } else if (method === 'isJailBroken' || method === 'isRooted') {
                            result.success(BooleanCls.FALSE.value);
                            return;
                        }
                        return this.onMethodCall(call, result);
                    };
                    console.log("[+] [Frida] FreeRASP plugin bridge hooked on " + clsName);
                }
            } catch (err) {}
        });
    } catch (e) {}

    // 3. SU / Magisk File Checks Bypass
    try {
        var File = Java.use('java.io.File');
        var suPaths = [
            '/system/bin/su',
            '/system/xbin/su',
            '/sbin/su',
            '/system/sd/xbin/su',
            '/system/bin/failsafe/su',
            '/data/local/su',
            '/data/local/bin/su',
            '/data/local/xbin/su',
            '/system/app/Superuser.apk',
            '/sbin/.magisk',
            '/data/adb/magisk',
            '/system/xbin/daemonsu',
            '/system/etc/init.d/99SuperSUDaemon',
            '/dev/com.koushikdutta.superuser.daemon/'
        ];

        File.exists.implementation = function () {
            var path = this.getAbsolutePath();
            for (var i = 0; i < suPaths.length; i++) {
                if (path.indexOf(suPaths[i]) !== -1) {
                    return false;
                }
            }
            return this.exists.call(this);
        };
        console.log("[+] [Frida] File.exists SU & Magisk paths hooked");
    } catch (e) {}

    // 4. Runtime.exec & ProcessBuilder Command Inspection Bypass
    try {
        var Runtime = Java.use('java.lang.Runtime');
        Runtime.exec.overload('java.lang.String').implementation = function (cmd) {
            if (cmd && (cmd.indexOf('su') !== -1 || cmd.indexOf('which') !== -1 || cmd.indexOf('magisk') !== -1)) {
                var IOException = Java.use('java.io.IOException');
                throw IOException.$new('Command blocked or not found');
            }
            return this.exec.overload('java.lang.String').call(this, cmd);
        };

        Runtime.exec.overload('[Ljava.lang.String;').implementation = function (cmdArray) {
            if (cmdArray && cmdArray.length > 0) {
                var cmdStr = cmdArray.join(' ');
                if (cmdStr.indexOf('su') !== -1 || cmdStr.indexOf('which') !== -1 || cmdStr.indexOf('magisk') !== -1) {
                    var IOException = Java.use('java.io.IOException');
                    throw IOException.$new('Command blocked or not found');
                }
            }
            return this.exec.overload('[Ljava.lang.String;').call(this, cmdArray);
        };
        console.log("[+] [Frida] Runtime.exec SU commands blocked");
    } catch (e) {}

    // 5. Build Properties Spoofing
    try {
        var Build = Java.use('android.os.Build');
        Build.TAGS.value = 'release-keys';
        console.log("[+] [Frida] Build.TAGS spoofed to 'release-keys'");
    } catch (e) {}

    try {
        var SystemProperties = Java.use('android.os.SystemProperties');
        SystemProperties.get.overload('java.lang.String').implementation = function (key) {
            if (key === 'ro.build.tags') {
                return 'release-keys';
            } else if (key === 'ro.debuggable') {
                return '0';
            } else if (key === 'ro.secure') {
                return '1';
            }
            return this.get.overload('java.lang.String').call(this, key);
        };

        SystemProperties.get.overload('java.lang.String', 'java.lang.String').implementation = function (key, def) {
            if (key === 'ro.build.tags') {
                return 'release-keys';
            } else if (key === 'ro.debuggable') {
                return '0';
            } else if (key === 'ro.secure') {
                return '1';
            }
            return this.get.overload('java.lang.String', 'java.lang.String').call(this, key, def);
        };
    } catch (e) {}
});

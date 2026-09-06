/**
 * Universal Root & RASP Bypass Hook Module
 * Covers RootBeer, FreeRASP / Talsec (TALSEC_INFO Intent & method channel), Magisk / SU file checks, Build props, and command execution.
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

    // 2. Talsec / FreeRASP Library Bypass (Fireshell Security Team tested Intent Hook)
    try {
        var Intent = Java.use("android.content.Intent");
        Intent.getStringExtra.overload("java.lang.String").implementation = function (str) {
            var extra = this.getStringExtra(str);
            var action = this.getAction();

            if (action === "TALSEC_INFO") {
                console.log("[+] [Frida] Hooking getStringExtra(\"" + str + "\") from " + action);
                console.log("\t Bypassing " + extra + " detection");
                return "";
            }
            return extra;
        };
        console.log("[+] [Frida] Talsec TALSEC_INFO Intent broadcast hook installed");
    } catch (e) {}

    // Talsec SDK direct class hooks (Java / Kotlin & Flutter plugin)
    var talsecCoreClasses = [
        'com.aheaditec.talsec.security.Talsec',
        'com.aheadtec.talsec.security.Talsec'
    ];
    talsecCoreClasses.forEach(function (clsName) {
        try {
            var Talsec = Java.use(clsName);
            if (Talsec.start) {
                Talsec.start.implementation = function () {
                    console.log("[+] [Frida] " + clsName + ".start() suppressed");
                    return;
                };
            }
        } catch (err) {}
    });

    // FreeRASP Flutter Plugin & Bridge Method Call Bypass
    var flutterClasses = [
        'com.aheaditec.talsec_security.TalsecSecurityPlugin',
        'com.aheaditec.talsec_security.c',
        'com.aheaditec.talsec_security.b',
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
                        console.log("[+] [Frida] FreeRASP " + clsName + ".checkForIssues -> empty list");
                        result.success(ArrayList.$new());
                        return;
                    } else if (method === 'isRealDevice') {
                        console.log("[+] [Frida] FreeRASP " + clsName + ".isRealDevice -> true");
                        result.success(BooleanCls.TRUE.value);
                        return;
                    } else if (method === 'isJailBroken' || method === 'isRooted' || method === 'isEmulator' || method === 'isTampered') {
                        console.log("[+] [Frida] FreeRASP " + clsName + "." + method + " -> false");
                        result.success(BooleanCls.FALSE.value);
                        return;
                    }
                    return this.onMethodCall(call, result);
                };
                console.log("[+] [Frida] FreeRASP plugin bridge hooked on " + clsName);
            }
        } catch (err) {}
    });

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
        var rootCmdRegex = /(?:^|[\/\s])(?:su|magisk|busybox|daemonsu)(?:[\/\s]|$)/i;
        var whichRootRegex = /(?:^|\s)which\s+(?:su|magisk|busybox)/i;

        Runtime.exec.overload('java.lang.String').implementation = function (cmd) {
            if (cmd && (rootCmdRegex.test(cmd) || whichRootRegex.test(cmd))) {
                return this.exec.overload('java.lang.String').call(this, 'echo not_found');
            }
            return this.exec.overload('java.lang.String').call(this, cmd);
        };

        Runtime.exec.overload('[Ljava.lang.String;').implementation = function (cmdArray) {
            if (cmdArray && cmdArray.length > 0) {
                var cmdStr = cmdArray.join(' ');
                if (rootCmdRegex.test(cmdStr) || whichRootRegex.test(cmdStr)) {
                    var safeCmd = Java.array('java.lang.String', ['echo', 'not_found']);
                    return this.exec.overload('[Ljava.lang.String;').call(this, safeCmd);
                }
            }
            return this.exec.overload('[Ljava.lang.String;').call(this, cmdArray);
        };
        console.log("[+] [Frida] Runtime.exec SU commands safely neutralized");
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

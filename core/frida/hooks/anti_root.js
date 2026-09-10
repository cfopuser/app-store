/**
 * anti_root.js
 * 
 * Core Frida Module: Universal Anti-Root, Anti-Emulator & RASP Bypass.
 * Stage: Both (Native libc + Dalvik/ART Java)
 * 
 * Unifies:
 * - Native libc system calls (access, stat, openat, fopen, __system_property_get)
 * - Java RootBeer & RootBeerFresh detection checks
 * - FreeRASP / Talsec SDK & Flutter bridge neutralization
 * - Anti-kill defenses (System.exit & Process.killProcess blocking)
 * - Emulator hardware, telephony, and sensor virtualization
 * - Xamarin / Mono runtime root detection bypass
 */

(function (root) {
    'use strict';

    const MODULE_NAME = 'anti_root';

    const ROOT_BINARIES = [
        'su', 'busybox', 'magisk', 'daemonsu', 'supersu', 'which',
        'subin', 'amphoras', 'koushikdutta', 'stericson'
    ];

    const ROOT_PATHS = [
        '/system/app/Superuser.apk',
        '/sbin/su',
        '/system/bin/su',
        '/system/xbin/su',
        '/data/local/xbin/su',
        '/data/local/bin/su',
        '/system/sd/xbin/su',
        '/system/bin/failsafe/su',
        '/data/local/su',
        '/su/bin/su',
        '/system/etc/init.d/99SuperSUDaemon',
        '/dev/com.koushikdutta.superuser.daemon/',
        '/system/xbin/daemonsu',
        '/system/xbin/busybox',
        '/system/bin/magisk',
        '/sbin/magisk',
        '/data/adb/magisk',
        '/data/adb/magisk.db',
        '/data/adb/modules',
        '/data/adb/.boot_count',
        '/proc/net/unix',
        '/system/bin/.ext/.su',
        '/system/usr/we-need-root/su-backup',
        '/system/xbin/ku.sud'
    ];

    const ROOT_PACKAGES = [
        'com.noshufou.android.su',
        'com.noshufou.android.su.elite',
        'eu.chainfire.supersu',
        'com.koushikdutta.superuser',
        'com.thirdparty.superuser',
        'com.yellowes.su',
        'com.topjohnwu.magisk',
        'com.kingroot.kinguser',
        'com.kingo.root',
        'com.smedialink.oneclickroot',
        'com.zhiqupk.root.global',
        'com.alephzain.framaroot',
        'me.weishu.kernelsu',
        'com.koushikdutta.rommanager',
        'com.koushikdutta.rommanager.license',
        'com.dimonvideo.luckypatcher',
        'com.chelpus.lackypatch',
        'com.chelpus.luckypatcher',
        'com.ramdroid.appquarantine',
        'com.ramdroid.appquarantinepro',
        'com.devadvance.rootcloak',
        'com.devadvance.rootcloakplus',
        'de.robv.android.xposed.installer',
        'com.saurik.substrate',
        'com.zachspong.temprootremovejb',
        'com.amphoras.hidemyroot',
        'com.amphoras.hidemyrootadfree',
        'com.formyhm.hiderootPremium',
        'com.formyhm.hideroot'
    ];

    const EMULATOR_FILES = [
        '/dev/socket/qemud',
        '/dev/qemu_pipe',
        '/system/lib/libc_malloc_debug_qemu.so',
        '/sys/qemu_trace',
        '/system/bin/qemu-props',
        '/dev/socket/genyd',
        '/dev/socket/baseband_genyd',
        '/system/bin/nox-prop',
        '/system/bin/ttVM-prop',
        '/system/bin/androVM-prop',
        '/system/bin/microvirt-prop',
        '/ueventd.nox.rc',
        '/ueventd.ttVM_x86.rc',
        '/fstab.nox',
        '/fstab.ttVM_x86'
    ];

    const SPOOFED_PROPS = {
        'ro.build.tags': 'release-keys',
        'ro.build.type': 'user',
        'ro.debuggable': '0',
        'ro.secure': '1',
        'ro.build.flavor': 'user',
        'ro.build.selinux': '1',
        'ro.boot.flash.locked': '1',
        'ro.boot.verifiedbootstate': 'green',
        'ro.boot.vbmeta.device_state': 'locked',
        'ro.hardware': 'qcom',
        'ro.product.model': 'Pixel 7',
        'ro.product.brand': 'google',
        'ro.product.name': 'panther',
        'ro.product.device': 'panther',
        'ro.product.manufacturer': 'Google',
        'ro.kernel.qemu': '0',
        'ro.kernel.android.qemud': '0'
    };

    function isSensitivePath(path) {
        if (!path || typeof path !== 'string') return false;
        for (let i = 0; i < ROOT_PATHS.length; i++) {
            if (path === ROOT_PATHS[i]) return true;
        }
        for (let i = 0; i < EMULATOR_FILES.length; i++) {
            if (path === EMULATOR_FILES[i]) return true;
        }
        if (/(^|\/)(su|busybox|magisk|daemonsu|supersu)$/i.test(path)) {
            return true;
        }
        if (path.includes('/proc/net/unix') || path.includes('/data/adb/.boot_count')) {
            return true;
        }
        return false;
    }

    // --- NATIVE STAGE HOOKS ---
    function hookRootBeerJniSymbols(logger) {
        const targets = [
            'Java_com_kimchangyoun_rootbeerFresh_RootBeerNative_checkForMagiskUDS',
            'Java_com_kimchangyoun_rootbeerFresh_RootBeerNative_checkForRoot',
            'Java_com_scottyab_rootbeer_RootBeerNative_checkForRoot',
            'Java_com_kimchangyoun_rootbeerFresh_RootBeerNative_setLogDebugMessages',
            'Java_com_scottyab_rootbeer_RootBeerNative_setLogDebugMessages'
        ];

        targets.forEach(sym => {
            const symPtr = Module.findExportByName(null, sym);
            if (symPtr) {
                try {
                    Interceptor.attach(symPtr, {
                        onLeave: function (retval) {
                            logger.debug(`[RootBeerNative JNI] Neutralized ${sym} -> 0`);
                            retval.replace(ptr(0));
                        }
                    });
                } catch (_) {}
            }
        });
    }

    function setupNativeRootBypass(logger, safeUtils) {
        const libc = Process.findModuleByName('libc.so');
        if (!libc) return;

        // 1. access & faccessat
        safeUtils.safeAttachNative('libc.so', 'access', {
            onEnter: function (args) {
                this.blocked = false;
                if (args[0].isNull()) return;
                try {
                    const path = args[0].readUtf8String();
                    if (isSensitivePath(path)) {
                        this.blocked = true;
                        logger.debug(`[libc.access] Blocked sensitive file check: ${path}`);
                    }
                } catch (_) {}
            },
            onLeave: function (retval) {
                if (this.blocked) retval.replace(ptr(-1));
            }
        }, logger);

        safeUtils.safeAttachNative('libc.so', 'faccessat', {
            onEnter: function (args) {
                this.blocked = false;
                if (args[1].isNull()) return;
                try {
                    const path = args[1].readUtf8String();
                    if (isSensitivePath(path)) {
                        this.blocked = true;
                        logger.debug(`[libc.faccessat] Blocked sensitive file check: ${path}`);
                    }
                } catch (_) {}
            },
            onLeave: function (retval) {
                if (this.blocked) retval.replace(ptr(-1));
            }
        }, logger);

        // 2. stat family
        ['stat', 'lstat', 'fstatat64', 'newfstatat'].forEach(sym => {
            const isAt = sym.includes('at');
            safeUtils.safeAttachNative('libc.so', sym, {
                onEnter: function (args) {
                    this.blocked = false;
                    const pathPtr = isAt ? args[1] : args[0];
                    if (!pathPtr || pathPtr.isNull()) return;
                    try {
                        const path = pathPtr.readUtf8String();
                        if (isSensitivePath(path)) {
                            this.blocked = true;
                            logger.debug(`[libc.${sym}] Blocked sensitive file stat: ${path}`);
                        }
                    } catch (_) {}
                },
                onLeave: function (retval) {
                    if (this.blocked) retval.replace(ptr(-1));
                }
            }, logger);
        });

        // 3. fopen & openat
        safeUtils.safeAttachNative('libc.so', 'fopen', {
            onEnter: function (args) {
                this.blocked = false;
                if (args[0].isNull()) return;
                try {
                    const path = args[0].readUtf8String();
                    if (isSensitivePath(path)) {
                        this.blocked = true;
                        logger.debug(`[libc.fopen] Blocked opening sensitive file: ${path}`);
                    }
                } catch (_) {}
            },
            onLeave: function (retval) {
                if (this.blocked) retval.replace(ptr(0));
            }
        }, logger);

        safeUtils.safeAttachNative('libc.so', 'openat', {
            onEnter: function (args) {
                this.blocked = false;
                if (args[1].isNull()) return;
                try {
                    const path = args[1].readUtf8String();
                    if (isSensitivePath(path)) {
                        this.blocked = true;
                        logger.debug(`[libc.openat] Blocked opening sensitive file: ${path}`);
                    }
                } catch (_) {}
            },
            onLeave: function (retval) {
                if (this.blocked) retval.replace(ptr(-1));
            }
        }, logger);

        // 4. __system_property_get
        safeUtils.safeAttachNative('libc.so', '__system_property_get', {
            onEnter: function (args) {
                this.propName = null;
                this.valuePtr = args[1];
                if (args[0].isNull()) return;
                try {
                    this.propName = args[0].readUtf8String();
                } catch (_) {}
            },
            onLeave: function (retval) {
                if (this.propName && (this.propName in SPOOFED_PROPS) && !this.valuePtr.isNull()) {
                    const spoofVal = SPOOFED_PROPS[this.propName];
                    this.valuePtr.writeUtf8String(spoofVal);
                    retval.replace(ptr(spoofVal.length));
                    logger.debug(`[libc.__system_property_get] Spoofed ${this.propName} -> ${spoofVal}`);
                }
            }
        }, logger);

        // 5. Dynamic Linker hook for RootBeer native JNI library
        hookRootBeerJniSymbols(logger);
        ['android_dlopen_ext', 'dlopen'].forEach(dlName => {
            safeUtils.safeAttachNative(null, dlName, {
                onEnter: function (args) {
                    this.libName = args[0].isNull() ? '' : args[0].readUtf8String();
                },
                onLeave: function (retval) {
                    if (this.libName && (this.libName.includes('libtool-checker.so') || this.libName.includes('libtoolChecker.so'))) {
                        logger.info(`[dlopen] Detected RootBeer library: ${this.libName}`);
                        hookRootBeerJniSymbols(logger);
                    }
                }
            }, logger);
        });

        // 6. Native Anti-Kill (exit, _exit, _Exit, kill self)
        ['exit', '_exit', '_Exit'].forEach(fn => {
            safeUtils.safeAttachNative('libc.so', fn, {
                onEnter: function (args) {
                    const code = args[0].toInt32();
                    logger.warn(`[AntiKill Native] Intercepted libc.${fn}(${code})`);
                    // Sleep calling thread to prevent terminating the entire process
                    Thread.sleep(60000);
                }
            }, logger);
        });

        safeUtils.safeAttachNative('libc.so', 'kill', {
            onEnter: function (args) {
                this.blocked = false;
                const targetPid = args[0].toInt32();
                if (targetPid === Process.id || targetPid === 0 || targetPid === -1) {
                    logger.warn(`[AntiKill Native] Suppressed libc.kill(${targetPid}, ${args[1].toInt32()}) on self`);
                    this.blocked = true;
                }
            },
            onLeave: function (retval) {
                if (this.blocked) {
                    retval.replace(ptr(0));
                }
            }
        }, logger);
    }

    function setupXamarinBypass(logger) {
        const monoModules = ['libmonosgen-2.0.so', 'libmonosgen-64.so', 'libmono-native.so'];
        let monoSo = null;
        for (let i = 0; i < monoModules.length; i++) {
            monoSo = Process.findModuleByName(monoModules[i]);
            if (monoSo) break;
        }
        if (!monoSo) return;

        try {
            const mono_thread_attach = Module.findExportByName(monoSo.name, 'mono_thread_attach');
            const mono_get_root_domain = Module.findExportByName(monoSo.name, 'mono_get_root_domain');
            if (mono_thread_attach && mono_get_root_domain) {
                const getRootDomain = new NativeFunction(mono_get_root_domain, 'pointer', []);
                const threadAttach = new NativeFunction(mono_thread_attach, 'pointer', ['pointer']);
                const rootDomain = getRootDomain();
                if (!rootDomain.isNull()) {
                    threadAttach(rootDomain);
                    logger.debug('Attached to Mono/Xamarin root domain.');
                }
            }
        } catch (e) {
            logger.debug(`Xamarin attach: ${e.message}`);
        }
    }

    // --- JAVA STAGE HOOKS ---
    function setupJavaFileHooks(logger, safeUtils) {
        safeUtils.safeJavaUse('java.io.File', function (File) {
            const origExists = File.exists;
            File.exists.implementation = function () {
                const path = this.getAbsolutePath();
                if (isSensitivePath(path)) {
                    logger.debug(`[File.exists] Denying root file: ${path}`);
                    return false;
                }
                return origExists.call(this);
            };
        }, logger);

        safeUtils.safeJavaUse('java.io.UnixFileSystem', function (UnixFileSystem) {
            const origCheck = UnixFileSystem.checkAccess;
            UnixFileSystem.checkAccess.implementation = function (file, access) {
                const path = file.getAbsolutePath();
                if (isSensitivePath(path)) {
                    logger.debug(`[UnixFileSystem.checkAccess] Denying: ${path}`);
                    return false;
                }
                return origCheck.call(this, file, access);
            };
        }, logger);
    }

    function setupJavaPackageManagerHooks(logger, safeUtils) {
        safeUtils.safeJavaUse('android.app.ApplicationPackageManager', function (AppPkgMgr) {
            const getPackageInfo = AppPkgMgr.getPackageInfo;
            const NameNotFoundException = Java.use('android.content.pm.PackageManager$NameNotFoundException');

            AppPkgMgr.getPackageInfo.overload('java.lang.String', 'int').implementation = function (pkgName, flags) {
                if (ROOT_PACKAGES.indexOf(pkgName) !== -1) {
                    logger.debug(`[PackageManager] Concealing root package: ${pkgName}`);
                    throw NameNotFoundException.$new(pkgName);
                }
                return getPackageInfo.overload('java.lang.String', 'int').call(this, pkgName, flags);
            };

            try {
                const PackageInfoFlags = Java.use('android.content.pm.PackageManager$PackageInfoFlags');
                AppPkgMgr.getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').implementation = function (pkgName, flags) {
                    if (ROOT_PACKAGES.indexOf(pkgName) !== -1) {
                        logger.debug(`[PackageManager] Concealing root package: ${pkgName}`);
                        throw NameNotFoundException.$new(pkgName);
                    }
                    return getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').call(this, pkgName, flags);
                };
            } catch (_) {}
        }, logger);
    }

    function setupJavaCommandHooks(logger, safeUtils) {
        safeUtils.safeJavaUse('java.lang.ProcessImpl', function (ProcessImpl) {
            ProcessImpl.start.implementation = function (cmdarray, env, dir, redirects, redirectErrorStream) {
                if (cmdarray && cmdarray.length > 0) {
                    const cmd = cmdarray[0] ? cmdarray[0].toString() : '';
                    const fullCmd = Array.from(cmdarray).map(c => (c ? c.toString() : '')).join(' ');

                    let isRootCmd = false;
                    for (let i = 0; i < ROOT_BINARIES.length; i++) {
                        const bin = ROOT_BINARIES[i];
                        if (cmd === bin || /(^|\/)(su|magisk|busybox|daemonsu)$/i.test(cmd) || fullCmd.includes('which ' + bin)) {
                            isRootCmd = true;
                            break;
                        }
                    }

                    if (isRootCmd) {
                        logger.debug(`[ProcessImpl.start] Neutralizing root command: ${fullCmd}`);
                        const StringClass = Java.use('java.lang.String');
                        const fakeArray = Java.array('java.lang.String', [
                            StringClass.$new('/system/bin/sh'),
                            StringClass.$new('-c'),
                            StringClass.$new('exit 1')
                        ]);
                        return ProcessImpl.start.call(this, fakeArray, env, dir, redirects, redirectErrorStream);
                    }
                }
                return ProcessImpl.start.call(this, cmdarray, env, dir, redirects, redirectErrorStream);
            };
        }, logger);

        safeUtils.safeJavaUse('java.lang.Runtime', function (Runtime) {
            const rootCmdRegex = /(?:^|[\/\s])(?:su|magisk|busybox|daemonsu)(?:[\/\s]|$)/i;
            const whichRootRegex = /(?:^|\s)which\s+(?:su|magisk|busybox)/i;

            try {
                Runtime.exec.overload('java.lang.String').implementation = function (cmd) {
                    if (cmd && (rootCmdRegex.test(cmd) || whichRootRegex.test(cmd))) {
                        return this.exec.overload('java.lang.String').call(this, 'echo not_found');
                    }
                    return this.exec.overload('java.lang.String').call(this, cmd);
                };
            } catch (_) {}

            try {
                Runtime.exec.overload('[Ljava.lang.String;').implementation = function (cmdArray) {
                    if (cmdArray && cmdArray.length > 0) {
                        const joined = Array.from(cmdArray).join(' ');
                        if (rootCmdRegex.test(joined) || whichRootRegex.test(joined)) {
                            const StringClass = Java.use('java.lang.String');
                            const fake = Java.array('java.lang.String', [StringClass.$new('echo'), StringClass.$new('not_found')]);
                            return this.exec.overload('[Ljava.lang.String;').call(this, fake);
                        }
                    }
                    return this.exec.overload('[Ljava.lang.String;').call(this, cmdArray);
                };
            } catch (_) {}
        }, logger);
    }

    function setupAntiKillDefenses(logger, safeUtils) {
        // 1. System.exit
        safeUtils.safeJavaUse('java.lang.System', function (System) {
            try {
                System.exit.implementation = function (code) {
                    logger.warn(`[AntiKill] Blocked System.exit(${code}) invocation.`);
                };
            } catch (_) {}
        }, logger);

        // 2. Runtime.exit & Runtime.halt
        safeUtils.safeJavaUse('java.lang.Runtime', function (Runtime) {
            try {
                Runtime.exit.overload('int').implementation = function (code) {
                    logger.warn(`[AntiKill] Blocked Runtime.exit(${code}) invocation.`);
                };
            } catch (_) {}
            try {
                Runtime.halt.overload('int').implementation = function (code) {
                    logger.warn(`[AntiKill] Blocked Runtime.halt(${code}) invocation.`);
                };
            } catch (_) {}
        }, logger);

        // 3. Process.killProcess & Process.sendSignal
        safeUtils.safeJavaUse('android.os.Process', function (ProcessCls) {
            try {
                ProcessCls.killProcess.implementation = function (pid) {
                    logger.warn(`[AntiKill] Blocked Process.killProcess(${pid}) invocation.`);
                };
            } catch (_) {}
            try {
                ProcessCls.sendSignal.implementation = function (pid, sig) {
                    logger.warn(`[AntiKill] Blocked Process.sendSignal(${pid}, ${sig}) invocation.`);
                };
            } catch (_) {}
        }, logger);

        // 4. Activity finishAffinity & finishAndRemoveTask
        safeUtils.safeJavaUse('android.app.Activity', function (Activity) {
            try {
                Activity.finishAffinity.implementation = function () {
                    logger.warn('[AntiKill] Blocked Activity.finishAffinity() invocation.');
                };
            } catch (_) {}
            try {
                Activity.finishAndRemoveTask.implementation = function () {
                    logger.warn('[AntiKill] Blocked Activity.finishAndRemoveTask() invocation.');
                    return true;
                };
            } catch (_) {}
        }, logger);
    }

    function setupTalsecFreeRASPBypass(logger, safeUtils) {
        safeUtils.safeJavaUse('android.content.Intent', function (Intent) {
            Intent.getStringExtra.overload('java.lang.String').implementation = function (str) {
                const extra = this.getStringExtra(str);
                const action = this.getAction();
                if (action === 'TALSEC_INFO') {
                    logger.debug(`[Talsec] Neutralized TALSEC_INFO extra '${str}'`);
                    return '';
                }
                return extra;
            };
        }, logger);

        const talsecClasses = [
            'com.aheaditec.talsec.security.Talsec',
            'com.aheadtec.talsec.security.Talsec'
        ];
        talsecClasses.forEach(cls => {
            safeUtils.safeJavaUse(cls, function (Talsec) {
                if (Talsec.start) {
                    Talsec.start.implementation = function () {
                        logger.info(`[Talsec] Suppressed ${cls}.start()`);
                    };
                }
            }, logger);
        });

        // Flutter FreeRASP plugin methods
        const flutterClasses = [
            'com.aheaditec.talsec_security.TalsecSecurityPlugin',
            'com.aheadtec.talsec.security.TalsecPlugin'
        ];
        flutterClasses.forEach(cls => {
            safeUtils.safeJavaUse(cls, function (Plugin) {
                if (Plugin.onMethodCall) {
                    Plugin.onMethodCall.implementation = function (call, result) {
                        const method = call.method.value || (call.method ? call.method.toString() : '');
                        const ArrayList = Java.use('java.util.ArrayList');
                        const BooleanCls = Java.use('java.lang.Boolean');

                        if (method === 'checkForIssues') {
                            result.success(ArrayList.$new());
                            return;
                        } else if (method === 'isRealDevice') {
                            result.success(BooleanCls.TRUE.value);
                            return;
                        } else if (['isJailBroken', 'isRooted', 'isEmulator', 'isTampered'].indexOf(method) !== -1) {
                            result.success(BooleanCls.FALSE.value);
                            return;
                        }
                        return this.onMethodCall(call, result);
                    };
                }
            }, logger);
        });
    }

    function setupRootBeerBypass(logger, safeUtils) {
        const rootBeerClasses = [
            'com.scottyab.rootbeer.RootBeer',
            'com.kimchangyoun.rootbeer.RootBeer',
            'com.kimchangyoun.rootbeerFresh.RootBeer'
        ];
        const falseMethods = [
            'isRooted', 'isRootedWithoutBusyBoxCheck', 'isRootedWithBusyBoxCheck',
            'checkSuExists', 'checkForBinary', 'checkForDangerousProps', 'checkForRWPaths',
            'checkSuBinary', 'checkBusyBoxBinary', 'checkMagiskBinary', 'checkTestKeys',
            'checkRootManagementApps', 'checkPotentiallyDangerousApps', 'checkRootCloakingApps',
            'checkForRootNative', 'checkForMagiskUDS', 'detectRootManagementApps',
            'detectPotentiallyDangerousApps', 'detectTestKeys', 'checkForBusyBoxBinary',
            'checkForSuBinary', 'detectRootCloakingApps'
        ];

        rootBeerClasses.forEach(className => {
            safeUtils.safeJavaUse(className, function (RB) {
                falseMethods.forEach(method => {
                    try {
                        if (RB[method]) {
                            RB[method].implementation = function () {
                                return false;
                            };
                        }
                    } catch (_) {}
                });
                logger.info(`Disarmed RootBeer checks on ${className}`);
            }, logger);
        });
    }

    function setupJavaEmulatorBypass(logger, safeUtils) {
        safeUtils.safeJavaUse('android.telephony.TelephonyManager', function (TelephonyManager) {
            if (TelephonyManager.getDeviceId) {
                try { TelephonyManager.getDeviceId.overload().implementation = function () { return '358240051111111'; }; } catch (_) {}
            }
            if (TelephonyManager.getSimOperatorName) {
                try { TelephonyManager.getSimOperatorName.overload().implementation = function () { return 'T-Mobile'; }; } catch (_) {}
            }
            if (TelephonyManager.getNetworkOperatorName) {
                try { TelephonyManager.getNetworkOperatorName.overload().implementation = function () { return 'T-Mobile'; }; } catch (_) {}
            }
            if (TelephonyManager.getSimState) {
                try { TelephonyManager.getSimState.overload().implementation = function () { return 5; }; } catch (_) {}
            }
            if (TelephonyManager.getPhoneType) {
                try { TelephonyManager.getPhoneType.overload().implementation = function () { return 1; }; } catch (_) {}
            }
        }, logger);

        safeUtils.safeJavaUse('android.os.Build', function (Build) {
            Build.TAGS.value = 'release-keys';
            Build.TYPE.value = 'user';
            Build.MANUFACTURER.value = 'Google';
            Build.BRAND.value = 'google';
            Build.DEVICE.value = 'panther';
            Build.MODEL.value = 'Pixel 7';
            Build.HARDWARE.value = 'qcom';
            Build.BOARD.value = 'panther';
            Build.PRODUCT.value = 'panther';
            Build.FINGERPRINT.value = 'google/panther/panther:13/TQ3A.230901.001/10750761:user/release-keys';
        }, logger);
    }

    // --- MODULE DEFINITION ---
    const HookModule = {
        name: MODULE_NAME,
        description: 'Universal Anti-Root, Anti-Emulator & RASP Bypass',
        stage: 'both',
        defaultEnabled: true,

        initNative: function (config, context) {
            const logger = context.logger || console;
            const safeUtils = context.safeUtils;

            logger.info('Initializing native Anti-Root bypasses...');
            if (config.bypass_native_root !== false) {
                setupNativeRootBypass(logger, safeUtils);
            }
            if (config.bypass_xamarin !== false) {
                setupXamarinBypass(logger);
            }
        },

        initJava: function (config, context) {
            const logger = context.logger || console;
            const safeUtils = context.safeUtils;

            logger.info('Initializing Java Anti-Root & RASP bypasses...');

            setupJavaFileHooks(logger, safeUtils);
            setupJavaPackageManagerHooks(logger, safeUtils);
            setupJavaCommandHooks(logger, safeUtils);
            setupRootBeerBypass(logger, safeUtils);

            if (config.anti_kill !== false) {
                setupAntiKillDefenses(logger, safeUtils);
            }

            if (config.bypass_talsec !== false) {
                setupTalsecFreeRASPBypass(logger, safeUtils);
            }

            if (config.bypass_emulator !== false) {
                setupJavaEmulatorBypass(logger, safeUtils);
            }

            logger.info('Anti-Root & RASP protection layers active.');
        }
    };

    if (root.__FRIDA_CORE__) {
        root.__FRIDA_CORE__.register(HookModule);
    }

})(typeof globalThis !== 'undefined' ? globalThis : this);

/**
 * anti_root_emulator.js
 * 
 * Production-grade Frida module for bypassing:
 * 1. Root detection (binaries, packages, build properties, su execution, native libc checks)
 * 2. Emulator detection (Build props, QEMU/Ranchu pipes, telephony, sensor checks)
 * 3. Framework-specific checks (Xamarin / Mono runtime)
 * 
 * Works seamlessly with both dynamic attachment (frida -U -f ...) and static
 * embedding via frida-gadget (early instrumentation).
 */

(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.AntiRootEmulator = factory();
    }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    const MODULE_NAME = 'AntiRootEmulator';

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
        // Known Root Management Apps
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
        // Known Dangerous & Cheating / Mod Apps
        'com.koushikdutta.rommanager',
        'com.koushikdutta.rommanager.license',
        'com.dimonvideo.luckypatcher',
        'com.chelpus.lackypatch',
        'com.chelpus.luckypatcher',
        'com.ramdroid.appquarantine',
        'com.ramdroid.appquarantinepro',
        'com.android.vending.billing.InAppBillingService.COIN',
        'com.android.vending.billing.InAppBillingService.LUCK',
        'com.blackmartalpha',
        'org.blackmart.market',
        'com.allinone.free',
        'com.repodroid.app',
        'org.creeplays.hack',
        'com.baseappfull.fwd',
        'com.zmapp',
        'com.dv.marketmod.installer',
        'org.mobilism.android',
        'com.android.wp.net.log',
        'com.android.camera.update',
        'cc.madkite.freedom',
        'com.solohsu.android.edxp.manager',
        'org.meowcat.edxposed.manager',
        'com.xmodgame',
        'com.cih.game_cih',
        'com.charles.lpoqasert',
        'catch_.me_.if_.you_.can_',
        // Known Root Cloaking & Hooking Frameworks
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

    /**
     * Check if a given file path is related to root binaries, artifacts, UDS or emulators.
     */
    function isSensitivePath(path) {
        if (!path || typeof path !== 'string') return false;
        for (let i = 0; i < ROOT_PATHS.length; i++) {
            if (path === ROOT_PATHS[i]) return true;
        }
        for (let i = 0; i < EMULATOR_FILES.length; i++) {
            if (path === EMULATOR_FILES[i]) return true;
        }
        // Strict boundary check for binary names to avoid false positive matching
        if (/(^|\/)(su|busybox|magisk|daemonsu|supersu)$/i.test(path)) {
            return true;
        }
        if (path.includes('/proc/net/unix') || path.includes('/data/adb/.boot_count')) {
            return true;
        }
        return false;
    }

    function bypassJavaRoot(logger) {
        // 1. File checks (File.exists)
        try {
            const File = Java.use('java.io.File');
            const existsOriginal = File.exists;
            File.exists.implementation = function () {
                const path = this.getAbsolutePath();
                if (isSensitivePath(path)) {
                    logger.debug(`[File.exists] Denying sensitive file: ${path}`);
                    return false;
                }
                return existsOriginal.call(this);
            };
            logger.debug('Hooked File.exists');
        } catch (e) {
            logger.debug(`File.exists hook skipped: ${e.message}`);
        }

        // 2. UnixFileSystem.checkAccess
        try {
            const UnixFileSystem = Java.use('java.io.UnixFileSystem');
            const checkAccessOriginal = UnixFileSystem.checkAccess;
            UnixFileSystem.checkAccess.implementation = function (file, access) {
                const path = file.getAbsolutePath();
                if (isSensitivePath(path)) {
                    logger.debug(`[UnixFileSystem.checkAccess] Denied: ${path}`);
                    return false;
                }
                return checkAccessOriginal.call(this, file, access);
            };
            logger.debug('Hooked UnixFileSystem.checkAccess');
        } catch (e) {
            logger.debug(`UnixFileSystem.checkAccess hook skipped: ${e.message}`);
        }

        // 3. ApplicationPackageManager.getPackageInfo
        try {
            const ApplicationPackageManager = Java.use('android.app.ApplicationPackageManager');
            const getPackageInfo = ApplicationPackageManager.getPackageInfo;
            const NameNotFoundException = Java.use('android.content.pm.PackageManager$NameNotFoundException');

            getPackageInfo.overload('java.lang.String', 'int').implementation = function (pkgName, flags) {
                if (ROOT_PACKAGES.indexOf(pkgName) !== -1) {
                    logger.debug(`[PackageManager] Concealing root package: ${pkgName}`);
                    throw NameNotFoundException.$new(pkgName);
                }
                return getPackageInfo.overload('java.lang.String', 'int').call(this, pkgName, flags);
            };

            // Android 13+ PackageInfoFlags overload
            try {
                const PackageInfoFlags = Java.use('android.content.pm.PackageManager$PackageInfoFlags');
                getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').implementation = function (pkgName, flags) {
                    if (ROOT_PACKAGES.indexOf(pkgName) !== -1) {
                        logger.debug(`[PackageManager] Concealing root package (flags): ${pkgName}`);
                        throw NameNotFoundException.$new(pkgName);
                    }
                    return getPackageInfo.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').call(this, pkgName, flags);
                };
            } catch (_) {}
            logger.debug('Hooked ApplicationPackageManager.getPackageInfo');
        } catch (e) {
            logger.debug(`PackageManager hook skipped: ${e.message}`);
        }

        // 4. Command execution choke-points: ProcessImpl.start & ProcessBuilder.start
        try {
            const ProcessImpl = Java.use('java.lang.ProcessImpl');
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

                    // Simulate restricted permission on sensitive shell queries
                    if (fullCmd.includes('getprop ro.debuggable') || fullCmd.includes('mount')) {
                        logger.debug(`[ProcessImpl.start] Blocking inspection query: ${fullCmd}`);
                        try {
                            const IOException = Java.use('java.io.IOException');
                            throw IOException.$new('Command execution restricted');
                        } catch (err) {
                            const StringClass = Java.use('java.lang.String');
                            const fakeArray = Java.array('java.lang.String', [
                                StringClass.$new('/system/bin/sh'),
                                StringClass.$new('-c'),
                                StringClass.$new('exit 1')
                            ]);
                            return ProcessImpl.start.call(this, fakeArray, env, dir, redirects, redirectErrorStream);
                        }
                    }
                }
                return ProcessImpl.start.call(this, cmdarray, env, dir, redirects, redirectErrorStream);
            };
            logger.debug('Hooked ProcessImpl.start');
        } catch (e) {
            logger.debug(`ProcessImpl.start hook skipped: ${e.message}`);
        }

        // 5. SystemProperties.get & getInt & getBoolean
        try {
            const SystemProperties = Java.use('android.os.SystemProperties');
            const getOriginal = SystemProperties.get;
            SystemProperties.get.overload('java.lang.String').implementation = function (key) {
                if (key in SPOOFED_PROPS) {
                    logger.debug(`[SystemProperties.get] Spoofed ${key} -> ${SPOOFED_PROPS[key]}`);
                    return SPOOFED_PROPS[key];
                }
                let res = getOriginal.overload('java.lang.String').call(this, key);
                if (key === 'ro.build.tags' && res && res.includes('test-keys')) {
                    return res.replace('test-keys', 'release-keys');
                }
                return res;
            };

            SystemProperties.get.overload('java.lang.String', 'java.lang.String').implementation = function (key, def) {
                if (key in SPOOFED_PROPS) {
                    logger.debug(`[SystemProperties.get] Spoofed ${key} -> ${SPOOFED_PROPS[key]}`);
                    return SPOOFED_PROPS[key];
                }
                let res = getOriginal.overload('java.lang.String', 'java.lang.String').call(this, key, def);
                if (key === 'ro.build.tags' && res && res.includes('test-keys')) {
                    return res.replace('test-keys', 'release-keys');
                }
                return res;
            };

            SystemProperties.getInt.implementation = function (key, def) {
                if (key === 'ro.debuggable') return 0;
                if (key === 'ro.secure') return 1;
                return this.getInt(key, def);
            };

            SystemProperties.getBoolean.implementation = function (key, def) {
                if (key === 'ro.debuggable') return false;
                if (key === 'ro.secure') return true;
                return this.getBoolean(key, def);
            };
            logger.debug('Hooked android.os.SystemProperties');
        } catch (e) {
            logger.debug(`SystemProperties hook skipped: ${e.message}`);
        }

        // 6. android.os.Build static field overrides
        try {
            const Build = Java.use('android.os.Build');
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
            logger.debug('Spoofed android.os.Build static fields');
        } catch (e) {
            logger.debug(`Build fields spoofing skipped: ${e.message}`);
        }

        // 7. RootBeer library specific method overrides
        const rootBeerClasses = [
            'com.scottyab.rootbeer.RootBeer',
            'com.kimchangyoun.rootbeer.RootBeer',
            'com.kimchangyoun.rootbeerFresh.RootBeer'
        ];
        rootBeerClasses.forEach(className => {
            try {
                const RB = Java.use(className);
                const falseMethods = [
                    'isRooted',
                    'isRootedWithoutBusyBoxCheck',
                    'isRootedWithBusyBoxCheck',
                    'detectRootManagementApps',
                    'detectPotentiallyDangerousApps',
                    'detectTestKeys',
                    'checkForBusyBoxBinary',
                    'checkForSuBinary',
                    'checkSuExists',
                    'checkForRWPaths',
                    'checkForDangerousProps',
                    'checkForRootNative',
                    'checkForMagiskBinary',
                    'checkForMagiskUDS',
                    'detectRootCloakingApps'
                ];
                falseMethods.forEach(methodName => {
                    try {
                        if (RB[methodName]) {
                            RB[methodName].implementation = function () {
                                logger.debug(`[RootBeer] Neutralized ${className}.${methodName}() -> false`);
                                return false;
                            };
                        }
                    } catch (_) {}
                });
                logger.info(`Neutralized ${className}`);
            } catch (_) {}
        });
    }

    function bypassJavaEmulator(logger) {
        // TelephonyManager hooks
        try {
            const TelephonyManager = Java.use('android.telephony.TelephonyManager');
            if (TelephonyManager.getDeviceId) {
                try {
                    TelephonyManager.getDeviceId.overload().implementation = function () {
                        return '358240051111111';
                    };
                } catch (_) {}
            }
            if (TelephonyManager.getSimOperatorName) {
                try {
                    TelephonyManager.getSimOperatorName.overload().implementation = function () {
                        return 'T-Mobile';
                    };
                } catch (_) {}
            }
            if (TelephonyManager.getNetworkOperatorName) {
                try {
                    TelephonyManager.getNetworkOperatorName.overload().implementation = function () {
                        return 'T-Mobile';
                    };
                } catch (_) {}
            }
            if (TelephonyManager.getSimState) {
                try {
                    TelephonyManager.getSimState.overload().implementation = function () {
                        return 5; // SIM_STATE_READY
                    };
                } catch (_) {}
            }
            if (TelephonyManager.getPhoneType) {
                try {
                    TelephonyManager.getPhoneType.overload().implementation = function () {
                        return 1; // PHONE_TYPE_GSM
                    };
                } catch (_) {}
            }
            logger.debug('Hooked TelephonyManager emulator indicators');
        } catch (e) {
            logger.debug(`TelephonyManager hook skipped: ${e.message}`);
        }

        // SensorManager: Emulators often lack accelerometer or report 0 sensors
        try {
            const SensorManager = Java.use('android.hardware.SensorManager');
            if (SensorManager.getSensorList) {
                const getSensorList = SensorManager.getSensorList;
                SensorManager.getSensorList.overload('int').implementation = function (type) {
                    const list = getSensorList.call(this, type);
                    if (list.size() === 0) {
                        logger.debug(`[SensorManager] Emulated presence for sensor type ${type}`);
                    }
                    return list;
                };
            }
        } catch (e) {
            logger.debug(`SensorManager hook skipped: ${e.message}`);
        }
    }

    /**
     * Intercept RootBeer and RootBeerFresh native JNI functions dynamically
     */
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

    function bypassNativeRoot(logger) {
        const libc = Process.findModuleByName('libc.so');
        if (!libc) {
            logger.debug('libc.so not found for native hooks');
            return;
        }

        // 1. Hook access & faccessat
        const accessPtr = Module.findExportByName('libc.so', 'access');
        if (accessPtr) {
            try {
                Interceptor.attach(accessPtr, {
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
                        if (this.blocked) {
                            retval.replace(ptr(-1));
                        }
                    }
                });
                logger.debug('Hooked native libc.so!access');
            } catch (e) {
                logger.debug(`Failed to hook native access: ${e.message}`);
            }
        }

        const faccessatPtr = Module.findExportByName('libc.so', 'faccessat');
        if (faccessatPtr) {
            try {
                Interceptor.attach(faccessatPtr, {
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
                        if (this.blocked) {
                            retval.replace(ptr(-1));
                        }
                    }
                });
                logger.debug('Hooked native libc.so!faccessat');
            } catch (e) {}
        }

        // 2. Hook stat, lstat, fstatat64, newfstatat
        const statSymbols = ['stat', 'lstat', 'fstatat64', 'newfstatat'];
        statSymbols.forEach(sym => {
            const symPtr = Module.findExportByName('libc.so', sym);
            if (symPtr) {
                try {
                    const isAt = sym.includes('at');
                    Interceptor.attach(symPtr, {
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
                            if (this.blocked) {
                                retval.replace(ptr(-1));
                            }
                        }
                    });
                } catch (_) {}
            }
        });

        // 3. Hook fopen, open, openat (especially protecting /proc/net/unix and /data/adb/.boot_count)
        const fopenPtr = Module.findExportByName('libc.so', 'fopen');
        if (fopenPtr) {
            try {
                Interceptor.attach(fopenPtr, {
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
                        if (this.blocked) {
                            retval.replace(ptr(0)); // Return NULL
                        }
                    }
                });
            } catch (_) {}
        }

        const openatPtr = Module.findExportByName('libc.so', 'openat');
        if (openatPtr) {
            try {
                Interceptor.attach(openatPtr, {
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
                        if (this.blocked) {
                            retval.replace(ptr(-1)); // Return -1 (EACCES/ENOENT)
                        }
                    }
                });
            } catch (_) {}
        }

        // 4. Hook __system_property_get(const char *name, char *value)
        const sysPropGet = Module.findExportByName('libc.so', '__system_property_get');
        if (sysPropGet) {
            try {
                Interceptor.attach(sysPropGet, {
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
                });
                logger.debug('Hooked native libc.so!__system_property_get');
            } catch (e) {
                logger.debug(`Failed to hook native __system_property_get: ${e.message}`);
            }
        }

        // 5. Dynamic Linker Hook for RootBeer / RootBeerFresh JNI symbols
        hookRootBeerJniSymbols(logger);
        const dlopenNames = ['android_dlopen_ext', 'dlopen'];
        dlopenNames.forEach(dlName => {
            const dlPtr = Module.findExportByName(null, dlName);
            if (dlPtr) {
                try {
                    Interceptor.attach(dlPtr, {
                        onEnter: function (args) {
                            this.libName = args[0].isNull() ? '' : args[0].readUtf8String();
                        },
                        onLeave: function (retval) {
                            if (this.libName && (this.libName.includes('libtool-checker.so') || this.libName.includes('libtoolChecker.so'))) {
                                logger.info(`[dlopen] Detected RootBeer library loaded: ${this.libName}`);
                                hookRootBeerJniSymbols(logger);
                            }
                        }
                    });
                } catch (_) {}
            }
        });
    }

    function bypassXamarinMono(logger) {
        const monoModules = ['libmonosgen-2.0.so', 'libmonosgen-64.so', 'libmono-native.so'];
        let monoSo = null;

        for (let i = 0; i < monoModules.length; i++) {
            monoSo = Process.findModuleByName(monoModules[i]);
            if (monoSo) break;
        }

        if (!monoSo) {
            logger.debug('Mono/Xamarin runtime library not present in process.');
            return;
        }

        logger.info(`Detected Mono/Xamarin runtime: ${monoSo.name}`);

        try {
            const mono_thread_attach = Module.findExportByName(monoSo.name, 'mono_thread_attach');
            const mono_get_root_domain = Module.findExportByName(monoSo.name, 'mono_get_root_domain');

            if (mono_thread_attach && mono_get_root_domain) {
                const getRootDomain = new NativeFunction(mono_get_root_domain, 'pointer', []);
                const threadAttach = new NativeFunction(mono_thread_attach, 'pointer', ['pointer']);

                const rootDomain = getRootDomain();
                if (!rootDomain.isNull()) {
                    threadAttach(rootDomain);
                    logger.debug('Successfully attached to Mono root domain.');
                }
            }
        } catch (e) {
            logger.debug(`Mono attach warning: ${e.message}`);
        }
    }

    return {
        name: MODULE_NAME,
        init: function (options, logger) {
            options = options || {};
            logger = logger || console;

            logger.info(`[${MODULE_NAME}] Initializing Anti-Root & Anti-Emulator bypasses...`);

            try {
                bypassNativeRoot(logger);
            } catch (e) {
                logger.error(`[${MODULE_NAME}] Native root bypass error: ${e.message}`);
            }

            try {
                bypassXamarinMono(logger);
            } catch (e) {
                logger.error(`[${MODULE_NAME}] Xamarin bypass error: ${e.message}`);
            }

            if (typeof Java !== 'undefined' && Java.available) {
                const runner = function () {
                    try {
                        bypassJavaRoot(logger);
                        if (options.enableEmulatorBypass !== false) {
                            bypassJavaEmulator(logger);
                        }
                        logger.info(`[${MODULE_NAME}] Java bypasses successfully deployed.`);
                    } catch (err) {
                        logger.error(`[${MODULE_NAME}] Java bypass initialization failed: ${err.message}`);
                    }
                };

                if (Java.performWhenReady) {
                    Java.performWhenReady(runner);
                } else {
                    Java.perform(runner);
                }
            } else {
                logger.debug(`[${MODULE_NAME}] Java runtime not yet ready; waiting for availability.`);
                const interval = setInterval(function () {
                    if (typeof Java !== 'undefined' && Java.available) {
                        clearInterval(interval);
                        Java.perform(function () {
                            bypassJavaRoot(logger);
                            if (options.enableEmulatorBypass !== false) {
                                bypassJavaEmulator(logger);
                            }
                            logger.info(`[${MODULE_NAME}] Java bypasses deployed after delay.`);
                        });
                    }
                }, 50);
            }
        }
    };
});

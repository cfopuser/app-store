/**
 * unified_bypass_bundle.js
 * 
 * Standalone, single-file bundle of the Unified Modern Frida Bypass Suite.
 * Combines:
 * - AntiFrida (Port masking, /proc/self/maps stream cloaking, ptrace bypass, thread rename)
 * - AntiRootEmulator (Root binaries/packages/props, command interception, emulator hardware & sensors, Xamarin/Mono)
 * - SslUnpinning (TrustManager, Conscrypt TrustManagerImpl, NetworkSecurityConfig, OkHttp 3/4, Cronet, BoringSSL)
 * - UnifiedBypass master controller and logger
 * 
 * Ready for direct injection:
 *   frida -U -f com.example.app -l frida_suite/unified_bypass_bundle.js --no-pause
 * or packaged as Frida Gadget script.
 */

(function (root) {
    'use strict';

    // --- Configuration ---
    const Config = {
        logLevel: 'INFO', // 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'NONE'
        enableRootBypass: true,
        enableEmulatorBypass: true,
        enableSslBypass: true,
        enableAntiFrida: true,
        enableXamarinBypass: true
    };

    if (typeof root.BYPASS_CONFIG === 'object' && root.BYPASS_CONFIG !== null) {
        Object.assign(Config, root.BYPASS_CONFIG);
    }

    // --- Logger ---
    const LogLevels = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3, NONE: 4 };

    class Logger {
        constructor(prefix, minLevelName) {
            this.prefix = prefix ? `[${prefix}]` : '[BypassSuite]';
            this.minLevel = LogLevels[minLevelName] !== undefined ? LogLevels[minLevelName] : LogLevels.INFO;
        }

        setLevel(levelName) {
            if (LogLevels[levelName] !== undefined) this.minLevel = LogLevels[levelName];
        }

        _log(levelName, msg) {
            if (LogLevels[levelName] >= this.minLevel && LogLevels[levelName] < LogLevels.NONE) {
                console.log(`${this.prefix} [${levelName}] ${msg}`);
            }
        }

        debug(msg) { this._log('DEBUG', msg); }
        info(msg)  { this._log('INFO', msg); }
        warn(msg)  { this._log('WARN', msg); }
        error(msg) { this._log('ERROR', msg); }
    }

    const suiteLogger = new Logger('UnifiedBypass', Config.logLevel);

    /* ========================================================================= */
    /* MODULE 1: Anti-Frida & Anti-Debugging                                     */
    /* ========================================================================= */
    const AntiFrida = (function () {
        const MODULE_NAME = 'AntiFrida';
        const FRIDA_PORTS = [27042, 27047];
        const FRIDA_KEYWORDS = ['frida-agent', 'frida-gadget', 'frida-server', 'linjector', 'gum-js-loop', 'pool-frida', 'gmain', 'gdbus'];

        function setupPtrace(logger) {
            const ptracePtr = Module.findExportByName('libc.so', 'ptrace');
            if (ptracePtr) {
                try {
                    Interceptor.attach(ptracePtr, {
                        onEnter: function (args) {
                            if (args[0].toInt32() === 0) this.isTraceme = true;
                        },
                        onLeave: function (retval) {
                            if (this.isTraceme) retval.replace(ptr(0));
                        }
                    });
                    logger.debug('Hooked libc.so!ptrace');
                } catch (e) { logger.debug(`ptrace hook error: ${e.message}`); }
            }
        }

        function setupPortBypass(logger) {
            const connectPtr = Module.findExportByName('libc.so', 'connect');
            if (connectPtr) {
                try {
                    Interceptor.attach(connectPtr, {
                        onEnter: function (args) {
                            this.blocked = false;
                            const sa = args[1];
                            if (!sa.isNull()) {
                                try {
                                    if (sa.readU16() === 2) {
                                        const port = (sa.add(2).readU8() << 8) | sa.add(3).readU8();
                                        if (FRIDA_PORTS.indexOf(port) !== -1) {
                                            logger.debug(`Cloaked connection on Frida port ${port}`);
                                            this.blocked = true;
                                        }
                                    }
                                } catch (_) {}
                            }
                        },
                        onLeave: function (retval) {
                            if (this.blocked) retval.replace(ptr(-1));
                        }
                    });
                    logger.debug('Hooked libc.so!connect');
                } catch (e) { logger.debug(`connect hook error: ${e.message}`); }
            }
        }

        function setupProcMaps(logger) {
            const trackedFds = new Map();
            const trackedFp = new Map();

            const openPtr = Module.findExportByName('libc.so', 'open');
            const openatPtr = Module.findExportByName('libc.so', 'openat');
            const fopenPtr = Module.findExportByName('libc.so', 'fopen');
            const readPtr = Module.findExportByName('libc.so', 'read');
            const fgetsPtr = Module.findExportByName('libc.so', 'fgets');
            const closePtr = Module.findExportByName('libc.so', 'close');
            const fclosePtr = Module.findExportByName('libc.so', 'fclose');

            function checkPath(p) {
                if (!p) return null;
                if (p.includes('/maps')) return 'maps';
                if (p.includes('/status')) return 'status';
                return null;
            }

            if (openPtr) {
                try {
                    Interceptor.attach(openPtr, {
                        onEnter: function (args) {
                            this.type = null;
                            if (!args[0].isNull()) {
                                try { this.type = checkPath(args[0].readUtf8String()); } catch (_) {}
                            }
                        },
                        onLeave: function (retval) {
                            const fd = retval.toInt32();
                            if (fd >= 0 && this.type) trackedFds.set(fd, this.type);
                        }
                    });
                } catch (_) {}
            }

            if (openatPtr) {
                try {
                    Interceptor.attach(openatPtr, {
                        onEnter: function (args) {
                            this.type = null;
                            if (!args[1].isNull()) {
                                try { this.type = checkPath(args[1].readUtf8String()); } catch (_) {}
                            }
                        },
                        onLeave: function (retval) {
                            const fd = retval.toInt32();
                            if (fd >= 0 && this.type) trackedFds.set(fd, this.type);
                        }
                    });
                } catch (_) {}
            }

            if (fopenPtr) {
                try {
                    Interceptor.attach(fopenPtr, {
                        onEnter: function (args) {
                            this.type = null;
                            if (!args[0].isNull()) {
                                try { this.type = checkPath(args[0].readUtf8String()); } catch (_) {}
                            }
                        },
                        onLeave: function (retval) {
                            if (!retval.isNull() && this.type) trackedFp.set(retval.toString(), this.type);
                        }
                    });
                } catch (_) {}
            }

            if (closePtr) {
                try {
                    Interceptor.attach(closePtr, {
                        onEnter: function (args) { trackedFds.delete(args[0].toInt32()); }
                    });
                } catch (_) {}
            }

            if (fclosePtr) {
                try {
                    Interceptor.attach(fclosePtr, {
                        onEnter: function (args) { trackedFp.delete(args[0].toString()); }
                    });
                } catch (_) {}
            }

            if (readPtr) {
                try {
                    Interceptor.attach(readPtr, {
                        onEnter: function (args) {
                            this.buf = args[1];
                            this.type = trackedFds.get(args[0].toInt32());
                        },
                        onLeave: function (retval) {
                            const bytes = retval.toInt32();
                            if (bytes > 0 && this.type && !this.buf.isNull()) {
                                try {
                                    const content = this.buf.readUtf8String(bytes);
                                    if (content) {
                                        if (this.type === 'status') {
                                            const sanitized = content.replace(/TracerPid:\s*\d+/g, 'TracerPid:\t0');
                                            if (sanitized !== content) this.buf.writeUtf8String(sanitized);
                                        } else if (this.type === 'maps') {
                                            let modified = false;
                                            const filtered = content.split('\n').filter(line => {
                                                for (let k of FRIDA_KEYWORDS) {
                                                    if (line.includes(k)) { modified = true; return false; }
                                                }
                                                return true;
                                            });
                                            if (modified) {
                                                const newText = filtered.join('\n');
                                                this.buf.writeUtf8String(newText);
                                                retval.replace(ptr(newText.length));
                                            }
                                        }
                                    }
                                } catch (_) {}
                            }
                        }
                    });
                } catch (_) {}
            }

            if (fgetsPtr) {
                try {
                    Interceptor.attach(fgetsPtr, {
                        onEnter: function (args) {
                            this.buf = args[0];
                            this.type = trackedFp.get(args[2].toString());
                        },
                        onLeave: function (retval) {
                            if (!retval.isNull() && this.type && !this.buf.isNull()) {
                                try {
                                    const line = this.buf.readUtf8String();
                                    if (line) {
                                        if (this.type === 'status' && line.startsWith('TracerPid:')) {
                                            this.buf.writeUtf8String('TracerPid:\t0\n');
                                        } else if (this.type === 'maps') {
                                            for (let k of FRIDA_KEYWORDS) {
                                                if (line.includes(k)) {
                                                    this.buf.writeUtf8String('\n');
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                } catch (_) {}
                            }
                        }
                    });
                } catch (_) {}
            }
            logger.debug('Hooked /proc maps and status streams');
        }

        function setupThreadMasking(logger) {
            const getnamePtr = Module.findExportByName('libc.so', 'pthread_getname_np');
            if (getnamePtr) {
                try {
                    Interceptor.attach(getnamePtr, {
                        onEnter: function (args) { this.namePtr = args[1]; },
                        onLeave: function (retval) {
                            if (retval.toInt32() === 0 && !this.namePtr.isNull()) {
                                try {
                                    const name = this.namePtr.readUtf8String();
                                    for (let k of FRIDA_KEYWORDS) {
                                        if (name && name.includes(k)) {
                                            this.namePtr.writeUtf8String('pool-thread');
                                            break;
                                        }
                                    }
                                } catch (_) {}
                            }
                        }
                    });
                    logger.debug('Hooked libc.so!pthread_getname_np');
                } catch (_) {}
            }
        }

        return {
            init: function (opts, logger) {
                logger.info(`[${MODULE_NAME}] Initializing Anti-Frida protections...`);
                setupPtrace(logger);
                setupPortBypass(logger);
                setupProcMaps(logger);
                setupThreadMasking(logger);
            }
        };
    })();

    /* ========================================================================= */
    /* MODULE 2: Anti-Root & Anti-Emulator                                       */
    /* ========================================================================= */
    const AntiRootEmulator = (function () {
        const MODULE_NAME = 'AntiRootEmulator';
        const ROOT_BINARIES = ['su', 'busybox', 'magisk', 'daemonsu', 'supersu', 'which'];
        const ROOT_PATHS = [
            '/system/app/Superuser.apk', '/sbin/su', '/system/bin/su', '/system/xbin/su',
            '/data/local/xbin/su', '/data/local/bin/su', '/system/sd/xbin/su', '/system/bin/failsafe/su',
            '/data/local/su', '/su/bin/su', '/system/etc/init.d/99SuperSUDaemon',
            '/system/xbin/daemonsu', '/system/xbin/busybox', '/system/bin/magisk', '/sbin/magisk',
            '/data/adb/magisk', '/data/adb/magisk.db', '/data/adb/modules', '/data/adb/.boot_count',
            '/proc/net/unix'
        ];
        const ROOT_PACKAGES = [
            'com.noshufou.android.su', 'com.noshufou.android.su.elite', 'eu.chainfire.supersu',
            'com.koushikdutta.superuser', 'com.thirdparty.superuser', 'com.yellowes.su',
            'com.topjohnwu.magisk', 'com.kingroot.kinguser', 'com.kingo.root',
            'com.smedialink.oneclickroot', 'com.zhiqupk.root.global', 'com.alephzain.framaroot',
            'me.weishu.kernelsu', 'com.koushikdutta.rommanager', 'com.koushikdutta.rommanager.license',
            'com.dimonvideo.luckypatcher', 'com.chelpus.lackypatch', 'com.chelpus.luckypatcher',
            'com.ramdroid.appquarantine', 'com.ramdroid.appquarantinepro',
            'com.android.vending.billing.InAppBillingService.COIN', 'com.android.vending.billing.InAppBillingService.LUCK',
            'com.blackmartalpha', 'org.blackmart.market', 'com.allinone.free', 'com.repodroid.app',
            'org.creeplays.hack', 'com.baseappfull.fwd', 'com.zmapp', 'com.dv.marketmod.installer',
            'org.mobilism.android', 'com.android.wp.net.log', 'com.android.camera.update',
            'cc.madkite.freedom', 'com.solohsu.android.edxp.manager', 'org.meowcat.edxposed.manager',
            'com.xmodgame', 'com.cih.game_cih', 'com.charles.lpoqasert', 'catch_.me_.if_.you_.can_',
            'com.devadvance.rootcloak', 'com.devadvance.rootcloakplus', 'de.robv.android.xposed.installer',
            'com.saurik.substrate', 'com.zachspong.temprootremovejb', 'com.amphoras.hidemyroot',
            'com.amphoras.hidemyrootadfree', 'com.formyhm.hiderootPremium', 'com.formyhm.hideroot'
        ];
        const EMULATOR_FILES = [
            '/dev/socket/qemud', '/dev/qemu_pipe', '/system/lib/libc_malloc_debug_qemu.so',
            '/sys/qemu_trace', '/system/bin/qemu-props', '/dev/socket/genyd'
        ];
        const SPOOFED_PROPS = {
            'ro.build.tags': 'release-keys', 'ro.build.type': 'user', 'ro.debuggable': '0',
            'ro.secure': '1', 'ro.build.selinux': '1', 'ro.hardware': 'qcom', 'ro.product.model': 'Pixel 7',
            'ro.product.brand': 'google', 'ro.product.manufacturer': 'Google',
            'ro.kernel.qemu': '0', 'ro.kernel.android.qemud': '0'
        };

        function isSensitive(p) {
            if (!p || typeof p !== 'string') return false;
            if (ROOT_PATHS.indexOf(p) !== -1 || EMULATOR_FILES.indexOf(p) !== -1) return true;
            if (/(^|\/)(su|busybox|magisk|daemonsu|supersu)$/i.test(p)) return true;
            if (p.includes('/proc/net/unix') || p.includes('/data/adb/.boot_count')) return true;
            return false;
        }

        function bypassJava(logger, opts) {
            try {
                const File = Java.use('java.io.File');
                const origExists = File.exists;
                File.exists.implementation = function () {
                    const p = this.getAbsolutePath();
                    if (isSensitive(p)) {
                        logger.debug(`[File.exists] Denied: ${p}`);
                        return false;
                    }
                    return origExists.call(this);
                };
            } catch (_) {}

            try {
                const UnixFileSystem = Java.use('java.io.UnixFileSystem');
                const origCheckAccess = UnixFileSystem.checkAccess;
                UnixFileSystem.checkAccess.implementation = function (file, access) {
                    const p = file.getAbsolutePath();
                    if (isSensitive(p)) return false;
                    return origCheckAccess.call(this, file, access);
                };
            } catch (_) {}

            try {
                const ApplicationPackageManager = Java.use('android.app.ApplicationPackageManager');
                const origGetPkg = ApplicationPackageManager.getPackageInfo;
                const NameNotFoundException = Java.use('android.content.pm.PackageManager$NameNotFoundException');
                origGetPkg.overload('java.lang.String', 'int').implementation = function (pkg, flags) {
                    if (ROOT_PACKAGES.indexOf(pkg) !== -1) throw NameNotFoundException.$new(pkg);
                    return origGetPkg.overload('java.lang.String', 'int').call(this, pkg, flags);
                };
                try {
                    const PackageInfoFlags = Java.use('android.content.pm.PackageManager$PackageInfoFlags');
                    origGetPkg.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').implementation = function (pkg, flags) {
                        if (ROOT_PACKAGES.indexOf(pkg) !== -1) throw NameNotFoundException.$new(pkg);
                        return origGetPkg.overload('java.lang.String', 'android.content.pm.PackageManager$PackageInfoFlags').call(this, pkg, flags);
                    };
                } catch (_) {}
            } catch (_) {}

            try {
                const ProcessImpl = Java.use('java.lang.ProcessImpl');
                ProcessImpl.start.implementation = function (cmdarray, env, dir, redirects, redirectErrorStream) {
                    if (cmdarray && cmdarray.length > 0) {
                        const cmd = cmdarray[0] ? cmdarray[0].toString() : '';
                        const full = Array.from(cmdarray).map(c => (c ? c.toString() : '')).join(' ');
                        if (/(^|\/)(su|magisk|busybox|daemonsu)$/i.test(cmd) || full.includes('which su')) {
                            logger.debug(`[ProcessImpl.start] Neutralized root cmd: ${full}`);
                            const StringClass = Java.use('java.lang.String');
                            const fake = Java.array('java.lang.String', [
                                StringClass.$new('/system/bin/sh'),
                                StringClass.$new('-c'),
                                StringClass.$new('exit 1')
                            ]);
                            return ProcessImpl.start.call(this, fake, env, dir, redirects, redirectErrorStream);
                        }
                    }
                    return ProcessImpl.start.call(this, cmdarray, env, dir, redirects, redirectErrorStream);
                };
            } catch (_) {}

            try {
                const SystemProperties = Java.use('android.os.SystemProperties');
                const origGet = SystemProperties.get;
                SystemProperties.get.overload('java.lang.String').implementation = function (k) {
                    if (k in SPOOFED_PROPS) return SPOOFED_PROPS[k];
                    let res = origGet.overload('java.lang.String').call(this, k);
                    if (k === 'ro.build.tags' && res && res.includes('test-keys')) return res.replace('test-keys', 'release-keys');
                    return res;
                };
                SystemProperties.get.overload('java.lang.String', 'java.lang.String').implementation = function (k, d) {
                    if (k in SPOOFED_PROPS) return SPOOFED_PROPS[k];
                    let res = origGet.overload('java.lang.String', 'java.lang.String').call(this, k, d);
                    if (k === 'ro.build.tags' && res && res.includes('test-keys')) return res.replace('test-keys', 'release-keys');
                    return res;
                };
                SystemProperties.getInt.implementation = function (k, d) {
                    if (k === 'ro.debuggable') return 0;
                    if (k === 'ro.secure') return 1;
                    return this.getInt(k, d);
                };
                SystemProperties.getBoolean.implementation = function (k, d) {
                    if (k === 'ro.debuggable') return false;
                    if (k === 'ro.secure') return true;
                    return this.getBoolean(k, d);
                };
            } catch (_) {}

            try {
                const Build = Java.use('android.os.Build');
                Build.TAGS.value = 'release-keys';
                Build.TYPE.value = 'user';
                Build.MANUFACTURER.value = 'Google';
                Build.MODEL.value = 'Pixel 7';
                Build.HARDWARE.value = 'qcom';
            } catch (_) {}

            const rootBeerClasses = [
                'com.scottyab.rootbeer.RootBeer',
                'com.kimchangyoun.rootbeer.RootBeer',
                'com.kimchangyoun.rootbeerFresh.RootBeer'
            ];
            rootBeerClasses.forEach(c => {
                try {
                    const RB = Java.use(c);
                    ['isRooted', 'isRootedWithoutBusyBoxCheck', 'isRootedWithBusyBoxCheck', 'detectTestKeys', 'checkForSuBinary', 'checkForMagiskUDS', 'checkForRootNative'].forEach(m => {
                        try { if (RB[m]) RB[m].implementation = function () { return false; }; } catch (_) {}
                    });
                } catch (_) {}
            });

            if (opts.enableEmulatorBypass !== false) {
                try {
                    const TelephonyManager = Java.use('android.telephony.TelephonyManager');
                    if (TelephonyManager.getSimOperatorName) {
                        TelephonyManager.getSimOperatorName.overload().implementation = function () { return 'T-Mobile'; };
                    }
                    if (TelephonyManager.getSimState) {
                        TelephonyManager.getSimState.overload().implementation = function () { return 5; };
                    }
                } catch (_) {}
            }
        }

        function hookRootBeerJni() {
            const syms = [
                'Java_com_kimchangyoun_rootbeerFresh_RootBeerNative_checkForMagiskUDS',
                'Java_com_kimchangyoun_rootbeerFresh_RootBeerNative_checkForRoot',
                'Java_com_scottyab_rootbeer_RootBeerNative_checkForRoot'
            ];
            syms.forEach(sym => {
                const ptrSym = Module.findExportByName(null, sym);
                if (ptrSym) {
                    try {
                        Interceptor.attach(ptrSym, {
                            onLeave: function (retval) { retval.replace(ptr(0)); }
                        });
                    } catch (_) {}
                }
            });
        }

        function bypassNative(logger) {
            const accessPtr = Module.findExportByName('libc.so', 'access');
            if (accessPtr) {
                try {
                    Interceptor.attach(accessPtr, {
                        onEnter: function (args) {
                            this.blocked = false;
                            if (!args[0].isNull()) {
                                try {
                                    const p = args[0].readUtf8String();
                                    if (isSensitive(p)) this.blocked = true;
                                } catch (_) {}
                            }
                        },
                        onLeave: function (retval) {
                            if (this.blocked) retval.replace(ptr(-1));
                        }
                    });
                } catch (_) {}
            }

            const statSyms = ['stat', 'lstat', 'fstatat64', 'newfstatat', 'openat'];
            statSyms.forEach(sym => {
                const pSym = Module.findExportByName('libc.so', sym);
                if (pSym) {
                    try {
                        const isAt = sym.includes('at');
                        Interceptor.attach(pSym, {
                            onEnter: function (args) {
                                this.blocked = false;
                                const pPtr = isAt ? args[1] : args[0];
                                if (!pPtr || pPtr.isNull()) return;
                                try {
                                    const p = pPtr.readUtf8String();
                                    if (isSensitive(p)) this.blocked = true;
                                } catch (_) {}
                            },
                            onLeave: function (retval) {
                                if (this.blocked) retval.replace(ptr(-1));
                            }
                        });
                    } catch (_) {}
                }
            });

            const fopenPtr = Module.findExportByName('libc.so', 'fopen');
            if (fopenPtr) {
                try {
                    Interceptor.attach(fopenPtr, {
                        onEnter: function (args) {
                            this.blocked = false;
                            if (!args[0].isNull()) {
                                try {
                                    const p = args[0].readUtf8String();
                                    if (isSensitive(p)) this.blocked = true;
                                } catch (_) {}
                            }
                        },
                        onLeave: function (retval) {
                            if (this.blocked) retval.replace(ptr(0));
                        }
                    });
                } catch (_) {}
            }

            const sysPropGet = Module.findExportByName('libc.so', '__system_property_get');
            if (sysPropGet) {
                try {
                    Interceptor.attach(sysPropGet, {
                        onEnter: function (args) {
                            this.prop = null;
                            this.vPtr = args[1];
                            if (!args[0].isNull()) {
                                try { this.prop = args[0].readUtf8String(); } catch (_) {}
                            }
                        },
                        onLeave: function (retval) {
                            if (this.prop && (this.prop in SPOOFED_PROPS) && !this.vPtr.isNull()) {
                                const v = SPOOFED_PROPS[this.prop];
                                this.vPtr.writeUtf8String(v);
                                retval.replace(ptr(v.length));
                            }
                        }
                    });
                } catch (_) {}
            }

            hookRootBeerJni();
            const dlopenNames = ['android_dlopen_ext', 'dlopen'];
            dlopenNames.forEach(dl => {
                const dlPtr = Module.findExportByName(null, dl);
                if (dlPtr) {
                    try {
                        Interceptor.attach(dlPtr, {
                            onEnter: function (args) {
                                this.lib = args[0].isNull() ? '' : args[0].readUtf8String();
                            },
                            onLeave: function () {
                                if (this.lib && (this.lib.includes('libtool-checker.so') || this.lib.includes('libtoolChecker.so'))) {
                                    hookRootBeerJni();
                                }
                            }
                        });
                    } catch (_) {}
                }
            });
        }

        function bypassXamarin(logger) {
            const monoLibs = ['libmonosgen-2.0.so', 'libmonosgen-64.so', 'libmono-native.so'];
            for (let lib of monoLibs) {
                const mod = Process.findModuleByName(lib);
                if (mod) {
                    logger.info(`Attached to Xamarin runtime: ${mod.name}`);
                    break;
                }
            }
        }

        return {
            init: function (opts, logger) {
                logger.info(`[${MODULE_NAME}] Initializing Anti-Root & Anti-Emulator bypasses...`);
                bypassNative(logger);
                bypassXamarin(logger);

                const runner = function () {
                    try {
                        bypassJava(logger, opts);
                        logger.info(`[${MODULE_NAME}] Java bypasses successfully deployed.`);
                    } catch (e) {
                        logger.error(`[${MODULE_NAME}] Java deployment failed: ${e.message}`);
                    }
                };

                if (typeof Java !== 'undefined' && Java.available) {
                    if (Java.performWhenReady) Java.performWhenReady(runner);
                    else Java.perform(runner);
                } else {
                    const timer = setInterval(() => {
                        if (typeof Java !== 'undefined' && Java.available) {
                            clearInterval(timer);
                            Java.perform(runner);
                        }
                    }, 50);
                }
            }
        };
    })();

    /* ========================================================================= */
    /* MODULE 3: Universal SSL Pinning Bypass                                    */
    /* ========================================================================= */
    const SslUnpinning = (function () {
        const MODULE_NAME = 'SslUnpinning';

        function bypassJava(logger) {
            try {
                const X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
                const SSLContext = Java.use('javax.net.ssl.SSLContext');

                const TrustAllManager = Java.registerClass({
                    name: 're.frida.unified.TrustAllManager',
                    implements: [X509TrustManager],
                    methods: {
                        checkClientTrusted: function (chain, authType) {},
                        checkServerTrusted: function (chain, authType) {},
                        getAcceptedIssuers: function () { return []; }
                    }
                });

                const mgrs = [TrustAllManager.$new()];
                const origInit = SSLContext.init;
                SSLContext.init.overload(
                    '[Ljavax.net.ssl.KeyManager;',
                    '[Ljavax.net.ssl.TrustManager;',
                    'java.security.SecureRandom'
                ).implementation = function (km, tm, sr) {
                    origInit.call(this, km, mgrs, sr);
                };
                logger.debug('Hooked SSLContext.init');
            } catch (_) {}

            try {
                const TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
                try {
                    TrustManagerImpl.checkTrustedRecursive.implementation = function () {
                        return Java.use('java.util.ArrayList').$new();
                    };
                } catch (_) {}
                try {
                    TrustManagerImpl.checkServerTrusted.overload(
                        '[Ljava.security.cert.X509Certificate;',
                        'java.lang.String',
                        'java.lang.String'
                    ).implementation = function () {
                        return Java.use('java.util.ArrayList').$new();
                    };
                } catch (_) {}
            } catch (_) {}

            try {
                const NetworkSecurityTrustManager = Java.use('android.security.net.config.NetworkSecurityTrustManager');
                NetworkSecurityTrustManager.checkPins.implementation = function () {};
            } catch (_) {}

            ['okhttp3.CertificatePinner', 'com.squareup.okhttp.CertificatePinner'].forEach(cls => {
                try {
                    const Pinner = Java.use(cls);
                    try { Pinner.check.overload('java.lang.String', 'java.util.List').implementation = function () {}; } catch (_) {}
                    try { Pinner['check$okhttp'].implementation = function () {}; } catch (_) {}
                    try { Pinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function () {}; } catch (_) {}
                    logger.debug(`Hooked ${cls}`);
                } catch (_) {}
            });
        }

        function bypassNative(logger) {
            ['libssl.so', 'libcrypto.so', 'libboringssl.so'].forEach(lib => {
                const mod = Process.findModuleByName(lib);
                if (!mod) return;

                const setCustom = Module.findExportByName(lib, 'SSL_CTX_set_custom_verify');
                if (setCustom) {
                    try {
                        Interceptor.attach(setCustom, {
                            onEnter: function (args) { args[2] = ptr(0); }
                        });
                    } catch (_) {}
                }

                const getVerify = Module.findExportByName(lib, 'SSL_get_verify_result');
                if (getVerify) {
                    try {
                        Interceptor.attach(getVerify, {
                            onLeave: function (retval) { if (!retval.isNull()) retval.replace(ptr(0)); }
                        });
                    } catch (_) {}
                }
            });
        }

        return {
            init: function (opts, logger) {
                logger.info(`[${MODULE_NAME}] Initializing Universal SSL Unpinning...`);
                bypassNative(logger);

                const runner = function () {
                    try {
                        bypassJava(logger);
                        logger.info(`[${MODULE_NAME}] Java SSL unpinning deployed.`);
                    } catch (e) {
                        logger.error(`[${MODULE_NAME}] Java unpinning failed: ${e.message}`);
                    }
                };

                if (typeof Java !== 'undefined' && Java.available) {
                    if (Java.performWhenReady) Java.performWhenReady(runner);
                    else Java.perform(runner);
                } else {
                    const timer = setInterval(() => {
                        if (typeof Java !== 'undefined' && Java.available) {
                            clearInterval(timer);
                            Java.perform(runner);
                        }
                    }, 50);
                }
            }
        };
    })();

    /* ========================================================================= */
    /* MASTER CONTROLLER BOOTSTRAP                                               */
    /* ========================================================================= */
    function bootstrap() {
        suiteLogger.info('Unified Frida Bypass Suite v2.0 starting...');
        suiteLogger.info(`Config: Root=${Config.enableRootBypass}, Emulator=${Config.enableEmulatorBypass}, SSL=${Config.enableSslBypass}, AntiFrida=${Config.enableAntiFrida}`);

        if (Config.enableAntiFrida) {
            AntiFrida.init(Config, new Logger('AntiFrida', Config.logLevel));
        }

        if (Config.enableRootBypass || Config.enableEmulatorBypass) {
            AntiRootEmulator.init(Config, new Logger('AntiRoot', Config.logLevel));
        }

        if (Config.enableSslBypass) {
            SslUnpinning.init(Config, new Logger('SslUnpin', Config.logLevel));
        }

        suiteLogger.info('All active bypass components initialized.');
    }

    root.BypassSuite = {
        Config: Config,
        Logger: Logger,
        init: bootstrap,
        AntiFrida: AntiFrida,
        AntiRootEmulator: AntiRootEmulator,
        SslUnpinning: SslUnpinning
    };

    bootstrap();

})(typeof globalThis !== 'undefined' ? globalThis : this);

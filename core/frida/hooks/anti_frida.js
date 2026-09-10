/**
 * anti_frida.js
 * 
 * Core Frida Module: Anti-Frida & Anti-Debugging Bypass.
 * Stage: Native (Runs synchronously during initial process load)
 * 
 * Capabilities:
 * 1. ptrace anti-debugging (PTRACE_TRACEME, PT_DENY_ATTACH)
 * 2. Port scanning interception (Frida server ports 27042, 27047, or custom)
 * 3. /proc/self/maps and /proc/self/status inspection tampering (virtualized stream filtering)
 * 4. Thread enumeration and name masking (gmain, gdbus, gum-js-loop)
 */

(function (root) {
    'use strict';

    const MODULE_NAME = 'anti_frida';

    const DEFAULT_PORTS = [27042, 27047];
    const FRIDA_KEYWORDS = [
        'frida-agent',
        'frida-gadget',
        'frida-server',
        'linjector',
        'gum-js-loop',
        'pool-frida',
        'gmain',
        'gdbus'
    ];

    function setupPtraceBypass(logger, safeUtils) {
        safeUtils.safeAttachNative('libc.so', 'ptrace', {
            onEnter: function (args) {
                const request = args[0].toInt32();
                // PTRACE_TRACEME = 0
                if (request === 0) {
                    this.isTraceme = true;
                    logger.debug('[ptrace] Neutralizing PTRACE_TRACEME (0)');
                }
            },
            onLeave: function (retval) {
                if (this.isTraceme) {
                    retval.replace(ptr(0)); // Return success (0)
                }
            }
        }, logger);
    }

    function setupPortBypass(ports, logger, safeUtils) {
        const portList = Array.isArray(ports) ? ports : DEFAULT_PORTS;
        safeUtils.safeAttachNative('libc.so', 'connect', {
            onEnter: function (args) {
                this.blocked = false;
                const sockaddrPtr = args[1];
                if (sockaddrPtr.isNull()) return;

                try {
                    const family = sockaddrPtr.readU16();
                    // AF_INET = 2
                    if (family === 2) {
                        // Port is in network byte order (big endian) at offset 2
                        const portHigh = sockaddrPtr.add(2).readU8();
                        const portLow = sockaddrPtr.add(3).readU8();
                        const port = (portHigh << 8) | portLow;

                        if (portList.indexOf(port) !== -1) {
                            logger.debug(`[connect] Intercepted port probe on Frida port ${port}`);
                            this.blocked = true;
                        }
                    }
                } catch (_) {}
            },
            onLeave: function (retval) {
                if (this.blocked) {
                    // Return -1 with ECONNREFUSED (111)
                    retval.replace(ptr(-1));
                }
            }
        }, logger);
    }

    function setupProcMapsBypass(logger) {
        const trackedFds = new Map(); // fd -> 'maps' | 'status'
        const trackedFp = new Map();  // FILE* -> 'maps' | 'status'

        const openPtr = Module.findExportByName('libc.so', 'open');
        const openatPtr = Module.findExportByName('libc.so', 'openat');
        const fopenPtr = Module.findExportByName('libc.so', 'fopen');
        const readPtr = Module.findExportByName('libc.so', 'read');
        const fgetsPtr = Module.findExportByName('libc.so', 'fgets');
        const closePtr = Module.findExportByName('libc.so', 'close');
        const fclosePtr = Module.findExportByName('libc.so', 'fclose');

        function checkPath(pathStr) {
            if (!pathStr) return null;
            if (pathStr.includes('/maps')) return 'maps';
            if (pathStr.includes('/status')) return 'status';
            return null;
        }

        if (openPtr) {
            try {
                Interceptor.attach(openPtr, {
                    onEnter: function (args) {
                        this.pathType = null;
                        if (args[0].isNull()) return;
                        try {
                            const p = args[0].readUtf8String();
                            this.pathType = checkPath(p);
                        } catch (_) {}
                    },
                    onLeave: function (retval) {
                        const fd = retval.toInt32();
                        if (fd >= 0 && this.pathType) {
                            trackedFds.set(fd, this.pathType);
                            logger.debug(`[open] Tracking fd ${fd} -> ${this.pathType}`);
                        }
                    }
                });
            } catch (_) {}
        }

        if (openatPtr) {
            try {
                Interceptor.attach(openatPtr, {
                    onEnter: function (args) {
                        this.pathType = null;
                        if (args[1].isNull()) return;
                        try {
                            const p = args[1].readUtf8String();
                            this.pathType = checkPath(p);
                        } catch (_) {}
                    },
                    onLeave: function (retval) {
                        const fd = retval.toInt32();
                        if (fd >= 0 && this.pathType) {
                            trackedFds.set(fd, this.pathType);
                            logger.debug(`[openat] Tracking fd ${fd} -> ${this.pathType}`);
                        }
                    }
                });
            } catch (_) {}
        }

        if (fopenPtr) {
            try {
                Interceptor.attach(fopenPtr, {
                    onEnter: function (args) {
                        this.pathType = null;
                        if (args[0].isNull()) return;
                        try {
                            const p = args[0].readUtf8String();
                            this.pathType = checkPath(p);
                        } catch (_) {}
                    },
                    onLeave: function (retval) {
                        if (!retval.isNull() && this.pathType) {
                            trackedFp.set(retval.toString(), this.pathType);
                            logger.debug(`[fopen] Tracking fp ${retval} -> ${this.pathType}`);
                        }
                    }
                });
            } catch (_) {}
        }

        if (closePtr) {
            try {
                Interceptor.attach(closePtr, {
                    onEnter: function (args) {
                        const fd = args[0].toInt32();
                        if (trackedFds.has(fd)) {
                            trackedFds.delete(fd);
                        }
                    }
                });
            } catch (_) {}
        }

        if (fclosePtr) {
            try {
                Interceptor.attach(fclosePtr, {
                    onEnter: function (args) {
                        const key = args[0].toString();
                        if (trackedFp.has(key)) {
                            trackedFp.delete(key);
                        }
                    }
                });
            } catch (_) {}
        }

        if (readPtr) {
            try {
                Interceptor.attach(readPtr, {
                    onEnter: function (args) {
                        this.fd = args[0].toInt32();
                        this.buf = args[1];
                        this.type = trackedFds.get(this.fd);
                    },
                    onLeave: function (retval) {
                        const bytesRead = retval.toInt32();
                        if (bytesRead > 0 && this.type && !this.buf.isNull()) {
                            try {
                                const content = this.buf.readUtf8String(bytesRead);
                                if (!content) return;

                                if (this.type === 'status') {
                                    const sanitized = content.replace(/TracerPid:\s*\d+/g, 'TracerPid:\t0');
                                    if (sanitized !== content) {
                                        this.buf.writeUtf8String(sanitized);
                                        logger.debug('[read] Concealed TracerPid in /proc/self/status');
                                    }
                                } else if (this.type === 'maps') {
                                    const lines = content.split('\n');
                                    let modified = false;
                                    const filtered = lines.filter(line => {
                                        for (let i = 0; i < FRIDA_KEYWORDS.length; i++) {
                                            if (line.includes(FRIDA_KEYWORDS[i])) {
                                                modified = true;
                                                return false;
                                            }
                                        }
                                        return true;
                                    });

                                    if (modified) {
                                        const newContent = filtered.join('\n');
                                        this.buf.writeUtf8String(newContent);
                                        retval.replace(ptr(newContent.length));
                                        logger.debug('[read] Cloaked Frida entries in /proc/*/maps');
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
                        this.fpKey = args[2].toString();
                        this.type = trackedFp.get(this.fpKey);
                    },
                    onLeave: function (retval) {
                        if (!retval.isNull() && this.type && !this.buf.isNull()) {
                            try {
                                const line = this.buf.readUtf8String();
                                if (!line) return;

                                if (this.type === 'status') {
                                    if (line.startsWith('TracerPid:')) {
                                        this.buf.writeUtf8String('TracerPid:\t0\n');
                                        logger.debug('[fgets] Concealed TracerPid');
                                    }
                                } else if (this.type === 'maps') {
                                    for (let i = 0; i < FRIDA_KEYWORDS.length; i++) {
                                        if (line.includes(FRIDA_KEYWORDS[i])) {
                                            this.buf.writeUtf8String('\n');
                                            logger.debug(`[fgets] Masked line containing ${FRIDA_KEYWORDS[i]}`);
                                            break;
                                        }
                                    }
                                }
                            } catch (_) {}
                        }
                    }
                });
            } catch (_) {}
        }

        logger.debug('Configured /proc/self/maps & status stream cloaking');
    }

    function setupThreadMasking(logger, safeUtils) {
        safeUtils.safeAttachNative('libc.so', 'pthread_getname_np', {
            onEnter: function (args) {
                this.namePtr = args[1];
                this.len = args[2].toInt32();
            },
            onLeave: function (retval) {
                if (retval.toInt32() === 0 && !this.namePtr.isNull()) {
                    try {
                        const threadName = this.namePtr.readUtf8String();
                        for (let i = 0; i < FRIDA_KEYWORDS.length; i++) {
                            if (threadName && threadName.includes(FRIDA_KEYWORDS[i])) {
                                this.namePtr.writeUtf8String('pool-thread');
                                logger.debug(`[pthread_getname_np] Masked thread name: ${threadName} -> pool-thread`);
                                break;
                            }
                        }
                    } catch (_) {}
                }
            }
        }, logger);
    }

    const HookModule = {
        name: MODULE_NAME,
        description: 'Anti-Frida & Anti-Debugging native cloaking',
        stage: 'native',
        defaultEnabled: true,

        initNative: function (config, context) {
            const logger = context.logger || console;
            const safeUtils = context.safeUtils;

            logger.info('Initializing Anti-Frida & Anti-Debug native bypasses...');

            if (config.bypass_ptrace !== false) {
                setupPtraceBypass(logger, safeUtils);
            }

            if (config.cloak_ports !== false) {
                setupPortBypass(config.block_ports, logger, safeUtils);
            }

            if (config.cloak_proc_maps !== false) {
                setupProcMapsBypass(logger);
            }

            if (config.mask_threads !== false) {
                setupThreadMasking(logger, safeUtils);
            }

            logger.info('Anti-Frida protection layers active.');
        }
    };

    if (root.__FRIDA_CORE__) {
        root.__FRIDA_CORE__.register(HookModule);
    }

})(typeof globalThis !== 'undefined' ? globalThis : this);

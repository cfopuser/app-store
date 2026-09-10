/**
 * anti_frida.js
 * 
 * Production-grade Anti-Frida & Anti-Debugging Bypass.
 * Covers:
 * 1. ptrace anti-debugging (PTRACE_TRACEME, PT_DENY_ATTACH)
 * 2. Port scanning interception (Frida server ports 27042, 27047)
 * 3. /proc/self/maps and /proc/self/status inspection tampering (virtualized stream filtering)
 * 4. Thread enumeration and name masking (gmain, gdbus, gum-js-loop)
 */

(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.AntiFrida = factory();
    }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    const MODULE_NAME = 'AntiFrida';

    const FRIDA_PORTS = [27042, 27047];
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

    function setupPtraceBypass(logger) {
        const ptracePtr = Module.findExportByName('libc.so', 'ptrace');
        if (!ptracePtr) {
            logger.debug('ptrace export not found in libc.so');
            return;
        }

        try {
            Interceptor.attach(ptracePtr, {
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
            });
            logger.debug('Hooked native libc.so!ptrace');
        } catch (e) {
            logger.debug(`Failed to hook ptrace: ${e.message}`);
        }
    }

    function setupPortBypass(logger) {
        // Intercept connect() socket calls
        const connectPtr = Module.findExportByName('libc.so', 'connect');
        if (!connectPtr) return;

        try {
            Interceptor.attach(connectPtr, {
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

                            if (FRIDA_PORTS.indexOf(port) !== -1) {
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
            });
            logger.debug('Hooked native libc.so!connect (Frida port cloak)');
        } catch (e) {
            logger.debug(`Failed to hook connect: ${e.message}`);
        }
    }

    function setupProcMapsBypass(logger) {
        // Track open file descriptors pointing to /proc/*/maps or status
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

        // 1. open(path, flags, mode)
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

        // 2. openat(dirfd, path, flags, mode)
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

        // 3. fopen(path, mode)
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

        // 4. close & fclose cleanup
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

        // 5. read(fd, buf, count)
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
                                    // Replace TracerPid: <pid> with TracerPid:\t0
                                    const sanitized = content.replace(/TracerPid:\s*\d+/g, 'TracerPid:\t0');
                                    if (sanitized !== content) {
                                        this.buf.writeUtf8String(sanitized);
                                        logger.debug('[read] Concealed TracerPid in /proc/self/status');
                                    }
                                } else if (this.type === 'maps') {
                                    // Sanitize Frida lines from maps
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

        // 6. fgets(buf, size, fp)
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
                                            // Empty line or replace with benign libc mapping
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

    function setupThreadMasking(logger) {
        // Intercept pthread_getname_np(pthread_t thread, char *name, size_t len)
        const getnamePtr = Module.findExportByName('libc.so', 'pthread_getname_np');
        if (getnamePtr) {
            try {
                Interceptor.attach(getnamePtr, {
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
                });
                logger.debug('Hooked native libc.so!pthread_getname_np');
            } catch (e) {
                logger.debug(`Failed to hook pthread_getname_np: ${e.message}`);
            }
        }
    }

    return {
        name: MODULE_NAME,
        init: function (options, logger) {
            options = options || {};
            logger = logger || console;

            logger.info(`[${MODULE_NAME}] Initializing Anti-Frida & Anti-Debug bypasses...`);

            try {
                setupPtraceBypass(logger);
            } catch (e) {
                logger.error(`[${MODULE_NAME}] ptrace bypass error: ${e.message}`);
            }

            try {
                setupPortBypass(logger);
            } catch (e) {
                logger.error(`[${MODULE_NAME}] Port bypass error: ${e.message}`);
            }

            try {
                setupProcMapsBypass(logger);
            } catch (e) {
                logger.error(`[${MODULE_NAME}] /proc maps & status cloak error: ${e.message}`);
            }

            try {
                setupThreadMasking(logger);
            } catch (e) {
                logger.error(`[${MODULE_NAME}] Thread masking error: ${e.message}`);
            }

            logger.info(`[${MODULE_NAME}] Anti-Frida protection layers active.`);
        }
    };
});

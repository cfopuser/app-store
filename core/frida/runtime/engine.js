/**
 * engine.js
 * 
 * Central Frida Core Hooks Engine (frida-hooks-core) Micro-Kernel.
 * Manages hook module registration, lifecycle staging (native -> Java -> custom),
 * structured logging, and defensive error boundaries.
 */

(function (root) {
    'use strict';

    // Prevent duplicate engine initialization
    if (root.__FRIDA_CORE__ && root.__FRIDA_CORE__.initialized) {
        return;
    }

    // --- 1. Structured Logging Utility ---
    const LogLevels = {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3,
        NONE: 4
    };

    class Logger {
        constructor(prefix, minLevelName) {
            this.prefix = prefix ? `[${prefix}]` : '[FridaCore]';
            const levelUpper = (typeof minLevelName === 'string' ? minLevelName.toUpperCase() : 'INFO');
            this.minLevel = LogLevels[levelUpper] !== undefined ? LogLevels[levelUpper] : LogLevels.INFO;
        }

        setLevel(levelName) {
            const levelUpper = (typeof levelName === 'string' ? levelName.toUpperCase() : 'INFO');
            if (LogLevels[levelUpper] !== undefined) {
                this.minLevel = LogLevels[levelUpper];
            }
        }

        _log(levelName, msg, err) {
            const lvl = LogLevels[levelName];
            if (lvl >= this.minLevel && lvl < LogLevels.NONE) {
                let formatted = `${this.prefix} [${levelName}] ${msg}`;
                if (err && err.stack) {
                    formatted += `\n${err.stack}`;
                } else if (err) {
                    formatted += ` (Details: ${err.message || err})`;
                }
                console.log(formatted);
            }
        }

        debug(msg) { this._log('DEBUG', msg); }
        info(msg)  { this._log('INFO', msg); }
        warn(msg, err)  { this._log('WARN', msg, err); }
        error(msg, err) { this._log('ERROR', msg, err); }

        createChild(subName) {
            return new Logger(`${this.prefix.replace(/[\[\]]/g, '')}:${subName}`, Object.keys(LogLevels).find(k => LogLevels[k] === this.minLevel));
        }
    }

    // --- 2. Defensive Hooking Utilities ---
    const SafeUtils = {
        /**
         * Safely attach an Interceptor to a native library export without throwing.
         */
        safeAttachNative: function (libName, exportName, callbacks, logger) {
            try {
                const targetPtr = Module.findExportByName(libName, exportName);
                if (!targetPtr) {
                    if (logger) logger.debug(`Native export '${exportName}' not found in ${libName || 'global scope'}`);
                    return false;
                }
                Interceptor.attach(targetPtr, callbacks);
                if (logger) logger.debug(`Successfully hooked native ${libName ? libName + '!' : ''}${exportName}`);
                return true;
            } catch (err) {
                if (logger) logger.warn(`Failed hooking native ${exportName}: ${err.message}`);
                return false;
            }
        },

        /**
         * Safely wrap Java.use with error suppression.
         */
        safeJavaUse: function (className, callback, logger) {
            try {
                const clazz = Java.use(className);
                if (clazz && typeof callback === 'function') {
                    callback(clazz);
                    return true;
                }
            } catch (err) {
                if (logger) logger.debug(`Class '${className}' not found or hook failed: ${err.message}`);
            }
            return false;
        }
    };

    // --- 3. Hook Module Registry ---
    class HookRegistry {
        constructor() {
            this.modules = new Map();
            this.activeModules = new Set();
            this.config = {};
            this.logger = new Logger('FridaCore', 'INFO');
            this.initialized = false;
        }

        /**
         * Register a hook module.
         * @param {Object} module 
         */
        register(module) {
            if (!module || typeof module.name !== 'string' || !module.name.trim()) {
                throw new Error('[FridaCore] Invalid module: name is required');
            }
            const name = module.name.trim();
            if (this.modules.has(name)) {
                this.logger.warn(`Overriding previously registered module '${name}'`);
            }
            this.modules.set(name, module);
            this.logger.debug(`Registered hook module: ${name} (stage: ${module.stage || 'both'})`);
        }

        get(name) {
            return this.modules.get(name);
        }

        list() {
            return Array.from(this.modules.keys());
        }

        /**
         * Orchestrate and bootstrap the complete hook lifecycle.
         * @param {Object} userConfig 
         */
        bootstrap(userConfig) {
            if (this.initialized) {
                this.logger.warn('Frida Core engine already bootstrapped.');
                return;
            }

            this.config = userConfig || {};
            const logLevel = this.config.log_level || (this.config.frida && this.config.frida.log_level) || 'INFO';
            this.logger.setLevel(logLevel);

            this.logger.info('========================================================');
            this.logger.info('  Frida Core Hooks Engine (frida-hooks-core) v2.0       ');
            this.logger.info(`  Log Level: ${logLevel}`);
            this.logger.info('========================================================');

            const moduleConfigs = this.config.modules || {};
            
            // Resolve enabled state for all registered modules
            for (const [name, mod] of this.modules.entries()) {
                let isEnabled = mod.defaultEnabled !== false;
                let modConf = moduleConfigs[name];

                // Check boolean or object toggle
                if (typeof modConf === 'boolean') {
                    isEnabled = modConf;
                    modConf = { enabled: modConf };
                } else if (typeof modConf === 'object' && modConf !== null) {
                    if (typeof modConf.enabled === 'boolean') {
                        isEnabled = modConf.enabled;
                    }
                }

                // Check environment probe if defined
                if (isEnabled && typeof mod.isSupported === 'function') {
                    try {
                        isEnabled = Boolean(mod.isSupported({ config: modConf, root: root, logger: this.logger }));
                    } catch (e) {
                        this.logger.warn(`Module '${name}' isSupported() check failed: ${e.message}`);
                        isEnabled = false;
                    }
                }

                if (isEnabled) {
                    this.activeModules.add(name);
                }
            }

            this.logger.info(`Active modules (${this.activeModules.size}): [${Array.from(this.activeModules).join(', ')}]`);

            // --- STAGE 1: Native Hooks Execution ---
            this._runNativeStage(moduleConfigs);

            // --- STAGE 2: Java Hooks Execution ---
            this._runJavaStage(moduleConfigs);

            this.initialized = true;
        }

        _runNativeStage(moduleConfigs) {
            this.logger.debug('Starting STAGE 1: Native hooks deployment...');
            let count = 0;

            for (const name of this.activeModules) {
                const mod = this.modules.get(name);
                const stage = mod.stage || 'both';
                if ((stage === 'native' || stage === 'both') && typeof mod.initNative === 'function') {
                    const modLogger = new Logger(name, Object.keys(LogLevels).find(k => LogLevels[k] === this.logger.minLevel));
                    const modConf = moduleConfigs[name] || {};
                    try {
                        mod.initNative(modConf, {
                            logger: modLogger,
                            safeUtils: SafeUtils,
                            root: root
                        });
                        count++;
                        this.logger.debug(`[Stage: Native] Module '${name}' deployed.`);
                    } catch (err) {
                        this.logger.error(`[Stage: Native] Error deploying module '${name}':`, err);
                    }
                }
            }
            this.logger.info(`Stage 1 (Native) complete: ${count} module(s) attached.`);
        }

        _runJavaStage(moduleConfigs) {
            const hasJavaModules = Array.from(this.activeModules).some(name => {
                const mod = this.modules.get(name);
                const stage = mod.stage || 'both';
                return (stage === 'java' || stage === 'both') && typeof mod.initJava === 'function';
            });

            if (!hasJavaModules) {
                this.logger.debug('No Java stage modules active.');
                this._runCustomHooks();
                return;
            }

            const self = this;
            const executeJavaHooks = function () {
                self.logger.debug('Starting STAGE 2: Java hooks deployment inside ART runtime...');
                let count = 0;

                for (const name of self.activeModules) {
                    const mod = self.modules.get(name);
                    const stage = mod.stage || 'both';
                    if ((stage === 'java' || stage === 'both') && typeof mod.initJava === 'function') {
                        const modLogger = new Logger(name, Object.keys(LogLevels).find(k => LogLevels[k] === self.logger.minLevel));
                        const modConf = moduleConfigs[name] || {};
                        try {
                            mod.initJava(modConf, {
                                logger: modLogger,
                                safeUtils: SafeUtils,
                                root: root
                            });
                            count++;
                            self.logger.debug(`[Stage: Java] Module '${name}' deployed.`);
                        } catch (err) {
                            self.logger.error(`[Stage: Java] Error deploying module '${name}':`, err);
                        }
                    }
                }
                self.logger.info(`Stage 2 (Java) complete: ${count} module(s) attached.`);
                self._runCustomHooks();
            };

            // Synchronization with Dalvik/ART VM readiness
            if (typeof Java !== 'undefined' && Java.available) {
                if (typeof Java.performWhenReady === 'function') {
                    Java.performWhenReady(executeJavaHooks);
                } else {
                    Java.perform(executeJavaHooks);
                }
            } else {
                this.logger.debug('Java VM not yet ready; polling for availability...');
                const pollInterval = setInterval(function () {
                    if (typeof Java !== 'undefined' && Java.available) {
                        clearInterval(pollInterval);
                        Java.perform(executeJavaHooks);
                    }
                }, 25);
            }
        }

        _runCustomHooks() {
            const custom = this.config.custom_hooks;
            if (custom && typeof custom === 'function') {
                try {
                    this.logger.info('Executing custom app hook function...');
                    custom(this.logger);
                } catch (e) {
                    this.logger.error('Error executing custom app hooks:', e);
                }
            }
        }
    }

    // Expose engine instance on root
    const registry = new HookRegistry();
    root.__FRIDA_CORE__ = {
        Registry: registry,
        Logger: Logger,
        SafeUtils: SafeUtils,
        register: function (mod) { registry.register(mod); },
        bootstrap: function (cfg) { registry.bootstrap(cfg); }
    };

})(typeof globalThis !== 'undefined' ? globalThis : this);

/**
 * unified_bypass.js
 * 
 * Master Entrypoint & Orchestrator for the Unified Modern Frida Bypass Suite.
 * Coordinates:
 * - Anti-Root & Anti-Emulator (anti_root_emulator.js)
 * - Universal SSL Unpinning (ssl_unpinning.js)
 * - Anti-Frida & Anti-Debugging Cloak (anti_frida.js)
 * 
 * Works in both dynamic runtime attachment (frida CLI) and static frida-gadget injection.
 */

(function (root) {
    'use strict';

    // --- 1. Global Configuration ---
    const Config = {
        logLevel: 'INFO', // 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'NONE'
        enableRootBypass: true,
        enableEmulatorBypass: true,
        enableSslBypass: true,
        enableAntiFrida: true,
        enableXamarinBypass: true
    };

    // Allow override from globalThis.BYPASS_CONFIG if defined
    if (typeof root.BYPASS_CONFIG === 'object' && root.BYPASS_CONFIG !== null) {
        Object.assign(Config, root.BYPASS_CONFIG);
    }

    // --- 2. High-Performance Logging Utility ---
    const LogLevels = {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3,
        NONE: 4
    };

    class Logger {
        constructor(prefix, minLevelName) {
            this.prefix = prefix ? `[${prefix}]` : '[BypassSuite]';
            this.minLevel = LogLevels[minLevelName] !== undefined ? LogLevels[minLevelName] : LogLevels.INFO;
        }

        setLevel(levelName) {
            if (LogLevels[levelName] !== undefined) {
                this.minLevel = LogLevels[levelName];
            }
        }

        _log(levelName, msg) {
            if (LogLevels[levelName] >= this.minLevel && LogLevels[levelName] < LogLevels.NONE) {
                const tag = `[${levelName}]`;
                console.log(`${this.prefix} ${tag} ${msg}`);
            }
        }

        debug(msg) { this._log('DEBUG', msg); }
        info(msg)  { this._log('INFO', msg); }
        warn(msg)  { this._log('WARN', msg); }
        error(msg) { this._log('ERROR', msg); }
    }

    const suiteLogger = new Logger('UnifiedBypass', Config.logLevel);

    // --- 3. Master Loader & Initialization ---
    function initializeSuite() {
        suiteLogger.info('Initializing Modern Frida Bypass Suite v2.0...');
        suiteLogger.info(`Active Config: Root=${Config.enableRootBypass}, Emulator=${Config.enableEmulatorBypass}, SSL=${Config.enableSslBypass}, AntiFrida=${Config.enableAntiFrida}`);

        // 1. Anti-Frida & Anti-Debugging (Execute first to cloak instrumentation before other hooks register)
        if (Config.enableAntiFrida) {
            if (root.AntiFrida && typeof root.AntiFrida.init === 'function') {
                try {
                    root.AntiFrida.init(Config, new Logger('AntiFrida', Config.logLevel));
                } catch (e) {
                    suiteLogger.error(`Failed initializing AntiFrida module: ${e.message}`);
                }
            } else {
                suiteLogger.debug('AntiFrida module not loaded in global scope.');
            }
        }

        // 2. Anti-Root & Anti-Emulator
        if (Config.enableRootBypass || Config.enableEmulatorBypass) {
            if (root.AntiRootEmulator && typeof root.AntiRootEmulator.init === 'function') {
                try {
                    root.AntiRootEmulator.init(Config, new Logger('AntiRoot', Config.logLevel));
                } catch (e) {
                    suiteLogger.error(`Failed initializing AntiRootEmulator module: ${e.message}`);
                }
            } else {
                suiteLogger.debug('AntiRootEmulator module not loaded in global scope.');
            }
        }

        // 3. SSL Unpinning
        if (Config.enableSslBypass) {
            if (root.SslUnpinning && typeof root.SslUnpinning.init === 'function') {
                try {
                    root.SslUnpinning.init(Config, new Logger('SslUnpin', Config.logLevel));
                } catch (e) {
                    suiteLogger.error(`Failed initializing SslUnpinning module: ${e.message}`);
                }
            } else {
                suiteLogger.debug('SslUnpinning module not loaded in global scope.');
            }
        }

        suiteLogger.info('Bypass Suite orchestrator initialized successfully.');
    }

    // Expose orchestrator and Logger to global scope
    root.BypassSuite = {
        Config: Config,
        Logger: Logger,
        init: initializeSuite
    };

    // Auto-bootstrap
    initializeSuite();

})(typeof globalThis !== 'undefined' ? globalThis : this);

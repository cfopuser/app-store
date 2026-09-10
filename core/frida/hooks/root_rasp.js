/**
 * root_rasp.js
 * 
 * Compatibility alias for anti_root.js.
 * Ensures backward compatibility with legacy scripts and tests referencing root_rasp.
 */

// Load unified anti_root module
(function (root) {
    'use strict';
    if (root.__FRIDA_CORE__ && root.__FRIDA_CORE__.Registry) {
        const antiRoot = root.__FRIDA_CORE__.Registry.get('anti_root');
        if (antiRoot) {
            root.__FRIDA_CORE__.register({
                ...antiRoot,
                name: 'root_rasp'
            });
        }
    }
})(typeof globalThis !== 'undefined' ? globalThis : this);

import { RELEASES_INDEX, RELEASES_API, APPS_DIR, REGISTERED_APPS, setRegisteredApps } from './config.js';

export let allReleases = [];
export let appConfigs = {};
export let appStatuses = {};
export let appStats = {};

/**
 * Fetch releases from the static index first (no rate-limit risk).
 * Falls back to the GitHub API only if the static file is missing.
 */
async function fetchReleases() {
    // 1. Try the static releases.json committed by the CI workflow
    try {
        const resp = await fetch(RELEASES_INDEX);
        if (resp.ok) {
            const data = await resp.json();
            if (Array.isArray(data) && data.length > 0) {
                console.log(`[api] Loaded ${data.length} releases from static index`);
                return data;
            }
        }
    } catch { /* static file not available — fall through */ }

    // 2. Fallback: live GitHub API (may be rate-limited for anonymous users)
    console.warn('[api] Static releases.json unavailable — falling back to GitHub API');
    try {
        const resp = await fetch(RELEASES_API);
        if (resp.ok) {
            return await resp.json();
        }
        console.error(`[api] GitHub API returned ${resp.status}`);
    } catch (e) {
        console.error('[api] GitHub API fetch failed', e);
    }

    return [];
}

export async function fetchAppData() {
    try {
        let apps;
        try {
            const r = await fetch('apps.json');
            apps = await r.json();
        } catch {
            apps = ['bit'];
        }
        setRegisteredApps(apps);

        const t = Date.now();
        const [releases, ...configsResps] = await Promise.all([
            fetchReleases(),
            ...REGISTERED_APPS.map(id => fetch(`${APPS_DIR}/${id}/app.json?t=${t}`).then(r => r.json().catch(() => null))),
            ...REGISTERED_APPS.map(id => fetch(`${APPS_DIR}/${id}/status.json?t=${t}`).then(r => r.json().catch(() => ({ success: true })))),
            fetch(`download_stats.json?t=${t}`).then(r => r.json().catch(() => ({})))
        ]);

        allReleases = releases;
        const configs = configsResps.slice(0, REGISTERED_APPS.length);
        const statuses = configsResps.slice(REGISTERED_APPS.length, REGISTERED_APPS.length * 2);
        appStats = configsResps[configsResps.length - 1] || {};

        REGISTERED_APPS.forEach((id, i) => {
            if (configs[i]) {
                // Flatten the config if it's nested
                const config = configs[i];
                const categories = ["metadata", "assets", "source", "patching", "paths", "maintenance"];
                const isNested = categories.some(cat => config[cat] && typeof config[cat] === 'object');
                
                if (isNested) {
                    const flattened = {};
                    Object.keys(config).forEach(key => {
                        if (categories.includes(key) && typeof config[key] === 'object') {
                            Object.assign(flattened, config[key]);
                        } else {
                            flattened[key] = config[key];
                        }
                    });
                    appConfigs[id] = flattened;
                } else {
                    appConfigs[id] = config;
                }
                
                appStatuses[id] = statuses[i];
            }
        });
        return true;
    } catch (e) {
        console.error("Data fetch failed", e);
        return false;
    }
}

export function getAppReleases(appId) {
    let rels = allReleases.filter(r => r.tag_name.startsWith(`${appId}-v`) && r.assets?.length > 0);
    if (rels.length === 0 && appId === 'bit') {
        rels = allReleases.filter(r => r.tag_name.startsWith('v') && !r.tag_name.includes('-v') && r.assets?.length > 0);
    }
    return rels;
}

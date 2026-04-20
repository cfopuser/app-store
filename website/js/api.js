import { RELEASES_API, APPS_DIR, REGISTERED_APPS, setRegisteredApps } from './config.js';

export let allReleases = [];
export let appConfigs = {};
export let appStatuses = {};
export let appStats = {};

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

        const [releasesResp, ...configsResps] = await Promise.all([
            fetch(RELEASES_API).then(r => r.json()),
            ...REGISTERED_APPS.map(id => fetch(`${APPS_DIR}/${id}/app.json`).then(r => r.json().catch(() => null))),
            ...REGISTERED_APPS.map(id => fetch(`${APPS_DIR}/${id}/status.json`).then(r => r.json().catch(() => ({ success: true })))),
            fetch('download_stats.json').then(r => r.json().catch(() => ({})))
        ]);

        allReleases = releasesResp;
        const configs = configsResps.slice(0, REGISTERED_APPS.length);
        const statuses = configsResps.slice(REGISTERED_APPS.length, REGISTERED_APPS.length * 2);
        appStats = configsResps[configsResps.length - 1] || {};

        REGISTERED_APPS.forEach((id, i) => {
            if (configs[i]) {
                appConfigs[id] = configs[i];
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

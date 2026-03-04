// ─── Configuration ───
const REPO = "cfopuser/app-store";
const RELEASES_API = `https://api.github.com/repos/${REPO}/releases`;
const APPS_DIR = "apps";
let REGISTERED_APPS = [];

// ─── i18n ───
const i18n = {
    en: {
        heroTitle: "Discover Apps",
        heroSubtitle: "Community-maintained patched versions. Updated automatically.",
        downloadBtn: "Get",
        downloadBtnFull: "Download APK",
        released: "Released",
        olderVersions: "Version History",
        noAssets: "Unavailable",
        loading: "Loading library...",
        noApps: "Check back later for updates.",
        disclaimer: "Unofficial project. Not affiliated with app developers. Use at your own risk.",
        langLabel: "עברית",
        errorTitle: "Patch Failed",
        errorDetail: "Patch failed for v{version}",
        errorMessage: "Error: {message}",
        submitApp: "Request an App",
        latestVersion: "Latest Version",
        maintainedBy: "Maintained by",
        viewAll: "See All",
    },
    he: {
        heroTitle: "חנות האפליקציות",
        heroSubtitle: "גרסאות ערוכות וחסומות. מתעדכן באופן אוטומטי.",
        downloadBtn: "הורדה",
        downloadBtnFull: "הורד APK",
        released: "פורסם ב-",
        olderVersions: "היסטוריית גרסאות",
        noAssets: "לא זמין",
        loading: "טוען...",
        noApps: "אין אפליקציות זמינות כרגע.",
        disclaimer: "פרויקט לא רשמי. אינו קשור למפתחי האפליקציות. השימוש באחריות המשתמש בלבד.",
        langLabel: "English",
        errorTitle: "שגיאה בתיקון",
        errorDetail: "התיקון נכשל עבור גרסה {version}",
        errorMessage: "שגיאה: {message}",
        submitApp: "בקשת אפליקציה חדשה",
        latestVersion: "גרסה אחרונה",
        maintainedBy: "מתוחזק ע״י",
        viewAll: "הצג הכל",
    }
};

// ─── Theme & Language ───
let currentLang = localStorage.getItem('preferredLanguage') ||
    ((navigator.language || '').startsWith('he') ? 'he' : 'en');

let isDark = localStorage.getItem('theme') === 'dark' ||
    (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);

function updateTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('themeIcon');
    if (isDark) {
        html.classList.add('dark');
        icon.className = 'fa-solid fa-sun text-base sm:text-lg transition-transform';
    } else {
        html.classList.remove('dark');
        icon.className = 'fa-solid fa-moon text-base sm:text-lg transition-transform';
    }
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function toggleTheme() {
    isDark = !isDark;
    updateTheme();
}

function updateLang() {
    document.documentElement.dir = currentLang === 'he' ? 'rtl' : 'ltr';
    document.documentElement.lang = currentLang;

    document.querySelectorAll('[data-key]').forEach(el => {
        const key = el.getAttribute('data-key');
        if (i18n[currentLang][key]) el.textContent = i18n[currentLang][key];
    });

    document.getElementById('langLabel').textContent = i18n[currentLang].langLabel;
    if (Object.keys(appConfigs).length > 0) renderGrid();
}

function toggleLang() {
    currentLang = currentLang === 'en' ? 'he' : 'en';
    localStorage.setItem('preferredLanguage', currentLang);
    updateLang();
}

// ─── Data & Rendering ───
const loader = document.getElementById('loader');
const appGrid = document.getElementById('appGrid');
const emptyState = document.getElementById('emptyState');
const appModal = document.getElementById('appModal');
const modalBackdrop = document.getElementById('modalBackdrop');
const modalPanel = document.getElementById('modalPanel');
const modalContent = document.getElementById('modalContent');

let allReleases = [];
let appConfigs = {};
let appStatuses = {};

async function loadData() {
    try {
        try {
            const r = await fetch('apps.json');
            REGISTERED_APPS = await r.json();
        } catch {
            REGISTERED_APPS = ['bit']; 
        }

        const [releasesResp, ...configsResps] = await Promise.all([
            fetch(RELEASES_API).then(r => r.json()),
            ...REGISTERED_APPS.map(id => fetch(`${APPS_DIR}/${id}/app.json`).then(r => r.json().catch(() => null))),
            ...REGISTERED_APPS.map(id => fetch(`${APPS_DIR}/${id}/status.json`).then(r => r.json().catch(() => ({ success: true }))))
        ]);

        allReleases = releasesResp;
        const configs = configsResps.slice(0, REGISTERED_APPS.length);
        const statuses = configsResps.slice(REGISTERED_APPS.length);

        REGISTERED_APPS.forEach((id, i) => {
            if (configs[i]) {
                appConfigs[id] = configs[i];
                appStatuses[id] = statuses[i];
            }
        });

        loader.classList.add('hidden');

        if (Object.keys(appConfigs).length > 0) {
            renderGrid();
            appGrid.classList.remove('hidden');
        } else {
            emptyState.classList.remove('hidden');
        }

    } catch (e) {
        console.error("Init failed", e);
        loader.classList.add('hidden');
        emptyState.classList.remove('hidden');
    }
}

function getAppReleases(appId) {
    let rels = allReleases.filter(r => r.tag_name.startsWith(`${appId}-v`) && r.assets?.length > 0);
    if (rels.length === 0 && appId === 'bit') {
        rels = allReleases.filter(r => r.tag_name.startsWith('v') && !r.tag_name.includes('-v') && r.assets?.length > 0);
    }
    return rels;
}

function t(key) { return i18n[currentLang][key] || key; }

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString(
        currentLang === 'he' ? 'he-IL' : 'en-US',
        { year: 'numeric', month: 'short', day: 'numeric' }
    );
}

function formatSize(bytes) {
    if (!bytes) return '?';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function renderGrid() {
    appGrid.innerHTML = Object.keys(appConfigs).map(appId => {
        const config = appConfigs[appId];
        const status = appStatuses[appId] || { success: true };
        const releases = getAppReleases(appId);
        const latest = releases[0];
        const isOk = status.success !== false;
        const name = currentLang === 'he' ? (config.name_he || config.name) : config.name;
        const desc = currentLang === 'he' ? (config.description_he || config.description) : config.description;

        return `
        <div class="group relative bg-white dark:bg-slate-800 rounded-3xl p-5 border border-slate-100 dark:border-slate-800 shadow-sm active:scale-[0.98] active:bg-slate-50 dark:active:bg-slate-700/50 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col h-full touch-manipulation" onclick="openModal('${appId}')">
            
            <div class="flex items-start justify-between mb-4">
                <img src="${config.icon_url}" alt="${name}" 
                     class="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-slate-50 dark:bg-slate-900 object-cover shadow-sm flex-shrink-0"
                     onerror="this.src='https://placehold.co/64?text=${name[0]}'">
                ${!isOk ? `<span class="bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-[10px] font-bold px-2 py-1 rounded-full flex items-center gap-1"><i class="fa-solid fa-triangle-exclamation"></i> Error</span>` : ''}
            </div>

            <h3 class="font-bold text-lg text-slate-900 dark:text-white mb-0.5 line-clamp-1">${name}</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 font-mono mb-2 truncate">${config.package_name}</p>
            <p class="text-sm text-slate-600 dark:text-slate-300 line-clamp-2 mb-4 flex-grow leading-relaxed">${desc || ''}</p>
            
            <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-50 dark:border-slate-700/50">
                <div class="flex flex-col">
                    <span class="text-xs text-slate-400 uppercase tracking-wider font-medium">${latest ? 'v' + latest.tag_name.replace(/.*-v|v/, '') : '-'}</span>
                     <span class="text-[10px] text-slate-400">${latest ? formatDate(latest.published_at) : ''}</span>
                </div>
                
                <button class="bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 active:bg-slate-200 dark:active:bg-slate-500 text-brand-600 dark:text-brand-400 font-bold py-2 px-5 rounded-full text-sm transition-colors touch-manipulation">
                    ${t('downloadBtn')}
                </button>
            </div>
        </div>
        `;
    }).join('');
}

function openModal(appId) {
    const config = appConfigs[appId];
    const releases = getAppReleases(appId);
    const status = appStatuses[appId] || { success: true };
    const latest = releases[0];
    const asset = latest?.assets.find(a => a.name.endsWith('.apk')) || latest?.assets[0];
    const name = currentLang === 'he' ? (config.name_he || config.name) : config.name;
    const isOk = status.success !== false;

    modalContent.innerHTML = `
        <div class="flex flex-col items-center mb-6 pt-2">
            <img src="${config.icon_url}" class="w-20 h-20 sm:w-24 sm:h-24 rounded-[1.5rem] sm:rounded-[2rem] shadow-xl mb-4 bg-white dark:bg-slate-800" onerror="this.src='https://placehold.co/96?text=${name[0]}'">
            <h2 class="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-1 text-center">${name}</h2>
            <p class="text-slate-400 font-mono text-xs sm:text-sm mb-3 break-all text-center px-4">${config.package_name}</p>
            ${config.maintainer ? `
                <p class="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/50 px-3 py-1 rounded-full">
                    ${t('maintainedBy')} <span class="font-medium text-brand-600 dark:text-brand-400">@${config.maintainer}</span>
                </p>
            ` : ''}
        </div>

        ${!isOk ? `
            <div class="bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 rounded-2xl p-4 mb-6 text-center mx-1">
                <div class="text-red-600 dark:text-red-400 font-bold mb-1 flex items-center justify-center gap-2 text-sm sm:text-base">
                    <i class="fa-solid fa-circle-exclamation"></i>
                    <span>${t('errorTitle')}</span>
                </div>
                <p class="text-xs sm:text-sm text-red-600/80 dark:text-red-300 mb-2">
                    ${t('errorDetail').replace('{version}', status.failed_version || '?')}
                </p>
                 ${status.error_message ? `<p class="text-[10px] sm:text-xs font-mono text-red-500 dark:text-red-400/70 bg-white/50 dark:bg-black/20 p-2 rounded break-words text-left">${status.error_message}</p>` : ''}
            </div>
        ` : ''}

        ${latest ? `
            <div class="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-4 sm:p-5 mb-6 border border-slate-100 dark:border-slate-800">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h3 class="font-bold text-slate-900 dark:text-white text-sm sm:text-base">${t('latestVersion')}</h3>
                        <p class="text-xs sm:text-sm text-slate-500">v${latest.tag_name.replace(/.*-v|v/, '')}</p>
                    </div>
                    <span class="text-xs text-slate-400">${formatDate(latest.published_at)}</span>
                </div>
                
                ${asset ? `
                <a href="${asset.browser_download_url}" 
                   class="w-full bg-brand-600 hover:bg-brand-700 active:bg-brand-800 active:scale-[0.98] text-white font-bold py-3.5 px-6 rounded-xl shadow-lg shadow-brand-500/20 transition-all flex items-center justify-center gap-2 touch-manipulation">
                     <i class="fa-solid fa-download"></i>
                     <span>${t('downloadBtnFull')}</span>
                     <span class="text-brand-200 font-normal text-sm ml-1">(${formatSize(asset.size)})</span>
                </a>
                ` : ''}
            </div>
        ` : ''}

        ${releases.length > 1 ? `
            <div class="border-t border-slate-100 dark:border-slate-800 pt-6 pb-2">
                <h3 class="font-bold text-slate-900 dark:text-white mb-3 px-1 text-sm sm:text-base">${t('olderVersions')}</h3>
                <div class="space-y-2 max-h-52 overflow-y-auto pr-1 custom-scrollbar">
                    ${releases.slice(1).map(r => {
        const a = r.assets.find(as => as.name.endsWith('.apk')) || r.assets[0];
        if (!a) return '';
        return `
                        <a href="${a.browser_download_url}" class="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/50 active:bg-slate-100 dark:active:bg-slate-800 transition border border-transparent hover:border-slate-100 dark:hover:border-slate-700 touch-manipulation">
                            <div>
                                <div class="font-semibold text-slate-700 dark:text-slate-300 text-sm">v${r.tag_name.replace(/.*-v|v/, '')}</div>
                                <div class="text-xs text-slate-400">${formatDate(r.published_at)}</div>
                            </div>
                            <i class="fa-solid fa-cloud-arrow-down text-slate-300 dark:text-slate-600"></i>
                        </a>
                        `;
    }).join('')}
                </div>
            </div>
        ` : ''}
    `;

    appModal.classList.remove('hidden');
    // Animate In
    setTimeout(() => {
        modalBackdrop.classList.remove('opacity-0');
        modalPanel.classList.remove('translate-y-full', 'opacity-0');
    }, 10);
    
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    // Animate Out
    modalBackdrop.classList.add('opacity-0');
    modalPanel.classList.add('translate-y-full');
    // Wait for animation
    setTimeout(() => {
         appModal.classList.add('hidden');
         modalPanel.classList.add('opacity-0'); // Reset opacity for next open
         document.body.style.overflow = '';
    }, 300);
}

// ─── Listeners ───
document.getElementById('themeToggle').addEventListener('click', toggleTheme);
document.getElementById('langToggle').addEventListener('click', toggleLang);
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modalBackdrop').addEventListener('click', closeModal);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ─── Start ───
updateTheme();
updateLang();
loadData();

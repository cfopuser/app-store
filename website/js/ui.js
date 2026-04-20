import { appConfigs, appStatuses, appStats, getAppReleases } from './api.js';
import { currentLang, t, formatDate, formatSize, formatNumber } from './i18n.js';

export const appGrid = document.getElementById('appGrid');
export const emptyState = document.getElementById('emptyState');
export const appModal = document.getElementById('appModal');
export const modalBackdrop = document.getElementById('modalBackdrop');
export const modalPanel = document.getElementById('modalPanel');
export const modalContent = document.getElementById('modalContent');
export const loader = document.getElementById('loader');
export const gridContainer = document.getElementById('gridContainer');
export const featuredAppArea = document.getElementById('featuredAppArea');

const isDark = () => document.documentElement.classList.contains('dark');

export const appVisuals = {
    bit: { icon: "credit-card", bg: "bg-gradient-to-br from-teal-400 to-emerald-600", iconClass: "text-white drop-shadow-sm" },
    egg: { icon: "bus", bg: "bg-gradient-to-br from-indigo-500 to-blue-700", iconClass: "text-white drop-shadow-sm" },
    hopon: { icon: "hash", bg: "bg-gradient-to-br from-slate-100 to-slate-300 dark:from-slate-700 dark:to-slate-900", iconClass: "text-slate-700 dark:text-slate-300" },
    meld: { icon: "music", bg: "bg-gradient-to-br from-lime-400 to-green-600", iconClass: "text-white drop-shadow-sm" },
    metrolist: { icon: "music", bg: "bg-gradient-to-br from-zinc-800 to-black", iconClass: "text-white drop-shadow-sm" },
    mizrahi: { icon: "infinity", bg: "bg-gradient-to-br from-orange-400 to-rose-500", iconClass: "text-white drop-shadow-sm" },
    spotify: { icon: "music", bg: "bg-gradient-to-br from-green-400 to-emerald-700", iconClass: "text-white drop-shadow-sm" },
    termux: { icon: "terminal", bg: "bg-gradient-to-br from-slate-800 to-slate-900", iconClass: "text-white drop-shadow-sm" },
    waze: { icon: "map-pin", bg: "bg-gradient-to-br from-cyan-400 to-blue-600", iconClass: "text-white drop-shadow-sm" },
    whatsapp: { icon: "message-circle", bg: "bg-gradient-to-br from-green-500 to-emerald-500", iconClass: "text-white drop-shadow-sm" },
    yahav: { icon: "landmark", bg: "bg-gradient-to-br from-yellow-400 to-orange-500", iconClass: "text-white drop-shadow-sm" }
};
const defaultVisual = { icon: "smartphone", bg: "bg-gradient-to-br from-slate-400 to-slate-600", iconClass: "text-white drop-shadow-sm" };

function buildAppGridCard(appId) {
    const config = appConfigs[appId];
    const status = appStatuses[appId] || { success: true };
    const releases = getAppReleases(appId);
    const latest = releases[0];
    const isOk = status.success !== false;
    const name = currentLang === 'he' ? (config.name_he || config.name) : config.name;
    const desc = currentLang === 'he' ? (config.description_he || config.description) : config.description;
    const downloads = appStats[appId] || 0;
    const visual = appVisuals[appId] || defaultVisual;
    const asset = latest?.assets.find(a => a.name.endsWith('.apk')) || latest?.assets[0];

    return `
    <div class="group relative rounded-2xl transition-all duration-500 p-[1px] hover:-translate-y-1 cursor-pointer" onclick="window.openAppModal('${appId}')">
        <div class="absolute inset-0 rounded-2xl transition-opacity duration-500 bg-zinc-200/50 dark:bg-zinc-800/50 group-hover:opacity-0"></div>
        <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-rose-400/80 via-fuchsia-400/80 to-indigo-400/80 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        
        <div class="relative h-full flex flex-col p-6 rounded-[15px] bg-white dark:bg-[#15151A] shadow-sm group-hover:shadow-xl transition-shadow duration-500">
            <div class="flex items-start justify-between mb-5">
                <div class="w-14 h-14 rounded-xl shadow-sm relative overflow-hidden bg-white dark:bg-zinc-950 p-1 flex items-center justify-center">
                    <img src="${config.icon_url}" class="w-full h-full object-contain rounded-lg" onerror="this.parentElement.innerHTML='<div class=\\'w-full h-full rounded-lg ${visual.bg} flex items-center justify-center\\'><i data-lucide=\\'${visual.icon}\\' class=\\'w-6 h-6 ${visual.iconClass}\\'></i></div>'">
                </div>
                
                <div class="flex flex-col items-end gap-2">
                    ${!isOk ? `<span title="${t('patchErrorTooltip')}" class="inline-flex items-center justify-center p-1 rounded-full bg-rose-500/10 text-rose-500 dark:text-rose-400"><i data-lucide="alert-circle" class="w-4 h-4"></i></span>` : ''}
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-widest bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 border border-zinc-200/50 dark:border-zinc-700/50">
                        <i data-lucide="download" class="w-3 h-3"></i> ${formatNumber(downloads)}
                    </span>
                </div>
            </div>

            <div class="flex-1 space-y-2 mb-6">
                <div class="flex justify-between items-start">
                    <h3 class="font-semibold text-lg text-zinc-900 dark:text-zinc-100">${name}</h3>
                </div>
                <p class="font-mono text-[10px] text-zinc-400 dark:text-zinc-500 truncate">${config.package_name}</p>
                <p class="text-sm leading-relaxed line-clamp-2 text-zinc-500 dark:text-zinc-400">${desc || ''}</p>
                
                ${config.maintainer ? `
                <div class="flex items-center gap-1.5 mt-2 opacity-60 group-hover:opacity-100 transition-opacity">
                    <div class="w-4 h-4 rounded-full bg-gradient-to-tr from-rose-400 to-indigo-500 p-[1px]">
                         <div class="w-full h-full rounded-full bg-white dark:bg-[#15151A] flex items-center justify-center">
                            <i data-lucide="user" class="w-2 h-2 text-zinc-400"></i>
                         </div>
                    </div>
                    <span class="text-[10px] text-zinc-400 font-medium">@${config.maintainer}</span>
                </div>
                ` : ''}
            </div>

            <div class="flex items-end justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800/60">
                <div class="font-mono text-[10px] uppercase tracking-widest space-y-1.5 text-zinc-400 dark:text-zinc-500">
                    <div class="text-zinc-700 dark:text-zinc-300 font-bold">${latest ? 'v' + latest.tag_name.replace(/.*-v|v/, '') : '-'}</div>
                    <div class="flex items-center gap-1 opacity-70">
                         ${latest ? formatDate(latest.published_at) : ''}
                    </div>
                </div>
                
                <button onclick="${asset ? `event.stopPropagation(); window.trackDownload('${appId}'); window.location.href='${asset.browser_download_url}';` : `event.stopPropagation();`}" 
                        class="px-5 py-2 rounded-full text-xs font-semibold transition-all bg-zinc-100 text-zinc-600 group-hover:bg-zinc-900 group-hover:text-white dark:bg-zinc-800 dark:text-zinc-300 dark:group-hover:bg-zinc-100 dark:group-hover:text-zinc-900 shadow-sm transform active:scale-95">
                    ${t('get')}
                </button>
            </div>
        </div>
    </div>
    `;
}

function buildFeaturedApp(appId) {
    const config = appConfigs[appId];
    const status = appStatuses[appId] || { success: true };
    const releases = getAppReleases(appId);
    const latest = releases[0];
    const isOk = status.success !== false;
    const name = currentLang === 'he' ? (config.name_he || config.name) : config.name;
    const desc = currentLang === 'he' ? (config.description_he || config.description) : config.description;
    const downloads = appStats[appId] || 0;
    const visual = appVisuals[appId] || defaultVisual;
    const asset = latest?.assets.find(a => a.name.endsWith('.apk')) || latest?.assets[0];

    return `
    <section class="space-y-4 relative group" onclick="window.openAppModal('${appId}')" style="cursor: pointer;">
        <div class="flex items-center gap-2">
            <i data-lucide="sparkles" class="w-4 h-4 text-rose-400"></i>
            <h2 class="text-xs font-sans uppercase tracking-[0.15em] font-bold text-zinc-400 dark:text-zinc-500">${t('mostDownloads')}</h2>
        </div>
        
        <div class="relative">
            <div class="absolute -inset-1 bg-gradient-to-r from-rose-400 via-fuchsia-400 to-indigo-400 rounded-3xl blur-xl opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            
            <div class="relative p-[1px] rounded-[2rem] overflow-hidden bg-zinc-200 dark:bg-zinc-800">
                <div class="relative px-5 py-8 sm:p-10 flex flex-col sm:flex-row items-start sm:items-center gap-6 sm:gap-8 rounded-[calc(2rem-1px)] z-10 bg-white dark:bg-[#15151A]">
                    
                    <div class="w-20 h-20 sm:w-28 sm:h-28 shrink-0 rounded-[1.25rem] sm:rounded-[1.5rem] bg-white dark:bg-zinc-950 p-2 shadow-sm relative overflow-hidden flex items-center justify-center ring-1 ring-zinc-100 dark:ring-zinc-800">
                        <img src="${config.icon_url}" class="w-full h-full object-contain rounded-xl" onerror="this.parentElement.innerHTML='<div class=\\'w-full h-full rounded-xl ${visual.bg} flex items-center justify-center\\'><i data-lucide=\\'${visual.icon}\\' class=\\'w-10 h-10 sm:w-12 sm:h-12 ${visual.iconClass}\\'></i></div>'">
                    </div>
                    
                    <div class="flex-1 space-y-2 sm:space-y-3 w-full">
                        <div class="flex flex-wrap items-baseline gap-2 sm:gap-3">
                            <h3 class="text-2xl sm:text-3xl font-semibold text-zinc-900 dark:text-zinc-100">${name}</h3>
                            <span class="text-[10px] sm:text-xs font-mono px-2 py-0.5 rounded border bg-zinc-100 border-zinc-200 text-zinc-500 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-400">
                                ${latest ? 'v' + latest.tag_name.replace(/.*-v|v/, '') : '-'}
                            </span>
                        </div>
                        <p class="font-mono text-[10px] sm:text-xs text-zinc-400 dark:text-zinc-500">${config.package_name}</p>
                        <p class="text-sm sm:text-base leading-relaxed text-zinc-500 dark:text-zinc-400 max-w-xl">
                            ${desc}
                        </p>
                        ${config.maintainer ? `
                        <div class="flex items-center gap-2 opacity-70">
                             <div class="w-5 h-5 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                                <i data-lucide="user" class="w-3 h-3 text-zinc-400"></i>
                             </div>
                             <span class="text-[10px] sm:text-xs text-zinc-500 font-medium">${t('maintainedBy')} @${config.maintainer}</span>
                        </div>
                        ` : ''}
                    </div>

                    <div class="flex flex-col sm:items-end gap-3 w-full sm:w-auto mt-2 sm:mt-0 pt-4 sm:pt-0 border-t sm:border-t-0 border-zinc-100 dark:border-zinc-800">
                        <button onclick="${asset ? `event.stopPropagation(); window.trackDownload('${appId}'); window.location.href='${asset.browser_download_url}';` : `event.stopPropagation();`}" 
                            class="group/btn relative flex items-center justify-center gap-2 px-8 py-3.5 w-full sm:w-auto rounded-full font-medium bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 overflow-hidden transition-transform hover:-translate-y-0.5 active:translate-y-0 shadow-lg sm:shadow-md">
                            <div class="absolute inset-0 bg-gradient-to-r from-rose-400 via-fuchsia-400 to-indigo-400 opacity-0 group-hover/btn:opacity-20 transition-opacity duration-300"></div>
                            <span class="relative z-10">${t('get')}</span>
                            <i data-lucide="download" class="w-4 h-4 relative z-10 opacity-70 group-hover/btn:opacity-100 transition-opacity"></i>
                        </button>
                        <span class="font-mono text-[10px] uppercase tracking-widest text-zinc-400 dark:text-zinc-500 flex items-center gap-1.5 justify-center sm:justify-end">
                            <i data-lucide="download" class="w-3 h-3"></i> ${formatNumber(downloads)} installs
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </section>
    `;
}

export function renderGrid(query = '') {
    const appsList = Object.keys(appConfigs);
    
    // Sort apps by downloads to find the featured app
    const sortedApps = [...appsList].sort((a, b) => (appStats[b] || 0) - (appStats[a] || 0));
    const featuredAppId = sortedApps[0];

    let filteredApps = appsList;
    if (query) {
        const q = query.toLowerCase();
        filteredApps = appsList.filter(appId => {
            const config = appConfigs[appId];
            return (config.name && config.name.toLowerCase().includes(q)) ||
                   (config.name_he && config.name_he.toLowerCase().includes(q)) ||
                   (config.package_name && config.package_name.toLowerCase().includes(q)) ||
                   (config.description && config.description.toLowerCase().includes(q)) ||
                   (config.description_he && config.description_he.toLowerCase().includes(q));
        });
    }

    if (filteredApps.length > 0) {
        let gridApps = filteredApps;

        if (!query && featuredAppId && appConfigs[featuredAppId]) {
            featuredAppArea.innerHTML = buildFeaturedApp(featuredAppId);
            featuredAppArea.classList.remove('hidden');
            gridApps = filteredApps.filter(id => id !== featuredAppId);
        } else {
            featuredAppArea.classList.add('hidden');
        }

        appGrid.innerHTML = gridApps.map(buildAppGridCard).join('');
        gridContainer.classList.remove('hidden');
        emptyState.classList.add('hidden');
    } else {
        featuredAppArea.classList.add('hidden');
        gridContainer.classList.add('hidden');
        emptyState.classList.remove('hidden');
    }

    // Re-initialize Lucide icons
    if (window.lucide) window.lucide.createIcons();
}

export function openModal(appId) {
    const config = appConfigs[appId];
    const releases = getAppReleases(appId);
    const status = appStatuses[appId] || { success: true };
    const latest = releases[0];
    const asset = latest?.assets.find(a => a.name.endsWith('.apk')) || latest?.assets[0];
    const name = currentLang === 'he' ? (config.name_he || config.name) : config.name;
    const desc = currentLang === 'he' ? (config.description_he || config.description) : config.description;
    const isOk = status.success !== false;
    const visual = appVisuals[appId] || defaultVisual;

    modalContent.innerHTML = `
        <div class="flex flex-col items-center mb-6 pt-2">
            <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-[1.5rem] sm:rounded-[2rem] shadow-xl mb-4 bg-white dark:bg-zinc-950 flex items-center justify-center ring-4 ring-white dark:ring-zinc-800/50 p-2 overflow-hidden">
                <img src="${config.icon_url}" class="w-full h-full object-contain rounded-[1rem]" onerror="this.parentElement.innerHTML='<div class=\\'w-full h-full rounded-[1rem] ${visual.bg} flex items-center justify-center\\'><i data-lucide=\\'${visual.icon}\\' class=\\'w-10 h-10 ${visual.iconClass}\\'></i></div>'">
            </div>
            <h2 class="text-2xl sm:text-3xl font-bold text-zinc-900 dark:text-zinc-100 mb-1 text-center">${name}</h2>
            <p class="text-zinc-400 dark:text-zinc-500 font-mono text-xs sm:text-sm mb-4 break-all text-center px-4">${config.package_name}</p>
            
            ${config.maintainer ? `
                <div class="inline-flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800/50 px-4 py-2 rounded-full border border-zinc-200 dark:border-zinc-700/50 shadow-sm">
                    <div class="w-6 h-6 rounded-full bg-gradient-to-br from-rose-400 to-indigo-500 flex items-center justify-center text-white text-[10px] font-bold shadow-inner">
                        <i data-lucide="user" class="w-3 h-3"></i>
                    </div>
                    <span class="text-xs text-zinc-500 dark:text-zinc-400">
                        ${t('maintainedBy')} <span class="font-semibold text-zinc-700 dark:text-zinc-200">@${config.maintainer}</span>
                    </span>
                </div>
            ` : ''}
        </div>

        <div class="mb-6 px-1">
            <h3 class="font-bold text-zinc-900 dark:text-zinc-100 text-sm sm:text-base mb-2">About App</h3>
            <p class="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed whitespace-pre-wrap">${desc || 'No description available.'}</p>
        </div>

        ${!isOk ? `
            <div class="bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-900/30 rounded-2xl p-5 mb-6 text-left mx-1 shadow-sm">
                <div class="flex items-start gap-3">
                    <div class="w-10 h-10 rounded-full bg-rose-100 dark:bg-rose-900/50 flex items-center justify-center text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5">
                        <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <h4 class="text-rose-800 dark:text-rose-300 font-bold text-base mb-1">${t('patchErrorTooltip')}</h4>
                        <p class="text-sm text-rose-600/90 dark:text-rose-300 mb-3">
                            ${t('errorDetail').replace('{version}', status.failed_version || '?')}
                        </p>
                         ${status.error_message ? `
                         <div class="bg-white/60 dark:bg-black/20 p-3 rounded-lg border border-rose-100 dark:border-rose-900/20">
                            <p class="text-xs font-mono text-rose-600 dark:text-rose-400 break-words">${status.error_message}</p>
                         </div>` : ''}
                    </div>
                </div>
            </div>
        ` : ''}

        ${latest ? `
            <div class="bg-zinc-50 dark:bg-zinc-800/40 rounded-3xl p-5 sm:p-6 mb-6 border border-zinc-200 dark:border-zinc-700/50 shadow-sm relative overflow-hidden group">
                <div class="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none group-hover:bg-rose-500/10 transition-colors duration-500"></div>
                <div class="flex justify-between items-center mb-5 relative z-10">
                    <div>
                        <h3 class="font-bold text-zinc-900 dark:text-zinc-100 text-base sm:text-lg mb-1">${t('latestVersion')}</h3>
                        <div class="flex items-center gap-2">
                            <span class="bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-xs font-bold px-2 py-0.5 rounded-md">v${latest.tag_name.replace(/.*-v|v/, '')}</span>
                            <span class="text-xs text-zinc-500">${formatDate(latest.published_at)}</span>
                        </div>
                    </div>
                </div>
                
                ${asset ? `
                <a href="${asset.browser_download_url}" onclick="window.trackDownload('${appId}')"
                   class="relative z-10 w-full bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:scale-[1.02] active:scale-[0.98] font-bold py-4 px-6 rounded-2xl shadow-lg transition-all flex items-center justify-center gap-3 touch-manipulation group/dwn ring-1 ring-white/10 overflow-hidden">
                     <div class="absolute inset-0 bg-gradient-to-r from-rose-400 via-fuchsia-400 to-indigo-400 opacity-0 group-hover/dwn:opacity-20 transition-opacity duration-300"></div>
                     <i data-lucide="download" class="w-5 h-5 group-hover/dwn:animate-bounce relative z-10"></i>
                     <span class="text-base relative z-10">${t('downloadBtnFull')}</span>
                     <span class="text-zinc-300 dark:text-zinc-600 font-medium text-sm ml-auto bg-zinc-800 dark:bg-zinc-200 px-3 py-1 rounded-full relative z-10">${formatSize(asset.size)}</span>
                </a>
                ` : ''}
            </div>
        ` : ''}

        ${releases.length > 1 ? `
            <div class="border-t border-zinc-200 dark:border-zinc-800/50 pt-6 pb-2">
                <h3 class="font-bold text-zinc-900 dark:text-zinc-100 mb-4 px-1 text-sm sm:text-base flex items-center gap-2">
                    <i data-lucide="history" class="text-zinc-400 w-4 h-4"></i> ${t('olderVersions')}
                </h3>
                <div class="space-y-2.5 max-h-52 overflow-y-auto pr-2 custom-scrollbar">
                    ${releases.slice(1).map(r => {
        const a = r.assets.find(as => as.name.endsWith('.apk')) || r.assets[0];
        if (!a) return '';
        return `
                        <a href="${a.browser_download_url}" onclick="window.trackDownload('${appId}')" class="group flex items-center justify-between p-3.5 rounded-2xl bg-zinc-50 dark:bg-zinc-800/30 hover:bg-zinc-100 dark:hover:bg-zinc-800 active:bg-zinc-200 dark:active:bg-zinc-700 transition-all border border-transparent hover:border-zinc-200 dark:hover:border-zinc-700 touch-manipulation">
                            <div>
                                <div class="font-semibold text-zinc-700 dark:text-zinc-200 text-sm mb-0.5 transition-colors">v${r.tag_name.replace(/.*-v|v/, '')}</div>
                                <div class="text-xs text-zinc-500">${formatDate(r.published_at)}</div>
                            </div>
                            <div class="w-10 h-10 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center transition-colors overflow-hidden relative">
                                <div class="absolute inset-0 bg-gradient-to-tr from-rose-400 to-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                                <i data-lucide="download" class="text-zinc-400 w-4 h-4 group-hover:text-white transition-colors relative z-10"></i>
                            </div>
                        </a>
                        `;
    }).join('')}
                </div>
            </div>
        ` : ''}
    `;

    appModal.classList.remove('hidden');
    // Animate In
    requestAnimationFrame(() => {
        modalBackdrop.classList.replace('opacity-0', 'opacity-100');
        modalPanel.classList.remove('translate-y-full', 'opacity-0');
        modalPanel.classList.add('translate-y-0', 'opacity-100');
    });

    if (window.lucide) window.lucide.createIcons();
    document.body.style.overflow = 'hidden';
}

export function closeModal() {
    // Animate Out
    modalBackdrop.classList.add('opacity-0');
    modalPanel.classList.add('translate-y-full', 'scale-95', 'opacity-0');
    modalPanel.classList.remove('scale-100');
    // Wait for animation
    setTimeout(() => {
        appModal.classList.add('hidden');
        document.body.style.overflow = '';
    }, 400); // Matched with transition duration
}

window.openAppModal = openModal; // Expose for inline onclick in grid

window.trackDownload = (appId) => {
    if (window.goatcounter && window.goatcounter.count) {
        window.goatcounter.count({
            path: 'download-' + appId,
            event: true
        });
    }
    console.log(`Tracking download for ${appId}`);
};

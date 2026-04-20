import { appConfigs, appStatuses, appStats, getAppReleases } from './api.js';
import { currentLang, t, formatDate, formatSize, formatNumber } from './i18n.js';

export const appGrid = document.getElementById('appGrid');
export const emptyState = document.getElementById('emptyState');
export const appModal = document.getElementById('appModal');
export const modalBackdrop = document.getElementById('modalBackdrop');
export const modalPanel = document.getElementById('modalPanel');
export const modalContent = document.getElementById('modalContent');
export const loader = document.getElementById('loader');

export function renderGrid() {
    appGrid.innerHTML = Object.keys(appConfigs).map(appId => {
        const config = appConfigs[appId];
        const status = appStatuses[appId] || { success: true };
        const releases = getAppReleases(appId);
        const latest = releases[0];
        const isOk = status.success !== false;
        const name = currentLang === 'he' ? (config.name_he || config.name) : config.name;
        const desc = currentLang === 'he' ? (config.description_he || config.description) : config.description;
        const downloads = appStats[appId] || 0;

        return `
        <div class="group relative bg-white/80 dark:bg-slate-900/80 backdrop-blur-md rounded-3xl p-5 border border-white/20 dark:border-slate-700/50 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.1)] active:scale-[0.98] active:bg-slate-50 dark:active:bg-slate-800 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col h-full touch-manipulation" onclick="window.openAppModal('${appId}')">
            
            <div class="flex items-start justify-between mb-4">
                <img src="${config.icon_url}" alt="${name}" 
                     class="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-white dark:bg-slate-950 object-cover shadow-sm flex-shrink-0"
                     onerror="this.src='https://placehold.co/64?text=${name[0]}'">
                <div class="flex flex-col items-end gap-1.5">
                    ${!isOk ? `<span class="bg-red-500/10 text-red-600 dark:text-red-400 text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5 border border-red-500/20 backdrop-blur-sm shadow-sm"><i class="fa-solid fa-triangle-exclamation"></i> Error</span>` : ''}
                    <span class="bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-[10px] sm:text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1.5 border border-slate-200/50 dark:border-slate-700/50 shadow-sm"><i class="fa-solid fa-download opacity-70"></i> ${formatNumber(downloads)}</span>
                </div>
            </div>

            <h3 class="font-bold text-lg text-slate-900 dark:text-white mb-0.5 line-clamp-1 group-hover:text-brand-500 dark:group-hover:text-brand-400 transition-colors">${name}</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 font-mono mb-2 truncate">${config.package_name}</p>
            <p class="text-sm text-slate-600 dark:text-slate-300 line-clamp-2 mb-4 flex-grow leading-relaxed">${desc || ''}</p>
            
            <div class="flex items-center justify-between mt-auto pt-4 border-t border-slate-100 dark:border-slate-800/50">
                <div class="flex flex-col">
                    <span class="text-xs text-slate-400 uppercase tracking-wider font-medium">${latest ? 'v' + latest.tag_name.replace(/.*-v|v/, '') : '-'}</span>
                     <span class="text-[10px] text-slate-400">${latest ? formatDate(latest.published_at) : ''}</span>
                </div>
                
                <button class="bg-brand-50 hover:bg-brand-100 dark:bg-brand-500/10 dark:hover:bg-brand-500/20 active:bg-brand-200 dark:active:bg-brand-500/30 text-brand-600 dark:text-brand-400 font-bold py-2 px-5 rounded-full text-sm transition-all touch-manipulation">
                    ${t('downloadBtn')}
                </button>
            </div>
        </div>
        `;
    }).join('');
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

    modalContent.innerHTML = `
        <div class="flex flex-col items-center mb-6 pt-2">
            <img src="${config.icon_url}" class="w-20 h-20 sm:w-24 sm:h-24 rounded-[1.5rem] sm:rounded-[2rem] shadow-xl mb-4 bg-white dark:bg-slate-800 ring-4 ring-white dark:ring-slate-800/50" onerror="this.src='https://placehold.co/96?text=${name[0]}'">
            <h2 class="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-1 text-center">${name}</h2>
            <p class="text-slate-400 font-mono text-xs sm:text-sm mb-4 break-all text-center px-4">${config.package_name}</p>
            
            ${config.maintainer ? `
                <div class="inline-flex items-center gap-2 bg-slate-50 dark:bg-slate-800/50 px-4 py-2 rounded-full border border-slate-100 dark:border-slate-700/50 shadow-sm">
                    <div class="w-6 h-6 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-[10px] font-bold shadow-inner">
                        <i class="fa-solid fa-user-astronaut"></i>
                    </div>
                    <span class="text-xs text-slate-500 dark:text-slate-400">
                        ${t('maintainedBy')} <span class="font-semibold text-slate-700 dark:text-slate-200">@${config.maintainer}</span>
                    </span>
                </div>
            ` : ''}
        </div>

        <div class="mb-6 px-1">
            <h3 class="font-bold text-slate-900 dark:text-white text-sm sm:text-base mb-2">About App</h3>
            <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">${desc || 'No description available.'}</p>
        </div>

        ${!isOk ? `
            <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 rounded-2xl p-5 mb-6 text-left mx-1 shadow-sm">
                <div class="flex items-start gap-3">
                    <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5">
                        <i class="fa-solid fa-triangle-exclamation text-lg"></i>
                    </div>
                    <div>
                        <h4 class="text-red-800 dark:text-red-300 font-bold text-base mb-1">${t('errorTitle')}</h4>
                        <p class="text-sm text-red-600/90 dark:text-red-300 mb-3">
                            ${t('errorDetail').replace('{version}', status.failed_version || '?')}
                        </p>
                         ${status.error_message ? `
                         <div class="bg-white/60 dark:bg-black/20 p-3 rounded-lg border border-red-100 dark:border-red-900/20">
                            <p class="text-xs font-mono text-red-600 dark:text-red-400 break-words">${status.error_message}</p>
                         </div>` : ''}
                    </div>
                </div>
            </div>
        ` : ''}

        ${latest ? `
            <div class="bg-slate-50 dark:bg-slate-800/40 rounded-3xl p-5 sm:p-6 mb-6 border border-slate-100 dark:border-slate-700/50 shadow-sm relative overflow-hidden">
                <div class="absolute top-0 right-0 w-32 h-32 bg-brand-500/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
                <div class="flex justify-between items-center mb-5 relative z-10">
                    <div>
                        <h3 class="font-bold text-slate-900 dark:text-white text-base sm:text-lg mb-1">${t('latestVersion')}</h3>
                        <div class="flex items-center gap-2">
                            <span class="bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold px-2 py-0.5 rounded-md">v${latest.tag_name.replace(/.*-v|v/, '')}</span>
                            <span class="text-xs text-slate-500">${formatDate(latest.published_at)}</span>
                        </div>
                    </div>
                </div>
                
                ${asset ? `
                <a href="${asset.browser_download_url}" onclick="window.trackDownload('${appId}')"
                   class="relative z-10 w-full bg-brand-600 hover:bg-brand-500 active:bg-brand-700 active:scale-[0.98] text-white font-bold py-4 px-6 rounded-2xl shadow-lg shadow-brand-500/25 transition-all flex items-center justify-center gap-3 touch-manipulation group ring-1 ring-white/10">
                     <i class="fa-solid fa-download text-lg group-hover:animate-bounce"></i>
                     <span class="text-base">${t('downloadBtnFull')}</span>
                     <span class="text-brand-100 font-medium text-sm ml-auto bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">${formatSize(asset.size)}</span>
                </a>
                ` : ''}
            </div>
        ` : ''}

        ${releases.length > 1 ? `
            <div class="border-t border-slate-100 dark:border-slate-800/50 pt-6 pb-2">
                <h3 class="font-bold text-slate-900 dark:text-white mb-4 px-1 text-sm sm:text-base flex items-center gap-2">
                    <i class="fa-solid fa-clock-rotate-left text-slate-400 text-sm"></i> ${t('olderVersions')}
                </h3>
                <div class="space-y-2.5 max-h-52 overflow-y-auto pr-2 custom-scrollbar">
                    ${releases.slice(1).map(r => {
        const a = r.assets.find(as => as.name.endsWith('.apk')) || r.assets[0];
        if (!a) return '';
        return `
                        <a href="${a.browser_download_url}" onclick="window.trackDownload('${appId}')" class="group flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/30 hover:bg-white dark:hover:bg-slate-800 active:bg-slate-100 dark:active:bg-slate-700 transition-all border border-transparent hover:border-slate-200 dark:hover:border-slate-700 hover:shadow-sm touch-manipulation">
                            <div>
                                <div class="font-semibold text-slate-700 dark:text-slate-200 text-sm mb-0.5 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">v${r.tag_name.replace(/.*-v|v/, '')}</div>
                                <div class="text-xs text-slate-500">${formatDate(r.published_at)}</div>
                            </div>
                            <div class="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 group-hover:bg-brand-50 dark:group-hover:bg-brand-500/10 flex items-center justify-center transition-colors">
                                <i class="fa-solid fa-cloud-arrow-down text-slate-400 group-hover:text-brand-500 transition-colors"></i>
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
        modalBackdrop.classList.remove('opacity-0');
        modalPanel.classList.remove('translate-y-full', 'scale-95', 'opacity-0');
        modalPanel.classList.add('scale-100');
    });

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

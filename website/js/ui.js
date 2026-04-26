import { appConfigs, appStatuses, appStats, getAppReleases } from './api.js';
import { currentLang, t, formatDate, formatSize, formatNumber } from './i18n.js';

export const appGrid = document.getElementById('appGrid');
export const emptyState = document.getElementById('emptyState');
export const loader = document.getElementById('loader');
export const gridContainer = document.getElementById('gridContainer');
export const featuredAppArea = document.getElementById('featuredAppArea');
export const appPage = document.getElementById('appPage');
export const lightbox = document.getElementById('lightbox');
export const lightboxImage = document.getElementById('lightboxImage');
export const lightboxCounter = document.getElementById('lightboxCounter');

let currentScreenshots = [];
let currentScreenshotIndex = 0;
let activeCategory = 'all';

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
    <div class="group relative rounded-2xl transition-all duration-500 p-[1px] hover:-translate-y-1 cursor-pointer app-card-mobile" onclick="window.location.hash='#app/${appId}'">
        <div class="absolute inset-0 rounded-2xl transition-opacity duration-500 bg-zinc-200/50 dark:bg-zinc-800/50 group-hover:opacity-0 desktop-only"></div>
        <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-rose-400/80 via-fuchsia-400/80 to-indigo-400/80 opacity-0 group-hover:opacity-100 transition-opacity duration-500 desktop-only"></div>
        
        <div class="relative h-full flex flex-col p-6 rounded-[15px] bg-white dark:bg-[#15151A] shadow-sm group-hover:shadow-xl transition-shadow duration-500">
            <div class="flex items-start justify-between mb-5">
                <div class="w-14 h-14 rounded-xl shadow-sm relative overflow-hidden bg-white dark:bg-zinc-950 p-1 flex items-center justify-center icon-container">
                    <img src="${config.icon_url}" class="w-full h-full object-contain rounded-lg" onerror="this.parentElement.innerHTML='<div class=\\'w-full h-full rounded-lg ${visual.bg} flex items-center justify-center\\'><i data-lucide=\\'${visual.icon}\\' class=\\'w-6 h-6 ${visual.iconClass}\\'></i></div>'">
                </div>
                
                <div class="flex flex-col items-end gap-2 desktop-only">
                    ${!isOk ? `<span title="${t('patchErrorTooltip')}" class="inline-flex items-center justify-center p-1 rounded-full bg-rose-500/10 text-rose-500 dark:text-rose-400"><i data-lucide="alert-circle" class="w-4 h-4"></i></span>` : ''}
                    <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono uppercase tracking-widest bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200/50 dark:border-zinc-700/50">
                        <i data-lucide="download" class="w-3.5 h-3.5"></i> ${formatNumber(downloads)}
                    </span>
                </div>
            </div>

            <div class="flex-1 space-y-2 mb-6 info-container">
                <div class="flex justify-between items-start">
                    <h3 class="font-semibold text-base text-zinc-900 dark:text-zinc-100">${name}</h3>
                </div>
                <p class="font-mono text-xs text-zinc-500 dark:text-zinc-500 truncate package-name">${config.package_name}</p>
                <p class="text-sm leading-relaxed line-clamp-2 text-zinc-600 dark:text-zinc-400">${desc || ''}</p>
                
                ${config.maintainer ? `
                <div class="flex items-center gap-1.5 mt-2 opacity-70 group-hover:opacity-100 transition-opacity maintainer-tag">
                    <div class="w-5 h-5 rounded-full bg-gradient-to-tr from-rose-400 to-indigo-500 p-[1px]">
                         <div class="w-full h-full rounded-full bg-white dark:bg-[#15151A] flex items-center justify-center">
                            <i data-lucide="user" class="w-2.5 h-2.5 text-zinc-500"></i>
                         </div>
                    </div>
                    <span class="text-xs text-zinc-500 dark:text-zinc-400 font-medium">@${config.maintainer}</span>
                </div>
                ` : ''}
            </div>

            <div class="flex items-end justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800/60 action-container">
                <div class="font-mono text-xs uppercase tracking-widest space-y-1.5 text-zinc-500 dark:text-zinc-500 desktop-only">
                    <div class="text-zinc-800 dark:text-zinc-300 font-bold">${latest ? 'v' + latest.tag_name.replace(/.*-v|v/, '') : '-'}</div>
                    <div class="flex items-center gap-1 opacity-80">
                         ${latest ? formatDate(latest.published_at) : ''}
                    </div>
                </div>
                
                <button onclick="${asset ? `event.stopPropagation(); window.location.href='${asset.browser_download_url}';` : `event.stopPropagation();`}" 
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
    <section class="space-y-4 relative group" onclick="window.location.hash='#app/${appId}'" style="cursor: pointer;">
        <div class="flex items-center gap-2">
            <i data-lucide="sparkles" class="w-4 h-4 text-rose-400"></i>
            <h2 class="text-sm font-sans uppercase tracking-[0.15em] font-bold text-zinc-500 dark:text-zinc-500">${t('mostDownloads')}</h2>
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
                            <h3 class="text-xl sm:text-3xl font-semibold text-zinc-900 dark:text-zinc-100">${name}</h3>
                            <span class="text-xs sm:text-sm font-mono px-2.5 py-1 rounded border bg-zinc-100 border-zinc-200 text-zinc-600 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-400">
                                ${latest ? 'v' + latest.tag_name.replace(/.*-v|v/, '') : '-'}
                            </span>
                        </div>
                        <p class="font-mono text-xs sm:text-sm text-zinc-500 dark:text-zinc-500">${config.package_name}</p>
                        <p class="text-sm sm:text-base leading-relaxed text-zinc-700 dark:text-zinc-400 max-w-xl">
                            ${desc}
                        </p>
                        ${config.maintainer ? `
                        <div class="flex items-center gap-2 opacity-80">
                             <div class="w-6 h-6 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                                <i data-lucide="user" class="w-3.5 h-3.5 text-zinc-500"></i>
                             </div>
                             <span class="text-sm text-zinc-600 font-medium">${t('maintainedBy')} @${config.maintainer}</span>
                        </div>
                        ` : ''}
                    </div>

                    <div class="flex flex-col sm:items-end gap-3 w-full sm:w-auto mt-2 sm:mt-0 pt-4 sm:pt-0 border-t sm:border-t-0 border-zinc-100 dark:border-zinc-800">
                        <button onclick="${asset ? `event.stopPropagation(); window.location.href='${asset.browser_download_url}';` : `event.stopPropagation();`}" 
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

export function renderCategories() {
    const container = document.getElementById('categoryContainer');
    if (!container) return;

    const categories = new Set();
    Object.values(appConfigs).forEach(config => {
        if (config.category) categories.add(config.category);
    });

    const sortedCategories = Array.from(categories).sort();
    
    let html = `
        <button onclick="window.setCategory('all')" class="px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider transition-all border ${activeCategory === 'all' ? 'bg-zinc-900 border-zinc-900 text-white dark:bg-white dark:border-white dark:text-black shadow-lg' : 'bg-white border-zinc-200 text-zinc-500 hover:border-zinc-300 dark:bg-zinc-900 dark:border-zinc-800 dark:hover:border-zinc-700 shadow-sm'}">
            ${currentLang === 'he' ? 'הכל' : 'All'}
        </button>
    `;

    sortedCategories.forEach(cat => {
        const cat_he = Object.values(appConfigs).find(c => c.category === cat)?.category_he || cat;
        const displayName = currentLang === 'he' ? cat_he : cat;
        const isActive = activeCategory === cat;

        html += `
            <button onclick="window.setCategory('${cat}')" class="px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider transition-all border ${isActive ? 'bg-zinc-900 border-zinc-900 text-white dark:bg-white dark:border-white dark:text-black shadow-lg' : 'bg-white border-zinc-200 text-zinc-500 hover:border-zinc-300 dark:bg-zinc-900 dark:border-zinc-800 dark:hover:border-zinc-700 shadow-sm'}">
                ${displayName}
            </button>
        `;
    });

    container.innerHTML = html;
    container.classList.remove('hidden');
}

window.setCategory = (cat) => {
    activeCategory = cat;
    renderCategories();
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value : '';
    renderGrid(query, 'default');
};

export function renderGrid(query = '', sortBy = 'default') {
    renderCategories();
    let appsList = Object.keys(appConfigs);
    
    // Sort apps by downloads to find the featured app
    const sortedByStats = [...appsList].sort((a, b) => (appStats[b] || 0) - (appStats[a] || 0));
    const featuredAppId = sortedByStats[0];

    if (sortBy === 'downloads') {
        appsList = sortedByStats;
    }

    let filteredApps = appsList;
    
    // Filter by Category first
    if (activeCategory !== 'all') {
        filteredApps = filteredApps.filter(appId => appConfigs[appId].category === activeCategory);
    }

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

        if (!query && activeCategory === 'all' && featuredAppId && appConfigs[featuredAppId]) {
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

export function renderAppPage(appId) {
    const config = appConfigs[appId];
    const releases = getAppReleases(appId);
    const status = appStatuses[appId] || { success: true };
    const latest = releases[0];
    const asset = latest?.assets.find(a => a.name.endsWith('.apk')) || latest?.assets[0];
    const name = currentLang === 'he' ? (config.name_he || config.name) : (config.name_play || config.name);
    const desc = currentLang === 'he' ? (config.full_description_he || config.full_description || config.description_he || config.description) : (config.full_description || config.description);
    const shortDesc = currentLang === 'he' ? (config.description_he || config.description) : (config.description);
    const isOk = status.success !== false;
    const visual = appVisuals[appId] || defaultVisual;
    const screenshots = (currentLang === 'he' && config.screenshots_he && config.screenshots_he.length > 0) ? config.screenshots_he : (config.screenshots || []);
    const category = currentLang === 'he' ? (config.category_he || config.category || 'Application') : (config.category || 'Application');

    currentScreenshots = screenshots;
    currentScreenshotIndex = 0;

    // Hide grid and featured
    gridContainer.classList.add('hidden');
    featuredAppArea.classList.add('hidden');
    appPage.classList.remove('hidden');

    appPage.innerHTML = `
        <!-- Back Button -->
        <button onclick="window.location.hash=''" class="mb-8 flex items-center gap-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors group">
            <i data-lucide="arrow-left" class="w-5 h-5 transition-transform group-hover:-translate-x-1 ${currentLang === 'he' ? 'rotate-180 group-hover:translate-x-1' : ''}"></i>
            <span class="font-medium">${t('backToRepo')}</span>
        </button>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-12">
            <!-- Left Column: Icon & Info -->
            <div class="lg:col-span-2 space-y-10">
                
                <!-- Hero Info -->
                <div class="flex flex-col sm:flex-row items-center sm:items-start gap-8">
                    <div class="w-32 h-32 sm:w-40 sm:h-40 shrink-0 rounded-[2.5rem] bg-white dark:bg-zinc-900 p-3 shadow-2xl relative overflow-hidden ring-1 ring-zinc-200 dark:ring-zinc-800 flex items-center justify-center">
                        <img src="${config.icon_url}" class="w-full h-full object-contain rounded-[1.75rem]" onerror="this.src='website/images/favicon.png'">
                    </div>
                    
                    <div class="flex-1 text-center sm:text-left space-y-4">
                        <div class="space-y-1">
                            <h1 class="text-3xl sm:text-5xl font-bold text-zinc-900 dark:text-zinc-100 tracking-tight">${name}</h1>
                            <p class="text-zinc-500 dark:text-zinc-500 font-mono text-sm sm:text-base">${config.package_name}</p>
                        </div>
                        
                        <div class="flex flex-wrap items-center justify-center sm:justify-start gap-3">
                            <span class="px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 text-xs font-bold border border-zinc-200 dark:border-zinc-700">${category}</span>
                            ${latest ? `<span class="px-3 py-1 rounded-full bg-rose-500/10 text-rose-500 text-xs font-bold border border-rose-500/20">v${latest.tag_name.replace(/.*-v|v/, '')}</span>` : ''}
                            ${config.maintainer ? `
                                <span class="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-500 text-xs font-bold border border-indigo-500/20">@${config.maintainer}</span>
                            ` : ''}
                        </div>

                        <div class="pt-4">
                            ${asset ? `
                                <a href="${asset.browser_download_url}" class="inline-flex items-center gap-3 px-10 py-4 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-full font-bold text-lg shadow-xl hover:scale-105 active:scale-95 transition-all">
                                    <i data-lucide="download" class="w-5 h-5"></i>
                                    ${t('downloadBtnFull')}
                                    <span class="ml-2 opacity-50 text-sm font-normal border-l border-white/20 dark:border-black/20 pl-3 ${currentLang === 'he' ? 'mr-2 ml-0 border-l-0 border-r pr-3 pl-0' : ''}">${formatSize(asset.size)}</span>
                                </a>
                            ` : ''}
                        </div>
                    </div>
                </div>

                <!-- Screenshots Carousel -->
                ${screenshots.length > 0 ? `
                    <div class="space-y-4 relative group/gallery">
                        <div class="flex items-center justify-between">
                            <h3 class="text-xl font-bold flex items-center gap-2">
                                <i data-lucide="image" class="w-5 h-5 text-zinc-400"></i>
                                ${t('screenshots')}
                            </h3>
                            <span class="text-xs text-zinc-400 font-medium uppercase tracking-wider">${t('clickToEnlarge')}</span>
                        </div>
                        
                        <div class="relative">
                            <div id="screenshotTrack" class="flex gap-4 overflow-x-auto pb-6 no-scrollbar snap-x touch-pan-x scroll-smooth">
                                ${screenshots.map((s, idx) => `
                                    <div onclick="window.openLightbox(${idx})" class="screenshot-item shrink-0 w-64 sm:w-72 aspect-[9/16] rounded-2xl overflow-hidden shadow-lg bg-zinc-200 dark:bg-zinc-800 snap-start ring-1 ring-zinc-200 dark:ring-zinc-800">
                                        <img src="${s}" class="w-full h-full object-cover" loading="lazy" onerror="this.parentElement.style.display='none'">
                                    </div>
                                `).join('')}
                            </div>
                            
                            <!-- Desktop Scroll Buttons -->
                            <button onclick="document.getElementById('screenshotTrack').scrollBy({left: -400, behavior: 'smooth'})" class="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 dark:bg-zinc-900/80 shadow-lg border border-zinc-200 dark:border-zinc-800 opacity-0 group-hover/gallery:opacity-100 transition-opacity hidden sm:flex items-center justify-center">
                                <i data-lucide="chevron-left" class="w-6 h-6"></i>
                            </button>
                            <button onclick="document.getElementById('screenshotTrack').scrollBy({left: 400, behavior: 'smooth'})" class="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 dark:bg-zinc-900/80 shadow-lg border border-zinc-200 dark:border-zinc-800 opacity-0 group-hover/gallery:opacity-100 transition-opacity hidden sm:flex items-center justify-center">
                                <i data-lucide="chevron-right" class="w-6 h-6"></i>
                            </button>
                        </div>
                    </div>
                ` : ''}

                <!-- Description -->
                <div class="space-y-6">
                    <h3 class="text-xl font-bold flex items-center gap-2">
                        <i data-lucide="info" class="w-5 h-5 text-zinc-400"></i>
                        ${t('aboutApp')}
                    </h3>
                    <div class="${currentLang === 'he' ? 'rtl' : ''} space-y-8">
                        <!-- Custom Base Description -->
                        <div class="text-xl sm:text-2xl text-zinc-900 dark:text-zinc-100 font-medium leading-relaxed">
                            ${shortDesc}
                        </div>

                        <!-- Official Full Description (Expandable with Fade) -->
                        ${desc && desc !== shortDesc ? `
                            <div class="pt-8 border-t border-zinc-100 dark:border-zinc-800/50">
                                <div class="flex items-center gap-2 text-xs font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-[0.2em] mb-4">
                                    <i data-lucide="quote" class="w-3 h-3"></i>
                                    ${t('officialDescription')}
                                </div>
                                <div class="relative group cursor-pointer" onclick="const c = this.querySelector('.desc-content'); c.classList.remove('max-h-32', 'overflow-hidden'); c.classList.add('max-h-[5000px]'); this.querySelector('.expand-overlay').classList.add('hidden'); this.classList.remove('cursor-pointer'); this.classList.add('cursor-auto');">
                                    <div class="desc-content prose dark:prose-invert max-w-none text-zinc-600 dark:text-zinc-400 italic leading-relaxed pl-6 border-l-2 border-zinc-100 dark:border-zinc-800 ${currentLang === 'he' ? 'pl-0 pr-6 border-l-0 border-r-2' : ''} max-h-32 overflow-hidden transition-all duration-700 ease-in-out">
                                        ${desc}
                                    </div>
                                    <div class="expand-overlay absolute bottom-0 left-0 w-full h-20 bg-gradient-to-t from-[#F9F9FA] via-[#F9F9FA]/90 to-transparent dark:from-[#0E0E12] dark:via-[#0E0E12]/90 pointer-events-none transition-opacity duration-300 flex flex-col justify-end items-center pb-2">
                                        <div class="text-xs font-bold text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-100 transition-colors flex items-center gap-1">
                                            <span>${t('readMore')}</span>
                                            <i data-lucide="chevron-down" class="w-3 h-3"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>

            <!-- Right Column: Metadata & History -->
            <div class="space-y-8">
                ${!isOk ? `
                    <div class="bg-rose-500/10 border border-rose-500/20 rounded-3xl p-6 space-y-3">
                        <div class="flex items-center gap-2 text-rose-500">
                            <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                            <h4 class="font-bold">${t('buildIssue')}</h4>
                        </div>
                        <p class="text-sm text-rose-600/90 dark:text-rose-400">
                            ${currentLang === 'he' ? `ניסיון הפאץ' האחרון (v${status.failed_version || '?'}) נכשל. גרסאות קודמות עשויות להיות זמינות.` : `The latest patch attempt (v${status.failed_version || '?'}) failed. Previous versions may still be available.`}
                        </p>
                    </div>
                ` : ''}

                <!-- Stats Card -->
                <div class="bg-zinc-50 dark:bg-zinc-900/50 rounded-3xl p-6 border border-zinc-200 dark:border-zinc-800 space-y-4">
                    <h4 class="font-bold text-sm uppercase tracking-wider text-zinc-400">${t('technicalDetails')}</h4>
                    <div class="space-y-3">
                        <div class="flex justify-between items-center py-2 border-b border-zinc-100 dark:border-zinc-800">
                            <span class="text-zinc-500 text-sm">${t('downloads')}</span>
                            <span class="font-mono text-sm font-bold">${formatNumber(appStats[appId] || 0)}</span>
                        </div>
                        <div class="flex justify-between items-center py-2 border-b border-zinc-100 dark:border-zinc-800">
                            <span class="text-zinc-500 text-sm">${t('sourceTitle')}</span>
                            <span class="text-sm capitalize font-bold">${config.source || 'Unknown'}</span>
                        </div>
                        <div class="flex justify-between items-center py-2">
                            <span class="text-zinc-500 text-sm">${t('lastUpdate')}</span>
                            <span class="text-sm font-bold">${latest ? formatDate(latest.published_at) : 'N/A'}</span>
                        </div>
                    </div>
                </div>

                <!-- Version History -->
                ${releases.length > 1 ? `
                    <div class="space-y-4">
                        <h4 class="font-bold text-sm uppercase tracking-wider text-zinc-400">${t('olderVersions')}</h4>
                        <div class="space-y-2">
                            ${releases.slice(1).map(r => {
                                const a = r.assets.find(as => as.name.endsWith('.apk')) || r.assets[0];
                                if (!a) return '';
                                return `
                                    <a href="${a.browser_download_url}" class="flex items-center justify-between p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-900/50 border border-transparent hover:border-zinc-200 dark:hover:border-zinc-800 transition-all group">
                                        <div>
                                            <div class="font-bold text-sm">v${r.tag_name.replace(/.*-v|v/, '')}</div>
                                            <div class="text-[10px] text-zinc-500 uppercase tracking-tight">${formatDate(r.published_at)}</div>
                                        </div>
                                        <i data-lucide="download" class="w-4 h-4 text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-100 transition-colors"></i>
                                    </a>
                                `;
                            }).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    // Re-initialize Lucide
    if (window.lucide) window.lucide.createIcons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Lightbox Logic
export function openLightbox(index) {
    currentScreenshotIndex = index;
    updateLightbox();
    lightbox.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

export function closeLightbox() {
    lightbox.classList.add('hidden');
    document.body.style.overflow = '';
}

function updateLightbox() {
    if (!currentScreenshots || currentScreenshots.length === 0) {
        lightbox.classList.add('hidden');
        document.body.style.overflow = '';
        return;
    }
    lightboxImage.src = currentScreenshots[currentScreenshotIndex];
    lightboxCounter.textContent = `${currentScreenshotIndex + 1} / ${currentScreenshots.length}`;
}

export function nextScreenshot() {
    currentScreenshotIndex = (currentScreenshotIndex + 1) % currentScreenshots.length;
    updateLightbox();
}

export function prevScreenshot() {
    currentScreenshotIndex = (currentScreenshotIndex - 1 + currentScreenshots.length) % currentScreenshots.length;
    updateLightbox();
}

// Expose to window for inline onclicks
window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;
window.nextScreenshot = nextScreenshot;
window.prevScreenshot = prevScreenshot;

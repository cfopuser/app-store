import { currentLang, i18n, setLang, t } from './i18n.js';
import { fetchAppData, appConfigs } from './api.js';
import { renderGrid, loader, appGrid, emptyState } from './ui.js';
import { openRequestForm } from './requestForm.js';


let isDark = localStorage.getItem('theme') === 'dark' ||
    (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);

let currentSort = 'default';

function updateTheme() {
    const html = document.documentElement;
    const themeBtnOuter = document.getElementById('themeToggle');
    
    if (isDark) {
        html.classList.add('dark');
        themeBtnOuter.innerHTML = `<i data-lucide="sun" id="themeIcon" class="w-4 h-4"></i>`;
    } else {
        html.classList.remove('dark');
        themeBtnOuter.innerHTML = `<i data-lucide="moon" id="themeIcon" class="w-4 h-4"></i>`;
    }
    
    if (window.lucide) {
        window.lucide.createIcons({
            attrs: {
                class: 'w-4 h-4'
            },
            nameAttr: 'data-lucide'
        });
    }
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function toggleTheme() {
    isDark = !isDark;
    updateTheme();
}

function updateLangUI() {
    document.documentElement.dir = currentLang === 'he' ? 'rtl' : 'ltr';
    document.documentElement.lang = currentLang;

    document.querySelectorAll('[data-key]').forEach(el => {
        const key = el.getAttribute('data-key');
        const val = t(key);
        if (val !== key) el.textContent = val;
    });

    document.querySelectorAll('[data-key-placeholder]').forEach(el => {
        const key = el.getAttribute('data-key-placeholder');
        if (i18n[currentLang][key]) el.placeholder = i18n[currentLang][key];
    });

    document.getElementById('langLabel').textContent = i18n[currentLang].langLabel;
    
    // Re-render grid or app page
    if (Object.keys(appConfigs).length > 0) {
        handleRoute();
    }
}

function toggleLang() {
    setLang(currentLang === 'en' ? 'he' : 'en');
    updateLangUI();
}

async function init() {
    updateTheme();
    updateLangUI();

    const success = await fetchAppData();
    loader.classList.add('hidden');

    if (success && Object.keys(appConfigs).length > 0) {
        handleRoute();
    } else {
        emptyState.classList.remove('hidden');
    }
}

function handleRoute() {
    const hash = window.location.hash;
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value : '';

    if (hash.startsWith('#app/')) {
        const appId = hash.split('/')[1];
        if (appConfigs[appId]) {
            import('./ui.js').then(m => m.renderAppPage(appId));
        } else {
            window.location.hash = '';
        }
    } else {
        import('./ui.js').then(m => {
            m.renderGrid(query, currentSort);
            document.getElementById('appPage').classList.add('hidden');
            document.getElementById('gridContainer').classList.remove('hidden');
            if (m.featuredAppArea) m.featuredAppArea.classList.remove('hidden');
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('langToggle').addEventListener('click', toggleLang);

    // Lightbox events
    const closeLightbox = () => import('./ui.js').then(m => m.closeLightbox());
    const nextScreenshot = () => import('./ui.js').then(m => m.nextScreenshot());
    const prevScreenshot = () => import('./ui.js').then(m => m.prevScreenshot());

    document.getElementById('closeLightbox').addEventListener('click', closeLightbox);
    document.getElementById('nextScreenshot').addEventListener('click', nextScreenshot);
    document.getElementById('prevScreenshot').addEventListener('click', prevScreenshot);
    document.getElementById('lightbox').addEventListener('click', e => {
        if (e.target.id === 'lightbox') closeLightbox();
    });

    document.addEventListener('keydown', e => { 
        if (e.key === 'Escape') {
            if (!document.getElementById('lightbox').classList.contains('hidden')) {
                closeLightbox();
            } else if (window.location.hash !== '') {
                window.location.hash = '';
            }
        } 
        if (!document.getElementById('lightbox').classList.contains('hidden')) {
            if (e.key === 'ArrowRight') nextScreenshot();
            if (e.key === 'ArrowLeft') prevScreenshot();
        }
    });

    // Wire up all Request App buttons to the custom form modal
    document.querySelectorAll('#requestAppBtn, #requestAppBtnMobile').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault();
            openRequestForm();
        });
    });


    document.getElementById('searchInput').addEventListener('input', (e) => {
        renderGrid(e.target.value, currentSort);
        // Sync with mobile search if visible
        const mobSearch = document.getElementById('mobileSearchInput');
        if (mobSearch) mobSearch.value = e.target.value;
    });

    const mobSearch = document.getElementById('mobileSearchInput');
    if (mobSearch) {
        mobSearch.addEventListener('input', (e) => {
            renderGrid(e.target.value, currentSort);
            // Sync with desktop search
            document.getElementById('searchInput').value = e.target.value;
        });
    }

    const mobBtn = document.getElementById('mobileSearchBtn');
    if (mobBtn) {
        mobBtn.addEventListener('click', () => {
            const container = document.getElementById('mobileSearchContainer');
            container.classList.toggle('hidden');
            if (!container.classList.contains('hidden')) {
                document.getElementById('mobileSearchInput').focus();
            }
        });
    }

    const sortBtn = document.getElementById('sortDownloads');
    if (sortBtn) {
        sortBtn.addEventListener('click', () => {
            currentSort = currentSort === 'downloads' ? 'default' : 'downloads';
            
            // Visual feedback - highlight pill when active
            if (currentSort === 'downloads') {
                sortBtn.classList.add('border-rose-400/60', 'dark:border-rose-500/50', 'bg-rose-50', 'dark:bg-rose-950/30', 'text-rose-600', 'dark:text-rose-400');
                sortBtn.classList.remove('border-zinc-200', 'dark:border-zinc-700/80', 'bg-zinc-100', 'dark:bg-zinc-800/60', 'text-zinc-500', 'dark:text-zinc-400');
            } else {
                sortBtn.classList.remove('border-rose-400/60', 'dark:border-rose-500/50', 'bg-rose-50', 'dark:bg-rose-950/30', 'text-rose-600', 'dark:text-rose-400');
                sortBtn.classList.add('border-zinc-200', 'dark:border-zinc-700/80', 'bg-zinc-100', 'dark:bg-zinc-800/60', 'text-zinc-500', 'dark:text-zinc-400');
            }

            const query = document.getElementById('searchInput').value;
            renderGrid(query, currentSort);
        });
    }

    // --- Mobile Bottom Navigation Logic ---
    const navHome = document.getElementById('navHome');
    const navSearch = document.getElementById('navSearch');
    const navRequest = document.getElementById('navRequest');

    if (navHome) {
        navHome.addEventListener('click', () => {
            // Reset search state
            document.getElementById('searchInput').value = '';
            if (document.getElementById('mobileSearchInput')) {
                document.getElementById('mobileSearchInput').value = '';
            }
            document.getElementById('mobileSearchContainer').classList.add('hidden');
            
            // Re-render full list
            renderGrid('', currentSort);
            
            // UI Feedback
            window.scrollTo({ top: 0, behavior: 'smooth' });
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            navHome.classList.add('active');
        });
    }

    if (navSearch) {
        navSearch.addEventListener('click', () => {
            const container = document.getElementById('mobileSearchContainer');
            container.classList.toggle('hidden');
            if (!container.classList.contains('hidden')) {
                document.getElementById('mobileSearchInput').focus();
            }
            
            // UI Feedback
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            navSearch.classList.add('active');
        });
    }

    if (navRequest) {
        navRequest.addEventListener('click', () => {
            openRequestForm();
            
            // UI Feedback
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            navRequest.classList.add('active');
        });
    }

    window.addEventListener('hashchange', handleRoute);

    init();
});

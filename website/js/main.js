import { currentLang, i18n, setLang } from './i18n.js';
import { fetchAppData, appConfigs } from './api.js';
import { renderGrid, closeModal, loader, appGrid, emptyState } from './ui.js';

let isDark = localStorage.getItem('theme') === 'dark' ||
    (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);

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
        if (i18n[currentLang][key]) el.textContent = i18n[currentLang][key];
    });

    document.querySelectorAll('[data-key-placeholder]').forEach(el => {
        const key = el.getAttribute('data-key-placeholder');
        if (i18n[currentLang][key]) el.placeholder = i18n[currentLang][key];
    });

    document.getElementById('langLabel').textContent = i18n[currentLang].langLabel;
    
    // Re-render grid if data is loaded
    if (Object.keys(appConfigs).length > 0) {
        const query = document.getElementById('searchInput').value;
        renderGrid(query);
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
        const query = document.getElementById('searchInput').value;
        renderGrid(query);
    } else {
        emptyState.classList.remove('hidden');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('langToggle').addEventListener('click', toggleLang);
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalBackdrop').addEventListener('click', closeModal);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

    document.getElementById('searchInput').addEventListener('input', (e) => {
        renderGrid(e.target.value);
        // Sync with mobile search if visible
        const mobSearch = document.getElementById('mobileSearchInput');
        if (mobSearch) mobSearch.value = e.target.value;
    });

    const mobSearch = document.getElementById('mobileSearchInput');
    if (mobSearch) {
        mobSearch.addEventListener('input', (e) => {
            renderGrid(e.target.value);
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

    init();
});

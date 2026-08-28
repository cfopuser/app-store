import { t, currentLang } from './i18n.js';

const GITHUB_ISSUE_URL = 'https://github.com/cfopuser/bit-updates/issues/new';

let formModal = null;
let step = 0;
const TOTAL_STEPS = 3;

const state = {
    app_name: '',
    app_name_he: '',
    package_name: '',
    app_description: '',
    patch_description: '',
    technical_details: '',
    source: 'Google Play',
    source_url: '',
    ack: false,
};

const errors = {};

// Preset common patch options
const PATCH_PRESETS = [
    { id: 'filter', key: 'formPresetFilter', icon: 'shield', textEn: 'Bypass content filter restrictions', textHe: 'עקיפת חסימת סינון או נטפרי' },
    { id: 'signature', key: 'formPresetSignature', icon: 'key-round', textEn: 'Bypass signature check', textHe: 'ביטול בדיקת חתימה' },
    { id: 'browser', key: 'formPresetBrowser', icon: 'globe', textEn: 'Block internal browser', textHe: 'חסימת דפדפן פנימי' },
    { id: 'offline', key: 'formPresetOffline', icon: 'wifi-off', textEn: 'Full offline mode', textHe: 'מצב אופליין מלא' },
    { id: 'sideload', key: 'formPresetSideload', icon: 'download', textEn: 'Bypass installer source check', textHe: 'עקיפת בדיקת מקור התקנה' },
];

const SOURCES = ['Google Play', 'F-Droid', 'Huawei AppGallery', 'APKMirror', 'APKPure', 'Aptoide', 'GitHub', 'Other'];

const SOURCE_ICONS = {
    'Google Play': `
        <svg viewBox="0 0 24 24" class="w-5 h-5 flex-shrink-0" fill="none">
            <path d="M3.25 1.5C3.08 1.88 3 2.33 3 2.87v18.26c0 .54.08.99.25 1.37L13.12 12 3.25 1.5z" fill="#00D1FF"/>
            <path d="M17.06 8.06L13.12 12l3.94 3.94 3.86-2.21c1.36-.78 1.36-2.04 0-2.82l-3.86-2.85z" fill="#FFD400"/>
            <path d="M3.25 22.5c.89.33 1.95.22 2.85-.3l10.96-6.26L13.12 12 3.25 22.5z" fill="#FF334B"/>
            <path d="M3.25 1.5L13.12 12l3.94-3.94L6.1 1.8C5.2 1.28 4.14 1.17 3.25 1.5z" fill="#00E676"/>
        </svg>`,

    'F-Droid': `
        <img src="website/images/sources/fdroid.png" alt="F-Droid" class="w-5 h-5 object-contain rounded-md flex-shrink-0">`,

    'Huawei AppGallery': `
        <img src="website/images/sources/huawei.png" alt="Huawei AppGallery" class="w-5 h-5 object-contain rounded-md flex-shrink-0">`,

    'APKMirror': `
        <img src="website/images/sources/apkmirror.png" alt="APKMirror" class="w-5 h-5 object-contain rounded-md flex-shrink-0">`,

    'APKPure': `
        <img src="website/images/sources/apkpure.png" alt="APKPure" class="w-5 h-5 object-contain rounded-md flex-shrink-0">`,

    'Aptoide': `
        <img src="website/images/sources/aptoide.svg" alt="Aptoide" class="w-5 h-5 object-contain rounded-md flex-shrink-0">`,

    'GitHub': `
        <svg viewBox="0 0 24 24" class="w-5 h-5 flex-shrink-0 fill-zinc-900 dark:fill-white">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/>
        </svg>`,

    'Other': `
        <svg viewBox="0 0 24 24" class="w-5 h-5 flex-shrink-0 text-zinc-500 dark:text-zinc-400" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="1.5"/>
            <circle cx="19" cy="12" r="1.5"/>
            <circle cx="5" cy="12" r="1.5"/>
        </svg>`
};

const SOURCE_LABEL_KEYS = {
    'Google Play': 'formSourceGooglePlay',
    'F-Droid': 'formSourceFDroid',
    'Huawei AppGallery': 'formSourceHuawei',
    APKMirror: 'formSourceAPKMirror',
    APKPure: 'formSourceAPKPure',
    Aptoide: 'formSourceAptoide',
    GitHub: 'formSourceGitHub',
    Other: 'formSourceOther'
};

// ─── Modal Shell Builder ───────────────────────────────────────────────────────
function buildFormModal() {
    const el = document.createElement('div');
    el.id = 'requestFormModal';
    el.className = 'fixed inset-0 z-[70] hidden overflow-hidden select-none';
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('role', 'dialog');
    el.innerHTML = `
        <div id="rfBackdrop" class="fixed inset-0 bg-[#09090C]/80 backdrop-blur-md transition-opacity duration-300 opacity-0"></div>
        <div class="fixed inset-0 z-10 w-screen h-full overflow-hidden flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div id="rfPanel"
                class="relative w-full sm:max-w-lg md:max-w-xl max-h-[94vh] sm:max-h-[88vh] bg-white dark:bg-[#141419] shadow-2xl rounded-t-[2rem] sm:rounded-3xl border-t sm:border border-zinc-200/80 dark:border-zinc-800 flex flex-col transform transition-all duration-300 translate-y-full opacity-0 overflow-hidden">
                
                <!-- Pinned Header -->
                <div class="relative px-5 pt-4 pb-2 sm:px-7 sm:pt-6 flex-shrink-0 border-b border-zinc-100 dark:border-zinc-800/60 bg-white/95 dark:bg-[#141419]/95 backdrop-blur-sm z-20">
                    <!-- Mobile drag handle -->
                    <div class="w-full flex justify-center pb-2.5 sm:hidden">
                        <div class="w-10 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700"></div>
                    </div>

                    <!-- Top row: Badge + Close button -->
                    <div class="flex items-center justify-between gap-3">
                        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 text-zinc-700 dark:text-zinc-300">
                            <i data-lucide="plus-circle" class="w-3.5 h-3.5 text-fuchsia-500"></i>
                            <span class="text-xs font-semibold" id="rfHeaderTitle"><bdi>${t('formTitle')}</bdi></span>
                        </div>
                        <button id="rfClose" type="button" class="p-1.5 rounded-full text-zinc-400 hover:text-zinc-700 dark:text-zinc-500 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all active:scale-95" aria-label="Close">
                            <i data-lucide="x" class="w-5 h-5"></i>
                        </button>
                    </div>

                    <p class="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-2 leading-relaxed" id="rfHeaderSubtitle">
                        <bdi>${t('formSubtitle')}</bdi>
                    </p>

                    <!-- Stepper Bar -->
                    <div class="pt-4 pb-1 relative" id="rfStepper">
                        <!-- Progress Line -->
                        <div class="absolute top-[26px] inset-x-8 h-[2px] bg-zinc-200 dark:bg-zinc-800 rounded-full z-0 overflow-hidden">
                            <div id="rfProgressBar" class="h-full bg-fuchsia-500 transition-all duration-300 rounded-full" style="width: 0%;"></div>
                        </div>

                        <!-- Step Dots -->
                        <div class="relative z-10 flex justify-between items-center w-full px-2" id="rfDotsContainer">
                            <!-- Injected by updateStepper() -->
                        </div>
                    </div>
                </div>

                <!-- Scrollable Body (Step Content) -->
                <div id="rfContentArea" class="flex-1 overflow-y-auto custom-scrollbar px-5 py-5 sm:px-7 overscroll-contain select-text">
                    <!-- Injected by renderCurrentStep() -->
                </div>

                <!-- Sticky Action Footer -->
                <div id="rfFooter" class="px-5 py-3.5 sm:px-7 sm:py-4 border-t border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/90 dark:bg-[#111115]/90 backdrop-blur-md flex items-center justify-between gap-3 flex-shrink-0 z-20">
                    <div id="rfBackWrapper">
                        <button type="button" id="rfBack" class="hidden items-center gap-1.5 px-4 py-2 rounded-full text-xs sm:text-sm font-semibold border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 active:scale-95 transition-all">
                            <i data-lucide="arrow-left" id="rfBackIcon" class="w-3.5 h-3.5"></i>
                            <span id="rfBackLabel"><bdi>${t('formBack')}</bdi></span>
                        </button>
                    </div>

                    <div class="flex items-center gap-2">
                        <button type="button" id="rfNext" class="group flex items-center gap-2 px-5 sm:px-6 py-2.5 rounded-full text-xs sm:text-sm font-semibold bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-200 active:scale-95 transition-all shadow-sm">
                            <span id="rfNextLabel"><bdi>${t('formNext')}</bdi></span>
                            <i data-lucide="arrow-right" id="rfNextIcon" class="w-4 h-4 transition-transform group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5"></i>
                        </button>
                    </div>
                </div>

            </div>
        </div>
    `;
    document.body.appendChild(el);

    document.getElementById('rfClose').addEventListener('click', closeRequestForm);
    document.getElementById('rfBackdrop').addEventListener('click', closeRequestForm);
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && formModal && !formModal.classList.contains('hidden')) {
            closeRequestForm();
        }
    });

    document.getElementById('rfNext').addEventListener('click', handleNextOrSubmit);
    document.getElementById('rfBack').addEventListener('click', handleBack);

    return el;
}

// ─── Extract Package from URL Helper ──────────────────────────────────────────
function extractPackageFromText(input) {
    if (!input) return null;
    const str = input.trim();
    // Match standard id= parameter in Play Store or other query strings
    const idMatch = str.match(/[?&]id=([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)/i);
    if (idMatch) return idMatch[1];

    // Match Play Store direct path
    const pathMatch = str.match(/apps\/details\/([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)/i);
    if (pathMatch) return pathMatch[1];

    // Match raw package format
    if (/^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$/.test(str)) {
        return str;
    }
    return null;
}

// ─── Stepper Updates ───────────────────────────────────────────────────────────
function updateStepper() {
    const isRTL = currentLang === 'he';
    const stepLabels = [t('formStep1'), t('formStep2'), t('formStep3')];
    const dotsContainer = document.getElementById('rfDotsContainer');
    const progressBar = document.getElementById('rfProgressBar');

    if (!dotsContainer || !progressBar) return;

    const percent = (step / (TOTAL_STEPS - 1)) * 100;
    progressBar.style.width = `${percent}%`;

    dotsContainer.innerHTML = stepLabels.map((label, idx) => {
        const isDone = idx < step;
        const isActive = idx === step;

        let dotClasses = 'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ';
        let textClasses = 'text-[11px] font-semibold transition-colors duration-300 mt-1 whitespace-nowrap ';

        if (isDone) {
            dotClasses += 'bg-fuchsia-500 text-white shadow-sm ring-2 ring-fuchsia-500/20';
            textClasses += 'text-zinc-600 dark:text-zinc-400';
        } else if (isActive) {
            dotClasses += 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 shadow-md ring-4 ring-fuchsia-500/20 scale-105';
            textClasses += 'text-zinc-900 dark:text-zinc-100 font-bold';
        } else {
            dotClasses += 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-600 border border-zinc-200 dark:border-zinc-700';
            textClasses += 'text-zinc-400 dark:text-zinc-600';
        }

        const innerIcon = isDone
            ? `<i data-lucide="check" class="w-3.5 h-3.5 animate-pop"></i>`
            : `<span>${idx + 1}</span>`;

        return `
            <div class="flex flex-col items-center flex-1 cursor-pointer select-none" data-step-dot="${idx}">
                <div class="${dotClasses}">
                    ${innerIcon}
                </div>
                <span class="${textClasses}"><bdi>${label}</bdi></span>
            </div>
        `;
    }).join('');

    // Allow jumping back to previously completed steps
    dotsContainer.querySelectorAll('[data-step-dot]').forEach(el => {
        const targetStep = parseInt(el.dataset.stepDot, 10);
        if (targetStep < step) {
            el.addEventListener('click', () => {
                goToStep(targetStep, 'backward');
            });
        }
    });

    if (window.lucide) window.lucide.createIcons();
}

// ─── Input & Helper Builders ──────────────────────────────────────────────────
function fieldWrapper(id, labelHtml, hintHtml, inputHtml, error) {
    return `
        <div class="space-y-1.5 group" id="group_${id}">
            <div class="flex items-center justify-between">
                <label for="${id}" class="block text-xs sm:text-sm font-bold text-zinc-900 dark:text-zinc-200">${labelHtml}</label>
            </div>
            ${hintHtml ? `<p class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">${hintHtml}</p>` : ''}
            ${inputHtml}
            <div class="min-h-[18px]">
                <p id="err_${id}" class="text-xs text-rose-500 flex items-center gap-1 mt-0.5 ${error ? '' : 'hidden'}">
                    <i data-lucide="alert-circle" class="w-3.5 h-3.5 flex-shrink-0"></i>
                    <bdi>${error || ''}</bdi>
                </p>
            </div>
        </div>
    `;
}

function getInputClasses(hasError) {
    const base = 'w-full rounded-xl border px-3.5 py-2.5 text-sm bg-zinc-50/70 dark:bg-[#1A1A21] text-zinc-900 dark:text-zinc-100 outline-none transition-all placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:ring-2 focus:ring-fuchsia-400/30';
    return hasError
        ? `${base} border-rose-400 dark:border-rose-500/80`
        : `${base} border-zinc-200 dark:border-zinc-700/80 focus:border-fuchsia-400 dark:focus:border-fuchsia-500`;
}

function getTextareaClasses(hasError) {
    const base = 'w-full rounded-xl border px-3.5 py-2.5 text-sm bg-zinc-50/70 dark:bg-[#1A1A21] text-zinc-900 dark:text-zinc-100 outline-none transition-all placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:ring-2 focus:ring-fuchsia-400/30 resize-none';
    return hasError
        ? `${base} border-rose-400 dark:border-rose-500/80`
        : `${base} border-zinc-200 dark:border-zinc-700/80 focus:border-fuchsia-400 dark:focus:border-fuchsia-500`;
}

// ─── Step 0: App Details ───────────────────────────────────────────────────────
function renderStep0() {
    const isHe = currentLang === 'he';

    const nameField = fieldWrapper(
        'app_name',
        `<bdi>${t('formFieldAppName')}</bdi> <span class="text-rose-500">*</span>`,
        null,
        `<div class="relative">
            <input id="app_name" type="text" class="${getInputClasses(errors.app_name)}" value="${escHtml(state.app_name)}" placeholder="${t('formFieldAppNamePlaceholder')}">
        </div>`,
        errors.app_name
    );

    const heNameField = fieldWrapper(
        'app_name_he',
        `<bdi>${t('formFieldAppNameHe')}</bdi> <span class="text-zinc-400 text-xs font-normal ms-1">${t('formOptional')}</span>`,
        null,
        `<div class="relative">
            <input id="app_name_he" type="text" class="${getInputClasses(errors.app_name_he)}" value="${escHtml(state.app_name_he)}" placeholder="${t('formFieldAppNameHePlaceholder')}">
        </div>`,
        errors.app_name_he
    );

    const packageField = fieldWrapper(
        'package_name',
        `<bdi>${t('formFieldPackage')}</bdi> <span class="text-rose-500">*</span>`,
        `<bdi>${t('formFieldPackageHint')}</bdi>`,
        `<div class="relative">
            <input id="package_name" type="text" class="${getInputClasses(errors.package_name)} font-mono text-xs sm:text-sm" value="${escHtml(state.package_name)}" placeholder="${t('formFieldPackagePlaceholder')}" dir="ltr" style="text-align: left;">
            <div id="pkgExtractedBadge" class="hidden absolute top-2.5 end-3 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold uppercase tracking-wider items-center gap-1 animate-pop">
                <i data-lucide="sparkles" class="w-3 h-3"></i>
                <span id="pkgBadgeText">${t('formAutoExtracted')}</span>
            </div>
        </div>`,
        errors.package_name
    );

    const descField = fieldWrapper(
        'app_description',
        `<bdi>${t('formFieldAppDescription')}</bdi> <span class="text-rose-500">*</span>`,
        null,
        `<textarea id="app_description" class="${getTextareaClasses(errors.app_description)}" rows="2" placeholder="${t('formFieldAppDescriptionPlaceholder')}">${escHtml(state.app_description)}</textarea>`,
        errors.app_description
    );

    return `
        <div class="space-y-4">
            ${isHe ? nameField + heNameField : nameField + heNameField}
            ${packageField}
            ${descField}
        </div>
    `;
}

// ─── Step 1: Patch Details & Presets ──────────────────────────────────────────
function renderStep1() {
    const isHe = currentLang === 'he';

    const presetChips = PATCH_PRESETS.map(preset => {
        const label = isHe ? preset.textHe : preset.textEn;
        const isActive = state.patch_description.includes(label);
        return `
            <button type="button" data-preset-id="${preset.id}" data-preset-text="${escHtml(label)}"
                class="preset-chip text-xs font-medium px-3 py-1.5 rounded-lg border transition-all inline-flex items-center gap-1.5 ${isActive ? 'is-active' : 'border-zinc-200 dark:border-zinc-700/80 bg-zinc-100/70 dark:bg-zinc-800/60 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'}">
                <i data-lucide="${preset.icon}" class="w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-fuchsia-500' : 'text-zinc-400 dark:text-zinc-500'}"></i>
                <span><bdi>${t(preset.key)}</bdi></span>
            </button>
        `;
    }).join('');

    const patchField = fieldWrapper(
        'patch_description',
        `<bdi>${t('formFieldPatch')}</bdi> <span class="text-rose-500">*</span>`,
        `<bdi>${t('formFieldPatchHint')}</bdi>`,
        `
        <div class="flex flex-wrap gap-1.5 pb-2 pt-1" id="presetChipsContainer">
            ${presetChips}
        </div>
        <textarea id="patch_description" class="${getTextareaClasses(errors.patch_description)}" rows="4" placeholder="${t('formFieldPatchPlaceholder')}">${escHtml(state.patch_description)}</textarea>
        `,
        errors.patch_description
    );

    const techField = fieldWrapper(
        'technical_details',
        `<bdi>${t('formFieldTechnical')}</bdi> <span class="text-zinc-400 text-xs font-normal ms-1">${t('formOptional')}</span>`,
        null,
        `<textarea id="technical_details" class="${getTextareaClasses(errors.technical_details)} font-mono text-xs" rows="3" placeholder="${t('formFieldTechnicalPlaceholder')}">${escHtml(state.technical_details)}</textarea>`,
        errors.technical_details
    );

    return `
        <div class="space-y-4">
            ${patchField}
            ${techField}
        </div>
    `;
}

// ─── Step 2: Source Selection & Live Preview ──────────────────────────────────
function renderStep2() {
    const sourceCards = SOURCES.map(src => {
        const isSelected = state.source === src;
        return `
            <button type="button" data-source-name="${src}"
                class="source-card flex items-center gap-2.5 p-2.5 sm:p-3 rounded-2xl border text-start transition-all cursor-pointer select-none ${isSelected ? 'is-selected border-fuchsia-500 text-zinc-900 dark:text-white ring-2 ring-fuchsia-500/20' : 'border-zinc-200 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/60 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-700'}">
                <div class="flex-shrink-0 flex items-center justify-center">
                    ${SOURCE_ICONS[src]}
                </div>
                <div class="flex-1 min-w-0">
                    <span class="block text-xs sm:text-sm font-semibold tracking-tight leading-snug whitespace-nowrap overflow-hidden text-ellipsis"><bdi>${t(SOURCE_LABEL_KEYS[src])}</bdi></span>
                </div>
                <div class="check-badge w-4 h-4 rounded-full flex-shrink-0 border flex items-center justify-center transition-all ${isSelected ? 'border-fuchsia-500 bg-fuchsia-500 text-white scale-100' : 'border-zinc-300 dark:border-zinc-700 bg-transparent scale-90'}">
                    ${isSelected ? '<svg class="w-2.5 h-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' : ''}
                </div>
            </button>
        `;
    }).join('');

    const sourceField = `
        <div class="space-y-2">
            <label class="block text-xs sm:text-sm font-bold text-zinc-900 dark:text-zinc-200"><bdi>${t('formFieldSource')}</bdi> <span class="text-rose-500">*</span></label>
            <div class="grid grid-cols-2 gap-2" id="sourceCardsGrid">
                ${sourceCards}
            </div>
            <p id="err_source" class="text-xs text-rose-500 flex items-center gap-1 mt-1 ${errors.source ? '' : 'hidden'}">
                <i data-lucide="alert-circle" class="w-3.5 h-3.5 flex-shrink-0"></i>
                <bdi>${errors.source || ''}</bdi>
            </p>
        </div>
    `;

    const sourceUrlPlaceholder = state.source === 'GitHub'
        ? 'https://github.com/owner/repo'
        : state.source === 'Google Play'
            ? 'https://play.google.com/store/apps/details?id=...'
            : 'https://...';

    const sourceUrlField = fieldWrapper(
        'source_url',
        `<bdi>${t('formFieldSourceUrl')}</bdi> <span class="text-zinc-400 text-xs font-normal ms-1">${t('formOptional')}</span>`,
        null,
        `<input id="source_url" type="url" class="${getInputClasses(errors.source_url)}" value="${escHtml(state.source_url)}" placeholder="${sourceUrlPlaceholder}" dir="ltr" style="text-align: left;">`,
        errors.source_url
    );

    // Live summary preview card
    const primaryName = state.app_name.trim() || state.app_name_he.trim() || 'App';
    const summaryCard = `
        <div class="rounded-2xl border border-zinc-200/90 dark:border-zinc-800 bg-gradient-to-br from-zinc-50 to-zinc-100/60 dark:from-[#17171F] dark:to-[#121217] p-3.5 sm:p-4 space-y-2.5 shadow-sm">
            <div class="flex items-center justify-between gap-2 border-b border-zinc-200/60 dark:border-zinc-800/80 pb-2">
                <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded-lg bg-fuchsia-500/10 dark:bg-fuchsia-500/20 text-fuchsia-600 dark:text-fuchsia-400 flex items-center justify-center text-xs font-bold">
                        <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i>
                    </div>
                    <span class="text-xs font-bold uppercase tracking-wider text-zinc-700 dark:text-zinc-300"><bdi>${t('formSummaryTitle')}</bdi></span>
                </div>
                <span id="summarySourceTag" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-200/80 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">${escHtml(state.source)}</span>
            </div>
            
            <div class="flex items-start justify-between gap-3 text-xs">
                <div>
                    <span class="font-bold text-zinc-900 dark:text-zinc-100">${escHtml(primaryName)}</span>
                    ${state.app_name_he && state.app_name ? `<span class="text-zinc-500 dark:text-zinc-400 ms-1.5">(${escHtml(state.app_name_he)})</span>` : ''}
                    <div class="font-mono text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">${escHtml(state.package_name || '')}</div>
                </div>
            </div>

            <p class="text-xs text-zinc-600 dark:text-zinc-400 line-clamp-2 italic leading-relaxed">
                "${escHtml(state.patch_description || '')}"
            </p>
        </div>
    `;

    const ackCheckbox = `
        <div class="space-y-1.5 pt-1">
            <label class="flex items-start gap-3 cursor-pointer group select-none">
                <div class="relative mt-0.5 flex-shrink-0">
                    <input type="checkbox" id="ack" class="sr-only peer" ${state.ack ? 'checked' : ''}>
                    <div id="ackBox" class="w-5 h-5 rounded-md border-2 transition-all flex items-center justify-center ${state.ack ? 'border-fuchsia-500 bg-fuchsia-500 text-white' : 'border-zinc-300 dark:border-zinc-600 group-hover:border-zinc-400'}">
                        <i data-lucide="check" class="w-3.5 h-3.5 ${state.ack ? '' : 'opacity-0'} transition-opacity" id="ackIcon"></i>
                    </div>
                </div>
                <span class="text-xs sm:text-sm text-zinc-700 dark:text-zinc-300 leading-snug"><bdi>${t('formFieldAck')}</bdi> <span class="text-rose-500">*</span></span>
            </label>
            <p id="err_ack" class="text-xs text-rose-500 flex items-center gap-1 ${errors.ack ? '' : 'hidden'}">
                <i data-lucide="alert-circle" class="w-3.5 h-3.5 flex-shrink-0"></i>
                <bdi>${errors.ack || ''}</bdi>
            </p>
        </div>
    `;

    return `
        <div class="space-y-4">
            ${sourceField}
            ${sourceUrlField}
            ${summaryCard}
            ${ackCheckbox}
        </div>
    `;
}

// ─── Render Current Step to Content Area ──────────────────────────────────────
function renderCurrentStep(direction = 'forward') {
    const contentArea = document.getElementById('rfContentArea');
    if (!contentArea) return;

    const stepGenerators = [renderStep0, renderStep1, renderStep2];
    const html = stepGenerators[step]();

    const animClass = direction === 'backward' ? 'step-slide-backward' : 'step-slide-forward';
    contentArea.innerHTML = `<div class="${animClass}">${html}</div>`;
    contentArea.scrollTop = 0;

    bindActiveStepEvents();
    updateFooterUI();
    updateStepper();

    if (window.lucide) window.lucide.createIcons();
}

// ─── Dynamic In-Place Event Binding ───────────────────────────────────────────
function bindActiveStepEvents() {
    // Step 0 bindings
    const appName = document.getElementById('app_name');
    if (appName) {
        appName.addEventListener('input', e => {
            state.app_name = e.target.value;
            clearFieldErr('app_name');
        });
    }

    const appNameHe = document.getElementById('app_name_he');
    if (appNameHe) {
        appNameHe.addEventListener('input', e => {
            state.app_name_he = e.target.value;
            clearFieldErr('app_name_he');
        });
    }

    const pkgName = document.getElementById('package_name');
    if (pkgName) {
        pkgName.addEventListener('input', e => {
            const rawVal = e.target.value;
            const extracted = extractPackageFromText(rawVal);
            if (extracted && extracted !== rawVal) {
                state.package_name = extracted;
                pkgName.value = extracted;
                showPkgExtractedBadge();
                if (!state.source_url && rawVal.startsWith('http')) {
                    state.source_url = rawVal;
                }
            } else {
                state.package_name = rawVal;
            }
            clearFieldErr('package_name');
        });
    }

    const desc = document.getElementById('app_description');
    if (desc) {
        desc.addEventListener('input', e => {
            state.app_description = e.target.value;
            clearFieldErr('app_description');
        });
    }

    // Step 1 bindings
    const patchDesc = document.getElementById('patch_description');
    if (patchDesc) {
        patchDesc.addEventListener('input', e => {
            state.patch_description = e.target.value;
            clearFieldErr('patch_description');
            updatePresetChipsState();
        });
    }

    const techDetails = document.getElementById('technical_details');
    if (techDetails) {
        techDetails.addEventListener('input', e => {
            state.technical_details = e.target.value;
        });
    }

    // Preset chip clicks (instant in-place modification)
    document.querySelectorAll('.preset-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const text = chip.dataset.presetText;
            const current = state.patch_description.trim();
            if (current.includes(text)) {
                // Remove it
                state.patch_description = current.replace(text, '').replace(/\n\s*\n/g, '\n').trim();
            } else {
                // Append it
                state.patch_description = current ? `${current}\n• ${text}` : `• ${text}`;
            }
            if (patchDesc) {
                patchDesc.value = state.patch_description;
                clearFieldErr('patch_description');
            }
            updatePresetChipsState();
        });
    });

    // Step 2 bindings — Source Cards (zero-flicker in-place toggle)
    document.querySelectorAll('.source-card').forEach(card => {
        card.addEventListener('click', () => {
            const srcName = card.dataset.sourceName;
            state.source = srcName;
            clearFieldErr('source');

            // In-place DOM update without re-rendering step
            document.querySelectorAll('.source-card').forEach(c => {
                const isThis = c.dataset.sourceName === srcName;
                c.classList.toggle('is-selected', isThis);
                c.classList.toggle('border-fuchsia-500', isThis);
                c.classList.toggle('ring-2', isThis);
                c.classList.toggle('ring-fuchsia-500/20', isThis);

                const badge = c.querySelector('.check-badge');
                if (badge) {
                    badge.classList.toggle('border-fuchsia-500', isThis);
                    badge.classList.toggle('bg-fuchsia-500', isThis);
                    badge.classList.toggle('text-white', isThis);
                    badge.classList.toggle('scale-100', isThis);
                    badge.classList.toggle('scale-90', !isThis);
                    badge.innerHTML = isThis
                        ? '<svg class="w-2.5 h-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
                        : '';
                }
            });

            // Update live summary source tag
            const summaryTag = document.getElementById('summarySourceTag');
            if (summaryTag) summaryTag.textContent = srcName;

            // Update source URL placeholder dynamically
            const urlInput = document.getElementById('source_url');
            if (urlInput) {
                urlInput.placeholder = srcName === 'GitHub'
                    ? 'https://github.com/owner/repo'
                    : srcName === 'Google Play'
                        ? 'https://play.google.com/store/apps/details?id=...'
                        : 'https://...';
            }
        });
    });

    const srcUrl = document.getElementById('source_url');
    if (srcUrl) {
        srcUrl.addEventListener('input', e => {
            state.source_url = e.target.value;
            // Also try to extract package if not set
            if (!state.package_name) {
                const pkg = extractPackageFromText(e.target.value);
                if (pkg) state.package_name = pkg;
            }
        });
    }

    const ackCheckbox = document.getElementById('ack');
    if (ackCheckbox) {
        ackCheckbox.addEventListener('change', e => {
            state.ack = e.target.checked;
            clearFieldErr('ack');
            const ackBox = document.getElementById('ackBox');
            const ackIcon = document.getElementById('ackIcon');
            if (ackBox) {
                ackBox.classList.toggle('border-fuchsia-500', state.ack);
                ackBox.classList.toggle('bg-fuchsia-500', state.ack);
                ackBox.classList.toggle('text-white', state.ack);
            }
            if (ackIcon) {
                ackIcon.classList.toggle('opacity-0', !state.ack);
            }
        });
    }
}

function updatePresetChipsState() {
    const desc = state.patch_description || '';
    document.querySelectorAll('.preset-chip').forEach(chip => {
        const text = chip.dataset.presetText;
        const active = desc.includes(text);
        chip.classList.toggle('is-active', active);
        const icon = chip.querySelector('[data-lucide]');
        if (icon) {
            icon.classList.toggle('text-fuchsia-500', active);
            icon.classList.toggle('text-zinc-400', !active);
            icon.classList.toggle('dark:text-zinc-500', !active);
        }
    });
}

function showPkgExtractedBadge() {
    const badge = document.getElementById('pkgExtractedBadge');
    if (!badge) return;
    badge.classList.remove('hidden');
    badge.classList.add('flex');
    setTimeout(() => {
        badge.classList.add('hidden');
        badge.classList.remove('flex');
    }, 4000);
}

// ─── Inline Error Handling & Shake Animation ───────────────────────────────────
function showFieldErr(fieldId, message) {
    errors[fieldId] = message;
    const inputEl = document.getElementById(fieldId);
    if (inputEl) {
        inputEl.classList.add('border-rose-400', 'dark:border-rose-500/80', 'animate-shake');
        setTimeout(() => inputEl.classList.remove('animate-shake'), 400);
    }
    const errText = document.getElementById(`err_${fieldId}`);
    if (errText) {
        errText.querySelector('bdi').textContent = message;
        errText.classList.remove('hidden');
    }
}

function clearFieldErr(fieldId) {
    delete errors[fieldId];
    const inputEl = document.getElementById(fieldId);
    if (inputEl) {
        inputEl.classList.remove('border-rose-400', 'dark:border-rose-500/80', 'animate-shake');
    }
    const errText = document.getElementById(`err_${fieldId}`);
    if (errText) {
        errText.classList.add('hidden');
    }
}

// ─── Step Navigation & Validation ──────────────────────────────────────────────
function validateStep(stepIndex) {
    const stepErrs = {};
    if (stepIndex === 0) {
        if (!state.app_name.trim() && !state.app_name_he.trim()) {
            stepErrs.app_name = t('formValidationNameRequired');
        }
        if (!state.package_name.trim()) {
            stepErrs.package_name = t('formValidationRequired');
        } else if (!extractPackageFromText(state.package_name.trim())) {
            stepErrs.package_name = t('formValidationPackage');
        }
        if (!state.app_description.trim()) {
            stepErrs.app_description = t('formValidationRequired');
        }
    } else if (stepIndex === 1) {
        if (!state.patch_description.trim()) {
            stepErrs.patch_description = t('formValidationRequired');
        }
    } else if (stepIndex === 2) {
        if (!state.source) {
            stepErrs.source = t('formValidationRequired');
        }
        if (!state.ack) {
            stepErrs.ack = t('formValidationAck');
        }
    }
    return stepErrs;
}

function goToStep(targetStep, direction = 'forward') {
    step = targetStep;
    renderCurrentStep(direction);
}

function handleNextOrSubmit() {
    const stepErrs = validateStep(step);
    Object.keys(stepErrs).forEach(field => showFieldErr(field, stepErrs[field]));

    if (Object.keys(stepErrs).length > 0) {
        return;
    }

    if (step < TOTAL_STEPS - 1) {
        goToStep(step + 1, 'forward');
    } else {
        submitIssue();
    }
}

function handleBack() {
    if (step > 0) {
        goToStep(step - 1, 'backward');
    }
}

function updateFooterUI() {
    const isFirst = step === 0;
    const isLast = step === TOTAL_STEPS - 1;
    const isRTL = currentLang === 'he';

    const backBtn = document.getElementById('rfBack');
    const backIcon = document.getElementById('rfBackIcon');
    if (backBtn) {
        backBtn.classList.toggle('hidden', isFirst);
        backBtn.classList.toggle('flex', !isFirst);
        if (backIcon) {
            backIcon.setAttribute('data-lucide', isRTL ? 'arrow-right' : 'arrow-left');
        }
    }

    const nextBtn = document.getElementById('rfNext');
    const nextLabel = document.getElementById('rfNextLabel');
    const nextIcon = document.getElementById('rfNextIcon');

    if (nextBtn && nextLabel && nextIcon) {
        if (isLast) {
            nextLabel.innerHTML = `<bdi>${t('formSubmit')}</bdi>`;
            nextIcon.setAttribute('data-lucide', 'external-link');
            nextBtn.className = 'group flex items-center gap-2 px-5 sm:px-6 py-2.5 rounded-full text-xs sm:text-sm font-semibold bg-fuchsia-600 hover:bg-fuchsia-500 text-white shadow-sm active:scale-95 transition-all';
        } else {
            nextLabel.innerHTML = `<bdi>${t('formNext')}</bdi>`;
            nextIcon.setAttribute('data-lucide', isRTL ? 'arrow-left' : 'arrow-right');
            nextBtn.className = 'group flex items-center gap-2 px-5 sm:px-6 py-2.5 rounded-full text-xs sm:text-sm font-semibold bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-200 active:scale-95 transition-all shadow-sm';
        }
    }

    if (window.lucide) window.lucide.createIcons();
}

// ─── Submit GitHub Issue ───────────────────────────────────────────────────────
function buildIssueBody() {
    const lines = [];
    if (state.app_name.trim()) lines.push(`### App Name\n${state.app_name.trim()}`);
    if (state.app_name_he.trim()) lines.push(`\n### App Name (Hebrew)\n${state.app_name_he.trim()}`);
    lines.push(`\n### Package Name\n\`${state.package_name.trim()}\``);
    lines.push(`\n### App Description\n${state.app_description.trim()}`);
    lines.push(`\n### What needs to be changed?\n${state.patch_description.trim()}`);
    if (state.technical_details.trim()) lines.push(`\n### Technical Details\n${state.technical_details.trim()}`);
    lines.push(`\n### APK Source\n${state.source}`);
    if (state.source_url.trim()) lines.push(`\n### Source URL\n${state.source_url.trim()}`);
    lines.push(`\n### Acknowledgment\n- [x] I have verified this app is available on the specified source and that the patch is possible`);
    return lines.join('');
}

function buildGitHubUrl() {
    const body = buildIssueBody();
    const primaryName = (currentLang === 'he' && state.app_name_he.trim())
        ? state.app_name_he.trim()
        : state.app_name.trim() || state.app_name_he.trim();
    const title = `[App Request] ${primaryName}`;
    const params = new URLSearchParams({
        title,
        labels: 'new-app',
        body,
    });
    return `${GITHUB_ISSUE_URL}?${params.toString()}`;
}

function submitIssue() {
    const nextBtn = document.getElementById('rfNext');
    const nextLabel = document.getElementById('rfNextLabel');
    if (nextLabel) nextLabel.innerHTML = `<bdi>${t('formSubmitting')}</bdi>`;
    if (nextBtn) nextBtn.disabled = true;

    const url = buildGitHubUrl();

    setTimeout(() => {
        window.open(url, '_blank', 'noopener,noreferrer');
        closeRequestForm();
        if (nextBtn) nextBtn.disabled = false;
    }, 400);
}

// ─── Open & Close Modal Handlers ──────────────────────────────────────────────
export function openRequestForm() {
    if (!formModal) formModal = buildFormModal();

    const isHe = currentLang === 'he';
    const panel = document.getElementById('rfPanel');
    if (panel) {
        panel.dir = isHe ? 'rtl' : 'ltr';
    }

    // Reset state & errors
    step = 0;
    state.app_name = '';
    state.app_name_he = '';
    state.package_name = '';
    state.app_description = '';
    state.patch_description = '';
    state.technical_details = '';
    state.source = 'Google Play';
    state.source_url = '';
    state.ack = false;

    Object.keys(errors).forEach(k => delete errors[k]);

    // Update header labels for current language
    const headerTitle = document.getElementById('rfHeaderTitle');
    if (headerTitle) headerTitle.innerHTML = `<bdi>${t('formTitle')}</bdi>`;
    const headerSubtitle = document.getElementById('rfHeaderSubtitle');
    if (headerSubtitle) headerSubtitle.innerHTML = `<bdi>${t('formSubtitle')}</bdi>`;

    renderCurrentStep('forward');

    formModal.classList.remove('hidden');

    requestAnimationFrame(() => {
        document.getElementById('rfBackdrop').classList.replace('opacity-0', 'opacity-100');
        panel.classList.remove('translate-y-full', 'opacity-0');
        panel.classList.add('translate-y-0', 'opacity-100');
    });

    document.body.style.overflow = 'hidden';
}

export function closeRequestForm() {
    if (!formModal) return;
    const backdrop = document.getElementById('rfBackdrop');
    const panel = document.getElementById('rfPanel');

    if (backdrop) backdrop.classList.replace('opacity-100', 'opacity-0');
    if (panel) {
        panel.classList.remove('translate-y-0', 'opacity-100');
        panel.classList.add('translate-y-full', 'opacity-0');
    }

    setTimeout(() => {
        formModal.classList.add('hidden');
        document.body.style.overflow = '';
    }, 320);
}

// ─── Escaper ───────────────────────────────────────────────────────────────────
function escHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

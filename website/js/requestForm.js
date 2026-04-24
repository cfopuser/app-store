import { t, currentLang } from './i18n.js';

const GITHUB_ISSUE_URL = 'https://github.com/cfopuser/bit-updates/issues/new';

// ─── Modal container (reuse the existing #appModal infrastructure) ────────────
let formModal = null;

function buildFormModal() {
    const el = document.createElement('div');
    el.id = 'requestFormModal';
    el.className = 'relative z-[60] hidden';
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('role', 'dialog');
    el.innerHTML = `
        <div id="rfBackdrop" class="fixed inset-0 bg-[#0E0E12]/85 backdrop-blur-sm transition-opacity opacity-0"></div>
        <div class="fixed inset-0 z-10 w-screen overflow-y-auto">
            <div class="flex min-h-full items-end sm:items-center justify-center p-0 sm:p-4">
                <div id="rfPanel"
                    class="relative w-full sm:max-w-lg transform overflow-hidden rounded-t-[2rem] sm:rounded-3xl bg-white dark:bg-[#15151A] shadow-2xl transition-all duration-350 border-t sm:border border-zinc-200 dark:border-zinc-800 flex flex-col max-h-[92vh] sm:max-h-[88vh] translate-y-full opacity-0">

                    <!-- drag handle -->
                    <div class="w-full flex justify-center pt-3 pb-1 sm:hidden flex-shrink-0">
                        <div class="w-12 h-1.5 rounded-full bg-zinc-200 dark:bg-zinc-700"></div>
                    </div>

                    <!-- close button -->
                    <button id="rfClose" class="absolute top-3 sm:top-4 z-20 p-2 rounded-full text-zinc-400 hover:text-zinc-600 dark:text-zinc-500 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors focus:outline-none" style="inset-inline-end: 1rem;">
                        <i data-lucide="x" class="w-5 h-5"></i>
                    </button>

                    <!-- scrollable body -->
                    <div id="rfBody" class="flex-1 overflow-y-auto custom-scrollbar overscroll-contain px-5 pb-8 sm:px-8 pt-4">
                        <!-- injected by renderStep() -->
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(el);

    document.getElementById('rfClose').addEventListener('click', closeRequestForm);
    document.getElementById('rfBackdrop').addEventListener('click', closeRequestForm);
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && !formModal.classList.contains('hidden')) closeRequestForm();
    });

    return el;
}

// ─── State ────────────────────────────────────────────────────────────────────
let step = 0;
const TOTAL_STEPS = 3;

const state = {
    app_name: '',
    app_name_he: '',
    package_name: '',
    app_description: '',
    patch_description: '',
    technical_details: '',
    source: '',
    source_url: '',
    ack: false,
};

const errors = {};

// ─── Validation ───────────────────────────────────────────────────────────────
function validate(stepIndex) {
    const errs = {};
    if (stepIndex === 0) {
        if (currentLang === 'he') {
            if (!state.app_name_he.trim()) errs.app_name_he = t('formValidationRequired');
        } else {
            if (!state.app_name.trim()) errs.app_name = t('formValidationRequired');
        }
        if (!state.package_name.trim()) errs.package_name = t('formValidationRequired');
        else if (!/^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$/.test(state.package_name.trim()))
            errs.package_name = t('formValidationPackage');
        if (!state.app_description.trim()) errs.app_description = t('formValidationRequired');
    }
    if (stepIndex === 1) {
        if (!state.patch_description.trim()) errs.patch_description = t('formValidationRequired');
    }
    if (stepIndex === 2) {
        if (!state.source) errs.source = t('formValidationRequired');
        if (!state.ack) errs.ack = t('formValidationAck');
    }
    return errs;
}

// ─── Step renderers ───────────────────────────────────────────────────────────
function fieldGroup(id, label, hint, inputHtml, error) {
    return `
    <div class="space-y-1.5">
        <label for="${id}" class="block text-sm font-semibold text-zinc-800 dark:text-zinc-200">${label}</label>
        ${hint ? `<p class="text-xs text-zinc-400 dark:text-zinc-500">${hint}</p>` : ''}
        ${inputHtml}
        ${error ? `<p class="text-xs text-rose-500 flex items-center gap-1 mt-1"><i data-lucide="alert-circle" class="w-3 h-3 flex-shrink-0"></i><bdi>${error}</bdi></p>` : ''}
    </div>`;
}

function inputClass(id) {
    const base = 'w-full rounded-xl border px-4 py-3 text-sm bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 outline-none transition-all placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:ring-2 focus:ring-fuchsia-400/40';
    const errBorder = errors[id]
        ? 'border-rose-400 dark:border-rose-500/70'
        : 'border-zinc-200 dark:border-zinc-700 focus:border-fuchsia-400 dark:focus:border-fuchsia-500';
    return `${base} ${errBorder}`;
}

function textareaClass(id) {
    const base = 'w-full rounded-xl border px-4 py-3 text-sm bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 outline-none transition-all placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:ring-2 focus:ring-fuchsia-400/40 resize-none';
    const errBorder = errors[id]
        ? 'border-rose-400 dark:border-rose-500/70'
        : 'border-zinc-200 dark:border-zinc-700 focus:border-fuchsia-400 dark:focus:border-fuchsia-500';
    return `${base} ${errBorder}`;
}

function renderStep0() {
    const isHe = currentLang === 'he';
    
    const enField = fieldGroup('app_name', `<bdi>${t('formFieldAppName')}</bdi> ${!isHe ? '<span class="text-rose-500">*</span>' : `<span class="text-zinc-400 text-xs font-normal ms-1">(${t('formOptional')})</span>`}`, null,
        `<input id="app_name" type="text" class="${inputClass('app_name')}" value="${escHtml(state.app_name)}" placeholder="${t('formFieldAppNamePlaceholder')}" dir="ltr" style="text-align: left;">`,
        errors.app_name);

    const heField = fieldGroup('app_name_he', `<bdi>${t('formFieldAppNameHe')}</bdi> ${isHe ? '<span class="text-rose-500">*</span>' : `<span class="text-zinc-400 text-xs font-normal ms-1">(${t('formOptional')})</span>`}`, null,
        `<input id="app_name_he" type="text" class="${inputClass('app_name_he')}" value="${escHtml(state.app_name_he)}" placeholder="${t('formFieldAppNameHePlaceholder')}">`,
        errors.app_name_he);

    return `
    <div class="space-y-5 animate-fade-in">
        ${isHe ? heField + '\n' + enField : enField + '\n' + heField}
        ${fieldGroup('package_name', `<bdi>${t('formFieldPackage')}</bdi> <span class="text-rose-500">*</span>`, `<bdi>${t('formFieldPackageHint')}</bdi>`,
            `<input id="package_name" type="text" class="${inputClass('package_name')} font-mono" value="${escHtml(state.package_name)}" placeholder="${t('formFieldPackagePlaceholder')}" dir="ltr" style="text-align: left;">`,
            errors.package_name)}
        ${fieldGroup('app_description', `<bdi>${t('formFieldAppDescription')}</bdi> <span class="text-rose-500">*</span>`, `<bdi>${t('formFieldAppDescriptionHint')}</bdi>`,
            `<textarea id="app_description" class="${textareaClass('app_description')}" rows="2" placeholder="${t('formFieldAppDescriptionPlaceholder')}">${escHtml(state.app_description)}</textarea>`,
            errors.app_description)}
    </div>`;
}

function renderStep1() {
    return `
    <div class="space-y-5 animate-fade-in">
        ${fieldGroup('patch_description', `<bdi>${t('formFieldPatch')}</bdi> <span class="text-rose-500">*</span>`, `<bdi>${t('formFieldPatchHint')}</bdi>`,
            `<textarea id="patch_description" class="${textareaClass('patch_description')}" rows="5" placeholder="${t('formFieldPatchPlaceholder')}">${escHtml(state.patch_description)}</textarea>`,
            errors.patch_description)}
        ${fieldGroup('technical_details', `<bdi>${t('formFieldTechnical')}</bdi>`, null,
            `<textarea id="technical_details" class="${textareaClass('technical_details')} font-mono" rows="4" placeholder="${t('formFieldTechnicalPlaceholder')}">${escHtml(state.technical_details)}</textarea>`,
            errors.technical_details)}
    </div>`;
}

const SOURCES = ['APKMirror', 'APKPure', 'Aptoide', 'GitHub', 'Other'];
const SOURCE_ICONS = { 
    APKMirror: 'globe', 
    APKPure: 'smartphone', 
    Aptoide: 'shopping-bag', 
    GitHub: 'code-2', 
    Other: 'more-horizontal' 
};
const SOURCE_LABEL_KEYS = { 
    APKMirror: 'formSourceAPKMirror', 
    APKPure: 'formSourceAPKPure', 
    Aptoide: 'formSourceAptoide', 
    GitHub: 'formSourceGitHub', 
    Other: 'formSourceOther' 
};

function renderStep2() {
    const sourceCards = SOURCES.map(src => {
        const isSelected = state.source === src;
        return `
        <button type="button" data-source="${src}"
            class="source-card flex flex-col items-center gap-2 p-4 rounded-xl border transition-all cursor-pointer text-center focus:outline-none ${isSelected
                ? 'border-fuchsia-400 bg-fuchsia-50 dark:bg-fuchsia-950/30 dark:border-fuchsia-500 ring-2 ring-fuchsia-400/30 text-fuchsia-700 dark:text-fuchsia-300'
                : 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 hover:border-zinc-300 dark:hover:border-zinc-600 hover:bg-white dark:hover:bg-zinc-800'}">
            <i data-lucide="${SOURCE_ICONS[src]}" class="w-5 h-5"></i>
            <span class="text-xs font-semibold"><bdi>${t(SOURCE_LABEL_KEYS[src])}</bdi></span>
        </button>`;
    }).join('');

    return `
    <div class="space-y-5 animate-fade-in">
        <div class="space-y-1.5">
            <label class="block text-sm font-semibold text-zinc-800 dark:text-zinc-200"><bdi>${t('formFieldSource')}</bdi> <span class="text-rose-500">*</span></label>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">${sourceCards}</div>
            ${errors.source ? `<p class="text-xs text-rose-500 flex items-center gap-1 mt-1"><i data-lucide="alert-circle" class="w-3 h-3 flex-shrink-0"></i><bdi>${errors.source}</bdi></p>` : ''}
        </div>
        ${fieldGroup('source_url', `<bdi>${t('formFieldSourceUrl')}</bdi>`, null,
            `<input id="source_url" type="url" class="${inputClass('source_url')}" value="${escHtml(state.source_url)}" placeholder="${t('formFieldSourceUrlPlaceholder')}" dir="ltr" style="text-align: left;">`,
            errors.source_url)}
        <div class="space-y-2">
            <label class="flex items-start gap-3 cursor-pointer group">
                <div class="relative mt-0.5 flex-shrink-0">
                    <input type="checkbox" id="ack" class="sr-only peer" ${state.ack ? 'checked' : ''}>
                    <div class="w-5 h-5 rounded-md border-2 border-zinc-300 dark:border-zinc-600 peer-checked:border-fuchsia-500 peer-checked:bg-fuchsia-500 transition-all flex items-center justify-center">
                        <i data-lucide="check" class="w-3 h-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity" id="ackCheck"></i>
                    </div>
                </div>
                <span class="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed"><bdi>${t('formFieldAck')}</bdi></span>
            </label>
            ${errors.ack ? `<p class="text-xs text-rose-500 flex items-center gap-1"><i data-lucide="alert-circle" class="w-3 h-3 flex-shrink-0"></i><bdi>${errors.ack}</bdi></p>` : ''}
        </div>
    </div>`;
}

// ─── Full step shell ──────────────────────────────────────────────────────────
function renderStep() {
    const stepLabels = [t('formStep1'), t('formStep2'), t('formStep3')];
    const isRTL = currentLang === 'he';

    const rfPanel = document.getElementById('rfPanel');
    const prevStep = parseInt(rfPanel.dataset.prevStep || '0');
    rfPanel.dataset.prevStep = step;

    const klinePos = (step / (TOTAL_STEPS - 1)) * 100;
    
    // Animate the line fill, and a slide effect for the step content!
    const slideOffset = step > prevStep ? (isRTL ? '-30px' : '30px') : (step < prevStep ? (isRTL ? '30px' : '-30px') : '0px');
    
    const animStyles = `
    <style>
    .kline-line {
        position: absolute;
        top: 0;
        ${isRTL ? 'right' : 'left'}: 0;
        height: 100%;
        background: #d946ef;
        transition: width 0.8s cubic-bezier(0.65, 0, 0.35, 1);
        width: ${klinePos}%;
        z-index: 10;
    }
    @keyframes slideFadeContent {
        from { opacity: 0; transform: translateX(${slideOffset}) scale(0.98); }
        to { opacity: 1; transform: translateX(0) scale(1); }
    }
    .animate-slide-fade { animation: slideFadeContent 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
    </style>`;

    // Progress dots layout with a smooth background track
    const dots = stepLabels.map((label, i) => {
        const done = i < step;
        const active = i === step;
        const iconHTML = done ? '<i data-lucide="check" class="w-3.5 h-3.5 animate-in zoom-in duration-300"></i>' : i + 1;
        const dotClasses = done 
            ? 'bg-fuchsia-500 text-white shadow-sm ring-2 ring-fuchsia-500/20' 
            : active 
                ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 shadow-md ring-4 ring-zinc-900/10 dark:ring-white/10 scale-110' 
                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400';
        const textClasses = active ? 'text-zinc-800 dark:text-zinc-200 font-bold scale-105' : 'text-zinc-400';

        return `
        <div class="flex flex-col items-center gap-2 w-16 relative z-10 transition-transform duration-500">
            <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-500 ${dotClasses}">
                ${iconHTML}
            </div>
            <span class="text-[10px] font-medium uppercase tracking-wider transition-all duration-500 ${textClasses}">
                <bdi>${label}</bdi>
            </span>
        </div>`;
    }).join('');

    const stepContent = [renderStep0, renderStep1, renderStep2][step]();

    const isLast = step === TOTAL_STEPS - 1;
    const isFirst = step === 0;

    // Navigation arrows adapt to RTL
    const backBtn = !isFirst ? `
        <button type="button" id="rfBack"
            class="flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all active:scale-95">
            <i data-lucide="${isRTL ? 'chevron-right' : 'chevron-left'}" class="w-4 h-4"></i>
            <bdi>${t('formBack')}</bdi>
        </button>` : `<div></div>`;

    const nextBtn = !isLast ? `
        <button type="button" id="rfNext"
            class="group flex items-center gap-2 px-6 py-2.5 rounded-full text-sm font-semibold bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-md overflow-hidden relative">
            <div class="absolute inset-0 bg-gradient-to-r from-rose-400 via-fuchsia-400 to-indigo-400 opacity-0 group-hover:opacity-20 transition-opacity"></div>
            <span class="relative z-10"><bdi>${t('formNext')}</bdi></span>
            <i data-lucide="${isRTL ? 'chevron-left' : 'chevron-right'}" class="w-4 h-4 relative z-10 transition-transform ${isRTL ? 'group-hover:-translate-x-0.5' : 'group-hover:translate-x-0.5'}"></i>
        </button>` : `
        <button type="button" id="rfSubmit"
            class="group flex items-center gap-2 px-6 py-2.5 rounded-full text-sm font-semibold bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-md overflow-hidden relative">
            <div class="absolute inset-0 bg-gradient-to-r from-rose-400 via-fuchsia-400 to-indigo-400 opacity-0 group-hover:opacity-30 transition-opacity"></div>
            <i data-lucide="external-link" class="w-4 h-4 relative z-10"></i>
            <span class="relative z-10"><bdi>${t('formSubmit')}</bdi></span>
        </button>`;

    return `
    ${animStyles}
    <!-- Header -->
    <div class="mb-6 ${isRTL ? 'pl-8' : 'pr-8'}">
        <div class="inline-flex items-center gap-2 mb-3 px-3 py-1.5 rounded-full bg-fuchsia-50 dark:bg-fuchsia-950/30 border border-fuchsia-200 dark:border-fuchsia-800/40">
            <i data-lucide="plus-circle" class="w-3.5 h-3.5 text-fuchsia-500"></i>
            <span class="text-xs font-semibold text-fuchsia-600 dark:text-fuchsia-400 uppercase tracking-wider"><bdi>${t('formTitle')}</bdi></span>
        </div>
        <p class="text-sm text-zinc-500 dark:text-zinc-400"><bdi>${t('formSubtitle')}</bdi></p>
    </div>

    <!-- Progress Stepper (Animated Line) -->
    <div class="relative mb-10 pt-2 px-8">
        <div class="absolute top-[22px] left-[2rem] right-[2rem] h-[3px] bg-zinc-100 dark:bg-zinc-800/80 rounded-full overflow-hidden z-0">
            <div class="kline-line"></div>
        </div>
        <div class="relative z-20 flex justify-between items-start w-full">
            ${dots}
        </div>
    </div>

    <!-- Step content -->
    <div class="animate-slide-fade">
        ${stepContent.replace('animate-fade-in', '')}
    </div>

    <!-- Navigation -->
    <div class="flex items-center justify-between mt-8 pt-5 border-t border-zinc-100 dark:border-zinc-800">
        ${backBtn}${nextBtn}
    </div>`;
}

// ─── Event binding per step ───────────────────────────────────────────────────
function bindStepEvents() {
    // Step 0
    const appNameEl = document.getElementById('app_name');
    if (appNameEl) appNameEl.addEventListener('input', e => { state.app_name = e.target.value; clearError('app_name'); });
    const appNameHeEl = document.getElementById('app_name_he');
    if (appNameHeEl) appNameHeEl.addEventListener('input', e => { state.app_name_he = e.target.value; });
    const pkgEl = document.getElementById('package_name');
    if (pkgEl) pkgEl.addEventListener('input', e => { state.package_name = e.target.value; clearError('package_name'); });
    const descEl = document.getElementById('app_description');
    if (descEl) descEl.addEventListener('input', e => { state.app_description = e.target.value; clearError('app_description'); });

    // Step 1
    const patchEl = document.getElementById('patch_description');
    if (patchEl) patchEl.addEventListener('input', e => { state.patch_description = e.target.value; clearError('patch_description'); });
    const techEl = document.getElementById('technical_details');
    if (techEl) techEl.addEventListener('input', e => { state.technical_details = e.target.value; });

    // Step 2 — source cards
    document.querySelectorAll('.source-card').forEach(btn => {
        btn.addEventListener('click', () => {
            state.source = btn.dataset.source;
            clearError('source');
            rerender();
        });
    });
    const srcUrlEl = document.getElementById('source_url');
    if (srcUrlEl) srcUrlEl.addEventListener('input', e => { state.source_url = e.target.value; });
    const ackEl = document.getElementById('ack');
    if (ackEl) {
        ackEl.addEventListener('change', e => {
            state.ack = e.target.checked;
            clearError('ack');
            // toggle check icon visibility
            const checkIcon = document.getElementById('ackCheck');
            if (checkIcon) checkIcon.style.opacity = state.ack ? '1' : '0';
        });
    }

    // Navigation buttons
    const nextBtn = document.getElementById('rfNext');
    if (nextBtn) nextBtn.addEventListener('click', goNext);
    const backBtn = document.getElementById('rfBack');
    if (backBtn) backBtn.addEventListener('click', goBack);
    const submitBtn = document.getElementById('rfSubmit');
    if (submitBtn) submitBtn.addEventListener('click', handleSubmit);
}

function clearError(field) {
    delete errors[field];
}

function rerender() {
    const body = document.getElementById('rfBody');
    if (!body) return;
    body.innerHTML = renderStep();
    bindStepEvents();
    if (window.lucide) window.lucide.createIcons();
}

function goNext() {
    const stepErrors = validate(step);
    Object.assign(errors, stepErrors);
    if (Object.keys(stepErrors).length > 0) {
        rerender();
        return;
    }
    if (step < TOTAL_STEPS - 1) {
        step++;
        rerender();
        document.getElementById('rfPanel').scrollTop = 0;
    }
}

function goBack() {
    if (step > 0) {
        step--;
        rerender();
    }
}

// ─── Build GitHub URL ─────────────────────────────────────────────────────────
// NOTE: We intentionally do NOT pass template= here.
// When template= is present GitHub renders the yml form and ignores the body param,
// leaving all fields blank. Without template=, the title + body are pre-filled correctly.
function buildGitHubUrl() {
    const body = buildIssueBody();
    const primaryName = (currentLang === 'he' && state.app_name_he.trim()) ? state.app_name_he.trim() : state.app_name.trim() || state.app_name_he.trim();
    const title = `[App Request] ${primaryName}`;
    const params = new URLSearchParams({
        title,
        labels: 'new-app',
        body,
    });
    return `${GITHUB_ISSUE_URL}?${params.toString()}`;
}

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

function handleSubmit() {
    const stepErrors = validate(step);
    Object.assign(errors, stepErrors);
    if (Object.keys(stepErrors).length > 0) {
        rerender();
        return;
    }
    const url = buildGitHubUrl();
    window.open(url, '_blank', 'noopener,noreferrer');
    closeRequestForm();
}

// ─── Open / Close ─────────────────────────────────────────────────────────────
export function openRequestForm() {
    if (!formModal) formModal = buildFormModal();

    document.getElementById('rfPanel').dir = currentLang === 'he' ? 'rtl' : 'ltr';

    // Reset state
    step = 0;
    document.getElementById('rfPanel').dataset.prevStep = '0';
    Object.keys(state).forEach(k => {
        state[k] = typeof state[k] === 'boolean' ? false : '';
    });
    Object.keys(errors).forEach(k => delete errors[k]);

    formModal.classList.remove('hidden');
    rerender();

    requestAnimationFrame(() => {
        document.getElementById('rfBackdrop').classList.replace('opacity-0', 'opacity-100');
        const panel = document.getElementById('rfPanel');
        // Remove entry state (slide up from bottom on mobile, fade in on desktop)
        panel.classList.remove('translate-y-full', 'opacity-0');
        panel.classList.add('translate-y-0', 'opacity-100');
    });

    document.body.style.overflow = 'hidden';
}

export function closeRequestForm() {
    if (!formModal) return;
    const backdrop = document.getElementById('rfBackdrop');
    const panel = document.getElementById('rfPanel');
    backdrop.classList.add('opacity-0');
    panel.classList.add('translate-y-full', 'opacity-0');
    panel.classList.remove('translate-y-0', 'opacity-100');
    setTimeout(() => {
        formModal.classList.add('hidden');
        document.body.style.overflow = '';
    }, 350);
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

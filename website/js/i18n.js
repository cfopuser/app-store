export const i18n = {
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
        downloads: "Downloads",
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
        downloads: "הורדות",
    }
};

export let currentLang = localStorage.getItem('preferredLanguage') ||
    ((navigator.language || '').startsWith('he') ? 'he' : 'en');

export function t(key) {
    return i18n[currentLang][key] || key;
}

export function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('preferredLanguage', currentLang);
}

export function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString(
        currentLang === 'he' ? 'he-IL' : 'en-US',
        { year: 'numeric', month: 'short', day: 'numeric' }
    );
}

export function formatNumber(num) {
    if (!num) return '0';
    return new Intl.NumberFormat(currentLang === 'he' ? 'he-IL' : 'en-US', {
        notation: "compact",
        maximumFractionDigits: 1
    }).format(num);
}

export function formatSize(bytes) {
    if (!bytes) return '?';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

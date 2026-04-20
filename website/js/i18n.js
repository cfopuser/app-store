export const i18n = {
    en: {
        title: "Store",
        discover: "App Collection",
        subtitle: `Patched and "kosher" versions with automatic updates.`,
        searchPlaceholder: "Search...",
        get: "Install",
        featured: "Highlighted Release",
        allApps: "Repository",
        tryAdjusting: "Try adjusting your query parameters.",
        downloadBtn: "Install",
        downloadBtnFull: "Download APK",
        released: "Released",
        olderVersions: "Version History",
        noAssets: "Unavailable",
        loading: "Loading library...",
        noApps: "Nothing found.",
        disclaimer: "Unofficial project. Not affiliated with app developers. Use at your own risk.",
        langLabel: "HE",
        errorTitle: "Unstable",
        errorDetail: "Patch failed for v{version}",
        errorMessage: "Error: {message}",
        submitApp: "Request an App",
        latestVersion: "Latest Version",
        maintainedBy: "Maintained by",
        viewAll: "See All",
        downloads: "Downloads",
        mostDownloads: "Most Downloads"
    },
    he: {
        title: "חנות",
        discover: "מאגר אפליקציות",
        subtitle: "גרסאות ערוכות וחסומות, מתעדכנות אוטומטית.",
        searchPlaceholder: "חיפוש...",
        get: "התקנה",
        featured: "שחרור בולט",
        allApps: "מאגר אפליקציות",
        tryAdjusting: "נסה לשנות את פרמטרי החיפוש.",
        downloadBtn: "התקנה",
        downloadBtnFull: "הורד APK",
        released: "פורסם ב-",
        olderVersions: "היסטוריית גרסאות",
        noAssets: "לא זמין",
        loading: "טוען...",
        noApps: "לא נמצאו תוצאות.",
        disclaimer: "פרויקט לא רשמי. אינו קשור למפתחי האפליקציות.",
        langLabel: "EN",
        errorTitle: "לא יציב",
        errorDetail: "התיקון נכשל עבור גרסה {version}",
        errorMessage: "שגיאה: {message}",
        submitApp: "בקשת אפליקציה חדשה",
        latestVersion: "גרסה אחרונה",
        maintainedBy: "נערך ע״י",
        viewAll: "הצג הכל",
        downloads: "הורדות",
        mostDownloads: "הכי הרבה הורדות"
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

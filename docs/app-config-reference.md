# App Configuration Reference (`app.json`)

Each application managed by this repository is configured via an `app.json` file located at `apps/<app_id>/app.json`.

This document provides a comprehensive reference for all available configuration keys, data types, default values, supported source adapters, patching options, and Frida runtime modules.

---

## Table of Contents

- [1. Configuration Structures](#1-configuration-structures)
- [2. Full JSON Schema Example](#2-full-json-schema-example)
- [3. Schema Field Reference](#3-schema-field-reference)
  - [3.1 `metadata`](#31-metadata)
  - [3.2 `assets`](#32-assets)
  - [3.3 `source`](#33-source)
  - [3.4 `patching`](#34-patching)
  - [3.5 `patching.frida` (Hook Subsystems)](#35-patchingfrida-hook-subsystems)
  - [3.6 `paths`](#36-paths)
  - [3.7 `maintenance`](#37-maintenance)
- [4. Source Adapter Details](#4-source-adapter-details)
- [5. Complete Real-World Examples](#5-complete-real-world-examples)

---

## 1. Configuration Structures

The configuration parser (`core/utils.py:load_app_config`) supports two formats:

1. **Categorized Structure (Standard / Recommended)**: Cleanly separated sections (`metadata`, `assets`, `source`, `patching`, `paths`, `maintenance`).
2. **Flat Structure (Backward Compatibility)**: All keys defined at the root level of the JSON object.

---

## 2. Full JSON Schema Example

```json
{
  "metadata": {
    "id": "sample_app",
    "name": "Sample Application",
    "name_he": "אפליקציה לדוגמה",
    "package_name": "com.example.sampleapp",
    "description": "Short application description in English.",
    "description_he": "תיאור קצר של האפליקציה בעברית.",
    "full_description": "Full HTML-formatted application description in English.<br>Supports bullet points and formatting.",
    "full_description_he": "תיאור מלא ומפורט בעברית בפורמט HTML.<br>תומך ברשימות ועיצוב.",
    "category": "Tools",
    "category_he": "כלים"
  },
  "assets": {
    "icon_url": "apps/sample_app/icon.png",
    "screenshots": [
      "apps/sample_app/screenshots/screen_1.png",
      "apps/sample_app/screenshots/screen_2.png"
    ],
    "screenshots_he": [
      "apps/sample_app/screenshots_he/screen_1.png",
      "apps/sample_app/screenshots_he/screen_2.png"
    ]
  },
  "source": {
    "source": "apkeep",
    "name_play": "Sample Application",
    "repo": "owner/repository",
    "github_asset_regex": ".*universal.*\\.apk",
    "apkpure_file_type": "XAPK",
    "apkpure_version": "latest",
    "uptodown_subdomain": "sample-app"
  },
  "patching": {
    "inject_updater": true,
    "updater_target_smali": "com/example/sampleapp/MainActivity.smali",
    "inject_frida": true,
    "frida": {
      "enabled": true,
      "log_level": "INFO",
      "modules": {
        "anti_frida": {
          "enabled": true,
          "block_ports": [27042, 27047],
          "cloak_proc_maps": true,
          "mask_threads": true
        },
        "anti_root": {
          "enabled": true,
          "bypass_rootbeer": true,
          "bypass_talsec": true,
          "bypass_emulator": true,
          "anti_kill": true
        },
        "ssl_unpin": {
          "enabled": true,
          "bypass_boringssl": true,
          "bypass_okhttp": true,
          "bypass_trust_manager": true
        },
        "installer_pair": {
          "enabled": true,
          "installer_package": "com.android.vending",
          "bypass_pair_license": true
        },
        "signature_spoof": {
          "enabled": true,
          "original_signature_hex": null,
          "original_signature_base64": null
        },
        "webview_firewall": {
          "enabled": false,
          "allowed_domains": [
            "accounts.google.com",
            "auth.example.com"
          ],
          "blocked_message": "הגישה לקישור זה נחסמה"
        }
      },
      "custom_hooks": "// Inline custom Frida JavaScript code"
    },
    "clone_config": {
      "old_pkg": "com.example.sampleapp",
      "new_pkg": "com.example.sampleapp.cloned",
      "app_name_suffix": " (Cloned)"
    },
    "string_replacements": [
      {
        "key": "app_name",
        "values": {
          "default": "Sample (Patched)",
          "he": "דוגמה (ערוך)"
        }
      }
    ],
    "hotfixes": {
      "1.0.0": ".1"
    },
    "version_overrides": {
      "1.0.0": "1.0.1"
    },
    "version_code_overrides": {
      "1.0.0": "10001"
    }
  },
  "paths": {
    "version_file": "apps/sample_app/version.txt",
    "status_file": "apps/sample_app/status.json"
  },
  "maintenance": {
    "maintainer": "username"
  }
}
```

---

## 3. Schema Field Reference

### 3.1 `metadata`

Contains descriptive information about the application used by the web storefront and updater payloads.

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `id` | `string` | **Yes** | Unique identifier matching the subdirectory name in `apps/<id>/`. |
| `name` | `string` | **Yes** | Primary application name (English / default display). |
| `name_he` | `string` | No | Localized Hebrew display name. |
| `package_name` | `string` | **Yes** | The original Android application package ID (e.g. `com.whatsapp`, `il.co.bezeq.my`). |
| `description` | `string` | No | Short English summary for app cards on the website. |
| `description_he` | `string` | No | Short Hebrew summary for app cards on the website. |
| `full_description` | `string` | No | Detailed long description in English (supports HTML tags like `<br>`, `•`). |
| `full_description_he` | `string` | No | Detailed long description in Hebrew (supports HTML tags). |
| `category` | `string` | No | Categorization tag (e.g. `"Finance"`, `"Communication"`, `"Music & Audio"`, `"Tools"`). |
| `category_he` | `string` | No | Hebrew category tag (e.g. `"פיננסיים"`, `"תקשורת"`, `"כלים"`). |

---

### 3.2 `assets`

Visual media used by the web catalog.

| Field | Type | Default | Description |
| :--- | :--- | :---: | :--- |
| `icon_url` | `string` | `""` | Relative path to local icon (e.g., `apps/<id>/icon.png`) or remote image URL. |
| `screenshots` | `string[]` | `[]` | List of relative paths or URLs to English screenshots. |
| `screenshots_he` | `string[]` | `[]` | List of relative paths or URLs to Hebrew screenshots. |

---

### 3.3 `source`

Defines how the pipeline queries for new releases and downloads upstream APK/XAPK packages.

| Field | Type | Relevant Source(s) | Description |
| :--- | :--- | :--- | :--- |
| `source` | `string` | *All* | The source adapter identifier (e.g., `"apkeep"`, `"github"`, `"aptoide"`, `"apkmirror"`, `"apkpure"`, etc.). |
| `name_play` | `string` | `apkeep`, `aptoide` | Exact Google Play app title or search query for scrapers. |
| `repo` | `string` | `github` | Target GitHub repository in `"owner/repo"` format. |
| `github_asset_regex` | `string` | `github` | Regular expression to select the desired release asset (e.g. `".*universal.*\\.apk"`). |
| `apkpure_file_type` | `string` | `apkpure` | Preferred package format: `"XAPK"` (default) or `"APK"`. |
| `apkpure_version` | `string` | `apkpure` | Upstream version query: `"latest"` (default) or specific version. |
| `uptodown_subdomain`| `string` | `uptodown`, `custom_fallback` | Custom Uptodown subdomain if different from the package name. |

---

### 3.4 `patching`

Controls the bytecode and resource patching pipeline executed during `run.py --step patch`.

| Field | Type | Default | Description |
| :--- | :--- | :---: | :--- |
| `inject_updater` | `boolean` | `true` | When `true`, injects the universal in-app update checker dialog into the app's main launcher activity. |
| `updater_target_smali` | `string` | `null` | Relative Smali path (e.g., `"com/whatsapp/home/ui/HomeActivity.smali"`) if manual activity selection is preferred over automatic manifest discovery. |
| `inject_frida` | `boolean` | `true` | Master switch for Frida Gadget injection. When `false`, skips Frida injection entirely. |
| `skip_mitm` | `boolean` | `false` | Legacy flag to skip network security config injection. |
| `frida` | `object` | `{}` | Detailed configuration for Frida Core Hooks Engine (see section 3.5). |
| `clone_config` | `object` | `null` | Configuration for cloning/renaming the package (see below). |
| `string_replacements` | `object[]` | `[]` | Declarative string resource replacements in `res/values*/strings.xml`. |
| `hotfixes` | `object` | `{}` | Map of exact `versionName` to suffix (e.g. `{"1.2.3": ".1"}` -> `1.2.3.1`). |
| `version_overrides` | `object` | `{}` | Map of remote version name to replaced version name in manifest & `apktool.yml`. |
| `version_code_overrides`| `object` | `{}` | Map of remote version name to replaced integer/string `versionCode`. |

#### `clone_config` Sub-fields:
- **`old_pkg`** (`string`, required): Original package name (e.g., `"com.whatsapp"`).
- **`new_pkg`** (`string`, required): New target package name (e.g., `"com.whatsapp.kosher"`).
- **`app_name_suffix`** (`string`, default: `" (Cloned)"`): Suffix appended to the app title in `strings.xml`. Set to `""` for no suffix.

#### `string_replacements` Item Format:
```json
{
  "key": "string_resource_name",
  "values": {
    "default": "Default string value",
    "he": "ערך מחרוזת בעברית",
    "en": "English string value"
  }
}
```

---

### 3.5 `patching.frida` (Hook Subsystems)

Configures the compiled `gadget_hooks.js` payload injected alongside the Frida Gadget shared library.

| Key | Type | Default | Description |
| :--- | :--- | :---: | :--- |
| `enabled` | `boolean` | `true` | Master toggle for the Frida runtime engine. |
| `log_level` | `string` | `"INFO"` | Runtime console logging level (`"DEBUG"`, `"INFO"`, `"WARN"`, `"ERROR"`). |
| `custom_hooks` | `string \| string[]` | `null` | Inline custom JavaScript code injected into the Frida runtime. |
| `modules` | `object` | `{}` | Configuration for built-in modular hook subsystems. |

#### Frida Modules (`modules.*`):

1. **`anti_frida`**:
   - `enabled` (`boolean`, default: `true`): Native cloaking and anti-debugging defense.
   - `block_ports` (`number[]`, default: `[27042, 27047]`): Neutralizes TCP port scans for Frida listening ports.
   - `cloak_proc_maps` (`boolean`, default: `true`): Cloaks `frida-gadget.so` memory maps from `/proc/self/maps`.
   - `mask_threads` (`boolean`, default: `true`): Masks Frida-spawned threads (`gmain`, `gum-js-loop`).

2. **`anti_root`** (alias: `root_rasp`):
   - `enabled` (`boolean`, default: `true`): Universal Root & RASP bypass.
   - `bypass_rootbeer` (`boolean`, default: `true`): Neutralizes RootBeer detection checks.
   - `bypass_talsec` (`boolean`, default: `true`): Disables Talsec/FreeRASP security threat callbacks.
   - `bypass_emulator` (`boolean`, default: `true`): Spoofs build properties to bypass emulator detection.
   - `anti_kill` (`boolean`, default: `true`): Prevents anti-tamper libraries from calling `System.exit()`, `killProcess()`, or `abort()`.

3. **`ssl_unpin`**:
   - `enabled` (`boolean`, default: `true`): Universal SSL/TLS certificate unpinning.
   - `bypass_boringssl` (`boolean`, default: `true`): Bypasses native BoringSSL `SSL_CTX_set_custom_verify`.
   - `bypass_okhttp` (`boolean`, default: `true`): Hooks OkHttp3 `CertificatePinner`.
   - `bypass_trust_manager` (`boolean`, default: `true`): Hooks Java `X509TrustManager.checkServerTrusted`.

4. **`installer_pair`**:
   - `enabled` (`boolean`, default: `true`): Play Store installer spoofing.
   - `installer_package` (`string`, default: `"com.android.vending"`): Spoofed installer source package.
   - `bypass_pair_license` (`boolean`, default: `true`): Bypasses Play App Integrity and license checks.

5. **`signature_spoof`**:
   - `enabled` (`boolean`, default: `true`): Dynamic APK signature spoofing.
   - `original_signature_hex` (`string \| null`): Original signature in hexadecimal format.
   - `original_signature_base64` (`string \| null`): Original signature in Base64 format.

6. **`webview_firewall`**:
   - `enabled` (`boolean`, default: `false`): In-app browser / WebView navigation whitelist.
   - `allowed_domains` (`string[]`, default: `[]`): Whitelist of allowed domain hostnames.
   - `blocked_message` (`string`, default: `"הגישה לקישור זה נחסמה"`): User alert message when an unlisted domain is accessed.

---

### 3.6 `paths`

Internal file paths for tracking build states.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `version_file` | `string` | `"apps/<id>/version.txt"` | File where the currently published version string is stored. |
| `status_file` | `string` | `"apps/<id>/status.json"` | File where build execution status and error logs are stored. |

---

### 3.7 `maintenance`

| Field | Type | Description |
| :--- | :--- | :--- |
| `maintainer` | `string` | GitHub handle of the developer responsible for maintaining the app's configuration and patches. |

---

## 4. Source Adapter Details

| Adapter Name (`source`) | Lookup Field | Primary Use Case |
| :--- | :--- | :--- |
| `apkeep` | `package_name` (or `name_play`) | Downloads latest versions directly using the `apkeep` CLI tool from Google Play. |
| `github` | `repo` | Fetches latest APK releases from public GitHub repositories. |
| `aptoide` | `package_name` (or `name_play`) | Queries and downloads packages from Aptoide repository. |
| `apkmirror` | `package_name` | Scrapes APKMirror for latest published releases. |
| `apkpure` | `package_name` | Scrapes APKPure website for latest APK / XAPK files. |
| `apkpure_mobile` | `package_name` | Mobile API scraper for APKPure. |
| `apkcombo` | `package_name` | Scrapes APKCombo for direct APK/XAPK links. |
| `google_play` | `package_name` | Google Play Store direct scraper. |
| `uptodown` | `package_name` | Scrapes Uptodown for package downloads. |
| `whatsapp_official` | `package_name` | Direct scraper for official WhatsApp standalone web APK releases. |
| `custom_fallback` | `package_name` | Multi-source fallback engine. |

---

## 5. Complete Real-World Examples

### Example 1: Standard Play Store App (e.g. `apps/bezeq/app.json`)
Zero custom code needed — fully declarative with automated Frida unpinning and root bypass:

```json
{
  "metadata": {
    "id": "bezeq",
    "name": "בזק Bezeq",
    "name_he": "בזק Bezeq",
    "package_name": "il.co.bezeq.my",
    "description": "Bezeq app – patched for sideloading.",
    "description_he": "אפליקציית בזק - ערוכה להתקנה מקובץ.",
    "category": "Communication",
    "category_he": "תקשורת"
  },
  "assets": {
    "icon_url": "apps/bezeq/icon.png",
    "screenshots": [
      "apps/bezeq/screenshots/screen_1.png"
    ],
    "screenshots_he": [
      "apps/bezeq/screenshots_he/screen_1.png"
    ]
  },
  "source": {
    "source": "apkeep",
    "name_play": "בזק Bezeq"
  },
  "patching": {
    "inject_updater": false
  },
  "paths": {
    "version_file": "apps/bezeq/version.txt",
    "status_file": "apps/bezeq/status.json"
  },
  "maintenance": {
    "maintainer": "cfopuser"
  }
}
```

---

### Example 2: GitHub App with WebView Domain Whitelist (e.g. `apps/meld/app.json`)

```json
{
  "metadata": {
    "id": "meld",
    "name": "Meld",
    "name_he": "מלד",
    "package_name": "com.meld.app",
    "description": "Music client patched to block unneeded web views.",
    "description_he": "נגן מוזיקה ערוך לחסימת דפדפנים פנימיים.",
    "category": "Music & Audio",
    "category_he": "מוזיקה ושמע"
  },
  "assets": {
    "icon_url": "https://raw.githubusercontent.com/FrancescoGrazioso/Meld/main/fastlane/metadata/android/en-US/images/icon.png"
  },
  "source": {
    "source": "github",
    "repo": "FrancescoGrazioso/Meld"
  },
  "patching": {
    "inject_updater": false,
    "frida": {
      "webview_firewall": {
        "allowed_domains": [
          "accounts.spotify.com",
          "open.spotify.com",
          "accounts.google.com",
          "appleid.apple.com"
        ]
      }
    },
    "hotfixes": {
      "0.6.2": ".1"
    }
  },
  "paths": {
    "version_file": "apps/meld/version.txt",
    "status_file": "apps/meld/status.json"
  },
  "maintenance": {
    "maintainer": "lilor159357"
  }
}
```

---

### Example 3: Cloned App with Version Overrides (e.g. `apps/whatsapp/app.json`)

```json
{
  "metadata": {
    "id": "whatsapp",
    "name": "WhatsApp Messenger",
    "name_he": "וואטסאפ",
    "package_name": "com.whatsapp",
    "description": "WhatsApp with kosher patch applied.",
    "description_he": "וואטסאפ מסונן: חסימת תמונות פרופיל, ערוצים וסטטוסים.",
    "category": "Communication",
    "category_he": "תקשורת"
  },
  "assets": {
    "icon_url": "apps/whatsapp/icon.png"
  },
  "source": {
    "source": "apkeep",
    "name_play": "WhatsApp Messenger"
  },
  "patching": {
    "inject_updater": true,
    "updater_target_smali": "com/whatsapp/home/ui/HomeActivity.smali",
    "version_overrides": {
      "2.26.29.73": "2.26.30.2"
    },
    "version_code_overrides": {
      "2.26.29.73": "263000110"
    },
    "hotfixes": {
      "2.26.30.70": ".1"
    },
    "clone_config": {
      "old_pkg": "com.whatsapp",
      "new_pkg": "com.whatsapp.kosher",
      "app_name_suffix": ""
    }
  },
  "paths": {
    "version_file": "apps/whatsapp/version.txt",
    "status_file": "apps/whatsapp/status.json"
  },
  "maintenance": {
    "maintainer": "lilor159357"
  }
}
```

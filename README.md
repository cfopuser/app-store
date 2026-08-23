# App Store & Automated APK Patcher

[![Patch and Sign APKs](https://github.com/cfopuser/app-store/actions/workflows/apk_patcher.yml/badge.svg)](https://github.com/cfopuser/app-store/actions/workflows/apk_patcher.yml)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-blue.svg)](LICENSE)
[![Web Store](https://img.shields.io/badge/Web_Store-Live_Catalog-rose.svg)](https://cfopuser.github.io/app-store/)
[![Mitmachim Top](https://img.shields.io/badge/Community-Mitmachim_Top-blue)](https://mitmachim.top/topic/93647/%D7%9C%D7%94%D7%95%D7%A8%D7%93%D7%94-%D7%9E%D7%90%D7%92%D7%A8-%D7%90%D7%A4%D7%9C%D7%99%D7%A7%D7%A6%D7%99%D7%95%D7%AA-%D7%9E%D7%95%D7%AA%D7%90%D7%9E%D7%95%D7%AA-%D7%9C%D7%A1%D7%99%D7%A0%D7%95%D7%9F-%D7%9E%D7%AA%D7%A2%D7%93%D7%9B%D7%A0%D7%95%D7%AA-%D7%90%D7%95%D7%98%D7%95%D7%9E%D7%98%D7%99%D7%AA)

An automated, community-driven repository and build system for patched Android apps.  
Designed to provide apps tailored for filtered networks (NetFree, etc.), emulator and root environments, sideloading restrictions, and kosher or image-filtered modifications — automatically updated and published whenever a new upstream version is released.

- Web Catalog: [cfopuser.github.io/app-store](https://cfopuser.github.io/app-store/)
- Community Thread: [Mitmachim Top (מתמחים טופ)](https://mitmachim.top/topic/93647/%D7%9C%D7%94%D7%95%D7%A8%D7%93%D7%94-%D7%9E%D7%90%D7%92%D7%A8-%D7%90%D7%A4%D7%9C%D7%99%D7%A7%D7%A6%D7%99%D7%95%D7%AA-%D7%9E%D7%95%D7%AA%D7%90%D7%9E%D7%95%D7%AA-%D7%9C%D7%A1%D7%99%D7%A0%D7%95%D7%9F-%D7%9E%D7%AA%D7%A2%D7%93%D7%9B%D7%A0%D7%95%D7%AA-%D7%90%D7%95%D7%98%D7%95%D7%9E%D7%98%D7%99%D7%AA)

---

## The Story and Motivation

Many Android applications cannot be used out-of-the-box in specific environments:
- Filtered Networks (NetFree): Blocked by TLS certificate pinning or unsupported custom root CAs.
- Sideloading and Installer Checks: Apps refusing to run unless installed via Google Play.
- Root and Emulator Restrictions: Banking and utility apps checking device integrity (FreeRASP, Play Integrity, RootBeer).
- Custom and Kosher Editions: Requirements for media removal (blocking images, videos, feeds, or channels).

In the community, developers regularly patch and share modified APKs. But as soon as an app releases an update, the old build becomes obsolete, links break, and someone has to manually decompile, patch, resign, and re-upload the file from scratch.

### The Solution: "Write the patch once, automate the rest."
With this repository, you write the patching logic once in a Python module (`patch.py`). The CI/CD engine takes care of everything else:
1. Monitoring upstream sources daily for new releases.
2. Downloading and converting packages (including dynamic multi-split XAPK merging).
3. Applying automated certificate and Smali patches.
4. Injecting an in-app auto-updater.
5. Recompiling, signing, and publishing directly to GitHub Releases and the web catalog.

---

## Key Features

- Fully Automated CI/CD: Daily GitHub Actions workflow checks, builds, and publishes new releases without manual intervention.
- Universal In-App Auto-Updater: Injected directly into decompiled smali bytecodes, alerting users via a native dialog whenever an updated APK is available on GitHub Releases.
- Network Filter Support (apk-mitm): Automatically injects network security configurations to trust user/custom CAs for filtered connections.
- Multi-Source Scraping: Integrated download source adapters for Apkeep (Play Store), APKPure, Aptoide, APKCombo, Uptodown, and GitHub Releases.
- Split-APK / XAPK Conversion: Built-in APKEditor and xapktoapk pipelines to merge multi-architecture split packages into single standalone APKs.
- Package Cloning (clone_config): Support for package renaming to allow side-by-side installations.
- Modern Web Frontend: Clean, fast web interface with dark mode, search, multi-language support (Hebrew/English), screenshot galleries, and direct downloads.

---

## How the Pipeline Works

```text
  ┌─────────────────┐
  │ Upstream Source │ (Play Store, APKPure, Aptoide, GitHub, etc.)
  └────────┬────────┘
           │ (Version check / Download)
           ▼
  ┌─────────────────┐
  │  Download Step  │ ──► XAPK to APK Merge (APKEditor)
  │ (run.py --step  │ ──► apk-mitm (Network Security Config injection)
  │    download)    │ ──► pre_patch.py (Optional APK-level transformations)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Decompile Step  │ ──► Apktool (smali & resources decode)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │   Patch Step    │ ──► apps/<app_id>/patch.py (Smali regex / AST edits)
  │  (run.py --step │ ──► Package Cloner (AndroidManifest / authorities rename)
  │     patch)      │ ──► Universal Updater Injection (storeautoupdater)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Rebuild & Sign  │ ──► Apktool build ──► UberApkSigner (Keystore)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Publish Release │ ──► GitHub Releases + Static Web Catalog Update
  └─────────────────┘

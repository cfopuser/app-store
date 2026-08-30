# AGENTS.md

## Repository Overview
Automated modular APK patching and publishing pipeline for customized Android apps (NetFree network filter compatibility, sideload/integrity bypasses, and kosher/media-trimmed modifications). Outputs are published to GitHub Releases and indexed for the static GitHub Pages web catalog (`cfopuser/app-store`).

## Core Architecture & Execution Flow
Orchestrated via `run.py` in a **Single-Pass Pipeline**:
1. **Download (`run.py --step download`)**:
   - Source adapter selected via `apps/<app_id>/app.json` (`core/sources/registry.py`).
   - Compares remote version with `apps/<app_id>/version.txt`.
   - Downloads artifact as `latest.apk` (merging `.xapk`/split APKs via `core/apkeditor_merger.py` if needed).
   - Executes optional binary hook `apps/<app_id>/pre_patch.py` (`run_pre_patch`).
2. **Decompile (CI / Apktool)**:
   - `apktool d -f latest.apk -o build_output`
3. **Patch (`run.py --step patch`)**:
   - **AAPT2 Resilience**: Strips `recreateOnConfigChanges` from Manifest (fixes API 37 bug) and cleans invalid `layout_gravity="0x0"` from layout XMLs.
   - **String Replacements**: Applies declarative `string_replacements` from `app.json` across localized `res/values*/strings.xml`.
   - **Frida Gadget Subsystem (`core/frida/`)**:
     - Automatically bundles universal hook modules (`ssl_unpin.js`, `root_rasp.js`, `installer_pair.js`, `signature_spoof.js`, `webview_firewall.js`).
     - Places `libgadget.so`, `libgadget.config.so`, and `libgadget.script.so` into target ABI folders under `lib/`.
     - Injects `System.loadLibrary("gadget")` into `Application.<clinit>` or `MainActivity.<clinit>`.
     - Sets `android:extractNativeLibs="true"` in Manifest.
   - **Custom App Patcher (`apps/<app_id>/patch.py`)**: Optional smali/asset surgery (e.g. WhatsApp tab trimming, Spotify media nulling).
   - **Package Cloner**: Applies package rename if `clone_config` exists in `app.json` (`core/cloner.py`).
   - **Hotfixes & Overrides**: Applies version/code overrides or hotfix suffixes if defined (`core/hotfix.py`).
   - **Universal In-App Auto-Updater**: Injects `storeautoupdater` smali (`core/universal_updater.py`) unless `inject_updater: false`.
4. **Repack & Sign (CI / Apktool & UberApkSigner)**:
   - `apktool b build_output -o patched_unsigned.apk`
   - Signs with `uber-apk-signer` and uploads release tagged `{app_id}-v{version}`.

## Developer Commands

### Testing
- **Run all unit tests**: `python -m pytest tests`
  - ⚠️ **CRITICAL**: Do NOT run bare `pytest`. Bare pytest attempts to collect scratch scripts in `scratch/` which will fail with missing module errors. Always specify `tests`.
- **Run a single test file**: `python -m pytest tests/test_frida_gadget.py`
- **Run a single test case**: `python -m pytest tests/test_frida_builder.py -k test_default_modules_included`

### Pipeline Operations
- **List registered apps**: `python run.py --list`
- **Process single app (download only)**: `python run.py --app <app_id> --step download`
- **Patch decompiled app directory**: `python run.py --app <app_id> --step patch` (expects `./build_output/`)
- **Process all steps locally**: `python run.py --app <app_id> --step all`
- **Regenerate app catalog listing**: `python run.py --update-listing` (updates `apps.json`)
- **Update release download counts**: `python run.py --update-stats` (requires `GITHUB_TOKEN`)
- **Update static releases index**: `python run.py --update-releases` (requires `GITHUB_TOKEN`, writes `releases.json`)
- **Fetch Google Play metadata & assets**: `python metadata_fetcher.py`

## App Package Conventions (`apps/<app_id>/`)
- `app.json`: Configuration and metadata (flat or categorized into `metadata`, `assets`, `source`, `patching`, `paths`, `maintenance`).
  - Required fields: `id`, `name`, `package_name`, `source`, `version_file`, `status_file`.
  - Optional toggles: `inject_frida` (default `true`), `frida` (config dict for `ssl_unpin`, `root_rasp`, `installer_pair`, `signature_spoof`, `webview_firewall`, `custom_hooks`), `string_replacements`, `inject_updater` (default `true`), `updater_target_smali`, `clone_config`, `hotfixes`, `version_overrides`, `version_code_overrides`.
- `hooks.js`: Optional app-specific Frida JavaScript hook module.
- `patch.py`: Optional entrypoint for custom smali/resource patching. Must expose `def patch(decompiled_dir: str) -> bool:`.
- `pre_patch.py`: Optional pre-decompilation APK binary modifier. Must expose `def pre_patch(apk_path: str) -> bool:`.
- `version.txt`: Tracks currently published upstream version.
- `status.json`: Generated JSON indicating last build timestamp and success/failure status.

## Operational & Environment Gotchas
- **Repository owner/name resolution**: Resolved in `core/repository.py` in priority order: `GITHUB_REPOSITORY` env -> `UPDATER_REPO_OWNER` & `UPDATER_REPO_NAME` env -> git remote origin URL -> default `cfopuser/app-store`. Set these env vars when working on forks.
- **Decompiled directory path**: CI and CLI conventions strictly expect the decompiled directory to be named `build_output`.
- **Working directory**: All CLI scripts must be run from the repository root to ensure relative imports and `apps/` path resolution succeed.
- **External CLI dependencies for end-to-end runs**: Java 17+, `apktool`, and `uber-apk-signer`.

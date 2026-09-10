# Architecture

## Core Flow

The repository runs one consistent patching flow:

1. Download stage (`run.py --step download`)
   - Resolve source adapter by `app.json.source`
   - Check remote version
   - Download APK if update exists
   - Run optional `pre_patch.py`
   - Run optional `apk-mitm` (unless `skip_mitm: true`)

2. Patch stage (`run.py --step patch`)
   - Run required `apps/<app_id>/patch.py`
   - Run optional clone stage (`clone_config`)
   - Run universal updater injection (unless `inject_updater: false`)

3. CI build stage
   - Decode, rebuild, sign, release
   - Update `version.txt`

## Extension Points

- Source adapters: `core/sources/*.py`
- APK-level hook: `apps/<app_id>/pre_patch.py`
- Decompiled patch hook: `apps/<app_id>/patch.py`
- Clone transform: `core/cloner.py` via `clone_config`
- Updater injection: `core/universal_updater.py`

## Failure Semantics

- Download/search/source errors raise `DownloadError` and fail the app pipeline.
- "No update" returns success with no artifact updates.
- Patch/clone/updater failures fail the app pipeline and update `status.json`.

## App Config Keys

See the full documentation in [App Configuration Reference](app-config-reference.md).

- Required:
  - `id`, `name`, `package_name`, `source`, `version_file`, `status_file`
- Optional behavior:
  - `skip_mitm` (bool)
  - `inject_updater` (bool, default `true`)
  - `updater_target_smali` (str)
  - `clone_config` (`old_pkg`, `new_pkg`, optional `app_name_suffix`)
  - `frida` (Frida Core Hooks Engine configuration and modules)
  - `string_replacements`, `hotfixes`, `version_overrides`, `version_code_overrides`

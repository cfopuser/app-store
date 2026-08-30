"""
Generic patch runner — orchestrates Frida injection, AAPT2 resilience, string replacements,
custom app patch.py modules, package cloner, hotfixes, and universal updater.
"""

from __future__ import annotations

import importlib.util
import os
import re
from typing import Any

from core.cloner import run_clone
from core.frida.gadget import inject_frida_gadget
from core.hotfix import apply_hotfix_if_needed
from core.universal_updater import inject_universal_updater
from core.utils import load_app_config


def apply_aapt2_resilience(decompiled_dir: str):
    """
    Apply AAPT2 compile resilience fixes:
    1. Strip 'recreateOnConfigChanges' attribute from AndroidManifest.xml (API 37 bug).
    2. Strip invalid 'layout_gravity="0x0"' and 'gravity="0x0"' from layout XMLs.
    """
    # 1. AndroidManifest.xml
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(r'\s*[a-zA-Z0-9_:]*recreateOnConfigChanges=["\'][^"\']*["\']', '', content)
            if new_content != content:
                with open(manifest_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print("[+] [AAPT2 Resilience] Stripped recreateOnConfigChanges from AndroidManifest.xml")
        except Exception as e:
            print(f"[-] [AAPT2 Resilience] Error modifying manifest: {e}")

    # 2. Layout XML files
    res_dir = os.path.join(decompiled_dir, "res")
    if os.path.isdir(res_dir):
        for root, _, files in os.walk(res_dir):
            if not os.path.basename(root).startswith("layout"):
                continue
            for file in files:
                if not file.endswith(".xml"):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        xml_content = f.read()
                    # Fix 0x0 gravity attributes
                    fixed_content = re.sub(r'\s*android:layout_gravity=["\']0x0["\']', '', xml_content)
                    fixed_content = re.sub(r'\s*android:gravity=["\']0x0["\']', '', fixed_content)
                    if fixed_content != xml_content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(fixed_content)
                        print(f"[+] [AAPT2 Resilience] Fixed invalid gravity attribute in {file}")
                except Exception:
                    pass


def apply_string_replacements(decompiled_dir: str, replacements: list[dict[str, Any]] | None):
    """
    Replace string resources in res/values*/strings.xml based on declarative configuration.
    """
    if not replacements:
        return

    res_dir = os.path.join(decompiled_dir, "res")
    if not os.path.isdir(res_dir):
        return

    for item in replacements:
        key = item.get("key")
        values = item.get("values", {})
        if not key or not values:
            continue

        for lang, val in values.items():
            target_dirs = []
            if lang == "default":
                target_dirs.append("values")
            elif lang == "he":
                target_dirs.extend(["values-he", "values-iw", "values"])
            else:
                target_dirs.append(f"values-{lang}")

            for vdir in target_dirs:
                vdir_path = os.path.join(res_dir, vdir)
                strings_xml = os.path.join(vdir_path, "strings.xml")
                if not os.path.isfile(strings_xml):
                    continue

                try:
                    with open(strings_xml, "r", encoding="utf-8") as f:
                        s_content = f.read()

                    pattern = re.compile(rf'(<string\s+name=["\']{re.escape(key)}["\']>)(.*?)(</string>)', re.DOTALL)
                    if pattern.search(s_content):
                        new_content = pattern.sub(rf'\g<1>{val}\g<3>', s_content)
                        if new_content != s_content:
                            with open(strings_xml, "w", encoding="utf-8") as f:
                                f.write(new_content)
                            print(f"[+] [String Replacer] Replaced '{key}' in {vdir}/strings.xml")
                except Exception as exc:
                    print(f"[-] [String Replacer] Failed to patch {strings_xml}: {exc}")


def run_patch(app_id: str, decompiled_dir: str) -> bool:
    """
    Apply single-pass patch pipeline to decompiled APK directory:
    1. AAPT2 Resilience transforms (manifest bug fixes, gravity cleanups).
    2. Declarative string replacements.
    3. Frida Gadget & Universal Hook Injection (unless disabled).
    4. Custom app patch.py module (if present).
    5. Package Cloner (if clone_config is set).
    6. Hotfixes & Version Overrides.
    7. Universal In-App Auto-Updater (if inject_updater is true).

    Args:
        app_id: The app identifier (subfolder name under apps/).
        decompiled_dir: Path to the apktool-decompiled directory.

    Returns:
        True if all patch stages completed successfully, False otherwise.
    """
    print(f"\n[*] [{app_id}] Starting single-pass patch pipeline on: {decompiled_dir}")

    config = {}
    try:
        config = load_app_config(app_id)
    except Exception:
        # Keep patch runner resilient in unit tests and local ad-hoc runs
        config = {}

    # 1. AAPT2 Resilience
    apply_aapt2_resilience(decompiled_dir)

    # 2. String Replacements
    string_replacements = config.get("string_replacements", [])
    if string_replacements:
        apply_string_replacements(decompiled_dir, string_replacements)

    # 3. Frida Gadget Subsystem
    # Enabled by default unless explicitly set to false
    inject_frida = config.get("inject_frida", True)
    if isinstance(config.get("frida"), dict):
        inject_frida = config["frida"].get("enabled", inject_frida)

    if inject_frida:
        print(f"[*] [{app_id}] Applying Frida Gadget injection...")
        frida_success = inject_frida_gadget(decompiled_dir, config, app_id=app_id)
        if not frida_success:
            print(f"[-] [{app_id}] Frida Gadget injection failed.")
            return False
    else:
        print(f"[*] [{app_id}] Frida injection disabled by config.")

    # 4. Custom App Smali/Asset Surgery (Optional escape hatch)
    patch_module_path = os.path.join("apps", app_id, "patch.py")
    if os.path.isfile(patch_module_path):
        print(f"[*] [{app_id}] Loading custom patch module: {patch_module_path}")
        try:
            spec = importlib.util.spec_from_file_location(
                f"apps.{app_id}.patch", patch_module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "patch") and callable(module.patch):
                print(f"[*] [{app_id}] Executing custom patch.py...")
                custom_result = module.patch(decompiled_dir)
                if not custom_result:
                    print(f"[-] [{app_id}] Custom patch.py returned failure.")
                    return False
        except Exception as e:
            print(f"[-] [{app_id}] Custom patch.py raised an exception: {e}")
            return False
    else:
        print(f"[i] [{app_id}] No custom patch.py found (using standard universal pipeline).")

    # 5. Package Cloner
    clone_config = config.get("clone_config")
    if clone_config:
        print(f"[*] [{app_id}] Applying clone configuration...")
        if not run_clone(decompiled_dir, clone_config):
            print(f"[-] [{app_id}] Clone stage failed.")
            return False

    # 6. Hotfixes & Overrides
    apply_hotfix_if_needed(decompiled_dir, config)

    # 7. Universal Auto-Updater
    inject_updater = bool(config.get("inject_updater", True))
    if inject_updater:
        target_smali = config.get("updater_target_smali")
        print(f"[*] [{app_id}] Applying updater injection...")
        updater_success = inject_universal_updater(
            decompiled_dir=decompiled_dir,
            app_id=app_id,
            target_activity_smali=target_smali,
        )
        if not updater_success:
            print(f"[-] [{app_id}] Updater injection failed.")
            return False
    else:
        print(f"[*] [{app_id}] Updater injection disabled by config.")

    print(f"[+] [{app_id}] Patch pipeline completed successfully!")
    return True

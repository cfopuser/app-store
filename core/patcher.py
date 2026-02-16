"""
Generic patch runner — dynamically loads an app's patch.py module.
"""

import importlib
import importlib.util
import os
import sys


def run_patch(app_id: str, decompiled_dir: str) -> bool:
    """
    Import apps/{app_id}/patch.py and call its patch(decompiled_dir) function.

    Args:
        app_id: The app identifier (subfolder name under apps/).
        decompiled_dir: Path to the apktool-decompiled directory.

    Returns:
        True if the patch was applied successfully, False otherwise.
    """
    patch_module_path = os.path.join("apps", app_id, "patch.py")

    if not os.path.isfile(patch_module_path):
        print(f"[-] [{app_id}] No patch.py found at {patch_module_path}")
        return False

    print(f"[*] [{app_id}] Loading patch module: {patch_module_path}")

    try:
        spec = importlib.util.spec_from_file_location(
            f"apps.{app_id}.patch", patch_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"[-] [{app_id}] Failed to load patch module: {e}")
        return False

    if not hasattr(module, "patch") or not callable(module.patch):
        print(f"[-] [{app_id}] patch.py does not have a callable 'patch' function")
        return False

    print(f"[*] [{app_id}] Running patch on: {decompiled_dir}")
    try:
        result = module.patch(decompiled_dir)
    except Exception as e:
        print(f"[-] [{app_id}] Patch raised an exception: {e}")
        return False

    if result:
        print(f"[+] [{app_id}] Patch completed successfully!")
    else:
        print(f"[-] [{app_id}] Patch returned failure.")

    return bool(result)

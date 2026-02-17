"""Shared utility functions for the patching framework."""

import json
import os


def set_github_output(key: str, value: str):
    """Write a key=value pair to GITHUB_OUTPUT (or print if not in CI)."""
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"[Output] {key}={value}")


def get_local_version(version_file: str) -> str:
    """Read the locally tracked version from a file."""
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "0.0.0"


def update_version(version_file: str, new_version: str):
    """Write the new version to the tracking file."""
    os.makedirs(os.path.dirname(version_file), exist_ok=True)
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(new_version)


def update_status(status_file: str, success: bool, failed_version: str = "",
                  error_message: str = ""):
    """Write build status to the per-app status file."""
    import datetime
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    status = {
        "success": success,
        "failed_version": failed_version,
        "error_message": error_message,
        "updated_at": datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y"),
    }
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status, f)


def load_app_config(app_id: str) -> dict:
    """Load and return the app.json config for a given app ID."""
    config_path = os.path.join("apps", app_id, "app.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"App config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def discover_apps() -> list[str]:
    """Return a list of all registered app IDs (subfolder names under apps/)."""
    apps_dir = "apps"
    if not os.path.isdir(apps_dir):
        return []
    app_ids = []
    for name in sorted(os.listdir(apps_dir)):
        config_path = os.path.join(apps_dir, name, "app.json")
        if os.path.isfile(config_path):
            app_ids.append(name)
    return app_ids


def generate_apps_listing(output_file: str = "apps.json"):
    """Discover all apps and write their IDs to a JSON file for the frontend."""
    app_ids = discover_apps()
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(app_ids, f, indent=2)
    print(f"[+] Generated {output_file} with {len(app_ids)} apps.")


def run_apk_mitm(apk_path: str):
    """
    Run apk-mitm on the specified APK file.
    Requires apk-mitm to be installed (npm install -g apk-mitm).
    """
    import subprocess
    import shutil

    if not os.path.exists(apk_path):
        print(f"[-] APK not found: {apk_path}")
        return False

    print(f"[*] Running apk-mitm on {apk_path}...")

    # Check if apk-mitm is available
    if not shutil.which("apk-mitm"):
        print("[-] apk-mitm not found in PATH. Please install it with 'npm install -g apk-mitm'.")
        return False

    try:
        # apk-mitm <path-to-apk>
        # It typically produces <original>-patched.apk
        result = subprocess.run(["apk-mitm", apk_path], check=True)
        
        # Determine the output filename
        # apk-mitm logic: if input is app.apk, output is app-patched.apk
        base, ext = os.path.splitext(apk_path)
        patched_apk = f"{base}-patched{ext}"

        if os.path.exists(patched_apk):
            print(f"[+] apk-mitm completed. Patched APK: {patched_apk}")
            # Replace original with patched version to keep pipeline simple
            os.replace(patched_apk, apk_path)
            print(f"[*] Replaced original {apk_path} with patched version.")
            return True
        else:
            print(f"[-] apk-mitm finished but {patched_apk} was not found.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"[-] apk-mitm failed: {e}")
        return False
    except Exception as e:
        print(f"[-] An error occurred while running apk-mitm: {e}")
        return False

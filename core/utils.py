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
    """Load and return the app.json config for a given app ID, flattening categories."""
    config_path = os.path.join("apps", app_id, "app.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"App config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # If it's the new nested structure, flatten it for backward compatibility
    # We check for common category keys
    categories = ["metadata", "assets", "source", "patching", "paths", "maintenance"]
    if any(k in config and isinstance(config[k], dict) for k in categories):
        flattened = {}
        for key, value in config.items():
            if key in categories and isinstance(value, dict):
                flattened.update(value)
            else:
                flattened[key] = value
        return flattened
    return config


def save_app_config(app_id: str, config: dict):
    """Save the app config in a categorized structure."""
    config_path = os.path.join("apps", app_id, "app.json")
    
    # Define mapping of fields to categories
    mapping = {
        "metadata": ["id", "name", "name_he", "package_name", "description", "description_he", 
                     "full_description", "full_description_he", "category", "category_he"],
        "assets": ["icon_url", "screenshots", "screenshots_he"],
        "source": ["source", "repo", "github_asset_regex", "name_play"],
        "patching": ["skip_mitm", "inject_updater", "updater_target_smali", "hotfixes", "clone_config"],
        "paths": ["version_file", "status_file"],
        "maintenance": ["maintainer"]
    }
    
    categorized = {}
    remaining_keys = set(config.keys())
    
    for category, fields in mapping.items():
        cat_data = {}
        for field in fields:
            if field in config:
                cat_data[field] = config[field]
                remaining_keys.discard(field)
        if cat_data:
            categorized[category] = cat_data
            
    # Add any leftover keys to the root
    for key in remaining_keys:
        categorized[key] = config[key]
        
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(categorized, f, indent=2, ensure_ascii=False)


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

def generate_download_stats(repo_name: str = "cfopuser/app-store", output_file: str = "download_stats.json"):
    """
    Fetch all releases from GitHub and aggregate download counts per app.
    Only counts .apk assets.
    """
    import requests
    
    print(f"[*] Fetching release statistics for {repo_name}...")
    
    app_ids = discover_apps()
    stats = {app_id: 0 for app_id in app_ids}
    
    # GitHub API usually returns 30 per page. We'll fetch a few pages to be sure.
    page = 1
    total_releases_processed = 0
    
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
        
    while True:
        url = f"https://api.github.com/repos/{repo_name}/releases?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[-] Failed to fetch releases: {response.status_code} {response.text}")
            break
            
        releases = response.json()
        if not releases:
            break
            
        for release in releases:
            tag = release.get("tag_name", "")
            assets = release.get("assets", [])
            
            # Determine which app this release belongs to
            target_app = None
            for app_id in app_ids:
                if tag.startswith(f"{app_id}-v"):
                    target_app = app_id
                    break
            
            # Special case for 'bit' which might use 'vX.Y.Z' without app prefix
            if not target_app and "bit" in app_ids:
                if tag.startswith("v") and "-" not in tag:
                    target_app = "bit"
            
            if target_app:
                for asset in assets:
                    if asset.get("name", "").endswith(".apk"):
                        stats[target_app] += asset.get("download_count", 0)
            
        total_releases_processed += len(releases)
        if len(releases) < 100:
            break
        page += 1
        
    print(f"[+] Processed {total_releases_processed} releases. Saving stats...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"[+] Download stats saved to {output_file}")


def generate_releases_index(repo_name: str = "cfopuser/app-store", output_file: str = "releases.json"):
    """
    Fetch ALL releases from GitHub (with pagination) and write a static
    releases.json index.  This file is committed to the repo and served
    by GitHub Pages so the website never needs to hit the GitHub API
    at runtime — completely side-stepping rate-limit issues.

    Must be run in CI where GITHUB_TOKEN is available (5 000 req/h).
    """
    import requests

    print(f"[*] Generating releases index for {repo_name}...")

    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    else:
        print("[!] Warning: No GITHUB_TOKEN set — may hit rate limits.")

    all_releases = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{repo_name}/releases?per_page=100&page={page}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"[-] Failed to fetch releases page {page}: {resp.status_code} {resp.text}")
            break

        releases = resp.json()
        if not releases:
            break

        for r in releases:
            # Only keep the fields the website actually needs — keeps the
            # file small and avoids leaking anything sensitive.
            entry = {
                "tag_name": r.get("tag_name", ""),
                "name": r.get("name", ""),
                "published_at": r.get("published_at", ""),
                "body": r.get("body", ""),
                "html_url": r.get("html_url", ""),
                "assets": [],
            }
            for asset in r.get("assets", []):
                entry["assets"].append({
                    "name": asset.get("name", ""),
                    "size": asset.get("size", 0),
                    "download_count": asset.get("download_count", 0),
                    "browser_download_url": asset.get("browser_download_url", ""),
                })
            all_releases.append(entry)

        if len(releases) < 100:
            break
        page += 1

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_releases, f, separators=(",", ":"))

    print(f"[+] Releases index saved to {output_file} ({len(all_releases)} releases)")

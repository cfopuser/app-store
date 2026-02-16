"""
Generic APKMirror downloader — config-driven.

Reads an app's app.json and checks APKMirror for updates.
Downloads the APK if a newer version is available.
"""

import os
import re
import sys

from apkmirror import APKMirror
from core.utils import get_local_version, update_version, set_github_output


def extract_version_from_title(title: str) -> str:
    """Pull a version string like '6.10.1' out of an APKMirror result title."""
    match = re.search(r"(\d+(?:\.\d+)+)", title)
    return match.group(1) if match else "0.0.0"


def download_app(app_config: dict, output_filename: str = "latest.apk") -> tuple:
    """
    Check APKMirror for updates and download if a newer version exists.

    Args:
        app_config: Parsed app.json dict.
        output_filename: Where to save the downloaded APK.

    Returns:
        (update_needed: bool, new_version: str | None)
    """
    package_name = app_config["package_name"]
    version_file = app_config["version_file"]
    app_name = app_config["name"]

    apkm = APKMirror(timeout=10, results=5)

    print(f"[*] [{app_name}] Checking APKMirror for: {package_name}")

    # 1. Get local version
    local_version = get_local_version(version_file)
    print(f"[*] [{app_name}] Local version: {local_version}")

    # 2. Search APKMirror
    print(f"[*] [{app_name}] Searching APKMirror...")
    try:
        results = apkm.search(package_name)
    except Exception as e:
        print(f"[-] [{app_name}] Search failed: {e}")
        return False, None

    if not results:
        print(f"[-] [{app_name}] No results found on APKMirror.")
        return False, None

    # 3. Analyze latest result
    latest_result = results[0]
    app_title = latest_result["name"]
    remote_version = extract_version_from_title(app_title)

    print(f"[*] [{app_name}] Latest release: {app_title}")
    print(f"[*] [{app_name}] Remote version: {remote_version}")

    # 4. Compare versions
    if remote_version == local_version:
        print(f"[i] [{app_name}] Versions match. No update needed.")
        return False, None

    print(f"[!] [{app_name}] Update detected! ({local_version} -> {remote_version})")

    # 5. Download
    app_release_url = latest_result["link"]

    try:
        print(f"[*] [{app_name}] Getting variant details...")
        details = apkm.get_app_details(app_release_url)
        variant_download_url = details["download_link"]

        print(f"[*] [{app_name}] Variant: {details['architecture']} / Android {details['android_version']}")

        print(f"[*] [{app_name}] Getting download page...")
        download_button_page = apkm.get_download_link(variant_download_url)

        print(f"[*] [{app_name}] Extracting direct link...")
        direct_link = apkm.get_direct_download_link(download_button_page)

        print(f"[*] [{app_name}] Downloading to {output_filename}...")

        headers = {
            "User-Agent": apkm.user_agent,
            "Referer": download_button_page,
        }

        response = apkm.scraper.get(direct_link, stream=True, headers=headers)

        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"[+] [{app_name}] Download complete: {output_filename}")
            update_version(version_file, remote_version)
            return True, remote_version
        else:
            print(f"[-] [{app_name}] Download failed with status: {response.status_code}")
            return False, None

    except Exception as e:
        print(f"[-] [{app_name}] Error during download process: {e}")
        return False, None

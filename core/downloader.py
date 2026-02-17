## File: core/downloader.py
"""
Generic APK downloader — config-driven.
Supports multiple sources (APKMirror, Aptoide).
"""

import os
import requests
from core.sources import APKMirrorSource, AptoideSource, GitHubSource
from core.utils import get_local_version


def download_app(app_config: dict, output_filename: str = "latest.apk") -> tuple:
    """
    Check configured source for updates and download if a newer version exists.

    Args:
        app_config: Parsed app.json dict.
        output_filename: Where to save the downloaded APK.

    Returns:
        (update_needed: bool, new_version: str | None)
    """
    package_name = app_config["package_name"]
    version_file = app_config["version_file"]
    app_name = app_config["name"]
    source_name = app_config.get("source", "apkmirror").lower()

    # 1. Initialize source
    if source_name == "aptoide":
        source = AptoideSource()
    elif source_name == "github":
        if "repo" not in app_config:
            print(f"[-] [{app_name}] 'repo' field is required for github source.")
            return False, None
        source = GitHubSource()
        package_name = app_config["repo"]  # For GitHub, we search by repo
    else:
        # Default to APKMirror
        source = APKMirrorSource()

    print(f"[*] [{app_name}] Using source: {source_name}")

    # 2. Get local version
    local_version = get_local_version(version_file)
    print(f"[*] [{app_name}] Local version: {local_version}")

    # 3. Check for updates
    try:
        remote_version, release_url, title = source.get_latest_version(package_name)
    except Exception as e:
        print(f"[-] [{app_name}] Search failed: {e}")
        return False, None

    if not remote_version:
        print(f"[-] [{app_name}] No results found on {source_name}.")
        return False, None

    print(f"[*] [{app_name}] Latest release: {title}")
    print(f"[*] [{app_name}] Remote version: {remote_version}")

    # 4. Compare versions
    if remote_version == local_version:
        print(f"[i] [{app_name}] Versions match. No update needed.")
        return False, None

    print(f"[!] [{app_name}] Update detected! ({local_version} -> {remote_version})")

    # 5. Resolve final download link
    try:
        direct_link = source.get_download_url(release_url)
        if not direct_link:
            print(f"[-] [{app_name}] Failed to resolve direct download link.")
            return False, None

        print(f"[*] [{app_name}] Downloading from {source_name} to {output_filename}...")

        # Common download logic
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        
        # Use scraper if available, else requests
        scraper = getattr(source, 'scraper', requests)
        
        response = scraper.get(direct_link, stream=True, headers=headers)

        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"[+] [{app_name}] Download complete: {output_filename}")
            # Note: Version is updated by the orchestrator (run.py or CI) only on success
            return True, remote_version
        else:
            print(f"[-] [{app_name}] Download failed with status: {response.status_code}")
            if response.status_code == 403:
                print(f"[-] [{app_name}] Access Forbidden. This could be due to IP blocking or scraper detection.")
            return False, None

    except Exception as e:
        print(f"[-] [{app_name}] Error during download process: {e}")
        return False, None
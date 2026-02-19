"""
Generic APK downloader, config-driven.
Supports multiple sources and normalizes the final artifact to APK.
"""

import os
import re
import shutil
import subprocess
import sys
import zipfile
from urllib.parse import urlparse

import requests

from core.sources import create_source
from core.utils import get_local_version


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
}


def _extract_filename_from_response(response: requests.Response) -> str | None:
    content_disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r"filename\*?=['\"]?(?:UTF-8'')?([^'\";\n]+)", content_disposition)
    if match:
        return os.path.basename(match.group(1).strip())

    parsed = urlparse(response.url)
    filename = os.path.basename(parsed.path or "").strip()
    return filename or None


def _detect_extension(response: requests.Response, filename: str | None) -> str:
    if filename:
        lower = filename.lower()
        if lower.endswith(".xapk"):
            return ".xapk"
        if lower.endswith(".apk"):
            return ".apk"

    content_type = (response.headers.get("Content-Type") or "").lower()
    if "application/vnd.android.package-archive" in content_type:
        return ".apk"
    if "application/octet-stream" in content_type:
        # Could be either; keep apk as default.
        return ".apk"
    return ".bin"


def _is_valid_apk(path: str) -> bool:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False

    try:
        with zipfile.ZipFile(path, "r") as apk_zip:
            return "AndroidManifest.xml" in apk_zip.namelist()
    except zipfile.BadZipFile:
        return False


def _is_xapk(path: str) -> bool:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False

    try:
        with zipfile.ZipFile(path, "r") as package_zip:
            names = set(package_zip.namelist())
            has_manifest = "manifest.json" in names
            has_any_apk = any(name.lower().endswith(".apk") for name in names)
            return has_manifest and has_any_apk
    except zipfile.BadZipFile:
        return False


def _convert_xapk_to_apk(xapk_path: str) -> str:
    converter_script = os.path.join("core", "xapktoapk.py")
    command = [sys.executable, converter_script, xapk_path]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()
        details = stderr or stdout or str(e)
        raise RuntimeError(f"XAPK conversion failed: {details}") from e

    converted_apk = os.path.splitext(xapk_path)[0] + ".apk"
    if not os.path.exists(converted_apk):
        raise RuntimeError(f"XAPK conversion did not produce APK: {converted_apk}")

    return converted_apk


def _normalize_downloaded_file(download_path: str, output_filename: str):
    output_dir = os.path.dirname(output_filename)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if _is_valid_apk(download_path):
        shutil.move(download_path, output_filename)
        return

    if _is_xapk(download_path):
        converted_apk = _convert_xapk_to_apk(os.path.abspath(download_path))
        shutil.move(converted_apk, output_filename)
        if os.path.exists(download_path):
            os.remove(download_path)
        return

    raise RuntimeError("Downloaded file is neither a valid APK nor a convertible XAPK.")


def download_app(app_config: dict, output_filename: str = "latest.apk") -> tuple:
    """
    Check configured source for updates and download if a newer version exists.

    Args:
        app_config: Parsed app.json dict.
        output_filename: Where to save the downloaded APK.

    Returns:
        (update_needed: bool, new_version: str | None)
    """
    version_file = app_config["version_file"]
    app_name = app_config["name"]
    source_name = app_config.get("source", "apkmirror")

    # 1. Initialize source from registry.
    try:
        source_name, source, lookup_value = create_source(source_name, app_config)
    except Exception as e:
        print(f"[-] [{app_name}] Source configuration error: {e}")
        return False, None

    print(f"[*] [{app_name}] Using source: {source_name}")

    # 2. Get local version.
    local_version = get_local_version(version_file)
    print(f"[*] [{app_name}] Local version: {local_version}")

    # 3. Check for updates.
    try:
        remote_version, release_url, title = source.get_latest_version(lookup_value)
    except Exception as e:
        print(f"[-] [{app_name}] Search failed: {e}")
        return False, None

    if not remote_version:
        print(f"[-] [{app_name}] No results found on {source_name}.")
        return False, None

    print(f"[*] [{app_name}] Latest release: {title}")
    print(f"[*] [{app_name}] Remote version: {remote_version}")

    # 4. Compare versions.
    if remote_version == local_version:
        print(f"[i] [{app_name}] Versions match. No update needed.")
        return False, None

    print(f"[!] [{app_name}] Update detected! ({local_version} -> {remote_version})")

    # 5. Resolve final download link and download package.
    try:
        direct_link = source.get_download_url(release_url)
        if not direct_link:
            print(f"[-] [{app_name}] Failed to resolve direct download link.")
            return False, None

        print(f"[*] [{app_name}] Downloading from {source_name} to {output_filename}...")
        headers = getattr(source, "headers", DEFAULT_HEADERS)
        downloader = getattr(source, "scraper", requests)
        response = downloader.get(direct_link, stream=True, headers=headers, allow_redirects=True)
        try:
            if response.status_code != 200:
                print(f"[-] [{app_name}] Download failed with status: {response.status_code}")
                if response.status_code == 403:
                    print(
                        f"[-] [{app_name}] Access Forbidden. This could be due to "
                        "IP blocking or scraper detection."
                    )
                return False, None

            content_type = (response.headers.get("Content-Type") or "").lower()
            if content_type.startswith("text/html"):
                print(f"[-] [{app_name}] Received HTML page instead of package binary.")
                return False, None

            response_filename = _extract_filename_from_response(response)
            extension = _detect_extension(response, response_filename)
            temp_download = f"{output_filename}.download{extension}"

            with open(temp_download, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        finally:
            response.close()

        _normalize_downloaded_file(temp_download, output_filename)
        if not _is_valid_apk(output_filename):
            print(f"[-] [{app_name}] Final output is not a valid APK: {output_filename}")
            return False, None

        print(f"[+] [{app_name}] Download complete: {output_filename}")
        # Note: Version is updated by the orchestrator (run.py or CI) only on success.
        return True, remote_version

    except Exception as e:
        print(f"[-] [{app_name}] Error during download process: {e}")
        return False, None

import sys
import os
import re
import cloudscraper
from apkmirror import APKMirror

# Configuration
PACKAGE_NAME = "com.bnhp.payments.paymentsapp"
VERSION_FILE = "version.txt"
OUTPUT_FILENAME = "latest.apk"

def get_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    return "0.0.0"

def extract_version_from_title(title):
    # Regex to find version numbers (e.g., "6.1", "10.0.0", "1.2.3-release")
    match = re.search(r"(\d+(?:\.\d+)+)", title)
    return match.group(1) if match else "0.0.0"

def set_github_output(key, value):
    # Writes to GITHUB_OUTPUT environment variable if it exists
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"[Output] {key}={value}")

def main():
    apkm = APKMirror(timeout=10, results=5)
    
    print(f"[*] Initializing APKMirror check for: {PACKAGE_NAME}")
    
    # 1. Get Local Version
    local_version = get_local_version()
    print(f"[*] Local Version: {local_version}")

    # 2. Search APKMirror
    print("[*] Searching APKMirror...")
    try:
        results = apkm.search(PACKAGE_NAME)
    except Exception as e:
        print(f"[-] Search failed: {e}")
        sys.exit(1)

    if not results:
        print("[-] No results found on APKMirror.")
        sys.exit(1)

    # 3. Analyze Latest Result
    # APKMirror search usually returns the latest release first
    latest_result = results[0]
    app_title = latest_result['name']
    remote_version = extract_version_from_title(app_title)
    
    print(f"[*] Found latest release: {app_title}")
    print(f"[*] Detected Remote Version: {remote_version}")

    # 4. Compare Versions
    if remote_version == local_version:
        print("[i] Versions match. No update needed.")
        set_github_output("update_needed", "false")
        sys.exit(0)

    print(f"[!] Update detected! ({local_version} -> {remote_version})")
    
    # 5. Start Download Flow
    app_release_url = latest_result["link"]
    
    try:
        print("[*] Getting variant details...")
        details = apkm.get_app_details(app_release_url)
        variant_download_url = details["download_link"]
        
        print(f"[*] Variant: {details['architecture']} / Android {details['android_version']}")

        print("[*] Getting download page...")
        download_button_page = apkm.get_download_link(variant_download_url)

        print("[*] Extracting direct link...")
        direct_link = apkm.get_direct_download_link(download_button_page)
        
        print(f"[*] Downloading to {OUTPUT_FILENAME}...")
        
        # Headers are critical for APKMirror
        headers = {
            "User-Agent": apkm.user_agent,
            "Referer": download_button_page
        }

        # Reuse the scraper session
        response = apkm.scraper.get(direct_link, stream=True, headers=headers)
        
        if response.status_code == 200:
            with open(OUTPUT_FILENAME, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"[+] Download complete: {OUTPUT_FILENAME}")
            
            # Update local version file
            with open(VERSION_FILE, "w") as f:
                f.write(remote_version)
            
            set_github_output("update_needed", "true")
            set_github_output("new_version", remote_version)
        else:
            print(f"[-] Download failed with status: {response.status_code}")
            sys.exit(1)

    except Exception as e:
        print(f"[-] Error during download process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
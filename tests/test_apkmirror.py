import sys
import os

# Add the project root to sys.path to allow importing core
sys.path.append(os.getcwd())

from core.downloader import download_app

def test_apkmirror_metadata():
    # Mock config for an app on APKMirror
    app_config = {
        "id": "bit",
        "name": "Bit",
        "package_name": "com.bnhp.payments.paymentsapp",
        "source": "apkmirror",
        "version_file": "tests/bit_version.txt"
    }
    
    # Ensure version file doesn't exist to force search
    if os.path.exists("tests/bit_version.txt"):
        os.remove("tests/bit_version.txt")

    print("Testing APKMirror search...")
    # We won't actually download to save time/bandwidth, just check metadata fetch
    # Wait, download_app does both. I'll just check if it finds a version.
    
    from core.sources.apkmirror import APKMirrorSource
    source = APKMirrorSource()
    version, link, title = source.get_latest_version(app_config["package_name"])
    
    if version and link:
        print(f"[SUCCESS] Found version on APKMirror: {version}")
        print(f"[SUCCESS] Link: {link}")
    else:
        print("[FAILURE] Could not fetch metadata from APKMirror.")
        sys.exit(1)

if __name__ == "__main__":
    test_apkmirror_metadata()

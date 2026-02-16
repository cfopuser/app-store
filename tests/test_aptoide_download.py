import sys
import os

# Add the project root to sys.path to allow importing core
sys.path.append(os.getcwd())

from core.downloader import download_app

def test_aptoide_download():
    # Mock config for a test app
    app_config = {
        "id": "waze_test",
        "name": "Waze Test",
        "package_name": "com.waze",
        "source": "aptoide",
        "version_file": "tests/waze_version.txt"
    }
    
    # Ensure version file doesn't exist to force download
    if os.path.exists("tests/waze_version.txt"):
        os.remove("tests/waze_version.txt")
        
    output_apk = "tests/waze_test.apk"
    if os.path.exists(output_apk):
        os.remove(output_apk)

    print("Testing Aptoide download...")
    update_needed, new_version = download_app(app_config, output_filename=output_apk)
    
    if update_needed and os.path.exists(output_apk):
        size = os.path.getsize(output_apk)
        print(f"[SUCCESS] Downloaded version {new_version}, size: {size} bytes")
        # Cleanup
        os.remove(output_apk)
        os.remove("tests/waze_version.txt")
    else:
        print("[FAILURE] Download failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_aptoide_download()

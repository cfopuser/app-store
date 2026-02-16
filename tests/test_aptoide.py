import sys
import os

# Add the project root to sys.path to allow importing core
sys.path.append(os.getcwd())

from core.sources.aptoide import AptoideSource

def test_aptoide_metadata():
    source = AptoideSource()
    package_name = "com.waze"  # Use Waze as a test app
    
    print(f"Testing Aptoide metadata for {package_name}...")
    version, download_url, title = source.get_latest_version(package_name)
    
    if version and download_url:
        print(f"[SUCCESS] Found version: {version}")
        print(f"[SUCCESS] Download URL: {download_url}")
        print(f"[SUCCESS] Title: {title}")
    else:
        print("[FAILURE] Could not fetch metadata from Aptoide.")
        sys.exit(1)

if __name__ == "__main__":
    test_aptoide_metadata()

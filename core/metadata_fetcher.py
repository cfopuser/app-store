import os
import json
import requests
from core.utils import discover_apps, load_app_config
from core.sources.aurora import AuroraSource

def download_image(url, save_path):
    """Download an image from a URL to a local path."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  [-] Failed to download image {url}: {e}")
        return False

def fetch_metadata(app_id_filter=None, force=False):
    """Fetch and update metadata for all registered apps (or a specific one)."""
    app_ids = [app_id_filter] if app_id_filter else discover_apps()
    
    try:
        source_en = AuroraSource(locale="en_US")
        source_he = AuroraSource(locale="iw_IL")
    except Exception as e:
        print(f"[-] Could not initialize AuroraSource: {e}")
        return

    for app_id in app_ids:
        print(f"[*] Checking metadata for: {app_id}")
        try:
            config = load_app_config(app_id)
            package_name = config.get("package_name")
            if not package_name:
                print(f"  [!] No package name for {app_id}, skipping.")
                continue

            # Check what's missing
            needs_text = not config.get("full_description") or not config.get("full_description_he")
            
            icon_path = f"apps/{app_id}/icon.png"
            needs_icon = not os.path.exists(icon_path)
            
            screenshot_dir_en = f"apps/{app_id}/screenshots"
            needs_screenshots_en = not os.path.exists(screenshot_dir_en) or not os.listdir(screenshot_dir_en)
            
            screenshot_dir_he = f"apps/{app_id}/screenshots_he"
            needs_screenshots_he = not os.path.exists(screenshot_dir_he) or not os.listdir(screenshot_dir_he)

            if not force and not (needs_text or needs_icon or needs_screenshots_en or needs_screenshots_he):
                print(f"  [i] All metadata and assets exist. Use --force to update.")
                continue

            print(f"  [*] Fetching fresh metadata...")
            details_en = source_en._get_details(package_name)
            details_he = source_he._get_details(package_name)
            
            # Update text fields if missing or force
            if force or not config.get("full_description"):
                config["full_description"] = details_en.get("descriptionHtml", config.get("full_description", ""))
            
            if force or not config.get("full_description_he"):
                config["full_description_he"] = details_he.get("descriptionHtml", config.get("full_description_he", ""))
            
            if force or not config.get("name_play"):
                config["name_play"] = details_en.get("title", config.get("name_play", config.get("name")))

            app_details_en = details_en.get("details", {}).get("appDetails", {})
            if force or not config.get("category"):
                config["category"] = app_details_en.get("appCategory", ["Application"])[0]

            app_details_he = details_he.get("details", {}).get("appDetails", {})
            if force or not config.get("category_he"):
                config["category_he"] = app_details_he.get("appCategory", [config.get("category", "Application")])[0]

            # Handle Icon
            if force or needs_icon:
                images_en = details_en.get("image", [])
                icon_item = next((img for img in images_en if img.get("imageType") == 4), None)
                if icon_item:
                    icon_url = icon_item.get("imageUrl")
                    print(f"  [*] Downloading icon...")
                    if download_image(icon_url, icon_path):
                        config["icon_url"] = icon_path

            # Screenshots (English)
            if force or needs_screenshots_en:
                images_en = details_en.get("image", [])
                screenshot_items_en = [img for img in images_en if img.get("imageType") == 1]
                if screenshot_items_en:
                    print(f"  [*] Downloading {len(screenshot_items_en)} EN screenshots...")
                    os.makedirs(screenshot_dir_en, exist_ok=True)
                    # Clear only if forcing
                    if force and os.path.exists(screenshot_dir_en):
                        for f in os.listdir(screenshot_dir_en):
                            os.remove(os.path.join(screenshot_dir_en, f))
                    
                    local_screenshots_en = []
                    for i, item in enumerate(screenshot_items_en):
                        url = item.get("imageUrl")
                        local_path = f"{screenshot_dir_en}/screen_{i+1}.png"
                        if download_image(url, local_path):
                            local_screenshots_en.append(local_path)
                    config["screenshots"] = local_screenshots_en

            # Screenshots (Hebrew)
            if force or needs_screenshots_he:
                images_he = details_he.get("image", [])
                screenshot_items_he = [img for img in images_he if img.get("imageType") == 1]
                if screenshot_items_he:
                    print(f"  [*] Downloading {len(screenshot_items_he)} HE screenshots...")
                    os.makedirs(screenshot_dir_he, exist_ok=True)
                    # Clear only if forcing
                    if force and os.path.exists(screenshot_dir_he):
                        for f in os.listdir(screenshot_dir_he):
                            os.remove(os.path.join(screenshot_dir_he, f))
                    
                    local_screenshots_he = []
                    for i, item in enumerate(screenshot_items_he):
                        url = item.get("imageUrl")
                        local_path = f"{screenshot_dir_he}/screen_{i+1}.png"
                        if download_image(url, local_path):
                            local_screenshots_he.append(local_path)
                    config["screenshots_he"] = local_screenshots_he

            # Save updated config
            from core.utils import save_app_config
            save_app_config(app_id, config)
            
            print(f"  [+] Updated {app_id} metadata.")

        except Exception as e:
            print(f"  [-] Error processing {app_id}: {e}")

if __name__ == "__main__":
    import sys
    app_id = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_metadata(app_id)

if __name__ == "__main__":
    import sys
    app_id = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_metadata(app_id)

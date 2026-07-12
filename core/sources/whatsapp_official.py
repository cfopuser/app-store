import re
import cloudscraper
from bs4 import BeautifulSoup

class WhatsAppOfficialSource:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "https://www.whatsapp.com/android"
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

    def get_latest_version(self, package_name: str):
        print(f"[*] [WhatsApp Official] Fetching latest APK from {self.base_url}")

        try:
            response = self.scraper.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            
            # --- LOG: Save HTML to file for debugging ---
            with open("whatsapp_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("[*] [WhatsApp Official] Saved HTML to whatsapp_page.html")
            
            # --- LOG: Print first 500 characters of HTML ---
            print("[*] [WhatsApp Official] HTML preview (first 500 chars):")
            print(html[:500])
            
            soup = BeautifulSoup(html, 'html.parser')

            # --- 1. Find the direct APK download link ---
            apk_link = None
            
            # Method 1: Search all <a> tags
            all_links = soup.find_all('a', href=True)
            print(f"[*] [WhatsApp Official] Found {len(all_links)} links")
            for i, link in enumerate(all_links):
                href = link.get('href', '')
                if 'scontent.whatsapp.net' in href and href.endswith('.apk'):
                    apk_link = href
                    print(f"[+] [WhatsApp Official] Found APK link in <a> tag #{i}: {href[:100]}...")
                    break

            # Method 2: Search in raw HTML (fallback)
            if not apk_link:
                print("[*] [WhatsApp Official] No link in <a> tags, searching raw HTML...")
                pattern = r'https://scontent\.whatsapp\.net/[^\s"\'<>]+\.apk[^\s"\'<>]*'
                matches = re.findall(pattern, html)
                print(f"[*] [WhatsApp Official] Found {len(matches)} raw matches")
                for i, match in enumerate(matches):
                    print(f"    Match #{i}: {match[:100]}...")
                if matches:
                    apk_link = matches[0]
                    print(f"[+] [WhatsApp Official] Using first raw match: {apk_link[:100]}...")

            # Method 3: Search for any .apk link (not just scontent)
            if not apk_link:
                print("[*] [WhatsApp Official] No scontent link found, searching for any .apk link...")
                pattern = r'https?://[^\s"\'<>]+\.apk[^\s"\'<>]*'
                matches = re.findall(pattern, html)
                print(f"[*] [WhatsApp Official] Found {len(matches)} .apk links")
                for i, match in enumerate(matches):
                    print(f"    Match #{i}: {match[:100]}...")
                if matches:
                    apk_link = matches[0]
                    print(f"[+] [WhatsApp Official] Using first .apk match: {apk_link[:100]}...")

            if not apk_link:
                print("[-] [WhatsApp Official] Could not find APK download link.")
                return None, None, None

            print(f"[+] [WhatsApp Official] Final APK link: {apk_link[:100]}...")

            # --- 2. Extract version number ---
            version = None

            version_patterns = [
                r'גרסה\s+([\d.]+)',
                r'Version\s+([\d.]+)',
                r'version["\']?\s*[:=]\s*["\']?([\d.]+)',
                r'v([\d.]+)',
            ]
            for pattern in version_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    print(f"[*] [WhatsApp Official] Found version via pattern '{pattern}': {version}")
                    break

            if not version:
                print("[*] [WhatsApp Official] No version in HTML, trying URL...")
                filename_match = re.search(r'/([^/]+)\.apk', apk_link)
                if filename_match:
                    filename = filename_match.group(1)
                    print(f"[*] [WhatsApp Official] Filename: {filename}")
                    ver_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
                    if ver_match:
                        version = ver_match.group(1)
                        print(f"[*] [WhatsApp Official] Found version in filename: {version}")
                    else:
                        ver_match = re.search(r'(\d+\.\d+\.\d+)', filename)
                        if ver_match:
                            version = ver_match.group(1)
                            print(f"[*] [WhatsApp Official] Found version in filename: {version}")

            if not version:
                from datetime import datetime
                version = datetime.utcnow().strftime("%Y.%m.%d")
                print(f"[!] [WhatsApp Official] Could not determine version, using date: {version}")

            title = "WhatsApp Messenger"
            print(f"[+] [WhatsApp Official] Version: {version}")

            return version, apk_link, title

        except Exception as e:
            print(f"[-] [WhatsApp Official] Error fetching metadata: {e}")
            return None, None, None

    def get_download_url(self, initial_url: str):
        return initial_url

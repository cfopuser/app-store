import re
import gzip
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
            'Accept-Encoding': 'gzip, deflate',  # הורדנו את br
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def _decode_response(self, response):
        """מפענח את התוכן אם הוא דחוס."""
        content_encoding = response.headers.get('Content-Encoding', '').lower()
        raw_content = response.content
        
        if 'gzip' in content_encoding:
            try:
                return gzip.decompress(raw_content).decode('utf-8')
            except Exception as e:
                print(f"[!] [WhatsApp Official] Failed to decode gzip: {e}")
                return raw_content.decode('utf-8', errors='ignore')
        else:
            return raw_content.decode('utf-8', errors='ignore')

    def get_latest_version(self, package_name: str):
        print(f"[*] [WhatsApp Official] Fetching latest APK from {self.base_url}")

        try:
            response = self.scraper.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            
            # פענוח ידני
            html = self._decode_response(response)
            
            # שמירה לקובץ לבדיקה
            with open("whatsapp_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("[*] [WhatsApp Official] Saved decoded HTML to whatsapp_page.html")
            
            # תצוגה מקדימה
            print("[*] [WhatsApp Official] HTML preview (first 500 chars):")
            print(html[:500])
            
            soup = BeautifulSoup(html, 'html.parser')

            # --- 1. חיפוש קישור ---
            apk_link = None
            
            # חיפוש בכל הקישורים
            all_links = soup.find_all('a', href=True)
            print(f"[*] [WhatsApp Official] Found {len(all_links)} links")
            
            for link in all_links:
                href = link.get('href', '')
                if 'scontent.whatsapp.net' in href and '.apk' in href:
                    apk_link = href
                    print(f"[+] [WhatsApp Official] Found APK link: {href[:100]}...")
                    break

            # חיפוש גולמי ב-HTML
            if not apk_link:
                print("[*] [WhatsApp Official] Searching raw HTML for APK links...")
                pattern = r'https?://[^\s"\'<>]+\.apk[^\s"\'<>]*'
                matches = re.findall(pattern, html)
                print(f"[*] [WhatsApp Official] Found {len(matches)} raw matches")
                if matches:
                    apk_link = matches[0]
                    print(f"[+] [WhatsApp Official] Using raw match: {apk_link[:100]}...")

            if not apk_link:
                print("[-] [WhatsApp Official] Could not find APK download link.")
                return None, None, None

            # --- 2. חילוץ גרסה ---
            version = None
            patterns = [
                r'גרסה\s+([\d.]+)',
                r'Version\s+([\d.]+)',
                r'version["\']?\s*[:=]\s*["\']?([\d.]+)',
                r'v([\d.]+)',
            ]
            for pat in patterns:
                match = re.search(pat, html, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    print(f"[*] [WhatsApp Official] Found version via '{pat}': {version}")
                    break

            if not version:
                # נסיון מחלץ משם הקובץ
                filename_match = re.search(r'/([^/]+)\.apk', apk_link)
                if filename_match:
                    filename = filename_match.group(1)
                    ver_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename) or re.search(r'(\d+\.\d+\.\d+)', filename)
                    if ver_match:
                        version = ver_match.group(1)
                        print(f"[*] [WhatsApp Official] Found version in filename: {version}")

            if not version:
                from datetime import datetime
                version = datetime.utcnow().strftime("%Y.%m.%d")
                print(f"[!] [WhatsApp Official] Using date as version: {version}")

            title = "WhatsApp Messenger"
            print(f"[+] [WhatsApp Official] Final version: {version}")
            return version, apk_link, title

        except Exception as e:
            print(f"[-] [WhatsApp Official] Error: {e}")
            return None, None, None

    def get_download_url(self, initial_url: str):
        return initial_url

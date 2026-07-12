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
        """
        Fetch the latest WhatsApp APK directly from whatsapp.com.
        
        Returns:
            (version, download_link, title)
        """
        print(f"[*] [WhatsApp Official] Fetching latest APK from {self.base_url}")

        try:
            response = self.scraper.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            # --- 1. Find the direct APK download link ---
            # Look for links that point to scontent.whatsapp.net with .apk
            apk_link = None
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                if 'scontent.whatsapp.net' in href and href.endswith('.apk'):
                    apk_link = href
                    break

            # Fallback: search in the raw HTML (in case it's in a script or meta tag)
            if not apk_link:
                pattern = r'https://scontent\.whatsapp\.net/[^\s"\'<>]+\.apk[^\s"\'<>]*'
                match = re.search(pattern, html)
                if match:
                    apk_link = match.group(0)

            if not apk_link:
                print("[-] [WhatsApp Official] Could not find APK download link.")
                return None, None, None

            print(f"[+] [WhatsApp Official] Found APK link: {apk_link[:100]}...")

            # --- 2. Extract version number ---
            version = None

            # Try to find version in the HTML (common pattern: "Version X.Y.Z" or "vX.Y.Z")
            version_patterns = [
                r'Version\s+([\d.]+)',
                r'version["\']?\s*[:=]\s*["\']?([\d.]+)',
                r'v([\d.]+)',
            ]
            for pattern in version_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    break

            # If still no version, try to extract from the APK filename or URL
            if not version:
                # Example: .../10000000_2445548149293237_4579588530844501720_n.apk
                # Sometimes the version is in the filename
                filename_match = re.search(r'/([^/]+)\.apk', apk_link)
                if filename_match:
                    filename = filename_match.group(1)
                    # Look for version-like pattern in filename
                    ver_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
                    if ver_match:
                        version = ver_match.group(1)
                    else:
                        # Try to find a simpler version pattern (e.g., 2.26.27)
                        ver_match = re.search(r'(\d+\.\d+\.\d+)', filename)
                        if ver_match:
                            version = ver_match.group(1)

            # Final fallback: use the current date as version (not ideal, but better than nothing)
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
        """The initial URL is already the direct download link."""
        return initial_url

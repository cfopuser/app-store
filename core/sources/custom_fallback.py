# core/sources/custom_fallback.py

import os
import re
import time
import base64
from bs4 import BeautifulSoup
import cloudscraper

class CustomFallbackSource:
    def __init__(self, uptodown_subdomain=None, timeout=30):
        self.uptodown_subdomain = uptodown_subdomain
        self.timeout = timeout
        
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.scraper.headers.update({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def _get_best_apkpure_variant(self, package_name):
        api_url = "https://api.pureapk.com/m/v3/cms/app_version"
        headers = {
            'x-sv': '29',
            'x-abis': 'arm64-v8a,armeabi-v7a,armeabi',
            'x-gp': '1',
            # כותרת אנדרואיד קריטית כדי שה-API יחשוף את גרסאות ה-XAPK הגדולות
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }
        params = {
            'hl': 'en-US',
            'package_name': package_name
        }
        try:
            print(f"[*] [Custom Fallback] Querying APKPure API for {package_name} variants...")
            r = self.scraper.get(api_url, params=params, headers=headers, timeout=self.timeout)
            r.raise_for_status()
            
            strings = re.findall(rb'[ -~]{8,}', r.content)
            valid_urls = []
            for s in strings:
                if s.startswith(b'http'):
                    s_upper = s.upper()
                    if b'/APK' in s_upper or b'/XAPK' in s_upper:
                        url = s.decode('utf-8')
                        if url not in valid_urls:
                            valid_urls.append(url)
            
            if not valid_urls:
                print("[-] No valid URLs found in API response.")
                return None, None
                
            print(f"[*] Found {len(valid_urls)} variant(s). Checking file sizes via Stream Headers...")
            
            best_url = valid_urls[0]
            max_size = 0
            best_version = None
            
            # בדיקה של 5 הוריאציות הראשונות
            for url in valid_urls[:5]:
                try:
                    # 1. פענוח Base64 מהקישור כדי לחלץ את מספר הגרסה האמיתי
                    url_b64 = url.split('/')[-1].split('?')[0]
                    padded = url_b64 + '=' * (-len(url_b64) % 4)
                    decoded_info = base64.b64decode(padded).decode('utf-8', errors='ignore')
                    
                    ver_match = re.search(r"(\d+(?:\.\d+){1,})", decoded_info)
                    extracted_ver = ver_match.group(1) if ver_match else "Unknown"
                    
                    # 2. קריאת גודל הקובץ בעזרת GET + stream=True במקום HEAD שעושה בעיות
                    with self.scraper.get(url, stream=True, allow_redirects=True, timeout=5) as res:
                        size = int(res.headers.get("Content-Length", 0))
                        mb_size = size // 1024 // 1024
                        print(f"    - Found variant: {mb_size} MB | Version: {extracted_ver}")
                        
                        if size > max_size:
                            max_size = size
                            best_url = url
                            best_version = extracted_ver if extracted_ver != "Unknown" else None

                except Exception as e:
                    pass
                    
            print(f"[+] Selected largest variant: {max_size // 1024 // 1024} MB (Version: {best_version})")
            return best_url, best_version
        except Exception as e:
            print(f"[-] APKPure API check failed: {e}")
            return None, None

    def get_latest_version(self, package_name):
        print(f"[*] [Custom Fallback] Checking latest version for {package_name}...")
        
        # 1. APKPure
        try:
            best_url, version = self._get_best_apkpure_variant(package_name)
            if best_url:
                if not version:
                    version = "latest"
                return version, f"apkpure_mobile:{best_url}", package_name
        except Exception as e:
            print(f"[-] APKPure variant check failed: {e}")

        # 2. Aptoide
        try:
            from core.sources.aptoide import AptoideSource
            aptoide = AptoideSource(timeout=self.timeout)
            version, download_url, title = aptoide.get_latest_version(package_name)
            if version:
                return version, f"aptoide:{download_url}", title
        except Exception as e:
            pass

        # 3. Uptodown
        if self.uptodown_subdomain:
            try:
                version, download_url, title = self._scrape_uptodown_meta(self.uptodown_subdomain)
                if version:
                    return version, f"uptodown:{download_url}", title
            except Exception as e:
                pass

        return "latest", f"fallback:{package_name}", package_name

    def get_download_url(self, initial_url):
        if initial_url.startswith("apkpure_mobile:"):
            return initial_url.split("apkpure_mobile:", 1)[1]
        if initial_url.startswith("aptoide:"):
            return initial_url.split("aptoide:", 1)[1]
        if initial_url.startswith("uptodown:"):
            return initial_url.split("uptodown:", 1)[1]

        package_name = initial_url.split("fallback:", 1)[1] if "fallback:" in initial_url else initial_url
        best_url, _ = self._get_best_apkpure_variant(package_name)
        if best_url: return best_url
        
        return None

    def _scrape_uptodown_meta(self, subdomain):
        base_url = subdomain if subdomain.startswith("http") else f"https://{subdomain}.en.uptodown.com/android"
        download_page = f"{base_url.rstrip('/')}/download"
        
        r = self.scraper.get(download_page, timeout=self.timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        version_div = soup.select_one('div.version')
        version = version_div.get_text(strip=True) if version_div else None
        
        name_el = soup.select_one('#detail-app-name')
        file_id = name_el.get('data-file-id') if name_el else None
        
        if not file_id: return None, None, None

        pre_download_url = f"{download_page.rstrip('/')}/{file_id}-x"
        self.scraper.headers.update({'Referer': download_page})
        r2 = self.scraper.get(pre_download_url, timeout=self.timeout)
        r2.raise_for_status()
        
        soup2 = BeautifulSoup(r2.text, "html.parser")
        download_button = soup2.select_one('#detail-download-button')
        final_token = download_button.get('data-url') if download_button else None
        
        if not final_token: return None, None, None

        final_token = final_token.strip('/')
        download_url = f"https://dw.uptodown.com/dwn/{final_token}/app.apk"
        return version, download_url, subdomain

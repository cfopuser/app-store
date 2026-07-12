# core/sources/custom_fallback.py

import os
import re
import time
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

    def _get_uptodown_pure_apk(self, package_name):
        """
        עדיפות 1: משיכת APK טהור מ-Uptodown.
        מסנן אקטיבית קבצי XAPK ומחפש וריאציית APK אם נדרש.
        """
        try:
            print(f"[*] [Custom Fallback] Querying Uptodown for pure Standalone APK...")
            app_url = None
            
            # 1. חיפוש האפליקציה (או שימוש בסאב-דומיין אם קיים)
            if self.uptodown_subdomain:
                app_url = f"https://{self.uptodown_subdomain}.en.uptodown.com/android"
            else:
                search_url = f"https://en.uptodown.com/android/search?query={package_name}"
                r_search = self.scraper.get(search_url, timeout=self.timeout)
                soup_search = BeautifulSoup(r_search.text, 'html.parser')
                first_item = soup_search.select_one('.item .name a')
                if first_item:
                    app_url = first_item.get('href')

            if not app_url:
                print("[-] Uptodown: App not found.")
                return None, None

            # 2. כניסה לעמוד ההורדה
            download_page = f"{app_url.rstrip('/')}/download"
            r_dl = self.scraper.get(download_page, timeout=self.timeout)
            soup_dl = BeautifulSoup(r_dl.text, 'html.parser')

            version_div = soup_dl.select_one('div.version')
            version_name = version_div.get_text(strip=True) if version_div else "latest"

            name_el = soup_dl.select_one('#detail-app-name')
            if not name_el:
                return None, None

            default_file_id = name_el.get('data-file-id')
            format_el = soup_dl.select_one('span.format')
            file_format = format_el.get_text(strip=True).upper() if format_el else "APK"

            target_file_id = None
            
            # 3. סינון XAPK מול APK
            if "APK" in file_format and "XAPK" not in file_format:
                target_file_id = default_file_id
            else:
                print("[-] Uptodown: Default file is XAPK. Searching for pure APK variants...")
                variants_btn = soup_dl.select_one('button.variants')
                if variants_btn:
                    data_version = variants_btn.get('data-version')
                    # שליפת ה-ID המיוחד (data-code) מתוך העמוד
                    data_code_match = re.search(r'data-code="(\d+)"', r_dl.text)
                    if data_code_match and data_version:
                        data_code = data_code_match.group(1)
                        domain = app_url.split('//')[1].split('/')[0]
                        variants_url = f"https://{domain}/app/{data_code}/version/{data_version}/files"
                        
                        r_var = self.scraper.get(variants_url, timeout=self.timeout)
                        if r_var.status_code == 200:
                            var_json = r_var.json()
                            var_soup = BeautifulSoup(var_json.get('content', ''), 'html.parser')
                            for variant in var_soup.select('div.variant'):
                                v_format_el = variant.select_one('div.v-file span')
                                v_format = v_format_el.get_text(strip=True).upper() if v_format_el else ""
                                if "APK" in v_format and "XAPK" not in v_format:
                                    report_el = variant.select_one('.v-report')
                                    if report_el:
                                        target_file_id = report_el.get('data-file-id')
                                        print(f"    - Found pure APK variant on Uptodown (ID: {target_file_id})")
                                        break
                                        
            if not target_file_id:
                print("[-] Could not find a pure APK variant on Uptodown.")
                return None, None

            # 4. חילוץ טוקן ההורדה הסופי
            pre_download_url = f"{download_page.rstrip('/')}/{target_file_id}-x"
            self.scraper.headers.update({'Referer': download_page})
            r_pre = self.scraper.get(pre_download_url, timeout=self.timeout)
            soup_pre = BeautifulSoup(r_pre.text, 'html.parser')
            
            download_button = soup_pre.select_one('#detail-download-button')
            final_token = download_button.get('data-url') if download_button else None
            
            if not final_token:
                return None, None
                
            final_token = final_token.strip('/')
            download_url = f"https://dw.uptodown.com/dwn/{final_token}/app.apk"
            
            print(f"[+] Found pure APK from Uptodown! Version: {version_name}")
            return download_url, version_name
            
        except Exception as e:
            print(f"[-] Uptodown check failed: {e}")
            return None, None

    def _get_aptoide_apk(self, package_name):
        """
        עדיפות 2: משיכת APK דרך Aptoide (תמיד מספק APK נקי).
        """
        try:
            print(f"[*] [Custom Fallback] Querying Aptoide API for pure Standalone APK...")
            search_url = f"https://ws75.aptoide.com/api/7/listSearchApps?query={package_name}"
            res = self.scraper.get(search_url, timeout=self.timeout).json()
            
            app_id = None
            for app in res.get('datalist', {}).get('list', []):
                if app.get('package') == package_name:
                    app_id = app.get('id')
                    break
            
            if not app_id:
                return None, None
                
            info_url = f"https://ws75.aptoide.com/api/7/getApp?app_id={app_id}"
            info_res = self.scraper.get(info_url, timeout=self.timeout).json()
            
            meta = info_res.get('nodes', {}).get('meta', {}).get('data', {})
            file_info = meta.get('file', {})
            download_url = file_info.get('path')
            version_name = file_info.get('vername')
            
            if download_url and download_url.endswith('.apk'):
                print(f"[+] Found pure APK from Aptoide! Version: {version_name}")
                return download_url, version_name
                
            return None, None
        except Exception as e:
            print(f"[-] Aptoide API check failed: {e}")
            return None, None

    def _get_apkpure_pure_apk(self, package_name):
        """
        עדיפות 3: APKPure API - סינון קשוח שזורק כל XAPK.
        """
        api_url = "https://api.pureapk.com/m/v3/cms/app_version"
        headers = {
            'x-sv': '29',
            'x-abis': 'arm64-v8a,armeabi-v7a,armeabi',
            'x-gp': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }
        params = {
            'hl': 'en-US',
            'package_name': package_name
        }
        try:
            print(f"[*] [Custom Fallback] Querying APKPure API for pure APK variants...")
            r = self.scraper.get(api_url, params=params, headers=headers, timeout=self.timeout)
            r.raise_for_status()
            
            strings = re.findall(rb'[ -~]{8,}', r.content)
            valid_urls = []
            for s in strings:
                if s.startswith(b'http'):
                    s_upper = s.upper()
                    if b'/APK/' in s_upper and b'XAPK' not in s_upper:
                        url = s.decode('utf-8')
                        if url not in valid_urls:
                            valid_urls.append(url)
            
            if not valid_urls:
                print("[-] No pure APK valid URLs found in APKPure API response.")
                return None
                
            best_url = valid_urls[0]
            max_size = 0
            
            for url in valid_urls[:5]:
                try:
                    with self.scraper.get(url, stream=True, allow_redirects=True, timeout=5) as res:
                        size = int(res.headers.get("Content-Length", 0))
                        mb_size = size // 1024 // 1024
                        print(f"    - Found pure APK variant: {mb_size} MB")
                        if size > max_size:
                            max_size = size
                            best_url = url
                except Exception as e:
                    pass
                    
            print(f"[+] Selected largest pure APK variant: {max_size // 1024 // 1024} MB")
            return best_url
        except Exception as e:
            print(f"[-] APKPure API check failed: {e}")
            return None

    def get_latest_version(self, package_name):
        print(f"[*] [Custom Fallback] Resolving accurate version and pure APK download link for {package_name}...")
        
        real_version = "latest"
        
        # 0. שאיבת מספר הגרסה הרשמי
        try:
            from core.sources.apkpure_mobile import APKPureMobileSource
            pure = APKPureMobileSource(timeout=self.timeout)
            v, _, _ = pure.get_latest_version(package_name)
            if v and v != "latest":
                real_version = v
                print(f"[+] Successfully resolved version name: {real_version}")
        except Exception as e:
            pass

        # 1. עדיפות ראשונה: Uptodown
        uptodown_url, uptodown_ver = self._get_uptodown_pure_apk(package_name)
        if uptodown_url:
            if real_version == "latest" and uptodown_ver:
                real_version = uptodown_ver
            return real_version, f"uptodown_direct:{uptodown_url}", package_name

        # 2. עדיפות שניה: Aptoide
        aptoide_url, aptoide_ver = self._get_aptoide_apk(package_name)
        if aptoide_url:
            if real_version == "latest" and aptoide_ver:
                real_version = aptoide_ver
            return real_version, f"aptoide_direct:{aptoide_url}", package_name
            
        # 3. עדיפות שלישית (גיבוי אחרון): APKPure מסונן XAPK
        pure_apk_url = self._get_apkpure_pure_apk(package_name)
        if pure_apk_url:
            return real_version, f"apkpure_direct:{pure_apk_url}", package_name

        return real_version, f"fallback:{package_name}", package_name

    def get_download_url(self, initial_url):
        if initial_url.startswith("uptodown_direct:"):
            return initial_url.split("uptodown_direct:", 1)[1]
        if initial_url.startswith("aptoide_direct:"):
            return initial_url.split("aptoide_direct:", 1)[1]
        if initial_url.startswith("apkpure_direct:"):
            return initial_url.split("apkpure_direct:", 1)[1]

        package_name = initial_url.split("fallback:", 1)[1] if "fallback:" in initial_url else initial_url
        
        # שיחזור לוגיקת העדיפויות במקרה של ניתוב מחדש
        uptodown_url, _ = self._get_uptodown_pure_apk(package_name)
        if uptodown_url: return uptodown_url
        
        aptoide_url, _ = self._get_aptoide_apk(package_name)
        if aptoide_url: return aptoide_url
        
        pure_apk_url = self._get_apkpure_pure_apk(package_name)
        if pure_apk_url: return pure_apk_url
        
        return None

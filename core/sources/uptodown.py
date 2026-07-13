# core/sources/uptodown_source.py

import re
from bs4 import BeautifulSoup
import cloudscraper

class UptodownSource:
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
        משיכת APK טהור מ-Uptodown.
        מסנן אקטיבית קבצי XAPK ומחפש וריאציית APK אם נדרש.
        """
        try:
            print(f"[*] [Uptodown Source] Querying Uptodown for pure Standalone APK...")
            app_url = None
            
            # 1. חיפוש האפליקציה (או שימוש בסאב-דומיין אם קיים)
            if self.uptodown_subdomain:
                app_url = f"https://{self.uptodown_subdomain}.en.uptodown.com/android"
            else:
                # תוקן: כתובת החיפוש שהייתה שבורה בקוד המקורי
                search_url = f"https://en.uptodown.com/android/search?q={package_name}"
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

    def get_latest_version(self, package_name):
        print(f"[*] [Uptodown Source] Resolving version and pure APK link for {package_name}...")
        
        url, version = self._get_uptodown_pure_apk(package_name)
        
        if url:
            return version, f"uptodown_direct:{url}", package_name
            
        return "latest", f"fallback:{package_name}", package_name

    def get_download_url(self, initial_url):
        # במקרה והלינק כבר הומר בהצלחה
        if initial_url.startswith("uptodown_direct:"):
            return initial_url.split("uptodown_direct:", 1)[1]

        # במקרה של ניתוב מחדש / כשל בבדיקה הראשונית
        package_name = initial_url.split("fallback:", 1)[1] if "fallback:" in initial_url else initial_url
        
        url, _ = self._get_uptodown_pure_apk(package_name)
        return url

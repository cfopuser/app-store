# core/sources/uptodown_source_debug.py

import re
import json
from bs4 import BeautifulSoup
import cloudscraper

class UptodownSourceDebug:
    def __init__(self, uptodown_subdomain=None, timeout=30, debug=True):
        self.uptodown_subdomain = uptodown_subdomain
        self.timeout = timeout
        self.debug = debug  # שליטה על הדפסות

        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        self.scraper.headers.update({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def _log(self, *args, **kwargs):
        if self.debug:
            print("[DEBUG]", *args, **kwargs)

    def _save_html(self, soup, filename):
        """שומר את ה-HTML לקובץ לניתוח ידני"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        self._log(f"Saved HTML to {filename}")

    def _extract_real_version(self, soup, url=""):
        """
        מנסה לחלץ גרסה מכל המקומות האפשריים.
        מחזירה tuple: (version, source_description)
        """
        candidates = []
        sources = []

        # 1. meta name="version"
        meta_ver = soup.find('meta', {'name': 'version'})
        if meta_ver and meta_ver.get('content'):
            val = meta_ver.get('content').strip()
            candidates.append(val)
            sources.append(f"meta name='version' -> {val}")

        # 2. meta property="og:version"
        meta_og = soup.find('meta', {'property': 'og:version'})
        if meta_og and meta_og.get('content'):
            val = meta_og.get('content').strip()
            candidates.append(val)
            sources.append(f"meta property='og:version' -> {val}")

        # 3. meta itemscope version (לעיתים)
        meta_item = soup.find('meta', {'itemprop': 'version'})
        if meta_item and meta_item.get('content'):
            val = meta_item.get('content').strip()
            candidates.append(val)
            sources.append(f"meta itemprop='version' -> {val}")

        # 4. תגית span עם class="version" (יכול להיות "Version 7.34" או "2.26.27.72")
        ver_span = soup.select_one('span.version, div.version')
        if ver_span:
            val = ver_span.get_text(strip=True)
            # מנקה "Version" או "v" אם קיימים
            val = re.sub(r'^[Vv]ersion\s*', '', val).strip()
            candidates.append(val)
            sources.append(f"span.version / div.version -> {val}")

        # 5. חיפוש כללי בטקסט – כל המספרים עם 3-4 חלקים
        text = soup.get_text()
        pattern = r'\b(\d+\.\d+\.\d+(?:\.\d+)?)\b'
        matches = re.findall(pattern, text)
        if matches:
            # נבחר את הארוך ביותר (סביר להניח 4 חלקים)
            best = max(matches, key=lambda x: len(x))
            candidates.append(best)
            sources.append(f"regex general -> {best} (found {len(matches)} candidates)")

        # 6. ניסיון לשלוף מכתובת הורדה אם קיימת (data-url)
        download_btn = soup.select_one('#detail-download-button')
        if download_btn and download_btn.get('data-url'):
            # לפעמים ה-data-url מכיל רמז לגרסה? לא סביר אבל נבדוק
            pass

        # 7. ניסיון מתוך תגית h1 או title
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # מחפש גרסה בכותרת
            match = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)?)', title_text)
            if match:
                val = match.group(1)
                candidates.append(val)
                sources.append(f"title tag -> {val}")

        # הדפסת כל המועמדים
        self._log("=== VERSION CANDIDATES ===")
        for i, (cand, src) in enumerate(zip(candidates, sources), 1):
            self._log(f"  {i}. {cand}  (source: {src})")

        # בחירת המועמד המועדף: אם יש גרסה עם 4 חלקים, נבחר אותה; אחרת הארוך ביותר
        best_version = "latest"
        best_source = "none"
        # סינון גרסאות שנראות כמו מספרים (לא טקסט)
        numeric_candidates = [c for c in candidates if re.match(r'^\d+\.\d+\.\d+(?:\.\d+)?$', c)]
        if numeric_candidates:
            # מעדיפים 4 חלקים (x.x.x.x) על פני 3 חלקים
            four_part = [c for c in numeric_candidates if len(c.split('.')) == 4]
            if four_part:
                best_version = four_part[0]
                best_source = "four-part numeric"
            else:
                # בוחרים את הארוך ביותר
                best_version = max(numeric_candidates, key=lambda x: len(x))
                best_source = "numeric (max length)"
        else:
            # אם אין מספרים, משאירים "latest"
            self._log("No numeric version found, using 'latest'")

        self._log(f"Selected version: {best_version} (source: {best_source})")
        return best_version, best_source

    def _get_uptodown_pure_apk(self, package_name):
        self._log(f"Starting _get_uptodown_pure_apk for {package_name}")

        try:
            app_url = None

            # 1. חיפוש
            if self.uptodown_subdomain:
                app_url = f"https://{self.uptodown_subdomain}.en.uptodown.com/android"
                self._log(f"Using subdomain: {app_url}")
            else:
                search_url = f"https://en.uptodown.com/android/search?q={package_name}"
                self._log(f"Search URL: {search_url}")
                r_search = self.scraper.get(search_url, timeout=self.timeout)
                self._log(f"Search response status: {r_search.status_code}")
                soup_search = BeautifulSoup(r_search.text, 'html.parser')

                # שמירת HTML של תוצאות החיפוש
                self._save_html(soup_search, f"search_{package_name}.html")

                first_item = soup_search.select_one('.item .name a')
                if first_item:
                    app_url = first_item.get('href')
                    self._log(f"Found app URL: {app_url}")
                else:
                    self._log("No .item .name a found in search results")

            if not app_url:
                self._log("App URL is None, returning None")
                return None, None

            # 2. כניסה לעמוד ההורדה
            download_page = f"{app_url.rstrip('/')}/download"
            self._log(f"Download page: {download_page}")
            r_dl = self.scraper.get(download_page, timeout=self.timeout)
            self._log(f"Download page status: {r_dl.status_code}")
            soup_dl = BeautifulSoup(r_dl.text, 'html.parser')

            # שמירת HTML של דף ההורדה
            self._save_html(soup_dl, f"download_{package_name}.html")

            # חילוץ גרסה משופר
            version_name, version_source = self._extract_real_version(soup_dl, download_page)
            self._log(f"Extracted version: {version_name} (from {version_source})")

            # 3. שליפת מזהה קובץ
            name_el = soup_dl.select_one('#detail-app-name')
            if not name_el:
                self._log("No #detail-app-name element found")
                return None, None
            default_file_id = name_el.get('data-file-id')
            self._log(f"Default file ID: {default_file_id}")

            format_el = soup_dl.select_one('span.format')
            file_format = format_el.get_text(strip=True).upper() if format_el else "APK"
            self._log(f"File format from span.format: {file_format}")

            target_file_id = None

            # 4. סינון XAPK
            if "APK" in file_format and "XAPK" not in file_format:
                target_file_id = default_file_id
                self._log("Default file is pure APK, using default ID")
            else:
                self._log("Default file is XAPK or unknown, searching for pure APK variants...")
                variants_btn = soup_dl.select_one('button.variants')
                if variants_btn:
                    data_version = variants_btn.get('data-version')
                    self._log(f"Variants button found, data-version: {data_version}")

                    data_code_match = re.search(r'data-code="(\d+)"', r_dl.text)
                    if data_code_match and data_version:
                        data_code = data_code_match.group(1)
                        domain = app_url.split('//')[1].split('/')[0]
                        variants_url = f"https://{domain}/app/{data_code}/version/{data_version}/files"
                        self._log(f"Variants URL: {variants_url}")

                        r_var = self.scraper.get(variants_url, timeout=self.timeout)
                        self._log(f"Variants response status: {r_var.status_code}")
                        if r_var.status_code == 200:
                            var_json = r_var.json()
                            # שמירת ה-JSON לניתוח
                            with open(f"variants_{package_name}.json", 'w') as f:
                                json.dump(var_json, f, indent=2)
                            self._log("Saved variants JSON")

                            var_soup = BeautifulSoup(var_json.get('content', ''), 'html.parser')
                            # הדפסת כל הווריאנטים שנמצאו
                            variants = var_soup.select('div.variant')
                            self._log(f"Found {len(variants)} variants in JSON")
                            for idx, variant in enumerate(variants, 1):
                                v_format_el = variant.select_one('div.v-file span')
                                v_format = v_format_el.get_text(strip=True).upper() if v_format_el else "UNKNOWN"
                                report_el = variant.select_one('.v-report')
                                file_id = report_el.get('data-file-id') if report_el else None
                                self._log(f"  Variant #{idx}: format={v_format}, file_id={file_id}")
                                if "APK" in v_format and "XAPK" not in v_format:
                                    if report_el:
                                        target_file_id = report_el.get('data-file-id')
                                        self._log(f"  -> Selected pure APK variant with ID {target_file_id}")
                                        break
                        else:
                            self._log("Failed to get variants JSON")
                    else:
                        self._log("Missing data-code or data-version in page")
                else:
                    self._log("No variants button found")

            if not target_file_id:
                self._log("No pure APK variant found, returning None")
                return None, None

            # 5. חילוץ טוקן הורדה
            pre_download_url = f"{download_page.rstrip('/')}/{target_file_id}-x"
            self._log(f"Pre-download URL: {pre_download_url}")
            self.scraper.headers.update({'Referer': download_page})
            r_pre = self.scraper.get(pre_download_url, timeout=self.timeout)
            self._log(f"Pre-download status: {r_pre.status_code}")
            soup_pre = BeautifulSoup(r_pre.text, 'html.parser')

            # שמירת HTML של דף הטרום-הורדה
            self._save_html(soup_pre, f"predownload_{package_name}.html")

            download_button = soup_pre.select_one('#detail-download-button')
            if download_button:
                final_token = download_button.get('data-url')
                self._log(f"Download button data-url: {final_token}")
            else:
                self._log("No #detail-download-button found")
                final_token = None

            if not final_token:
                self._log("No final token, returning None")
                return None, None

            final_token = final_token.strip('/')
            download_url = f"https://dw.uptodown.com/dwn/{final_token}/app.apk"
            self._log(f"Final download URL: {download_url}")

            self._log(f"Success! Version: {version_name}, URL: {download_url}")
            return download_url, version_name

        except Exception as e:
            self._log(f"Exception in _get_uptodown_pure_apk: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def get_latest_version(self, package_name):
        self._log(f"get_latest_version called for {package_name}")
        url, version = self._get_uptodown_pure_apk(package_name)
        if url:
            self._log(f"Returning version={version}, url={url}")
            return version, f"uptodown_direct:{url}", package_name
        self._log("No URL, returning fallback")
        return "latest", f"fallback:{package_name}", package_name

    def get_download_url(self, initial_url):
        self._log(f"get_download_url called with {initial_url}")
        if initial_url.startswith("uptodown_direct:"):
            return initial_url.split("uptodown_direct:", 1)[1]
        package_name = initial_url.split("fallback:", 1)[1] if "fallback:" in initial_url else initial_url
        url, _ = self._get_uptodown_pure_apk(package_name)
        return url

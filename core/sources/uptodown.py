import re
import json
from bs4 import BeautifulSoup
import cloudscraper

class UptodownSource:
    def __init__(self, uptodown_subdomain=None, timeout=30, debug=True):
        self.uptodown_subdomain = uptodown_subdomain
        self.timeout = timeout
        self.debug = debug

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

    # ---------- Version extraction ----------
    def _extract_version_from_title(self, soup):
        title = soup.find('title')
        if title:
            # תומך ב-2 חלקים ומעלה, ללא הגבלה. למשל 1.2 או 1.2.3.4.5
            match = re.search(r'(\d+(?:\.\d+)+)', title.get_text())
            if match:
                return match.group(1)
        return None

    def _extract_version_from_ld_json(self, soup):
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    ver = None
                    if 'mainEntity' in data and isinstance(data['mainEntity'], dict):
                        ver = data['mainEntity'].get('softwareVersion')
                    else:
                        ver = data.get('softwareVersion')
                    if ver and ver.strip():
                        return ver.strip()
                except:
                    continue
        return None

    def _extract_version_from_div(self, soup):
        # מחפש קלאסים אופייניים לגרסה ב-Uptodown
        version_el = soup.select_one('.version, .detail-version')
        if version_el:
            match = re.search(r'(\d+(?:\.\d+)+)', version_el.get_text())
            if match:
                return match.group(1)
        return None

    def _extract_version_from_url(self, url):
        match = re.search(r'(\d+(?:\.\d+)+)', url)
        return match.group(1) if match else None

    def _extract_version_from_headers(self, url):
        try:
            head = self.scraper.head(url, allow_redirects=True, timeout=10)
            cd = head.headers.get('Content-Disposition', '')
            match = re.search(r'filename="?([^"]+)"?', cd)
            if match:
                filename = match.group(1)
                return self._extract_version_from_url(filename)
        except:
            pass
        return None

    def _get_real_version(self, soup, download_url):
        # סדר חילוץ מבוסס אמינות:

        # 1. JSON-LD (הכי אמין, מידע מובנה ומדויק מהאתר)
        ver = self._extract_version_from_ld_json(soup)
        if ver:
            self._log(f"Version from LD+JSON: {ver}")
            return ver

        # 2. אלמנט ייעודי לגרסה באתר (div/span שמיועד לזה)
        ver = self._extract_version_from_div(soup)
        if ver:
            self._log(f"Version from HTML element: {ver}")
            return ver

        # 3. כותרת העמוד (Title) - לרוב מכיל את שם האפליקציה והגרסה
        ver = self._extract_version_from_title(soup)
        if ver:
            self._log(f"Version from title: {ver}")
            return ver

        # 4. מתוך ה-Headers של ההורדה (שם הקובץ האמיתי בשרת)
        if download_url:
            ver = self._extract_version_from_headers(download_url)
            if ver:
                self._log(f"Version from Content-Disposition: {ver}")
                return ver

        # 5. רשת ביטחון אחרונה: סריקת כל הטקסט בעמוד
        self._log("Searching raw text for version (fallback)...")
        text = soup.get_text()
        
        # חיפוש דינאמי: תופס מספר, ואחריו בין 1 ל-5 פעמים "נקודה ומספר" 
        # (מכסה גרסאות מ-1.0 ועד 1.2.3.4.5.6)
        all_versions = re.findall(r'\b(\d+(?:\.\d+){1,5})\b', text)
        
        if all_versions:
            # סינון גרסאות "זבל" - נעדיף גרסאות שיש בהן לפחות 2 נקודות (3 חלקים ומעלה)
            valid_versions = [v for v in all_versions if v.count('.') >= 2]
            
            # אם אין גרסאות ארוכות, נתפשר על מה שיש (למשל גרסאות של שני חלקים כמו 4.5)
            if not valid_versions:
                valid_versions = all_versions
                
            # בחירת הגרסה הגבוהה ביותר מבין התוצאות
            best = max(valid_versions, key=lambda v: tuple(map(int, v.split('.'))))
            self._log(f"Version from text fallback: {best}")
            return best

        self._log("No version found, using 'latest'")
        return "latest"

    # ---------- Download logic ----------
    def _get_uptodown_pure_apk(self, package_name):
        self._log(f"Querying Uptodown for {package_name}...")
        try:
            app_url = None

            if self.uptodown_subdomain:
                app_url = f"https://{self.uptodown_subdomain}.en.uptodown.com/android"
            else:
                search_url = f"https://en.uptodown.com/android/search?q={package_name}"
                self._log(f"Search URL: {search_url}")
                r_search = self.scraper.get(search_url, timeout=self.timeout)
                
                # 1. בדיקה אם Uptodown ביצע הפניה אוטומטית ישירות לדף האפליקציה
                if r_search.url != search_url and re.match(r'https://[a-z0-9-]+\.en\.uptodown\.com/android/?$', r_search.url):
                    self._log("Search auto-redirected directly to the app page.")
                    app_url = r_search.url.rstrip('/')
                else:
                    soup_search = BeautifulSoup(r_search.text, 'html.parser')

                    # 2. איסוף מועמדים ייחודיים בלבד כדי למנוע כפילויות
                    candidates = []
                    for link in soup_search.find_all('a', href=True):
                        href = link.get('href', '').rstrip('/')
                        if re.match(r'https://[a-z0-9-]+\.en\.uptodown\.com/android$', href):
                            if 'uptodown-android' not in href and href not in candidates:
                                candidates.append(href)

                    self._log(f"Found {len(candidates)} app candidate(s)")
                    if candidates:
                        # 3. אופטימיזציה: מיון המועמדים כדי למזער קריאות רשת
                        # נבדוק קודם קישורים שה-URL שלהם מכיל את המילה העיקרית של החבילה (למשל 'whatsapp')
                        pkg_keyword = package_name.lower().split('.')[-1]
                        candidates = sorted(candidates, key=lambda c: 0 if pkg_keyword in c else 1)
                        
                        for cand_url in candidates:
                            self._log(f"Verifying candidate: {cand_url}")
                            try:
                                cand_r = self.scraper.get(cand_url, timeout=self.timeout)
                                # 4. אימות מדויק: מוודאים ששם החבילה (לדוגמה com.whatsapp) קיים ב-HTML של המועמד
                                # שימוש ב- boundaries (\b) מונע זיהוי שגוי של חבילות עם שם דומה 
                                if re.search(r'\b' + re.escape(package_name) + r'\b', cand_r.text):
                                    app_url = cand_url
                                    break
                            except Exception as e:
                                self._log(f"Error checking candidate {cand_url}: {e}")
                                
                        if not app_url:
                            self._log("Warning: Could not strictly verify package name. Falling back to first candidate.")
                            app_url = candidates[0]

                        self._log(f"Selected app URL: {app_url}")
                    else:
                        self._log("No app link found.")
                        return None, None

            if not app_url:
                self._log("App not found.")
                return None, None

            download_page = f"{app_url}/download"
            self._log(f"Download page: {download_page}")
            r_dl = self.scraper.get(download_page, timeout=self.timeout)
            soup_dl = BeautifulSoup(r_dl.text, 'html.parser')

            # --- מכאן והלאה שאר הקוד נשאר ללא שינוי ---
            # שליפת מזהה קובץ
            name_el = soup_dl.select_one('#detail-app-name')
            if not name_el:
                return None, None
            default_file_id = name_el.get('data-file-id')

            format_el = soup_dl.select_one('span.format')
            file_format = format_el.get_text(strip=True).upper() if format_el else "APK"

            target_file_id = None
            if "APK" in file_format and "XAPK" not in file_format:
                target_file_id = default_file_id
            else:
                self._log("Default is XAPK, searching variants...")
                variants_btn = soup_dl.select_one('button.variants')
                if variants_btn:
                    data_version = variants_btn.get('data-version')
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
                                        break

            if not target_file_id:
                self._log("No pure APK variant found.")
                return None, None

            # חילוץ טוקן
            pre_download_url = f"{download_page}/{target_file_id}-x"
            self.scraper.headers.update({'Referer': download_page})
            r_pre = self.scraper.get(pre_download_url, timeout=self.timeout)
            soup_pre = BeautifulSoup(r_pre.text, 'html.parser')

            download_button = soup_pre.select_one('#detail-download-button')
            final_token = download_button.get('data-url') if download_button else None
            if not final_token:
                return None, None
            final_token = final_token.strip('/')
            download_url = f"https://dw.uptodown.com/dwn/{final_token}/app.apk"

            # חילוץ גרסה
            version_name = self._get_real_version(soup_dl, download_url)

            self._log(f"Final version: {version_name}")
            self._log(f"Final URL: {download_url}")
            return download_url, version_name

        except Exception as e:
            self._log(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    # ---------- Public interface ----------
    def get_latest_version(self, package_name):
        self._log(f"get_latest_version({package_name})")
        url, version = self._get_uptodown_pure_apk(package_name)
        if url:
            return version, f"uptodown_direct:{url}", package_name
        return "latest", f"fallback:{package_name}", package_name

    def get_download_url(self, initial_url):
        self._log(f"get_download_url({initial_url})")
        if initial_url.startswith("uptodown_direct:"):
            return initial_url.split("uptodown_direct:", 1)[1]
        package_name = initial_url.split("fallback:", 1)[1] if "fallback:" in initial_url else initial_url
        url, _ = self._get_uptodown_pure_apk(package_name)
        return url

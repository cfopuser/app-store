# core/sources/uptodown.py

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

    # ---------- חילוץ גרסה ----------
    def _extract_version_from_title(self, soup):
        title = soup.find('title')
        if title:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', title.get_text())
            if match:
                return match.group(1)
        return None

    def _extract_version_from_ld_json(self, soup):
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    if 'mainEntity' in data and isinstance(data['mainEntity'], dict):
                        ver = data['mainEntity'].get('softwareVersion')
                    else:
                        ver = data.get('softwareVersion')
                    if ver and re.match(r'^\d+\.\d+\.\d+\.\d+$', ver):
                        return ver
                except:
                    continue
        return None

    def _extract_version_from_div(self, soup):
        div_ver = soup.select_one('div.version')
        if div_ver:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', div_ver.get_text())
            if match:
                return match.group(1)
        return None

    def _extract_version_from_url(self, url):
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', url)
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
        # 1. title
        ver = self._extract_version_from_title(soup)
        if ver:
            self._log(f"Version from title: {ver}")
            return ver

        # 2. JSON-LD
        ver = self._extract_version_from_ld_json(soup)
        if ver:
            self._log(f"Version from LD+JSON: {ver}")
            return ver

        # 3. טקסט
        text = soup.get_text()
        matches = re.findall(r'\b(\d+\.\d+\.\d+\.\d+)\b', text)
        if matches:
            ver = matches[0]
            self._log(f"Version from text: {ver}")
            return ver

        # 4. div.version
        ver = self._extract_version_from_div(soup)
        if ver:
            self._log(f"Version from div.version: {ver}")
            return ver

        # 5. HEAD
        if download_url:
            ver = self._extract_version_from_headers(download_url)
            if ver:
                self._log(f"Version from Content-Disposition: {ver}")
                return ver

        self._log("No version found, using 'latest'")
        return "latest"

    # ---------- הורדה ----------
    def _get_uptodown_pure_apk(self, package_name):
        self._log(f"Querying Uptodown for {package_name}...")
        try:
            app_url = None

            # ... inside _get_uptodown_pure_apk ...

            if self.uptodown_subdomain:
                app_url = f"https://{self.uptodown_subdomain}.en.uptodown.com/android"
            else:
                # FIX 1: use the real search URL
                search_url = f"https://en.uptodown.com/android/search?q={package_name}"
                self._log(f"Search URL: {search_url}")
                r_search = self.scraper.get(search_url, timeout=self.timeout)
                soup_search = BeautifulSoup(r_search.text, 'html.parser')

                all_links = soup_search.find_all('a', href=True)
                self._log(f"Found {len(all_links)} links in search results")
                for link in all_links[:15]:
                    self._log(f"  link: {link.get('href')} - text: {link.get_text(strip=True)[:50]}")

                # FIX 2: better candidate extraction – look for absolute uptodown subdomain URLs
                candidates = []
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    # Match absolute URLs like https://appname.en.uptodown.com/android
                    if href and 'en.uptodown.com/android' in href and 'search' not in href:
                        candidates.append((href, text))

                self._log(f"Found {len(candidates)} candidate links")
                for href, text in candidates:
                    self._log(f"  candidate: {href} - text: {text}")

                if candidates:
                    # Match by package_name or keyword as before
                    for href, text in candidates:
                        if package_name in href or package_name in text:
                            app_url = href
                            self._log(f"Selected link (package match): {app_url}")
                            break
                    if not app_url:
                        for href, text in candidates:
                            # fallback keyword match – adjust as needed
                            if 'whatsapp' in href.lower() or 'whatsapp' in text.lower():
                                app_url = href
                                self._log(f"Selected link (keyword match): {app_url}")
                                break
                    if not app_url and candidates:
                        app_url = candidates[0][0]
                        self._log(f"Selected link (first candidate): {app_url}")

                    if app_url and not app_url.startswith('http'):
                        app_url = 'https://' + app_url
                        self._log(f"Full app URL: {app_url}")

            # ... rest of the method
            if not app_url:
                self._log("App not found.")
                return None, None

            download_page = f"{app_url.rstrip('/')}/download"
            self._log(f"Download page: {download_page}")
            r_dl = self.scraper.get(download_page, timeout=self.timeout)
            soup_dl = BeautifulSoup(r_dl.text, 'html.parser')

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

    # ---------- ממשק ----------
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

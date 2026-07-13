# core/sources/uptodown.py

import re
import json
from bs4 import BeautifulSoup
import cloudscraper

class UptodownSource:
    def __init__(self, uptodown_subdomain=None, timeout=30, debug=True):
        self.uptodown_subdomain = uptodown_subdomain
        self.timeout = timeout
        self.debug = debug  # ניתן להפעיל/לכבות הדפסות

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
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        self._log(f"Saved HTML to {filename}")

    def _extract_real_version(self, soup):
        """
        מחזירה (version, source_description)
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

        # 3. meta itemprop="version"
        meta_item = soup.find('meta', {'itemprop': 'version'})
        if meta_item and meta_item.get('content'):
            val = meta_item.get('content').strip()
            candidates.append(val)
            sources.append(f"meta itemprop='version' -> {val}")

        # 4. span.version / div.version
        ver_span = soup.select_one('span.version, div.version')
        if ver_span:
            val = ver_span.get_text(strip=True)
            val = re.sub(r'^[Vv]ersion\s*', '', val).strip()
            candidates.append(val)
            sources.append(f"span/div.version -> {val}")

        # 5. regex כללי
        text = soup.get_text()
        pattern = r'\b(\d+\.\d+\.\d+(?:\.\d+)?)\b'
        matches = re.findall(pattern, text)
        if matches:
            best = max(matches, key=lambda x: len(x))
            candidates.append(best)
            sources.append(f"regex general -> {best}")

        # 6. כותרת (title)
        title = soup.find('title')
        if title:
            match = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)?)', title.get_text())
            if match:
                val = match.group(1)
                candidates.append(val)
                sources.append(f"title tag -> {val}")

        # 7. data-url של כפתור ההורדה (אם קיים)
        download_btn = soup.select_one('#detail-download-button')
        if download_btn and download_btn.get('data-url'):
            url = download_btn['data-url']
            match = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)?)', url)
            if match:
                val = match.group(1)
                candidates.append(val)
                sources.append(f"data-url -> {val}")

        self._log("=== VERSION CANDIDATES ===")
        for i, (cand, src) in enumerate(zip(candidates, sources), 1):
            self._log(f"  {i}. {cand}  (source: {src})")

        # בחירה: מעדיפים 4 חלקים
        numeric = [c for c in candidates if re.match(r'^\d+\.\d+\.\d+(?:\.\d+)?$', c)]
        if numeric:
            four_part = [c for c in numeric if len(c.split('.')) == 4]
            best = four_part[0] if four_part else max(numeric, key=lambda x: len(x))
            self._log(f"Selected version: {best}")
            return best, "numeric"
        self._log("No numeric version found, using 'latest'")
        return "latest", "none"

    def _get_uptodown_pure_apk(self, package_name):
        self._log(f"Querying Uptodown for {package_name}...")
        try:
            app_url = None
            if self.uptodown_subdomain:
                app_url = f"https://{self.uptodown_subdomain}.en.uptodown.com/android"
                self._log(f"Using subdomain: {app_url}")
            else:
                search_url = f"https://en.uptodown.com/android/search?q={package_name}"
                self._log(f"Search URL: {search_url}")
                r_search = self.scraper.get(search_url, timeout=self.timeout)
                soup_search = BeautifulSoup(r_search.text, 'html.parser')
                self._save_html(soup_search, f"search_{package_name}.html")
                first_item = soup_search.select_one('.item .name a')
                if first_item:
                    app_url = first_item.get('href')
                    self._log(f"Found app URL: {app_url}")

            if not app_url:
                self._log("App not found.")
                return None, None

            download_page = f"{app_url.rstrip('/')}/download"
            self._log(f"Download page: {download_page}")
            r_dl = self.scraper.get(download_page, timeout=self.timeout)
            soup_dl = BeautifulSoup(r_dl.text, 'html.parser')
            self._save_html(soup_dl, f"download_{package_name}.html")

            version_name, _ = self._extract_real_version(soup_dl)
            self._log(f"Extracted version: {version_name}")

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
                            with open(f"variants_{package_name}.json", 'w') as f:
                                json.dump(var_json, f, indent=2)
                            var_soup = BeautifulSoup(var_json.get('content', ''), 'html.parser')
                            for variant in var_soup.select('div.variant'):
                                v_format_el = variant.select_one('div.v-file span')
                                v_format = v_format_el.get_text(strip=True).upper() if v_format_el else ""
                                if "APK" in v_format and "XAPK" not in v_format:
                                    report_el = variant.select_one('.v-report')
                                    if report_el:
                                        target_file_id = report_el.get('data-file-id')
                                        self._log(f"Found pure APK variant ID: {target_file_id}")
                                        break

            if not target_file_id:
                self._log("No pure APK variant found.")
                return None, None

            pre_download_url = f"{download_page.rstrip('/')}/{target_file_id}-x"
            self.scraper.headers.update({'Referer': download_page})
            r_pre = self.scraper.get(pre_download_url, timeout=self.timeout)
            soup_pre = BeautifulSoup(r_pre.text, 'html.parser')
            self._save_html(soup_pre, f"predownload_{package_name}.html")

            download_button = soup_pre.select_one('#detail-download-button')
            final_token = download_button.get('data-url') if download_button else None
            if not final_token:
                return None, None
            final_token = final_token.strip('/')
            download_url = f"https://dw.uptodown.com/dwn/{final_token}/app.apk"
            self._log(f"Final URL: {download_url}")
            return download_url, version_name

        except Exception as e:
            self._log(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return None, None

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

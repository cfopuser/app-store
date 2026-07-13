def _get_uptodown_pure_apk(self, package_name):
    self._log(f"Querying Uptodown for {package_name}...")
    try:
        app_url = None
        if self.uptodown_subdomain:
            app_url = f"https://{self.uptodown_subdomain}.en.uptodown.com/android"
        else:
            search_url = f"https://en.uptodown.com/android/search?q={package_name}"
            r_search = self.scraper.get(search_url, timeout=self.timeout)
            soup_search = BeautifulSoup(r_search.text, 'html.parser')
            first_item = soup_search.select_one('.item .name a')
            if first_item:
                app_url = first_item.get('href')

        if not app_url:
            return None, None

        download_page = f"{app_url.rstrip('/')}/download"
        r_dl = self.scraper.get(download_page, timeout=self.timeout)
        soup_dl = BeautifulSoup(r_dl.text, 'html.parser')

        # 1. ניסיון ראשון: JSON-LD
        version_name = self._extract_version_from_ld_json(soup_dl)
        if not version_name:
            # 2. ניסיון שני: Title
            version_name = self._extract_version_from_title(soup_dl)
        if not version_name:
            # 3. ניסיון שלישי: div.version
            version_name = self._extract_version_from_div(soup_dl)

        # שאר הלוגיקה של שליפת file_id וכו'
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
            return None, None

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

        # 🚀 **חילוץ גרסה מה-URL הסופי (אם עדיין אין)**
        if not version_name or version_name == "latest":
            version_from_url = re.search(r'(\d+\.\d+\.\d+\.\d+)', download_url)
            if version_from_url:
                version_name = version_from_url.group(1)
                self._log(f"Extracted version from URL: {version_name}")

        # 🚀 **גיבוי: לשלוח HEAD request ולקבל את שם הקובץ**
        if not version_name or version_name == "latest":
            try:
                head = self.scraper.head(download_url, allow_redirects=True, timeout=10)
                content_disposition = head.headers.get('Content-Disposition', '')
                match = re.search(r'filename="?([^"]+)"?', content_disposition)
                if match:
                    filename = match.group(1)
                    version_from_filename = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
                    if version_from_filename:
                        version_name = version_from_filename.group(1)
                        self._log(f"Extracted version from filename: {version_name}")
            except Exception as e:
                self._log(f"HEAD request failed: {e}")

        self._log(f"Final version: {version_name}")
        self._log(f"Final URL: {download_url}")
        return download_url, version_name

    except Exception as e:
        self._log(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def _extract_version_from_ld_json(self, soup):
    """שולפת גרסה מתגית JSON-LD."""
    script_tag = soup.find('script', type='application/ld+json')
    if script_tag and script_tag.string:
        try:
            data = json.loads(script_tag.string)
            if 'mainEntity' in data and isinstance(data['mainEntity'], dict):
                return data['mainEntity'].get('softwareVersion')
            return data.get('softwareVersion')
        except:
            pass
    return None

def _extract_version_from_title(self, soup):
    """שולפת גרסה מה-title."""
    title = soup.find('title')
    if title:
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', title.get_text())
        if match:
            return match.group(1)
    return None

def _extract_version_from_div(self, soup):
    """שולפת גרסה מ-div.version."""
    div_ver = soup.select_one('div.version')
    if div_ver:
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', div_ver.get_text())
        if match:
            return match.group(1)
    return None

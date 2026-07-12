# core/sources/custom_fallback.py

import os
import re
import time
import base64
from urllib.parse import quote_plus, unquote
import requests
from bs4 import BeautifulSoup
import cloudscraper

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

class CustomFallbackSource:
    def __init__(self, uptodown_subdomain=None, timeout=30, retries=3):
        self.uptodown_subdomain = uptodown_subdomain
        self.timeout = timeout
        self.retries = retries
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update(DEFAULT_HEADERS)

    def _get_page(self, url):
        """GET request with 429 Rate Limit handling and backoff"""
        for i in range(self.retries):
            try:
                r = self.scraper.get(url, timeout=self.timeout, allow_redirects=True)
                if r.status_code == 429:
                    wait_time = int(r.headers.get("Retry-After", 15))
                    print(f"[-] [429 Rate Limit] Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                r.raise_for_status()
                return BeautifulSoup(r.text, "html.parser")
            except Exception as e:
                print(f"[-] Attempt {i+1} failed: {e}")
                time.sleep(3 * (i + 1))
        return None

    def get_latest_version(self, package_name):
        """
        Retrieves the latest version of the app.
        We reuse your existing unmodified APKMirrorSource to parse the version.
        """
        try:
            from core.sources.apkmirror import APKMirrorSource
            apkm = APKMirrorSource()
            version, _, title = apkm.get_latest_version(package_name)
            if version:
                return version, package_name, title
        except Exception as e:
            print(f"[-] [Custom Fallback] Temporary error using APKMirror for version check: {e}")
        
        # Fallback version string if APKMirror is completely down/blocked
        return "latest", package_name, package_name

    def get_download_url(self, package_name):
        """
        This is called by core/downloader.py to fetch the direct link.
        It runs the fallback scraping sequence.
        """
        print(f"[*] [Custom Fallback] Resolving download link for {package_name}...")

        # 1. Try APKMirror scraping (Dynamic score-based variant parser)
        try:
            url = self._scrape_apkmirror(package_name)
            if url:
                return url
        except Exception as e:
            print(f"[-] APKMirror scraping failed: {e}")

        # 2. Try Uptodown scraping (if subdomain is defined)
        if self.uptodown_subdomain:
            try:
                url = self._scrape_uptodown(self.uptodown_subdomain)
                if url:
                    return url
            except Exception as e:
                print(f"[-] Uptodown scraping failed: {e}")

        # 3. Try APKCombo scraping
        try:
            url = self._scrape_apkcombo(package_name)
            if url:
                return url
        except Exception as e:
            print(f"[-] APKCombo scraping failed: {e}")

        return None

    # ─── Scraper Methods ──────────────────────────────────────────────────────

    def _scrape_apkmirror(self, package_name):
        search_url = f"https://www.apkmirror.com/?post_type=app_release&searchtype=apk&s={quote_plus(package_name)}"
        soup = self._get_page(search_url)
        if not soup: return None

        app_rows = soup.find_all("div", {"class": "appRow"})
        if not app_rows: return None

        release_page = "https://www.apkmirror.com" + app_rows[0].find("a", {"class": "downloadLink"})["href"]
        soup2 = self._get_page(release_page)
        if not soup2: return None

        candidates = []
        for a in soup2.find_all("a", href=re.compile(r"/apk/.+/\d+/$")):
            parent_text = (a.find_parent() or a).get_text(" ", strip=True).upper()
            if "BUNDLE" in parent_text or "APKM" in parent_text:
                continue
            candidates.append((a["href"], parent_text.lower()))

        def score_variant(item):
            _, text = item
            if "nodpi" in text or "universal" in text:
                return 0
            if "arm64" in text:
                return 1
            return 2

        if not candidates: return None
        candidates.sort(key=score_variant)
        best_variant_url = "https://www.apkmirror.com" + candidates[0][0]
        
        soup3 = self._get_page(best_variant_url)
        if not soup3: return None
            
        btn = soup3.find("a", href=re.compile(r"download/\?key="))
        if not btn: return None
            
        interstitial_url = "https://www.apkmirror.com" + btn["href"]
        soup4 = self._get_page(interstitial_url)
        if not soup4: return None

        for a in soup4.find_all("a", href=True):
            if "cdn.apkmirror.com" in a["href"] or re.search(r"\.apk(\?|$)", a["href"]):
                return a["href"]
        return None

    def _scrape_uptodown(self, subdomain):
        base_url = subdomain if subdomain.startswith("http") else f"https://{subdomain}.en.uptodown.com/android"
        download_page = f"{base_url.rstrip('/')}/download"
        
        soup = self._get_page(download_page)
        if not soup: return None

        name_el = soup.select_one('#detail-app-name')
        file_id = name_el.get('data-file-id') if name_el else None
        if not file_id: return None

        pre_download_url = f"{download_page.rstrip('/')}/{file_id}-x"
        self.scraper.headers.update({'Referer': download_page})
        soup2 = self._get_page(pre_download_url)
        if not soup2: return None

        download_button = soup2.select_one('#detail-download-button')
        final_token = download_button.get('data-url') if download_button else None
        if not final_token: return None

        final_token = final_token.strip('/')
        return f"https://dw.uptodown.com/dwn/{final_token}/app.apk"

    def _scrape_apkcombo(self, package_name):
        url = f"https://apkcombo.com/app/{package_name}/download/apk"
        soup = self._get_page(url)
        if not soup: return None

        if not soup.select_one('a.variant'):
            html = str(soup)
            xid_match = re.search(r'var xid = "([^"]+)"', html)
            if xid_match:
                xid = xid_match.group(1)
                path_match = re.search(rf'fetchData\("([^"]+/{package_name}/)" \+ xid', html)
                if not path_match:
                    path_match = re.search(rf'"(/[^"]+/{package_name}/)"', html)
                
                if path_match:
                    path_segment = path_match.group(1).strip('"')
                    ajax_url = f"https://apkcombo.com{path_segment}{xid}/dl"
                    try:
                        post_res = self.scraper.post(ajax_url, data={'package_name': package_name, 'version': ''})
                        soup = BeautifulSoup(post_res.text, 'html.parser')
                    except:
                        return None

        variants = soup.select('a.variant')
        raw_link = ""
        if variants:
            raw_link = variants[0].get('href', '')
            
        if not raw_link:
            link_match = re.search(r'href="((?:/d\?u=|/r2\?u=|https?://[^"]+)\.apk[^"]*)"', str(soup))
            if link_match:
                raw_link = link_match.group(1)

        clean_link = raw_link
        if "u=" in raw_link:
            idx = raw_link.find("u=")
            if idx != -1:
                val = unquote(raw_link[idx + 2:])
                if val.startswith('http'):
                    clean_link = val
                else:
                    try:
                        padded_val = val + '=' * (-len(val) % 4)
                        decoded = base64.b64decode(padded_val).decode('utf-8', errors='ignore')
                        url_match = re.search(r'https?://[^\s|%|&]+', decoded)
                        if url_match:
                            clean_link = url_match.group(0)
                    except:
                        pass
        return clean_link

import re
import base64
from urllib.parse import unquote
import cloudscraper
from bs4 import BeautifulSoup

class APKComboSource:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36'
        })
        
    def get_latest_version(self, package_name: str):
        """
        Fetch metadata from APKCombo.
        
        Returns:
            (version, download_link, title)
        """
        print(f"[*] [APKCombo] Fetching metadata for: {package_name}")
        url = f"https://apkcombo.com/app/{package_name}/download/apk"
        
        try:
            response = self.scraper.get(url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            # Phase 1: Check if we need to do the XID POST
            if not soup.select_one('a.variant'):
                print("[*] [APKCombo] Direct links not found, looking for XID...")
                xid_match = re.search(r'var xid = "([^"]+)"', html)
                if xid_match:
                    xid = xid_match.group(1)
                    path_match = re.search(rf'fetchData\("([^"]+/{package_name}/)" \+ xid', html)
                    if not path_match:
                        path_match = re.search(rf'"(/[^"]+/{package_name}/)"', html)
                    
                    if path_match:
                        path_segment = path_match.group(1).strip('"')
                        ajax_url = f"https://apkcombo.com{path_segment}{xid}/dl"
                        print(f"[*] [APKCombo] Performing POST to {ajax_url}...")
                        
                        post_res = self.scraper.post(ajax_url, data={
                            'package_name': package_name,
                            'version': ''
                        }, timeout=self.timeout)
                        html = post_res.text

            return self._parse_html(html, package_name)
        except Exception as e:
            print(f"[-] [APKCombo] Error fetching metadata: {e}")
            return None, None, None

    def _parse_html(self, html: str, package_name: str):
        soup = BeautifulSoup(html, 'html.parser')
        
        title_el = soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            title_match = re.search(r'Download ([^-]+) APK', html)
            if title_match:
                title = title_match.group(1).strip()

        vername_el = soup.select_one('span.vername')
        version = vername_el.get_text(strip=True) if vername_el else ""
        if not version:
            version_match = re.search(r'<span[^>]*class="[^"]*vername[^"]*"[^>]*>([^<]+)</span>', html)
            if version_match:
                version = version_match.group(1).strip()

        variants = soup.select('a.variant')
        raw_link = ""
        target_variant = None
        
        if variants:
            for v in variants:
                vtype_el = v.select_one('.vtype')
                vtype_text = vtype_el.get_text(strip=True).upper() if vtype_el else ""
                if 'XAPK' in vtype_text or 'APKS' in vtype_text:
                    target_variant = v
                    break
            
            if not target_variant:
                target_variant = variants[0]
                
            raw_link = target_variant.get('href', '')
            
            if not version:
                vername_el = target_variant.select_one('.vername')
                if vername_el:
                    version = vername_el.get_text(strip=True)
        
        if not raw_link:
            link_match = re.search(r'href="((?:/d\?u=|/r2\?u=|https?://[^"]+)\.apk[^"]*)"', html)
            if not link_match:
                link_match = re.search(r'href="((?:/d\?u=|/r2\?u=)[^"]+)"', html)
            if link_match:
                raw_link = link_match.group(1)

        clean_link = raw_link
        if "u=" in raw_link and ("?u=" in raw_link or "&u=" in raw_link):
            idx = raw_link.find("u=")
            if idx != -1:
                val = unquote(raw_link[idx + 2:])
                if val.startswith('http'):
                    if "pureapk.com" in val:
                        clean_link = raw_link
                    else:
                        clean_link = val
                elif val.startswith('/'):
                    clean_link = f"https://apkcombo.com{val}"
                else:
                    try:
                        padded_val = val + '=' * (-len(val) % 4)
                        decoded = base64.b64decode(padded_val).decode('utf-8', errors='ignore')
                        if 'http' in decoded:
                            url_match = re.search(r'https?://[^\s|%|&]+', decoded)
                            if url_match:
                                decoded_url = url_match.group(0)
                                if "pureapk.com" in decoded_url:
                                    clean_link = raw_link
                                else:
                                    clean_link = decoded_url
                            else:
                                clean_link = raw_link
                        else:
                            clean_link = raw_link
                    except:
                        clean_link = raw_link
        
        if clean_link.startswith('/') and not clean_link.startswith('http'):
            clean_link = f"https://apkcombo.com{clean_link}"
            
        if not clean_link or not version:
            return None, None, None
            
        return version, clean_link, title or package_name

    def get_download_url(self, initial_url: str):
        """APKCombo initial URL is usually the direct link or redirector we parsed out"""
        return initial_url

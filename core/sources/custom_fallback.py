# core/sources/custom_fallback.py

import os
import re
import time
import requests
from bs4 import BeautifulSoup
import cloudscraper

class CustomFallbackSource:
    def __init__(self, uptodown_subdomain=None, timeout=30):
        self.uptodown_subdomain = uptodown_subdomain
        self.timeout = timeout
        self.scraper = cloudscraper.create_scraper()

    def get_latest_version(self, package_name):
        """
        שואב את מספר הגרסה דרך מקורות שאינם חסומים ב-Cloudflare:
        1. APKPure Mobile API (המקור הקיים שלכם)
        2. Aptoide API (המקור הקיים שלכם)
        3. Uptodown (במידה והוגדר תת-דומיין)
        """
        print(f"[*] [Custom Fallback] Checking latest version for {package_name}...")
        
        # 1. ניסיון דרך APKPure Mobile הקיים בריפו שלכם (ללא Cloudflare)
        try:
            from core.sources.apkpure_mobile import APKPureMobileSource
            pure = APKPureMobileSource(timeout=self.timeout)
            version, release_url, title = pure.get_latest_version(package_name)
            if version and version != "latest":
                print(f"[+] [Custom Fallback] Found version on APKPure Mobile: {version}")
                return version, f"apkpure_mobile:{release_url}", title
        except Exception as e:
            print(f"[-] APKPure Mobile version check failed: {e}")

        # 2. ניסיון דרך Aptoide הקיים בריפו שלכם (ללא Cloudflare)
        try:
            from core.sources.aptoide import AptoideSource
            aptoide = AptoideSource(timeout=self.timeout)
            version, download_url, title = aptoide.get_latest_version(package_name)
            if version:
                print(f"[+] [Custom Fallback] Found version on Aptoide: {version}")
                return version, f"aptoide:{download_url}", title
        except Exception as e:
            print(f"[-] Aptoide version check failed: {e}")

        # 3. ניסיון דרך Uptodown (ללא Cloudflare)
        if self.uptodown_subdomain:
            try:
                version, download_url, title = self._scrape_uptodown_meta(self.uptodown_subdomain)
                if version:
                    print(f"[+] [Custom Fallback] Found version on Uptodown: {version}")
                    return version, f"uptodown:{download_url}", title
            except Exception as e:
                print(f"[-] Uptodown version check failed: {e}")

        return "latest", f"fallback:{package_name}", package_name

    def get_download_url(self, initial_url):
        """
        מחלץ את קישור ההורדה הישיר על בסיס המקור שזוהה בשלב הקודם.
        מעקף זה מונע לחלוטין את חסימות 403 של Cloudflare.
        """
        print(f"[*] [Custom Fallback] Resolving download URL for: {initial_url}")

        if initial_url.startswith("apkpure_mobile:"):
            real_url = initial_url.split("apkpure_mobile:", 1)[1]
            return real_url

        if initial_url.startswith("aptoide:"):
            real_url = initial_url.split("aptoide:", 1)[1]
            return real_url

        if initial_url.startswith("uptodown:"):
            real_url = initial_url.split("uptodown:", 1)[1]
            return real_url

        # במקרה שלא זוהה קישור מובנה, הרץ בדיקה ישירה לפי הסדר
        package_name = initial_url.split("fallback:", 1)[1] if "fallback:" in initial_url else initial_url
        
        # 1. APKPure Mobile
        try:
            from core.sources.apkpure_mobile import APKPureMobileSource
            pure = APKPureMobileSource(timeout=self.timeout)
            _, download_url, _ = pure.get_latest_version(package_name)
            if download_url:
                return download_url
        except:
            pass

        # 2. Aptoide
        try:
            from core.sources.aptoide import AptoideSource
            aptoide = AptoideSource(timeout=self.timeout)
            _, download_url, _ = aptoide.get_latest_version(package_name)
            if download_url:
                return download_url
        except:
            pass

        # 3. Uptodown
        if self.uptodown_subdomain:
            try:
                _, download_url, _ = self._scrape_uptodown_meta(self.uptodown_subdomain)
                if download_url:
                    return download_url
            except:
                pass

        return None

    def _scrape_uptodown_meta(self, subdomain):
        """Uptodown scraping (לא חסום ב-Cloudflare)"""
        base_url = subdomain if subdomain.startswith("http") else f"https://{subdomain}.en.uptodown.com/android"
        download_page = f"{base_url.rstrip('/')}/download"
        
        r = self.scraper.get(download_page, timeout=self.timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        version_div = soup.select_one('div.version')
        version = version_div.get_text(strip=True) if version_div else None
        
        name_el = soup.select_one('#detail-app-name')
        file_id = name_el.get('data-file-id') if name_el else None
        
        if not file_id:
            return None, None, None

        pre_download_url = f"{download_page.rstrip('/')}/{file_id}-x"
        self.scraper.headers.update({'Referer': download_page})
        r2 = self.scraper.get(pre_download_url, timeout=self.timeout)
        r2.raise_for_status()
        
        soup2 = BeautifulSoup(r2.text, "html.parser")
        download_button = soup2.select_one('#detail-download-button')
        final_token = download_button.get('data-url') if download_button else None
        
        if not final_token:
            return None, None, None

        final_token = final_token.strip('/')
        download_url = f"https://dw.uptodown.com/dwn/{final_token}/app.apk"
        return version, download_url, subdomain

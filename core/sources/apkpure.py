import re
from urllib.parse import quote

import cloudscraper


class APKPureSource:
    def __init__(self, timeout: int = 30, file_type: str = "XAPK", version: str = "latest"):
        self.timeout = timeout
        self.file_type = file_type.upper()
        self.version = version
        self.base_direct_api = "https://d.apkpure.com/b"
        
        # Use cloudscraper to bypass Cloudflare/WAF 403 errors
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://apkpure.com/",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    def _build_direct_url(self, package_name: str) -> str:
        package = quote(package_name, safe=".")
        return f"{self.base_direct_api}/{self.file_type}/{package}?version={self.version}"

    def _extract_version(self, text: str) -> str | None:
        if not text:
            return None
        match = re.search(r"(\d+(?:\.\d+){1,})", text)
        return match.group(1) if match else None

    def get_latest_version(self, package_name: str):
        """
        Resolve latest package via direct endpoint and infer version from response metadata.

        Returns:
            (version, release_url, title)
        """
        release_url = self._build_direct_url(package_name)
        print(f"[*] [APKPure] Resolving latest package for: {package_name}")

        response = None
        try:
            # Use self.scraper instead of requests to bypass 403
            response = self.scraper.get(
                release_url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True,
            )
            response.raise_for_status()

            content_type = (response.headers.get("Content-Type") or "").lower()
            if content_type.startswith("text/html"):
                print("[-] [APKPure] Received HTML instead of package binary.")
                return None, None, None

            content_disposition = response.headers.get("Content-Disposition", "")
            filename_match = re.search(
                r"filename\*?=['\"]?(?:UTF-8'')?([^'\";\n]+)", content_disposition
            )
            filename = filename_match.group(1) if filename_match else ""

            version = (
                self._extract_version(filename)
                or self._extract_version(response.url)
                or "latest"
            )
            title = filename or package_name
            return version, release_url, title
        except Exception as e:
            print(f"[-] [APKPure] Error resolving metadata: {e}")
            return None, None, None
        finally:
            if response is not None:
                response.close()

    def get_download_url(self, initial_url: str):
        """APKPure direct endpoint handles redirect to CDN."""
        return initial_url
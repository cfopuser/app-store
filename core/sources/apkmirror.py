import time
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import cloudscraper

class APKMirrorSource:
    def __init__(self, timeout: int = 5, results: int = 5):
        self.timeout = timeout
        self.results = results
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
        self.headers = {"User-Agent": self.user_agent}
        self.base_url = "https://www.apkmirror.com"
        self.base_search = f"{self.base_url}/?post_type=app_release&searchtype=apk&s="
        self.scraper = cloudscraper.create_scraper()

    def _extract_version_from_title(self, title: str) -> str:
        match = re.search(r"(\d+(?:\.\d+)+)", title)
        return match.group(1) if match else "0.0.0"

    def get_latest_version(self, package_name: str):
        """
        Search for the latest version and return minimal info.
        
        Returns:
            (version, download_link, title)
        """
        print(f"[*] [APKMirror] Searching for: {package_name}")
        time.sleep(self.timeout)
        search_url = self.base_search + quote_plus(package_name)
        resp = self.scraper.get(search_url, headers=self.headers)
        
        if resp.status_code != 200:
            return None, None, None

        soup = BeautifulSoup(resp.text, "html.parser")
        app_rows = soup.find_all("div", {"class": "appRow"})
        
        if not app_rows:
            return None, None, None

        latest = app_rows[0]
        title = latest.find("h5", {"class": "appRowTitle"}).text.strip()
        version = self._extract_version_from_title(title)
        link = self.base_url + latest.find("a", {"class": "downloadLink"})["href"]
        
        return version, link, title

    def get_download_url(self, app_release_url: str):
        """Resolve the final direct download link."""
        time.sleep(self.timeout)
        print("[*] [APKMirror] Getting variant details...")
        resp = self.scraper.get(app_release_url, headers=self.headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # This part is sensitive to APKMirror HTML structure
        rows = soup.find_all("div", {"class": ["table-row", "headerFont"]})
        if len(rows) < 2:
            return None

        # Just take the first variant for now (similar to original logic)
        data = rows[1]
        download_link = self.base_url + data.find_all("a", {"class": "accent_color"})[0]["href"]

        time.sleep(self.timeout)
        print("[*] [APKMirror] Getting download page...")
        resp = self.scraper.get(download_link, headers=self.headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        button_page = self.base_url + str(soup.find_all("a", {"class": "downloadButton"})[0]["href"])

        time.sleep(self.timeout)
        print("[*] [APKMirror] Extracting direct link...")
        resp = self.scraper.get(button_page, headers=self.headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        direct_link_element = soup.find(
            "a",
            {
                "rel": "nofollow",
                "data-google-interstitial": "false",
                "href": lambda href: href and "/wp-content/themes/APKMirror/download.php" in href,
            }
        )
        
        if not direct_link_element:
            return None

        return self.base_url + str(direct_link_element["href"])

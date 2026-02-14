import time
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

import cloudscraper


class APKMirror:
    def __init__(
        self, timeout: int = None, results: int = None, user_agent: str = None
    ):
        self.timeout = timeout if timeout else 5
        self.results = results if results else 5

        self.user_agent = (
            user_agent
            if user_agent
            else "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
        )
        self.headers = {"User-Agent": self.user_agent}

        self.base_url = "https://www.apkmirror.com"
        self.base_search = f"{self.base_url}/?post_type=app_release&searchtype=apk&s="

        self.scraper = cloudscraper.create_scraper()

    def search(self, query):
        print("[search] Sleeping...")

        time.sleep(self.timeout)

        search_url = self.base_search + quote_plus(query)
        resp = self.scraper.get(search_url, headers=self.headers)

        print(f"[search] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        apps = []
        appRow = soup.find_all("div", {"class": "appRow"})

        for app in appRow:
            try:
                app_dict = {
                    "name": app.find("h5", {"class": "appRowTitle"}).text.strip(),
                    "link": self.base_url
                    + app.find("a", {"class": "downloadLink"})["href"],
                    "image": self.base_url
                    + app.find("img", {"class": "ellipsisText"})["src"]
                    .replace("h=32", "h=512")
                    .replace("w=32", "w=512"),
                }

                apps.append(app_dict)

            except AttributeError:
                pass

        return apps[: self.results]

    def get_app_details(self, app_link):
        print("[get_app_details] Sleeping...")

        time.sleep(self.timeout)

        resp = self.scraper.get(app_link, headers=self.headers)

        print(f"[get_app_details] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        data = soup.find_all("div", {"class": ["table-row", "headerFont"]})[1]

        architecture = data.find_all(
            "div",
            {
                "class": [
                    "table-cell",
                    "rowheight",
                    "addseparator",
                    "expand",
                    "pad",
                    "dowrap",
                ]
            },
        )[1].text.strip()
        android_version = data.find_all(
            "div",
            {
                "class": [
                    "table-cell",
                    "rowheight",
                    "addseparator",
                    "expand",
                    "pad",
                    "dowrap",
                ]
            },
        )[2].text.strip()
        dpi = data.find_all(
            "div",
            {
                "class": [
                    "table-cell",
                    "rowheight",
                    "addseparator",
                    "expand",
                    "pad",
                    "dowrap",
                ]
            },
        )[3].text.strip()
        download_link = (
            self.base_url + data.find_all("a", {"class": "accent_color"})[0]["href"]
        )

        return {
            "architecture": architecture,
            "android_version": android_version,
            "dpi": dpi,
            "download_link": download_link,
        }

    def get_download_link(self, app_download_link):
        print("[get_download_link] Sleeping...")

        time.sleep(self.timeout)

        resp = self.scraper.get(app_download_link, headers=self.headers)

        print(f"[get_download_link] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        return self.base_url + str(
            soup.find_all("a", {"class": "downloadButton"})[0]["href"]
        )

    def get_direct_download_link(self, app_download_url):
        print("[get_direct_download_link] Sleeping...")

        time.sleep(self.timeout)

        resp = self.scraper.get(app_download_url, headers=self.headers)

        print(f"[get_direct_download_link] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        data = soup.find(
            "a",
            {
                "rel": "nofollow",
                "data-google-interstitial": "false",
                "href": lambda href: href
                and "/wp-content/themes/APKMirror/download.php" in href,
            },
        )["href"]

        return self.base_url + str(data)

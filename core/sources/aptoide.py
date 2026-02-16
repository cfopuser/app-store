import requests

class AptoideSource:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.base_url = "https://ws2.aptoide.com/api/7/app/getMeta"

    def get_latest_version(self, package_name: str):
        """
        Fetch metadata from Aptoide API.
        
        Returns:
            (version, download_link, title)
        """
        print(f"[*] [Aptoide] Fetching metadata for: {package_name}")
        params = {
            "package_name": package_name,
            "language": "en"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get("info", {}).get("status") != "OK":
                print(f"[-] [Aptoide] API returned status: {data.get('info', {}).get('status')}")
                return None, None, None
            
            app_data = data.get("data", {})
            file_data = app_data.get("file", {})
            
            version = file_data.get("vername")
            # Prefer 'path', fallback to 'path_alt'
            download_url = file_data.get("path") or file_data.get("path_alt")
            title = app_data.get("name", package_name)
            
            return version, download_url, title
            
        except Exception as e:
            print(f"[-] [Aptoide] Error fetching metadata: {e}")
            return None, None, None

    def get_download_url(self, initial_url: str):
        """Aptoide provides the direct link in the metadata, so this is just a passthrough."""
        return initial_url

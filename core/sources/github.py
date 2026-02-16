import requests
import re

class GitHubSource:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.api_base_url = "https://api.github.com/repos"

    def get_latest_version(self, repo: str):
        """
        Fetch latest release metadata from GitHub API.
        
        Args:
            repo: GitHub repository in the format 'Owner/Repo'.
            
        Returns:
            (version, download_url, title)
        """
        print(f"[*] [GitHub] Fetching latest release for: {repo}")
        url = f"{self.api_base_url}/{repo}/releases/latest"
        
        try:
            # We don't use a token by default to keep it simple, 
            # but GitHub API has rate limits for unauthenticated requests.
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            version = data.get("tag_name")
            title = data.get("name") or version
            
            # Find the first .apk asset
            assets = data.get("assets", [])
            download_url = None
            for asset in assets:
                if asset.get("name", "").endswith(".apk"):
                    download_url = asset.get("browser_download_url")
                    break
            
            if not download_url:
                print(f"[-] [GitHub] No APK asset found in release {version}")
                return None, None, None
                
            return version, download_url, title
            
        except Exception as e:
            print(f"[-] [GitHub] Error fetching metadata: {e}")
            return None, None, None

    def get_download_url(self, initial_url: str):
        """GitHub browser_download_url is a direct-ish link (redirects to objects.githubusercontent.com)."""
        return initial_url

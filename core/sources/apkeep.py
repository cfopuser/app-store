import os
import sys
import re
import platform
import subprocess
import urllib.request
from pathlib import Path

class FakeResponse:
    """עוטף את הקובץ שהורד ומזרים אותו ל-downloader.py"""
    def __init__(self, filepath, url):
        self.filepath = filepath
        self.status_code = 200
        self.url = url
        filename = os.path.basename(filepath)
        content_type = "application/vnd.android.package-archive" if filename.endswith(".apk") else "application/octet-stream"
        self.headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"'
        }

    def iter_content(self, chunk_size=8192):
        with open(self.filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def close(self):
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
            except Exception:
                pass


class ApkeepScraper:
    def __init__(self, source_instance):
        self.source = source_instance

    def get(self, url, stream=False, headers=None, allow_redirects=True):
        package_name = url.split("apkeep_dl:")[1]
        out_dir = os.path.join(os.getcwd(), "scratch", "apkeep_tmp")
        os.makedirs(out_dir, exist_ok=True)

        print(f"[*] [apkeep] Downloading {package_name} from Google Play Store...")

        # הרצת פקודת ההורדה מול גוגל פליי
        cmd = [
            self.source.bin_path,
            "-a", package_name,
            "-d", "google-play",
            "-e", self.source.google_email,
            "-t", self.source.aas_token,
            out_dir
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"apkeep download failed: {e}")

        # איתור הקובץ שירד
        downloaded_file = None
        for f in os.listdir(out_dir):
            if f.startswith(package_name) and f.endswith((".apk", ".xapk", ".apks")):
                downloaded_file = os.path.join(out_dir, f)
                break

        if not downloaded_file:
            candidates = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith((".apk", ".xapk", ".apks"))]
            if candidates:
                downloaded_file = candidates[0]

        if not downloaded_file:
            raise RuntimeError("apkeep finished successfully, but no APK file was found in output directory.")

        return FakeResponse(downloaded_file, url)


class ApkeepSource:
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        
        # קריאת נתוני ההזדהות של גוגל מתוך משתני הסביבה (GitHub Secrets)
        self.google_email = os.getenv("GOOGLE_EMAIL", "").strip()
        self.aas_token = os.getenv("AAS_TOKEN", "").strip()

        if not self.google_email or not self.aas_token:
            raise ValueError(
                "Missing credentials for Google Play! Please set GOOGLE_EMAIL and AAS_TOKEN in environment/secrets."
            )

        self.bin_path = self._ensure_binary_exists()
        self.scraper = ApkeepScraper(self)
        self.headers = {}

    def _ensure_binary_exists(self) -> str:
        """מוריד את הבינארי של apkeep לפי מערכת ההפעלה"""
        bin_dir = os.path.join(os.getcwd(), "core", "bin")
        os.makedirs(bin_dir, exist_ok=True)

        is_win = platform.system() == "Windows"
        bin_name = "apkeep.exe" if is_win else "apkeep"
        bin_path = os.path.join(bin_dir, bin_name)

        if os.path.exists(bin_path):
            return bin_path

        print(f"[*] [apkeep] Downloading apkeep tool for {platform.system()}...")
        if is_win:
            url = "https://github.com/EFForg/apkeep/releases/latest/download/apkeep-x86_64-pc-windows-msvc.exe"
        else:
            url = "https://github.com/EFForg/apkeep/releases/latest/download/apkeep-x86_64-unknown-linux-gnu"

        try:
            urllib.request.urlretrieve(url, bin_path)
            if not is_win:
                os.chmod(bin_path, 0o755)
            print(f"[+] [apkeep] Tool ready at {bin_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to download apkeep binary: {e}")

        return bin_path

    def _extract_version(self, text: str) -> str | None:
        match = re.search(r"(\d+(?:\.\d+){1,})", text)
        return match.group(1) if match else None

    def get_latest_version(self, package_name: str):
        print(f"[*] [apkeep] Checking version for {package_name} on Google Play...")
        cmd = [
            self.bin_path,
            "-l",
            "-a", package_name,
            "-d", "google-play",
            "-e", self.google_email,
            "-t", self.aas_token
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            output = res.stdout.strip()
            
            lines = [line.strip() for line in output.splitlines() if line.strip()]
            version = None
            for line in lines:
                v = self._extract_version(line)
                if v:
                    version = v
                    break

            if not version:
                version = "latest"

            return version, package_name, package_name

        except Exception as e:
            print(f"[-] [apkeep] Failed to query Google Play version: {e}")
            return None, None, None

    def get_download_url(self, initial_url: str):
        return f"apkeep_dl:{initial_url}"

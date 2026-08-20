import os
import sys
import re
import platform
import subprocess
import urllib.request
from pathlib import Path

class LocalFileResponse:
    """עוטף את הקובץ שכבר הורדנו ומעביר אותו ל-downloader.py"""
    def __init__(self, filepath):
        self.filepath = filepath
        self.status_code = 200
        self.url = filepath
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
        pass # אנחנו לא מוחקים כאן, ה-OS ינקה את תיקיית ה-scratch בסוף הריצה


class ApkeepScraper:
    def get(self, url, stream=False, headers=None, allow_redirects=True):
        # ה-URL כאן הוא למעשה הנתיב הלוקאלי לקובץ שכבר הורדנו בשלב בדיקת הגרסה!
        filepath = url.split("apkeep_local:")[1]
        print(f"[*] [apkeep] Using already downloaded Google Play artifact: {os.path.basename(filepath)}")
        return LocalFileResponse(filepath)


class ApkeepSource:
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        
        self.google_email = os.getenv("GOOGLE_EMAIL", "").strip()
        self.aas_token = os.getenv("AAS_TOKEN", "").strip()

        if not self.google_email or not self.aas_token:
            raise ValueError(
                "Missing credentials for Google Play! Please set GOOGLE_EMAIL and AAS_TOKEN in environment/secrets."
            )

        self.bin_path = self._ensure_binary_exists()
        self.scraper = ApkeepScraper()
        self.headers = {}

    def _ensure_binary_exists(self) -> str:
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
        except Exception as e:
            raise RuntimeError(f"Failed to download apkeep binary: {e}")

        return bin_path

    def get_latest_version(self, package_name: str):
        print(f"[*] [apkeep] Initiating Google Play download to extract REAL version for {package_name}...")
        
        out_dir = os.path.join(os.getcwd(), "scratch", "apkeep_tmp")
        os.makedirs(out_dir, exist_ok=True)
        
        # ניקוי קבצים ישנים של האפליקציה בתיקייה (אם נשארו מריצה קודמת)
        for f in os.listdir(out_dir):
            if f.startswith(package_name):
                try: os.remove(os.path.join(out_dir, f))
                except: pass

        cmd = [
            self.bin_path,
            "-a", package_name,
            "-d", "google-play",
            "-e", self.google_email,
            "-t", self.aas_token,
            out_dir
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"[-] [apkeep] Download from Google Play failed: {e}")
            return None, None, None

        # מציאת הקובץ שהורדנו כרגע
        downloaded_file = None
        for f in os.listdir(out_dir):
            if f.startswith(package_name) and f.endswith((".apk", ".xapk", ".apks")):
                downloaded_file = os.path.join(out_dir, f)
                break
        
        if not downloaded_file:
            print("[-] [apkeep] Could not find the downloaded file in temp folder.")
            return None, None, None

        print(f"[*] [apkeep] Extracting versionName directly from {os.path.basename(downloaded_file)}...")
        
        # פירוק מהיר (ללא קוד מקור, רק Manifest) כדי לשלוף את הגרסה האמיתית
        decode_dir = os.path.join(out_dir, f"{package_name}_meta")
        apktool_cmd = ["apktool", "d", "-s", "-f", "-o", decode_dir, downloaded_file]
        
        version = "latest"
        try:
            subprocess.run(apktool_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            yml_path = os.path.join(decode_dir, "apktool.yml")
            
            if os.path.exists(yml_path):
                with open(yml_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"versionName:\s*['\"]?([^'\">\r\n]+)", content)
                    if match:
                        version = match.group(1).strip()
            
            print(f"[+] [apkeep] Real Google Play Version extracted: {version}")
            
        except Exception as e:
            print(f"[-] [apkeep] Failed to extract exact version (fallback to 'latest'): {e}")

        # מחזירים את הגרסה, ואת נתיב הקובץ במקום URL!
        return version, downloaded_file, package_name


    def get_download_url(self, local_filepath: str):
        # המערכת תקרא לפונקציה הזו רק אם נמצא ש`version` שונה מהמקומי.
        # לכן פשוט נחזיר קידומת שתגיד ל-Scraper להשתמש בקובץ הקיים!
        return f"apkeep_local:{local_filepath}"

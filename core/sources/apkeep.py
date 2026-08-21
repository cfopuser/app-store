import os
import sys
import re
import platform
import subprocess
import urllib.request
import zipfile
from pathlib import Path

class LocalFileResponse:
    """עוטף את קובץ ה-XAPK שאספנו ומעביר אותו ל-downloader"""
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
        pass


class ApkeepScraper:
    def __init__(self, source_instance):
        self.source = source_instance

    def get(self, url, stream=False, headers=None, allow_redirects=True):
        if url.startswith("apkeep_local:"):
            filepath = url.split("apkeep_local:")[1]
            print(f"[*] [apkeep] Using already downloaded Universal XAPK: {os.path.basename(filepath)}")
            return LocalFileResponse(filepath, url)
        
        elif url.startswith("apkeep_dl:"):
            package_name = url.split("apkeep_dl:")[1]
            out_dir = os.path.join(os.getcwd(), "scratch", "apkeep_tmp")
            
            # בניית ה-XAPK מתוך פרופילים מרובים
            xapk_path = self.source._download_universal_xapk(package_name, out_dir)
            return LocalFileResponse(xapk_path, url)
        else:
            raise ValueError(f"Unknown URL format for apkeep scraper: {url}")


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
        self.scraper = ApkeepScraper(self)
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

    def _download_universal_xapk(self, package_name: str, out_dir: str) -> str:
        """מזייף בקשות עבור שני פרופילי מעבדים, אוסף את החלקים, ובונה קובץ XAPK אוניברסלי"""
        os.makedirs(out_dir, exist_ok=True)
        
        dir_64 = os.path.join(out_dir, "64")
        dir_32 = os.path.join(out_dir, "32")
        os.makedirs(dir_64, exist_ok=True)
        os.makedirs(dir_32, exist_ok=True)

        # תיקון קריטי: כותרת [default] וארכיטקטורות (NativePlatforms) כפי ש-apkeep דורש!
        prop_64 = os.path.join(out_dir, "64.properties")
        with open(prop_64, "w") as f:
            f.write("""[default]
Build.VERSION.SDK_INT=30
Build.VERSION.RELEASE=11
Build.HARDWARE=walleye
Build.BRAND=google
Build.MODEL=Pixel 2
Build.DEVICE=walleye
Build.MANUFACTURER=Google
Build.PRODUCT=walleye
NativePlatforms=arm64-v8a,armeabi-v7a,armeabi
""")
            
        prop_32 = os.path.join(out_dir, "32.properties")
        with open(prop_32, "w") as f:
            f.write("""[default]
Build.VERSION.SDK_INT=30
Build.VERSION.RELEASE=11
Build.HARDWARE=sailfish
Build.BRAND=google
Build.MODEL=Pixel
Build.DEVICE=sailfish
Build.MANUFACTURER=Google
Build.PRODUCT=sailfish
NativePlatforms=armeabi-v7a,armeabi
""")

        # הוספת split_apk=true כדי לוודא שנקבל את הקבצים המפוצלים במקום בסיס בלבד
        print(f"[*] [apkeep] Fetching 64-bit splits from Google Play...")
        subprocess.run([
            self.bin_path, "-a", package_name, "-d", "google-play",
            "-e", self.google_email, "-t", self.aas_token,
            "-o", f"device=default,split_apk=true,device_properties_file={prop_64}",
            dir_64
        ], check=True, stdout=subprocess.DEVNULL)

        print(f"[*] [apkeep] Fetching 32-bit splits from Google Play...")
        subprocess.run([
            self.bin_path, "-a", package_name, "-d", "google-play",
            "-e", self.google_email, "-t", self.aas_token,
            "-o", f"device=default,split_apk=true,device_properties_file={prop_32}",
            dir_32
        ], check=True, stdout=subprocess.DEVNULL)

        print("[*] [apkeep] Merging downloaded splits into a Universal XAPK...")
        
        all_apks = {}
        for d in [dir_64, dir_32]:
            for f in os.listdir(d):
                filepath = os.path.join(d, f)
                if f.endswith(".apk"):
                    all_apks[f] = filepath
                elif f.endswith((".apks", ".xapk")):
                    with zipfile.ZipFile(filepath, 'r') as z:
                        for zf in z.namelist():
                            if zf.endswith(".apk"):
                                ext_path = os.path.join(d, zf)
                                if not os.path.exists(ext_path):
                                    z.extract(zf, d)
                                all_apks[zf] = ext_path

        if not all_apks:
            raise RuntimeError("Failed to collect APK splits from Google Play.")

        # כעת נוצר קובץ XAPK מסודר שמכיל את כל החתיכות ללא כפילויות (64+32)
        xapk_path = os.path.join(out_dir, f"{package_name}_universal.xapk")
        with zipfile.ZipFile(xapk_path, 'w') as z:
            z.writestr("manifest.json", '{"package_name":"' + package_name + '"}')
            for apk_name, apk_path in all_apks.items():
                z.write(apk_path, apk_name)

        return xapk_path

    def get_latest_version(self, package_name: str):
        # ---------------------------------------------------------
        # שלב 1: בדיקת הגרסה מול Google Play (סריקת רשת מהירה)
        # ---------------------------------------------------------
        print(f"[*] [apkeep] Checking Play Store web page for {package_name}...")
        url = f"https://play.google.com/store/apps/details?id={package_name}&hl=en"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            
            version_match = re.search(r'\[\[\["(\d+(?:\.\d+)+)"\]\]', html)
            if not version_match:
                version_match = re.search(r'\["(\d+\.\d+\.\d+(?:\.\d+)?)"\]', html)

            if version_match:
                version = version_match.group(1)
                print(f"[+] [apkeep] Found Google Play version: {version}")
                return version, f"dl:{package_name}", package_name
        except Exception as e:
            print(f"[-] [apkeep] Web scrape failed: {e}")

        # ---------------------------------------------------------
        # שלב 2: אם גוגל מסתירה את הגרסה, מורידים את הפרופילים ומרכיבים XAPK כדי לגלות
        # ---------------------------------------------------------
        print(f"[!] [apkeep] Version hidden. Building Universal APK from splits to extract real version...")
        
        out_dir = os.path.join(os.getcwd(), "scratch", "apkeep_tmp")
        os.makedirs(out_dir, exist_ok=True)
        
        try:
            xapk_path = self._download_universal_xapk(package_name, out_dir)
        except Exception as e:
            print(f"[-] [apkeep] Universal build failed: {e}")
            return None, None, None

        print(f"[*] [apkeep] Extracting versionName directly from Universal XAPK...")
        decode_dir = os.path.join(out_dir, f"{package_name}_meta")
        apktool_cmd = ["apktool", "d", "-s", "-f", "-o", decode_dir, xapk_path]
        
        version = "latest"
        try:
            subprocess.run(apktool_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            yml_path = os.path.join(decode_dir, "apktool.yml")
            if os.path.exists(yml_path):
                with open(yml_path, "r", encoding="utf-8") as f:
                    match = re.search(r"versionName:\s*['\"]?([^'\">\r\n]+)", f.read())
                    if match:
                        version = match.group(1).strip()
            print(f"[+] [apkeep] Real Version extracted: {version}")
        except Exception as e:
            print(f"[-] [apkeep] Failed to extract exact version: {e}")

        return version, f"local:{xapk_path}", package_name


    def get_download_url(self, release_url: str):
        if release_url.startswith("local:"):
            filepath = release_url.split("local:")[1]
            return f"apkeep_local:{filepath}"
        elif release_url.startswith("dl:"):
            package_name = release_url.split("dl:")[1]
            return f"apkeep_dl:{package_name}"
            
        return None

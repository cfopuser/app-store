import os
import sys
import subprocess
import zipfile
import tempfile
import urllib.request
import json

def get_apkeditor(jar_path):
    """מוריד את הגרסה העדכנית של APKEditor מגיטהאב כדי למזג אפליקציות מפוצלות"""
    if os.path.exists(jar_path):
        return
    print("[*] [APKEditor Merger] Downloading REAndroid/APKEditor...")
    try:
        # קודם כל מנסים למשוך את הגרסה האחרונה ביותר דרך ה-API (שלרוב תהיה 1.4.7 או חדשה יותר)
        req = urllib.request.Request("https://api.github.com/repos/REAndroid/APKEditor/releases/latest")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            assets = data.get('assets',[])
            url = next(a['browser_download_url'] for a in assets if a['name'].endswith('.jar'))
            urllib.request.urlretrieve(url, jar_path)
    except Exception as e:
        print(f"[*] [APKEditor Merger] API rate limit hit or error: {e}. Using fallback 1.4.7...")
        # גיבוי קשיח ואמין לגרסה 1.4.7 (העדכנית ביותר נכון לעכשיו)
        fallback_url = "https://github.com/REAndroid/APKEditor/releases/download/V1.4.7/APKEditor-1.4.7.jar"
        try:
            urllib.request.urlretrieve(fallback_url, jar_path)
        except Exception as fallback_err:
            print(f"[-] [APKEditor Merger] Fallback download failed: {fallback_err}")
            sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python apkeditor_merger.py <file.xapk>")
        sys.exit(1)

    xapk_path = os.path.abspath(sys.argv[1])
    output_apk = os.path.splitext(xapk_path)[0] + ".apk"

    # מיקום הכלי בתיקייה זמנית כדי לא ללכלך את המאגר
    editor_jar = os.path.join(tempfile.gettempdir(), "APKEditor.jar")
    get_apkeditor(editor_jar)

    # יצירת תיקייה זמנית לחילוץ חלקי האפליקציה (Splits)
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"[*] [APKEditor Merger] Extracting split APKs from {os.path.basename(xapk_path)}...")
        with zipfile.ZipFile(xapk_path, 'r') as z:
            apk_files = [f for f in z.namelist() if f.endswith('.apk')]
            if not apk_files:
                print("[-] [APKEditor Merger] No APK files found inside XAPK.")
                sys.exit(1)
            for item in apk_files:
                z.extract(item, tmpdir)

        print("[*] [APKEditor Merger] Merging split APKs to a single fat APK...")
        
        # הרצת APKEditor למיזוג: m = merge, -i = input directory, -o = output
        cmd =["java", "-jar", editor_jar, "m", "-i", tmpdir, "-o", output_apk]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print(f"[+] [APKEditor Merger] Successfully merged into {os.path.basename(output_apk)}")
        except subprocess.CalledProcessError as e:
            print(f"[-] [APKEditor Merger] Merge failed:\n{e.output.decode(errors='ignore')}")
            sys.exit(1)

if __name__ == '__main__':
    main()

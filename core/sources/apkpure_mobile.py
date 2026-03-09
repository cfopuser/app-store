import re
import requests

class APKPureMobileSource:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_api = "https://api.pureapk.com/m/v3/cms/app_version"
        
        # כותרות שמחקות מכשיר אנדרואיד כדי לא להחסם
        self.headers = {
            'x-sv': '29',
            'x-abis': 'arm64-v8a,armeabi-v7a,armeabi',
            'x-gp': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
        }

    def get_latest_version(self, package_name: str):
        print(f"[*] [APKPure Mobile] Fetching metadata for: {package_name}")
        params = {
            'hl': 'en-US',
            'package_name': package_name
        }
        
        try:
            response = requests.get(
                self.base_api,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            # חילוץ כתובות URL מתוך התשובה הבינארית (מחקה את פקודות strings | grep)
            # מחפש כתובות שמסתיימות ב-.apk (תוך התעלמות מאותיות רישיות/קטנות)
            urls = re.findall(rb'https?://[^\s\0"\'<>]+?\.apk', response.content, flags=re.IGNORECASE)
            
            if not urls:
                print("[-] [APKPure Mobile] No APK URL found in API response.")
                return None, None, None
                
            # לוקחים את התוצאה הראשונה (העדכנית ביותר) וממירים לסטרינג
            release_url = urls[0].decode('utf-8')
            
            # ניסיון לחלץ את גרסת האפליקציה מתוך שם הקובץ ב-URL
            version = "latest"
            version_match = re.search(r'_([\d\.]+)_', release_url)
            if version_match:
                version = version_match.group(1)
            
            title = package_name
            return version, release_url, title
            
        except Exception as e:
            print(f"[-] [APKPure Mobile] Error resolving via API: {e}")
            return None, None, None

    def get_download_url(self, initial_url: str):
        # ה-URL שהתקבל הוא כבר קישור ישיר להורדה, פשוט מחזירים אותו
        return initial_url

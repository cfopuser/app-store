import os
import re
import shutil
import xml.etree.ElementTree as ET

from core.repository import resolve_repository

def get_package_name(manifest_path: str) -> str:
    """קורא את ה-AndroidManifest.xml כדי לחלץ את שם החבילה של האפליקציה."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        return root.get('package')
    except Exception as e:
        print(f"[-] Could not parse package name from manifest: {e}")
        return None

def get_main_activity_smali_path(manifest_path: str) -> str:
    """סורק את ה-AndroidManifest.xml כדי למצוא אוטומטית את מסך הפתיחה (MainActivity)."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        ns = {'android': 'http://schemas.android.com/apk/res/android'}
        
        def is_main_launcher(element):
            is_main = False
            is_launcher = False
            for intent_filter in element.iter('intent-filter'):
                for action in intent_filter.iter('action'):
                    if action.get(f"{{{ns['android']}}}name") == "android.intent.action.MAIN":
                        is_main = True
                for category in intent_filter.iter('category'):
                    if category.get(f"{{{ns['android']}}}name") == "android.intent.category.LAUNCHER":
                        is_launcher = True
            return is_main and is_launcher

        target_activity_name = None

        for activity in root.iter('activity'):
            if is_main_launcher(activity):
                target_activity_name = activity.get(f"{{{ns['android']}}}name")
                break
        
        if not target_activity_name:
            for alias in root.iter('activity-alias'):
                if is_main_launcher(alias):
                    target_activity_name = alias.get(f"{{{ns['android']}}}targetActivity")
                    break
                    
        if target_activity_name:
            if target_activity_name.startswith("."):
                target_activity_name = root.get('package') + target_activity_name
            return target_activity_name.replace('.', '/') + ".smali"

    except Exception as e:
        print(f"[-] Could not parse main activity from manifest: {e}")
    return None

def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting patch process in {decompiled_dir}...")
    
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    payload_dir = os.path.join(current_script_dir, "updater_payload")
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")

    # =========================================================================
    # תיקון שגיאת הקימפול של Apktool (API 37 aapt2 Bug) - חובה להריץ בהתחלה
    # =========================================================================
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()
        
        # מסיר את המאפיין הבעייתי שגורם לקריסה
        new_manifest_content = re.sub(r'\s*[a-zA-Z0-9_:]*recreateOnConfigChanges=["\'][^"\']*["\']', '', manifest_content)
        
        if new_manifest_content != manifest_content:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(new_manifest_content)
            print("[+] Successfully removed recreateOnConfigChanges from AndroidManifest.xml")
    except Exception as e:
        print(f"[-] Failed to fix AndroidManifest.xml compile bug: {e}")

    # =========================================================================
    # חלק 1: הלוגיקה הייחודית של ספוטיפיי 
    # =========================================================================
    print("[*] Applying Spotify-specific patches...")
    target_worker_file = "sharehousekeepingworker.smali"
    
    es_image_patched = False
    video_surface_patched = False

    for root, dirs, files in os.walk(decompiled_dir):
        for filename in files:
            if filename.lower() == target_worker_file:
                try:
                    os.remove(os.path.join(root, filename))
                    print(f"[+] Deleted {filename}")
                except Exception as e:
                    print(f"[-] Failed to delete {filename}: {e}")

        # --- טיפול ב-EsImage$ImageData.smali ---
        if "EsImage$ImageData.smali" in files:
            file_path = os.path.join(root, "EsImage$ImageData.smali")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r"(\.method public (?:final )?getData\(\)L[^;]+;)[\s\S]*?(\.end method)"
            replacement = r"\1\n    .locals 1\n\n    const/4 v0, 0x0\n\n    return-object v0\n\2"
            
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[+] Patched EsImage$ImageData successfully in {file_path}")
                es_image_patched = True
            else:
                print("\n[-] CRITICAL: Failed to patch getData() in EsImage$ImageData.smali!")
                print(f"[i] Dumping Smali context from {file_path}:")
                lines = content.splitlines()
                found_method = False
                for idx, line in enumerate(lines):
                    if 'getData(' in line:
                        found_method = True
                        start = max(0, idx - 2)
                        end = min(len(lines), idx + 15)  # מציג את כל גוף המתודה
                        print(f"--- Method context around line {idx+1} ---")
                        for i in range(start, end):
                            marker = ">>>" if i == idx else "   "
                            print(f"{marker} {i+1}: {lines[i]}")
                        print("------------------------------------------\n")
                if not found_method:
                    print("[-] 'getData(' was not found anywhere in the file!")
                
                # הכשלת התהליך במקום!
                raise RuntimeError("Aborting build: EsImage$ImageData was not patched!")

        # --- טיפול ב-VideoSurfaceView.smali ---
        if "VideoSurfaceView.smali" in files:
            file_path = os.path.join(root, "VideoSurfaceView.smali")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r"(\.method public (?:final )?getTextureView\(\)Landroid/view/TextureView;)[\s\S]*?(\.end method)"
            replacement = r"\1\n    .locals 1\n\n    const/4 v0, 0x0\n\n    return-object v0\n\2"
            
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[+] Patched VideoSurfaceView successfully in {file_path}")
                video_surface_patched = True
            else:
                print("\n[-] CRITICAL: Failed to patch getTextureView() in VideoSurfaceView.smali!")
                print(f"[i] Dumping Smali context from {file_path}:")
                lines = content.splitlines()
                found_method = False
                for idx, line in enumerate(lines):
                    if 'getTextureView(' in line:
                        found_method = True
                        start = max(0, idx - 2)
                        end = min(len(lines), idx + 15)
                        print(f"--- Method context around line {idx+1} ---")
                        for i in range(start, end):
                            marker = ">>>" if i == idx else "   "
                            print(f"{marker} {i+1}: {lines[i]}")
                        print("------------------------------------------\n")
                if not found_method:
                    print("[-] 'getTextureView(' was not found anywhere in the file!")
                
                # הכשלת התהליך במקום!
                raise RuntimeError("Aborting build: VideoSurfaceView was not patched!")

    # בדיקת ביטחון: אם הקבצים בכלל לא נמצאו בריצת הסריקה
    if not es_image_patched:
        raise RuntimeError("[-] CRITICAL: EsImage$ImageData.smali was not found in the APK! Aborting.")
    # =========================================================================
    # חלק 1.5: ביטול תמונת האלבום בנגן ההתראות (MediaMetadataCompat) - חובה
    # =========================================================================
    print("\n[*] Disabling notification album art (mandatory)...")
    builder_re = re.compile(
        r'new-instance\s+[vp]\d+,\s+Landroid/support/v4/media/MediaMetadataCompat;'
    )
    
    # regex משופר - במקום לחפש מתודה בשם 'e', הוא מחפש כל מתודה דינמית
    # כך הוא חסין לשינויים ב-obfuscation שקורים בגרסאות חדשות.
    art_uri_invoke_re = re.compile(
        r'(const-string\s+[vp]\d+,\s*"android\.media\.metadata\.ALBUM_ART_URI"\s*\n)'
        r'(?:[ \t]*(?:\.[^\n]*)?\n)*'
        r'\s*(invoke-virtual\s+\{[^}]+\},\s*L[^;]+;->[a-zA-Z0-9_$]+\([^)]*\)[^\s]+)',
        re.MULTILINE
    )

    target_path = None
    target_content = None

    # שלב 1: איתור הקובץ הבונה
    for root, dirs, files in os.walk(decompiled_dir):
        for file in files:
            if not file.endswith('.smali'):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue
            if builder_re.search(content) and 'ALBUM_ART_URI' in content:
                target_path = path
                target_content = content
                break
        if target_path:
            break

    if not target_path:
        print("[-] CRITICAL: MediaMetadataCompat builder file not found. Aborting.")
        return False

    print(f"[i] Builder file located: {target_path}")

    # שלב 2: ניסיון למצוא את ה-invoke
    match = art_uri_invoke_re.search(target_content)
    if not match:
        print("[!] Could not match the invoke pattern (even with .line allowance).")
        print("[i] Dumping context around ALBUM_ART_URI:")
        lines = target_content.splitlines()
        for idx, line in enumerate(lines):
            if 'ALBUM_ART_URI' in line:
                start = max(0, idx - 2)
                end = min(len(lines), idx + 6)   # מרחיבים קצת
                print(f"--- Occurrence near line {idx+1} ---")
                for i in range(start, end):
                    marker = ">>>" if i == idx else "   "
                    print(f"{marker} {i+1}: {lines[i]}")
                print()
        print("[-] CRITICAL: ALBUM_ART_URI invoke pattern mismatch. Aborting.")
        return False

    # שלב 3: החלפה
    new_content, count = art_uri_invoke_re.subn(r'\1# \2', target_content)
    if count == 0:
        print("[-] CRITICAL: Replacement failed despite pattern match. Aborting.")
        return False

    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"[+] Notification album art disabled successfully in {target_path}")

    # =========================================================================
    # חלק 2: הזרקת מנגנון העדכון האוניברסלי
    # =========================================================================
    print("\n[*] Applying Universal Updater patch...")
    
    app_id = os.path.basename(current_script_dir)
    repo_owner, repo_name = resolve_repository()
    print(f"[i] Detected Repo: {repo_owner}/{repo_name}")

    version_txt_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/main/apps/{app_id}/version.txt"
    download_prefix = f"https://github.com/{repo_owner}/{repo_name}/releases/download/{app_id}-v"
    download_middle = f"/{app_id}-patched-"

    package_name = get_package_name(manifest_path)
    if not package_name:
        print("[-] CRITICAL: Failed to get package name. Aborting updater injection.")
        return False
    
    provider_authority = f"{package_name}.provider"
    target_activity_smali = get_main_activity_smali_path(manifest_path)
    
    print(f"[i] App ID: {app_id}")
    print(f"[i] Package Name: {package_name}")
    print(f"[i] Main Activity: {target_activity_smali}")

    if not os.path.exists(payload_dir):
        print("[!] Warning: Updater payload directory not found! Skipping updater injection.")
        return True

    # -- א. העתקת קבצי העדכון --
    try:
        max_dex = max(
            [int(d.replace("smali_classes", "")) for d in os.listdir(decompiled_dir) if d.startswith("smali_classes") and d.replace("smali_classes", "").isdigit()]
            or [0]
        )
        next_smali_dir = f"smali_classes{max_dex + 1}"
        
        dst_smali_root = os.path.join(decompiled_dir, next_smali_dir, "storeautoupdater")
        src_updater_files = os.path.join(payload_dir, "smali", "storeautoupdater")
        
        if os.path.exists(src_updater_files):
            shutil.copytree(src_updater_files, dst_smali_root, dirs_exist_ok=True)
        else:
            print("[-] CRITICAL: 'storeautoupdater' directory not found in payload/smali.")
            return False
            
        src_res = os.path.join(payload_dir, "res")
        dst_res = os.path.join(decompiled_dir, "res")
        shutil.copytree(src_res, dst_res, dirs_exist_ok=True)
        
        for smali_file in os.listdir(dst_smali_root):
            smali_path = os.path.join(dst_smali_root, smali_file)
            if os.path.isfile(smali_path) and smali_path.endswith('.smali'):
                with open(smali_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                content = content.replace("__PROVIDER_AUTHORITY__", provider_authority)
                content = content.replace("__VERSION_TXT_URL__", version_txt_url)
                content = content.replace("__RELEASE_DOWNLOAD_PREFIX__", download_prefix)
                content = content.replace("__RELEASE_DOWNLOAD_MIDDLE__", download_middle)
                
                with open(smali_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        print(f"[+] Replaced all dynamic placeholders successfully.")

    except Exception as e:
        print(f"[-] Failed to copy or patch updater payload: {e}")
        return False

    # -- ב. הוספת ההרשאות והשירותים ל-AndroidManifest.xml --
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()

        if 'android.permission.REQUEST_INSTALL_PACKAGES' not in manifest_content:
            manifest_content = manifest_content.replace(
                '<application', 
                '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>\n    <application'
            )

        manifest_components = f"""
        <service android:name="storeautoupdater.DownloadService" />
        <provider
            android:name="storeautoupdater.GenericFileProvider"
            android:authorities="{provider_authority}"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/provider_paths" />
        </provider>
"""
        if 'android:name="storeautoupdater.GenericFileProvider"' not in manifest_content:
            manifest_content = manifest_content.replace(
                '</application>', 
                f'{manifest_components}\n    </application>'
            )

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        print("[+] AndroidManifest.xml updated for updater permissions.")
    except Exception as e:
        print(f"[-] Failed to patch AndroidManifest.xml: {e}")
        return False

    # -- ג. הזרקת קוד העדכון למסך הראשי (MainActivity) --
    if not target_activity_smali:
        print("[!] Warning: Could not detect Main Activity automatically.")
        return False

    main_activity_patched = False
    target_filename = os.path.basename(target_activity_smali)

    for root, _, files in os.walk(decompiled_dir):
        if target_filename in files:
            full_path = os.path.join(root, target_filename)
            if target_activity_smali.replace('/', os.sep) not in full_path:
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    main_smali_content = f.read()

                if "Lstoreautoupdater/Updater;->check" in main_smali_content:
                    print("[i] Updater call already exists in MainActivity.")
                    main_activity_patched = True
                else:
                    method_pattern = re.compile(r"(\.method.*?onCreate\(Landroid/os/Bundle;\)V)(.*?)(\.end method)", re.DOTALL)
                    match = method_pattern.search(main_smali_content)
                    
                    if match:
                        method_body = match.group(2)
                        last_return_idx = method_body.rfind("return-void")
                        
                        if last_return_idx != -1:
                            updater_call = (
                                "\n\n    # --- START INJECTION (Universal Updater) ---\n"
                                "    move-object v0, p0\n"
                                "    invoke-static {v0}, Lstoreautoupdater/Updater;->check(Landroid/content/Context;)V\n"
                                "    # --- END INJECTION ---\n\n    "
                            )
                            
                            new_method_body = method_body[:last_return_idx] + updater_call + method_body[last_return_idx:]
                            new_full_method = match.group(1) + new_method_body + match.group(3)
                            main_smali_content = main_smali_content.replace(match.group(0), new_full_method, 1)

                            with open(full_path, 'w', encoding='utf-8') as f:
                                f.write(main_smali_content)
                                
                            main_activity_patched = True
                            print(f"[+] Updater call injected successfully into {target_activity_smali}")
                        else:
                            print(f"[-] Could not find 'return-void' in {target_filename} onCreate().")
                    else:
                        print(f"[-] Could not find onCreate() in {target_filename}.")
            except Exception as e:
                print(f"[-] Failed to process {target_filename}: {e}")
            break
            
    if not main_activity_patched:
        print(f"[-] Error: Failed to patch {target_activity_smali}.")
        return False

    return True

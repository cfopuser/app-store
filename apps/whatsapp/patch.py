import os 
import re 
import zipfile
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.hazmat.primitives import serialization


def patch(decompiled_dir: str) -> bool: 
    print(f"[*] Starting WhatsApp Kosher patch (Smart Line-by-Line Execution)...") 
     
    # 1. חסימות תוכן רגילות 
    photos = _patch_profile_photos(decompiled_dir) 
    newsletter = _patch_newsletter_launcher(decompiled_dir) 
    tabs = _patch_home_tabs(decompiled_dir) 
     
    # 2. חסימות ליבה 
    spi = _patch_secure_pending_intent(decompiled_dir) 
    browser = _patch_force_external_browser(decompiled_dir) 
     
    # 3. טיפול בסטטוסים 
    status_nuke = _patch_nuke_status_activity(decompiled_dir) 
    status_redirect = _patch_redirect_status_intents(decompiled_dir) 
     
    # 4. חסימת טאב הגיפים - אלגוריתם חכם חדש 
    gifs_tab = _patch_gifs_tab(decompiled_dir) 
    mime_crash = _patch_mime_type_crash(decompiled_dir) 
    sig_bypass = _patch_signature_bypass(decompiled_dir)
 
    results = [photos, newsletter, tabs, spi, browser, status_nuke, status_redirect, gifs_tab, mime_crash, sig_bypass] 
     
    if all(results): 
        print("\n[SUCCESS] All patches applied successfully!") 
        return True 
    else: 
        print("\n[FAILURE] One or more critical patches failed. Check logs.") 
        return False 
         
 
# --------------------------------------------------------- 
# 1. חסימת תמונות פרופיל 
# --------------------------------------------------------- 
def _patch_profile_photos(root_dir): 
    anchor = 'contactPhotosBitmapManager/getphotofast/' 
    print(f"\n[1] Scanning for Photo Manager ({anchor})...") 
     
    target_file = _find_file_by_string(root_dir, anchor) 
    if not target_file: 
        print("    [-] File not found.") 
        return False 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read() 
        original_content = content 
         
        declaration_pattern = r"(\s+(?:\.locals|\.registers) \d+)" 
 
        bitmap_regex = r"(\.method public final \w+\(Landroid\/content\/Context;L[^;]+;Ljava\/lang\/String;FIJZZ\)Landroid\/graphics\/Bitmap;)" + declaration_pattern 
        content = re.sub(bitmap_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content) 
 
        stream_regex = r"(\.method public final \w+\(L[^;]+;Z\)Ljava\/io\/InputStream;)" + declaration_pattern 
        content = re.sub(stream_regex, r"\1\2\n    const/4 v0, 0x0\n    return-object v0", content) 
         
        if content != original_content: 
            print("    [+] Photo loaders blocked successfully.") 
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content) 
            return True 
        else: 
            print("    [-] Photo loader signatures not found.") 
            return False 
    except Exception as e: 
        print(f"    [-] Error: {e}") 
        return False 
 
# --------------------------------------------------------- 
# 2. נטרול ניוזלטר 
# --------------------------------------------------------- 
def _patch_newsletter_launcher(root_dir): 
    anchor = "NewsletterLinkLauncher/type not handled" 
    print(f"\n[2] Scanning for Newsletter Launcher ({anchor})...") 
     
    target_file = _find_file_by_string(root_dir, anchor) 
    if not target_file: 
        print("    [-] File not found.") 
        return False 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read() 
        original_content = content 
         
        injection = "\n    return-void" 
        declaration_pattern = r"(\s+(?:\.locals|\.registers) \d+)" 
         
        entry_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;\)V)" + declaration_pattern 
        content = re.sub(entry_regex, r"\1\2" + injection, content) 
 
        main_regex = r"(\.method public final \w+\(Landroid\/content\/Context;Landroid\/net\/Uri;L[^;]+;Ljava\/lang\/Integer;Ljava\/lang\/Long;Ljava\/lang\/String;IJ\)V)" + declaration_pattern 
        content = re.sub(main_regex, r"\1\2" + injection, content) 
 
        if content != original_content: 
            print("    [+] Newsletter launcher methods killed.") 
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content) 
            return True 
        else: 
            print("    [-] Newsletter launcher signatures not found.") 
            return False 
    except Exception as e: 
        print(f"    [-] Error: {e}") 
        return False 
 
# --------------------------------------------------------- 
# 3. הסרת טאב העדכונים 
# --------------------------------------------------------- 
def _patch_home_tabs(root_dir): 
    anchor = "Tried to set badge for invalid tab id" 
    print(f"\n[3] Scanning for Home Tabs ({anchor})...") 
     
    target_file = _find_file_by_string(root_dir, anchor) 
    if not target_file: 
        print("    [-] File not found.") 
        return False 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read() 
         
        method_pattern = re.compile(r'(\.method.*?\.end method)', re.DOTALL) 
         
        new_content = content 
        patch_applied = False 
         
        for method_match in method_pattern.finditer(content): 
            method_body = method_match.group(1) 
             
            if "0x12c" in method_body and "0x258" in method_body and "AbstractCollection;->add" in method_body: 
                updates_regex = r"(const/16\s+[vp]\d+,\s*0x12c.*?)((?:invoke-virtual|invoke-interface)\s*\{[vp]\d+,\s*[vp]\d+\},\s*Ljava/util/AbstractCollection;->add\(Ljava/lang/Object;\)Z)" 
                if re.search(updates_regex, method_body, re.DOTALL): 
                    new_method_body = re.sub(updates_regex, r"\1# \2", method_body, count=1, flags=re.DOTALL) 
                    new_content = new_content.replace(method_body, new_method_body) 
                    patch_applied = True 
                    print("    [+] Home Tabs: 'Updates' tab (0x12c) REMOVED.") 
                    break 
         
        if patch_applied: 
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content) 
            return True 
        else: 
            print("    [-] Home Tabs: Target method found, but regex failed.") 
            return False 
    except Exception as e: 
        print(f"    [-] Error: {e}") 
        return False 
 
# --------------------------------------------------------- 
# 4. תיקון SecurePendingIntent 
# --------------------------------------------------------- 
def _patch_secure_pending_intent(root_dir): 
    anchor = "Please set reporter for SecurePendingIntent library" 
    print(f"\n[4] Scanning for SecurePendingIntent ({anchor})...") 
     
    target_file = _find_file_by_string(root_dir, anchor) 
    if not target_file: 
        print("    [i] File not found (optional, skipping).") 
        return True  
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read() 
        pattern = re.compile(r"(if-nez [vp]\d+, (:cond_\w+))(\s*(?:\.line \d+\s*)*)(const-string [vp]\d+, \"Please set reporter)") 
        new_content, num_subs = pattern.subn(r"goto \2\3\4", content) 
         
        if num_subs > 0: 
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content) 
            print(f"    [SUCCESS] Bypassed {num_subs} SecurePendingIntent checks.") 
            return True 
        else: 
            print("    [-] Check not found or already bypassed.") 
            return True 
    except Exception as e: 
        print(f"    [-] Error: {e}") 
        return False 
 
# --------------------------------------------------------- 
# 5. חסימת דפדפן פנימי 
# --------------------------------------------------------- 
def _patch_force_external_browser(root_dir): 
    target_filename = "WaInAppBrowsingActivity.smali" 
    print(f"\n[5] Hijacking Internal Browser ({target_filename})...") 
     
    target_file = _find_file_recursive(root_dir, target_filename) 
    if not target_file: 
        print("    [-] WaInAppBrowsingActivity.smali not found. Skipping.") 
        return False 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read() 
 
        super_class_match = re.search(r"^\.super\s+(L[^;]+;)", content, re.MULTILINE) 
        if not super_class_match: return False 
        parent_class = super_class_match.group(1) 
 
        method_pattern = re.compile(r"(\.method public onCreate\(Landroid\/os\/Bundle;\)V)(.*?)(\.end method)", re.DOTALL) 
        match = method_pattern.search(content) 
        if not match: return False 
 
        original_body = match.group(2) 
        new_body = f""" 
    .locals 4 
    invoke-super {{p0, p1}}, {parent_class}->onCreate(Landroid/os/Bundle;)V 
    invoke-virtual {{p0}}, Landroid/app/Activity;->getIntent()Landroid/content/Intent; 
    move-result-object v0 
    const-string v1, "webview_url" 
    invoke-virtual {{v0, v1}}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String; 
    move-result-object v2 
    if-nez v2, :cond_start_browser 
    invoke-virtual {{p0}}, Landroid/app/Activity;->finish()V 
    return-void 
    :cond_start_browser 
    invoke-static {{v2}}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri; 
    move-result-object v0 
    new-instance v1, Landroid/content/Intent; 
    const-string v3, "android.intent.action.VIEW" 
    invoke-direct {{v1, v3, v0}}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V 
    :try_start_0 
    invoke-virtual {{p0, v1}}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V 
    :try_end_0 
    .catch Ljava/lang/Exception; {{:try_start_0 .. :try_end_0}} :catch_0 
    goto :goto_finish 
    :catch_0 
    move-exception v0 
    const/4 v0, 0x1  
    const-string v1, "\\u05dc\\u05d0 \\u05e0\\u05de\\u05e6\\u05d0 \\u05d3\\u05e4\\u05d3\\u05e4\\u05df / No Browser Found"  
    invoke-static {{p0, v1, v0}}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast; 
    move-result-object v0 
    invoke-virtual {{v0}}, Landroid/widget/Toast;->show()V 
    :goto_finish 
    invoke-virtual {{p0}}, Landroid/app/Activity;->finish()V 
    return-void 
""" 
        new_content = content.replace(original_body, new_body) 
        with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content) 
        print(f"    [+] Browser hijacked successfully!") 
        return True 
    except Exception as e: 
        print(f"    [-] Error patching browser: {e}") 
        return False 
 
# --------------------------------------------------------- 
# 6. הריגת נגן הסטטוסים 
# --------------------------------------------------------- 
def _patch_nuke_status_activity(root_dir): 
    target_filename = "StatusPlaybackActivity.smali" 
    print(f"\n[6] Nuking Status Playback Activity ({target_filename})...") 
 
    target_file = _find_file_recursive(root_dir, target_filename) 
    if not target_file: 
        print("    [-] StatusPlaybackActivity.smali not found.") 
        return False 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read() 
        super_match = re.search(r"^\.super\s+(L[^;]+;)", content, re.MULTILINE) 
        if not super_match: return False 
         
        parent_class = super_match.group(1) 
        print(f"    [i] Detected parent class: {parent_class}") 
 
        new_content = f""" 
.class public final Lcom/whatsapp/status/playback/StatusPlaybackActivity; 
.super {parent_class} 
.source "StatusPlaybackActivity.java" 
 
.method public constructor <init>()V 
    .locals 0 
    invoke-direct {{p0}}, {parent_class}-><init>()V 
    return-void 
.end method 
 
.method public onCreate(Landroid/os/Bundle;)V 
    .locals 0 
    invoke-super {{p0, p1}}, {parent_class}->onCreate(Landroid/os/Bundle;)V 
    invoke-virtual {{p0}}, Landroid/app/Activity;->finish()V 
    return-void 
.end method 
""" 
        with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content) 
        print(f"    [+] StatusPlaybackActivity replaced with zombie shell.") 
        return True 
    except Exception as e: 
        print(f"    [-] Error nuking status activity: {e}") 
        return False 
 
# --------------------------------------------------------- 
# 7. הטיית הפניות לסטטוס 
# --------------------------------------------------------- 
def _patch_redirect_status_intents(root_dir): 
    target_status_class = "Lcom/whatsapp/status/playback/StatusPlaybackActivity;" 
    redirect_class = "Lcom/whatsapp/HomeActivity;"  
    alt_redirect_class = "Lcom/whatsapp/Main;" 
 
    print(f"\n[7] Redirecting Status Intents...") 
     
    home_exists = _find_file_recursive(root_dir, "HomeActivity.smali") 
    main_exists = _find_file_recursive(root_dir, "Main.smali") 
    final_redirect = redirect_class if home_exists else (alt_redirect_class if main_exists else None) 
     
    if not final_redirect: 
        print("    [-] Redirect target not found. Skipping redirection.") 
        return True  
 
    print(f"    [i] Redirecting to: {final_redirect}") 
     
    patched_count = 0 
    for root, dirs, files in os.walk(root_dir): 
        for file in files: 
            if file.endswith(".smali") and file != "StatusPlaybackActivity.smali": 
                path = os.path.join(root, file) 
                try: 
                    with open(path, 'r', encoding='utf-8') as f: content = f.read() 
                    if target_status_class in content: 
                        new_content = content.replace(target_status_class, final_redirect) 
                        with open(path, 'w', encoding='utf-8') as f: f.write(new_content) 
                        patched_count += 1 
                except: continue 
 
    print(f"    [+] Redirected {patched_count} references.") 
    return True 
 
# --------------------------------------------------------- 
# 8. אלגוריתם חכם ומוחלט לחסימת הגיפים (מבוסס חקר קוד) 
# --------------------------------------------------------- 
def _patch_gifs_tab(root_dir): 
    anchor = "ExpressionsKeyboardOpener = " 
    print(f"\n[8] Executing Surgical GIF Removal...") 
     
    target_file = _find_file_by_string(root_dir, anchor) 
    if not target_file: 
        print("    [-] File not found.") 
        return False 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: 
            lines = f.read().split('\n') 
             
        # 1. חילוץ כל המחלקות שנטענות למקלדת הטאבים
        pattern = re.compile(r"sget-object\s+[vp]\d+,\s+(LX/[A-Za-z0-9_]+;)->A00:\1") 
        classes = set() 
        for line in lines: 
            match = pattern.search(line) 
            if match: 
                cls = match.group(1) 
                if "0Jv" not in cls and "0N2" not in cls: 
                    classes.add(cls) 
                     
        # 2. פתיחת קבצי המחלקות וזיהוי מדויק של מחלקת הגיפים לפי המחרוזת "Gifs"
        gif_class = None 
         
        for cls in classes: 
            class_name = cls.split('/')[-1].replace(';', '') 
            smali_filename = f"{class_name}.smali" 
            full_path = _find_file_recursive(root_dir, smali_filename) 
             
            if full_path: 
                with open(full_path, 'r', encoding='utf-8') as smali_file: 
                    if '"Gifs"' in smali_file.read(): 
                        gif_class = cls 
                        break 
         
        if not gif_class: 
            print("    [-] Could not confidently identify GIF class.") 
            return False 
             
        print(f"    [+] Confirmed GIF class: {gif_class}") 
         
        # 3. יישום מעקף הכירורגיה (GOTO Bypass) רק על הגיפים!
        new_lines =[] 
        removed_count = 0 
         
        insert_after = {} 
        replace_line = {} 
         
        for i, line in enumerate(lines): 
            stripped = line.strip() 
             
            if "sget-object" in stripped and gif_class in stripped and "->A00" in stripped: 
                skip_label = f":skip_gif_kosher_{removed_count}" 
                removed_count += 1 
                 
                j = i + 1 
                while j < len(lines): 
                    next_stripped = lines[j].strip() 
                    # דילוג על שורות ריקות, הערות או שורות של labels (כדי לעטוף את ההוספה בזהירות)
                    if next_stripped == "" or next_stripped.startswith(".line") or next_stripped.startswith(":"): 
                        j += 1 
                        continue 
                         
                    # מצב 1: הוספה ישירה (הפקודה הבאה היא add)
                    if "invoke-virtual" in next_stripped and "->add(Ljava/lang/Object;)Z" in next_stripped: 
                        insert_after[i] = insert_after.get(i, []) + [f"    goto {skip_label} # Bypass GIF"] 
                        insert_after[j] = insert_after.get(j, []) + [f"    {skip_label}"] 
                        break 
                         
                    # מצב 2: קפיצה להוספה משותפת
                    if next_stripped.startswith("goto"): 
                        match = re.search(r"goto(?:/16|/32)?\s+(:[a-zA-Z0-9_]+)", next_stripped) 
                        if match: 
                            target_label = match.group(1) 
                            replace_line[j] = lines[j].replace(target_label, skip_label) + " # Redirected GIF" 
                             
                            # חיפוש התווית אליה קפצנו כדי לשתול שם את חזרת הדילוג
                            k = 0 
                            while k < len(lines): 
                                if lines[k].strip() == target_label: 
                                    m = k + 1 
                                    while m < len(lines): 
                                        m_stripped = lines[m].strip() 
                                        if "invoke-virtual" in m_stripped and "->add(Ljava/lang/Object;)Z" in m_stripped: 
                                            insert_after[m] = insert_after.get(m, []) +[f"    {skip_label}"] 
                                            break 
                                        m += 1 
                                    break 
                                k += 1 
                        break 
                    break 
                     
        # בנייה מחדש של הקובץ
        for i, line in enumerate(lines): 
            if i in replace_line: 
                new_lines.append(replace_line[i]) 
            else: 
                new_lines.append(line) 
                 
            if i in insert_after: 
                new_lines.extend(insert_after[i]) 
                 
        if removed_count > 0: 
            with open(target_file, 'w', encoding='utf-8') as f: 
                f.write('\n'.join(new_lines)) 
            print(f"    [+] Successfully bypassed {removed_count} GIF additions!") 
            return True 
        else: 
            print("    [-] Failed to patch, no additions found.") 
            return False 
             
    except Exception as e: 
        print(f"    [-] Error patching GIF tab: {e}") 
        return False
# --------------------------------------------------------- 
# 9. מעקף חכם לקריסת MimeType של מערכת ההפעלה 
# --------------------------------------------------------- 
def _patch_mime_type_crash(root_dir): 
    anchor_string = "SecureFileBuilder" 
    print(f"\n[9] Scanning for SecureFile OS Crash Trigger ({anchor_string})...") 
 
    target_file = _find_file_by_string(root_dir, anchor_string) 
    if not target_file: 
        print(f"    [-] Target file containing '{anchor_string}' not found. Skipping.") 
        return True 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read() 
 
        # Regex חכם וכללי יותר: 
        # תופס קריאות static ו-virtual.
        # תופס כל אחת מהפונקציות המוכרות שגורמות לקריסות במכשירי נטפרי.
        regex_pattern = r"(invoke-(?:virtual|static)(?:/range)?\s*\{[^}]+\},\s*Landroid/webkit/MimeTypeMap;->(?:getMimeTypeFromExtension|getExtensionFromMimeType|getFileExtensionFromUrl)\(Ljava/lang/String;\)Ljava/lang/String;.*?move-result-object\s+([vp]\d+))" 
 
        if re.search(regex_pattern, content, re.DOTALL): 
            safe_replacement = r"const/4 \2, 0x0 # Bypassed OS Crash (Kosher Patch)" 
            new_content, count = re.subn(regex_pattern, safe_replacement, content, flags=re.DOTALL) 
             
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content) 
            print(f"    [+] Successfully neutralized {count} OS MimeType queries in {os.path.basename(target_file)}") 
            return True 
        else: 
            print("    [-] File found, but API call signature did not match.") 
            return False 
    except Exception as e: 
        print(f"    [-] Error patching MimeType crash: {e}") 
        return False

def extract_original_signature(apk_path: str) -> str:
    """מחלץ את החתימה המקורית של וואטסאפ מתוך ה-APK לפני הפירוק"""
    print("    [*] Extracting original WhatsApp signature...")
    with zipfile.ZipFile(apk_path, 'r') as zf:
        # חפש את קובץ האישור בתיקיית META-INF
        cert_files =[f for f in zf.namelist() if f.startswith('META-INF/') and (f.endswith('.DSA') or f.endswith('.RSA'))]
        if not cert_files:
            raise Exception("Could not find .DSA or .RSA certificate in original APK")
        cert_data = zf.read(cert_files[0])

    # המרת האישור למחרוזת HEX (בדיוק כמו ש-Schwartzblat עושה)
    der_cert = pkcs7.load_der_pkcs7_certificates(cert_data)[0]
    bytes_signature = der_cert.public_bytes(serialization.Encoding.DER)
    signature_hex = bytes_signature.hex()
    
    # נוודא שהמחרוזת זוגית
    formatted_signature = "".join([hex(b).split("x")[-1].zfill(2) for b in bytes_signature])
    return formatted_signature

def _patch_signature_bypass(decompiled_dir: str) -> bool:
    print("\n[*] Injecting Static Signature Bypass...")
    
    # 1. חילוץ החתימה מה-APK המקורי
    original_apk = "latest.apk"
    if not os.path.exists(original_apk):
        print("    [-] latest.apk not found. Cannot extract signature.")
        return False
        
    try:
        signature_hex = extract_original_signature(original_apk)
        print("    [+] Signature extracted successfully.")
    except Exception as e:
        print(f"    [-] Failed to extract signature: {e}")
        return False

    # 2. סריקה והחלפה של כל הקריאות ל-getPackageInfo בכל הקוד של וואטסאפ
    # (אנחנו עושים את זה *לפני* יצירת הקובץ שלנו כדי לא ליצור לולאה אינסופית!)
    print("    [*] Redirecting getPackageInfo calls to SigBypass...")
    
    pattern = re.compile(
        r"invoke-virtual\s*\{([vp]\d+),\s*([vp]\d+),\s*([vp]\d+)\},\s*Landroid/content/pm/PackageManager;->getPackageInfo\(Ljava/lang/String;I\)Landroid/content/pm/PackageInfo;"
    )
    
    patched_count = 0
    for root_path, _, files in os.walk(decompiled_dir):
        for file in files:
            if file.endswith(".smali"):
                full_path = os.path.join(root_path, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if "Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)" in content:
                        new_content, subs = pattern.subn(
                            r"invoke-static {\1, \2, \3}, Lcom/whatsapp/kosher/SigBypass;->getPackageInfo(Landroid/content/pm/PackageManager;Ljava/lang/String;I)Landroid/content/pm/PackageInfo;",
                            content
                        )
                        if subs > 0:
                            with open(full_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            patched_count += subs
                except Exception:
                    continue
                    
    print(f"    [+] Successfully redirected {patched_count} calls to signature bypass.")

    # 3. רק עכשיו ניצור את מחלקת ה-Smali שלנו
    smali_dir = os.path.join(decompiled_dir, "smali_classes2", "com", "whatsapp", "kosher")
    os.makedirs(smali_dir, exist_ok=True)
    
    bypass_smali_path = os.path.join(smali_dir, "SigBypass.smali")
    
    smali_code = f"""
.class public Lcom/whatsapp/kosher/SigBypass;
.super Ljava/lang/Object;

.method public static getPackageInfo(Landroid/content/pm/PackageManager;Ljava/lang/String;I)Landroid/content/pm/PackageInfo;
    .registers 7
    .annotation system Ldalvik/annotation/Throws;
        value = {{
            Landroid/content/pm/PackageManager$NameNotFoundException;
        }}
    .end annotation

    # קריאה לפונקציה המקורית
    invoke-virtual {{p0, p1, p2}}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;
    move-result-object v0

    # אם חזר null, נחזיר null
    if-nez v0, :not_null
    return-object v0

    :not_null
    # נוודא שמדובר בוואטסאפ
    const-string v1, "com.whatsapp.kosher"
    invoke-virtual {{v1, p1}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :is_whatsapp
    return-object v0

    :is_whatsapp
    # יצירת אובייקט חתימה מזויף עם החתימה המקורית
    new-instance v1, Landroid/content/pm/Signature;
    const-string v2, "{signature_hex}"
    invoke-direct {{v1, v2}}, Landroid/content/pm/Signature;-><init>(Ljava/lang/String;)V

    # הזרקת החתימה
    const/4 v2, 0x1
    new-array v2, v2,[Landroid/content/pm/Signature;
    const/4 v3, 0x0
    aput-object v1, v2, v3
    iput-object v2, v0, Landroid/content/pm/PackageInfo;->signatures:[Landroid/content/pm/Signature;

    # איפוס signingInfo (אנדרואיד 9+)
    const/4 v1, 0x0
    iput-object v1, v0, Landroid/content/pm/PackageInfo;->signingInfo:Landroid/content/pm/SigningInfo;

    return-object v0
.end method
"""
    with open(bypass_smali_path, 'w', encoding='utf-8') as f:
        f.write(smali_code.strip())
    print("    [+] Injected SigBypass.smali")

    return patched_count > 0

# --------------------------------------------------------- 
# פונקציות עזר 
# --------------------------------------------------------- 
def _find_file_by_string(root_dir, search_string): 
    for root, dirs, files in os.walk(root_dir): 
        for file in files: 
            if file.endswith(".smali"): 
                path = os.path.join(root, file) 
                try: 
                    with open(path, 'r', encoding='utf-8') as f: 
                        if search_string in f.read(): 
                            return path 
                except: 
                    continue 
    return None 
 
def _find_file_recursive(root_dir, filename): 
    for root, dirs, files in os.walk(root_dir): 
        if filename in files: 
            return os.path.join(root, filename) 
    return None

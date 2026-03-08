import os 
import re 
 
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
 
    results = [photos, newsletter, tabs, spi, browser, status_nuke, status_redirect, gifs_tab] 
     
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
# 8. אלגוריתם חכם ודינאמי לחסימת הגיפים (Line-by-Line Parser) 
# --------------------------------------------------------- 
def _patch_gifs_tab(root_dir): 
    anchor = "ExpressionsKeyboardOpener = " 
    print(f"\n[8] Executing Smart GIF Tab Removal ({anchor})...") 
     
    target_file = _find_file_by_string(root_dir, anchor) 
    if not target_file: 
        print("    [-] ExpressionsTrayTabHandler file not found.") 
        return False 
 
    try: 
        with open(target_file, 'r', encoding='utf-8') as f: 
            lines = f.read().split('\n') 
             
        # 1. זיהוי דינאמי של מחלקת הגיפים על ידי חיפוש האחורה מהלייבל הראשי 
        gif_class = None 
        for i, line in enumerate(lines): 
            # שינוי: מחפש כל goto ולא רק goto_0
            if "goto :goto_" in line: 
                # שינוי: סורק לאחור עד 15 שורות (במקום 6) למקרה שהקוד התרחק
                for j in range(i-1, max(-1, i-15), -1): 
                    if "sget-object" in lines[j]: 
                        match = re.search(r"(LX/[a-zA-Z0-9_]+;)->A00", lines[j]) 
                        if match: 
                            gif_class = match.group(1) 
                        break 
                if gif_class:
                    break 
                 
        if not gif_class: 
            print("    [-] Could not dynamically identify GIF class.") 
            print("    [DEBUG] הדפסת 150 שורות ראשונות של הקובץ לטובת דיבאג:")
            print("    " + "="*40)
            for idx, debug_line in enumerate(lines[:150]):
                print(f"    {idx:03d}: {debug_line.strip()}")
            print("    " + "="*40)
            return False 
             
        print(f"[i] Identified GIF class automatically: {gif_class}") 
         
        new_lines =[] 
        patch_goto_targets =[] 
        removed_count = 0 
        i = 0 
         
        # 2. מעבר שורה-שורה כמו קומפיילר ושינוי מבנה הקוד 
        while i < len(lines): 
            line = lines[i] 
             
            # אם מצאנו טעינה של מחלקת הגיפים למשתנה 
            if "sget-object" in line and gif_class in line: 
                j = i + 1 
                has_goto = False 
                has_label = False 
                add_index = -1 
                target_goto = None 
                 
                # סורקים קדימה כדי לראות לאן הבלוק הזה מוביל 
                while j < len(lines): 
                    ahead_line = lines[j] 
                    if "goto " in ahead_line and not has_label and add_index == -1: 
                        has_goto = True 
                        target_goto = ahead_line.strip().split(" ")[1] # חילוץ שם הקפיצה (כמו :goto_0) 
                        break 
                    if ahead_line.strip().startswith(":") and "goto " not in ahead_line: 
                        has_label = True 
                    if "invoke-virtual" in ahead_line and "->add(Ljava/lang/Object;)Z" in ahead_line: 
                        add_index = j 
                        break 
                    j += 1 
                     
                if has_goto and target_goto: 
                    # מקרה 1: קפיצה משותפת (כמו ב-Opener 11) - מזריקים קפיצה שעוקפת את הגיפים 
                    skip_label = f":skip_gif_target_{i}" 
                    new_lines.append(f"    goto {skip_label} # Bypassed GIF Addition") 
                    patch_goto_targets.append((target_goto, skip_label)) 
                    removed_count += 1 
                    while i <= j: i += 1 # מדלגים על הקוד המקורי 
                    continue 
                     
                elif add_index != -1: 
                    if has_label: 
                        # מקרה 2: הוספה עם לייבל באמצע (כמו :goto_5) - עוקפים את ההוספה בזהירות 
                        skip_label = f":skip_gif_target_{i}" 
                        new_lines.append(f"    goto {skip_label} # Bypassed inline GIF Addition") 
                        i_orig = i 
                        while i <= add_index: 
                            if i != i_orig: new_lines.append(lines[i]) # משאירים את הלייבל המקורי 
                            i += 1 
                        new_lines.append(f"    {skip_label}") 
                        removed_count += 1 
                        continue 
                    else: 
                        # מקרה 3: הוספה רגילה רציפה - פשוט מוחקים הכל 
                        new_lines.append("    # Removed standard GIF array addition") 
                        i = add_index + 1 
                        removed_count += 1 
                        continue 
                         
            new_lines.append(line) 
            i += 1 
             
        # 3. השתלת תוויות המעקף עבור המקרה הראשון (כמו Opener 11) לאחר פקודות ההוספה המשותפות 
        for tgt, skip_lbl in patch_goto_targets: 
            for idx, line in enumerate(new_lines): 
                if line.strip() == tgt: 
                    # מצאנו את הלייבל, עכשיו נחפש את ה-add הראשון שאחריו 
                    for k in range(idx+1, len(new_lines)): 
                        if "invoke-virtual" in new_lines[k] and "->add(" in new_lines[k]: 
                            new_lines.insert(k+1, f"    {skip_lbl}") 
                            break 
                    break 
                     
        print(f"    [+] Successfully neutralized {removed_count} GIF tab initializations.") 
         
        with open(target_file, 'w', encoding='utf-8') as f: 
            f.write('\n'.join(new_lines)) 
             
        return True 
         
    except Exception as e: 
        print(f"    [-] Error patching GIF tab: {e}") 
        return False 
 
 
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

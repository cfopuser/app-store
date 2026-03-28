import os
import re

# --- הגדרות ---
# קוד ה-JS הגולמי להזרקה ב-WebView של יוטיוב מיוזיק
JS_PAYLOAD = r'''javascript:(function(){function cleanPage(){const footer=document.querySelector('footer');if(footer)footer.remove();const langSelector=document.querySelector('[jscontroller="xiZRqc"]');if(langSelector)langSelector.remove();const guestModeDiv=document.querySelector('.RDsYTb');if(guestModeDiv)guestModeDiv.remove();document.querySelectorAll('ytmusic-player-page, ytmusic-player-bar[slot="player-bar"], #mini-guide, #guide, ytmusic-nav-bar .left-content, ytmusic-nav-bar .center-content').forEach(element=>{element.style.setProperty('display','none','important')});const navBarRight=document.querySelector('ytmusic-nav-bar .right-content');if(navBarRight){navBarRight.style.setProperty('margin-left','auto','important')}const popup=document.querySelector('tp-yt-iron-dropdown');if(popup&&popup.style.display!=='none'){const header=popup.querySelector('ytd-active-account-header-renderer');if(header)header.style.setProperty('display','none','important');popup.querySelectorAll('yt-multi-page-menu-section-renderer').forEach(section=>{if(!section.querySelector('a[href="/logout"]')){section.style.setProperty('display','none','important')}else{section.querySelectorAll('ytd-compact-link-renderer').forEach(item=>{if(!item.contains(section.querySelector('a[href="/logout"]'))){item.style.setProperty('display','none','important')}})}})}const immersiveBackground=document.querySelector('#background.immersive-background');if(immersiveBackground){immersiveBackground.style.setProperty('display','none','important')}const chipContainer=document.querySelector('ytmusic-chip-cloud-renderer');if(chipContainer){chipContainer.style.setProperty('display','none','important')}const allShelves=document.querySelectorAll('ytmusic-carousel-shelf-renderer');allShelves.forEach((shelf,index)=>{if(index===0){const carousel=shelf.querySelector('#ytmusic-carousel');if(carousel)carousel.style.setProperty('display','none','important');const header=shelf.querySelector('ytmusic-carousel-shelf-basic-header-renderer');if(header){const strapline=header.querySelector('.strapline');if(strapline)strapline.style.setProperty('display','none','important');const buttonGroup=header.querySelector('#button-group');if(buttonGroup)buttonGroup.style.setProperty('display','none','important')}const navButtons=shelf.querySelector('.button-group.style-scope.ytmusic-carousel-shelf-renderer');if(navButtons)navButtons.style.setProperty('display','none','important')}else{shelf.style.setProperty('display','none','important')}});const tastebuilder=document.querySelector('ytmusic-tastebuilder-shelf-renderer');if(tastebuilder){tastebuilder.style.setProperty('display','none','important')}const titleElement=document.querySelector('ytmusic-carousel-shelf-renderer yt-formatted-string.title');if(titleElement){const newText='אם זאת פעם ראשונה שאתם נכנסים, אתם יכולים לחזור כעת לאפליקציה (מומלץ לסגור לגמרי את האפליקציה ולפתוח מחדש, כדי שהיא תקלוט שנכנסתם), אם כבר הייתם מחוברים ואתם רוצים להחליף חשבון, צאו מהחשבון (לחיצה על העיגול) והתחילו מחדש את התהליך.';if(titleElement.textContent!==newText){titleElement.textContent=newText;titleElement.style.setProperty('direction','rtl','important');titleElement.style.setProperty('white-space','normal','important');titleElement.style.setProperty('text-overflow','clip','important');titleElement.style.setProperty('overflow','visible','important');titleElement.style.setProperty('height','auto','important');titleElement.style.setProperty('font-size','16px','important');titleElement.style.setProperty('font-weight','normal','important');titleElement.style.setProperty('line-height','1.5','important');titleElement.style.setProperty('color','white','important')}}}cleanPage();const observer=new MutationObserver(()=>{cleanPage()});observer.observe(document.body,{childList:true,subtree:true})})();'''

# הכנת ה-JS להזרקה ב-Smali
ESCAPED_JS = JS_PAYLOAD.replace('"', r'\"')

# קוד Smali לחסימת תמונות ב-WebView של ספוטיפיי (עם תמיכה בפורמט משתנים)
IMAGE_BLOCK_SMALI = """
    # --- START OF IMAGE BLOCKING INJECTION ---
    const/4 {scratch_reg}, 0x1
    invoke-virtual {{{settings_reg}, {scratch_reg}}}, Landroid/webkit/WebSettings;->setBlockNetworkImage(Z)V
    const/4 {scratch_reg}, 0x0
    invoke-virtual {{{settings_reg}, {scratch_reg}}}, Landroid/webkit/WebSettings;->setLoadsImagesAutomatically(Z)V
    # --- END OF IMAGE BLOCKING INJECTION ---"""

# קוד Smali לסינון כתובות בהתחברות (עם משתנה חילוץ URL דינמי)
SPOTIFY_FILTER_SMALI = """
    # --- START OF CUSTOM FILTER & LOGGER ---
    const-string v1, "MELD_FILTER"
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {{v2}}, Ljava/lang/StringBuilder;-><init>()V
    const-string v3, ">>> Trying to load: "
    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{v2, {url_reg}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{v2}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-static {{v1, v2}}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    const-string v1, "accounts.spotify.com"
    invoke-virtual {{{url_reg}, v1}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :meld_check_2
    goto :meld_allow_url

    :meld_check_2
    const-string v1, "open.spotify.com"
    invoke-virtual {{{url_reg}, v1}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :meld_check_3
    goto :meld_allow_url

    :meld_check_3
    const-string v1, "accounts.google.com"
    invoke-virtual {{{url_reg}, v1}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :meld_check_4
    goto :meld_allow_url

    :meld_check_4
    const-string v1, "appleid.apple.com"
    invoke-virtual {{{url_reg}, v1}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :meld_check_5
    goto :meld_allow_url

    :meld_check_5
    const-string v1, "challenge.spotify.com"
    invoke-virtual {{{url_reg}, v1}}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :meld_block_url
    goto :meld_allow_url

    :meld_block_url
    const-string v1, "MELD_FILTER"
    const-string v2, ">>> BLOCKED!"
    invoke-static {{v1, v2}}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I
    const/4 v0, 0x1
    return v0

    :meld_allow_url
    const-string v1, "MELD_FILTER"
    const-string v2, ">>> ALLOWED!"
    invoke-static {{v1, v2}}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I
    # --- END OF CUSTOM FILTER & LOGGER ---
"""


def patch(decompiled_dir: str) -> bool:
    """
    Apply the 'MetroList Kosher' patch dynamically.
    """
    print("[*] Starting MetroList 'Kosher' patch...")
    
    # 1. חסימת תמונות קטנות (Thumbnails)
    if not _patch_thumbnail(decompiled_dir):
        print("[-] Warning: Failed to patch Thumbnail.smali. Continuing...")
    
    # 2. הזרקת JS וחסימת תמונות ב-WebView של YouTube
    yt_webview_client = _find_webview_client_target(decompiled_dir)
    if yt_webview_client:
        _patch_webview(yt_webview_client)
    else:
        print("[-] Warning: YouTube WebViewClient not found.")

    # 3. חסימת תמונות ב-WebView של התחברות ספוטיפיי
    _patch_spotify_ui_image_block(decompiled_dir)

    # 4. הזרקת חומת האש (URL Whitelist) ל-WebViewClient של ספוטיפיי
    _patch_spotify_login_filter(decompiled_dir)
        
    print("[+] MetroList patch applied successfully.")
    return True

# --- פונקציות עזר פנימיות ---

def _patch_thumbnail(root_dir):
    print("[*] Searching for Thumbnail.smali to block image URLs...")
    for root, dirs, files in os.walk(root_dir):
        if "Thumbnail.smali" in files and "metrolist" in root and "models" in root:
            target_path = os.path.join(root, "Thumbnail.smali")
            try:
                with open(target_path, 'r', encoding='utf-8') as f: content = f.read()
                pattern = r'(iput-object p2, p0, Lcom/metrolist/innertube/models/Thumbnail;->(?:a|url):Ljava/lang/String;)'
                if re.search(pattern, content):
                    new_content = re.sub(pattern, r'const-string p2, ""\n    \1', content)
                    with open(target_path, 'w', encoding='utf-8') as f: f.write(new_content)
                    print("[+] Thumbnail.smali: URL loading blocked.")
                    return True
            except Exception as e:
                print(f"[-] Error patching Thumbnail.smali: {e}")
            return False
    return False

def _find_webview_client_target(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if 'VISITOR_DATA' in f.read():
                            return path
                except: pass
    return None

def _patch_webview(file_path):
    print(f"[*] Patching YouTube WebViewClient file: {os.path.basename(file_path)}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        class_match = re.search(r'\.class .*? (L[^;]+;)', content)
        field_match = re.search(r'\.field .*? ([^: ]+):Landroid/webkit/WebView;', content)
        
        if class_match and field_match:
            class_desc, field_view = class_match.group(1), field_match.group(1)
            if "setLoadsImagesAutomatically" not in content:
                super_call = r'(invoke-direct \{p0\}, Landroid/webkit/WebViewClient;-><init>\(\)V)'
                constructor_code = """
    invoke-virtual {p1}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v0
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/webkit/WebSettings;->setLoadsImagesAutomatically(Z)V"""
                content = re.sub(super_call, r'\1' + constructor_code, content, count=1)

            original_js_call = 'const-string p1, "javascript:Android.onRetrieveVisitorData'
            if original_js_call in content and f'const-string v1, "{ESCAPED_JS[:20]}' not in content:
                js_injection_block = f"""
    const-string v1, "{ESCAPED_JS}"
    iget-object v2, p0, {class_desc}->{field_view}:Landroid/webkit/WebView;
    invoke-virtual {{v2, v1}}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
"""
                content = content.replace(original_js_call, js_injection_block + "\n    " + original_js_call)
                print("[+] Injected cleaning JavaScript into onPageFinished.")
            
            with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
            return True
    except Exception as e:
        print(f"[-] Error in YouTube WebView patch: {e}")
    return False

def _patch_spotify_ui_image_block(root_dir):
    print("[*] Searching for Spotify UI to block images...")
    target_file = None
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '"https://accounts.spotify.com' in content and 'setUserAgentString' in content:
                            target_file = path
                            break
                except: pass
        if target_file: break
            
    if not target_file:
        print("[-] Could not find Spotify UI definition file.")
        return False
        
    print(f"[+] Found Spotify UI file: {os.path.basename(target_file)}")
    with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
        
    # מחלץ דינמית את האוגר של WebSettings ואוגר זמני מהקוד המקורי
    pattern = r'(invoke-virtual \{([vp]\d+), ([vp]\d+)\}, Landroid/webkit/WebSettings;->setUserAgentString\(Ljava/lang/String;\)V)'
    match = re.search(pattern, content)
    
    if match:
        full_line = match.group(1)
        settings_reg = match.group(2)
        scratch_reg = match.group(3)
        
        if "setBlockNetworkImage" not in content:
            injection = IMAGE_BLOCK_SMALI.format(settings_reg=settings_reg, scratch_reg=scratch_reg)
            new_content = content.replace(full_line, full_line + "\n" + injection)
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
            print("[+] Image blocking injected into Spotify Login UI.")
            return True
        else:
            print("[i] Image blocking already present in Spotify UI. Skipping.")
            return True
    return False

def _patch_spotify_login_filter(root_dir):
    print("[*] Searching for Spotify WebViewClient to inject URL filter...")
    target_file = None
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if '"SpotifyLogin: navigating to: "' in f.read():
                            target_file = path
                            break
                except: pass
        if target_file: break
    
    if not target_file:
        print("[-] Could not find Spotify WebViewClient file.")
        return False

    print(f"[+] Found Spotify WebViewClient: {os.path.basename(target_file)}")
    with open(target_file, 'r', encoding='utf-8') as f: content = f.read()

    # מאתר את בלוק ההדפסה המקורי כדי לחלץ את האוגר המכיל את כתובת ה-URL, ולדעת היכן להזריק
    pattern = r'(const-string[vp]\d+, "SpotifyLogin: navigating to: "(?:.*?)invoke-virtual \{[vp]\d+, ([vp]\d+)\}, Ljava/lang/String;->concat\(Ljava/lang/String;\)Ljava/lang/String;.*?)(const-string [vp]\d+, "https://open\.spotify\.com")'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        url_reg = match.group(2) # חילוץ האוגר (למשל p2)
        
        if "MELD_FILTER" not in content:
            injection = SPOTIFY_FILTER_SMALI.format(url_reg=url_reg)
            # הזרקה בדיוק לפני הבדיקה המקורית של ספוטיפיי
            new_content = content[:match.start(3)] + injection + content[match.start(3):]
            with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
            print(f"[+] Spotify URL whitelist filter injected (Using URL register: {url_reg}).")
            return True
        else:
            print("[i] Spotify URL filter already injected. Skipping.")
            return True
    else:
        print("[-] Could not map injection points for the URL filter.")
        return False

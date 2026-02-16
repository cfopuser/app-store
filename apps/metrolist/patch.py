import os
import re

# --- הגדרות ---
# קוד ה-JS הגולמי להזרקה ב-WebView
JS_PAYLOAD = r'''javascript:(function(){function cleanPage(){const footer=document.querySelector('footer');if(footer)footer.remove();const langSelector=document.querySelector('[jscontroller="xiZRqc"]');if(langSelector)langSelector.remove();const guestModeDiv=document.querySelector('.RDsYTb');if(guestModeDiv)guestModeDiv.remove();document.querySelectorAll('ytmusic-player-page, ytmusic-player-bar[slot="player-bar"], #mini-guide, #guide, ytmusic-nav-bar .left-content, ytmusic-nav-bar .center-content').forEach(element=>{element.style.setProperty('display','none','important')});const navBarRight=document.querySelector('ytmusic-nav-bar .right-content');if(navBarRight){navBarRight.style.setProperty('margin-left','auto','important')}const popup=document.querySelector('tp-yt-iron-dropdown');if(popup&&popup.style.display!=='none'){const header=popup.querySelector('ytd-active-account-header-renderer');if(header)header.style.setProperty('display','none','important');popup.querySelectorAll('yt-multi-page-menu-section-renderer').forEach(section=>{if(!section.querySelector('a[href="/logout"]')){section.style.setProperty('display','none','important')}else{section.querySelectorAll('ytd-compact-link-renderer').forEach(item=>{if(!item.contains(section.querySelector('a[href="/logout"]'))){item.style.setProperty('display','none','important')}})}})}const immersiveBackground=document.querySelector('#background.immersive-background');if(immersiveBackground){immersiveBackground.style.setProperty('display','none','important')}const chipContainer=document.querySelector('ytmusic-chip-cloud-renderer');if(chipContainer){chipContainer.style.setProperty('display','none','important')}const allShelves=document.querySelectorAll('ytmusic-carousel-shelf-renderer');allShelves.forEach((shelf,index)=>{if(index===0){const carousel=shelf.querySelector('#ytmusic-carousel');if(carousel)carousel.style.setProperty('display','none','important');const header=shelf.querySelector('ytmusic-carousel-shelf-basic-header-renderer');if(header){const strapline=header.querySelector('.strapline');if(strapline)strapline.style.setProperty('display','none','important');const buttonGroup=header.querySelector('#button-group');if(buttonGroup)buttonGroup.style.setProperty('display','none','important')}const navButtons=shelf.querySelector('.button-group.style-scope.ytmusic-carousel-shelf-renderer');if(navButtons)navButtons.style.setProperty('display','none','important')}else{shelf.style.setProperty('display','none','important')}});const tastebuilder=document.querySelector('ytmusic-tastebuilder-shelf-renderer');if(tastebuilder){tastebuilder.style.setProperty('display','none','important')}const titleElement=document.querySelector('ytmusic-carousel-shelf-renderer yt-formatted-string.title');if(titleElement){const newText='אם זאת פעם ראשונה שאתם נכנסים, אתם יכולים לחזור כעת לאפליקציה (מומלץ לסגור לגמרי את האפליקציה ולפתוח מחדש, כדי שהיא תקלוט שנכנסתם), אם כבר הייתם מחוברים ואתם רוצים להחליף חשבון, צאו מהחשבון (לחיצה על העיגול) והתחילו מחדש את התהליך.';if(titleElement.textContent!==newText){titleElement.textContent=newText;titleElement.style.setProperty('direction','rtl','important');titleElement.style.setProperty('white-space','normal','important');titleElement.style.setProperty('text-overflow','clip','important');titleElement.style.setProperty('overflow','visible','important');titleElement.style.setProperty('height','auto','important');titleElement.style.setProperty('font-size','16px','important');titleElement.style.setProperty('font-weight','normal','important');titleElement.style.setProperty('line-height','1.5','important');titleElement.style.setProperty('color','white','important')}}}cleanPage();const observer=new MutationObserver(()=>{cleanPage()});observer.observe(document.body,{childList:true,subtree:true})})();'''

# הכנת ה-JS להזרקה ב-Smali (בריחה מגרשיים)
ESCAPED_JS = JS_PAYLOAD.replace('"', r'\"')


def patch(decompiled_dir: str) -> bool:
    """
    Apply the 'MetroList Kosher' patch.
    - Blocks thumbnail URLs.
    - Injects JavaScript into the login WebView to bypass login and clean the UI.
    - Disables image loading in the WebView.
    """
    print("[*] Starting MetroList 'Kosher' patch...")
    
    # 1. חסימת תמונות קטנות (Thumbnails) ברמת האפליקציה
    thumbnail_patched = _patch_thumbnail(decompiled_dir)
    
    # 2. חיפוש דינמי של קובץ ה-WebViewClient הרלוונטי
    webview_client_file = _find_webview_client_target(decompiled_dir)
    
    if not webview_client_file:
        print("[-] CRITICAL: Could not find the target WebViewClient file (containing 'VISITOR_DATA'). Patch failed.")
        return False

    # 3. הזרקת JS וחסימת תמונות ב-WebView
    webview_patched = _patch_webview(webview_client_file)

    if not webview_patched:
        print("[-] CRITICAL: Failed to patch the WebViewClient file. Patch failed.")
        return False
        
    print(f"[i] Thumbnail patch status: {'Success' if thumbnail_patched else 'Skipped/Failed'}")
    print("[+] MetroList patch applied successfully.")
    return True

# --- פונקציות עזר פנימיות ---

def _patch_thumbnail(root_dir):
    """חוסם טעינת תמונות קטנות על ידי החלפת ה-URL במחרוזת ריקה."""
    print("[*] Searching for Thumbnail.smali to block image URLs...")
    for root, dirs, files in os.walk(root_dir):
        if "Thumbnail.smali" in files and "metrolist" in root and "models" in root:
            target_path = os.path.join(root, "Thumbnail.smali")
            try:
                with open(target_path, 'r', encoding='utf-8') as f: content = f.read()
                
                pattern = r'(iput-object p2, p0, Lcom/metrolist/innertube/models/Thumbnail;->a:Ljava/lang/String;)'
                if re.search(pattern, content):
                    new_content = re.sub(pattern, r'const-string p2, ""\n    \1', content)
                    with open(target_path, 'w', encoding='utf-8') as f: f.write(new_content)
                    print("[+] Thumbnail.smali: URL loading blocked.")
                    return True
                else:
                    print("[-] Thumbnail.smali: Pattern not found inside the file.")
                    
            except Exception as e:
                print(f"[-] Error patching Thumbnail.smali: {e}")
            return False
    
    print("[i] Thumbnail.smali not found, skipping this part.")
    return False

def _find_webview_client_target(root_dir):
    """מוצא את קובץ ה-Smali שמטפל בלוגיקת ה-WebView על ידי חיפוש מילת מפתח ייחודית."""
    print("[*] Scanning for the correct WebViewClient file using 'VISITOR_DATA' keyword...")
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if 'VISITOR_DATA' in f.read():
                            print(f"[+] Found target WebViewClient file: {file}")
                            return path
                except (IOError, UnicodeDecodeError):
                    pass # קבצים מסוימים עלולים להיכשל בקריאה
    return None

def _patch_webview(file_path):
    """מבצע את השינויים בקובץ ה-WebViewClient: חוסם תמונות ומזריק JS."""
    print(f"[*] Patching WebViewClient file: {os.path.basename(file_path)}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        
        # 1. חילוץ דינמי של שם המחלקה ושדה ה-WebView
        class_match = re.search(r'\.class .*? (L[^;]+;)', content)
        field_match = re.search(r'\.field .*? ([^: ]+):Landroid/webkit/WebView;', content)
        
        if not (class_match and field_match):
            print("[-] Could not dynamically identify Class Name or WebView Field in the target file.")
            return False
        
        class_desc = class_match.group(1)
        field_view = field_match.group(1)
        print(f"[i] Identified -> Class: {class_desc}, Field: {field_view}")

        # 2. הזרקת קוד לחסימת תמונות ב-Constructor
        if "setLoadsImagesAutomatically" not in content:
            constructor_code = """
    invoke-virtual {p1}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v0
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/webkit/WebSettings;->setLoadsImagesAutomatically(Z)V"""
            
            # מוצא את סוף ה-constructor ומזריק לפניו
            super_call = r'(invoke-direct \{p0\}, Landroid/webkit/WebViewClient;-><init>\(\)V)'
            if re.search(super_call, content):
                content = re.sub(super_call, r'\1' + constructor_code, content, count=1)
                print("[+] Injected image blocking code into constructor.")
            else:
                print("[-] Could not find super constructor call to inject image blocking code.")
                return False

        # 3. הזרקת קוד JS ב-onPageFinished
        js_injection_block = f"""
    const-string v1, "{ESCAPED_JS}"
    iget-object v2, p0, {class_desc}->{field_view}:Landroid/webkit/WebView;
    invoke-virtual {{v2, v1}}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
"""
        # מוצא את השורה שמפעילה JS אחר, ומזריק את הקוד שלנו לפניה
        original_js_call = 'const-string p1, "javascript:Android.onRetrieveVisitorData'
        
        if original_js_call in content:
            # מונע הזרקה כפולה אם הפאץ' כבר רץ
            if f'const-string v1, "{ESCAPED_JS[:20]}' not in content:
                content = content.replace(original_js_call, js_injection_block + "\n    " + original_js_call)
                print("[+] Injected cleaning JavaScript into onPageFinished.")
            else:
                print("[i] Cleaning JavaScript already present. Skipping injection.")
        else:
            print("[-] Could not find 'onRetrieveVisitorData' call to inject JavaScript.")
            return False
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    except Exception as e:
        print(f"[-] An error occurred while patching the WebView file: {e}")
        return False

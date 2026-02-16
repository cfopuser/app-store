import os
import re

def patch(decompiled_dir: str) -> bool:
    """
    Spotify Patch:
    1. Block Images (EsImage$ImageData -> getData returns null)
    2. Block Video (VideoSurfaceView -> getTextureView returns null)
    3. Block Share Image (Delete ShareHouseKeepingWorker)
    """
    
    # מונים למעקב אחר הצלחת הפעולות
    patches_applied = {
        "images": False,
        "video": False,
        "share_worker": False
    }

    print(f"[*] Scanning for Spotify target files in {decompiled_dir}...")

    for root, dirs, files in os.walk(decompiled_dir):
        
        # --- 3. מחיקת ShareHouseKeepingWorker ---
        if "ShareHouseKeepingWorker.smali" in files:
            file_path = os.path.join(root, "ShareHouseKeepingWorker.smali")
            try:
                os.remove(file_path)
                print(f"[+] Deleted ShareHouseKeepingWorker at: {file_path}")
                patches_applied["share_worker"] = True
            except Exception as e:
                print(f"[-] Failed to delete ShareHouseKeepingWorker: {e}")

        # --- 1. חסימת תמונות (EsImage$ImageData) ---
        if "EsImage$ImageData.smali" in files:
            file_path = os.path.join(root, "EsImage$ImageData.smali")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # חיפוש הפונקציה getData שמחזירה אובייקט כלשהו (L...;)
                # המדריך: לשנות ל-return null (0x0)
                # Regex גמיש שמתעלם משמות משתנים (v0, p0) וסוגי החזרה משתנים (Obfuscation)
                pattern_img = re.compile(
                    r"(\.method public final getData\(\)L.*?;.*?)(\.line \d+.*?iget-object [vp]\d+, [vp]\d+, Lcom\/spotify\/image\/esperanto\/proto\/EsImage\$ImageData;->.*?:L.*?;)(.*?.end method)",
                    re.DOTALL
                )
                
                if pattern_img.search(content):
                    # מחליף את גוף הפונקציה ב-return null
                    new_content = pattern_img.sub(r"\1\n    const/4 v0, 0x0\n    return-object v0\n\3", content)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"[+] Patched EsImage$ImageData (Images blocked)")
                    patches_applied["images"] = True
                else:
                    print("[-] EsImage$ImageData found but regex mismatch (Code might have changed).")

            except Exception as e:
                print(f"[-] Error patching images: {e}")

        # --- 2. חסימת וידאו (VideoSurfaceView) ---
        if "VideoSurfaceView.smali" in files:
            file_path = os.path.join(root, "VideoSurfaceView.smali")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # חיפוש הפונקציה getTextureView
                pattern_vid = re.compile(
                    r"(\.method public getTextureView\(\)Landroid\/view\/TextureView;.*?)(\.line \d+.*?iget-object [vp]\d+, [vp]\d+, Lcom\/spotify\/betamax\/player\/VideoSurfaceView;->.*?:Landroid\/view\/TextureView;)(.*?.end method)",
                    re.DOTALL
                )

                if pattern_vid.search(content):
                    # מחליף את גוף הפונקציה ב-return null
                    new_content = pattern_vid.sub(r"\1\n    const/4 v0, 0x0\n    return-object v0\n\3", content)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"[+] Patched VideoSurfaceView (Video blocked)")
                    patches_applied["video"] = True
                else:
                    print("[-] VideoSurfaceView found but regex mismatch.")

            except Exception as e:
                print(f"[-] Error patching video: {e}")

    # סיכום
    print(f"[*] Patch Summary: Images={patches_applied['images']}, Video={patches_applied['video']}, ShareWorkerDeleted={patches_applied['share_worker']}")

    # נחזיר הצלחה אם לפחות שני הדברים העיקריים (תמונות ווידאו) הצליחו
    if patches_applied["images"] and patches_applied["video"]:
        return True
    
    return False
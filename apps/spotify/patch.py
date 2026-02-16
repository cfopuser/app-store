import os
import re

def patch(decompiled_dir: str) -> bool:
    """
    Spotify Patch:
    1. Block Images (EsImage$ImageData -> getData returns null)
    2. Block Video (VideoSurfaceView -> getTextureView returns null)
    3. Block Share Image (Delete ShareHousekeepingWorker)
    """
    
    patches_applied = {
        "images": False,
        "video": False,
        "share_worker": False
    }

    print(f"[*] Scanning for Spotify target files in {decompiled_dir}...")

    # --- התיקון כאן: הופכים את החיפוש ל-case-insensitive ---
    target_worker_file = "sharehousekeepingworker.smali"

    for root, dirs, files in os.walk(decompiled_dir):
        
        # --- 3. מחיקת ShareHousekeepingWorker (מתוקן) ---
        for filename in files:
            if filename.lower() == target_worker_file:
                file_path = os.path.join(root, filename)
                try:
                    os.remove(file_path)
                    print(f"[+] Deleted {filename} at: {file_path}")
                    patches_applied["share_worker"] = True
                    # יוצאים מהלולאה הפנימית כי מצאנו ומחקנו
                    break 
                except Exception as e:
                    print(f"[-] Failed to delete {filename}: {e}")

        # --- 1. חסימת תמונות (EsImage$ImageData) ---
        if "EsImage$ImageData.smali" in files:
            file_path = os.path.join(root, "EsImage$ImageData.smali")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pattern_img = re.compile(
                    r"(\.method public final getData\(\)L.*?;.*?)(\.line \d+.*?iget-object [vp]\d+, [vp]\d+, Lcom\/spotify\/image\/esperanto\/proto\/EsImage\$ImageData;->.*?:L.*?;)(.*?.end method)",
                    re.DOTALL
                )
                
                if pattern_img.search(content):
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

                pattern_vid = re.compile(
                    r"(\.method public getTextureView\(\)Landroid\/view\/TextureView;.*?)(\.line \d+.*?iget-object [vp]\d+, [vp]\d+, Lcom\/spotify\/betamax\/player\/VideoSurfaceView;->.*?:Landroid\/view\/TextureView;)(.*?.end method)",
                    re.DOTALL
                )

                if pattern_vid.search(content):
                    new_content = pattern_vid.sub(r"\1\n    const/4 v0, 0x0\n    return-object v0\n\3", content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"[+] Patched VideoSurfaceView (Video blocked)")
                    patches_applied["video"] = True
                else:
                    print("[-] VideoSurfaceView found but regex mismatch.")

            except Exception as e:
                print(f"[-] Error patching video: {e}")

    print(f"[*] Patch Summary: Images={patches_applied['images']}, Video={patches_applied['video']}, ShareWorkerDeleted={patches_applied['share_worker']}")

    # נחזיר הצלחה אם כל שלושת החלקים עבדו
    if patches_applied["images"] and patches_applied["video"] and patches_applied["share_worker"]:
        return True
    
    print("[-] Not all patches were applied successfully.")
    return False

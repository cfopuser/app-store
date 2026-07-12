import os
import re

def patch(decompiled_dir: str) -> bool:
    """
    Applies all required patches:
    1. LicenseContentProvider.smali – bypass license check crash.
    2. Application.smali – remove PAIR checkLicense call from attachBaseContext.
    """
    success = True

    # ---------- Patch 1: LicenseContentProvider ----------
    target_filename = "LicenseContentProvider.smali"
    target_found = False

    print(f"[*] Searching for {target_filename}...")

    for root, dirs, files in os.walk(decompiled_dir):
        if target_filename in files:
            file_path = os.path.join(root, target_filename)
            print(f"[+] Found target file: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                pattern = r"(\.method public onCreate\(\)Z)([\s\S]*?)(\.end method)"
                replacement_body = """
    .registers 2
    
    # Patched by app-store script: Bypass license check initialization
    const/4 v0, 0x1
    return v0
"""
                if not re.search(pattern, content):
                    print(f"[-] Could not find onCreate method in {target_filename}. Structure might have changed.")
                    return False

                new_content = re.sub(pattern, f"\\1{replacement_body}\\3", content)

                if new_content == content:
                    print("[-] Patch attempted but content remained unchanged.")
                    return False

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("[+] LicenseContentProvider.onCreate patch applied successfully.")
                target_found = True
                break

            except Exception as e:
                print(f"[-] Error patching file: {e}")
                return False

    if not target_found:
        print(f"[-] Target file {target_filename} not found in decompiled directory.")
        return False

    # ---------- Patch 2: Application.smali (remove PAIR checkLicense) ----------
    target_app = "com/pairip/application/Application.smali"
    app_found = False

    print(f"[*] Searching for {target_app}...")

    for root, dirs, files in os.walk(decompiled_dir):
        if target_app in files:
            file_path = os.path.join(root, target_app)
            print(f"[+] Found target file: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # We want to replace the whole attachBaseContext method
                # with one that only calls super (removing checkLicense).
                # Pattern matches the method block.
                method_pattern = r"(\.method protected attachBaseContext\(Landroid/content/Context;\)V)([\s\S]*?)(\.end method)"
                
                # Replacement: only the super call, no checkLicense.
                replacement_method = r"""\1
    .registers 2
    invoke-super {p0, p1}, Lcom/pairip/application/Application;->attachBaseContext(Landroid/content/Context;)V
    return-void
\3"""

                if not re.search(method_pattern, content, re.DOTALL):
                    print(f"[-] Could not find attachBaseContext method in {target_app}. Structure might have changed.")
                    return False

                new_content = re.sub(method_pattern, replacement_method, content, flags=re.DOTALL)

                if new_content == content:
                    print("[-] Patch attempted but content remained unchanged.")
                    return False

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print("[+] Application.smali patched successfully! PAIR checkLicense removed.")
                app_found = True
                break

            except Exception as e:
                print(f"[-] Error patching Application.smali: {e}")
                return False

    if not app_found:
        print(f"[-] Target file {target_app} not found in decompiled directory.")
        return False

    print("[+] All patches applied successfully!")
    return True

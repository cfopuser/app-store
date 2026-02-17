import os
import re

def patch(decompiled_dir: str) -> bool:
    """
    Applies the patch to LicenseContentProvider.smali to bypass the license check crash.
    """
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

                # Regex to find the onCreate method block
                # It looks for .method public onCreate()Z ... until .end method
                pattern = r"(\.method public onCreate\(\)Z)([\s\S]*?)(\.end method)"
                
                # The replacement code: minimal valid smali that returns true (1)
                replacement_body = """
    .registers 2
    
    # Patched by app-store script: Bypass license check initialization
    const/4 v0, 0x1
    return v0
"""
                
                # Check if we can find the pattern first
                if not re.search(pattern, content):
                    print(f"[-] Could not find onCreate method in {target_filename}. Structure might have changed.")
                    return False

                # Perform the substitution
                new_content = re.sub(pattern, f"\\1{replacement_body}\\3", content)

                if new_content == content:
                    print("[-] Patch attempted but content remained unchanged.")
                    return False

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("[+] LicenseContentProvider.onCreate patch applied successfully.")
                target_found = True
                # We stop after patching the first occurrence, assuming unique class names
                break

            except Exception as e:
                print(f"[-] Error patching file: {e}")
                return False

    if not target_found:
        print(f"[-] Target file {target_filename} not found in decompiled directory.")
        return False

    return True

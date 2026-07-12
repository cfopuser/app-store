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

    # ---------- Patch 2: Find and patch Application.smali (remove PAIR checkLicense) ----------
    # Search for any file that contains "pairip/application/Application" in its path
    # or any file that contains the checkLicense call
    app_found = False
    print(f"[*] Searching for PAIR Application class...")

    for root, dirs, files in os.walk(decompiled_dir):
        for file in files:
            if not file.endswith('.smali'):
                continue
                
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, decompiled_dir)
            
            # Check if this is likely the PAIR Application class
            # Look for either the expected path OR the checkLicense call
            is_pair_app = False
            
            # Method 1: Check by path
            if 'pairip/application/Application.smali' in relative_path.replace('\\', '/'):
                is_pair_app = True
                print(f"[+] Found PAIR Application by path: {file_path}")
            
            # Method 2: If not found by path, search content for checkLicense
            if not is_pair_app:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for the characteristic checkLicense call
                    if ('.super' in content and 
                        'Lcom/pairip/licensecheck/LicenseClient;' in content and
                        'checkLicense' in content and
                        'attachBaseContext' in content):
                        
                        is_pair_app = True
                        print(f"[+] Found PAIR Application by content: {file_path}")
                        
                except Exception:
                    continue
            
            if is_pair_app:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # We want to replace the whole attachBaseContext method
                    # with one that only calls super (removing checkLicense).
                    method_pattern = r"(\.method (?:protected |public )?attachBaseContext\(Landroid/content/Context;\)V)([\s\S]*?)(\.end method)"
                    
                    # Replacement: only the super call, no checkLicense.
                    replacement_method = r"""\1
    .registers 2
    invoke-super {p0, p1}, Lcom/pairip/application/Application;->attachBaseContext(Landroid/content/Context;)V
    return-void
\3"""

                    if not re.search(method_pattern, content, re.DOTALL):
                        print(f"[-] Could not find attachBaseContext method in {file}. Structure might have changed.")
                        continue

                    new_content = re.sub(method_pattern, replacement_method, content, flags=re.DOTALL)

                    if new_content == content:
                        print("[-] Patch attempted but content remained unchanged.")
                        continue

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    print(f"[+] Application.smali patched successfully! PAIR checkLicense removed from {file}")
                    app_found = True
                    break

                except Exception as e:
                    print(f"[-] Error patching Application.smali: {e}")
                    return False

    if not app_found:
        print("[!] PAIR Application class not found. This might mean:")
        print("    1. The app doesn't use PAIR protection (unlikely)")
        print("    2. The PAIR class was heavily obfuscated")
        print("    3. The decompilation didn't include it")
        print("[*] Continuing anyway - the main LicenseContentProvider patch is applied.")
        # Don't fail, just continue

    print("[+] All available patches applied successfully!")
    return True

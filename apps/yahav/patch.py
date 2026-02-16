"""
Yahav Bank App Patch — Bypass Root, Emulator, Tamper, and Version Checks

Targets: 
1. authentication.js (Bypass version/status blocks)
2. MainActivity.smali (Bypass root/emulator gates & tamper alerts)
3. RootChecker.smali (Neutralize native library checks)
"""

import os
import re
import sys

def patch(decompiled_dir: str) -> bool:
    """
    Apply the multi-stage patch to the decompiled Yahav Bank APK.
    """
    print(f"[*] Starting Yahav Bank patch process in: {decompiled_dir}")
    
    success_flags = {
        "js_auth": False,
        "root_gate": False,
        "emu_gate": False,
        "tamper_bypass": False,
        "native_root": False
    }

    # --- 1. Patch authentication.js ---
    # Path: assets/www/ui/phone/module/authentication/js/authentication.js
    js_rel_path = os.path.join("assets", "www", "ui", "phone", "module", "authentication", "js", "authentication.js")
    js_full_path = os.path.join(decompiled_dir, js_rel_path)

    if os.path.exists(js_full_path):
        try:
            with open(js_full_path, 'r', encoding='utf-8') as f:
                js_content = f.read()

            # Target both 'b' (warning) and 'd' (error) handlers
            # Regex targets the function assignments and the property access chain
            js_pattern = re.compile(
                r"(b\s*=\s*function\s*\(b\)\s*\{props\.config\.constants\.versionManagementCodes\.updateWarningCodes.*?\},)\s*(d\s*=\s*function\s*\(b\)\s*\{props\.config\.constants\.versionManagementCodes\.updateErrorCodes.*?\})",
                re.DOTALL
            )
            
            js_replacement = (
                "b=function(b){a.getState().go(a.getState().current.navigationRoutes.onAuthenticationSuccess)},"
                "d=function(b){a.getState().go(a.getState().current.navigationRoutes.onAuthenticationSuccess)}"
            )

            if js_pattern.search(js_content):
                new_js = js_pattern.sub(js_replacement, js_content)
                with open(js_full_path, 'w', encoding='utf-8') as f:
                    f.write(new_js)
                print("[+] Patched authentication.js: Version/Update checks neutralized.")
                success_flags["js_auth"] = True
            else:
                print("[-] Failed to find JS patterns in authentication.js")
        except Exception as e:
            print(f"[-] Error patching JS: {e}")
    else:
        print(f"[-] authentication.js not found at {js_rel_path}")

    # --- 2. Patch Smali Files (MainActivity & RootChecker) ---
    # We walk the directory to handle multidex (smali, smali_classes2, etc.)
    for root, dirs, files in os.walk(decompiled_dir):
        
        # Target: MainActivity.smali
        if "MainActivity.smali" in files:
            file_path = os.path.join(root, "MainActivity.smali")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Patch Method B()Z (Root/Emulator Gate)
                if ".method public B()Z" in content:
                    content = re.sub(
                        r"\.method public B\(\)Z.*?\.end method",
                        ".method public B()Z\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n.end method",
                        content, flags=re.DOTALL
                    )
                    success_flags["root_gate"] = True

                # Patch Method A()Z (Emulator Hardware Strings)
                if ".method public A()Z" in content:
                    content = re.sub(
                        r"\.method public A\(\)Z.*?\.end method",
                        ".method public A()Z\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n.end method",
                        content, flags=re.DOTALL
                    )
                    success_flags["emu_gate"] = True

                # Patch Tamper Alert (:catch_0 in Method E()V)
                # We look for the catch block that handles the tamper dialog
                if "MainActivity$c;" in content and ":catch_0" in content:
                    # Find :catch_0 and inject return-void immediately after move-exception
                    content = content.replace(
                        ":catch_0\n    move-exception v0",
                        ":catch_0\n    move-exception v0\n    return-void"
                    )
                    success_flags["tamper_bypass"] = True

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[+] MainActivity.smali patched at: {file_path}")
            except Exception as e:
                print(f"[-] Error patching MainActivity.smali: {e}")

        # Target: RootChecker.smali
        if "RootChecker.smali" in files:
            file_path = os.path.join(root, "RootChecker.smali")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Method o()Z (Native Lib Loading) -> Force return True
                if ".method public o()Z" in content:
                    content = re.sub(
                        r"\.method public o\(\)Z.*?\.end method",
                        ".method public o()Z\n    .locals 1\n    const/4 v0, 0x1\n    return v0\n.end method",
                        content, flags=re.DOTALL
                    )
                    success_flags["native_root"] = True

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[+] RootChecker.smali patched at: {file_path}")
            except Exception as e:
                print(f"[-] Error patching RootChecker.smali: {e}")

    # --- Summary ---
    print("\n--- Patch Summary ---")
    for key, val in success_flags.items():
        status = "OK" if val else "FAILED/SKIPPED"
        print(f"[{status}] {key}")

    return all(success_flags.values())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python patch_yahav.py <decompiled_dir>")
    else:
        patch(sys.argv[1])
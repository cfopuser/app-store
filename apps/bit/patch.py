"""
Bit App Patch — Bypass sideload/installer check & Fix Android 9 Crash

Targets: 
1. AndroidManifest.xml -> Removes ProfileInstallerInitializer (Fixes Android 9 crash)
2. AppInitiationViewModel.smali -> Bypasses installer source check
"""

import os
import re
import sys

def patch_manifest(decompiled_dir: str) -> bool:
    """
    Removes the ProfileInstallerInitializer meta-data tag to prevent 
    crashes on Android 9 (API 28) caused by 'Trace.isEnabled()' calls.
    """
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    
    if not os.path.exists(manifest_path):
        print("[-] CRITICAL: AndroidManifest.xml not found.")
        return False

    print(f"[*] Scanning Manifest: {manifest_path}")

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to match the specific meta-data tag responsible for the crash
        # It looks for <meta-data ... name="...ProfileInstallerInitializer" ... />
        crash_tag_pattern = re.compile(
            r'<meta-data\s+[^>]*android:name="androidx\.profileinstaller\.ProfileInstallerInitializer"[^>]*/>',
            re.IGNORECASE
        )

        if crash_tag_pattern.search(content):
            print("[i] Found crashing ProfileInstallerInitializer tag.")
            # Remove the tag (replace with empty string)
            new_content = crash_tag_pattern.sub('', content)
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("[+] PATCH APPLIED: Removed ProfileInstallerInitializer (Android 9 Crash Fix).")
            return True
        else:
            print("[?] ProfileInstallerInitializer tag not found. App might already be patched or this version doesn't use it.")
            return True # Not a failure, just nothing to do

    except Exception as e:
        print(f"[-] Error patching Manifest: {str(e)}")
        return False

def patch_sideload_check(decompiled_dir: str) -> bool:
    """
    Apply the sideload bypass patch to a decompiled Bit APK.
    """
    target_filename = "AppInitiationViewModel.smali"
    file_found = False

    print(f"[*] Searching for {target_filename}...")

    for root, dirs, files in os.walk(decompiled_dir):
        if target_filename in files:
            file_path = os.path.join(root, target_filename)
            file_found = True
            print(f"[+] Found file at: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Primary regex: match invoke-static ArraysKt->contains, then
                # the move-result register, then the if-nez conditional branch.
                pattern = re.compile(
                    r"(invoke-static \{[vp]\d+, [vp]\d+\}, Lkotlin\/collections\/ArraysKt.*?;->contains\(.*?\).*?move-result ([vp]\d+).*?)if-nez \2, (:cond_\w+)",
                    re.DOTALL
                )

                match = pattern.search(content)

                if match:
                    print(f"[i] Logic found! Target label is: {match.group(3)}")
                    # Replace if-nez (jump if not zero/true) with goto (jump always)
                    # This assumes the positive case (contains=true) falls through, 
                    # and negative case jumps. We want to FORCE the jump to success or fall through based on logic.
                    # Actually, usually 'contains' returns true if valid. 
                    # If the logic is "if not contains, crash", then 'if-eqz' would jump to crash.
                    # Based on your previous snippet, you are replacing if-nez with goto.
                    new_content = pattern.sub(r"\1goto \3", content)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    print("[+] PATCH APPLIED: Sideload check bypassed.")
                    return True

                else:
                    print("[!] Complex regex failed, trying simple search fallback...")

                    if "Lkotlin/collections/ArraysKt" in content and "contains" in content:
                        print("[i] Found ArraysKt->contains usage. Attempting heuristic patch...")

                        fallback_pattern = re.compile(r"(if-nez p1, (:cond_\w+))")
                        if fallback_pattern.search(content):
                            new_content = fallback_pattern.sub(r"goto \2", content, count=1)

                            if new_content != content:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                print("[+] Simple fallback patch applied successfully.")
                                return True

                    print("[-] Pattern not found in SMALI.")
                    return False

            except Exception as e:
                print(f"[-] Error reading/writing file: {str(e)}")
                return False

    if not file_found:
        print(f"[-] CRITICAL: {target_filename} not found.")
        return False

    return False

def apply_patches(decompiled_dir: str):
    print("=== Starting Bit App Patcher ===")
    
    # 1. Apply Manifest Fix (Crash)
    manifest_success = patch_manifest(decompiled_dir)
    
    # 2. Apply Sideload Fix (Bypass)
    sideload_success = patch_sideload_check(decompiled_dir)

    print("\n=== Patch Summary ===")
    print(f"Manifest Crash Fix: {'SUCCESS' if manifest_success else 'SKIPPED/FAILED'}")
    print(f"Sideload Bypass:    {'SUCCESS' if sideload_success else 'FAILED'}")

    if manifest_success and sideload_success:
        print("\n[ok] All patches applied. You can now rebuild the APK.")
    else:
        print("\n[!] Warning: Some patches may not have been applied.")

# Example Usage Wrapper
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python patcher.py <path_to_decompiled_folder>")
    else:
        apply_patches(sys.argv[1])
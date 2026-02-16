"""
Bit App Patch — Bypass sideload/installer check

Targets: AppInitiationViewModel.smali
Method:  Replaces the `if-nez` branch (ArraysKt.contains check for
         allowed installers) with a `goto` to always take the success path.
"""

import os
import re
import sys


def patch(decompiled_dir: str) -> bool:
    """
    Apply the sideload bypass patch to a decompiled Bit APK.

    Args:
        decompiled_dir: Path to the apktool-decompiled directory.

    Returns:
        True if the patch was applied successfully, False otherwise.
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
                    new_content = pattern.sub(r"\1goto \3", content)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    print("[+] PATCH APPLIED SUCCESSFULLY: Sideload check bypassed.")
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

                    print("[-] Pattern not found. Dumping snippet for debugging:")
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if "contains" in line and "ArraysKt" in line:
                            print(f"Line {i}: {line}")
                            for j in range(1, 6):
                                if i + j < len(lines):
                                    print(f"Line {i+j}: {lines[i+j]}")

            except Exception as e:
                print(f"[-] Error reading/writing file: {str(e)}")
                return False

    if not file_found:
        print(f"[-] CRITICAL: {target_filename} not found.")
        return False

    print("[-] CRITICAL: File found but patch logic could not be applied.")
    return False

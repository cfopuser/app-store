"""
Egg App Patch — PAIR license check and Play Store installer verification
are handled universally by the Frida Gadget engine.
"""

import os
import re


def patch(decompiled_dir: str) -> bool:
    print(f"[*] [egg] Frida universal engine active for {decompiled_dir}")
    
    # Optional static layer for LicenseContentProvider if present
    target_filename = "LicenseContentProvider.smali"
    for root, dirs, files in os.walk(decompiled_dir):
        if target_filename in files:
            file_path = os.path.join(root, target_filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                pattern = r"(\.method public onCreate\(\)Z)([\s\S]*?)(\.end method)"
                replacement_body = "\n    .registers 2\n    const/4 v0, 0x1\n    return v0\n"
                if re.search(pattern, content):
                    new_content = re.sub(pattern, f"\\1{replacement_body}\\3", content)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print("[+] LicenseContentProvider.onCreate static fallback patch applied.")
            except Exception as e:
                print(f"[!] Optional static patch skipped: {e}")
            break

    return True

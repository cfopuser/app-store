"""
Bezeq App Patch — Neutralizes LicenseContentProvider bootstrap race condition.
All security, installer spoofing, PAIR checks, and Talsec FreeRASP are handled dynamically by Frida Gadget.
"""

import glob
import os
import re


def patch(decompiled_dir: str) -> bool:
    print(f"[*] [bezeq] Preparing Bezeq for Frida Gadget in {decompiled_dir}...")
    for file_path in glob.glob(os.path.join(decompiled_dir, "**/LicenseContentProvider.smali"), recursive=True):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(
                r"(\.method public onCreate\(\)Z)([\s\S]*?)(\.end method)",
                r"\1\n    .locals 1\n\n    const/4 v0, 0x1\n    return v0\n\3",
                content,
            )
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"[+] [bezeq] Stubbed {os.path.basename(file_path)} onCreate to prevent early bootstrap exit")
        except Exception as e:
            print(f"[-] [bezeq] Error patching {file_path}: {e}")
    return True

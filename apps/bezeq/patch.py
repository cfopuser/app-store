"""
Bezeq App Patch — Neutralizes LicenseContentProvider & LicenseClient bootstrap race conditions.
All security, installer spoofing, PAIR checks, Talsec FreeRASP, and unpinning are handled dynamically by Frida Gadget.
"""

import glob
import os
import re


def patch(decompiled_dir: str) -> bool:
    print(f"[*] [bezeq] Preparing Bezeq bootstrap lifecycle stubs in {decompiled_dir}...")

    rules = [
        (
            "**/LicenseContentProvider.smali",
            [
                (
                    r"(\.method public onCreate\(\)Z)([\s\S]*?)(\.end method)",
                    r"\1\n    .locals 1\n\n    const/4 v0, 0x1\n    return v0\n\3",
                )
            ],
        ),
        (
            "**/LicenseClient.smali",
            [
                (
                    r"(\.method public static checkLicense\(Landroid/content/Context;\)V)([\s\S]*?)(\.end method)",
                    r"\1\n    .locals 0\n\n    return-void\n\3",
                )
            ],
        ),
    ]

    for pattern, replacements in rules:
        search_pattern = os.path.join(decompiled_dir, pattern)
        for file_path in glob.glob(search_pattern, recursive=True):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                original_content = content
                for pat, rep in replacements:
                    content = re.sub(pat, rep, content, flags=re.DOTALL | re.MULTILINE)
                if content != original_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"[+] [bezeq] Neutralized {os.path.basename(file_path)} bootstrap check")
            except Exception as e:
                print(f"[-] [bezeq] Error patching {file_path}: {e}")

    return True

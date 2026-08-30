"""
MetroList App Patch — Blocks thumbnail image URLs.
Strings replacement, 64k multidex, and WebView domain firewall are handled universally by the engine.
"""

import os
import re


def patch(decompiled_dir: str) -> bool:
    print("[*] Starting MetroList custom thumbnail patch...")
    _patch_thumbnail(decompiled_dir)
    return True


def _patch_thumbnail(root_dir: str) -> bool:
    print("[*] Searching for Thumbnail.smali to block image URLs...")
    for root, dirs, files in os.walk(root_dir):
        if "Thumbnail.smali" in files and "metrolist" in root and "models" in root:
            target_path = os.path.join(root, "Thumbnail.smali")
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    content = f.read()
                pattern = r"(iput-object p2, p0, Lcom/metrolist/innertube/models/Thumbnail;->(?:a|url):Ljava/lang/String;)"
                if re.search(pattern, content):
                    new_content = re.sub(pattern, r'const-string p2, ""\n    \1', content)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print("[+] Thumbnail.smali: URL loading blocked.")
                    return True
            except Exception as e:
                print(f"[-] Error patching Thumbnail.smali: {e}")
    return False

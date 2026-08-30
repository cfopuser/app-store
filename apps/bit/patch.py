"""
Bit App Patch — Sideloading, PAIR checks, and Play Store installer verification
are handled universally by the Frida Gadget engine.
"""

import os
import re


def patch(decompiled_dir: str) -> bool:
    """
    Apply optional static sideload bypass if target file exists, otherwise Frida handles it.
    """
    print(f"[*] [bit] Frida universal installer engine active for {decompiled_dir}")
    
    target_filename = "AppInitiationViewModel.smali"
    for root, dirs, files in os.walk(decompiled_dir):
        if target_filename in files:
            file_path = os.path.join(root, target_filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                pattern = re.compile(
                    r"(invoke-static \{[vp]\d+, [vp]\d+\}, Lkotlin\/collections\/ArraysKt.*?;->contains\(.*?\).*?move-result ([vp]\d+).*?)if-nez \2, (:cond_\w+)",
                    re.DOTALL
                )
                match = pattern.search(content)
                if match:
                    new_content = pattern.sub(r"\1goto \3", content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print("[+] [bit] Static ArraysKt bypass applied as secondary defense.")
            except Exception as e:
                print(f"[i] [bit] Static patch skipped: {e}")
            break

    return True


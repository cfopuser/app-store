"""
Mizrahi App Patch — Sideloading, RootBeer, Daon FIDO, and SSL Pinning
are handled universally by the Frida Gadget engine.
"""

import glob
import os
import re


def patch_file(file_path, replacements):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[+] [mizrahi] Static patch applied to {os.path.basename(file_path)}")
    except Exception as e:
        print(f"[i] [mizrahi] Optional static patch skipped for {file_path}: {e}")


def patch(target_dir: str) -> bool:
    print(f"[*] [mizrahi] Frida universal engine active for {target_dir}")

    # Optional static layer as defense in depth
    rules = [
        (
            "**/matrix/cordova/filescanner/FileScanner.smali",
            [
                (r"\.method public isAppSecure\(\)Z.*?\.end method", ".method public isAppSecure()Z\n    .registers 2\n    const/4 v0, 0x1\n    return v0\n.end method"),
                (r"\.method public alertUnsecureAndStopApp\(\)V.*?\.end method", ".method public alertUnsecureAndStopApp()V\n    .registers 1\n    return-void\n.end method")
            ]
        ),
        (
            "**/com/scottyab/rootbeer/RootBeer.smali",
            [
                (r"\.method public isRooted\(\)Z.*?\.end method", ".method public isRooted()Z\n    .registers 2\n    const/4 v0, 0x0\n    return v0\n.end method")
            ]
        ),
        (
            "**/okhttp3/CertificatePinner.smali",
            [
                (r"\.method public check\(Ljava/lang/String;Ljava/util/List;\)V.*?\.end method", ".method public check(Ljava/lang/String;Ljava/util/List;)V\n    .registers 3\n    return-void\n.end method")
            ]
        )
    ]

    for pattern, replacements in rules:
        search_pattern = os.path.join(target_dir, pattern)
        matched_files = glob.glob(search_pattern, recursive=True)
        for file_path in matched_files:
            patch_file(file_path, replacements)

    return True


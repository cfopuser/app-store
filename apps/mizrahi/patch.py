import os
import re
import sys
import glob

def patch_file(file_path, replacements):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        for pattern, replacement in replacements:
            # We use re.DOTALL to match across newlines
            content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[+] Successfully patched {file_path}")
    except Exception as e:
        print(f"[-] Error processing {file_path}: {e}")

def patch(target_dir: str) -> bool:
    print(f"[*] Searching for files to patch in {target_dir}...")

    # Rules mapping file paths (or parts of file paths) to a list of (regex_pattern, replacement)
    rules = [
        # 1. Local Application Integrity: FileScanner
        (
            "**/matrix/cordova/filescanner/FileScanner.smali",
            [
                (
                    r"\.method public isAppSecure\(\)Z.*?\.end method",
                    """.method public isAppSecure()Z
    .registers 2
    const/4 v0, 0x1
    return v0
.end method"""
                ),
                (
                    r"\.method public alertUnsecureAndStopApp\(\)V.*?\.end method",
                    """.method public alertUnsecureAndStopApp()V
    .registers 1
    return-void
.end method"""
                )
            ]
        ),
        
        # 2. Environment & Root Detection: RootBeer
        (
            "**/com/scottyab/rootbeer/RootBeer.smali",
            [
                (
                    r"\.method public isRooted\(\)Z.*?\.end method",
                    """.method public isRooted()Z
    .registers 2
    const/4 v0, 0x0
    return v0
.end method"""
                ),
                (
                    r"\.method public isRootedWithBusyBoxCheck\(\)Z.*?\.end method",
                    """.method public isRootedWithBusyBoxCheck()Z
    .registers 2
    const/4 v0, 0x0
    return v0
.end method"""
                ),
                (
                    r"\.method public isRootedWithoutBusyBoxCheck\(\)Z.*?\.end method",
                    """.method public isRootedWithoutBusyBoxCheck()Z
    .registers 2
    const/4 v0, 0x0
    return v0
.end method"""
                )
            ]
        ),
        
        # 3. Custom Magisk Detection
        (
            "**/a/a/a/a/a/m/h.smali",
            [
                (
                    r"\.method public static b\(\)Z.*?\.end method",
                    """.method public static b()Z
    .registers 1
    const/4 v0, 0x0
    return v0
.end method"""
                )
            ]
        ),
        
        # 4. Emulator & Debugger Detection: Daon FIDO Client SDK
        (
            "**/com/daon/fido/client/sdk/state/n.smali",
            [
                (
                    r"\.method private static a\(\)Z.*?\.end method",
                    """.method private static a()Z
    .registers 1
    const/4 v0, 0x0
    return v0
.end method"""
                ),
                (
                    r"\.method private static b\(\)Z.*?\.end method",
                    """.method private static b()Z
    .registers 1
    const/4 v0, 0x0
    return v0
.end method"""
                ),
                (
                    r"\.method public static c\(\)Ljava/lang/String;.*?\.end method",
                    """.method public static c()Ljava/lang/String;
    .registers 1
    sget-object v0, Lcom/daon/fido/client/sdk/state/n$a;->c:Lcom/daon/fido/client/sdk/state/n$a;
    invoke-virtual {v0}, Ljava/lang/Enum;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method"""
                )
            ]
        ),
        
        # 5. Network Security: SSL Pinning via OkHttp CertificatePinner
        (
            "**/okhttp3/CertificatePinner.smali",
            [
                (
                    r"\.method public check\(Ljava/lang/String;Ljava/util/List;\)V.*?\.end method",
                    """.method public check(Ljava/lang/String;Ljava/util/List;)V
    .registers 3
    return-void
.end method"""
                ),
                (
                    r"\.method public varargs check\(Ljava/lang/String;\[Ljava/security/cert/Certificate;\)V.*?\.end method",
                    """.method public varargs check(Ljava/lang/String;[Ljava/security/cert/Certificate;)V
    .registers 3
    return-void
.end method"""
                )
            ]
        )
    ]

    for pattern, replacements in rules:
        # Use glob to find matching files
        search_pattern = os.path.join(target_dir, pattern)
        matched_files = glob.glob(search_pattern, recursive=True)
        
        for file_path in matched_files:
            patch_file(file_path, replacements)
            
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch(target)

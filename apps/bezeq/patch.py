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

def search_and_patch(target_dir: str, file_pattern: str, search_string: str, replacements: list):
    search_pattern = os.path.join(target_dir, file_pattern)
    matched_files = glob.glob(search_pattern, recursive=True)
    
    for file_path in matched_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if search_string in content:
                print(f"[*] Found target '{search_string}' in {file_path}")
                patch_file(file_path, replacements)
        except Exception as e:
            pass

def patch(target_dir: str) -> bool:
    print(f"[*] Searching for files to patch in {target_dir}...")

    # 1. LicenseContentProvider (Google Play Licensing Check)
    # Path is usually consistent for com.pairip
    rules = [
        (
            "**/com/pairip/licensecheck/LicenseContentProvider.smali",
            [
                (
                    r"\.method public onCreate\(\)Z.*?\.end method",
                    """.method public onCreate()Z
    .locals 1
    const/4 v0, 0x1
    return v0
.end method"""
                )
            ]
        )
    ]

    for pattern, replacements in rules:
        search_pattern = os.path.join(target_dir, pattern)
        matched_files = glob.glob(search_pattern, recursive=True)
        for file_path in matched_files:
            patch_file(file_path, replacements)

    # 2. Package_info_plus (Spoof installerStore to Google Play)
    # The file path varies (e.g. r6.1/a.smali), so we search for the specific Dart channel string
    package_info_replacements = [
        (
            r"sget v4, Landroid/os/Build\$VERSION;->SDK_INT:I\s+const/16 v5, 0x1e\s+if-lt v4, v5, :cond_0\s+invoke-static \{v2, v3\}, LI0/c;->d\(Landroid/content/pm/PackageManager;Ljava/lang/String;\)Landroid/content/pm/InstallSourceInfo;\s+move-result-object v2\s+invoke-static \{v2\}, LI0/d;->i\(Landroid/content/pm/InstallSourceInfo;\)Ljava/lang/String;\s+move-result-object v2\s+goto :goto_0\s+:cond_0\s+invoke-virtual \{v2, v3\}, Landroid/content/pm/PackageManager;->getInstallerPackageName\(Ljava/lang/String;\)Ljava/lang/String;\s+move-result-object v2",
            """sget v4, Landroid/os/Build$VERSION;->SDK_INT:I

    const-string v2, "com.android.vending" """
        )
    ]
    search_and_patch(target_dir, "**/smali*/**/*.smali", '"dev.fluttercommunity.plus/package_info"', package_info_replacements)

    # 3. jailbreak_root_detection (Neutralize root, emulator, debugger checks)
    # The file path varies (e.g. m6.1/c.smali), so we search for the specific Dart channel string
    root_detection_replacements = [
        (
            r"\.method public final onMethodCall\(LI6/j;LI6/l\$d;\)V.*?\.end method",
            """.method public final onMethodCall(LI6/j;LI6/l$d;)V
    .locals 3

    const-string v0, "call"
    invoke-static {p1, v0}, Lkotlin/jvm/internal/Intrinsics;->checkNotNullParameter(Ljava/lang/Object;Ljava/lang/String;)V

    const-string v0, "result"
    invoke-static {p2, v0}, Lkotlin/jvm/internal/Intrinsics;->checkNotNullParameter(Ljava/lang/Object;Ljava/lang/String;)V

    iget-object p1, p1, LI6/j;->a:Ljava/lang/String;

    const-string v0, "checkForIssues"
    invoke-static {p1, v0}, Lkotlin/jvm/internal/Intrinsics;->a(Ljava/lang/Object;Ljava/lang/Object;)Z
    move-result v0

    if-eqz v0, :cond_0

    new-instance p1, Ljava/util/ArrayList;
    invoke-direct {p1}, Ljava/util/ArrayList;-><init>()V
    check-cast p2, LI6/k;
    invoke-virtual {p2, p1}, LI6/k;->success(Ljava/lang/Object;)V
    return-void

    :cond_0
    const-string v0, "isRealDevice"
    invoke-static {p1, v0}, Lkotlin/jvm/internal/Intrinsics;->a(Ljava/lang/Object;Ljava/lang/Object;)Z
    move-result p1

    if-eqz p1, :cond_1

    sget-object p1, Ljava/lang/Boolean;->TRUE:Ljava/lang/Boolean;
    check-cast p2, LI6/k;
    invoke-virtual {p2, p1}, LI6/k;->success(Ljava/lang/Object;)V
    return-void

    :cond_1
    sget-object p1, Ljava/lang/Boolean;->FALSE:Ljava/lang/Boolean;
    check-cast p2, LI6/k;
    invoke-virtual {p2, p1}, LI6/k;->success(Ljava/lang/Object;)V
    return-void
.end method"""
        )
    ]
    search_and_patch(target_dir, "**/smali*/**/*.smali", '"jailbreak_root_detection"', root_detection_replacements)

    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch(target)

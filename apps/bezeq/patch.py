"""
Bezeq App Patch — Sideloading, PAIR licensing, PackageInfo installer, and FreeRASP bypass.
"""

import glob
import os
import re


def patch_file(file_path: str, replacements: list[tuple[str, str]]) -> bool:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[+] [bezeq] Successfully patched {os.path.basename(file_path)}")
            return True
    except Exception as e:
        print(f"[-] [bezeq] Error processing {file_path}: {e}")
    return False


def patch_freerasp(decompiled_dir: str) -> bool:
    print("[*] [bezeq] Searching for FreeRASP plugin to patch...")
    target_file = None
    for root, _, files in os.walk(decompiled_dir):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if '"isJailBroken"' in content and '"checkForIssues"' in content and '"isRealDevice"' in content:
                        target_file = path
                        break
                except Exception:
                    pass
        if target_file:
            break

    if not target_file:
        print("[-] [bezeq] FreeRASP plugin not found.")
        return False

    print(f"[+] [bezeq] Found FreeRASP plugin at: {target_file}")
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    method_pattern = r"(\.method public final onMethodCall\(L[^;]+;L[^;]+;\)V)([\s\S]*?)(\.end method)"
    match = re.search(method_pattern, content)
    if not match:
        print("[-] [bezeq] Could not find onMethodCall method in FreeRASP plugin.")
        return False

    method_body = match.group(2)
    iget_pattern = r"iget-object\s+([vp]\d+|p1),\s*p1,\s*(L[^;]+;->[a-zA-Z0-9_]+:Ljava/lang/String;)"
    iget_match = re.search(iget_pattern, method_body)
    if not iget_match:
        print("[-] [bezeq] Could not extract method name field access.")
        return False

    method_field = iget_match.group(2)
    success_pattern = r"(check-cast\s+p2,\s*(L[^;]+;)\s+)?invoke-(virtual|interface)\s*\{p2,\s*([vp]\d+)\},\s*(L[^;]+;->success\(Ljava/lang/Object;\)V)"
    success_match = re.search(success_pattern, method_body)
    if not success_match:
        print("[-] [bezeq] Could not extract success call pattern.")
        return False

    check_cast_str = f"check-cast p2, {success_match.group(2)}" if success_match.group(2) else ""
    invoke_type = success_match.group(3)
    success_method = success_match.group(5)

    replacement_body = f"""
    .locals 2

    # Extract the method name into v0
    iget-object v0, p1, {method_field}

    const-string v1, "checkForIssues"
    invoke-virtual {{v0, v1}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-eqz v1, :cond_checkForIssues

    const-string v1, "isRealDevice"
    invoke-virtual {{v0, v1}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-eqz v1, :cond_isRealDevice

    # Default: return false
    sget-object v0, Ljava/lang/Boolean;->FALSE:Ljava/lang/Boolean;
    goto :success

    :cond_isRealDevice
    sget-object v0, Ljava/lang/Boolean;->TRUE:Ljava/lang/Boolean;
    goto :success

    :cond_checkForIssues
    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {{v0}}, Ljava/util/ArrayList;-><init>()V

    :success
    {check_cast_str}
    invoke-{invoke_type} {{p2, v0}}, {success_method}
    return-void
"""

    new_content = content[:match.start(2)] + replacement_body + content[match.end(2):]
    if new_content != content:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("[+] [bezeq] Patched FreeRASP successfully.")
        return True
    return False


def patch(target_dir: str) -> bool:
    print(f"[*] [bezeq] Starting Bezeq local install & licensing patch in {target_dir}...")

    rules = [
        (
            "**/LicenseContentProvider.smali",
            [
                (
                    r"(\.method public onCreate\(\)Z)([\s\S]*?)(\.end method)",
                    r"""\1
    .locals 1

    const/4 v0, 0x1
    return v0
\3""",
                )
            ],
        ),
        (
            "**/LicenseClient.smali",
            [
                (
                    r"(\.method public static checkLicense\(Landroid/content/Context;\)V)([\s\S]*?)(\.end method)",
                    r"""\1
    .locals 0

    return-void
\3""",
                )
            ],
        ),
        (
            "**/*.smali",
            [
                (
                    r"(sget\s+([pv]\d+),\s*Landroid/os/Build\$VERSION;->SDK_INT:I\s+const/16\s+[pv]\d+,\s*0x1e[\s\S]{1,500}?getInstallerPackageName\(Ljava/lang/String;\)Ljava/lang/String;\s+move-result-object\s+([pv]\d+))",
                    r'sget \2, Landroid/os/Build$VERSION;->SDK_INT:I\n\n    const-string \3, "com.android.vending"',
                )
            ],
        ),
    ]

    for pattern, replacements in rules:
        search_pattern = os.path.join(target_dir, pattern)
        matched_files = glob.glob(search_pattern, recursive=True)
        for file_path in matched_files:
            patch_file(file_path, replacements)

    patch_freerasp(target_dir)
    return True

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
            return True
    except Exception as e:
        print(f"[-] Error processing {file_path}: {e}")
    return False

def patch_freerasp(decompiled_dir):
    print("[*] Searching for FreeRASP plugin to patch...")
    target_file = None
    for root, dirs, files in os.walk(decompiled_dir):
        for file in files:
            if file.endswith('.smali'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if '"isJailBroken"' in content and '"checkForIssues"' in content and '"isRealDevice"' in content:
                        target_file = path
                        break
                except:
                    pass
        if target_file:
            break

    if not target_file:
        print("[-] FreeRASP plugin not found.")
        return False

    print(f"[+] Found FreeRASP plugin at: {target_file}")
    
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match the entire onMethodCall method
    method_pattern = r"(\.method public final onMethodCall\(L[^;]+;L[^;]+;\)V)([\s\S]*?)(\.end method)"
    match = re.search(method_pattern, content)
    if not match:
        print("[-] Could not find onMethodCall method in FreeRASP plugin.")
        return False

    method_body = match.group(2)

    # Extract iget for method name
    iget_pattern = r"iget-object\s+([vp]\d+|p1),\s*p1,\s*(L[^;]+;->[a-zA-Z0-9_]+:Ljava/lang/String;)"
    iget_match = re.search(iget_pattern, method_body)
    if not iget_match:
        print("[-] Could not extract method name field access.")
        return False
    
    method_field = iget_match.group(2)

    # Extract success call
    success_pattern = r"(check-cast\s+p2,\s*(L[^;]+;)\s+)?invoke-(virtual|interface)\s*\{p2,\s*([vp]\d+)\},\s*(L[^;]+;->success\(Ljava/lang/Object;\)V)"
    success_match = re.search(success_pattern, method_body)
    if not success_match:
        print("[-] Could not extract success call pattern.")
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
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("[+] Patched FreeRASP successfully.")
        return True
    else:
        print("[-] FreeRASP patch attempted but content remained unchanged.")
        return False

def patch(target_dir: str) -> bool:
    print(f"[*] Searching for files to patch in {target_dir}...")

    # Rules mapping file paths (or parts of file paths) to a list of (regex_pattern, replacement)
    rules = [
        # 1. License Check Bypass
        (
            "**/LicenseContentProvider.smali",
            [
                (
                    r"(\.method public onCreate\(\)Z)([\s\S]*?)(\.end method)",
                    r"""\1
    .locals 1

    const/4 v0, 0x1
    return v0
\3"""
                )
            ]
        ),
        
        # 2. Package Info Plus - Install Source Bypass (com.android.vending)
        (
            "**/*.smali",
            [
                (
                    r"(sget\s+([pv]\d+),\s*Landroid/os/Build\$VERSION;->SDK_INT:I\s+const/16\s+[pv]\d+,\s*0x1e[\s\S]{1,500}?getInstallerPackageName\(Ljava/lang/String;\)Ljava/lang/String;\s+move-result-object\s+([pv]\d+))",
                    r'sget \2, Landroid/os/Build$VERSION;->SDK_INT:I\n\n    const-string \3, "com.android.vending"'
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
            
    # Apply dynamic patching for FreeRASP
    patch_freerasp(target_dir)
            
    return True

def patch_all(root_dir="."):
    print(f"[*] Starting patch process in root directory: {root_dir}")
    
    # Find all directories that start with 'smali'
    smali_dirs = []
    for entry in os.listdir(root_dir):
        full_path = os.path.join(root_dir, entry)
        if os.path.isdir(full_path) and entry.startswith('smali'):
            smali_dirs.append(full_path)

    if not smali_dirs:
        print("[-] No smali directories found in the current directory.")
        return False

    print(f"[*] Found smali directories: {', '.join(smali_dirs)}")
    
    # Run patch process for each smali directory
    for smali_dir in smali_dirs:
        patch(smali_dir)
        
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch_all(target)

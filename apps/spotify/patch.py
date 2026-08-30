"""
Spotify App Patch — Kosher & Media Tweaks:
1. Deletes sharehousekeepingworker.smali
2. Nulls EsImage$ImageData getData()
3. Nulls VideoSurfaceView getTextureView()
4. Disables notification album art (MediaMetadataCompat ALBUM_ART_URI)
"""

import os
import re


def patch(decompiled_dir: str) -> bool:
    print(f"[*] Starting Spotify custom patches in {decompiled_dir}...")

    # 1. Housekeeping Worker & Media View Nulling
    print("[*] Applying Spotify worker and media view patches...")
    target_worker_file = "sharehousekeepingworker.smali"
    for root, dirs, files in os.walk(decompiled_dir):
        for filename in files:
            if filename.lower() == target_worker_file:
                try:
                    os.remove(os.path.join(root, filename))
                    print(f"[+] Deleted {filename}")
                except Exception as e:
                    print(f"[-] Failed to delete {filename}: {e}")

        if "EsImage$ImageData.smali" in files:
            file_path = os.path.join(root, "EsImage$ImageData.smali")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(
                r"(\.method public final getData\(\)L.*?;.*?)(\.line \d+.*?iget-object\s+[vp]\d+,\s+[vp]\d+,\s+Lcom\/spotify\/image\/esperanto\/proto\/EsImage\$ImageData;->.*?:L.*?;)(.*?.end method)",
                r"\1\n    const/4 v0, 0x0\n    return-object v0\n\3",
                content,
                flags=re.DOTALL,
            )
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print("[+] Patched EsImage$ImageData")

        if "VideoSurfaceView.smali" in files:
            file_path = os.path.join(root, "VideoSurfaceView.smali")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(
                r"(\.method public getTextureView\(\)Landroid\/view\/TextureView;.*?)(\.line \d+.*?iget-object\s+[vp]\d+,\s+[vp]\d+,\s+Lcom\/spotify\/betamax\/player\/VideoSurfaceView;->.*?:Landroid\/view\/TextureView;)(.*?.end method)",
                r"\1\n    const/4 v0, 0x0\n    return-object v0\n\3",
                content,
                flags=re.DOTALL,
            )
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print("[+] Patched VideoSurfaceView")

    # 2. Disable Notification Album Art (MediaMetadataCompat)
    print("\n[*] Disabling notification album art (mandatory)...")
    builder_re = re.compile(
        r"new-instance\s+[vp]\d+,\s+Landroid/support/v4/media/MediaMetadataCompat;"
    )

    art_uri_invoke_re = re.compile(
        r'(const-string\s+[vp]\d+,\s*"android\.media\.metadata\.ALBUM_ART_URI"\s*\n)'
        r"(?:[ \t]*(?:\.[^\n]*)?\n)*"
        r"\s*(invoke-virtual\s+\{[^}]+\},\s*L[^;]+;->[a-zA-Z0-9_$]+\([^)]*\)[^\s]+)",
        re.MULTILINE,
    )

    target_path = None
    target_content = None

    for root, dirs, files in os.walk(decompiled_dir):
        for file in files:
            if not file.endswith(".smali"):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            if builder_re.search(content) and "ALBUM_ART_URI" in content:
                target_path = path
                target_content = content
                break
        if target_path:
            break

    if not target_path or not target_content:
        print("[!] MediaMetadataCompat builder file not found or not present in this build.")
        return True

    print(f"[i] Builder file located: {target_path}")

    match = art_uri_invoke_re.search(target_content)
    if not match:
        print("[!] Warning: Could not match the ALBUM_ART_URI invoke pattern.")
        return True

    new_content, count = art_uri_invoke_re.subn(r"\1# \2", target_content)
    if count > 0:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[+] Notification album art disabled successfully in {target_path}")

    return True

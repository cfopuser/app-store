"""
Frida Gadget Binary Manager & Smali Loader Injector.
Handles downloading/caching Frida gadget binaries, stealth renaming, and smali System.loadLibrary injection.
"""

from __future__ import annotations

import json
import lzma
import os
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from core.frida.builder import build_gadget_script


DEFAULT_FRIDA_VERSION = "16.6.6"
SUPPORTED_ABIS = ["arm64-v8a", "armeabi-v7a", "x86_64", "x86"]
ANDROID_NS = "http://schemas.android.com/apk/res/android"


ABI_FRIDA_MAP = {
    "arm64-v8a": "arm64",
    "armeabi-v7a": "arm",
    "x86_64": "x86_64",
    "x86": "x86",
}


def get_cache_dir() -> str:
    """Return the absolute path to core/frida/bin/."""
    cache_dir = os.path.join(os.path.dirname(__file__), "bin")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def ensure_gadget_binary(abi: str, version: str = DEFAULT_FRIDA_VERSION, cache_dir: str | None = None) -> str:
    """
    Ensure the Frida Gadget shared library for the specified ABI is cached locally.
    Downloads and decompresses .xz archive from GitHub releases if not cached.

    Args:
        abi: Android ABI ('arm64-v8a', 'armeabi-v7a', 'x86_64', 'x86').
        version: Frida release version tag.
        cache_dir: Optional custom cache directory.

    Returns:
        Absolute path to the decompressed .so file.
    """
    if abi not in SUPPORTED_ABIS:
        raise ValueError(f"Unsupported Android ABI: {abi}. Must be one of {SUPPORTED_ABIS}")

    if cache_dir is None:
        cache_dir = get_cache_dir()
    os.makedirs(cache_dir, exist_ok=True)

    target_so_path = os.path.join(cache_dir, f"frida-gadget-{version}-android-{abi}.so")
    if os.path.isfile(target_so_path) and os.path.getsize(target_so_path) > 0:
        return target_so_path

    frida_arch = ABI_FRIDA_MAP.get(abi, abi)
    # Download from GitHub Releases
    url = f"https://github.com/frida/frida/releases/download/{version}/frida-gadget-{version}-android-{frida_arch}.so.xz"
    print(f"[*] [Frida] Downloading Gadget ({abi}) from {url}...")

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "bit-updates/apk-patcher"}
        )
        with urllib.request.urlopen(req) as resp:
            compressed_data = resp.read()
        
        print(f"[*] [Frida] Decompressing Gadget ({abi})...")
        decompressed_data = lzma.decompress(compressed_data)
        
        with open(target_so_path, "wb") as f:
            f.write(decompressed_data)
            
        print(f"[+] [Frida] Saved Gadget binary to {target_so_path}")
        return target_so_path
    except Exception as exc:
        print(f"[-] [Frida] Failed to download Gadget for {abi}: {exc}")
        raise RuntimeError(f"Could not retrieve Frida Gadget for {abi}: {exc}") from exc


def detect_target_abis(decompiled_dir: str) -> list[str]:
    """
    Detect native ABIs present in decompiled_dir/lib/.
    If no native libraries exist, defaults to ['arm64-v8a', 'armeabi-v7a'].
    """
    lib_dir = os.path.join(decompiled_dir, "lib")
    if os.path.isdir(lib_dir):
        found_abis = [
            d for d in os.listdir(lib_dir)
            if os.path.isdir(os.path.join(lib_dir, d)) and d in SUPPORTED_ABIS
        ]
        if found_abis:
            return sorted(found_abis)

    # Pure Java/Kotlin app without native libs -> provide all 4 ABIs for maximum device and emulator compatibility
    return ["arm64-v8a", "armeabi-v7a", "x86_64", "x86"]


def _find_class_smali_file(decompiled_dir: str, class_name: str) -> str | None:
    """Find the smali file path corresponding to a Java class name."""
    clean_name = class_name.strip().lstrip(".")
    rel_path = clean_name.replace(".", os.sep) + ".smali"

    # Search in smali, smali_classes2, smali_classes3, etc.
    for item in sorted(os.listdir(decompiled_dir)):
        if item.startswith("smali"):
            candidate = os.path.join(decompiled_dir, item, rel_path)
            if os.path.isfile(candidate):
                return candidate

    filename = os.path.basename(rel_path)
    for root, _, files in os.walk(decompiled_dir):
        if filename in files:
            full_path = os.path.join(root, filename)
            if rel_path.replace(os.sep, "/") in full_path.replace(os.sep, "/"):
                return full_path

    return None


def _get_target_loader_class(decompiled_dir: str) -> tuple[str | None, str]:
    """
    Identify either Application class or Main Activity class to inject the loader.
    Returns (resolved_smali_file_path, class_descriptor_name).
    """
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if not os.path.isfile(manifest_path):
        return None, ""

    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        pkg = root.get("package") or ""
        ns = {"android": ANDROID_NS}

        # 1. Check custom Application class
        app_elem = root.find("application")
        if app_elem is not None:
            app_name = app_elem.get(f"{{{ANDROID_NS}}}name")
            if app_name:
                if app_name.startswith("."):
                    app_name = pkg + app_name
                elif "." not in app_name:
                    app_name = f"{pkg}.{app_name}"
                
                smali_path = _find_class_smali_file(decompiled_dir, app_name)
                if smali_path and os.path.isfile(smali_path):
                    return smali_path, app_name

        # 2. Check Main Launcher Activity
        def is_main_launcher(elem: ET.Element) -> bool:
            is_main = False
            is_launcher = False
            for intent in elem.iter("intent-filter"):
                for action in intent.iter("action"):
                    if action.get(f"{{{ns['android']}}}name") == "android.intent.action.MAIN":
                        is_main = True
                for cat in intent.iter("category"):
                    if cat.get(f"{{{ns['android']}}}name") == "android.intent.category.LAUNCHER":
                        is_launcher = True
            return is_main and is_launcher

        target_act_name = None
        for act in root.iter("activity"):
            if is_main_launcher(act):
                target_act_name = act.get(f"{{{ns['android']}}}name")
                break

        if not target_act_name:
            for alias in root.iter("activity-alias"):
                if is_main_launcher(alias):
                    target_act_name = alias.get(f"{{{ns['android']}}}targetActivity")
                    break

        if target_act_name:
            if target_act_name.startswith("."):
                target_act_name = pkg + target_act_name
            elif "." not in target_act_name:
                target_act_name = f"{pkg}.{target_act_name}"

            smali_path = _find_class_smali_file(decompiled_dir, target_act_name)
            if smali_path and os.path.isfile(smali_path):
                return smali_path, target_act_name

    except Exception as exc:
        print(f"[-] [Frida] Failed to parse manifest for loader target: {exc}")

    return None, ""


def inject_smali_loader(smali_file_path: str) -> bool:
    """
    Inject `System.loadLibrary("gadget")` into the static constructor <clinit>()V of a smali class.
    """
    if not os.path.isfile(smali_file_path):
        print(f"[-] [Frida] Smali file not found: {smali_file_path}")
        return False

    with open(smali_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Idempotent check
    if 'const-string v0, "gadget"' in content and 'Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V' in content:
        print(f"[i] [Frida] Gadget loader already present in {os.path.basename(smali_file_path)}")
        return True

    injection_code = (
        "\n    # --- START INJECTION (Frida Gadget Loader) ---\n"
        "    const-string v0, \"gadget\"\n"
        "    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V\n"
        "    # --- END INJECTION ---\n"
    )

    # Check if <clinit>()V already exists
    clinit_pattern = re.compile(r"(\.method\s+(?:public\s+|private\s+|protected\s+)?static\s+constructor\s+<clinit>\(\)V)(.*?)(\.end\s+method)", re.DOTALL)
    match = clinit_pattern.search(content)

    if match:
        header = match.group(1)
        body = match.group(2)
        footer = match.group(3)

        # Check .locals / .registers
        locals_match = re.search(r"(\.locals\s+)(\d+)", body)
        if locals_match:
            count = int(locals_match.group(2))
            if count < 1:
                body = body.replace(locals_match.group(0), f"{locals_match.group(1)}1", 1)
            # Insert after locals line
            body = re.sub(r"(\.locals\s+\d+[\r\n]+)", r"\1" + injection_code, body, count=1)
        else:
            registers_match = re.search(r"(\.registers\s+)(\d+)", body)
            if registers_match:
                count = int(registers_match.group(2))
                if count < 1:
                    body = body.replace(registers_match.group(0), f"{registers_match.group(1)}1", 1)
                body = re.sub(r"(\.registers\s+\d+[\r\n]+)", r"\1" + injection_code, body, count=1)
            else:
                body = "\n    .locals 1" + injection_code + body

        new_method = header + body + footer
        new_content = content[:match.start()] + new_method + content[match.end():]
    else:
        # Append <clinit>()V at end of class
        new_clinit = (
            "\n.method static constructor <clinit>()V\n"
            "    .locals 1\n"
            + injection_code +
            "\n    return-void\n"
            ".end method\n"
        )
        new_content = content + "\n" + new_clinit

    with open(smali_file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[+] [Frida] Injected System.loadLibrary('gadget') into {os.path.basename(smali_file_path)}")
    return True


def ensure_extract_native_libs(decompiled_dir: str):
    """Ensure android:extractNativeLibs="true" is set in AndroidManifest.xml."""
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if not os.path.isfile(manifest_path):
        return

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()

        if 'android:extractNativeLibs="false"' in content:
            content = content.replace('android:extractNativeLibs="false"', 'android:extractNativeLibs="true"')
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("[+] [Frida] Changed android:extractNativeLibs='false' to 'true'")
        elif '<application' in content and 'android:extractNativeLibs' not in content:
            content = re.sub(r'<application(\s+)', r'<application\1android:extractNativeLibs="true"\1', content, count=1)
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("[+] [Frida] Added android:extractNativeLibs='true' to AndroidManifest.xml")
    except Exception as exc:
        print(f"[-] [Frida] Failed to set extractNativeLibs: {exc}")


def ensure_compressed_native_libs(decompiled_dir: str):
    """Ensure .so is removed from doNotCompress in apktool.yml so Android extracts libs."""
    yml_path = os.path.join(decompiled_dir, "apktool.yml")
    if not os.path.isfile(yml_path):
        return
    try:
        with open(yml_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = re.sub(r'^\s*-\s*[\'"]?\.?so[\'"]?\s*$', '', content, flags=re.MULTILINE)
        if new_content != content:
            with open(yml_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("[+] [Frida] Removed .so from apktool.yml doNotCompress to force native lib extraction")
    except Exception as exc:
        print(f"[-] [Frida] Failed to update apktool.yml doNotCompress: {exc}")


def inject_frida_gadget(
    decompiled_dir: str,
    config: dict[str, Any] | None = None,
    app_id: str = "",
    frida_version: str = DEFAULT_FRIDA_VERSION,
) -> bool:
    """
    Complete injection of Frida Gadget binaries, configuration, and smali loader into a decompiled APK.

    Args:
        decompiled_dir: Path to apktool decompiled directory.
        config: App configuration from app.json.
        app_id: App ID identifier.
        frida_version: Version of Frida gadget to use.

    Returns:
        True on successful injection, False on error.
    """
    if config is None:
        config = {}

    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if not os.path.isfile(manifest_path):
        print(f"[i] [Frida] AndroidManifest.xml not found in {decompiled_dir}. Skipping Frida injection.")
        return True

    print(f"[*] [Frida] Starting Frida Gadget injection for [{app_id or 'app'}]...")

    # 1. Compile JavaScript payload
    script_content = build_gadget_script(config, app_id=app_id)

    # Write assets backup
    assets_dir = os.path.join(decompiled_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    with open(os.path.join(assets_dir, "gadget_hooks.js"), "w", encoding="utf-8") as f:
        f.write(script_content)

    # 2. Detect ABIs
    target_abis = detect_target_abis(decompiled_dir)
    print(f"[*] [Frida] Target ABIs: {', '.join(target_abis)}")

    gadget_config_dict = {
        "interaction": {
            "type": "script",
            "path": "libgadget.script.so",
            "on_change": "ignore"
        }
    }
    gadget_config_json = json.dumps(gadget_config_dict, indent=2)

    # 3. Copy binaries and write configs for each ABI
    cache_dir = get_cache_dir()
    for abi in target_abis:
        target_lib_dir = os.path.join(decompiled_dir, "lib", abi)
        os.makedirs(target_lib_dir, exist_ok=True)

        # Ensure gadget binary exists
        gadget_src = ensure_gadget_binary(abi, version=frida_version, cache_dir=cache_dir)
        gadget_dst = os.path.join(target_lib_dir, "libgadget.so")
        shutil.copyfile(gadget_src, gadget_dst)

        # Write libgadget.config.so
        config_dst = os.path.join(target_lib_dir, "libgadget.config.so")
        with open(config_dst, "w", encoding="utf-8") as f:
            f.write(gadget_config_json)

        # Write libgadget.script.so (contains the JS hooks)
        script_dst = os.path.join(target_lib_dir, "libgadget.script.so")
        with open(script_dst, "w", encoding="utf-8") as f:
            f.write(script_content)

        print(f"[+] [Frida] Placed Gadget + config + script in lib/{abi}/")

    # 4. Ensure native libs extraction
    ensure_extract_native_libs(decompiled_dir)
    ensure_compressed_native_libs(decompiled_dir)

    # 5. Inject Smali Loader
    target_smali_file, class_name = _get_target_loader_class(decompiled_dir)
    if not target_smali_file:
        print("[-] [Frida] CRITICAL: Could not find Application or Launcher Activity smali file to inject loader.")
        return False

    print(f"[*] [Frida] Target loader class: {class_name} ({target_smali_file})")
    if not inject_smali_loader(target_smali_file):
        return False

    print("[+] [Frida] Frida Gadget injection completed successfully!")
    return True

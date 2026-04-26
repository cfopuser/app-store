"""
Updater injector for decompiled APKs.
"""

from __future__ import annotations

import os
import re
import shutil
import xml.etree.ElementTree as ET

from core.repository import resolve_repository


def _get_package_name(manifest_path: str) -> str | None:
    """Return the Android package name from AndroidManifest.xml."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        return root.get("package")
    except Exception as exc:
        print(f"[-] Could not parse package name from manifest: {exc}")
        return None


def _get_main_activity_smali_path(manifest_path: str) -> str | None:
    """Return the main launcher activity as a smali relative path."""
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        ns = {"android": "http://schemas.android.com/apk/res/android"}

        def is_main_launcher(element: ET.Element) -> bool:
            is_main = False
            is_launcher = False
            for intent_filter in element.iter("intent-filter"):
                for action in intent_filter.iter("action"):
                    if action.get(f"{{{ns['android']}}}name") == "android.intent.action.MAIN":
                        is_main = True
                for category in intent_filter.iter("category"):
                    if category.get(f"{{{ns['android']}}}name") == "android.intent.category.LAUNCHER":
                        is_launcher = True
            return is_main and is_launcher

        target_activity_name = None

        for activity in root.iter("activity"):
            if is_main_launcher(activity):
                target_activity_name = activity.get(f"{{{ns['android']}}}name")
                break

        if not target_activity_name:
            for alias in root.iter("activity-alias"):
                if is_main_launcher(alias):
                    target_activity_name = alias.get(f"{{{ns['android']}}}targetActivity")
                    break

        if target_activity_name:
            if target_activity_name.startswith("."):
                package_name = root.get("package")
                if not package_name:
                    return None
                target_activity_name = package_name + target_activity_name
            return target_activity_name.replace(".", "/") + ".smali"
    except Exception as exc:
        print(f"[-] Could not parse main activity from manifest: {exc}")

    return None


def _resolve_repository() -> tuple[str, str]:
    """Resolve owner/repo for updater URLs."""
    return resolve_repository()


def _next_smali_classes_dir(decompiled_dir: str) -> str:
    # מחפש את המספר העוקב הראשון שפנוי כדי למנוע שבירת רצף טעינה באנדרואיד
    idx = 2
    while True:
        candidate = f"smali_classes{idx}"
        if not os.path.isdir(os.path.join(decompiled_dir, candidate)):
            return candidate
        idx += 1


def _copy_payload_and_replace_placeholders(
    decompiled_dir: str,
    payload_dir: str,
    provider_authority: str,
    version_txt_url: str,
    download_prefix: str,
    download_middle: str,
) -> bool:
    src_updater_files = os.path.join(payload_dir, "smali", "storeautoupdater")
    src_res = os.path.join(payload_dir, "res")

    if not os.path.isdir(src_updater_files):
        print("[-] CRITICAL: 'storeautoupdater' directory not found in payload/smali.")
        return False
    if not os.path.isdir(src_res):
        print("[-] CRITICAL: 'res' directory not found in payload.")
        return False

    try:
        next_smali_dir = _next_smali_classes_dir(decompiled_dir)
        dst_smali_root = os.path.join(decompiled_dir, next_smali_dir, "storeautoupdater")
        shutil.copytree(src_updater_files, dst_smali_root, dirs_exist_ok=True)

        dst_res = os.path.join(decompiled_dir, "res")
        shutil.copytree(src_res, dst_res, dirs_exist_ok=True)

        replacements = {
            "__PROVIDER_AUTHORITY__": provider_authority,
            "__VERSION_TXT_URL__": version_txt_url,
            "__RELEASE_DOWNLOAD_PREFIX__": download_prefix,
            "__RELEASE_DOWNLOAD_MIDDLE__": download_middle,
        }

        for root, _, files in os.walk(dst_smali_root):
            for filename in files:
                if not filename.endswith(".smali"):
                    continue
                smali_path = os.path.join(root, filename)
                with open(smali_path, "r", encoding="utf-8") as smali_file:
                    content = smali_file.read()

                for old, new in replacements.items():
                    content = content.replace(old, new)

                with open(smali_path, "w", encoding="utf-8") as smali_file:
                    smali_file.write(content)

        print(f"[+] Updater payload copied to {next_smali_dir}/storeautoupdater.")
        return True
    except Exception as exc:
        print(f"[-] Failed to copy or patch updater payload: {exc}")
        return False


def _patch_manifest(manifest_path: str, provider_authority: str) -> bool:
    try:
        with open(manifest_path, "r", encoding="utf-8") as manifest_file:
            manifest_content = manifest_file.read()

        if "android.permission.REQUEST_INSTALL_PACKAGES" not in manifest_content:
            if "<application" not in manifest_content:
                print("[-] Failed to patch AndroidManifest.xml: missing <application tag.")
                return False
            manifest_content = manifest_content.replace(
                "<application",
                '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>\n    <application',
                1,
            )

        if 'android:name="storeautoupdater.GenericFileProvider"' not in manifest_content:
            manifest_components = f"""
        <service android:name="storeautoupdater.DownloadService" />
        <provider
            android:name="storeautoupdater.GenericFileProvider"
            android:authorities="{provider_authority}"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/provider_paths" />
        </provider>
"""
            if "</application>" not in manifest_content:
                print("[-] Failed to patch AndroidManifest.xml: missing </application> tag.")
                return False
            manifest_content = manifest_content.replace(
                "</application>",
                f"{manifest_components}\n    </application>",
                1,
            )

        with open(manifest_path, "w", encoding="utf-8") as manifest_file:
            manifest_file.write(manifest_content)

        print("[+] AndroidManifest.xml updated for updater.")
        return True
    except Exception as exc:
        print(f"[-] Failed to patch AndroidManifest.xml: {exc}")
        return False


def _find_activity_file(decompiled_dir: str, activity_smali_path: str) -> str | None:
    relative_path = activity_smali_path.replace("/", os.sep)

    for item in sorted(os.listdir(decompiled_dir)):
        if not item.startswith("smali"):
            continue
        candidate = os.path.join(decompiled_dir, item, relative_path)
        if os.path.isfile(candidate):
            return candidate

    filename = os.path.basename(relative_path)
    for root, _, files in os.walk(decompiled_dir):
        if filename in files and relative_path in os.path.join(root, filename):
            return os.path.join(root, filename)

    return None


def _inject_updater_call(activity_file_path: str) -> bool:
    try:
        with open(activity_file_path, "r", encoding="utf-8") as activity_file:
            content = activity_file.read()
    except Exception as exc:
        print(f"[-] Failed to read activity file: {exc}")
        return False

    if "Lstoreautoupdater/Updater;->check" in content:
        print("[i] Updater call already exists in MainActivity.")
        return True

    method_pattern = re.compile(
        r"(\.method.*?onCreate\(Landroid/os/Bundle;\)V)(.*?)(\.end method)",
        re.DOTALL,
    )
    match = method_pattern.search(content)
    if not match:
        print("[i] Could not find onCreate() in the detected MainActivity. Attempting to generate it...")
        super_pattern = re.compile(r"\.super\s+(L[^;]+;)")
        super_match = super_pattern.search(content)
        if not super_match:
            print("[-] Could not find .super class in MainActivity.")
            return False
        
        super_class = super_match.group(1)
        
        injected_method = f"""
.method protected onCreate(Landroid/os/Bundle;)V
    .locals 0

    invoke-super {{p0, p1}}, {super_class}->onCreate(Landroid/os/Bundle;)V

    # --- START INJECTION (Universal Updater) ---
    invoke-static/range {{p0 .. p0}}, Lstoreautoupdater/Updater;->check(Landroid/content/Context;)V
    # --- END INJECTION ---

    return-void
.end method
"""
        new_content = content + "\n" + injected_method
        try:
            with open(activity_file_path, "w", encoding="utf-8") as activity_file:
                activity_file.write(new_content)
            print(f"[+] Updater call and onCreate injected successfully into {os.path.basename(activity_file_path)}")
            return True
        except Exception as exc:
            print(f"[-] Failed to write activity file: {exc}")
            return False

    method_body = match.group(2)
    last_return_idx = method_body.rfind("return-void")
    if last_return_idx == -1:
        print("[-] Could not find return-void in MainActivity onCreate().")
        return False

    updater_call = (
        "\n\n    # --- START INJECTION (Universal Updater) ---\n"
        "    invoke-static/range {p0 .. p0}, Lstoreautoupdater/Updater;->check(Landroid/content/Context;)V\n"
        "    # --- END INJECTION ---\n\n    "
    )
    new_method_body = method_body[:last_return_idx] + updater_call + method_body[last_return_idx:]
    new_method = match.group(1) + new_method_body + match.group(3)
    new_content = content.replace(match.group(0), new_method, 1)

    try:
        with open(activity_file_path, "w", encoding="utf-8") as activity_file:
            activity_file.write(new_content)
        print(f"[+] Updater call injected successfully into {os.path.basename(activity_file_path)}")
        return True
    except Exception as exc:
        print(f"[-] Failed to write activity file: {exc}")
        return False


def _normalize_smali_path(smali_path: str | None) -> str | None:
    if not smali_path:
        return None

    value = smali_path.strip().lstrip("/\\")
    if not value:
        return None

    if value.endswith(".smali"):
        return value.replace("\\", "/")

    return value.replace(".", "/") + ".smali"


def inject_universal_updater(
    decompiled_dir: str,
    app_id: str,
    payload_dir: str | None = None,
    target_activity_smali: str | None = None,
) -> bool:
    """
    Inject updater payload and startup hook into an APK decompile.
    """
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if not os.path.isfile(manifest_path):
        print("[-] CRITICAL: AndroidManifest.xml not found. Cannot inject updater.")
        return False

    package_name = _get_package_name(manifest_path)
    if not package_name:
        print("[-] CRITICAL: Failed to get package name. Aborting updater injection.")
        return False

    main_activity_smali = _normalize_smali_path(target_activity_smali)
    if not main_activity_smali:
        main_activity_smali = _get_main_activity_smali_path(manifest_path)
    if not main_activity_smali:
        print("[-] CRITICAL: Could not detect Main Activity automatically.")
        return False

    repo_owner, repo_name = _resolve_repository()
    print(f"[i] Detected Repo: {repo_owner}/{repo_name}")
    print(f"[i] App ID: {app_id}")
    print(f"[i] Package Name: {package_name}")
    print(f"[i] Main Activity: {main_activity_smali}")

    provider_authority = f"{package_name}.provider"
    version_txt_url = (
        f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/main/apps/{app_id}/version.txt"
    )
    download_prefix = f"https://github.com/{repo_owner}/{repo_name}/releases/download/{app_id}-v"
    download_middle = f"/{app_id}-patched-"

    if payload_dir is None:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        payload_dir = os.path.join(repo_root, "core", "updater_payload")

    if not os.path.isdir(payload_dir):
        print(f"[-] CRITICAL: Updater payload directory not found: {payload_dir}")
        return False

    if not _copy_payload_and_replace_placeholders(
        decompiled_dir=decompiled_dir,
        payload_dir=payload_dir,
        provider_authority=provider_authority,
        version_txt_url=version_txt_url,
        download_prefix=download_prefix,
        download_middle=download_middle,
    ):
        return False

    if not _patch_manifest(manifest_path, provider_authority):
        return False

    main_activity_file = _find_activity_file(decompiled_dir, main_activity_smali)
    if not main_activity_file:
        print(f"[-] Error: Failed to locate {main_activity_smali}.")
        return False

    if not _inject_updater_call(main_activity_file):
        return False

    print("[+] Universal updater injected successfully.")
    return True

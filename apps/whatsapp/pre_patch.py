import os
import shutil
import subprocess
import sys


PATCHER_REPO = os.getenv(
    "WHATSAPP_PATCHER_REPO",
    "https://github.com/Schwartzblat/WhatsAppPatcher.git",
)
PATCHER_REF = os.getenv("WHATSAPP_PATCHER_REF", "main")
PATCHER_DIR = "WhatsAppPatcher"


def _clone_patcher(repo_dir: str):
    # Ensure the directory is fully removed before cloning
    if os.path.exists(repo_dir):
        try:
            shutil.rmtree(repo_dir, ignore_errors=True)
        except Exception:
            # Fallback for Windows file locks
            import subprocess
            if os.name == 'nt':
                subprocess.call(['rmdir', '/S', '/Q', repo_dir], shell=True)
            else:
                subprocess.call(['rm', '-rf', repo_dir])

    subprocess.check_call(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            PATCHER_REF,
            PATCHER_REPO,
            repo_dir,
        ]
    )


def _install_dependencies(repo_dir: str):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", os.path.join(repo_dir, "requirements.txt")]
    )
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "stitch-test",
            "--index-url",
            "https://test.pypi.org/simple/",
            "--extra-index-url",
            "https://pypi.org/simple",
        ]
    )


def _apply_firebase_bypass(repo_dir: str):
    main_py_path = os.path.join(repo_dir, "main.py")
    if os.path.exists(main_py_path):
        with open(main_py_path, "r", encoding="utf-8") as file:
            content = file.read()
        content = content.replace("FirebaseParamsFinder(args),", "")
        with open(main_py_path, "w", encoding="utf-8") as file:
            file.write(content)

    java_path = os.path.join(
        repo_dir,
        "smali_generator",
        "app",
        "src",
        "main",
        "java",
        "com",
        "smali_generator",
        "TheAmazingPatch.java",
    )
    if os.path.exists(java_path):
        with open(java_path, "r", encoding="utf-8") as file:
            content = file.read()
        content = content.replace("new FirebaseParams(),", "")
        with open(java_path, "w", encoding="utf-8") as file:
            file.write(content)


def pre_patch(apk_path: str) -> bool:
    """
    Applies Schwartzblat WhatsApp patcher on the downloaded APK.
    """
    print(f"[*] [WhatsApp] Running APK-level patcher for: {apk_path}")

    if not os.path.exists(apk_path):
        print(f"[-] [WhatsApp] APK not found: {apk_path}")
        return False

    patched_apk = "latest_patched.apk"

    try:
        print(f"[*] [WhatsApp] Cloning patcher ({PATCHER_REF})...")
        _clone_patcher(PATCHER_DIR)

        print("[*] [WhatsApp] Installing patcher dependencies...")
        _install_dependencies(PATCHER_DIR)

        print("[*] [WhatsApp] Applying Firebase bypass customization...")
        _apply_firebase_bypass(PATCHER_DIR)

        abs_apk_path = os.path.abspath(apk_path)
        abs_output_path = os.path.abspath(patched_apk)

        print("[*] [WhatsApp] Executing patcher...")
        subprocess.check_call(
            [sys.executable, "main.py", "-p", abs_apk_path, "-o", abs_output_path, "--no-sign"],
            cwd=PATCHER_DIR,
        )

        if not os.path.exists(patched_apk):
            print("[-] [WhatsApp] Patcher completed without output APK.")
            return False

        shutil.move(patched_apk, apk_path)
        print(f"[+] [WhatsApp] Pre-patch successful: {apk_path}")
        return True

    except Exception as exc:
        print(f"[-] [WhatsApp] Pre-patch failed: {exc}")
        return False
    finally:
        if os.getenv("WHATSAPP_KEEP_PATCHER_DIR", "").lower() != "true" and os.path.exists(PATCHER_DIR):
            shutil.rmtree(PATCHER_DIR)

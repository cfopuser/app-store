## File: apps/whatsapp/pre_patch.py
import os
import subprocess
import shutil
import sys

def pre_patch(apk_path: str) -> bool:
    """
    Run Schwartzblat WhatsAppPatcher on the downloaded APK before decompiling.
    """
    print("[*] Running Schwartzblat WhatsAppPatcher as pre-patch...")
    
    cwd = os.getcwd()
    abs_apk_path = os.path.abspath(apk_path)
    out_apk_path = os.path.abspath("latest_patched.apk")
    
    try:
        # 1. Clone the patcher with its submodules
        if not os.path.exists("WhatsAppPatcher"):
            print("[*] Cloning WhatsAppPatcher with submodules...")
            # Configure git to use https instead of ssh for submodules
            subprocess.run(["git", "config", "--global", "url.https://github.com/.insteadOf", "git@github.com:"], check=True)
            subprocess.run(["git", "clone", "--recurse-submodules", "https://github.com/Schwartzblat/WhatsAppPatcher.git"], check=True)
            
        os.chdir("WhatsAppPatcher")
        
        # 2. Install required dependencies
        print("[*] Installing Patcher Dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "stitch-test", "--index-url", "https://test.pypi.org/simple/", "--extra-index-url", "https://pypi.org/simple"], check=True)
        
        # 3. Bypass Firebase patch (prevents the known API key crash)
        print("[*] Bypassing Firebase patch in WhatsAppPatcher...")
        main_path = "main.py"
        with open(main_path, "r", encoding="utf-8") as f:
            text = f.read()
        text = text.replace("FirebaseParamsFinder(args),", "")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        java_path = os.path.join("smali_generator", "app", "src", "main", "java", "com", "smali_generator", "TheAmazingPatch.java")
        if os.path.exists(java_path):
            with open(java_path, "r", encoding="utf-8") as f:
                java_text = f.read()
            java_text = java_text.replace("new FirebaseParams(),", "")
            with open(java_path, "w", encoding="utf-8") as f:
                f.write(java_text)
                
        # 4. Run the Python patcher over the APK
        print(f"[*] Running Patcher on {abs_apk_path} ...")
        res = subprocess.run([sys.executable, "main.py", "-p", abs_apk_path, "-o", out_apk_path, "--no-sign"])
        
        if res.returncode != 0 or not os.path.exists(out_apk_path):
            print("[-] WhatsApp Patcher execution failed or output file not found.")
            return False
            
        # 5. Overwrite the original downloaded APK with the patched binary
        print("[+] WhatsApp Patcher applied successfully. Replacing original APK.")
        shutil.move(out_apk_path, abs_apk_path)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[-] Subprocess error during WhatsApp pre-patch: {e}")
        return False
    except Exception as e:
        print(f"[-] Exception during WhatsApp pre-patch: {e}")
        return False
    finally:
        os.chdir(cwd)

def _download_universal_xapk(self, package_name: str, out_dir: str) -> str:
        """מזייף בקשות עבור שני פרופילי מעבדים מלאים, אוסף את החלקים, ובונה קובץ XAPK אוניברסלי"""
        os.makedirs(out_dir, exist_ok=True)
        
        dir_64 = os.path.join(out_dir, "64")
        dir_32 = os.path.join(out_dir, "32")
        os.makedirs(dir_64, exist_ok=True)
        os.makedirs(dir_32, exist_ok=True)

        # יצירת פרופיל מלא עבור מכשיר 64-ביט (חיקוי של Google Pixel 2)
        prop_64 = os.path.join(out_dir, "64.properties")
        with open(prop_64, "w") as f:
            f.write("""ro.build.version.sdk=28
ro.build.version.release=9
ro.product.device=walleye
ro.product.name=walleye
ro.product.model=Pixel 2
ro.product.manufacturer=Google
ro.product.brand=google
ro.build.id=PQ1A.181105.017.A1
ro.product.cpu.abi=arm64-v8a
ro.product.cpu.abilist=arm64-v8a,armeabi-v7a,armeabi
ro.product.locale.language=en
ro.product.locale.region=US
""")
            
        # יצירת פרופיל מלא עבור מכשיר 32-ביט (חיקוי של Google Pixel 1)
        prop_32 = os.path.join(out_dir, "32.properties")
        with open(prop_32, "w") as f:
            f.write("""ro.build.version.sdk=28
ro.build.version.release=9
ro.product.device=sailfish
ro.product.name=sailfish
ro.product.model=Pixel
ro.product.manufacturer=Google
ro.product.brand=google
ro.build.id=PQ1A.181105.017.A1
ro.product.cpu.abi=armeabi-v7a
ro.product.cpu.abilist=armeabi-v7a,armeabi
ro.product.locale.language=en
ro.product.locale.region=US
""")

        print(f"[*] [apkeep] Fetching 64-bit splits from Google Play...")
        subprocess.run([
            self.bin_path, "-a", package_name, "-d", "google-play",
            "-e", self.google_email, "-t", self.aas_token,
            "-o", f"device=default,device_properties_file={prop_64}",
            dir_64
        ], check=True, stdout=subprocess.DEVNULL)

        print(f"[*] [apkeep] Fetching 32-bit splits from Google Play...")
        subprocess.run([
            self.bin_path, "-a", package_name, "-d", "google-play",
            "-e", self.google_email, "-t", self.aas_token,
            "-o", f"device=default,device_properties_file={prop_32}",
            dir_32
        ], check=True, stdout=subprocess.DEVNULL)

        print("[*] [apkeep] Merging downloaded splits into a Universal XAPK...")
        
        all_apks = {}
        for d in [dir_64, dir_32]:
            for f in os.listdir(d):
                filepath = os.path.join(d, f)
                if f.endswith(".apk"):
                    all_apks[f] = filepath
                elif f.endswith((".apks", ".xapk")):
                    with zipfile.ZipFile(filepath, 'r') as z:
                        for zf in z.namelist():
                            if zf.endswith(".apk"):
                                ext_path = os.path.join(d, zf)
                                if not os.path.exists(ext_path):
                                    z.extract(zf, d)
                                all_apks[zf] = ext_path

        if not all_apks:
            raise RuntimeError("Failed to collect APK splits from Google Play.")

        # יצירת ה-XAPK האוניברסלי
        xapk_path = os.path.join(out_dir, f"{package_name}_universal.xapk")
        with zipfile.ZipFile(xapk_path, 'w') as z:
            z.writestr("manifest.json", '{"package_name":"' + package_name + '"}')
            for apk_name, apk_path in all_apks.items():
                z.write(apk_path, apk_name)

        return xapk_path

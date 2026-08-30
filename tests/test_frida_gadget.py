"""
Unit tests for core/frida/gadget.py
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from core.frida.gadget import (
    detect_target_abis,
    ensure_extract_native_libs,
    inject_smali_loader,
    inject_frida_gadget,
    ensure_gadget_binary,
)


class TestFridaGadget(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_detect_target_abis_with_native_libs(self):
        """Detects present ABIs in lib/ folder."""
        lib_dir = os.path.join(self.test_dir, "lib")
        os.makedirs(os.path.join(lib_dir, "arm64-v8a"))
        os.makedirs(os.path.join(lib_dir, "x86_64"))

        abis = detect_target_abis(self.test_dir)
        self.assertEqual(abis, ["arm64-v8a", "x86_64"])

    def test_detect_target_abis_pure_java(self):
        """Defaults to all 4 supported ABIs if no lib/ folder exists for max compatibility."""
        abis = detect_target_abis(self.test_dir)
        self.assertEqual(abis, ["arm64-v8a", "armeabi-v7a", "x86_64", "x86"])

    def test_inject_smali_loader_existing_clinit(self):
        """Injects System.loadLibrary into existing <clinit> method."""
        smali_path = os.path.join(self.test_dir, "TargetClass.smali")
        smali_content = """.class public Lcom/example/TargetClass;
.super Ljava/lang/Object;

.method static constructor <clinit>()V
    .locals 0

    return-void
.end method
"""
        with open(smali_path, "w", encoding="utf-8") as f:
            f.write(smali_content)

        success = inject_smali_loader(smali_path)
        self.assertTrue(success)

        with open(smali_path, "r", encoding="utf-8") as f:
            patched = f.read()

        self.assertIn('const-string v0, "gadget"', patched)
        self.assertIn("Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V", patched)
        self.assertIn(".locals 1", patched)

    def test_inject_smali_loader_no_clinit(self):
        """Creates <clinit>()V if it does not exist."""
        smali_path = os.path.join(self.test_dir, "TargetClass.smali")
        smali_content = """.class public Lcom/example/TargetClass;
.super Ljava/lang/Object;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method
"""
        with open(smali_path, "w", encoding="utf-8") as f:
            f.write(smali_content)

        success = inject_smali_loader(smali_path)
        self.assertTrue(success)

        with open(smali_path, "r", encoding="utf-8") as f:
            patched = f.read()

        self.assertIn(".method static constructor <clinit>()V", patched)
        self.assertIn('const-string v0, "gadget"', patched)
        self.assertIn("Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V", patched)

    def test_inject_smali_loader_idempotent(self):
        """Calling inject_smali_loader twice does not duplicate injection."""
        smali_path = os.path.join(self.test_dir, "TargetClass.smali")
        smali_content = """.class public Lcom/example/TargetClass;
.super Ljava/lang/Object;

.method static constructor <clinit>()V
    .locals 1
    const-string v0, "gadget"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V
    return-void
.end method
"""
        with open(smali_path, "w", encoding="utf-8") as f:
            f.write(smali_content)

        success = inject_smali_loader(smali_path)
        self.assertTrue(success)

        with open(smali_path, "r", encoding="utf-8") as f:
            patched = f.read()

        self.assertEqual(patched.count('const-string v0, "gadget"'), 1)

    def test_ensure_extract_native_libs(self):
        """Sets android:extractNativeLibs='true' in AndroidManifest.xml."""
        manifest_path = os.path.join(self.test_dir, "AndroidManifest.xml")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">\n  <application android:allowBackup="true">\n  </application>\n</manifest>')

        ensure_extract_native_libs(self.test_dir)

        with open(manifest_path, "r", encoding="utf-8") as f:
            patched = f.read()

        self.assertIn('android:extractNativeLibs="true"', patched)

    @patch("core.frida.gadget.ensure_gadget_binary")
    def test_inject_frida_gadget_full(self, mock_ensure_binary):
        """Full Frida Gadget injection places binary, config, script, and hooks smali."""
        # Setup mock dummy gadget binary
        dummy_so = os.path.join(self.test_dir, "dummy.so")
        with open(dummy_so, "wb") as f:
            f.write(b"\x7fELF_DUMMY_SO")
        mock_ensure_binary.return_value = dummy_so

        # Setup decompiled structure
        manifest_path = os.path.join(self.test_dir, "AndroidManifest.xml")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("""<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.app">
    <application android:name=".MyApplication">
        <activity android:name=".MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>""")

        smali_dir = os.path.join(self.test_dir, "smali", "com", "example", "app")
        os.makedirs(smali_dir)
        app_smali = os.path.join(smali_dir, "MyApplication.smali")
        with open(app_smali, "w", encoding="utf-8") as f:
            f.write(""".class public Lcom/example/app/MyApplication;
.super Landroid/app/Application;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Application;-><init>()V
    return-void
.end method
""")

        config = {
            "frida": {
                "webview_firewall": {
                    "allowed_domains": ["example.com"]
                }
            }
        }

        success = inject_frida_gadget(self.test_dir, config=config, app_id="test_app")
        self.assertTrue(success)

        # Check all ABIs placed for pure Java
        for abi in ["arm64-v8a", "armeabi-v7a", "x86_64", "x86"]:
            gadget_so = os.path.join(self.test_dir, "lib", abi, "libgadget.so")
            config_so = os.path.join(self.test_dir, "lib", abi, "libgadget.config.so")
            script_so = os.path.join(self.test_dir, "lib", abi, "libgadget.script.so")

            self.assertTrue(os.path.isfile(gadget_so))
            self.assertTrue(os.path.isfile(config_so))
            self.assertTrue(os.path.isfile(script_so))

            with open(config_so, "r", encoding="utf-8") as f:
                self.assertIn('"source":', f.read())

            with open(script_so, "r", encoding="utf-8") as f:
                self.assertIn("example.com", f.read())

        # Check MyApplication.smali patched
        with open(app_smali, "r", encoding="utf-8") as f:
            app_content = f.read()
            self.assertIn('const-string v0, "gadget"', app_content)
            self.assertIn("Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V", app_content)


if __name__ == "__main__":
    unittest.main()

"""
Integration tests for core/patcher.py (single-pass pipeline, AAPT2 resilience, string replacements, Frida)
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from core.patcher import (
    apply_aapt2_resilience,
    apply_string_replacements,
    run_patch,
)


class TestPatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_apply_aapt2_resilience(self):
        """Strips recreateOnConfigChanges and layout_gravity 0x0."""
        # 1. Setup manifest with buggy attribute
        manifest_path = os.path.join(self.test_dir, "AndroidManifest.xml")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write('<activity android:name=".MainActivity" android:recreateOnConfigChanges="all" />')

        # 2. Setup layout with 0x0 gravity
        layout_dir = os.path.join(self.test_dir, "res", "layout")
        os.makedirs(layout_dir)
        layout_path = os.path.join(layout_dir, "activity_main.xml")
        with open(layout_path, "w", encoding="utf-8") as f:
            f.write('<View android:layout_width="match_parent" android:layout_gravity="0x0" android:gravity="0x0" />')

        apply_aapt2_resilience(self.test_dir)

        with open(manifest_path, "r", encoding="utf-8") as f:
            self.assertNotIn("recreateOnConfigChanges", f.read())

        with open(layout_path, "r", encoding="utf-8") as f:
            layout_content = f.read()
            self.assertNotIn('android:layout_gravity="0x0"', layout_content)
            self.assertNotIn('android:gravity="0x0"', layout_content)

    def test_apply_string_replacements(self):
        """Replaces localized strings according to declarative spec."""
        res_dir = os.path.join(self.test_dir, "res")
        val_default = os.path.join(res_dir, "values")
        val_he = os.path.join(res_dir, "values-he")
        os.makedirs(val_default)
        os.makedirs(val_he)

        with open(os.path.join(val_default, "strings.xml"), "w", encoding="utf-8") as f:
            f.write('<resources><string name="target_key">Old English Value</string></resources>')

        with open(os.path.join(val_he, "strings.xml"), "w", encoding="utf-8") as f:
            f.write('<resources><string name="target_key">ערך ישן בעברית</string></resources>')

        replacements = [
            {
                "key": "target_key",
                "values": {
                    "he": "ערך חדש בעברית",
                    "default": "New English Value"
                }
            }
        ]

        apply_string_replacements(self.test_dir, replacements)

        with open(os.path.join(val_default, "strings.xml"), "r", encoding="utf-8") as f:
            self.assertIn("New English Value", f.read())

        with open(os.path.join(val_he, "strings.xml"), "r", encoding="utf-8") as f:
            self.assertIn("ערך חדש בעברית", f.read())

    @patch("core.frida.gadget.ensure_gadget_binary")
    @patch("core.patcher.load_app_config")
    def test_run_patch_full_pipeline(self, mock_load_config, mock_ensure_binary):
        """Full run_patch execution succeeds and applies all stages."""
        dummy_so = os.path.join(self.test_dir, "dummy.so")
        with open(dummy_so, "wb") as f:
            f.write(b"\x7fELF_DUMMY")
        mock_ensure_binary.return_value = dummy_so

        # Setup decompiled app structure
        manifest_path = os.path.join(self.test_dir, "AndroidManifest.xml")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("""<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.test.app">
    <application android:name=".App">
        <activity android:name=".MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>""")

        smali_dir = os.path.join(self.test_dir, "smali", "com", "test", "app")
        os.makedirs(smali_dir)
        with open(os.path.join(smali_dir, "App.smali"), "w", encoding="utf-8") as f:
            f.write(".class public Lcom/test/app/App;\n.super Landroid/app/Application;\n")
            
        with open(os.path.join(smali_dir, "MainActivity.smali"), "w", encoding="utf-8") as f:
            f.write(".class public Lcom/test/app/MainActivity;\n.super Landroid/app/Activity;\n.method protected onCreate(Landroid/os/Bundle;)V\n    .locals 0\n    return-void\n.end method\n")

        mock_load_config.return_value = {
            "id": "test_app",
            "inject_frida": True,
            "inject_updater": True,
            "frida": {
                "ssl_unpin": True,
                "root_rasp": True
            }
        }

        success = run_patch("test_app", self.test_dir)
        self.assertTrue(success)

        # Frida gadget placed
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "lib", "arm64-v8a", "libgadget.so")))
        # Updater injected
        with open(os.path.join(smali_dir, "MainActivity.smali"), "r", encoding="utf-8") as f:
            self.assertIn("Lstoreautoupdater/Updater;->check", f.read())


if __name__ == "__main__":
    unittest.main()

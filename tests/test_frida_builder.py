"""
Unit tests for core/frida/builder.py
"""

import json
import os
import unittest
from unittest.mock import patch

from core.frida.builder import build_gadget_script


class TestFridaBuilder(unittest.TestCase):

    def test_default_modules_included(self):
        """By default, SSL unpinning, Root/RASP, installer spoofing, and signature spoofing are included."""
        script = build_gadget_script(config={}, app_id="test_app")
        
        self.assertIn("[*] [Frida] Initializing Frida Gadget runtime...", script)
        self.assertIn("Universal SSL Unpinning", script)
        self.assertIn("CertificatePinner", script)
        self.assertIn("Root & RASP Bypass", script)
        self.assertIn("RootBeer", script)
        self.assertIn("Play Store Installer & PAIR Bypass", script)
        self.assertIn("com.android.vending", script)
        self.assertIn("Signature Spoofing", script)

    def test_disable_module_via_config(self):
        """Modules can be disabled explicitly in app config."""
        config = {
            "frida": {
                "ssl_unpin": False,
                "root_rasp": True,
                "installer_pair": False,
            }
        }
        script = build_gadget_script(config=config, app_id="test_app")

        self.assertNotIn("Universal SSL Unpinning", script)
        self.assertIn("Root & RASP Bypass", script)
        self.assertNotIn("Play Store Installer & PAIR Bypass", script)

    def test_webview_firewall_injection(self):
        """WebView firewall is enabled when allowed_domains is provided."""
        config = {
            "frida": {
                "webview_firewall": {
                    "allowed_domains": ["accounts.google.com", "open.spotify.com"],
                    "blocked_message": "Blocked by filter"
                }
            }
        }
        script = build_gadget_script(config=config, app_id="metrolist")

        self.assertIn("WebView Firewall", script)
        self.assertIn("accounts.google.com", script)
        self.assertIn("open.spotify.com", script)
        self.assertIn("Blocked by filter", script)

    def test_signature_spoof_hex_injection(self):
        """Original signature hex is injected if configured."""
        config = {
            "frida": {
                "signature_hex": "3082024..."
            }
        }
        script = build_gadget_script(config=config, app_id="test_app")

        self.assertIn('"3082024..."', script)

    def test_custom_inline_hooks(self):
        """Custom inline hooks from config are appended."""
        config = {
            "frida": {
                "custom_hooks": "console.log('Custom hook executed!');"
            }
        }
        script = build_gadget_script(config=config, app_id="test_app")

        self.assertIn("Custom App Hooks", script)
        self.assertIn("Custom hook executed!", script)


if __name__ == "__main__":
    unittest.main()

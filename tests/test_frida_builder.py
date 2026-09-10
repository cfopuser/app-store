"""
Unit tests for core/frida/builder.py
"""

import json
import os
import unittest
from unittest.mock import patch

from core.frida.builder import (
    build_gadget_script,
    build_standalone_bundle,
    normalize_config,
)


class TestFridaBuilder(unittest.TestCase):

    def test_default_modules_included(self):
        """By default, Anti-Frida, SSL unpinning, Root/RASP, installer spoofing, and signature spoofing are included."""
        script = build_gadget_script(config={}, app_id="test_app")
        
        self.assertIn("[*] [Frida] Initializing Frida Gadget runtime...", script)
        self.assertIn("Frida Core Hooks Engine", script)
        self.assertIn("Anti-Frida & Anti-Debug", script)
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

    def test_disable_anti_frida(self):
        """Anti-frida cloaking can be toggled off."""
        config = {
            "frida": {
                "anti_frida": False
            }
        }
        script = build_gadget_script(config=config, app_id="test_app")
        self.assertNotIn("Anti-Frida & Anti-Debug Native Cloak", script)

    def test_nested_modules_schema(self):
        """Supports the modern nested modules dictionary schema."""
        config = {
            "patching": {
                "frida": {
                    "enabled": True,
                    "log_level": "DEBUG",
                    "modules": {
                        "anti_frida": {
                            "enabled": True,
                            "block_ports": [27042]
                        },
                        "ssl_unpin": {
                            "enabled": False
                        },
                        "anti_root": {
                            "enabled": True,
                            "bypass_emulator": False
                        }
                    }
                }
            }
        }
        script = build_gadget_script(config=config, app_id="test_app")

        self.assertIn('"log_level": "DEBUG"', script)
        self.assertIn("Anti-Frida & Anti-Debug", script)
        self.assertIn("Root & RASP Bypass", script)
        self.assertNotIn("Universal SSL Unpinning", script)

    def test_normalize_config(self):
        """Test normalization of both flat and nested schemas."""
        flat_cfg = {
            "frida": {
                "ssl_unpin": False,
                "root_rasp": True,
                "signature_hex": "1234abcd"
            }
        }
        norm = normalize_config(flat_cfg)
        self.assertFalse(norm["modules"]["ssl_unpin"]["enabled"])
        self.assertTrue(norm["modules"]["anti_root"]["enabled"])
        self.assertEqual(norm["modules"]["signature_spoof"]["original_signature_hex"], "1234abcd")

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

    def test_standalone_bundle(self):
        """Standalone bundle generates executable script with bootstrap trigger."""
        bundle = build_standalone_bundle(config={}, app_id="cli_test")
        self.assertIn("__FRIDA_CORE__.bootstrap", bundle)
        self.assertIn("frida-hooks-core", bundle)


if __name__ == "__main__":
    unittest.main()

"""
Frida Hook Compiler & Builder.
Compiles declarative configuration and pre-made hook modules into a bundled gadget_hooks.js payload.
"""

from __future__ import annotations

import json
import os
from typing import Any


HOOKS_DIR = os.path.join(os.path.dirname(__file__), "hooks")


def _read_hook_module(module_name: str) -> str:
    """Read a hook module file by name from core/frida/hooks/."""
    file_path = os.path.join(HOOKS_DIR, f"{module_name}.js")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Frida hook module not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def build_gadget_script(config: dict[str, Any] | None = None, app_id: str = "") -> str:
    """
    Compile and bundle all active Frida hook modules based on app configuration.

    Args:
        config: App configuration dict (from app.json).
        app_id: App ID (used for locating optional apps/<app_id>/hooks.js).

    Returns:
        Compiled JavaScript code as a single string.
    """
    if config is None:
        config = {}

    # Support both flat and nested frida configuration
    frida_config: dict[str, Any] = {}
    if "frida" in config and isinstance(config["frida"], dict):
        frida_config = config["frida"]
    elif "patching" in config and isinstance(config["patching"], dict) and "frida" in config["patching"]:
        frida_config = config["patching"]["frida"]

    # Module toggles (defaults to True for universal security disarms)
    enable_ssl_unpin = frida_config.get("ssl_unpin", True)
    enable_root_rasp = frida_config.get("root_rasp", True)
    enable_installer_pair = frida_config.get("installer_pair", True)
    enable_signature_spoof = frida_config.get("signature_spoof", True)
    
    # WebView firewall is enabled if configured with allowed_domains
    webview_config = frida_config.get("webview_firewall")
    enable_webview_firewall = bool(webview_config and (isinstance(webview_config, dict) or webview_config is True))

    bundled_sections: list[str] = [
        "/* ========================================================================= */",
        f"/* Generated Frida Gadget Payload for [{app_id or 'default'}] */",
        "/* ========================================================================= */\n",
        "(function () {",
        "    console.log('[*] [Frida] Initializing Frida Gadget runtime...');\n",
        "    function runPayload() {",
        "        if (typeof Java === 'undefined' || !Java.available) {",
        "            setTimeout(runPayload, 50);",
        "            return;",
        "        }\n"
    ]

    # 1. SSL Unpinning
    if enable_ssl_unpin:
        ssl_code = _read_hook_module("ssl_unpin")
        bundled_sections.append("// --- Module: Universal SSL Unpinning ---")
        bundled_sections.append(ssl_code)
        bundled_sections.append("")

    # 2. Root & RASP Bypass
    if enable_root_rasp:
        root_code = _read_hook_module("root_rasp")
        bundled_sections.append("// --- Module: Root & RASP Bypass ---")
        bundled_sections.append(root_code)
        bundled_sections.append("")

    # 3. Installer Spoofing & PAIR Bypass
    if enable_installer_pair:
        installer_code = _read_hook_module("installer_pair")
        bundled_sections.append("// --- Module: Play Store Installer & PAIR Bypass ---")
        bundled_sections.append(installer_code)
        bundled_sections.append("")

    # 4. Signature Spoofing
    if enable_signature_spoof:
        sig_code = _read_hook_module("signature_spoof")
        sig_hex = frida_config.get("signature_hex")
        sig_b64 = frida_config.get("signature_base64")
        
        sig_code = sig_code.replace("/*__ORIGINAL_SIGNATURE_HEX__*/ null", json.dumps(sig_hex) if sig_hex else "null")
        sig_code = sig_code.replace("/*__ORIGINAL_SIGNATURE_BASE64__*/ null", json.dumps(sig_b64) if sig_b64 else "null")
        
        bundled_sections.append("// --- Module: Signature Spoofing ---")
        bundled_sections.append(sig_code)
        bundled_sections.append("")

    # 5. WebView Domain Whitelist Firewall
    if enable_webview_firewall:
        wf_code = _read_hook_module("webview_firewall")
        allowed_domains = []
        blocked_msg = "הגישה לקישור זה נחסמה"

        if isinstance(webview_config, dict):
            allowed_domains = webview_config.get("allowed_domains", [])
            blocked_msg = webview_config.get("blocked_message", blocked_msg)

        wf_code = wf_code.replace("/*__ALLOWED_DOMAINS__*/ []", json.dumps(allowed_domains, ensure_ascii=False))
        wf_code = wf_code.replace("/*__BLOCKED_MESSAGE__*/ \"הגישה לקישור זה נחסמה\"", json.dumps(blocked_msg, ensure_ascii=False))
        
        bundled_sections.append("// --- Module: WebView Firewall ---")
        bundled_sections.append(wf_code)
        bundled_sections.append("")

    # 6. Custom App Hooks (apps/<app_id>/hooks.js or config["frida"]["custom_hooks"])
    custom_hooks_content: list[str] = []

    if app_id:
        custom_app_hooks_file = os.path.join("apps", app_id, "hooks.js")
        if os.path.isfile(custom_app_hooks_file):
            with open(custom_app_hooks_file, "r", encoding="utf-8") as f:
                custom_hooks_content.append(f"// Custom app hooks from {custom_app_hooks_file}\n" + f.read())

    inline_custom = frida_config.get("custom_hooks")
    if inline_custom:
        if isinstance(inline_custom, list):
            custom_hooks_content.append("\n".join(inline_custom))
        elif isinstance(inline_custom, str):
            custom_hooks_content.append(inline_custom)

    if custom_hooks_content:
        bundled_sections.append("// --- Module: Custom App Hooks ---")
        bundled_sections.extend(custom_hooks_content)
        bundled_sections.append("")

    bundled_sections.append("        console.log('[+] [Frida] All configured modules loaded successfully.');")
    bundled_sections.append("    }")
    bundled_sections.append("")
    bundled_sections.append("    setTimeout(runPayload, 20);")
    bundled_sections.append("})();\n")

    return "\n".join(bundled_sections)

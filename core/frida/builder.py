"""
Frida Core Hooks Engine Compiler & Bundler (frida-hooks-core).
Compiles declarative configuration and modular hooks into a unified gadget_hooks.js payload.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


ENGINE_DIR = os.path.join(os.path.dirname(__file__), "runtime")
HOOKS_DIR = os.path.join(os.path.dirname(__file__), "hooks")

MODULE_FILE_MAP = {
    "anti_frida": "anti_frida",
    "anti_root": "anti_root",
    "root_rasp": "anti_root",  # Compatibility alias
    "ssl_unpin": "ssl_unpin",
    "installer_pair": "installer_pair",
    "signature_spoof": "signature_spoof",
    "webview_firewall": "webview_firewall",
}


def _read_runtime_engine() -> str:
    """Read the core micro-kernel runtime engine."""
    engine_file = os.path.join(ENGINE_DIR, "engine.js")
    if not os.path.isfile(engine_file):
        raise FileNotFoundError(f"Frida runtime engine not found: {engine_file}")
    with open(engine_file, "r", encoding="utf-8") as f:
        return f.read()


def _read_hook_module(module_name: str) -> str:
    """Read a hook module file by name from core/frida/hooks/."""
    resolved_file = MODULE_FILE_MAP.get(module_name, module_name)
    file_path = os.path.join(HOOKS_DIR, f"{resolved_file}.js")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Frida hook module not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def normalize_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Normalize app configuration into the standardized frida-hooks-core schema.
    Handles nested 'patching.frida', top-level 'frida', legacy flat flags,
    and modern 'modules' dictionaries.
    """
    if config is None:
        config = {}

    frida_raw: dict[str, Any] = {}
    if "frida" in config and isinstance(config["frida"], dict):
        frida_raw = config["frida"]
    elif "patching" in config and isinstance(config["patching"], dict) and "frida" in config["patching"]:
        frida_raw = config["patching"]["frida"]
    else:
        frida_raw = config

    normalized: dict[str, Any] = {
        "enabled": frida_raw.get("enabled", True),
        "log_level": frida_raw.get("log_level", "INFO"),
        "modules": {},
        "custom_hooks": frida_raw.get("custom_hooks")
    }

    raw_modules = frida_raw.get("modules", {}) if isinstance(frida_raw.get("modules"), dict) else {}

    # 1. anti_frida
    af_conf = raw_modules.get("anti_frida")
    if af_conf is None:
        af_enabled = frida_raw.get("anti_frida", True)
        normalized["modules"]["anti_frida"] = {
            "enabled": af_enabled,
            "block_ports": frida_raw.get("frida_ports", [27042, 27047]),
            "cloak_proc_maps": True,
            "mask_threads": True
        }
    elif isinstance(af_conf, bool):
        normalized["modules"]["anti_frida"] = {"enabled": af_conf}
    elif isinstance(af_conf, dict):
        normalized["modules"]["anti_frida"] = dict(af_conf)
        normalized["modules"]["anti_frida"].setdefault("enabled", True)

    # 2. anti_root (alias: root_rasp)
    ar_conf = raw_modules.get("anti_root") or raw_modules.get("root_rasp")
    if ar_conf is None:
        # Check flat flags: root_rasp or anti_root
        ar_enabled = frida_raw.get("anti_root", frida_raw.get("root_rasp", True))
        normalized["modules"]["anti_root"] = {
            "enabled": ar_enabled,
            "bypass_rootbeer": True,
            "bypass_talsec": True,
            "bypass_emulator": frida_raw.get("bypass_emulator", True),
            "anti_kill": True
        }
    elif isinstance(ar_conf, bool):
        normalized["modules"]["anti_root"] = {"enabled": ar_conf}
    elif isinstance(ar_conf, dict):
        normalized["modules"]["anti_root"] = dict(ar_conf)
        normalized["modules"]["anti_root"].setdefault("enabled", True)

    # 3. ssl_unpin
    ssl_conf = raw_modules.get("ssl_unpin")
    if ssl_conf is None:
        ssl_enabled = frida_raw.get("ssl_unpin", True)
        normalized["modules"]["ssl_unpin"] = {
            "enabled": ssl_enabled,
            "bypass_boringssl": True,
            "bypass_okhttp": True,
            "bypass_trust_manager": True
        }
    elif isinstance(ssl_conf, bool):
        normalized["modules"]["ssl_unpin"] = {"enabled": ssl_conf}
    elif isinstance(ssl_conf, dict):
        normalized["modules"]["ssl_unpin"] = dict(ssl_conf)
        normalized["modules"]["ssl_unpin"].setdefault("enabled", True)

    # 4. installer_pair
    ip_conf = raw_modules.get("installer_pair")
    if ip_conf is None:
        ip_enabled = frida_raw.get("installer_pair", True)
        normalized["modules"]["installer_pair"] = {
            "enabled": ip_enabled,
            "installer_package": frida_raw.get("installer_package", "com.android.vending"),
            "bypass_pair_license": True
        }
    elif isinstance(ip_conf, bool):
        normalized["modules"]["installer_pair"] = {"enabled": ip_conf}
    elif isinstance(ip_conf, dict):
        normalized["modules"]["installer_pair"] = dict(ip_conf)
        normalized["modules"]["installer_pair"].setdefault("enabled", True)

    # 5. signature_spoof
    sig_conf = raw_modules.get("signature_spoof")
    sig_hex = frida_raw.get("signature_hex") or (sig_conf.get("original_signature_hex") if isinstance(sig_conf, dict) else None)
    sig_b64 = frida_raw.get("signature_base64") or (sig_conf.get("original_signature_base64") if isinstance(sig_conf, dict) else None)

    if sig_conf is None:
        sig_enabled = frida_raw.get("signature_spoof", True)
        normalized["modules"]["signature_spoof"] = {
            "enabled": sig_enabled,
            "original_signature_hex": sig_hex,
            "original_signature_base64": sig_b64
        }
    elif isinstance(sig_conf, bool):
        normalized["modules"]["signature_spoof"] = {
            "enabled": sig_conf,
            "original_signature_hex": sig_hex,
            "original_signature_base64": sig_b64
        }
    elif isinstance(sig_conf, dict):
        normalized["modules"]["signature_spoof"] = dict(sig_conf)
        normalized["modules"]["signature_spoof"].setdefault("enabled", True)
        if sig_hex:
            normalized["modules"]["signature_spoof"]["original_signature_hex"] = sig_hex
        if sig_b64:
            normalized["modules"]["signature_spoof"]["original_signature_base64"] = sig_b64

    # 6. webview_firewall
    wf_raw = raw_modules.get("webview_firewall") or frida_raw.get("webview_firewall")
    if wf_raw:
        if isinstance(wf_raw, dict):
            allowed_domains = wf_raw.get("allowed_domains", [])
            blocked_msg = wf_raw.get("blocked_message", "הגישה לקישור זה נחסמה")
            is_enabled = wf_raw.get("enabled", bool(allowed_domains))
            normalized["modules"]["webview_firewall"] = {
                "enabled": is_enabled,
                "allowed_domains": allowed_domains,
                "blocked_message": blocked_msg
            }
        elif isinstance(wf_raw, bool):
            normalized["modules"]["webview_firewall"] = {"enabled": wf_raw, "allowed_domains": []}
    else:
        normalized["modules"]["webview_firewall"] = {"enabled": False, "allowed_domains": []}

    return normalized


def build_gadget_script(config: dict[str, Any] | None = None, app_id: str = "") -> str:
    """
    Compile and bundle all active Frida hook modules based on app configuration into
    a unified, production-grade payload for Frida Gadget or CLI.

    Args:
        config: App configuration dict (from app.json).
        app_id: App ID (used for locating optional apps/<app_id>/hooks.js).

    Returns:
        Compiled JavaScript code as a single string.
    """
    normalized_config = normalize_config(config)
    modules_config = normalized_config.get("modules", {})

    bundled_sections: list[str] = [
        "/* ========================================================================= */",
        f"/* Generated Frida Gadget Payload for [{app_id or 'default'}] */",
        "/* Frida Core Hooks Engine (frida-hooks-core) v2.0 */",
        "/* ========================================================================= */\n",
        "// [*] [Frida] Initializing Frida Gadget runtime...\n",
    ]

    # 1. Embed Micro-Kernel Engine
    bundled_sections.append("// === CORE ENGINE MICRO-KERNEL ===")
    bundled_sections.append(_read_runtime_engine())
    bundled_sections.append("")

    # 2. Anti-Frida & Anti-Debug Module
    af_opts = modules_config.get("anti_frida", {})
    if af_opts.get("enabled", True):
        bundled_sections.append("// --- Module: Anti-Frida & Anti-Debug Native Cloak ---")
        bundled_sections.append(_read_hook_module("anti_frida"))
        bundled_sections.append("")

    # 3. Universal Anti-Root & RASP Bypass Module
    ar_opts = modules_config.get("anti_root", {})
    if ar_opts.get("enabled", True):
        bundled_sections.append("// --- Module: Universal Root & RASP Bypass ---")
        bundled_sections.append(_read_hook_module("anti_root"))
        bundled_sections.append("")

    # 4. Universal SSL Unpinning Module
    ssl_opts = modules_config.get("ssl_unpin", {})
    if ssl_opts.get("enabled", True):
        bundled_sections.append("// --- Module: Universal SSL Unpinning ---")
        bundled_sections.append(_read_hook_module("ssl_unpin"))
        bundled_sections.append("")

    # 5. Play Store Installer Spoofing & PAIR Bypass Module
    ip_opts = modules_config.get("installer_pair", {})
    if ip_opts.get("enabled", True):
        bundled_sections.append("// --- Module: Play Store Installer & PAIR Bypass ---")
        bundled_sections.append(_read_hook_module("installer_pair"))
        bundled_sections.append("")

    # 6. Dynamic Signature Spoofing Module
    sig_opts = modules_config.get("signature_spoof", {})
    if sig_opts.get("enabled", True):
        sig_code = _read_hook_module("signature_spoof")
        sig_hex = sig_opts.get("original_signature_hex")
        sig_b64 = sig_opts.get("original_signature_base64")
        if sig_hex:
            sig_code = sig_code.replace("/*__ORIGINAL_SIGNATURE_HEX__*/ null", json.dumps(sig_hex))
        if sig_b64:
            sig_code = sig_code.replace("/*__ORIGINAL_SIGNATURE_BASE64__*/ null", json.dumps(sig_b64))

        bundled_sections.append("// --- Module: Signature Spoofing ---")
        bundled_sections.append(sig_code)
        bundled_sections.append("")

    # 7. WebView Firewall Module
    wf_opts = modules_config.get("webview_firewall", {})
    if wf_opts.get("enabled", False):
        wf_code = _read_hook_module("webview_firewall")
        allowed_domains = wf_opts.get("allowed_domains", [])
        blocked_msg = wf_opts.get("blocked_message", "הגישה לקישור זה נחסמה")

        wf_code = wf_code.replace("/*__ALLOWED_DOMAINS__*/ []", json.dumps(allowed_domains, ensure_ascii=False))
        wf_code = wf_code.replace('/*__BLOCKED_MESSAGE__*/ "הגישה לקישור זה נחסמה"', json.dumps(blocked_msg, ensure_ascii=False))

        bundled_sections.append("// --- Module: WebView Firewall ---")
        bundled_sections.append(wf_code)
        bundled_sections.append("")

    # 8. Custom App Hooks (apps/<app_id>/hooks.js or config inline custom_hooks)
    custom_hooks_content: list[str] = []
    if app_id:
        custom_app_hooks_file = os.path.join("apps", app_id, "hooks.js")
        if os.path.isfile(custom_app_hooks_file):
            with open(custom_app_hooks_file, "r", encoding="utf-8") as f:
                custom_hooks_content.append(f"// Custom app hooks from {custom_app_hooks_file}\n" + f.read())

    inline_custom = normalized_config.get("custom_hooks")
    if inline_custom:
        if isinstance(inline_custom, list):
            custom_hooks_content.append("\n".join(inline_custom))
        elif isinstance(inline_custom, str):
            custom_hooks_content.append(inline_custom)

    if custom_hooks_content:
        bundled_sections.append("// --- Module: Custom App Hooks ---")
        bundled_sections.extend(custom_hooks_content)
        bundled_sections.append("")

    # 9. Engine Bootstrap Trigger
    config_json_str = json.dumps(normalized_config, indent=2, ensure_ascii=False)
    bundled_sections.append("// === RUNTIME BOOTSTRAP TRIGGER ===")
    bundled_sections.append("(function () {")
    bundled_sections.append(f"    const __CONFIG__ = {config_json_str};")
    bundled_sections.append("    if (typeof globalThis !== 'undefined' && globalThis.__FRIDA_CORE__) {")
    bundled_sections.append("        globalThis.__FRIDA_CORE__.bootstrap(__CONFIG__);")
    bundled_sections.append("    }")
    bundled_sections.append("})();\n")

    return "\n".join(bundled_sections)


def build_standalone_bundle(config: dict[str, Any] | None = None, app_id: str = "") -> str:
    """Convenience alias for building a standalone bundle for CLI or Gadget."""
    return build_gadget_script(config=config, app_id=app_id)


def main() -> None:
    """CLI utility to generate Frida scripts from app configs."""
    parser = argparse.ArgumentParser(description="Frida Core Hooks Engine compiler")
    parser.add_argument("--app", default="", help="Target app ID (folder in apps/)")
    parser.add_argument("--config", default="", help="Path to custom app.json file")
    parser.add_argument("--output", "-o", default="", help="Output script path (defaults to stdout)")
    parser.add_argument("--log-level", default="INFO", help="Runtime log level (DEBUG, INFO, WARN, ERROR, NONE)")

    args = parser.parse_args()

    cfg: dict[str, Any] = {}
    if args.config and os.path.isfile(args.config):
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    elif args.app:
        app_json = os.path.join("apps", args.app, "app.json")
        if os.path.isfile(app_json):
            with open(app_json, "r", encoding="utf-8") as f:
                cfg = json.load(f)

    if args.log_level:
        cfg.setdefault("frida", {})
        if isinstance(cfg["frida"], dict):
            cfg["frida"]["log_level"] = args.log_level

    script = build_gadget_script(cfg, app_id=args.app)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"[+] Bundle written to: {args.output}")
    else:
        sys.stdout.write(script)


if __name__ == "__main__":
    main()

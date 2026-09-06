"""
Bit App Patch — Sideloading, PAIR checks, and Play Store installer verification
are handled universally by the Frida Gadget engine.
"""


def patch(decompiled_dir: str) -> bool:
    print(f"[*] [bit] Frida universal installer engine active for {decompiled_dir}")
    return True

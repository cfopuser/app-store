"""
Bezeq App Patch — Sideloading, PAIR licensing, and FreeRASP bypass
are handled universally by the Frida Gadget engine.
"""


def patch(decompiled_dir: str) -> bool:
    print(f"[*] [bezeq] Frida universal security engine active for {decompiled_dir}")
    return True

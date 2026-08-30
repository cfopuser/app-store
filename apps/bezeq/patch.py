"""
Bezeq App Patch — Sideloading, RootBeer, FreeRASP, and Installer spoofing
are handled universally by the Frida Gadget engine.
"""


def patch(decompiled_dir: str) -> bool:
    print(f"[*] [bezeq] Frida universal engine active for {decompiled_dir}")
    return True

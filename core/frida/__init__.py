"""
Frida Gadget & Universal Hooking Subsystem for bit-updates.
"""

from core.frida.builder import build_gadget_script
from core.frida.gadget import inject_frida_gadget

__all__ = ["build_gadget_script", "inject_frida_gadget"]

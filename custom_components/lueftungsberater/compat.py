"""Narrow Home Assistant compatibility helpers.

Keep intentional private-API workarounds in one place so a future Home
Assistant change is easy to detect, test and remove.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import CONF_REMOTE_HOST, ENTRY_KIND_REMOTE, entry_kind


def pin_subentry_capabilities(entry: ConfigEntry) -> None:
    """Keep read-only remote entries out of Home Assistant's room parent picker.

    Home Assistant currently caches ``supported_subentry_types`` in the private
    ``_supported_subentry_types`` field and exposes no public cache setter. Older
    remote entries may therefore retain a cached room capability until setup.
    Prefer doing nothing if that implementation detail ever disappears.
    """
    if not hasattr(entry, "_supported_subentry_types"):
        return
    remote = entry_kind(entry) == ENTRY_KIND_REMOTE or bool(
        entry.data.get(CONF_REMOTE_HOST)
    )
    object.__setattr__(entry, "_supported_subentry_types", {} if remote else None)
    clear_state_cache = getattr(entry, "clear_state_cache", None)
    if callable(clear_state_cache):
        clear_state_cache()

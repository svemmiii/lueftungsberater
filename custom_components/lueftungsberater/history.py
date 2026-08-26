"""Cleanup for the experimental v0.7.2 room-history stores.

v0.7.3 no longer keeps a second, integration-owned measurement history.
Home Assistant Recorder remains the single source of visible entity history.
This module only removes legacy v0.7.2 storage files on first setup.
"""
from __future__ import annotations

from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION

_LEGACY_PREFIX = f"{DOMAIN}.history."
_CLEANUP_FLAG = "legacy_room_history_cleaned"


def _legacy_history_keys(names: list[str]) -> list[str]:
    """Return only storage keys owned by the removed v0.7.2 history feature."""
    return sorted(name for name in names if name.startswith(_LEGACY_PREFIX))


async def async_cleanup_legacy_room_history(hass: HomeAssistant) -> None:
    """Remove legacy v0.7.2 history stores once per Home Assistant process."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_CLEANUP_FLAG):
        return

    storage_dir = Path(hass.config.path(".storage"))

    def _list_storage_names() -> list[str]:
        if not storage_dir.is_dir():
            return []
        return [path.name for path in storage_dir.iterdir() if path.is_file()]

    names = await hass.async_add_executor_job(_list_storage_names)
    for key in _legacy_history_keys(names):
        # Use Store.async_remove instead of unlinking directly so any matching
        # delayed-write bookkeeping is cleaned up through Home Assistant.
        await Store(hass, STORAGE_VERSION, key).async_remove()

    domain_data[_CLEANUP_FLAG] = True

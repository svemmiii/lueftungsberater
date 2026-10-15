"""Cleanup for the experimental v0.7.2 room-history stores.

v0.7.3 no longer keeps a second, integration-owned measurement history.
Home Assistant Recorder remains the single source of visible entity history.
This module only removes legacy v0.7.2 storage files on first setup.
"""
from __future__ import annotations

from pathlib import Path
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)

_LEGACY_PREFIX = f"{DOMAIN}.history."
_CLEANUP_FLAG = "legacy_room_history_cleaned"


def _legacy_history_keys(names: list[str], protected_entry_ids=()) -> list[str]:
    """Return only storage keys owned by the removed v0.7.2 history feature."""
    protected = {f"{_LEGACY_PREFIX}{entry_id}" for entry_id in protected_entry_ids}
    return sorted(name for name in names if name.startswith(_LEGACY_PREFIX) and name not in protected)


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

    try:
        names = await hass.async_add_executor_job(_list_storage_names)
    except Exception:  # noqa: BLE001 - legacy cleanup cannot block current rooms
        _LOGGER.warning("Legacy room-history storage could not be listed; retry on next setup",
                        exc_info=True)
        return
    # Other entries may still use the current history-enabled store.
    active_ids = {entry.entry_id for entry in hass.config_entries.async_entries(DOMAIN)}
    failed = False
    for key in _legacy_history_keys(names, active_ids):
        try:
            await Store(hass, STORAGE_VERSION, key).async_remove()
        except Exception:  # noqa: BLE001 - leave the original for a later retry
            failed = True
            _LOGGER.warning("Unable to remove legacy room-history store %s; will retry",
                            key, exc_info=True)
    if not failed:
        domain_data[_CLEANUP_FLAG] = True

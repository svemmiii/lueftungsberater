"""Lifecycle cleanup for Lüftungsassistent-owned Home Assistant stores."""
from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION, SUBENTRY_TYPE_ROOM

_ROOM_STORE_KINDS = ("airing", "co2", "decision", "mold")
_ENTRY_STORE_KINDS = ("air_quality", "recorder_entities")


def _room_store_prefix(entry_id: str, kind: str) -> str:
    return f"{DOMAIN}.{kind}.{entry_id}."


def _entry_store_key(entry_id: str, kind: str) -> str:
    return f"{DOMAIN}.{kind}.{entry_id}"


async def _storage_names(hass: HomeAssistant) -> list[str]:
    storage_dir = Path(hass.config.path(".storage"))

    def _list() -> list[str]:
        if not storage_dir.is_dir():
            return []
        return [path.name for path in storage_dir.iterdir() if path.is_file()]

    return await hass.async_add_executor_job(_list)


async def async_cleanup_orphaned_room_stores(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> set[str]:
    """Remove per-room stores whose config subentry no longer exists."""
    active_room_ids = {
        subentry.subentry_id
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    }
    removed: set[str] = set()
    for name in await _storage_names(hass):
        for kind in _ROOM_STORE_KINDS:
            prefix = _room_store_prefix(entry.entry_id, kind)
            if not name.startswith(prefix):
                continue
            room_id = name[len(prefix) :]
            if room_id and room_id not in active_room_ids:
                await Store(hass, STORAGE_VERSION, name).async_remove()
                removed.add(name)
            break
    return removed


async def async_remove_entry_stores(
    hass: HomeAssistant,
    entry_id: str,
) -> set[str]:
    """Remove every persistent store owned by a removed config entry."""
    names = await _storage_names(hass)
    removed: set[str] = set()
    room_prefixes = tuple(
        _room_store_prefix(entry_id, kind) for kind in _ROOM_STORE_KINDS
    )
    entry_keys = {
        _entry_store_key(entry_id, kind) for kind in _ENTRY_STORE_KINDS
    }
    for name in names:
        if name in entry_keys or name.startswith(room_prefixes):
            await Store(hass, STORAGE_VERSION, name).async_remove()
            removed.add(name)
    return removed

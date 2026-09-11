"""Recorder maintenance for Lüftungsassistent entities."""
from __future__ import annotations

import logging
from typing import Any, Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store

from .const import (
    DATA_RECORDER_RETENTION,
    DOMAIN,
    RECORDER_RETENTION_DAYS,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

_RECORDER_DOMAIN = "recorder"
_PURGE_SERVICE = "purge_entities"
_PURGE_HOUR = 5
_PURGE_MINUTE = 30

# Only these entities carry history that is useful on its own. The remaining
# helper/derived entities are still available live, but keeping their state
# timelines duplicates source sensors or a value already exposed by the advisor.
_RETAINED_HISTORY_SUFFIXES = (
    "_advisor",
    "_absolute_humidity",
    "_last_airing",
    "_critical_danger",
)


def _selected_entries(entries: Iterable[Any]) -> list[Any]:
    """Return entity-registry rows owned by this integration."""
    return [
        item
        for item in entries
        if getattr(item, "platform", None) == DOMAIN
        and getattr(item, "entity_id", None)
    ]


def _partition_history(entries: Iterable[Any]) -> tuple[list[str], list[str]]:
    """Split useful retained history from live-only/redundant helper history."""
    retained: set[str] = set()
    transient: set[str] = set()
    for item in _selected_entries(entries):
        entity_id = str(item.entity_id)
        unique_id = str(getattr(item, "unique_id", "") or "")
        if unique_id.endswith(_RETAINED_HISTORY_SUFFIXES):
            retained.add(entity_id)
        else:
            transient.add(entity_id)
    return sorted(retained), sorted(transient)


async def _async_purge_ids(
    hass: HomeAssistant,
    entity_ids: Iterable[str],
    *,
    keep_days: int,
) -> None:
    ids = sorted({str(entity_id) for entity_id in entity_ids if entity_id})
    if not ids or not hass.services.has_service(_RECORDER_DOMAIN, _PURGE_SERVICE):
        return
    await hass.services.async_call(
        _RECORDER_DOMAIN,
        _PURGE_SERVICE,
        {"entity_id": ids, "keep_days": keep_days},
        blocking=False,
    )


def _index_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    return Store(
        hass,
        STORAGE_VERSION,
        f"{DOMAIN}.recorder_entities.{entry_id}",
    )


async def async_refresh_recorder_entity_index(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Remember current entity IDs and purge history of entities removed later.

    Home Assistant clears registry rows when a room subentry is deleted. Keeping
    this tiny list lets the next reload still target the former entity IDs and
    prevents removed rooms from escaping this integration's retention policy.
    """
    registry = er.async_get(hass)
    current = {
        str(item.entity_id)
        for item in _selected_entries(
            er.async_entries_for_config_entry(registry, entry.entry_id)
        )
    }
    store = _index_store(hass, entry.entry_id)
    stored = await store.async_load() or {}
    previous_raw = stored.get("entity_ids", [])
    previous = {
        str(entity_id)
        for entity_id in previous_raw
        if isinstance(entity_id, str) and entity_id
    }
    removed = previous - current
    if removed:
        await _async_purge_ids(hass, removed, keep_days=0)
    await store.async_save({"entity_ids": sorted(current)})


async def async_remove_recorder_entity_index(
    hass: HomeAssistant,
    entry_id: str,
) -> None:
    """Purge known Lüftungsassistent states when the config entry is removed."""
    store = _index_store(hass, entry_id)
    stored = await store.async_load() or {}
    entity_ids = stored.get("entity_ids", [])
    if isinstance(entity_ids, list):
        await _async_purge_ids(hass, entity_ids, keep_days=0)
    await store.async_remove()


async def async_purge_recorder_history(
    hass: HomeAssistant,
    entry_ids: set[str] | None = None,
) -> None:
    """Keep useful history bounded and discard redundant helper timelines.

    The advisor/action state, indoor absolute humidity, last confirmed airing
    and hard-safety binary sensor keep RECORDER_RETENTION_DAYS. Other derived
    Lüftungsassistent entities are live helpers and are purged with keep_days=0
    during the daily maintenance run instead of duplicating source history.
    """
    if not hass.services.has_service(_RECORDER_DOMAIN, _PURGE_SERVICE):
        _LOGGER.debug("Recorder purge_entities is unavailable; skipping retention")
        return

    if entry_ids is None:
        state = hass.data.get(DOMAIN, {}).get(DATA_RECORDER_RETENTION, {})
        entry_ids = set(state.get("entry_ids", set()))

    if not entry_ids:
        return

    registry = er.async_get(hass)
    retained_ids: set[str] = set()
    transient_ids: set[str] = set()
    for entry_id in entry_ids:
        retained, transient = _partition_history(
            er.async_entries_for_config_entry(registry, entry_id)
        )
        retained_ids.update(retained)
        transient_ids.update(transient)

    await _async_purge_ids(
        hass,
        retained_ids,
        keep_days=RECORDER_RETENTION_DAYS,
    )
    await _async_purge_ids(hass, transient_ids, keep_days=0)


@callback
def async_register_recorder_retention(
    hass: HomeAssistant,
    entry: ConfigEntry,
):
    """Register one domain-wide daily purge and return an unload callback."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    state = domain_data.setdefault(
        DATA_RECORDER_RETENTION,
        {"entry_ids": set(), "entries": {}, "unsub": None, "task": None},
    )
    entry_ids: set[str] = state["entry_ids"]
    entry_ids.add(entry.entry_id)
    entries: dict[str, ConfigEntry] = state.setdefault("entries", {})
    entries[entry.entry_id] = entry
    state.setdefault("task", None)

    if state["unsub"] is None:

        @callback
        def _run_daily(_now) -> None:
            current = hass.data.get(DOMAIN, {}).get(DATA_RECORDER_RETENTION)
            if not current or not current.get("entry_ids"):
                return
            running = current.get("task")
            if running is not None and not running.done():
                return
            owner = next(iter(current.get("entries", {}).values()), None)
            if owner is None:
                return
            current["task"] = owner.async_create_background_task(
                hass,
                async_purge_recorder_history(hass),
                "Lüftungsassistent Recorder retention",
            )

        # Recorder's own nightly maintenance is scheduled around 04:12.
        # Run later so we do not intentionally queue our targeted purge at the
        # same time.
        state["unsub"] = async_track_time_change(
            hass,
            _run_daily,
            hour=_PURGE_HOUR,
            minute=_PURGE_MINUTE,
            second=0,
        )

    @callback
    def _unregister() -> None:
        current = hass.data.get(DOMAIN, {}).get(DATA_RECORDER_RETENTION)
        if not current:
            return
        current["entry_ids"].discard(entry.entry_id)
        current.get("entries", {}).pop(entry.entry_id, None)
        if current["entry_ids"]:
            return
        if current.get("unsub") is not None:
            current["unsub"]()
        task = current.get("task")
        if task is not None and not task.done():
            task.cancel()
        hass.data.get(DOMAIN, {}).pop(DATA_RECORDER_RETENTION, None)

    return _unregister

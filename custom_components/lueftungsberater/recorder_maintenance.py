"""Recorder maintenance for Lüftungsassistent entities."""
from __future__ import annotations

import logging
from typing import Any, Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_time_change
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
_REMOVED_INDEX_RETRY_DELAYS = (30, 120, 600, 1800)
_ORPHAN_INDEX_STORE_KEY = f"{DOMAIN}.recorder_orphans"

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
) -> bool:
    """Request a targeted recorder purge and report service-level success."""
    ids = sorted({str(entity_id) for entity_id in entity_ids if entity_id})
    if not ids:
        return True
    if not hass.services.has_service(_RECORDER_DOMAIN, _PURGE_SERVICE):
        return False
    try:
        # Recorder performs the heavy DB purge in its own task, but blocking=True
        # still lets us detect service/validation failures before forgetting the
        # entity IDs that must be retried on a later maintenance pass.
        await hass.services.async_call(
            _RECORDER_DOMAIN,
            _PURGE_SERVICE,
            {"entity_id": ids, "keep_days": keep_days},
            blocking=True,
        )
    except Exception:  # noqa: BLE001 - keep IDs for the next maintenance pass
        _LOGGER.warning(
            "Unable to request Recorder purge for %s",
            ", ".join(ids),
            exc_info=True,
        )
        return False
    return True


def _index_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    return Store(
        hass,
        STORAGE_VERSION,
        f"{DOMAIN}.recorder_entities.{entry_id}",
    )


def _orphan_index_store(hass: HomeAssistant) -> Store[dict[str, Any]]:
    """Return the persistent list of removed entries still awaiting purge."""
    return Store(hass, STORAGE_VERSION, _ORPHAN_INDEX_STORE_KEY)


async def _load_orphan_entry_ids(hass: HomeAssistant) -> set[str]:
    stored = await _orphan_index_store(hass).async_load() or {}
    raw = stored.get("entry_ids", [])
    return {str(item) for item in raw if isinstance(item, str) and item}


async def _save_orphan_entry_ids(hass: HomeAssistant, entry_ids: set[str]) -> None:
    store = _orphan_index_store(hass)
    if entry_ids:
        await store.async_save({"entry_ids": sorted(entry_ids)})
    else:
        await store.async_remove()


async def _remember_orphan_entry_id(hass: HomeAssistant, entry_id: str) -> None:
    entry_ids = await _load_orphan_entry_ids(hass)
    if entry_id in entry_ids:
        return
    entry_ids.add(entry_id)
    await _save_orphan_entry_ids(hass, entry_ids)


async def _forget_orphan_entry_id(hass: HomeAssistant, entry_id: str) -> None:
    entry_ids = await _load_orphan_entry_ids(hass)
    if entry_id not in entry_ids:
        return
    entry_ids.discard(entry_id)
    await _save_orphan_entry_ids(hass, entry_ids)


async def async_retry_orphaned_recorder_indexes(hass: HomeAssistant) -> set[str]:
    """Retry persistent Recorder cleanup for config entries already removed.

    A short in-memory retry chain handles transient failures immediately after
    removal. This persistent orphan list is the restart-safe backstop: whenever
    any Lüftungsassistent entry is loaded again, and on each daily maintenance
    run while the integration is active, stale removed-entry indexes are retried.
    """
    pending = await _load_orphan_entry_ids(hass)
    if not pending:
        return set()

    remaining: set[str] = set()
    for entry_id in sorted(pending):
        store = _index_store(hass, entry_id)
        stored = await store.async_load() or {}
        raw_ids = stored.get("entity_ids", [])
        ids = [item for item in raw_ids if isinstance(item, str) and item]
        if not ids:
            await store.async_remove()
            continue
        if await _async_purge_ids(hass, ids, keep_days=0):
            await store.async_remove()
            _LOGGER.info(
                "Recorder cleanup for removed Lüftungsassistent entry %s succeeded",
                entry_id,
            )
        else:
            remaining.add(entry_id)

    await _save_orphan_entry_ids(hass, remaining)
    return remaining


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
    purge_ok = True
    if removed:
        purge_ok = await _async_purge_ids(hass, removed, keep_days=0)
    # Keep failed purge candidates in the compact index so the next reload or
    # maintenance pass can retry them instead of forgetting them permanently.
    remembered = current if purge_ok else current | removed
    await store.async_save({"entity_ids": sorted(remembered)})


async def _async_retry_removed_recorder_index(
    hass: HomeAssistant,
    entry_id: str,
    attempt: int,
) -> None:
    """Retry purge for an entry which no longer exists in Config Entries.

    Once the final Lüftungsassistent entry is removed there is no daily
    integration scheduler left that could discover this orphan index later.
    Keep a short Home-Assistant-owned retry chain alive so a temporarily
    unavailable Recorder service cannot strand the retry file indefinitely.
    """
    store = _index_store(hass, entry_id)
    stored = await store.async_load() or {}
    entity_ids = stored.get("entity_ids", [])
    ids = [item for item in entity_ids if isinstance(item, str) and item]
    if not ids:
        await store.async_remove()
        await _forget_orphan_entry_id(hass, entry_id)
        return

    if await _async_purge_ids(hass, ids, keep_days=0):
        await store.async_remove()
        await _forget_orphan_entry_id(hass, entry_id)
        _LOGGER.info(
            "Recorder cleanup for removed Lüftungsassistent entry %s succeeded on retry",
            entry_id,
        )
        return

    _schedule_removed_recorder_index_retry(hass, entry_id, attempt + 1)


def _schedule_removed_recorder_index_retry(
    hass: HomeAssistant,
    entry_id: str,
    attempt: int = 0,
) -> None:
    """Schedule a bounded purge retry independent of any ConfigEntry lifecycle."""
    if attempt >= len(_REMOVED_INDEX_RETRY_DELAYS):
        _LOGGER.warning(
            "Recorder cleanup for removed Lüftungsassistent entry %s still failed; "
            "leaving its compact retry index in place",
            entry_id,
        )
        return

    delay = _REMOVED_INDEX_RETRY_DELAYS[attempt]

    @callback
    def _run(_now) -> None:
        hass.async_create_background_task(
            _async_retry_removed_recorder_index(hass, entry_id, attempt),
            f"Lüftungsassistent Recorder removal retry {entry_id}",
        )

    async_call_later(hass, delay, _run)


async def async_remove_recorder_entity_index(
    hass: HomeAssistant,
    entry_id: str,
) -> None:
    """Purge known states when a config entry is permanently removed."""
    store = _index_store(hass, entry_id)
    stored = await store.async_load() or {}
    entity_ids = stored.get("entity_ids", [])
    purge_ok = True
    if isinstance(entity_ids, list):
        purge_ok = await _async_purge_ids(hass, entity_ids, keep_days=0)
    if purge_ok:
        await store.async_remove()
        await _forget_orphan_entry_id(hass, entry_id)
    else:
        await _remember_orphan_entry_id(hass, entry_id)
        _LOGGER.warning(
            "Keeping Recorder entity index for %s because purge request failed; "
            "background retries will continue and the persistent orphan index "
            "will retry again after a later integration startup/daily run",
            entry_id,
        )
        _schedule_removed_recorder_index_retry(hass, entry_id)


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

    # Retry recorder indexes belonging to entries which were already removed.
    # This makes the cleanup survive Home Assistant restarts as long as the
    # integration is loaded again (or another Lüftungsassistent entry remains).
    await async_retry_orphaned_recorder_indexes(hass)

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
        {"entry_ids": set(), "unsub": None, "task": None, "orphan_task": None},
    )
    entry_ids: set[str] = state["entry_ids"]
    entry_ids.add(entry.entry_id)
    state.setdefault("task", None)
    orphan_task = state.setdefault("orphan_task", None)
    if orphan_task is None or orphan_task.done():
        state["orphan_task"] = hass.async_create_background_task(
            async_retry_orphaned_recorder_indexes(hass),
            "Lüftungsassistent Recorder orphan cleanup",
        )

    if state["unsub"] is None:

        @callback
        def _run_daily(_now) -> None:
            current = hass.data.get(DOMAIN, {}).get(DATA_RECORDER_RETENTION)
            if not current or not current.get("entry_ids"):
                return
            running = current.get("task")
            if running is not None and not running.done():
                return
            # The purge is domain-wide, not owned by one config entry. Bind
            # it to Home Assistant itself so unloading one of several entries
            # cannot cancel the shared daily run.
            current["task"] = hass.async_create_background_task(
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
        if current["entry_ids"]:
            return
        if current.get("unsub") is not None:
            current["unsub"]()
        task = current.get("task")
        if task is not None and not task.done():
            task.cancel()
        orphan_task = current.get("orphan_task")
        if orphan_task is not None and not orphan_task.done():
            orphan_task.cancel()
        hass.data.get(DOMAIN, {}).pop(DATA_RECORDER_RETENTION, None)

    return _unregister

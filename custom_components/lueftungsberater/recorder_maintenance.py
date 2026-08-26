"""Recorder maintenance for Lüftungsassistent entities."""
from __future__ import annotations

import logging
from typing import Any, Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DATA_RECORDER_RETENTION,
    DOMAIN,
    RECORDER_RETENTION_DAYS,
)

_LOGGER = logging.getLogger(__name__)

_RECORDER_DOMAIN = "recorder"
_PURGE_SERVICE = "purge_entities"
_PURGE_HOUR = 5
_PURGE_MINUTE = 30


def _selected_entity_ids(entries: Iterable[Any]) -> list[str]:
    """Return Lüftungsassistent entity IDs from registry entries."""
    return sorted(
        {
            str(item.entity_id)
            for item in entries
            if getattr(item, "platform", None) == DOMAIN
            and getattr(item, "entity_id", None)
        }
    )


async def async_purge_recorder_history(
    hass: HomeAssistant,
    entry_ids: set[str] | None = None,
) -> None:
    """Keep at most RECORDER_RETENTION_DAYS for our own Recorder states.

    This never creates or owns a second history store. It only asks Home
    Assistant Recorder to purge old state rows for exact entity IDs belonging
    to currently loaded Lüftungsassistent config entries.
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
    entity_ids: set[str] = set()
    for entry_id in entry_ids:
        entity_ids.update(
            _selected_entity_ids(
                er.async_entries_for_config_entry(registry, entry_id)
            )
        )

    if not entity_ids:
        return

    await hass.services.async_call(
        _RECORDER_DOMAIN,
        _PURGE_SERVICE,
        {
            "entity_id": sorted(entity_ids),
            "keep_days": RECORDER_RETENTION_DAYS,
        },
        blocking=False,
    )


@callback
def async_register_recorder_retention(
    hass: HomeAssistant,
    entry: ConfigEntry,
):
    """Register one domain-wide daily purge and return an unload callback."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    state = domain_data.setdefault(
        DATA_RECORDER_RETENTION,
        {"entry_ids": set(), "unsub": None},
    )
    entry_ids: set[str] = state["entry_ids"]
    entry_ids.add(entry.entry_id)

    if state["unsub"] is None:

        @callback
        def _run_daily(_now) -> None:
            hass.async_create_task(
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
        hass.data.get(DOMAIN, {}).pop(DATA_RECORDER_RETENTION, None)

    return _unregister

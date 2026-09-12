"""Persistent hard-safety fallback across provider outages and reloads.

Only normalized *hard* close-window decisions are persisted. Raw provider
payloads are deliberately not stored. A provider that is explicitly clear wins
immediately; unknown/unavailable states may reuse the last confirmed hard lock
for a bounded period only.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any, Literal

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_WARNING_SOURCE,
    CONF_WEATHER,
    DATA_SAFETY_STATE,
    DOMAIN,
    SAFETY_FALLBACK_MAX_AGE,
    STORAGE_VERSION,
    WARNING_SOURCE_NONE,
)

_LOGGER = logging.getLogger(__name__)

SafetyAvailability = Literal["active", "clear", "unknown"]
_WARNING_CHANNEL = "warning"
_WEATHER_CHANNEL = "weather"
_CONFIRM_WRITE_INTERVAL = timedelta(minutes=5)
_UNKNOWN_STATES = {"unknown", "unavailable", "none", ""}


def _store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}.safety_state.{entry_id}")


def _bucket(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    return hass.data.setdefault(DOMAIN, {}).setdefault(DATA_SAFETY_STATE, {})


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed.astimezone(dt_util.UTC)


def _json_reason_args(value: Any) -> dict[str, Any]:
    """Keep only simple serializable reason args in the safety store."""
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            continue
        if item is None or isinstance(item, (str, int, float, bool)):
            result[key] = item
    return result


async def _async_state(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    bucket = _bucket(hass)
    cached = bucket.get(entry.entry_id)
    if isinstance(cached, dict):
        return cached
    try:
        loaded = await _store(hass, entry.entry_id).async_load()
    except Exception:  # noqa: BLE001 - safety fallback must never break advice
        _LOGGER.warning(
            "Unable to load Lüftungsassistent safety fallback state for %s",
            entry.title,
            exc_info=True,
        )
        loaded = None
    state = dict(loaded) if isinstance(loaded, dict) else {}
    channels = state.get("channels")
    if not isinstance(channels, dict):
        state["channels"] = {}
    bucket[entry.entry_id] = state
    return state


async def _async_save_state(
    hass: HomeAssistant, entry: ConfigEntry, state: dict[str, Any]
) -> None:
    _bucket(hass)[entry.entry_id] = state
    try:
        await _store(hass, entry.entry_id).async_save(state)
    except Exception:  # noqa: BLE001 - retain the in-memory guard for this run
        _LOGGER.warning(
            "Unable to persist Lüftungsassistent safety fallback state for %s",
            entry.title,
            exc_info=True,
        )


def _record_is_valid(record: Any, source_key: str, now: datetime) -> bool:
    if not isinstance(record, dict) or str(record.get("source_key") or "") != source_key:
        return False
    valid_until = _parse_datetime(record.get("valid_until"))
    confirmed = _parse_datetime(record.get("last_confirmed_at"))
    if valid_until is None or confirmed is None:
        return False
    age = now - confirmed
    return (
        timedelta(0) <= age < SAFETY_FALLBACK_MAX_AGE
        and now < valid_until
    )


def _entry_entity_ids(hass: HomeAssistant, source_entry_id: str) -> list[str]:
    registry = er.async_get(hass)
    return [
        item.entity_id
        for item in er.async_entries_for_config_entry(registry, source_entry_id)
        if item.disabled_by is None
    ]


def _state_unknown(state: State | None) -> bool:
    return state is None or state.state in _UNKNOWN_STATES


def _warning_provider_availability(
    hass: HomeAssistant,
    entry: ConfigEntry,
    warnings: Any,
    previous: dict[str, Any] | None,
) -> tuple[SafetyAvailability, str]:
    source = entry.data.get(CONF_WARNING_SOURCE)
    source_key = str(source or "")
    if not source_key or source_key == WARNING_SOURCE_NONE:
        return "clear", source_key

    source_entry = hass.config_entries.async_get_entry(source_key)
    if source_entry is None:
        return "unknown", source_key

    # A currently confirmed hard instruction always wins and refreshes the
    # persisted guard. This is deliberately checked before availability so a
    # provider with several slots cannot be downgraded by one unrelated slot.
    if source_entry.domain == "dwd_weather_warnings":
        if bool(getattr(warnings, "weather_danger", False)):
            return "active", source_key
    elif bool(getattr(warnings, "official_close_instruction", False)) and (
        getattr(warnings, "nina_status", "none") == "danger"
    ):
        return "active", source_key

    # An explicit provider all-clear is authoritative even if old normalized
    # fallback data still exists.
    if getattr(warnings, "warning_notice_kind", None) == "all_clear":
        return "clear", source_key

    entity_ids = _entry_entity_ids(hass, source_entry.entry_id)

    # Once a hard lock has been confirmed, follow the exact source entity that
    # produced it. This prevents a new warning in another provider slot from
    # accidentally inheriting the old lock, while still keeping the old slot
    # fail-safe if *that* entity becomes unavailable.
    previous_entity = (
        str(previous.get("source_entity") or "").strip()
        if isinstance(previous, dict)
        else ""
    )
    if previous_entity:
        previous_state = hass.states.get(previous_entity)
        if _state_unknown(previous_state):
            return "unknown", source_key
        if source_entry.domain == "dwd_weather_warnings":
            # A current, available DWD source entity with no hard warning in the
            # freshly evaluated assessment is an authoritative clear.
            return "clear", source_key
        if previous_state is not None and previous_state.state == "off":
            return "clear", source_key
        if previous_state is not None and previous_state.state == "on":
            previous_ids = {
                str(item) for item in previous.get("warning_ids", []) if item
            } if isinstance(previous, dict) else set()
            current_id = str(
                previous_state.attributes.get("id")
                or previous_state.attributes.get("identifier")
                or ""
            ).strip()
            if previous_ids and current_id and current_id not in previous_ids:
                return "clear", source_key
            # Same active warning identity, but its detailed action text is
            # temporarily unavailable: reuse the bounded normalized hard lock.
            return "unknown", source_key

    if source_entry.domain == "dwd_weather_warnings":
        states: list[State | None] = []
        for entity_id in entity_ids:
            if not entity_id.startswith("sensor."):
                continue
            state = hass.states.get(entity_id)
            if state is None or "warning" in entity_id.lower() or (
                state is not None and "warning_count" in state.attributes
            ):
                states.append(state)
        if not states or any(_state_unknown(state) for state in states):
            return "unknown", source_key
        return "clear", source_key

    states = [
        hass.states.get(entity_id)
        for entity_id in entity_ids
        if entity_id.startswith("binary_sensor.")
    ]
    if not states or any(_state_unknown(state) for state in states):
        return "unknown", source_key

    # Without a previous source entity, treat a currently ON slot with missing
    # hard-detail text as unknown only when it still matches the old identity.
    live_on = [state for state in states if state is not None and state.state == "on"]
    if live_on and previous:
        previous_ids = {str(item) for item in previous.get("warning_ids", []) if item}
        current_ids = {
            str(state.attributes.get("id") or state.attributes.get("identifier") or "").strip()
            for state in live_on
        }
        current_ids.discard("")
        if previous_ids and current_ids and previous_ids.isdisjoint(current_ids):
            return "clear", source_key
        return "unknown", source_key

    return "clear", source_key


def _weather_provider_availability(
    hass: HomeAssistant,
    entry: ConfigEntry,
    weather: Any,
) -> tuple[SafetyAvailability, str]:
    entity_id = entry.data.get(CONF_WEATHER)
    source_key = str(entity_id or "")
    if not source_key:
        return "clear", source_key
    state = hass.states.get(source_key)
    if bool(getattr(weather, "weather_danger", False)) and not _state_unknown(state):
        return "active", source_key
    if _state_unknown(state):
        return "unknown", source_key
    return "clear", source_key


def _record_from_warning(
    warnings: Any, source_key: str, now: datetime
) -> dict[str, Any] | None:
    if getattr(warnings, "nina_status", "none") == "danger":
        kind = "nina_danger"
        reason_key = getattr(warnings, "nina_reason_key", None) or "nina_air_danger"
        reason_args = _json_reason_args(getattr(warnings, "nina_reason_args", {}))
    elif bool(getattr(warnings, "weather_danger", False)):
        kind = "warning_weather_danger"
        reason_key = getattr(warnings, "weather_reason_key", None) or "weather_danger"
        reason_args = _json_reason_args(getattr(warnings, "weather_reason_args", {}))
    else:
        return None

    source_entity = (
        getattr(warnings, "source_nina_entity", None)
        if kind == "nina_danger"
        else getattr(warnings, "source_weather_entity", None)
    )
    return {
        "source_key": source_key,
        "source_entity": source_entity,
        "provider_domain": getattr(warnings, "provider_domain", None),
        "kind": kind,
        "warning_ids": sorted(str(item) for item in getattr(warnings, "warning_ids", set()) if item),
        "reason_key": str(reason_key),
        "reason_args": reason_args,
        "official_close_instruction": bool(
            getattr(warnings, "official_close_instruction", False)
        ),
        "last_confirmed_at": now.isoformat(),
        "valid_until": (now + SAFETY_FALLBACK_MAX_AGE).isoformat(),
    }


def _record_from_weather(weather: Any, source_key: str, now: datetime) -> dict[str, Any]:
    return {
        "source_key": source_key,
        "provider_domain": getattr(weather, "provider_domain", None),
        "kind": "live_weather_danger",
        "reason_key": str(getattr(weather, "weather_reason_key", None) or "weather_danger"),
        "reason_args": _json_reason_args(getattr(weather, "weather_reason_args", {})),
        "last_confirmed_at": now.isoformat(),
        "valid_until": (now + SAFETY_FALLBACK_MAX_AGE).isoformat(),
    }


def _same_safety_payload(old: Any, new: dict[str, Any]) -> bool:
    if not isinstance(old, dict):
        return False
    ignored = {"last_confirmed_at", "valid_until"}
    return all(old.get(key) == value for key, value in new.items() if key not in ignored)


def _should_refresh_confirmation(old: Any, now: datetime) -> bool:
    if not isinstance(old, dict):
        return True
    confirmed = _parse_datetime(old.get("last_confirmed_at"))
    return (
        confirmed is None
        or not timedelta(0) <= now - confirmed < _CONFIRM_WRITE_INTERVAL
    )


def _apply_warning_record(warnings: Any, record: dict[str, Any]) -> None:
    warnings.provider_domain = record.get("provider_domain") or warnings.provider_domain
    warnings.warning_ids = {
        str(item) for item in record.get("warning_ids", []) if item
    }
    warnings.warning_notice_kind = None
    warnings.warning_notice_text = None
    kind = record.get("kind")
    if kind == "nina_danger":
        warnings.source_nina_entity = record.get("source_entity") or warnings.source_nina_entity
        warnings.nina_status = "danger"
        warnings.nina_reason_key = str(record.get("reason_key") or "nina_air_danger")
        warnings.nina_reason_args = dict(record.get("reason_args") or {})
        warnings.nina_original_reason = None
        warnings.official_close_instruction = True
    elif kind == "warning_weather_danger":
        warnings.source_weather_entity = record.get("source_entity") or warnings.source_weather_entity
        warnings.weather_danger = True
        warnings.weather_caution = False
        warnings.weather_reason_key = str(record.get("reason_key") or "weather_danger")
        warnings.weather_reason_args = dict(record.get("reason_args") or {})
        warnings.weather_original_reason = None
        warnings.official_close_instruction = bool(
            record.get("official_close_instruction", False)
        )


def _apply_weather_record(weather: Any, record: dict[str, Any]) -> None:
    weather.weather_danger = True
    weather.weather_caution = False
    weather.weather_reason_key = str(record.get("reason_key") or "weather_danger")
    weather.weather_reason_args = dict(record.get("reason_args") or {})
    weather.weather_original_reason = None


async def async_apply_persistent_safety_state(
    hass: HomeAssistant,
    entry: ConfigEntry,
    weather: Any,
    warnings: Any,
) -> None:
    """Persist current hard locks and apply bounded fallbacks on UNKNOWN data."""
    state = await _async_state(hass, entry)
    channels = state.setdefault("channels", {})
    if not isinstance(channels, dict):
        channels = {}
        state["channels"] = channels
    now = dt_util.utcnow()
    changed = False

    previous_warning = channels.get(_WARNING_CHANNEL)
    warning_availability, warning_source = _warning_provider_availability(
        hass, entry, warnings, previous_warning if isinstance(previous_warning, dict) else None
    )
    if warning_availability == "active":
        new_record = _record_from_warning(warnings, warning_source, now)
        if new_record is not None and (
            not _same_safety_payload(previous_warning, new_record)
            or _should_refresh_confirmation(previous_warning, now)
        ):
            channels[_WARNING_CHANNEL] = new_record
            changed = True
    elif warning_availability == "clear":
        if _WARNING_CHANNEL in channels:
            channels.pop(_WARNING_CHANNEL, None)
            changed = True
    elif _record_is_valid(previous_warning, warning_source, now):
        _apply_warning_record(warnings, previous_warning)
    elif _WARNING_CHANNEL in channels:
        channels.pop(_WARNING_CHANNEL, None)
        changed = True

    previous_weather = channels.get(_WEATHER_CHANNEL)
    weather_availability, weather_source = _weather_provider_availability(
        hass, entry, weather
    )
    if weather_availability == "active":
        new_record = _record_from_weather(weather, weather_source, now)
        if (
            not _same_safety_payload(previous_weather, new_record)
            or _should_refresh_confirmation(previous_weather, now)
        ):
            channels[_WEATHER_CHANNEL] = new_record
            changed = True
    elif weather_availability == "clear":
        if _WEATHER_CHANNEL in channels:
            channels.pop(_WEATHER_CHANNEL, None)
            changed = True
    elif _record_is_valid(previous_weather, weather_source, now):
        _apply_weather_record(weather, previous_weather)
    elif _WEATHER_CHANNEL in channels:
        channels.pop(_WEATHER_CHANNEL, None)
        changed = True

    if changed:
        await _async_save_state(hass, entry, state)


async def async_remove_persistent_safety_state(
    hass: HomeAssistant, entry_id: str
) -> None:
    """Remove normalized persistent safety state when the assistant is deleted."""
    domain_data = hass.data.get(DOMAIN)
    if isinstance(domain_data, dict):
        bucket = domain_data.get(DATA_SAFETY_STATE)
        if isinstance(bucket, dict):
            bucket.pop(entry_id, None)
            if not bucket:
                domain_data.pop(DATA_SAFETY_STATE, None)
    try:
        await _store(hass, entry_id).async_remove()
    except Exception:  # noqa: BLE001
        _LOGGER.debug(
            "Unable to remove Lüftungsassistent safety state for %s",
            entry_id,
            exc_info=True,
        )

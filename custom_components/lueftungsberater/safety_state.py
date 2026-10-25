"""Persistent hard-safety fallback across provider outages and reloads.

Only normalized *hard* close-window decisions are persisted. Raw provider
payloads are deliberately not stored. A provider that is explicitly clear wins
immediately; unknown/unavailable states may reuse the last confirmed hard lock
for a bounded period only.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from math import cos, hypot, radians
import logging
from typing import Any, Literal

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .air_sensors import state_is_fresh, state_number
from .providers import GUST_HARD_LOCK_KMH, WIND_HARD_LOCK_KMH, _wind_to_kmh
from .const import (
    CONF_WARNING_SOURCE,
    CONF_SHOW_GENERAL_WARNINGS,
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



def _weather_source_reliably_readable(
    hass: HomeAssistant, source: str, record: dict[str, Any], now: datetime,
) -> bool:
    """A previous hard-weather source can clear ONLY on reliable fresh evidence.

    Match the same 30-minute freshness, finite-number, physical range and unit
    rules used by the local weather provider. A reported state other than
    `unavailable` is not by itself evidence that a source has become safe.
    """
    state = hass.states.get(source)
    if not state_is_fresh(state):
        return False
    measurement = str(record.get("hazard_measurement") or "")
    reason = str(record.get("reason_key") or "")
    if source.startswith("weather."):
        if measurement == "condition" or reason in {
            "weather_hail_danger", "weather_thunderstorm_danger",
            "weather_exceptional_danger",
        }:
            # A real HA weather condition must be a known condition, not an
            # arbitrary nonempty string or an invalid numeric sensor payload.
            return state.state in {
                "clear-night", "cloudy", "fog", "hail", "lightning",
                "lightning-rainy", "partlycloudy", "pouring", "rainy",
                "snowy", "snowy-rainy", "sunny", "windy",
                "windy-variant", "exceptional",
            }
        # A weather entity's numeric wind values live in attributes, not in
        # `state`. Do not mistake a valid condition for valid wind telemetry.
        attrs = getattr(state, "attributes", {}) or {}
        unit = attrs.get("wind_speed_unit")
        wind = _wind_to_kmh(attrs.get("wind_speed"), unit)
        gust = _wind_to_kmh(attrs.get("wind_gust_speed"), unit)
        if measurement == "wind":
            return wind is not None and 0 <= wind <= 300
        if measurement == "gust":
            return gust is not None and 0 <= gust <= 400
        return any(value is not None and 0 <= value <= maximum
                   for value, maximum in ((wind, 300), (gust, 400)))
    if source.startswith("binary_sensor."):
        return state.state in {"on", "off"}
    if source.startswith("sensor."):
        # The previous hard danger was a physical wind/gust reading. Use the
        # same raw limits, accepted speed units and converted ranges as the
        # provider. For legacy records with no wind/gust subtype, only a valid
        # speed in either range can be trusted as clearance evidence.
        upper = 300 if measurement == "wind" else 400
        reading = state_number(hass, source, minimum=0.0, maximum=upper)
        if reading.value is None:
            return False
        speed = _wind_to_kmh(reading.value, reading.unit)
        return speed is not None and 0 <= speed <= upper
    # Unknown source types are not proof of a cleared safety condition.
    return False


def _weather_source_confirmed_safe(
    hass: HomeAssistant, source: str, record: dict[str, Any], now: datetime,
) -> bool:
    """A valid reading is not necessarily a safe reading.

    Judge the *same* hazard subtype that initiated the lock using the live
    hard-lock thresholds. Ambiguous legacy weather telemetry must not be
    discharged just because one of several attributes happens to be valid.
    """
    if not _weather_source_reliably_readable(hass, source, record, now):
        return False
    state = hass.states.get(source)
    measurement = str(record.get("hazard_measurement") or "")
    reason = str(record.get("reason_key") or "")
    if source.startswith("binary_sensor."):
        return state.state == "off"
    if source.startswith("weather."):
        if (reason in {"weather_hail_danger", "weather_thunderstorm_danger",
                       "weather_exceptional_danger"}
                or (measurement == "condition" and reason != "weather_wind_danger")):
            return state.state not in {"hail", "lightning", "lightning-rainy", "exceptional"}
        attrs = getattr(state, "attributes", {}) or {}
        unit = attrs.get("wind_speed_unit")
        wind = _wind_to_kmh(attrs.get("wind_speed"), unit)
        gust = _wind_to_kmh(attrs.get("wind_gust_speed"), unit)
        if measurement == "wind":
            return wind is not None and 0 <= wind < WIND_HARD_LOCK_KMH
        if measurement == "gust":
            return gust is not None and 0 <= gust < GUST_HARD_LOCK_KMH
        # Older records may not specify which measurement caused the lock.
        # Require BOTH physical readings to be valid and below their limits.
        return (wind is not None and gust is not None
                and 0 <= wind < WIND_HARD_LOCK_KMH
                and 0 <= gust < GUST_HARD_LOCK_KMH)
    if source.startswith("sensor."):
        maximum = 300 if measurement == "wind" else 400 if measurement == "gust" else 300
        reading = state_number(hass, source, minimum=0.0, maximum=maximum)
        speed = _wind_to_kmh(reading.value, reading.unit) if reading.value is not None else None
        if speed is None or speed < 0 or speed > maximum:
            return False
        if measurement == "wind":
            return speed < WIND_HARD_LOCK_KMH
        if measurement == "gust":
            return speed < GUST_HARD_LOCK_KMH
        # Legacy sensor without subtype: conservative, shared lowest limit.
        return speed < min(WIND_HARD_LOCK_KMH, GUST_HARD_LOCK_KMH)
    return False


_WARNING_SOURCE_ALIASES = {
    "mow": "mow", "mowas": "mow", "dwd": "dwd", "lhp": "lhp",
    "kat": "kat", "katwarn": "kat", "biw": "biw", "biwapp": "biw",
    "pol": "pol", "police": "pol", "polizei": "pol",
}


def _canonical_warning_id(value: Any) -> str:
    """Normalize known provider *aliases*, without erasing the provider identity.

    CAP identifiers from separate senders are not globally unique. In
    particular pol.shared-id must never match mow.shared-id. Bare identifiers
    stay bare and cannot cancel a source-qualified warning without trustworthy
    source attribution from the assessment that produced the reference.
    """
    text = str(value or "").strip()
    prefix, sep, suffix = text.partition(".")
    if sep and suffix:
        canonical = _WARNING_SOURCE_ALIASES.get(prefix.lower())
        if canonical:
            return f"{canonical}.{suffix}"
    return text


def _matching_warning_ids(
    previous: Any, current_ids: Any,
    current_cap_identities: Any = None,
) -> bool:
    """Require provider ID *and* CAP sender/sent for identifiable cancels.

    Legacy ID-only notices keep their existing behavior, but an actual CAP
    reference cannot cancel an older persisted warning whose sender/sent was
    never stored. That uncertainty must not silently become a CLEAR.
    """
    previous_ids = {
        _canonical_warning_id(value)
        for value in previous.get("warning_ids", []) if value
    } if isinstance(previous, dict) else set()
    cleared_ids = {_canonical_warning_id(value) for value in current_ids if value}
    if not previous_ids or not previous_ids.issubset(cleared_ids):
        return False
    raw_previous = previous.get("warning_cap_identities", {}) if isinstance(previous, dict) else {}
    raw_current = current_cap_identities if isinstance(current_cap_identities, dict) else {}
    for ident in previous_ids:
        old_signatures = {
            str(value) for key, values in raw_previous.items()
            if _canonical_warning_id(key) == ident
            for value in (values if isinstance(values, (list, set, tuple)) else [])
        } if isinstance(raw_previous, dict) else set()
        new_signatures = {
            str(value) for key, values in raw_current.items()
            if _canonical_warning_id(key) == ident
            for value in (values if isinstance(values, (list, set, tuple)) else [])
        }
        if old_signatures:
            if not old_signatures.issubset(new_signatures):
                return False
        elif new_signatures:
            # A persisted pre-upgrade warning has no sender evidence: a CAP
            # triple for the same naked ID could belong to another authority.
            return False
    return True


def _safety_location_distance_km(first: str, second: str) -> float | None:
    """Distance between two persisted auto-warning locations, or unknown.

    Key precision is 4 decimals (~11 m latitude). Treat GPS jitter as movement,
    not as evidence that an authoritative fire/smoke warning was cancelled.
    """
    try:
        old = first.split(":")
        new = second.split(":")
        if len(old) != 3 or len(new) != 3 or old[0] != "auto_warning" or new[0] != "auto_warning":
            return None
        old_lat, old_lon = float(old[1]), float(old[2])
        new_lat, new_lon = float(new[1]), float(new[2])
        if not (-90 <= old_lat <= 90 and -90 <= new_lat <= 90
                and -180 <= old_lon <= 180 and -180 <= new_lon <= 180):
            return None
        km_lat = (new_lat - old_lat) * 111.195
        km_lon = (((new_lon - old_lon + 180) % 360) - 180) * 111.195 * cos(radians((old_lat + new_lat) / 2))
        distance = hypot(km_lat, km_lon)
        return distance if distance == distance and distance != float("inf") else None
    except (TypeError, ValueError):
        return None


# Per-message providers, not just the provider of the strongest warning.  A
# single persisted hard lock can represent simultaneous NINA hazards from
# several feeds, while ``source_key`` identifies only the selected one.
_AUTO_WARNING_ID_SOURCES = {
    "mow": "nina_auto_mowas",
    "kat": "nina_auto_katwarn",
    "biw": "nina_auto_biwapp",
    "pol": "nina_auto_police",
    "dwd": "nina_auto_dwd",
    "lhp": "nina_auto_lhp",
}


def _all_previous_auto_warning_sources_resolved(
    previous: dict[str, Any],
    availability_map: dict[str, bool],
    location_key: str,
    *,
    explicit_cancellation: bool = False,
) -> bool:
    """A complete absence requires evidence for *every* old warning feed.

    Regional NINA dashboards are complete inventories when the dashboard and
    its detail/polygon evaluations succeeded; feeds absent from that inventory
    can then be considered checked too. A partial result or an available main
    feed alone is never evidence that another feed's old alert ended.
    """
    # Outside Germany, other national providers (e.g. NWS/MeteoAlarm) do not
    # expose NINA's per-feed keys. Preserve their pre-existing availability
    # semantics instead of accidentally making every non-NINA clear UNKNOWN.
    previous_key = str(previous.get("source_key") or "")
    previous_domain = str(previous.get("provider_domain") or "")
    if (":nina_auto_" not in previous_key
            and not previous_domain.startswith("nina_auto")
            and not any(key.startswith(f"{location_key}:nina_auto_") for key in availability_map)):
        return True

    complete_inventory = (
        availability_map.get(location_key) is True
        and availability_map.get(f"{location_key}:nina_auto_dashboard") is True
    )
    ids = previous.get("warning_ids", [])
    if not isinstance(ids, (list, tuple, set)) or not ids:
        # Older records without hazard IDs do not provide enough information
        # to discharge a multi-feed lock from a single feed's success.
        return complete_inventory

    for raw_id in ids:
        canonical = _canonical_warning_id(raw_id)
        prefix, sep, _identifier = canonical.partition(".")
        provider = _AUTO_WARNING_ID_SOURCES.get(prefix.lower()) if sep else None
        if provider is None:
            if not complete_inventory:
                return False
            continue
        status = availability_map.get(f"{location_key}:{provider}")
        if status is False:
            return False
        if status is not True and not complete_inventory and not explicit_cancellation:
            return False
    return True


def _manual_warning_source_unresolved(
    hass: HomeAssistant, entry: ConfigEntry, origin: str,
    warning_id: str = "",
) -> bool:
    """An offline manual HA warning source cannot certify an old alert ended."""
    manual_entry_id = origin.removeprefix("manual:")
    if not manual_entry_id or manual_entry_id != entry.data.get(CONF_WARNING_SOURCE):
        return True
    source_entry = hass.config_entries.async_get_entry(manual_entry_id)
    if source_entry is None:
        return True
    entity_ids = _entry_entity_ids(hass, source_entry.entry_id)
    checked = [hass.states.get(ident) for ident in entity_ids if ident.startswith("binary_sensor.")]
    # For a manual DWD source use the existing weather source fallback logic;
    # an ambiguous source (or no active slots) cannot cancel a stored lock.
    if source_entry.domain == "dwd_weather_warnings":
        checked = [hass.states.get(ident) for ident in entity_ids if ident.startswith("sensor.")]
    if not checked or any(_state_unknown(state) for state in checked):
        return True
    # A live ON slot with the same original identity is still a live alert,
    # even if its detail/action text was temporarily not supplied and another
    # source happens to provide the selected hard warning this cycle.
    for state in checked:
        if state is None or state.state != "on":
            continue
        current_id = str(state.attributes.get("id") or state.attributes.get("identifier") or "")
        if not current_id or _canonical_warning_id(current_id) == _canonical_warning_id(warning_id):
            return True
    return False


def _warning_components(value: Any) -> list[dict[str, str]]:
    """Return per-alert origin and CAP identity without deduplicating by ID.

    Legacy persisted states have only ID-keyed maps and remain readable.
    The new list stores distinct issuers of colliding identifiers separately.
    """
    if isinstance(value, dict):
        provided = value.get("warning_components")
        ids = value.get("warning_ids") or []
        origins = value.get("warning_origins") or {}
        cap_map = value.get("warning_cap_identities") or {}
    else:
        provided = getattr(value, "warning_components", None)
        ids = getattr(value, "warning_ids", set())
        origins = getattr(value, "warning_origins", {})
        cap_map = getattr(value, "warning_cap_identities", {})
    if isinstance(provided, list) and provided:
        parts = provided
    else:
        parts = []
        for ident in ids:
            signatures = cap_map.get(ident) if isinstance(cap_map, dict) else None
            for signature in (signatures or [""]):
                parts.append({"id": ident,
                              "origin": origins.get(ident, "") if isinstance(origins, dict) else "",
                              "cap": signature})
    result = {
        (str(item.get("id") or ""), str(item.get("origin") or ""),
         str(item.get("cap") or ""), str(item.get("entity") or ""))
        for item in parts if isinstance(item, dict) and item.get("id")
    }
    return [
        {**{"id": ident, "origin": origin, "cap": cap},
         **({"entity": entity} if entity else {})}
        for ident, origin, cap, entity in sorted(result)
    ]


def _missing_previous_warning_unresolved(
    hass: HomeAssistant,
    entry: ConfigEntry,
    warnings: Any,
    previous: dict[str, Any],
    new_record: dict[str, Any],
) -> bool:
    """Check every missing prior hazard, including manually configured feeds.

    Keep the *original* stored record on uncertainty. Do not merge it with the
    latest active warning (which would refresh an old hazard's one-hour TTL).
    """
    old_parts = _warning_components(previous)
    fresh_parts = _warning_components(new_record)
    # A matching short ID is insufficient if its CAP sender/sent or the
    # source which observed it is different. This handles auto/manual ID
    # collisions even when both originally used e.g. "mow.same-id".
    fresh_keys = {(item["id"], item["origin"], item["cap"])
                  for item in fresh_parts}
    missing = [part for part in old_parts
               if (part["id"], part["origin"], part["cap"]) not in fresh_keys]
    if not missing:
        return False
    availability = getattr(warnings, "provider_availability", {})
    old_key = str(previous.get("source_key") or "")
    old_domain = str(previous.get("provider_domain") or "")
    for part in missing:
        ident = part["id"]
        origin = part["origin"]
        if origin.startswith("manual:"):
            if _manual_warning_source_unresolved(hass, entry, origin, ident):
                return True
            continue
        if origin.startswith("auto:"):
            location = origin.removeprefix("auto:")
        elif old_key.startswith("auto_warning:"):
            # Backwards-compatible records prior to warning_origins: assume
            # the warning is automatic but don't ignore an offline manual
            # source in a previously mixed provider assessment.
            location = ":".join(old_key.split(":")[:3])
            if "+" in old_domain and entry.data.get(CONF_WARNING_SOURCE):
                if _manual_warning_source_unresolved(
                    hass, entry, f"manual:{entry.data[CONF_WARNING_SOURCE]}", ident
                ):
                    return True
        else:
            # Legacy manual records without origin metadata can still be
            # protected, rather than dropped on the first live auto refresh.
            manual_entry = entry.data.get(CONF_WARNING_SOURCE)
            if manual_entry and _manual_warning_source_unresolved(
                hass, entry, f"manual:{manual_entry}", ident
            ):
                return True
            continue
        if not isinstance(availability, dict) or not _all_previous_auto_warning_sources_resolved(
            {"source_key": f"{location}:nina_auto_mowas", "provider_domain": old_domain,
             "warning_ids": [ident]},
            availability, location,
        ):
            return True
    return False


def _warning_provider_availability(
    hass: HomeAssistant,
    entry: ConfigEntry,
    warnings: Any,
    previous: dict[str, Any] | None,
) -> tuple[SafetyAvailability, str]:
    current_safety_key = str(getattr(warnings, "safety_source_key", None) or "")
    availability_map = getattr(warnings, "provider_availability", {})
    previous_key = str(previous.get("source_key") or "") if isinstance(previous, dict) else ""

    # A new, *confirmed* manual hard warning takes precedence over clearance
    # of an older automatic warning. Otherwise an old auto source returning
    # CLEAR can prevent the newly active manual hazard from being persisted,
    # leaving no fallback when that manual feed goes offline moments later.
    # Only accept the actually configured HA warning integration, not a
    # stale/foreign source key or a mere informational NINA notice.
    selected_manual_source = str(entry.data.get(CONF_WARNING_SOURCE) or "")
    if (selected_manual_source
            and selected_manual_source != WARNING_SOURCE_NONE
            and current_safety_key == selected_manual_source):
        selected_entry = hass.config_entries.async_get_entry(selected_manual_source)
        if selected_entry is not None:
            if selected_entry.domain == "dwd_weather_warnings":
                if bool(getattr(warnings, "weather_hard_lock", False)):
                    return "active", current_safety_key
            elif (getattr(warnings, "nina_status", "none") == "danger"
                  and bool(getattr(warnings, "official_close_instruction", False))):
                return "active", current_safety_key

    if current_safety_key.startswith("auto_warning:") and (
        bool(getattr(warnings, "official_close_instruction", False))
        or bool(getattr(warnings, "weather_hard_lock", False))
    ):
        if isinstance(availability_map, dict) and availability_map.get(current_safety_key) is False:
            return "unknown", current_safety_key
        return "active", current_safety_key

    if previous_key.startswith("auto_warning:"):
        if isinstance(availability_map, dict) and previous_key in availability_map:
            if not availability_map[previous_key]:
                return "unknown", previous_key
            # The selected/strongest NINA feed may have recovered while other
            # feeds responsible for the *same stored lock* are still offline.
            # Never discharge those unresolved hazards from the main feed's
            # availability alone (including after a HA restart).
            previous_location = ":".join(previous_key.split(":")[:3])
            all_prior_cancelled = (
                getattr(warnings, "warning_notice_kind", None) == "all_clear"
                and _matching_warning_ids(
                    previous, getattr(warnings, "warning_ids", set()),
                    getattr(warnings, "warning_cap_identities", {}),
                )
            )
            if not _all_previous_auto_warning_sources_resolved(
                previous, availability_map, previous_location,
                explicit_cancellation=all_prior_cancelled,
            ):
                return "unknown", previous_key
            if getattr(warnings, "warning_ambiguous_clear", False):
                return "unknown", previous_key
            if getattr(warnings, "warning_notice_kind", None) == "all_clear":
                # A provider being available does not make a *partial* CAP
                # cancellation authoritative for all previously locked IDs.
                # A new Cancel ID is normalized to its CAP references above.
                if not _matching_warning_ids(
                    previous, getattr(warnings, "warning_ids", set()),
                    getattr(warnings, "warning_cap_identities", {}),
                ):
                    return "unknown", previous_key
            return "clear", previous_key
        # The safety key has a provider-independent location prefix followed by
        # an optional provider suffix.  Only a *different accepted location*
        # may immediately retire its old local lock; losing a provider suffix
        # at the SAME location is not evidence that the hazard ended.
        previous_location = ":".join(previous_key.split(":")[:3])
        current_location = ":".join(current_safety_key.split(":")[:3])
        if (current_safety_key.startswith("auto_warning:")
                and current_location != previous_location
                and isinstance(availability_map, dict)):
            # A change of rounded GPS coordinates (~11 m) is not a completed
            # cancellation. A failed new-location fetch likewise proves
            # nothing about the persisted hazard at the old coordinate.
            distance_km = _safety_location_distance_km(
                previous_location, current_location
            )
            fresh_inventory = availability_map.get(current_location) is True
            fresh_regional_dashboard = (
                availability_map.get(f"{current_location}:nina_auto_dashboard") is True
            )
            # Nearby: demand a complete, fresh regional candidate inventory.
            # After an actual multi-kilometre move, another successfully
            # evaluated automatic feed may confirm the new location instead.
            authoritative_new_location = (
                fresh_inventory
                and distance_km is not None
                and (fresh_regional_dashboard or distance_km >= 5.0)
            )
            if (authoritative_new_location
                    and not getattr(warnings, "warning_ambiguous_clear", False)
                    and getattr(warnings, "warning_notice_kind", None) != "all_clear"):
                return "clear", previous_key
            return "unknown", previous_key

        # A successful and *complete* regional NINA dashboard is an
        # authoritative current inventory for this coordinate, even when the
        # old individual provider has no candidates this cycle.  Merely
        # receiving data from another source (LHP, weather, etc.) is NOT.
        # Never interpret an unrelated/partial all-clear as that evidence.
        if (current_location == previous_location
                and isinstance(availability_map, dict)
                and availability_map.get(previous_location) is True
                and availability_map.get(f"{previous_location}:nina_auto_dashboard") is True
                and _all_previous_auto_warning_sources_resolved(
                    previous, availability_map, previous_location
                )
                and not getattr(warnings, "warning_ambiguous_clear", False)
                and getattr(warnings, "warning_notice_kind", None) != "all_clear"):
            return "clear", previous_key
        return "unknown", previous_key

    source = entry.data.get(CONF_WARNING_SOURCE)
    source_key = str(source or "")
    if not source_key or source_key == WARNING_SOURCE_NONE:
        return "clear", source_key

    source_entry = hass.config_entries.async_get_entry(source_key)
    if source_entry is None:
        return "unknown", source_key
    if isinstance(previous, dict) and getattr(warnings, "warning_ambiguous_clear", False):
        return "unknown", source_key

    # A currently confirmed hard instruction always wins and refreshes the
    # persisted guard. This is deliberately checked before availability so a
    # provider with several slots cannot be downgraded by one unrelated slot.
    if source_entry.domain == "dwd_weather_warnings":
        if bool(getattr(warnings, "weather_hard_lock", False)):
            return "active", str(getattr(warnings, "safety_source_key", None) or source_key)
    elif bool(getattr(warnings, "official_close_instruction", False)) and (
        getattr(warnings, "nina_status", "none") == "danger"
    ):
        return "active", str(getattr(warnings, "safety_source_key", None) or source_key)

    if getattr(warnings, "warning_ambiguous_clear", False):
        return "unknown", previous_key or source_key

    # Only a cancellation of the *same* previously relevant warning may
    # release a persisted hard lock. A drinking-water all-clear (or a new slot)
    # must never unlock an unrelated fumes warning.
    if getattr(warnings, "warning_notice_kind", None) == "all_clear":
        # All previously active window-related IDs must be resolved. Clearing
        # one of two simultaneous hazards must not release their shared lock.
        if (_matching_warning_ids(
            previous, getattr(warnings, "warning_ids", set()),
            getattr(warnings, "warning_cap_identities", {}),
        )
                and previous_key == source_key):
            return "clear", source_key
        return "unknown", source_key

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
            prior_ids = set(previous.get("warning_ids", [])) if isinstance(previous, dict) else set()
            if len(prior_ids) > 1:
                # A single NINA slot switching off cannot retire several
                # independent window hazards whose slot mapping was not stored.
                others = [
                    hass.states.get(eid) for eid in entity_ids
                    if eid.startswith("binary_sensor.") and eid != previous_entity
                ]
                if any(_state_unknown(item) or item.state == "on" for item in others):
                    return "unknown", source_key
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
                return ("clear" if len(previous_ids) == 1 else "unknown"), source_key
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
            return ("clear" if len(previous_ids) == 1 else "unknown"), source_key
        return "unknown", source_key

    return "clear", source_key


def _weather_provider_availability(
    hass: HomeAssistant,
    entry: ConfigEntry,
    weather: Any,
    previous: dict[str, Any] | None,
) -> tuple[SafetyAvailability, str]:
    """Return live-weather safety availability from the actual hazard source.

    The selected ``weather.*`` entity is only one possible source. A local wind
    or gust sensor can independently create a hard window danger, including
    while ``weather.*`` itself is unavailable. Once such a danger is persisted,
    CLEAR is therefore allowed only when every entity that produced the hard
    danger is currently available and the fresh assessment no longer reports it.
    If any of those exact entities is unavailable, the state is UNKNOWN and the
    bounded fallback remains in force.
    """
    auto_key = str(getattr(weather, "safety_source_key", None) or "")
    previous_key = str(previous.get("source_key") or "") if isinstance(previous, dict) else ""
    # Local hazard sensors remain individually authoritative when automatic
    # weather is enabled.  A successful forecast fetch says nothing about a
    # previously dangerous *local* gust/wind/rain sensor which is now offline.
    prior_local_sources: list[str] = []
    if isinstance(previous, dict):
        raw = previous.get("source_entities")
        if isinstance(raw, list):
            prior_local_sources = [
                str(source) for source in raw
                if str(source).startswith(("sensor.", "binary_sensor.", "weather."))
            ]
        if not prior_local_sources:
            legacy = str(previous.get("source_entity") or "")
            if legacy.startswith(("sensor.", "binary_sensor.", "weather.")):
                prior_local_sources = [legacy]
    if auto_key.startswith("auto_weather:"):
        available = getattr(weather, "provider_available", None)
        if bool(getattr(weather, "weather_hard_lock", False)):
            danger_sources = {
                str(item)
                for item in getattr(weather, "weather_danger_sources", set())
                if item
            }
            # A configured local wind/gust/rain station remains authoritative
            # even if the automatic forecast provider is temporarily offline.
            # Pseudo auto-provider keys have no HA state and therefore do not
            # satisfy this branch.
            if any(hass.states.get(source) is not None for source in danger_sources):
                return "active", auto_key
            return ("active" if available is True else "unknown"), auto_key
        if any(_state_unknown(hass.states.get(source)) for source in prior_local_sources):
            return "unknown", previous_key or auto_key
        if previous_key.startswith("auto_weather:") and previous_key != auto_key:
            # Rounded GPS keys move after ~11 metres. Only a fresh, successful
            # assessment at the new coordinate is evidence of safe weather;
            # a failed fetch must retain the bounded lock from the old place.
            return ("clear" if available is True else "unknown"), (
                auto_key if available is True else previous_key
            )
        return ("clear" if available is True else "unknown"), auto_key
    if previous_key.startswith("auto_weather:"):
        return "unknown", previous_key

    entity_id = entry.data.get(CONF_WEATHER)
    # Keep a stable channel identity even for configurations that use only local
    # weather sensors. The concrete hazard entities are stored separately below.
    source_key = str(entity_id or f"entry:{entry.entry_id}:live_weather")

    if bool(getattr(weather, "weather_hard_lock", False)):
        # The freshly normalized assessment is direct evidence of an active hard
        # danger. Do not downgrade it merely because an unrelated weather entity
        # is unavailable; its exact source entities are persisted with the record.
        return "active", source_key

    previous_sources: list[str] = []
    if isinstance(previous, dict):
        raw_sources = previous.get("source_entities")
        if isinstance(raw_sources, list):
            previous_sources = [str(item) for item in raw_sources if item]
        if not previous_sources:
            legacy_source = str(previous.get("source_entity") or "").strip()
            if legacy_source:
                previous_sources = [legacy_source]

    if previous_sources:
        # A known hard danger is cleared only when the exact source(s) that made
        # it dangerous are available again and the current assessment is safe.
        # One unknown source among several is enough to keep bounded fallback.
        if any(_state_unknown(hass.states.get(source)) for source in previous_sources):
            return "unknown", source_key
        return "clear", source_key

    if not entity_id:
        return "clear", source_key
    state = hass.states.get(str(entity_id))
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
    elif bool(getattr(warnings, "weather_hard_lock", False)):
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
    evidence_at = _parse_datetime(getattr(warnings, "hard_safety_evidence_at", None))
    confirmed_at = evidence_at or now
    expires_at = _parse_datetime(getattr(warnings, "hard_safety_expires_at", None))
    valid_until = min(confirmed_at + SAFETY_FALLBACK_MAX_AGE, expires_at) if expires_at else confirmed_at + SAFETY_FALLBACK_MAX_AGE
    return {
        "source_key": source_key,
        "source_entity": source_entity,
        "provider_domain": getattr(warnings, "provider_domain", None),
        "kind": kind,
        "warning_ids": sorted(str(item) for item in getattr(warnings, "warning_ids", set()) if item),
        "warning_origins": {
            str(ident): str(origin)
            for ident, origin in getattr(warnings, "warning_origins", {}).items()
            if ident and origin and ident in getattr(warnings, "warning_ids", set())
        },
        "warning_cap_identities": {
            str(ident): sorted(set(signatures))
            for ident, signatures in getattr(warnings, "warning_cap_identities", {}).items()
            if ident and signatures
        },
        "warning_components": _warning_components(warnings),
        "warning_observations": [
            dict(item) for item in getattr(warnings, "warning_observations", [])
            if isinstance(item, dict)
        ],
        "reason_key": str(reason_key),
        "reason_args": reason_args,
        "official_close_instruction": bool(
            getattr(warnings, "official_close_instruction", False)
        ),
        # Evidence refers to the last verified *active* observation, not the
        # original CAP sent timestamp. Failed refreshes must not renew this TTL.
        "last_confirmed_at": confirmed_at.isoformat(),
        "valid_until": valid_until.isoformat(),
    }


def _record_from_weather(weather: Any, source_key: str, now: datetime) -> dict[str, Any]:
    danger_sources = sorted(
        str(item)
        for item in getattr(weather, "weather_danger_sources", set())
        if item
    )
    # Backwards-compatible fallback for older/third-party WeatherAssessment-like
    # objects that do not yet provide the explicit source set.
    if not danger_sources and source_key.startswith(("weather.", "sensor.", "binary_sensor.")):
        danger_sources = [source_key]
    return {
        "source_key": source_key,
        "source_entities": danger_sources,
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


def _apply_warning_record(warnings: Any, record: dict[str, Any], *, restore_identity=True) -> None:
    if restore_identity:
        warnings.provider_domain = record.get("provider_domain") or warnings.provider_domain
        warnings.warning_ids = {
            str(item) for item in record.get("warning_ids", []) if item
        }
        warnings.warning_origins = dict(record.get("warning_origins") or {})
        warnings.warning_components = _warning_components(record)
        warnings.warning_cap_identities = {
            str(ident): set(signatures)
            for ident, signatures in (record.get("warning_cap_identities") or {}).items()
            if isinstance(signatures, list)
        }
    warnings.warning_notice_kind = None
    warnings.warning_notice_text = None
    parts = record.get("warning_records")
    if not isinstance(parts, list):
        parts = [record]
    for part in sorted(parts, key=lambda item: str(item.get("last_confirmed_at") or ""), reverse=True):
        kind = part.get("kind")
        if kind == "nina_danger":
            if getattr(warnings, "nina_status", "none") != "danger":
                warnings.source_nina_entity = part.get("source_entity") or warnings.source_nina_entity
                warnings.nina_reason_key = str(part.get("reason_key") or "nina_air_danger")
                warnings.nina_reason_args = dict(part.get("reason_args") or {})
                warnings.nina_original_reason = None
            warnings.nina_status = "danger"
            warnings.official_close_instruction = True
        elif kind == "warning_weather_danger":
            if not getattr(warnings, "weather_hard_lock", False):
                warnings.source_weather_entity = part.get("source_entity") or warnings.source_weather_entity
                warnings.weather_reason_key = str(part.get("reason_key") or "weather_danger")
                warnings.weather_reason_args = dict(part.get("reason_args") or {})
                warnings.weather_original_reason = None
            warnings.weather_danger = True
            warnings.weather_hard_lock = True
            warnings.weather_caution = False
            warnings.official_close_instruction |= bool(part.get("official_close_instruction", False))
        notice = part.get("notice")
        if not isinstance(notice, dict) or not notice:
            continue
        notices = getattr(warnings, "warning_notices", [])
        if any(item.get("id") == notice.get("id") and item.get("provider") == notice.get("provider")
               and item.get("sender") == notice.get("sender") for item in notices):
            continue
        cached = dict(notice)
        now = dt_util.utcnow()
        onset = _parse_datetime(cached.get("gust_onset") or cached.get("onset"))
        cached["using_cached_data"] = True
        if onset is not None and onset <= now and cached.get("phase") == "prelock":
            cached["phase"] = "active"
            if warnings.weather_reason_key == "official_wind_prelock":
                warnings.weather_reason_key = "official_wind_lock"
        notices.append(cached)
        warnings.warning_notices = notices
        boundaries = [_parse_datetime(cached.get(key)) for key in ("onset", "ends", "gust_onset", "gust_ends", "lock_ends")]
        boundaries.append(_parse_datetime(part.get("valid_until")))
        due = getattr(warnings, "next_transition_at", None)
        future = [stamp for stamp in boundaries if stamp is not None and stamp > now]
        if future:
            warnings.next_transition_at = min([due, *future]) if due is not None else min(future)


def _apply_weather_record(weather: Any, record: dict[str, Any]) -> None:
    weather.weather_danger = True
    weather.weather_hard_lock = True
    weather.weather_caution = False
    weather.weather_reason_key = str(record.get("reason_key") or "weather_danger")
    weather.weather_reason_args = dict(record.get("reason_args") or {})
    weather.weather_original_reason = None
    if hasattr(weather, "weather_danger_sources"):
        weather.weather_danger_sources = {
            str(item) for item in record.get("source_entities", []) if item
        }


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
    # Keep the raw CAP cancellation for per-message reconciliation. The UI
    # notice may be suppressed below when it does not cancel the *whole* old
    # aggregate, but its original semantics still matter for every component.
    original_warning_notice = getattr(warnings, "warning_notice_kind", None)
    warning_availability, warning_source = _warning_provider_availability(
        hass, entry, warnings, previous_warning if isinstance(previous_warning, dict) else None
    )
    if getattr(warnings, "warning_notice_kind", None) == "all_clear":
        if (not _matching_warning_ids(
            previous_warning, getattr(warnings, "warning_ids", set()),
            getattr(warnings, "warning_cap_identities", {}),
        ) or
                not isinstance(previous_warning, dict) or
                previous_warning.get("source_key") != warning_source):
            # An unrelated all-clear is never permission to release a hard
            # window lock. The opt-in general feed may still show it as plain
            # information, without the visually misleading "all-clear" label.
            warnings.warning_notice_kind = (
                "info" if entry.data.get(CONF_SHOW_GENERAL_WARNINGS, False) else None
            )
            if warnings.warning_notice_kind is None:
                warnings.warning_notice_text = None
            if getattr(warnings, "nina_status", "none") == "clear":
                warnings.nina_status = "none"
    # A manual slot can report CLEAR while an *additional* automatic hazard
    # from the same persisted multi-source lock is unverified (or vice versa).
    # Clearance must cover all old components, not just the strongest one.
    if warning_availability == "clear" and isinstance(previous_warning, dict):
        origins = previous_warning.get("warning_origins") or {}
        origin_types = {
            part["origin"].split(":", 1)[0]
            for part in _warning_components(previous_warning)
            if part["origin"]
        }
        legacy_mixed = (
            not origins
            and "+" in str(previous_warning.get("provider_domain") or "")
            and entry.data.get(CONF_WARNING_SOURCE)
        )
        if (({"auto", "manual"}.issubset(origin_types) or legacy_mixed)
                and _record_is_valid(
                    previous_warning, str(previous_warning.get("source_key") or ""), now
                )
                and _missing_previous_warning_unresolved(
                    hass, entry, warnings, previous_warning, {"warning_ids": []}
                )):
            warning_availability = "unknown"
            warning_source = str(previous_warning.get("source_key") or "")

    # Each CAP hazard has its own observation and expiry. The previous
    # implementation persisted one selected warning with one shared TTL: it
    # either discarded a fresh second danger during an outage or extended an
    # older, unverified danger whenever another feed refreshed.
    def _identity(record: dict[str, Any]) -> tuple[str, str, str, str]:
        # A CAP identifier may appear in several independently updating HA
        # warning slots.  Persist the specific slot as part of the key, while
        # accepting older/automatic entries without an explicit slot.
        slot = str(record.get("entity") or "")
        if not slot and str(record.get("origin") or "").startswith("manual:"):
            slot = str(record.get("source_entity") or "")
        return (str(record.get("id") or ""), str(record.get("origin") or ""),
                str(record.get("cap") or ""), slot)

    def _valid_component(record: dict[str, Any]) -> bool:
        return _record_is_valid(record, str(record.get("source_key") or ""), now)

    def _source_for_part(part: dict[str, str], main_key: str) -> str:
        origin = part.get("origin", "")
        if origin.startswith("manual:"):
            return origin.removeprefix("manual:")
        if origin.startswith("auto:"):
            location = origin.removeprefix("auto:")
            prefix = _canonical_warning_id(part.get("id", "")).split(".", 1)[0]
            feed = _AUTO_WARNING_ID_SOURCES.get(prefix)
            return f"{location}:{feed}" if feed else location
        return main_key

    def _records_from_legacy(record: Any) -> list[dict[str, Any]]:
        if not isinstance(record, dict):
            return []
        stored = record.get("warning_records")
        if isinstance(stored, list):
            loaded_parts = [dict(part) for part in stored if isinstance(part, dict)]
            # COMPLETE(10) (and some legacy aggregates below) attached the
            # *strongest* manual slot to every independent warning. When two
            # stored manual alerts share that slot but have no per-alert entity,
            # it cannot certify clearance of either. Remove the unverified
            # slot mapping; keep each old TTL until all slots can be checked.
            grouped: dict[tuple[str, str], int] = {}
            for part in loaded_parts:
                origin = str(part.get("origin") or "")
                slot = str(part.get("source_entity") or "")
                if origin.startswith("manual:") and slot and not part.get("entity"):
                    key = (origin, slot)
                    grouped[key] = grouped.get(key, 0) + 1
            for part in loaded_parts:
                key = (str(part.get("origin") or ""),
                       str(part.get("source_entity") or ""))
                if not part.get("entity") and grouped.get(key, 0) > 1:
                    part["source_entity"] = None
            return loaded_parts
        # Old schema: identity and origin may be absent. Preserve original
        # confirmation/expiry without inventing missing CAP identities.
        parts = _warning_components(record) or [
            {"id": "", "origin": f"unidentified:{record.get('source_key') or ''}", "cap": ""}
        ]
        # A pre-independent legacy aggregate cannot establish which manual
        # slot produced which of several stored warnings. Treat those source
        # entities as uncertain rather than applying its strongest slot to all.
        manual_counts: dict[str, int] = {}
        for part in parts:
            origin = str(part.get("origin") or "")
            if origin.startswith("manual:") and not part.get("entity"):
                manual_counts[origin] = manual_counts.get(origin, 0) + 1
        return [
            {**{key: record.get(key) for key in (
                "source_entity", "provider_domain", "kind", "reason_key",
                "reason_args", "official_close_instruction", "last_confirmed_at",
                "valid_until")}, **part,
             "source_key": _source_for_part(part, str(record.get("source_key") or "")),
             "source_entity": (part.get("entity") or (
                 record.get("source_entity")
                 if manual_counts.get(str(part.get("origin") or ""), 0) <= 1
                 else None
             ))}
            for part in parts
        ]

    previous_records = {
        _identity(part): part for part in _records_from_legacy(previous_warning)
        if _valid_component(part)
    }
    latest = _record_from_warning(warnings, warning_source, now) if warning_availability == "active" else None
    current_parts = _warning_components(latest) if latest else []
    if latest is not None and not current_parts:
        # Legacy hard-weather warnings may have no CAP identifier.
        current_parts = [
            {"id": "", "origin": f"unidentified:{warning_source}", "cap": ""}
        ]

    updated: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if latest is not None:
        for part in current_parts:
            key = _identity(part)
            source_key = _source_for_part(part, warning_source)
            candidate = {
                **{field: latest.get(field) for field in (
                    "source_entity", "provider_domain", "kind", "reason_key",
                    "reason_args", "official_close_instruction")},
                **part, "source_key": source_key,
                "source_entity": part.get("entity") or latest.get("source_entity"),
                "last_confirmed_at": latest["last_confirmed_at"],
                "valid_until": latest["valid_until"],
            }
            old = previous_records.get(key)
            observation = next((
                item for item in latest.get("warning_observations", [])
                if isinstance(item, dict) and _identity(item) == key
            ), None)
            if observation is not None:
                if isinstance(observation.get("notice"), dict):
                    candidate["notice"] = dict(observation["notice"])
                if observation.get("kind") in {"nina_danger", "warning_weather_danger"}:
                    for field in ("kind", "reason_key", "reason_args", "official_close_instruction"):
                        if field in observation:
                            candidate[field] = observation[field]
                proof_at = _parse_datetime(observation.get("confirmed_at"))
                if proof_at is not None:
                    candidate["last_confirmed_at"] = proof_at.isoformat()
                    expires_at = _parse_datetime(observation.get("expires"))
                    valid_until = proof_at + SAFETY_FALLBACK_MAX_AGE
                    if expires_at is not None:
                        valid_until = min(valid_until, expires_at)
                    candidate["valid_until"] = valid_until.isoformat()
            # An assessment merged from two live sources can carry a single
            # selected-source evidence timestamp. Don't use that timestamp to
            # renew an unrelated feed when it did not provide fresh evidence.
            is_other_source = (
                (source_key.startswith("auto_warning:") and
                 not warning_source.startswith("auto_warning:"))
                or (source_key.startswith("auto_warning:") and
                    warning_source.startswith("auto_warning:") and
                    source_key.split(":")[:3] != warning_source.split(":")[:3])
                or (not source_key.startswith("auto_warning:") and
                    source_key != warning_source)
            )
            if is_other_source and observation is None:
                avail = getattr(warnings, "provider_availability", {})
                if source_key.startswith("auto_warning:"):
                    fresh = isinstance(avail, dict) and avail.get(source_key) is True
                else:
                    fresh = False  # manual evidence belongs to its own selected assessment
                if not fresh and old is not None:
                    candidate["last_confirmed_at"] = old["last_confirmed_at"]
                    candidate["valid_until"] = old["valid_until"]
            if old is not None:
                latest_seen = _parse_datetime(candidate["last_confirmed_at"])
                old_seen = _parse_datetime(old.get("last_confirmed_at"))
                if (old_seen and latest_seen and
                        (latest_seen < old_seen or
                         (latest_seen > old_seen and
                          timedelta(0) <= now - old_seen < _CONFIRM_WRITE_INTERVAL))):
                    # Limit Store writes without accepting a stale proof or
                    # extending a missing feed's independently bounded TTL.
                    candidate["last_confirmed_at"] = old["last_confirmed_at"]
                    candidate["valid_until"] = old["valid_until"]
            if _valid_component(candidate):
                updated[key] = candidate

    # Assess absent *old* alerts one at a time, never through a shared
    # strongest-warning identity. New confirmed warnings have already been
    # added and cannot be vetoed by a previous unverified one.
    missing_statuses: dict[tuple[str, str, str, str], str] = {}
    for key, old in previous_records.items():
        if key in updated:
            continue
        singular = {
            **old,
            "warning_ids": [old["id"]] if old.get("id") else [],
            "warning_components": [
                {field: old.get(field, "") for field in ("id", "origin", "cap")}
            ] if old.get("id") else [],
            "warning_cap_identities": {
                old["id"]: [old["cap"]]
            } if old.get("id") and old.get("cap") else {},
        }
        # Evaluate disappearance with the live assessment's availability and
        # cancellation evidence, but suppress its unrelated active instruction.
        # Each missing component must itself be provably cleared.
        inactive = type("OldWarningClearance", (), {})()
        for attr in ("safety_source_key", "provider_availability",
                     "warning_notice_kind", "warning_ambiguous_clear",
                     "warning_ids", "warning_cap_identities"):
            setattr(inactive, attr, getattr(warnings, attr, None))
        inactive.warning_notice_kind = original_warning_notice
        inactive.official_close_instruction = False
        inactive.weather_hard_lock = False
        inactive.nina_status = "none"
        status, _ = _warning_provider_availability(hass, entry, inactive, singular)
        # An unrelated CAP all-clear cannot cancel another still unresolved
        # hazard, even if the previous provider happened to respond.
        if original_warning_notice == "all_clear" and not _matching_warning_ids(
            singular, getattr(warnings, "warning_ids", set()),
            getattr(warnings, "warning_cap_identities", {}),
        ):
            status = "unknown"
        missing_statuses[key] = status

    # Reconcile each historic hazard independently. A verified clearance of A
    # must remove A even when B is unresolved; only B keeps its own bounded
    # fallback. A partial inventory is never authority to clear B.
    for key, status in missing_statuses.items():
        if status != "clear":
            updated[key] = previous_records[key]

    if updated:
        parts = list(updated.values())
        # Prefer live advice when available, and otherwise the most recently
        # confirmed still-protected hazard. A legacy aggregate remains for
        # backwards-compatible cards, storage readers and older migrations.
        primary = latest if latest is not None else (
            max(parts, key=lambda item: item.get("last_confirmed_at") or "")
        )
        aggregate = dict(primary)
        # Observations are transient per-refresh evidence, not part of the
        # persistent schema. The per-message verified times are stored below.
        aggregate.pop("warning_observations", None)
        aggregate["warning_records"] = sorted(parts, key=lambda item: _identity(item))
        aggregate["warning_components"] = [
            {**{field: part.get(field, "") for field in ("id", "origin", "cap")},
             **({"entity": part["entity"]} if part.get("entity") else {})}
            for part in parts if part.get("id")
        ]
        aggregate["warning_ids"] = sorted({part["id"] for part in parts if part.get("id")})
        aggregate["warning_origins"] = {
            part["id"]: part.get("origin", "") for part in parts if part.get("id")
        }
        cap_map: dict[str, set[str]] = {}
        for part in parts:
            if part.get("id") and part.get("cap"):
                cap_map.setdefault(part["id"], set()).add(part["cap"])
        aggregate["warning_cap_identities"] = {
            ident: sorted(values) for ident, values in cap_map.items()
        }
        # Keep the earliest still-unresolved confirmation visible in the
        # legacy summary; actual TTLs are independent in warning_records.
        oldest = min(parts, key=lambda item: item.get("last_confirmed_at") or "")
        newest = max(parts, key=lambda item: item.get("valid_until") or "")
        aggregate["last_confirmed_at"] = oldest["last_confirmed_at"]
        aggregate["valid_until"] = newest["valid_until"]
        if (not _same_safety_payload(previous_warning, aggregate)
                or (not isinstance(previous_warning, dict)
                    or previous_warning.get("warning_records") != aggregate["warning_records"])):
            channels[_WARNING_CHANNEL] = aggregate
            changed = True
        if latest is None or missing_statuses:
            _apply_warning_record(warnings, aggregate, restore_identity=latest is None)
    elif _WARNING_CHANNEL in channels:
        channels.pop(_WARNING_CHANNEL, None)
        changed = True

    previous_weather = channels.get(_WEATHER_CHANNEL)
    # Weather dangers are independent just like CAP warnings. A new confirmed
    # gust at station B must never replace an unresolved earlier gust at A.
    # Keep the legacy summary for compatible consumers, but make weather_records
    # the authority for individual evidence timestamps and expiration times.
    prior_weather_parts: dict[str, dict[str, Any]] = {}
    if isinstance(previous_weather, dict):
        raw_parts = previous_weather.get("weather_records")
        if isinstance(raw_parts, list):
            candidates = [part for part in raw_parts if isinstance(part, dict)]
        else:
            # Migrate v0.11.3 / v0.11.4 weather guards without resetting the
            # original one-hour deadlines. Older records with multiple source
            # entities share the *original* deadline; no extra protection time
            # is invented for them during migration.
            original_sources = previous_weather.get("source_entities")
            if not isinstance(original_sources, list) or not original_sources:
                original_sources = [
                    previous_weather.get("source_entity")
                    or previous_weather.get("source_key")
                ]
            candidates = [
                {
                    **previous_weather,
                    "hazard_source": str(source),
                    "source_entities": [str(source)],
                }
                for source in original_sources if source
            ]
        for candidate in candidates:
            source = str(candidate.get("hazard_source") or "")
            if not source:
                source = str(next(iter(candidate.get("source_entities") or []), ""))
            if not source:
                continue
            part = dict(candidate)
            part["hazard_source"] = source
            part["source_entities"] = [source]
            part.setdefault("source_key", str(previous_weather.get("source_key") or ""))
            if _record_is_valid(part, str(part.get("source_key") or ""), now):
                # A corrupt/duplicate legacy source must not extend a TTL.
                old_part = prior_weather_parts.get(source)
                if old_part is None or str(part.get("valid_until") or "") < str(old_part.get("valid_until") or ""):
                    prior_weather_parts[source] = part

    weather_availability, weather_source = _weather_provider_availability(
        hass,
        entry,
        weather,
        previous_weather if isinstance(previous_weather, dict) else None,
    )
    current_weather_parts: dict[str, dict[str, Any]] = {}
    if weather_availability == "active":
        live = _record_from_weather(weather, weather_source, now)
        sources = live.get("source_entities") or [weather_source]
        for source_value in sources:
            source = str(source_value or "")
            if not source:
                continue
            if source.startswith(("sensor.", "binary_sensor.", "weather.")):
                # A syntactically available but invalid/stale physical reading
                # must not renew the weather hard-lock evidence either.
                provisional = {"hazard_measurement": (
                    "wind" if str(getattr(weather, "source_wind", "") or "") == source
                    else "gust" if str(getattr(weather, "source_gust", "") or "") == source
                    else "condition"
                ), "reason_key": getattr(weather, "weather_reason_key", None)}
                if not _weather_source_reliably_readable(hass, source, provisional, now):
                    continue
            elif source.startswith("auto_weather:"):
                # Automatic provider cache content is not fresh evidence when
                # the live fetch failed, even if another local sensor is active.
                if getattr(weather, "provider_available", None) is not True:
                    continue
            candidate = {
                **live,
                "hazard_source": source,
                "source_entities": [source],
            }
            # Preserve a true non-wind hard condition such as hail. If a
            # source also supplies wind/gust, label it as wind ONLY when the
            # exact value crosses its respective hard-lock threshold. When
            # wind and gust share one weather entity, select a truly hard
            # reading rather than blindly preferring the gust field.
            # An unrelated local hard gust must not inherit the *global*
            # hail/thunderstorm reason of a different weather entity.
            is_local_wind_source = source.startswith("sensor.") and source in {
                str(getattr(weather, "source_wind", "") or ""),
                str(getattr(weather, "source_gust", "") or ""),
            }
            non_wind_hard = (
                not is_local_wind_source
                and str(getattr(weather, "weather_reason_key", "") or "") in {
                    "weather_hail_danger", "weather_thunderstorm_danger",
                    "weather_exceptional_danger",
                }
            )
            candidate["hazard_measurement"] = "condition"
            if not non_wind_hard:
                for field, measurement, threshold, maximum, kind in (
                    ("source_gust", "wind_gust_kmh", GUST_HARD_LOCK_KMH, 400, "gust"),
                    ("source_wind", "wind_speed_kmh", WIND_HARD_LOCK_KMH, 300, "wind"),
                ):
                    if str(getattr(weather, field, None) or "") != source:
                        continue
                    speed = getattr(weather, measurement, None)
                    if (isinstance(speed, (int, float))
                            and threshold <= speed <= maximum):
                        candidate["reason_key"] = "weather_wind_danger"
                        candidate["reason_args"] = {"speed_kmh": speed}
                        candidate["hazard_measurement"] = kind
                        break
            old = prior_weather_parts.get(source)
            if old is not None and not _should_refresh_confirmation(old, now):
                candidate["last_confirmed_at"] = old["last_confirmed_at"]
                candidate["valid_until"] = old["valid_until"]
            if _record_is_valid(candidate, str(candidate.get("source_key") or ""), now):
                current_weather_parts[source] = candidate

    # Reconcile each absent old source independently. An available and now-safe
    # local sensor can be cleared despite an unrelated automatic weather outage;
    # conversely a working forecast cannot clear an unavailable *local* sensor.
    for source, old in prior_weather_parts.items():
        if source in current_weather_parts:
            continue
        if source.startswith(("sensor.", "binary_sensor.", "weather.")):
            # Identical validity rules to the original local weather reading:
            # stale, non-finite, implausible and unitless values are UNKNOWN.
            status = ("clear" if _weather_source_confirmed_safe(hass, source, old, now)
                      else "unknown")
        elif source.startswith("auto_weather:"):
            status = (
                "clear" if (
                    str(getattr(weather, "safety_source_key", "") or "").startswith("auto_weather:")
                    and getattr(weather, "provider_available", None) is True
                ) else "unknown"
            )
        else:
            # Unknown legacy provenance: use the existing provider evaluator,
            # never an unrelated sensor's current value as clearance evidence.
            status = weather_availability if weather_availability != "active" else "unknown"
        if status != "clear" and _record_is_valid(old, str(old.get("source_key") or ""), now):
            current_weather_parts[source] = old

    if current_weather_parts:
        parts = sorted(current_weather_parts.values(), key=lambda item: item["hazard_source"])
        # The most recent live danger controls the wording; an older fallback
        # supplies the wording only if the current assessment is otherwise safe.
        selected = (
            next((part for part in parts if part["hazard_source"] in (
                set(getattr(weather, "weather_danger_sources", set()) or set())
            )), None)
            if weather_availability == "active" else None
        ) or max(parts, key=lambda item: str(item.get("last_confirmed_at") or ""))
        aggregate = dict(selected)
        aggregate["weather_records"] = parts
        aggregate["source_entities"] = sorted(current_weather_parts)
        # Compatibility summary: individual deadlines live in weather_records.
        oldest = min(parts, key=lambda item: str(item.get("last_confirmed_at") or ""))
        latest_expiry = max(parts, key=lambda item: str(item.get("valid_until") or ""))
        aggregate["last_confirmed_at"] = oldest["last_confirmed_at"]
        aggregate["valid_until"] = latest_expiry["valid_until"]
        aggregate.pop("hazard_source", None)
        if (not isinstance(previous_weather, dict)
                or previous_weather != aggregate):
            channels[_WEATHER_CHANNEL] = aggregate
            changed = True
        if weather_availability != "active":
            _apply_weather_record(weather, selected | {"source_entities": sorted(current_weather_parts)})
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

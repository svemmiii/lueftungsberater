"""Opt-in, Recorder-friendly room measurements for the history dashboard card.

A Lovelace card is not a permanent background task. Activation is persisted on
Home Assistant's side, and coordinator-backed sensor entities survive restarts.
"""
from __future__ import annotations

import math
import logging
import time
from typing import Any

from homeassistant.helpers.storage import Store

from .air_sensors import HCHO_LIMITS, PM_LIMITS, VOC_MASS_LIMITS
from .const import DOMAIN, SUBENTRY_TYPE_ROOM
from .engine import CO2_GOOD_UPPER_PPM, RH_GOOD_LOWER, RH_GOOD_UPPER, temperature_need_limits
from .providers import AIR_QUALITY_LIMITS

_LOGGER = logging.getLogger(__name__)

# UI-facing keys are deliberately an allowlist, never arbitrary state paths.
# (label, unit, room-advisor attribute, source-advisor attribute)
HISTORY_METRICS: dict[str, tuple[str, str, str, str | None]] = {
    "co2_in": ("CO₂ innen", "ppm", "co2_ppm", "source_co2"),
    "co2_out": ("CO₂ außen", "ppm", "outdoor_co2_ppm", "source_outdoor_co2"),
    "temp_in": ("Temperatur innen", "°C", "temperature_inside", "source_temperature_inside"),
    "temp_out": ("Temperatur außen", "°C", "temperature_outside", "source_temperature_outside"),
    "humidity_in": ("Feuchte innen", "%", "humidity_inside", "source_humidity_inside"),
    "humidity_out": ("Feuchte außen", "%", "humidity_outside", "source_humidity_outside"),
    "target_temp": ("Solltemperatur", "°C", "target_temperature", "source_target_temperature"),
    "surface_temp": ("Oberflächentemperatur", "°C", "surface_temperature", "source_surface_temperature"),
    "surface_humidity": ("Oberflächenfeuchte", "%", "surface_relative_humidity", None),
    "absolute_delta": ("Feuchtedifferenz", "g/m³", "absolute_humidity_difference", "source_absolute_humidity_difference"),
    "absolute_in": ("Absolute Feuchte innen", "g/m³", "absolute_humidity_inside", "source_absolute_humidity_inside"),
    "absolute_out": ("Absolute Feuchte außen", "g/m³", "absolute_humidity_outside", "source_absolute_humidity_outside"),
    "pm25_in": ("PM2,5 innen", "µg/m³", "indoor_air_quality_values.pm2_5", "source_pm25_inside"),
    "pm25_out": ("PM2,5 außen", "µg/m³", "air_quality_values.pm2_5", "source_pm25_outside"),
    "pm10_in": ("PM10 innen", "µg/m³", "indoor_air_quality_values.pm10", "source_pm10_inside"),
    "pm10_out": ("PM10 außen", "µg/m³", "air_quality_values.pm10", "source_pm10_outside"),
    "no2_in": ("NO₂ innen", "µg/m³", "indoor_air_quality_values.no2", "source_no2_inside"),
    "no2_out": ("NO₂ außen", "µg/m³", "air_quality_values.no2", "source_no2_outside"),
    "o3_out": ("Ozon außen", "µg/m³", "air_quality_values.o3", "source_o3_outside"),
    "voc_in": ("TVOC innen", "µg/m³", "indoor_air_quality_values.voc", "source_voc_inside"),
    "voc_out": ("TVOC außen", "µg/m³", "air_quality_values.voc", "source_voc_outside"),
    "hcho_in": ("Formaldehyd innen", "mg/m³", "indoor_air_quality_values.formaldehyde", "source_formaldehyde_inside"),
    "wind_out": ("Wind außen", "km/h", "wind_speed_kmh", "source_wind_outside"),
    "gust_out": ("Böen außen", "km/h", "wind_gust_kmh", "source_gust_outside"),
}


def finite_value(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def preferred_air_quality_variant(weather: Any, aliases: tuple[str, ...]) -> str | None:
    """Select the actually available local measurement before provider variants.

    A local ppb gas measurement is stored in air_quality_values, not necessarily
    local_station_values. The provider records local provenance per variant so
    that a regional mass reading cannot hide a simultaneously active local gas.
    """
    if weather is None:
        return None
    regional = getattr(weather, "air_quality_values", None) or {}
    local = getattr(weather, "local_station_values", None) or {}
    local_keys = getattr(weather, "local_air_quality_keys", None) or ()
    def available(key: str) -> bool:
        return finite_value(local.get(key)) is not None or finite_value(regional.get(key)) is not None
    for key in aliases:
        if key in local_keys and available(key):
            return key
    for key in aliases:
        if finite_value(local.get(key)) is not None:
            return key
    return next((key for key in aliases if available(key)), None)


def _air_quality_sample(snapshot: Any, metric: str) -> tuple[float | None, str]:
    """Return one matching value/unit pair, independent of dominant pollutant."""
    indoor = metric.endswith("_in")
    kind = metric.split("_", 1)[0]
    aliases = {
        "voc": ("voc", "voc_parts", "voc_index"),
        "no2": ("no2", "no2_parts", "no2_index"),
        "o3": ("o3", "o3_parts"),
    }.get(kind, ())
    if not aliases or snapshot is None:
        return None, ""
    if indoor:
        values = snapshot.values.get("indoor_air_quality_values") or {}
        units = snapshot.values.get("indoor_air_quality_units") or {}
        key = next((key for key in aliases if finite_value(values.get(key)) is not None), None)
    else:
        weather = snapshot.weather
        regional = getattr(weather, "air_quality_values", None) or {}
        local = getattr(weather, "local_station_values", None) or {}
        values = {**regional, **local}
        units = getattr(weather, "air_quality_variant_units", None) or {}
        key = preferred_air_quality_variant(weather, aliases)
    if key is None:
        return None, ""
    value = finite_value(values.get(key))
    if value is None:
        return None, ""
    unit = units.get(key)
    if key.endswith("_index"):
        return value, "Index"  # Explicit ordinal scale, never mass.
    if key.endswith("_parts"):
        # pollutant_reading normalizes physical gas parts to ppb. The unit is
        # per key, not the one currently dominating the air-quality warning.
        if not unit:
            unit = "ppb" if key in {"no2_parts", "o3_parts"} else ""
        return value, unit or ""
    return value, unit or "µg/m³"


def current_unit(snapshot: Any, metric: str) -> str:
    """Return the current physical/ordinal scale; unknown is never mass."""
    if metric not in HISTORY_METRICS:
        return ""
    if metric.startswith(("voc_", "no2_", "o3_")):
        return _air_quality_sample(snapshot, metric)[1] if snapshot is not None else ""
    return HISTORY_METRICS[metric][1]


def current_value(snapshot: Any, metric: str) -> float | None:
    """Read from the coordinator snapshot, not stale HA advisor attributes."""
    if snapshot is None or metric not in HISTORY_METRICS:
        return None
    if metric.startswith(("voc_", "no2_", "o3_")):
        return _air_quality_sample(snapshot, metric)[0]
    key = HISTORY_METRICS[metric][2]
    if key.startswith("air_quality_values."):
        name = key.split(".", 1)[1]
        raw = (getattr(snapshot.weather, "local_station_values", None) or {}).get(name)
        if raw is None:
            raw = (getattr(snapshot.weather, "air_quality_values", None) or {}).get(name)
    elif key.startswith("indoor_air_quality_values."):
        raw = (snapshot.values.get("indoor_air_quality_values") or {}).get(key.split(".", 1)[1])
    elif key == "wind_speed_kmh":
        raw = snapshot.weather.wind_speed_kmh
    elif key == "wind_gust_kmh":
        raw = snapshot.weather.wind_gust_kmh
    elif key == "surface_relative_humidity":
        raw = snapshot.values.get("surface_relative_humidity")
    elif key == "absolute_humidity_difference":
        raw = getattr(snapshot.result, "absolute_humidity_difference", None) if snapshot.result else None
    elif key.startswith("absolute_humidity_"):
        result = snapshot.result
        raw = getattr(result, "indoor_absolute_humidity" if metric == "absolute_in" else "outdoor_absolute_humidity", None) if result else None
    else:
        raw = snapshot.values.get(key)
    return finite_value(raw)


def good_limits(metric: str, *, target: float | None = None, has_windows: bool = True) -> dict[str, float | None]:
    """Reuse the evaluation modules' limits; frontend never owns a second table."""
    kind = metric.rsplit("_", 1)[0]
    if kind == "co2":
        return {"low": None, "high": CO2_GOOD_UPPER_PPM}
    if kind == "humidity":
        return {"low": RH_GOOD_LOWER, "high": RH_GOOD_UPPER}
    if kind == "temp" and target is not None:
        distance, _ = temperature_need_limits(has_window_contacts=has_windows)
        return {"low": target - distance, "high": target + distance}
    lookup = {"pm25": "pm2_5", "pm10": "pm10", "no2": "no2", "o3": "o3"}
    key = lookup.get(kind)
    if key:
        limits = PM_LIMITS.get(key) or AIR_QUALITY_LIMITS.get(key)
        return {"low": None, "high": limits[1] if limits else None}
    if kind == "voc":
        return {"low": None, "high": VOC_MASS_LIMITS[1]}
    if kind == "hcho":
        return {"low": None, "high": HCHO_LIMITS[1]}
    return {"low": None, "high": None}  # no invented 'good' threshold


def allowed_metric(advisor_attributes: dict, metric: str) -> bool:
    """Allow only measurements actually configured/provided for this room."""
    if metric not in HISTORY_METRICS:
        return False
    _, _, value_path, source_key = HISTORY_METRICS[metric]
    if metric in advisor_attributes.get("_history_enabled", ()):
        return True  # Recorded helper may survive an unavailable/live-removed source.
    if metric in advisor_attributes.get("_history_inactive_metrics", ()):
        return False  # A removed source cannot be resurrected by stale values.
    if metric in advisor_attributes.get("_history_auto_available", ()):
        # Auto-weather measurements have no fixed Recorder entity. They are
        # selectable so the existing per-room helper can record them once
        # opted in, without fabricating historical readings during an outage.
        return True
    if metric == "co2_in" and not advisor_attributes.get("has_co2"):
        return False
    if metric == "surface_humidity":
        # The surface RH is derived from three configured measurements, not
        # directly measured by the surface-temperature sensor. Keep it
        # selectable while a constituent sensor is temporarily unavailable.
        return (advisor_attributes.get("surface_relative_humidity") is not None
                or all(advisor_attributes.get(key) for key in (
                    "source_surface_temperature", "source_humidity_inside",
                    "source_temperature_inside",
                )))
    source = advisor_attributes.get(source_key) if source_key else None
    if source:
        return True
    if value_path.startswith("air_quality_values."):
        return value_path.split(".", 1)[1] in (advisor_attributes.get("air_quality_values") or {})
    if value_path.startswith("indoor_air_quality_values."):
        return value_path.split(".", 1)[1] in (advisor_attributes.get("indoor_air_quality_values") or {})
    return advisor_attributes.get(value_path) is not None


def configured_metrics(attrs: dict, states=None) -> list[dict[str, Any]]:
    target = finite_value(attrs.get("target_temperature"))
    result = []
    measured_units = attrs.get("_history_metric_units") or {}
    for key, (label, default_unit, _, source_key) in HISTORY_METRICS.items():
        if not allowed_metric(attrs, key):
            continue
        limit = good_limits(key, target=target, has_windows=attrs.get("has_window_contacts") is True)
        source = attrs.get(source_key) if source_key else None
        state = states.get(source) if states is not None and source else None
        source_unit = str((state.attributes or {}).get("unit_of_measurement") or "").strip() if state else ""
        # Live source -> current helper scale -> no assumption for an offline
        # mass/parts/index helper. A hidden physical conversion is forbidden.
        variable = key.startswith(("voc_", "no2_", "o3_"))
        unit = source_unit or measured_units.get(key) or ("" if variable and not source else default_unit)
        if variable and not source_unit and not measured_units.get(key):
            unit = ""  # No trustworthy source unit yet: no fabricated µg/m³.
        compact = unit.lower().replace("μ", "µ").replace("³", "3").replace(" ", "")
        if key.startswith(("pm25_", "pm10_", "no2_", "o3_", "voc_", "hcho_")):
            if compact in {"mg/m3"}:
                if not key.startswith("hcho_") and limit["high"] is not None:
                    limit["high"] /= 1000.0
            elif compact in {"µg/m3", "ug/m3"}:
                if key.startswith("hcho_") and limit["high"] is not None:
                    limit["high"] *= 1000.0
            elif compact in {"ppb", "ppm"} and key.startswith(("no2_", "o3_")):
                pollutant = "no2_parts" if key.startswith("no2_") else "o3_parts"
                limit["high"] = PM_LIMITS[pollutant][1] / (1000.0 if compact == "ppm" else 1.0)
            else:
                # Index, unknown, VOC-parts and other incomparable scales have
                # no proven mass-concentration threshold.
                limit["high"] = None
        elif key.startswith("temp_") and compact in {"°f", "f"}:
            for bound in ("low", "high"):
                if limit[bound] is not None:
                    limit[bound] = limit[bound] * 1.8 + 32.0
        result.append({"key": key, "label": label, "unit": unit,
                       "source": source,
                       "low": limit["low"], "high": limit["high"]})
    return result


def history_sensor_unique_id(room_id: str, metric: str) -> str:
    # COMPLETE(14)'s surface RH mirror copied the °C source into a %-labelled
    # sensor. Avoid reusing its potentially corrupted Recorder history after
    # fixing the data source; all other established helper IDs remain stable.
    suffix = "_v2" if metric == "surface_humidity" else ""
    return f"{room_id}_history_{metric}{suffix}"


def history_data(hass, entry_id: str) -> dict[str, list[str]]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("history_enabled", {}).setdefault(entry_id, {})


async def async_save_history_confirmed(hass, store: Store, settings: dict[str, list[str]]) -> None:
    """Commit opt-ins only after verifying the durable HA storage contents.

    Home Assistant's Store.async_save catches some WriteError failures internally.
    Store.async_load on the *same* object can also return pending, unsaved data,
    so neither a successful await nor reloading that object is a disk commit.
    A new Store with the same key has no pending data; HA's store manager cache
    was invalidated by the save and it must load the actual persisted data.
    """
    await store.async_save(settings)
    try:
        persisted = await Store(hass, 1, store.key).async_load()
    except Exception as exc:
        raise RuntimeError(
            f"Unable to verify persisted history opt-ins in {store.key}"
        ) from exc
    if persisted != settings:
        raise RuntimeError(
            f"History opt-ins in {store.key} were not durably saved"
        )


async def async_load_history(hass, entry) -> dict[str, list[str]]:
    # The v0.7.2 cleanup targets `DOMAIN.history.*`. Never place new
    # persistent opt-ins in that legacy namespace.
    store = Store(hass, 1, f"{DOMAIN}.history_enabled.{entry.entry_id}")
    domain_data = hass.data.setdefault(DOMAIN, {})
    load_errors = domain_data.setdefault("history_load_errors", {})
    try:
        existing = await store.async_load()
        if existing is None:
            # An unreadable legacy store is optional history state. Never let
            # its failure prevent the existing rooms from starting, nor
            # silently replace the damaged file on the next opt-in.
            legacy = Store(hass, 1, f"{DOMAIN}.history.{entry.entry_id}")
            existing = await legacy.async_load()
            if isinstance(existing, dict):
                await async_save_history_confirmed(hass, store, existing)
                try:
                    await legacy.async_remove()
                except OSError:
                    _LOGGER.warning("Could not remove old history opt-in store for %s", entry.entry_id)
    except Exception:
        _LOGGER.exception(
            "History preferences for %s could not be loaded; room advice will continue "
            "but history opt-ins are read-only until the storage issue is fixed",
            entry.entry_id,
        )
        load_errors[entry.entry_id] = True
        # No preference or entity registration is reconstructed from a guessed
        # disk state. Preserve the unreadable Store for manual recovery.
        current = history_data(hass, entry.entry_id)
        current.clear()
        domain_data.setdefault("history_added", {}).pop(entry.entry_id, None)
        domain_data.setdefault("history_pending", {}).pop(entry.entry_id, None)
        return current
    if existing is not None and not isinstance(existing, dict):
        # Valid JSON with an invalid root can still contain recoverable user
        # preferences. Treat it like a read error: room advice may start, but
        # no fresh opt-in is allowed to overwrite the original Store.
        _LOGGER.error(
            "History preferences for %s have an invalid root type %s; "
            "keeping the Store read-only until repaired",
            entry.entry_id, type(existing).__name__,
        )
        load_errors[entry.entry_id] = True
        current = history_data(hass, entry.entry_id)
        current.clear()
        domain_data.setdefault("history_added", {}).pop(entry.entry_id, None)
        domain_data.setdefault("history_pending", {}).pop(entry.entry_id, None)
        return current
    load_errors.pop(entry.entry_id, None)
    existing = existing if isinstance(existing, dict) else {}
    valid_rooms = {s.subentry_id for s in entry.subentries.values() if s.subentry_type == SUBENTRY_TYPE_ROOM}
    allowed = set(HISTORY_METRICS) | {"decision"}
    clean: dict[str, list[str]] = {}
    damaged = False
    for room, keys in existing.items():
        # Keep even partially corrupt JSON recoverable: a later opt-in must
        # not overwrite malformed room data simply because other rooms loaded.
        if not isinstance(keys, list):
            damaged = True
            _LOGGER.warning("Invalid history opt-ins for room %s; keeping Store read-only", room)
            continue
        # Validate before membership tests: dict/list entries are unhashable.
        valid = list(dict.fromkeys(key for key in keys if isinstance(key, str) and key in allowed))
        if len(valid) != len(keys):
            if any(not isinstance(key, str) or key not in allowed for key in keys):
                damaged = True
                _LOGGER.warning("Invalid history metric in room %s; keeping Store read-only", room)
            else:
                _LOGGER.warning("Skipped duplicate history opt-ins for room %s", room)
        if room in valid_rooms:
            clean[room] = valid
    if damaged:
        load_errors[entry.entry_id] = True
        _LOGGER.error(
            "History preferences for %s are partially damaged; valid room history will "
            "remain readable, but saving is blocked to preserve the original Store",
            entry.entry_id,
        )
    # A new platform setup must register its initial enabled sensors afresh.
    # Do not mistake an earlier platform instance's registration for a live one.
    hass.data.setdefault(DOMAIN, {}).setdefault("history_added", {}).pop(entry.entry_id, None)
    hass.data[DOMAIN].setdefault("history_pending", {}).pop(entry.entry_id, None)
    # Loading a different persisted snapshot is a replacement, not a merge.
    # Otherwise removed room/metric opt-ins survive reload in memory.
    current = history_data(hass, entry.entry_id)
    current.clear()
    current.update(clean)
    hass.data[DOMAIN].setdefault("history_stores", {})[entry.entry_id] = store
    return clean


async def async_enable_history(hass, entry, room_id: str, metrics: list[str]) -> list[str]:
    """Persist opt-ins atomically and retry sensor registrations when necessary.

    A durable opt-in and a successfully submitted HA entity registration are
    separate facts: a failed add must not leave the feature permanently stuck.
    This lock is per config entry so two cards/rooms cannot overwrite the same
    Store or request the same entity twice concurrently.
    """
    from asyncio import Lock

    room = next(
        (sub for sub in entry.subentries.values()
         if sub.subentry_id == room_id and sub.subentry_type == SUBENTRY_TYPE_ROOM),
        None,
    )
    if room is None:
        raise ValueError("Unknown local room")
    requested = [
        key for key in metrics
        if isinstance(key, str) and (key == "decision" or key in HISTORY_METRICS)
    ]
    domain_data = hass.data.setdefault(DOMAIN, {})
    if entry.entry_id in domain_data.get("history_load_errors", {}):
        raise RuntimeError("History preferences are unreadable; refusing to overwrite their Store")
    locks = domain_data.setdefault("history_enable_locks", {})
    lock = locks.setdefault(entry.entry_id, Lock())
    async with lock:
        settings = history_data(hass, entry.entry_id)
        previous = set(settings.get(room_id, []))
        updated = sorted(previous.union(requested))
        if updated != sorted(previous):
            # Commit storage *before* publishing the opt-in. A failed save
            # leaves memory and registration untouched, allowing a clean retry.
            store = domain_data["history_stores"][entry.entry_id]
            await async_save_history_confirmed(hass, store, {**settings, room_id: updated})
            settings[room_id] = updated

        # Persisted does not imply registered. Even an already-enabled metric
        # should be retried if an earlier async_add_entities call failed.
        registered = domain_data.setdefault("history_added", {}).setdefault(
            entry.entry_id, {}
        ).setdefault(room_id, set())
        pending = domain_data.setdefault("history_pending", {}).setdefault(
            entry.entry_id, {}
        ).setdefault(room_id, {})
        # async_add_entities may queue HA's actual entity registration. A
        # successful submission is therefore only pending, not proof that an
        # entity exists in the registry. Check again after a grace period.
        registry = None
        try:
            from homeassistant.helpers import entity_registry as er
            registry = er.async_get(hass)
        except ImportError:
            # Isolated pure tests run without Home Assistant. They can still
            # check immediate submission/locking; real HA always has registry.
            pass
        now = time.monotonic()
        for key in updated:
            entity_id = (registry.async_get_entity_id(
                "sensor", DOMAIN, history_sensor_unique_id(room_id, key)
            ) if registry is not None else None)
            registry_entry = registry.async_get(entity_id) if entity_id else None
            disabled_by_user = (registry_entry is not None and
                                getattr(registry_entry, "disabled_by", None) is not None)
            # A registry row may survive a failed async platform add. A live
            # HA state (including 'unavailable'), or deliberate disabling,
            # proves we must NOT submit a duplicate entity.
            state_machine = getattr(hass, "states", None)
            current_state = state_machine.get(entity_id) if state_machine and entity_id else None
            if entity_id and (current_state is not None or disabled_by_user):
                registered.add(key)
                pending.pop(key, None)
            elif registry is not None and key in registered:
                submitted_at = pending.setdefault(key, now)
                if now - submitted_at >= 90.0:
                    # No registered entity after the async platform grace
                    # period: allow precisely one serialized retry.
                    registered.discard(key)
                    pending.pop(key, None)

        to_add = [key for key in updated if key not in registered]
        adder = domain_data.get("history_adders", {}).get(entry.entry_id)
        if to_add and adder is not None:
            # An immediate failure leaves the persisted opt-in intact but
            # does not mark the sensor as submitted. It remains retryable.
            added = adder(room_id, to_add)
            confirmed = to_add if added is None else [key for key in added if key in to_add]
            registered.update(confirmed)
            pending.update({key: now for key in confirmed})
        return settings.get(room_id, [])

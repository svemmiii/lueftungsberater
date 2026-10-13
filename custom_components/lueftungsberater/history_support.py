"""Opt-in, Recorder-friendly room measurements for the history dashboard card.

A Lovelace card is not a permanent background task. Activation is persisted on
Home Assistant's side, and coordinator-backed sensor entities survive restarts.
"""
from __future__ import annotations

import math
import logging
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


def current_value(snapshot: Any, metric: str) -> float | None:
    """Read from the coordinator snapshot, not stale HA advisor attributes."""
    if snapshot is None or metric not in HISTORY_METRICS:
        return None
    key = HISTORY_METRICS[metric][2]
    if key.startswith("air_quality_values."):
        name = key.split(".", 1)[1]
        raw = snapshot.weather.local_station_values.get(name)
        if raw is None:
            raw = snapshot.weather.air_quality_values.get(name)
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
    for key, (label, unit, _, source_key) in HISTORY_METRICS.items():
        if not allowed_metric(attrs, key):
            continue
        limit = good_limits(key, target=target, has_windows=attrs.get("has_window_contacts") is True)
        source = attrs.get(source_key) if source_key else None
        # Existing Recorder readings are in the original sensor's unit. Adapt
        # the axis and its bounds to that unit instead of mislabeling readings.
        state = states.get(source) if states is not None and source else None
        source_unit = str((state.attributes or {}).get("unit_of_measurement") or "").strip() if state else ""
        if source_unit:
            unit = source_unit
            compact = source_unit.lower().replace("μ", "µ").replace("³", "3").replace(" ", "")
            if key.startswith(("pm25_", "pm10_", "no2_", "o3_", "voc_", "hcho_")):
                if compact in {"mg/m3", "mg/m³"}:
                    if key.startswith("hcho_"):
                        pass
                    elif limit["high"] is not None:
                        limit["high"] /= 1000.0
                elif compact in {"µg/m3", "ug/m3"}:
                    if key.startswith("hcho_") and limit["high"] is not None:
                        limit["high"] *= 1000.0
                elif compact in {"ppb", "ppm"}:
                    # NO₂ and O₃ provide their own evaluator-side ppb stages.
                    pollutant = "no2_parts" if key.startswith("no2_") else "o3_parts" if key.startswith("o3_") else None
                    if pollutant and compact == "ppb":
                        limit["high"] = PM_LIMITS[pollutant][1]
                    else:
                        limit["high"] = None
                else:
                    # A relative VOC index is not a mass concentration.
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


async def async_load_history(hass, entry) -> dict[str, list[str]]:
    # The v0.7.2 cleanup targets `DOMAIN.history.*`. Never place new
    # persistent opt-ins in that legacy namespace.
    store = Store(hass, 1, f"{DOMAIN}.history_enabled.{entry.entry_id}")
    existing = await store.async_load()
    if existing is None:
        # COMPLETE(14/15) used the old cleanup namespace. Migrate before
        # async_cleanup_legacy_room_history runs during setup, then only
        # publish the migrated preferences when the new Store saved them.
        legacy = Store(hass, 1, f"{DOMAIN}.history.{entry.entry_id}")
        existing = await legacy.async_load()
        if isinstance(existing, dict):
            await store.async_save(existing)
            try:
                await legacy.async_remove()
            except OSError:
                # Migration succeeded: a failed legacy-file cleanup must not
                # prevent the integration from loading the new durable store.
                _LOGGER.warning("Could not remove old history opt-in store for %s", entry.entry_id)
    existing = existing if isinstance(existing, dict) else {}
    valid_rooms = {s.subentry_id for s in entry.subentries.values() if s.subentry_type == SUBENTRY_TYPE_ROOM}
    clean = {
        room: [key for key in keys if key == "decision" or key in HISTORY_METRICS]
        for room, keys in existing.items()
        if room in valid_rooms and isinstance(keys, list)
    }
    history_data(hass, entry.entry_id).update(clean)
    hass.data[DOMAIN].setdefault("history_stores", {})[entry.entry_id] = store
    return clean


async def async_enable_history(hass, entry, room_id: str, metrics: list[str]) -> list[str]:
    """Save the opt-in before adding sensors; survive interrupted sessions/restarts."""
    room = next((s for s in entry.subentries.values() if s.subentry_id == room_id and s.subentry_type == SUBENTRY_TYPE_ROOM), None)
    if room is None:
        raise ValueError("Unknown local room")
    requested = [key for key in metrics if key == "decision" or key in HISTORY_METRICS]
    settings = history_data(hass, entry.entry_id)
    previous = set(settings.get(room_id, []))
    missing = list(set(requested) - previous)
    if not missing:
        return settings.get(room_id, [])
    # Persist first and publish the opt-in only after durable storage succeeds.
    # Otherwise a transient Store failure makes future calls think it succeeded.
    updated = sorted(previous.union(missing))
    store = hass.data[DOMAIN]["history_stores"][entry.entry_id]
    await store.async_save({**settings, room_id: updated})
    settings[room_id] = updated
    adders = hass.data[DOMAIN].get("history_adders", {})
    adder = adders.get(entry.entry_id)
    if adder is not None:
        adder(room_id, missing)
    return settings[room_id]

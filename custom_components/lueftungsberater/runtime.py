"""Runtime helpers for mapping Home Assistant entities to the pure engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, State
from homeassistant.util.unit_conversion import TemperatureConverter

from .airing import get_tracker
from .co2 import get_co2_tracker
from .const import *
from .engine import evaluate_room
from .models import RoomInput, VentilationResult
from .providers import (
    WeatherAssessment,
    WarningAssessment,
    weather_assessment,
    warning_assessment,
)


@dataclass(slots=True)
class RoomSnapshot:
    """One consistent calculation snapshot shared by all entities of a room."""

    result: VentilationResult | None
    values: dict[str, Any]
    weather: WeatherAssessment
    warnings: WarningAssessment


def _number(hass: HomeAssistant, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None


def _to_celsius(value: Any, unit: str | None) -> float | None:
    """Convert a temperature value to Celsius for the decision engine."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not unit or unit == UnitOfTemperature.CELSIUS:
        return number

    try:
        return TemperatureConverter.convert(
            number,
            unit,
            UnitOfTemperature.CELSIUS,
        )
    except (TypeError, ValueError):
        return number


def _temperature_state_celsius(
    hass: HomeAssistant,
    entity_id: str | None,
) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    return _to_celsius(
        state.state,
        state.attributes.get("unit_of_measurement"),
    )


def weather_temperature_celsius(
    hass: HomeAssistant,
    weather: WeatherAssessment,
) -> float | None:
    """Normalize the selected/fallback weather temperature to Celsius."""
    if weather.temperature is None:
        return None

    source = weather.source_temperature
    state = hass.states.get(source) if source else None

    if state is None:
        return weather.temperature

    if source and source.startswith("weather."):
        unit = state.attributes.get("temperature_unit")
    else:
        unit = state.attributes.get("unit_of_measurement")

    return _to_celsius(weather.temperature, unit)


def _is_on(hass: HomeAssistant, entity_id: str | None) -> bool:
    return bool(entity_id and hass.states.is_state(entity_id, "on"))


def warning_source_configured(entry: ConfigEntry) -> bool:
    """Return whether the new warning-provider selector contains a real source."""
    source = entry.data.get(CONF_WARNING_SOURCE)
    return (
        isinstance(source, str)
        and bool(source)
        and source != WARNING_SOURCE_NONE
    )


def room_co2_value(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> float | None:
    """Return stabilized room CO2 value without changing the decision engine."""
    tracker = get_co2_tracker(hass, entry, subentry)
    if tracker is not None:
        return tracker.current_value
    return _number(hass, subentry.data.get(CONF_CO2))


def room_co2_data_status(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> str:
    """Return current/grace/unavailable/not_configured for UI diagnostics."""
    tracker = get_co2_tracker(hass, entry, subentry)
    if tracker is not None:
        return tracker.data_status
    return (
        "not_configured"
        if not subentry.data.get(CONF_CO2)
        else (
            "current"
            if _number(hass, subentry.data.get(CONF_CO2)) is not None
            else "unavailable"
        )
    )


def _text(hass: HomeAssistant, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    for attr in ("aktuelle_warnung", "warning", "warnung", "headline", "description"):
        val = state.attributes.get(attr)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return state.state


def target_temperature(
    hass: HomeAssistant,
    subentry: ConfigSubentry,
) -> float:
    """Return the configured/climate target normalized to Celsius."""
    target = subentry.data.get(CONF_TARGET_TEMP)
    climate_id = subentry.data.get(CONF_CLIMATE)

    if climate_id:
        climate_state = hass.states.get(climate_id)
        if climate_state:
            climate_target = climate_state.attributes.get("temperature")
            climate_unit = climate_state.attributes.get("temperature_unit")
            converted = _to_celsius(climate_target, climate_unit)
            if converted is not None:
                return converted

    try:
        # The fallback selector is deliberately defined in °C (5..35).
        return float(target) if target is not None else DEFAULT_TARGET_TEMP
    except (TypeError, ValueError):
        return DEFAULT_TARGET_TEMP


def _room_values(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    weather: WeatherAssessment,
) -> dict[str, Any]:
    tracker = get_tracker(hass, entry, subentry)
    windows = subentry.data.get(CONF_WINDOWS, []) or []
    has_windows = bool(windows)
    window_open = (
        tracker.is_open
        if tracker is not None
        else any(hass.states.is_state(entity_id, "on") for entity_id in windows)
    )

    return {
        # All temperatures exposed by this snapshot are Celsius. The frontend
        # converts them to the user's display unit when necessary.
        "temperature_inside": _temperature_state_celsius(
            hass,
            subentry.data.get(CONF_INDOOR_TEMP),
        ),
        "temperature_outside": weather_temperature_celsius(hass, weather),
        "target_temperature": target_temperature(hass, subentry),
        "humidity_inside": _number(hass, subentry.data.get(CONF_INDOOR_HUMIDITY)),
        "humidity_outside": weather.humidity,
        "co2_ppm": room_co2_value(hass, entry, subentry),
        "co2_data_status": room_co2_data_status(hass, entry, subentry),
        "has_co2": bool(subentry.data.get(CONF_CO2)),
        "has_window_contacts": has_windows,
        "window_open": window_open if has_windows else None,
        "open_minutes": (
            tracker.current_open_minutes
            if tracker is not None and tracker.is_open
            else None
        ),
        "last_confirmed_airing": (
            tracker.last_confirmed_airing
            if tracker is not None
            else None
        ),
        "hours_since_last_airing": (
            tracker.hours_since_last_airing
            if tracker is not None
            else None
        ),
    }


def room_display_values(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> dict[str, Any]:
    """Return normalized room input values for UI/attributes."""
    weather = weather_assessment(hass, entry)
    return _room_values(hass, entry, subentry, weather)


def room_source_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> set[str]:
    """Return all entities which should refresh this room."""
    entities: set[str] = set()

    weather = weather_assessment(hass, entry)
    warning = warning_assessment(hass, entry)
    entities.update(weather.source_entities)
    entities.update(warning.source_entities)

    for key in (
        CONF_OUTDOOR_TEMP,
        CONF_OUTDOOR_HUMIDITY,
        CONF_WEATHER_DANGER,
        CONF_WEATHER_REASON,
        CONF_NINA_STATUS,
        CONF_RAIN_NOW,
        CONF_RAIN_SOON,
    ):
        val = entry.data.get(key)
        if isinstance(val, str) and val:
            entities.add(val)

    for key in (
        CONF_INDOOR_TEMP,
        CONF_INDOOR_HUMIDITY,
        CONF_CO2,
        CONF_CLIMATE,
    ):
        val = subentry.data.get(key)
        if isinstance(val, str) and val:
            entities.add(val)

    for val in subentry.data.get(CONF_WINDOWS, []) or []:
        if val:
            entities.add(val)

    return entities


def build_room_snapshot(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> RoomSnapshot:
    """Build all room data once so every room entity sees the same snapshot."""
    weather = weather_assessment(hass, entry)
    warnings = warning_assessment(hass, entry)
    values = _room_values(hass, entry, subentry, weather)

    ti = values["temperature_inside"]
    hi = values["humidity_inside"]
    ta = values["temperature_outside"]
    ha = values["humidity_outside"]

    if None in (ti, hi, ta, ha):
        return RoomSnapshot(None, values, weather, warnings)

    if warning_source_configured(entry):
        normalized_nina = warnings.nina_status
        nina_reason_key = warnings.nina_reason_key
        nina_reason_args = dict(warnings.nina_reason_args)
        nina_original_reason = warnings.nina_original_reason
        provider_weather_caution = warnings.weather_caution
        provider_weather_danger = warnings.weather_danger
        provider_weather_reason_key = warnings.weather_reason_key
        provider_weather_reason_args = dict(warnings.weather_reason_args)
        provider_weather_original_reason = warnings.weather_original_reason
    else:
        nina_state = _text(hass, entry.data.get(CONF_NINA_STATUS)) or "none"
        normalized_nina = {
            "gefahr": "danger",
            "danger": "danger",
            "on": "danger",
            "vorsicht": "caution",
            "caution": "caution",
            "warning": "caution",
            "keine": "none",
            "none": "none",
            "off": "none",
        }.get(nina_state.lower(), "none")
        nina_reason_key = None
        nina_reason_args = {}
        nina_original_reason = _text(hass, entry.data.get(CONF_NINA_STATUS))
        provider_weather_caution = False
        provider_weather_danger = False
        provider_weather_reason_key = None
        provider_weather_reason_args = {}
        provider_weather_original_reason = None

    legacy_weather_danger = _is_on(
        hass,
        entry.data.get(CONF_WEATHER_DANGER),
    )
    legacy_weather_reason = _text(
        hass,
        entry.data.get(CONF_WEATHER_REASON),
    )

    weather_danger = (
        weather.weather_danger
        or provider_weather_danger
        or legacy_weather_danger
    )
    weather_caution = (
        not weather_danger
        and (weather.weather_caution or provider_weather_caution)
    )
    weather_reason_key = (
        provider_weather_reason_key
        or weather.weather_reason_key
    )
    weather_reason_args = (
        provider_weather_reason_args
        if provider_weather_reason_key
        else dict(weather.weather_reason_args)
    )
    weather_original_reason = (
        provider_weather_original_reason
        or legacy_weather_reason
        or weather.weather_original_reason
    )

    legacy_rain_now = _is_on(hass, entry.data.get(CONF_RAIN_NOW))
    legacy_rain_soon = _is_on(hass, entry.data.get(CONF_RAIN_SOON))

    result = evaluate_room(
        RoomInput(
            indoor_temp=ti,
            indoor_humidity=hi,
            outdoor_temp=ta,
            outdoor_humidity=ha,
            target_temp=values["target_temperature"],
            co2=values["co2_ppm"],
            window_open=bool(values["window_open"]),
            hours_since_airing=values["hours_since_last_airing"],
            rain_now=(weather.rain_now or legacy_rain_now),
            rain_soon=(weather.rain_soon or legacy_rain_soon),
            weather_caution=weather_caution,
            weather_danger=weather_danger,
            weather_reason_key=weather_reason_key,
            weather_reason_args=weather_reason_args,
            weather_original_reason=weather_original_reason,
            nina_status=normalized_nina,
            nina_reason_key=nina_reason_key,
            nina_reason_args=nina_reason_args,
            nina_original_reason=nina_original_reason,
        )
    )

    return RoomSnapshot(result, values, weather, warnings)


def build_result(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> VentilationResult | None:
    """Compatibility helper returning only the current room result."""
    return build_room_snapshot(hass, entry, subentry).result

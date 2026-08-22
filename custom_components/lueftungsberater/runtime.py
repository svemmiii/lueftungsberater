"""Runtime helpers for mapping Home Assistant entities to the pure engine."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from .const import *
from .airing import get_tracker
from .co2 import get_co2_tracker
from .engine import evaluate_room
from .providers import weather_assessment, warning_assessment
from .models import RoomInput, VentilationResult


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


def _is_on(hass: HomeAssistant, entity_id: str | None) -> bool:
    return bool(entity_id and hass.states.is_state(entity_id, "on"))


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
    # Prefer useful warning attributes when present.
    for attr in ("aktuelle_warnung", "warning", "warnung", "headline", "description"):
        val = state.attributes.get(attr)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return state.state


def target_temperature(
    hass: HomeAssistant,
    subentry: ConfigSubentry,
) -> float:
    """Return configured/Climate target temperature without changing engine logic."""
    target = subentry.data.get(CONF_TARGET_TEMP)
    climate_id = subentry.data.get(CONF_CLIMATE)

    if climate_id:
        climate_state = hass.states.get(climate_id)
        climate_target = (
            climate_state.attributes.get("temperature")
            if climate_state
            else None
        )
        try:
            if climate_target is not None:
                target = float(climate_target)
        except (TypeError, ValueError):
            pass

    try:
        return float(target) if target is not None else DEFAULT_TARGET_TEMP
    except (TypeError, ValueError):
        return DEFAULT_TARGET_TEMP


def room_display_values(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> dict[str, Any]:
    """Return raw input values for UI/attributes only."""
    tracker = get_tracker(hass, entry, subentry)
    windows = subentry.data.get(CONF_WINDOWS, []) or []
    has_windows = bool(windows)
    window_open = (
        tracker.is_open
        if tracker is not None
        else any(hass.states.is_state(entity_id, "on") for entity_id in windows)
    )

    weather = weather_assessment(hass, entry)

    return {
        "temperature_inside": _number(hass, subentry.data.get(CONF_INDOOR_TEMP)),
        "temperature_outside": weather.temperature,
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


def build_result(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> VentilationResult | None:
    ti = _number(hass, subentry.data.get(CONF_INDOOR_TEMP))
    hi = _number(hass, subentry.data.get(CONF_INDOOR_HUMIDITY))

    weather = weather_assessment(hass, entry)
    warning = warning_assessment(hass, entry)

    ta = weather.temperature
    ha = weather.humidity

    if None in (ti, hi, ta, ha):
        return None

    target = target_temperature(hass, subentry)

    windows = subentry.data.get(CONF_WINDOWS, []) or []
    tracker = get_tracker(hass, entry, subentry)
    window_open = (
        tracker.is_open
        if tracker is not None
        else any(hass.states.is_state(e, "on") for e in windows)
    )
    hours_since_airing = (
        tracker.hours_since_last_airing
        if tracker is not None
        else None
    )

    if entry.data.get(CONF_WARNING_SOURCE):
        normalized_nina = warning.nina_status
        nina_reason = warning.nina_reason
        provider_weather_danger = warning.weather_danger
        provider_weather_reason = warning.weather_reason
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
        nina_reason = None
        provider_weather_danger = False
        provider_weather_reason = None

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

    weather_reason = (
        provider_weather_reason
        or legacy_weather_reason
        or weather.weather_reason
    )

    legacy_rain_now = _is_on(hass, entry.data.get(CONF_RAIN_NOW))
    legacy_rain_soon = _is_on(hass, entry.data.get(CONF_RAIN_SOON))

    return evaluate_room(RoomInput(
        indoor_temp=ti,
        indoor_humidity=hi,
        outdoor_temp=ta,
        outdoor_humidity=ha,
        target_temp=target,
        co2=room_co2_value(hass, entry, subentry),
        window_open=window_open,
        hours_since_airing=hours_since_airing,
        rain_now=(weather.rain_now or legacy_rain_now),
        rain_soon=(weather.rain_soon or legacy_rain_soon),
        weather_danger=weather_danger,
        weather_reason=weather_reason,
        nina_status=normalized_nina,
        nina_reason=nina_reason,
    ))

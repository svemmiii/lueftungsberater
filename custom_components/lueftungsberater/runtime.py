"""Runtime helpers for mapping Home Assistant entities to the pure engine."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import TemperatureConverter

from .airing import get_tracker
from .air_quality import get_air_quality_tracker
from .co2 import get_co2_tracker
from .const import (
    CONF_CLIMATE,
    CONF_CO2,
    CONF_INDOOR_HUMIDITY,
    CONF_INDOOR_TEMP,
    CONF_MANUAL_OUTDOOR,
    CONF_NIGHT_END_TIME,
    CONF_NIGHT_START_HOUR,
    CONF_NIGHT_START_TIME,
    CONF_NINA_STATUS,
    CONF_OUTDOOR_CO2,
    CONF_RAIN_NOW,
    CONF_RAIN_SOON,
    CONF_SURFACE_TEMP,
    CONF_TARGET_TEMP,
    CONF_WARNING_SOURCE,
    CONF_WEATHER_DANGER,
    CONF_WEATHER_REASON,
    CONF_WINDOWS,
    DEFAULT_NIGHT_END_TIME,
    DEFAULT_NIGHT_START_HOUR,
    DEFAULT_TARGET_TEMP,
    WARNING_SOURCE_NONE,
)
from .engine import co2_outdoor_context, evaluate_room, surface_relative_humidity
from .models import RoomInput, VentilationResult
from .mold import get_mold_tracker
from .night import evaluate_night_ventilation
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


def _finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _plausible_temperature(value: Any) -> float | None:
    """Keep any Earth/room-plausible temperature; reject only absurd data."""
    number = _finite_number(value)
    if number is None or not -100.0 <= number <= 100.0:
        return None
    return number


def _plausible_humidity(value: Any) -> float | None:
    """Allow small supersaturation but reject clearly broken RH scaling."""
    number = _finite_number(value)
    if number is None or not 0.0 <= number <= 110.0:
        return None
    return number


def _plausible_co2(value: Any) -> float | None:
    """Reject only physically impossible CO2 ppm values, not dangerous ones."""
    number = _finite_number(value)
    if number is None or not 0.0 <= number <= 1_000_000.0:
        return None
    return number


def _manual_outdoor_entity(entry: ConfigEntry, key: str) -> str | None:
    section = entry.data.get(CONF_MANUAL_OUTDOOR)
    if isinstance(section, dict):
        value = section.get(key)
        if isinstance(value, str) and value:
            return value
    legacy = entry.data.get(key)
    return legacy if isinstance(legacy, str) and legacy else None


def _number(hass: HomeAssistant, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    try:
        return _finite_number(state.state)
    except (TypeError, ValueError):
        return None


def _to_celsius(value: Any, unit: str | None) -> float | None:
    """Convert a temperature value to Celsius for the decision engine."""
    number = _finite_number(value)
    if number is None:
        return None

    if not unit or unit == UnitOfTemperature.CELSIUS:
        return number

    try:
        return TemperatureConverter.convert(
            number,
            unit,
            UnitOfTemperature.CELSIUS,
        )
    except (HomeAssistantError, TypeError, ValueError):
        # A foreign/invalid unit is not evidence that the raw number is Celsius.
        return None


def _temperature_state_celsius(
    hass: HomeAssistant,
    entity_id: str | None,
) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    return _plausible_temperature(
        _to_celsius(
            state.state,
            state.attributes.get("unit_of_measurement"),
        )
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
        return _plausible_temperature(weather.temperature)

    if source and source.startswith("weather."):
        unit = state.attributes.get("temperature_unit")
    else:
        unit = state.attributes.get("unit_of_measurement")

    return _plausible_temperature(_to_celsius(weather.temperature, unit))


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
        return _plausible_co2(tracker.current_value)
    return _plausible_co2(_number(hass, subentry.data.get(CONF_CO2)))


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
            if _plausible_co2(_number(hass, subentry.data.get(CONF_CO2))) is not None
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
    """Return a plausible personal target in Celsius.

    The advisor itself deliberately supports a 5..35 °C comfort target. A
    climate entity may supply the live target, but only when that value is also
    inside the climate entity's own advertised range. Manipulated/out-of-range
    states therefore fall back to the user's stored advisor target instead of
    distorting the recommendation.
    """
    stored = _finite_number(subentry.data.get(CONF_TARGET_TEMP))
    fallback = stored if stored is not None and 5.0 <= stored <= 35.0 else DEFAULT_TARGET_TEMP
    climate_id = subentry.data.get(CONF_CLIMATE)

    if climate_id:
        climate_state = hass.states.get(climate_id)
        if climate_state:
            unit = climate_state.attributes.get("temperature_unit")
            converted = _to_celsius(climate_state.attributes.get("temperature"), unit)
            min_temp = _to_celsius(climate_state.attributes.get("min_temp"), unit)
            max_temp = _to_celsius(climate_state.attributes.get("max_temp"), unit)
            if converted is not None and 5.0 <= converted <= 35.0:
                if min_temp is not None and converted < min_temp:
                    return fallback
                if max_temp is not None and converted > max_temp:
                    return fallback
                return converted

    return fallback


def room_co2_window_values(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> tuple[float | None, bool]:
    """Return the two raw inputs needed by the CO₂ session hysteresis."""
    tracker = get_tracker(hass, entry, subentry)
    windows = subentry.data.get(CONF_WINDOWS, []) or []
    window_open = (
        tracker.is_open
        if tracker is not None
        else any(hass.states.is_state(entity_id, "on") for entity_id in windows)
    )
    return room_co2_value(hass, entry, subentry), bool(window_open)


def _room_values(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    weather: WeatherAssessment,
) -> dict[str, Any]:
    tracker = get_tracker(hass, entry, subentry)
    windows = subentry.data.get(CONF_WINDOWS, []) or []
    has_windows = bool(windows)
    co2_ppm, window_open = room_co2_window_values(hass, entry, subentry)

    return {
        # All temperatures exposed by this snapshot are Celsius. The frontend
        # converts them to the user's display unit when necessary.
        "temperature_inside": _temperature_state_celsius(
            hass,
            subentry.data.get(CONF_INDOOR_TEMP),
        ),
        "temperature_outside": weather_temperature_celsius(hass, weather),
        "target_temperature": target_temperature(hass, subentry),
        "humidity_inside": _plausible_humidity(_number(hass, subentry.data.get(CONF_INDOOR_HUMIDITY))),
        "humidity_outside": _plausible_humidity(weather.humidity),
        "air_quality_index": weather.air_quality_index,
        "air_quality_pollutant": weather.air_quality_pollutant,
        "air_quality_value": weather.air_quality_value,
        "air_quality_values": dict(weather.air_quality_values),
        "co2_ppm": co2_ppm,
        "outdoor_co2_ppm": _plausible_co2(
            _number(hass, _manual_outdoor_entity(entry, CONF_OUTDOOR_CO2))
        ),
        "surface_temperature": _temperature_state_celsius(
            hass, subentry.data.get(CONF_SURFACE_TEMP)
        ),
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
        "air_quality_baseline_value": None,
        "air_quality_typical": None,
        "air_quality_unusual": False,
        "air_quality_trend": "unknown",
        "air_quality_history_samples": 0,
        "night_ventilation_status": "unavailable",
        "night_ventilation_key": None,
        "night_ventilation_args": {},
    }


def room_display_values(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> dict[str, Any]:
    """Return normalized room input values for UI/attributes."""
    from .outside import get_outside_coordinator

    outside = get_outside_coordinator(hass, entry)
    weather = outside.data.weather if outside is not None and outside.data is not None else weather_assessment(hass, entry)
    return _room_values(hass, entry, subentry, weather)


def room_source_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> set[str]:
    """Return only room-local entities; outside sources are shared per advisor."""
    entities: set[str] = set()
    for key in (
        CONF_INDOOR_TEMP,
        CONF_INDOOR_HUMIDITY,
        CONF_CO2,
        CONF_CLIMATE,
        CONF_SURFACE_TEMP,
    ):
        val = subentry.data.get(key)
        if isinstance(val, str) and val:
            entities.add(val)
    for val in subentry.data.get(CONF_WINDOWS, []) or []:
        if val:
            entities.add(val)
    return entities


def _night_start_minutes(subentry: ConfigSubentry) -> int:
    """Return configured local display start as minutes after midnight."""
    raw = subentry.data.get(CONF_NIGHT_START_TIME)
    if isinstance(raw, str):
        parts = raw.split(":")
        try:
            hour = max(0, min(23, int(parts[0])))
            minute = max(0, min(59, int(parts[1]) if len(parts) > 1 else 0))
            return hour * 60 + minute
        except (TypeError, ValueError):
            pass
    try:
        hour = int(subentry.data.get(CONF_NIGHT_START_HOUR, DEFAULT_NIGHT_START_HOUR))
    except (TypeError, ValueError):
        hour = DEFAULT_NIGHT_START_HOUR
    return max(0, min(23, hour)) * 60


def _time_minutes(value: object, default: str) -> int:
    raw = value if isinstance(value, str) else default
    parts = str(raw).split(":")
    try:
        hour = max(0, min(23, int(parts[0])))
        minute = max(0, min(59, int(parts[1]) if len(parts) > 1 else 0))
    except (TypeError, ValueError):
        hour, minute = (int(part) for part in default.split(":"))
    return hour * 60 + minute


def _night_end_minutes(subentry: ConfigSubentry) -> int:
    """Return configured local display end as minutes after midnight."""
    return _time_minutes(subentry.data.get(CONF_NIGHT_END_TIME), DEFAULT_NIGHT_END_TIME)


def build_room_snapshot(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    previous_mode: str | None = None,
    previous_need: str | None = None,
    co2_pending_hold: bool = False,
    co2_airing_active: bool = False,
    co2_finish_ready: bool = False,
    co2_finish_target: float | None = None,
    co2_near_target: float | None = None,
    co2_rearm_threshold: float | None = None,
    co2_minimum_airing_active: bool = False,
    co2_minimum_airing_cautious: bool = False,
    weather: WeatherAssessment | None = None,
    warnings: WarningAssessment | None = None,
) -> RoomSnapshot:
    """Build all room data once so every room entity sees the same snapshot."""
    weather = weather or weather_assessment(hass, entry)
    warnings = warnings or warning_assessment(hass, entry)
    values = _room_values(hass, entry, subentry, weather)

    air_tracker = get_air_quality_tracker(hass, entry)
    if air_tracker is not None and weather.air_quality_values:
        air_context = air_tracker.context(
            weather.air_quality_pollutant, weather.air_quality_value
        )
        values["air_quality_baseline_value"] = air_context.baseline
        values["air_quality_typical"] = air_context.typical
        values["air_quality_unusual"] = air_context.unusual
        values["air_quality_trend"] = air_context.trend
        values["air_quality_history_samples"] = air_context.samples

    ti = values["temperature_inside"]
    hi = values["humidity_inside"]
    ta = values["temperature_outside"]
    ha = values["humidity_outside"]

    surface_rh = (
        surface_relative_humidity(ti, hi, values.get("surface_temperature"))
        if ti is not None and hi is not None
        else None
    )
    mold_tracker = get_mold_tracker(hass, entry, subentry)
    if mold_tracker is not None:
        mold_tracker.observe(surface_rh)
        values["mold_current_critical_minutes"] = mold_tracker.current_critical_minutes
        values["mold_critical_minutes_24h"] = mold_tracker.critical_minutes_24h
        values["mold_persistent"] = mold_tracker.persistent
    else:
        values["mold_current_critical_minutes"] = None
        values["mold_critical_minutes_24h"] = None
        values["mold_persistent"] = False
    values["surface_relative_humidity"] = surface_rh

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

    night_advice = evaluate_night_ventilation(
        now=dt_util.now(),
        indoor_temp=ti,
        indoor_humidity=hi,
        target_temp=values["target_temperature"],
        indoor_co2=values.get("co2_ppm"),
        outdoor_co2=values.get("outdoor_co2_ppm"),
        outdoor_temp=ta,
        outdoor_humidity=ha,
        rain_now=(weather.rain_now or legacy_rain_now),
        wind_speed_kmh=weather.wind_speed_kmh,
        wind_gust_kmh=weather.wind_gust_kmh,
        start_minute=_night_start_minutes(subentry),
        end_minute=_night_end_minutes(subentry),
        hourly_forecast=weather.hourly_forecast,
        air_quality=weather.air_quality_index,
        nina_status=normalized_nina,
        weather_caution=weather_caution,
        weather_danger=weather_danger,
        air_quality_typical=values.get("air_quality_typical"),
        air_quality_unusual=bool(values.get("air_quality_unusual")),
        air_quality_trend=str(values.get("air_quality_trend") or "unknown"),
    )
    values["night_ventilation_status"] = night_advice.status
    values["night_ventilation_key"] = night_advice.reason_key
    values["night_ventilation_args"] = dict(night_advice.reason_args)
    # Internal coordinator metadata only; sensor.py deliberately does not expose
    # this extra flag as an entity attribute.
    values["_night_ventilation_safety_block"] = night_advice.safety_block

    room_input = RoomInput(
        indoor_temp=ti,
        indoor_humidity=hi,
        outdoor_temp=ta,
        outdoor_humidity=ha,
        target_temp=values["target_temperature"],
        co2=values["co2_ppm"],
        outdoor_co2=values.get("outdoor_co2_ppm"),
        window_open=bool(values["window_open"]),
        open_minutes=values.get("open_minutes"),
        hours_since_airing=values["hours_since_last_airing"],
        rain_now=(weather.rain_now or legacy_rain_now),
        rain_soon=(weather.rain_soon or legacy_rain_soon),
        rain_minutes_until=weather.rain_minutes_until,
        weather_caution=weather_caution,
        weather_danger=weather_danger,
        weather_reason_key=weather_reason_key,
        weather_reason_args=weather_reason_args,
        weather_original_reason=weather_original_reason,
        short_term_weather_change=weather.short_term_change,
        short_term_weather_kind=weather.short_term_kind,
        short_term_weather_minutes=weather.short_term_minutes,
        short_term_weather_condition=weather.short_term_condition,
        nina_status=normalized_nina,
        nina_reason_key=nina_reason_key,
        nina_reason_args=nina_reason_args,
        nina_original_reason=nina_original_reason,
        surface_temp=values.get("surface_temperature"),
        mold_current_critical_minutes=values.get("mold_current_critical_minutes"),
        mold_critical_minutes_24h=values.get("mold_critical_minutes_24h"),
        mold_persistent=bool(values.get("mold_persistent")),
        air_quality=weather.air_quality_index,
        air_quality_pollutant=weather.air_quality_pollutant,
        air_quality_value=weather.air_quality_value,
        air_quality_baseline_value=values.get("air_quality_baseline_value"),
        air_quality_typical=values.get("air_quality_typical"),
        air_quality_unusual=bool(values.get("air_quality_unusual")),
        air_quality_trend=str(values.get("air_quality_trend") or "unknown"),
        air_quality_history_samples=int(values.get("air_quality_history_samples") or 0),
        previous_mode=previous_mode,
        previous_need=previous_need,
        co2_pending_hold=co2_pending_hold,
        co2_airing_active=co2_airing_active,
        co2_finish_ready=co2_finish_ready,
        co2_finish_target=co2_finish_target,
        co2_near_target=co2_near_target,
        co2_rearm_threshold=co2_rearm_threshold,
        co2_minimum_airing_active=co2_minimum_airing_active,
        co2_minimum_airing_cautious=co2_minimum_airing_cautious,
    )
    # Internal-only category snapshot for the five-minute CO₂ hold. Keeping it
    # in the shared room snapshot lets the coordinator compare outdoor changes
    # without adding recorder attributes or a second decision path.
    values["_co2_outdoor_context"] = co2_outdoor_context(room_input)
    result = evaluate_room(room_input)

    return RoomSnapshot(result, values, weather, warnings)


def build_result(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> VentilationResult | None:
    """Compatibility helper returning only the current room result."""
    return build_room_snapshot(hass, entry, subentry).result

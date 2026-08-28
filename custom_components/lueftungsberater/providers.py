"""Provider adapters for weather, radar and warning integrations."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import (
    CONF_MANUAL_OUTDOOR,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMP,
    CONF_WARNING_SOURCE,
    CONF_WEATHER,
    DATA_FORECAST_CACHE,
    DOMAIN,
    WARNING_SOURCE_NONE,
)

WEATHER_DANGER_CONDITIONS = {
    "lightning",
    "lightning-rainy",
    "hail",
    "exceptional",
}

RAIN_CONDITIONS = {
    "rainy",
    "pouring",
    "lightning-rainy",
    "snowy-rainy",
}

WEATHER_WARNING_WORDS = (
    "gewitter",
    "thunderstorm",
    "sturm",
    "storm",
    "orkan",
    "hurricane",
    "wind",
    "hagel",
    "hail",
    "starkregen",
    "heavy rain",
    "dauerregen",
    "continuous rain",
)

CLEAR_WORDS = (
    "entwarnung",
    "warnung ist aufgehoben",
    "warnung wurde aufgehoben",
    "die warnung ist aufgehoben",
    "gefahr ist vorüber",
    "gefahr ist vorueber",
    "all-clear",
    "all clear",
    "warning has been lifted",
    "warning lifted",
)

CLEAR_NEGATIONS = (
    "noch keine entwarnung",
    "keine entwarnung",
    "entwarnung liegt nicht vor",
    "entwarnung liegt noch nicht vor",
    "entwarnung wurde nicht",
    "entwarnung wurde noch nicht",
    "noch nicht entwarnt",
    "not an all-clear",
    "no all-clear",
    "warning has not been lifted",
)

# Defensive wording guard: these phrases contain the substring "Entwarnung"
# but do not mean that the affected room can be treated as fully clear. They are
# intentionally *not* a new warning state; they merely stop substring matching
# from turning an ambiguous/partial update into a full all-clear.
CLEAR_QUALIFIERS = (
    "teilentwarnung",
    "teil-entwarnung",
    "teilweise entwarnung",
    "bedingte entwarnung",
    "bedingt entwarnt",
    "entwarnung mit einschränkungen",
    "entwarnung mit einschraenkungen",
    "partielle entwarnung",
    "partial all-clear",
    "partial all clear",
    "conditional all-clear",
    "conditional all clear",
    "all-clear with restrictions",
    "all clear with restrictions",
)

# Official instructions are authoritative. The integration does not second-guess
# why an authority orders windows/doors closed or ventilation switched off.
OFFICIAL_CLOSE_ACTIONS = (
    "fenster und türen schließen",
    "fenster und tueren schliessen",
    "fenster und türen geschlossen halten",
    "fenster und tueren geschlossen halten",
    "fenster und türen weiterhin geschlossen halten",
    "fenster und tueren weiterhin geschlossen halten",
    "halten sie fenster und türen geschlossen",
    "halten sie fenster und tueren geschlossen",
    "schließen sie fenster und türen",
    "schliessen sie fenster und tueren",
    "schließen sie vorsorglich fenster",
    "schliessen sie vorsorglich fenster",
    "vorsorglich fenster",
    "fenster geschlossen halten",
    "fenster geschlossen lassen",
    "fenster und türen geschlossen lassen",
    "fenster und tueren geschlossen lassen",
    "fenster schließen",
    "fenster schliessen",
    "türen und fenster schließen",
    "tueren und fenster schliessen",
    "dachfenster schließen",
    "dachfenster schliessen",
    "close skylights",
    "lüftungs- und klimaanlagen ab",
    "luftungs- und klimaanlagen ab",
    "lüftungsanlage abschalten",
    "luftungsanlage abschalten",
    "lüftungsanlagen abschalten",
    "lüftungsanlage ausschalten",
    "luftungsanlage ausschalten",
    "lüftungsanlagen ausschalten",
    "luftungsanlagen ausschalten",
    "lüftung ausschalten",
    "luftung ausschalten",
    "klimaanlage ausschalten",
    "klimaanlagen ausschalten",
    "frischluftzufuhr vermeiden",
    "frischluftzufuhr abschalten",
    "außenluftzufuhr abschalten",
    "aussenluftzufuhr abschalten",
    "luftungsanlagen abschalten",
    "lüftung abschalten",
    "luftung abschalten",
    "klimaanlage abschalten",
    "klimaanlagen abschalten",
    "außenluftzufuhr vermeiden",
    "aussenluftzufuhr vermeiden",
    "keep windows and doors closed",
    "keep windows closed",
    "keep doors and windows closed",
    "shut windows",
    "shut the windows",
    "close windows and doors",
    "close the windows",
    "turn off ventilation",
    "switch off ventilation",
    "turn off air conditioning",
    "switch off air conditioning",
    "avoid outdoor air intake",
)


_LOGGER = logging.getLogger(__name__)
HOURLY_FORECAST_CACHE_MAX_AGE = timedelta(minutes=45)


@dataclass(slots=True)
class WeatherAssessment:
    """Normalized data from the selected weather provider."""

    temperature: float | None = None
    humidity: float | None = None
    rain_now: bool = False
    rain_soon: bool = False
    rain_minutes_until: float | None = None
    weather_caution: bool = False
    weather_danger: bool = False
    weather_reason_key: str | None = None
    weather_reason_args: dict[str, Any] = field(default_factory=dict)
    weather_original_reason: str | None = None
    source_entities: set[str] = field(default_factory=set)
    source_temperature: str | None = None
    source_humidity: str | None = None
    temperature_source_kind: str | None = None
    humidity_source_kind: str | None = None
    provider_domain: str | None = None
    radar_current_entity: str | None = None
    radar_next_entity: str | None = None
    wind_speed_kmh: float | None = None
    wind_gust_kmh: float | None = None
    air_quality_index: str = "unknown"
    air_quality_pollutant: str | None = None
    air_quality_value: float | None = None
    air_quality_values: dict[str, float] = field(default_factory=dict)
    hourly_forecast: list[dict[str, Any]] = field(default_factory=list)
    hourly_forecast_updated: datetime | None = None


@dataclass(slots=True)
class WarningAssessment:
    """Normalized data from the selected warning provider."""

    weather_caution: bool = False
    weather_danger: bool = False
    weather_reason_key: str | None = None
    weather_reason_args: dict[str, Any] = field(default_factory=dict)
    weather_original_reason: str | None = None
    nina_status: str = "none"
    nina_reason_key: str | None = None
    nina_reason_args: dict[str, Any] = field(default_factory=dict)
    nina_original_reason: str | None = None
    warning_notice_kind: str | None = None
    warning_notice_text: str | None = None
    official_close_instruction: bool = False
    source_entities: set[str] = field(default_factory=set)
    provider_domain: str | None = None
    warning_ids: set[str] = field(default_factory=set)


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _state_float(state: State | None) -> float | None:
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    return _float(state.state)


def _manual_override(entry: ConfigEntry, key: str) -> str | None:
    section = entry.data.get(CONF_MANUAL_OUTDOOR)
    if isinstance(section, dict):
        value = section.get(key)
        if isinstance(value, str) and value:
            return value

    legacy = entry.data.get(key)
    if isinstance(legacy, str) and legacy:
        return legacy
    return None


def _registry_entry(
    hass: HomeAssistant,
    entity_id: str | None,
):
    if not entity_id:
        return None
    return er.async_get(hass).async_get(entity_id)


def _config_entry_entities(
    hass: HomeAssistant,
    config_entry_id: str | None,
) -> list[str]:
    if not config_entry_id:
        return []
    registry = er.async_get(hass)
    return [
        item.entity_id
        for item in er.async_entries_for_config_entry(
            registry,
            config_entry_id,
        )
    ]


def _provider_domain_for_entity(
    hass: HomeAssistant,
    entity_id: str | None,
) -> str | None:
    registry_entry = _registry_entry(hass, entity_id)
    if registry_entry is None or not registry_entry.config_entry_id:
        return None
    config_entry = hass.config_entries.async_get_entry(
        registry_entry.config_entry_id
    )
    return config_entry.domain if config_entry else None


def _wind_to_kmh(value: Any, unit: str | None) -> float:
    number = _float(value) or 0.0
    unit = (unit or "km/h").lower()

    if unit in {"m/s", "mps"}:
        return number * 3.6
    if unit in {"mph", "mi/h"}:
        return number * 1.60934
    if unit in {"kn", "kt", "knot", "knots"}:
        return number * 1.852

    return number


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str) and value:
        result = dt_util.parse_datetime(value)
    else:
        return None

    if result is None:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=dt_util.UTC)
    return result



AIR_QUALITY_LIMITS: dict[str, tuple[float, float, float, float]] = {
    # UBA LQI 2025/2026 hourly classes: very good / good / moderate / poor /
    # very poor. Values are µg/m³ and the worst available pollutant wins.
    "no2": (10.0, 30.0, 60.0, 100.0),
    "pm10": (9.0, 27.0, 54.0, 90.0),
    "pm2_5": (5.0, 15.0, 30.0, 50.0),
    "o3": (24.0, 72.0, 144.0, 240.0),
    "so2": (10.0, 30.0, 60.0, 100.0),
}
AIR_QUALITY_MAX_AGE = timedelta(hours=3)

AIR_QUALITY_RANK = {
    "unknown": -1,
    "very_good": 0,
    "good": 1,
    "moderate": 2,
    "poor": 3,
    "very_poor": 4,
}


def _air_quality_kind(entity_id: str, original_name: str = "") -> str | None:
    low = f"{entity_id} {original_name}".lower().replace("-", "_")
    if "pm2_5" in low or "pm25" in low or "pm2.5" in low:
        return "pm2_5"
    if "pm10" in low:
        return "pm10"
    if "stickstoffdioxid" in low or "nitrogen_dioxide" in low or " no2" in f" {low}":
        return "no2"
    if "ozon" in low or "ozone" in low or " o3" in f" {low}":
        return "o3"
    if "schwefeldioxid" in low or "sulfur_dioxide" in low or "sulphur_dioxide" in low or " so2" in f" {low}":
        return "so2"
    return None


def _air_quality_state_is_fresh(state: State) -> bool:
    """Reject stale pollutant values without penalising lightweight test stubs."""
    stamp = getattr(state, "last_reported", None) or getattr(state, "last_updated", None)
    if not isinstance(stamp, datetime):
        return True
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt_util.UTC)
    age = dt_util.utcnow() - stamp
    return timedelta(0) <= age <= AIR_QUALITY_MAX_AGE


def _air_quality_ugm3(state: State | None) -> float | None:
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    if not _air_quality_state_is_fresh(state):
        return None
    value = _state_float(state)
    if value is None or value < 0:
        return None
    unit = str(state.attributes.get("unit_of_measurement") or "").lower().replace("μ", "µ")
    if unit in {"µg/m³", "ug/m³", "µg/m3", "ug/m3"}:
        converted = value
    elif unit in {"mg/m³", "mg/m3"}:
        converted = value * 1000.0
    else:
        # Do not guess concentrations from a unitless/foreign sensor.
        return None
    if converted > 5000:
        return None
    return converted


def _air_quality_class(kind: str, value: float) -> str:
    limits = AIR_QUALITY_LIMITS[kind]
    if value <= limits[0]:
        return "very_good"
    if value <= limits[1]:
        return "good"
    if value <= limits[2]:
        return "moderate"
    if value <= limits[3]:
        return "poor"
    return "very_poor"


def _discover_air_quality(
    hass: HomeAssistant,
    weather_entity_id: str,
) -> tuple[str, str | None, float | None, dict[str, float], set[str]]:
    """Return the UBA-LQI class from plausible sibling air-quality sensors."""
    registry_entry = _registry_entry(hass, weather_entity_id)
    if registry_entry is None:
        return "unknown", None, None, {}, set()

    registry = er.async_get(hass)
    candidates: list[tuple[str, str, State | None]] = []
    used: set[str] = set()
    for entity_id in _config_entry_entities(hass, registry_entry.config_entry_id):
        item = registry.async_get(entity_id)
        original_name = str(getattr(item, "original_name", "") or "") if item else ""
        kind = _air_quality_kind(entity_id, original_name)
        if kind is None:
            continue
        state = hass.states.get(entity_id)
        candidates.append((kind, entity_id, state))
        used.add(entity_id)

    values: dict[str, float] = {}
    valid_items: list[tuple[str, float]] = []
    for kind, _entity_id, state in candidates:
        value = _air_quality_ugm3(state)
        if value is None:
            continue
        # Keep the worst sensor when a provider exposes the same pollutant twice.
        values[kind] = max(value, values.get(kind, value))

    # dwd_weather temporarily exposed a lone 0 while its other air-quality
    # siblings were unavailable. A single zero surrounded by unavailable
    # siblings is therefore treated as a provider placeholder, not "perfect air".
    if len(candidates) >= 2 and len(values) == 1 and next(iter(values.values())) == 0:
        return "unknown", None, None, {}, used

    for kind, value in values.items():
        valid_items.append((kind, value))
    if not valid_items:
        return "unknown", None, None, {}, used

    worst_kind = None
    worst_value = None
    worst_class = "unknown"
    for kind, value in valid_items:
        classification = _air_quality_class(kind, value)
        if AIR_QUALITY_RANK[classification] > AIR_QUALITY_RANK[worst_class]:
            worst_class = classification
            worst_kind = kind
            worst_value = value

    return worst_class, worst_kind, worst_value, values, used



def _forecast_temperature_to_celsius(value: Any, unit: str | None) -> float | None:
    number = _float(value)
    if number is None:
        return None
    if not unit or unit == UnitOfTemperature.CELSIUS:
        return number
    try:
        return float(TemperatureConverter.convert(number, unit, UnitOfTemperature.CELSIUS))
    except (TypeError, ValueError):
        return number


def _normalize_hourly_forecast(
    hass: HomeAssistant,
    weather_entity_id: str,
    items: Any,
) -> list[dict[str, Any]]:
    """Normalize best-effort hourly forecast data into engine-friendly units."""
    if not isinstance(items, list):
        return []
    state = hass.states.get(weather_entity_id)
    temperature_unit = state.attributes.get("temperature_unit") if state else None
    wind_unit = state.attributes.get("wind_speed_unit") if state else None
    normalized: list[dict[str, Any]] = []
    for raw in items[:36]:
        if not isinstance(raw, dict):
            continue
        stamp = _parse_datetime(raw.get("datetime"))
        temp = _forecast_temperature_to_celsius(raw.get("temperature"), temperature_unit)
        if stamp is None or temp is None:
            continue
        item: dict[str, Any] = {
            "datetime": dt_util.as_local(stamp),
            "temperature": temp,
        }
        for key in ("humidity", "precipitation_probability", "precipitation"):
            value = _float(raw.get(key))
            if value is not None:
                item[key] = value
        condition = raw.get("condition")
        if isinstance(condition, str) and condition:
            item["condition"] = condition
        wind = _float(raw.get("wind_speed"))
        gust = _float(raw.get("wind_gust_speed"))
        if wind is not None:
            item["wind_speed"] = _wind_to_kmh(wind, wind_unit)
        if gust is not None:
            item["wind_gust_speed"] = _wind_to_kmh(gust, wind_unit)
        normalized.append(item)
    return normalized


def _cached_hourly_forecast(
    hass: HomeAssistant, entry: ConfigEntry
) -> tuple[list[dict[str, Any]], datetime | None]:
    entry_id = getattr(entry, "entry_id", None)
    domain_data = getattr(hass, "data", {})
    if not entry_id or not isinstance(domain_data, dict):
        return [], None
    cache = domain_data.get(DOMAIN, {}).get(DATA_FORECAST_CACHE, {}).get(entry_id)
    if not isinstance(cache, dict):
        return [], None
    items = cache.get("forecast")
    updated = cache.get("updated")
    return (list(items) if isinstance(items, list) else [], updated if isinstance(updated, datetime) else None)


async def async_refresh_hourly_forecast(
    hass: HomeAssistant, entry: ConfigEntry, *, force: bool = False
) -> None:
    """Refresh the selected weather entity's hourly forecast, if supported.

    Forecasts are optional. Unsupported providers or temporary failures must never
    make the normal current-condition advice unavailable.
    """
    weather_entity_id = entry.data.get(CONF_WEATHER)
    if not isinstance(weather_entity_id, str) or not weather_entity_id:
        return
    domain_data = hass.data.setdefault(DOMAIN, {})
    store = domain_data.setdefault(DATA_FORECAST_CACHE, {})
    cached = store.get(entry.entry_id)
    now = dt_util.utcnow()
    if not force and isinstance(cached, dict):
        updated = cached.get("updated")
        if isinstance(updated, datetime) and now - updated < HOURLY_FORECAST_CACHE_MAX_AGE:
            return

    try:
        response = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"type": "hourly"},
            target={"entity_id": weather_entity_id},
            blocking=True,
            return_response=True,
        )
    except Exception as exc:  # noqa: BLE001 - forecast support is optional
        _LOGGER.debug("Hourly forecast unavailable for %s: %s", weather_entity_id, exc)
        return

    entity_response = response.get(weather_entity_id) if isinstance(response, dict) else None
    raw_forecast = entity_response.get("forecast") if isinstance(entity_response, dict) else None
    normalized = _normalize_hourly_forecast(hass, weather_entity_id, raw_forecast)
    if normalized:
        store[entry.entry_id] = {"updated": now, "forecast": normalized}

def _discover_dwd_radar_entities(
    hass: HomeAssistant,
    weather_entity_id: str,
) -> tuple[str | None, str | None, set[str]]:
    """Find dwd_weather radar sensors related to the selected weather entry."""
    registry_entry = _registry_entry(hass, weather_entity_id)
    if registry_entry is None:
        return None, None, set()

    related = _config_entry_entities(
        hass,
        registry_entry.config_entry_id,
    )

    current = None
    next_rain = None
    used: set[str] = set()

    for entity_id in related:
        low = entity_id.lower()

        if (
            "radar_niederschlag_aktuell" in low
            or "radar_precipitation_current" in low
        ):
            current = entity_id
            used.add(entity_id)
        elif (
            "radar_nachster_niederschlag" in low
            or "radar_naechster_niederschlag" in low
            or "radar_next_precipitation" in low
        ):
            next_rain = entity_id
            used.add(entity_id)

    return current, next_rain, used


def weather_assessment(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> WeatherAssessment:
    """Normalize the selected weather entity plus known provider extras."""
    result = WeatherAssessment()
    weather_entity_id = entry.data.get(CONF_WEATHER)

    if not isinstance(weather_entity_id, str) or not weather_entity_id:
        temp_override = _manual_override(entry, CONF_OUTDOOR_TEMP)
        humidity_override = _manual_override(entry, CONF_OUTDOOR_HUMIDITY)

        if temp_override:
            result.source_entities.add(temp_override)
            result.source_temperature = temp_override
            result.temperature = _state_float(hass.states.get(temp_override))
            result.temperature_source_kind = (
                "local_sensor" if result.temperature is not None else "unavailable"
            )

        if humidity_override:
            result.source_entities.add(humidity_override)
            result.source_humidity = humidity_override
            result.humidity = _state_float(hass.states.get(humidity_override))
            result.humidity_source_kind = (
                "local_sensor" if result.humidity is not None else "unavailable"
            )

        return result

    state = hass.states.get(weather_entity_id)
    result.source_entities.add(weather_entity_id)
    result.provider_domain = _provider_domain_for_entity(
        hass,
        weather_entity_id,
    )
    result.hourly_forecast, result.hourly_forecast_updated = _cached_hourly_forecast(
        hass, entry
    )

    temp_override = _manual_override(entry, CONF_OUTDOOR_TEMP)
    humidity_override = _manual_override(entry, CONF_OUTDOOR_HUMIDITY)

    # Always subscribe to configured local sensors as well as the weather
    # entity. This lets the advisor fall back immediately when a local
    # sensor disappears and switch back automatically when it recovers.
    if temp_override:
        result.source_entities.add(temp_override)
    if humidity_override:
        result.source_entities.add(humidity_override)

    weather_available = (
        state is not None
        and state.state not in {"unknown", "unavailable", "none", ""}
    )
    weather_temperature = (
        _float(state.attributes.get("temperature"))
        if weather_available
        else None
    )
    weather_humidity = (
        _float(state.attributes.get("humidity"))
        if weather_available
        else None
    )

    local_temperature = (
        _state_float(hass.states.get(temp_override))
        if temp_override
        else None
    )
    if local_temperature is not None:
        result.temperature = local_temperature
        result.source_temperature = temp_override
        result.temperature_source_kind = "local_sensor"
    elif weather_temperature is not None:
        result.temperature = weather_temperature
        result.source_temperature = weather_entity_id
        result.temperature_source_kind = (
            "weather_fallback" if temp_override else "weather_service"
        )
    else:
        result.source_temperature = temp_override or weather_entity_id
        result.temperature_source_kind = "unavailable"

    local_humidity = (
        _state_float(hass.states.get(humidity_override))
        if humidity_override
        else None
    )
    if local_humidity is not None:
        result.humidity = local_humidity
        result.source_humidity = humidity_override
        result.humidity_source_kind = "local_sensor"
    elif weather_humidity is not None:
        result.humidity = weather_humidity
        result.source_humidity = weather_entity_id
        result.humidity_source_kind = (
            "weather_fallback" if humidity_override else "weather_service"
        )
    else:
        result.source_humidity = humidity_override or weather_entity_id
        result.humidity_source_kind = "unavailable"

    # Air-quality sensors are sibling entities of the selected weather config
    # entry and can remain valid even when the weather entity itself is briefly
    # unavailable. Evaluate them independently and subscribe to their changes.
    (
        result.air_quality_index,
        result.air_quality_pollutant,
        result.air_quality_value,
        result.air_quality_values,
        air_entities,
    ) = _discover_air_quality(hass, weather_entity_id)
    result.source_entities.update(air_entities)

    if not weather_available:
        return result

    condition = state.state
    result.rain_now = condition in RAIN_CONDITIONS
    if condition == "pouring":
        result.weather_reason_key = "weather_heavy_rain_current"

    wind_unit = state.attributes.get("wind_speed_unit")
    wind = _wind_to_kmh(state.attributes.get("wind_speed"), wind_unit)
    gust = _wind_to_kmh(state.attributes.get("wind_gust_speed"), wind_unit)
    result.wind_speed_kmh = wind if wind > 0 else None
    result.wind_gust_kmh = gust if gust > 0 else None

    # These are ventilation/window-safety thresholds, not claims about the
    # DWD warning colour. Bft 6 (39 km/h mean wind) starts as caution; from
    # roughly Bft 7 / storm-force gusts an open window itself becomes a
    # meaningful disadvantage, so the advisor may recommend keeping it shut.
    if condition in WEATHER_DANGER_CONDITIONS or wind >= 75 or gust >= 105:
        result.weather_danger = True
        result.weather_caution = False

        if condition in {"lightning", "lightning-rainy"}:
            result.weather_reason_key = "weather_thunderstorm_danger"
        elif condition == "hail":
            result.weather_reason_key = "weather_hail_danger"
        elif condition == "exceptional":
            result.weather_reason_key = "weather_exceptional_danger"
        else:
            speed = gust if gust >= 105 else wind
            result.weather_reason_key = "weather_wind_danger"
            result.weather_reason_args = {"speed_kmh": speed}
    elif wind >= 50 or gust >= 65:
        # With the four-stage advisor this is a clear disadvantage (orange),
        # not automatically the same as a hard red weather hazard.
        result.weather_caution = True
        speed = gust if gust >= 65 else wind
        result.weather_reason_key = "weather_wind_caution"
        result.weather_reason_args = {"speed_kmh": speed}

    current_radar, next_radar, radar_entities = _discover_dwd_radar_entities(
        hass,
        weather_entity_id,
    )
    result.source_entities.update(radar_entities)
    result.radar_current_entity = current_radar
    result.radar_next_entity = next_radar

    if current_radar:
        current_value = _state_float(hass.states.get(current_radar))
        if current_value is not None and current_value > 0:
            result.rain_now = True

    if next_radar:
        next_state = hass.states.get(next_radar)
        next_dt = None

        if next_state is not None:
            if next_state.state not in {
                "unknown",
                "unavailable",
                "none",
                "",
            }:
                next_dt = _parse_datetime(next_state.state)

            if next_dt is None:
                next_dt = _parse_datetime(
                    next_state.attributes.get("beginn")
                    or next_state.attributes.get("start")
                )

        if next_dt is not None:
            now = dt_util.utcnow()
            if now <= next_dt:
                result.rain_minutes_until = (next_dt - now).total_seconds() / 60.0
                # Keep the old boolean as a compatibility signal for exported
                # diagnostics/legacy inputs; the engine now decides whether the
                # forecast is actually relevant to the expected airing duration.
                if next_dt <= now + timedelta(hours=2):
                    result.rain_soon = True

    return result


def _text(state: State, attr: str) -> str:
    value = state.attributes.get(attr)
    return str(value).strip() if value is not None else ""


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(word in low for word in words)


def _is_clear_warning(text: str) -> bool:
    low = " ".join(str(text).lower().split())
    if any(word in low for word in CLEAR_QUALIFIERS):
        return False
    if any(word in low for word in CLEAR_NEGATIONS):
        return False
    # Catch natural negations around the word "Entwarnung" without requiring
    # an exhaustive list of sentence variants. Examples: "Entwarnung noch
    # nicht möglich", "keine vollständige Entwarnung".
    if re.search(r"(?:keine|keinerlei|noch keine|nicht|noch nicht)[^.!?]{0,50}entwarnung", low):
        return False
    if re.search(r"entwarnung[^.!?]{0,50}(?:noch nicht|nicht möglich|nicht erfolgt)", low):
        return False
    return any(word in low for word in CLEAR_WORDS)


def _weather_warning_kind(text: str) -> str:
    """Classify a warning so UI text can stay specific in every language."""
    low = text.lower()
    if any(word in low for word in ("starkregen", "heavy rain")):
        return "heavy_rain"
    if any(word in low for word in ("dauerregen", "continuous rain")):
        return "continuous_rain"
    if any(word in low for word in ("hagel", "hail")):
        return "hail"
    if any(word in low for word in ("gewitter", "thunderstorm")):
        return "thunderstorm"
    if any(word in low for word in ("orkan", "hurricane", "sturm", "storm")):
        return "storm"
    if "wind" in low or "bö" in low or "boe" in low:
        return "wind"
    return "weather"


def _weather_reason_key(text: str, danger: bool) -> str:
    kind = _weather_warning_kind(text)
    suffix = "danger" if danger else "caution"
    if kind == "weather":
        return f"weather_{suffix}"
    return f"weather_{kind}_{suffix}"


def _air_reason_key(text: str, status: str) -> str:
    low = text.lower()
    suffix = "danger" if status == "danger" else "caution"
    if any(word in low for word in (
        "brandrauch", "rauchentwicklung", "rauchgas", "rauchwolke",
        "rauchbelastung", "smoke",
    )):
        return f"air_smoke_{suffix}"
    if any(word in low for word in (
        "gefahrstoff", "schadstoff", "gasaustritt", "gaswolke",
        "chemieunfall", "chemikal", "giftig", "toxisch",
        "hazardous substance", "gas leak", "toxic",
    )):
        return f"air_hazard_{suffix}"
    return f"nina_air_{suffix}"


def _evaluate_air_warning(
    headline: str,
    description: str,
    actions: str,
    severity: str,
) -> str:
    """Return none/caution/danger/clear from official action instructions.

    v0.7 deliberately stops judging the event type or CAP severity itself. An
    authority has already assessed the incident. We only consume instructions
    that directly affect ventilation in the protected room/building.
    """
    alltext = " ".join((headline, description, actions)).lower()

    if _contains_any(f"{actions} {description}", OFFICIAL_CLOSE_ACTIONS):
        return "danger"

    if _is_clear_warning(alltext):
        return "clear"

    # No direct close/outdoor-air instruction means the official warning is
    # outside this integration's remit. Weather and measured air quality are
    # still evaluated independently by their dedicated paths.
    return "none"



def _optional_entity_registry(hass: HomeAssistant):
    """Return the entity registry when available.

    Warning evaluation can still work from legacy warning attributes when the
    registry is unavailable (for example in lightweight unit-test stubs or
    during very early startup).
    """
    try:
        return er.async_get(hass)
    except (AttributeError, KeyError):
        return None




def _nina_details_bucket(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("nina_details_cache", {})


async def async_refresh_nina_details(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Fetch full NINA details once per active warning id.

    Home Assistant's current NINA integration intentionally keeps only the
    warning id on the binary sensor and exposes long description/recommended
    actions through ``nina.get_details``. Caching by warning id avoids service
    calls on every room/sensor refresh.
    """
    source = entry.data.get(CONF_WARNING_SOURCE)
    if not isinstance(source, str) or not source or source == WARNING_SOURCE_NONE:
        return
    source_entry = hass.config_entries.async_get_entry(source)
    if source_entry is None or source_entry.domain != "nina":
        return
    if not hass.services.has_service("nina", "get_details"):
        return

    entity_ids = _config_entry_entities(hass, source_entry.entry_id)
    active: dict[str, str] = {}
    for entity_id in entity_ids:
        if not entity_id.startswith("binary_sensor."):
            continue
        state = hass.states.get(entity_id)
        if state is None or state.state != "on":
            continue
        warning_id = str(state.attributes.get("id") or "").strip()
        if warning_id:
            active[entity_id] = warning_id

    bucket = _nina_details_bucket(hass)
    prefix = f"{entry.entry_id}:"
    active_keys = {f"{prefix}{entity_id}" for entity_id in active}
    for key in [key for key in bucket if key.startswith(prefix) and key not in active_keys]:
        bucket.pop(key, None)

    for entity_id, warning_id in active.items():
        key = f"{prefix}{entity_id}"
        cached = bucket.get(key)
        if isinstance(cached, dict) and cached.get("warning_id") == warning_id:
            continue
        try:
            response = await hass.services.async_call(
                "nina",
                "get_details",
                {},
                target={"entity_id": entity_id},
                blocking=True,
                return_response=True,
            )
        except Exception:  # noqa: BLE001 - provider failure must never break advice
            _LOGGER.debug("Unable to fetch NINA details for %s", entity_id, exc_info=True)
            continue
        details = response.get(entity_id) if isinstance(response, dict) else None
        if isinstance(details, dict):
            bucket[key] = {"warning_id": warning_id, "details": dict(details)}


@callback
def async_clear_nina_details_cache(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop the small per-advisor NINA detail cache on unload."""
    bucket = _nina_details_bucket(hass)
    prefix = f"{entry.entry_id}:"
    for key in [key for key in bucket if key.startswith(prefix)]:
        bucket.pop(key, None)


def _cached_nina_details(hass: HomeAssistant, entry: ConfigEntry, entity_id: str) -> dict[str, Any]:
    cached = _nina_details_bucket(hass).get(f"{entry.entry_id}:{entity_id}")
    details = cached.get("details") if isinstance(cached, dict) else None
    return dict(details) if isinstance(details, dict) else {}


def _nina_slot_sensor_values(
    hass: HomeAssistant,
    entity_ids: list[str],
) -> dict[str, dict[str, str]]:
    """Collect NINA's newer per-slot detail sensor values.

    NINA is moving warning details away from binary-sensor attributes. Home
    Assistant currently exposes headline and severity as dedicated sensors whose
    unique IDs extend the warning binary sensor's unique ID. Keeping this small
    lookup means the advisor keeps classifying warnings after those legacy
    attributes disappear.
    """
    sensor_ids = [entity_id for entity_id in entity_ids if entity_id.startswith("sensor.")]
    if not sensor_ids:
        return {}

    registry = _optional_entity_registry(hass)
    if registry is None:
        return {}

    details: dict[str, dict[str, str]] = {}
    for entity_id in sensor_ids:
        registry_entry = registry.async_get(entity_id)
        unique_id = registry_entry.unique_id if registry_entry else None
        if not isinstance(unique_id, str):
            continue
        state = hass.states.get(entity_id)
        if state is None or state.state in {"unknown", "unavailable", "none", ""}:
            continue
        for field in ("headline", "severity"):
            suffix = f"-{field}"
            if unique_id.endswith(suffix):
                slot_id = unique_id[: -len(suffix)]
                details.setdefault(slot_id, {})[field] = str(state.state)
                break
    return details

def _evaluate_nina_like_entities(
    hass: HomeAssistant,
    entry: ConfigEntry | list[str],
    entity_ids: list[str] | None = None,
) -> WarningAssessment:
    # Keep the older two-argument helper shape for focused unit tests and for
    # third-party callers. Full NINA detail caching is available only when the
    # owning Lüftungsberater ConfigEntry is supplied.
    advisor_entry: ConfigEntry | None
    if entity_ids is None:
        entity_ids = list(entry) if isinstance(entry, list) else []
        advisor_entry = None
    else:
        advisor_entry = entry if not isinstance(entry, list) else None

    result = WarningAssessment()
    air_rank = {"none": 0, "clear": 1, "caution": 2, "danger": 3}
    slot_details = _nina_slot_sensor_values(hass, entity_ids)
    registry = _optional_entity_registry(hass) if slot_details else None

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state is None:
            continue

        if not entity_id.startswith("binary_sensor.") or state.state != "on":
            continue

        warning_id = state.attributes.get("id") or state.attributes.get("identifier")
        if warning_id:
            result.warning_ids.add(str(warning_id))
        else:
            # Stable fallback for providers without an explicit warning id.
            result.warning_ids.add(entity_id)

        registry_entry = registry.async_get(entity_id) if registry is not None else None
        slot_id = registry_entry.unique_id if registry_entry else None
        detail = slot_details.get(slot_id, {}) if isinstance(slot_id, str) else {}

        full = _cached_nina_details(hass, advisor_entry, entity_id) if advisor_entry is not None else {}
        headline = _text(state, "headline") or detail.get("headline", "") or str(full.get("headline") or "")
        description = _text(state, "description") or str(full.get("description") or "")
        actions = " ".join(
            part
            for part in (
                _text(state, "recommended_actions"),
                _text(state, "recommended_action"),
                _text(state, "instruction"),
                _text(state, "instructions"),
                _text(state, "recommendation"),
                _text(state, "recommendations"),
                _text(state, "advice"),
                str(full.get("recommended_actions") or ""),
                str(full.get("recommended_action") or ""),
                str(full.get("instruction") or ""),
                str(full.get("instructions") or ""),
                str(full.get("recommendation") or ""),
                str(full.get("recommendations") or ""),
                str(full.get("advice") or ""),
            )
            if part
        )
        severity = _text(state, "severity") or detail.get("severity", "") or str(full.get("severity") or "") or "Unknown"
        alltext = " ".join((headline, description, actions))

        air_state = _evaluate_air_warning(
            headline,
            description,
            actions,
            severity,
        )

        if air_state == "danger":
            result.official_close_instruction = True
        elif air_state == "clear":
            # Keep the all-clear visible while the provider still exposes the
            # warning slot. Once the slot disappears/goes off, normal engine
            # operation resumes with no artificial after-run. Explicit close
            # instructions were checked first and can therefore never be
            # accidentally neutralised by the word "Entwarnung" in the same
            # payload.
            if result.nina_status != "danger":
                result.nina_status = "clear"
                result.warning_notice_kind = "all_clear"
                result.warning_notice_text = headline or description or actions or None
            continue

        # Non-DWD warning providers are not reinterpreted by event type or CAP
        # severity. Only their explicit protection instructions below may alter
        # ventilation. DWD keeps its dedicated official warning-level path.

        if air_rank[air_state] > air_rank[result.nina_status]:
            result.nina_status = air_state
            result.nina_reason_key = (
                "official_close_instruction"
                if air_state == "danger"
                else _air_reason_key(alltext, air_state)
            )
            result.nina_original_reason = headline or description or actions or None

    return result


def _evaluate_dwd_warning_entities(
    hass: HomeAssistant,
    entity_ids: list[str],
) -> WarningAssessment:
    """Evaluate DWD Weather Warnings sensor(s)."""
    result = WarningAssessment()

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state is None:
            continue

        count = int(_float(state.attributes.get("warning_count")) or 0)
        if count <= 0:
            continue

        low_id = entity_id.lower()
        is_advance = (
            "advance" in low_id
            or "vorwarn" in low_id
            or "prewarning" in low_id
        )
        sensor_level = _state_float(state) or 0.0

        for index in range(1, count + 1):
            warning_id = (
                state.attributes.get(f"warning_{index}_identifier")
                or state.attributes.get(f"warning_{index}_id")
                or state.attributes.get(f"warning_{index}_event_id")
                or state.attributes.get(f"warning_{index}_sent")
            )
            result.warning_ids.add(str(warning_id) if warning_id else f"{entity_id}:{index}")
            name = str(
                state.attributes.get(f"warning_{index}_name", "")
                or ""
            )
            headline = str(
                state.attributes.get(f"warning_{index}_headline", "")
                or ""
            )
            instruction = str(
                state.attributes.get(f"warning_{index}_instruction", "") or ""
            )
            description = str(
                state.attributes.get(f"warning_{index}_description", "") or ""
            )
            text = f"{name} {headline} {description} {instruction}"

            # If DWD itself gives a window/ventilation protection instruction,
            # that instruction is authoritative regardless of the numeric level.
            if _contains_any(instruction, OFFICIAL_CLOSE_ACTIONS):
                result.official_close_instruction = True
                result.weather_danger = True
                result.weather_caution = False
                if result.weather_reason_key is None:
                    result.weather_reason_key = "official_close_instruction"
                    result.weather_original_reason = headline or instruction or name or None
                continue

            if not _contains_any(text, WEATHER_WARNING_WORDS):
                continue

            # DWD exposes a level for every individual warning. Prefer that
            # over the sensor state (which is only the highest active level),
            # otherwise an unrelated level-3 warning could incorrectly turn a
            # level-2 Starkregen warning red.
            warning_level = _float(
                state.attributes.get(f"warning_{index}_level")
            )
            level = warning_level if warning_level is not None else sensor_level

            reason = headline or name
            if not is_advance and level >= 3:
                result.weather_danger = True
                result.weather_caution = False
                if result.weather_reason_key is None:
                    result.weather_reason_key = _weather_reason_key(text, True)
                    result.weather_reason_args = {"warning_level": level}
                    result.weather_original_reason = reason or None
            elif not result.weather_danger:
                # DWD level 1/2 and advance information are advisory for
                # ventilation. Level 3/4 are actual severe-weather warnings.
                result.weather_caution = True
                if result.weather_reason_key is None:
                    result.weather_reason_key = _weather_reason_key(text, False)
                    result.weather_reason_args = {"warning_level": level}
                    result.weather_original_reason = reason or None

    return result


def warning_assessment(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> WarningAssessment:
    """Normalize the selected warning integration."""
    source = entry.data.get(CONF_WARNING_SOURCE)

    if (
        not isinstance(source, str)
        or not source
        or source == WARNING_SOURCE_NONE
    ):
        return WarningAssessment()

    source_entry = hass.config_entries.async_get_entry(source)
    if source_entry is None:
        return WarningAssessment()

    entity_ids = _config_entry_entities(hass, source_entry.entry_id)

    result = WarningAssessment(
        source_entities=set(entity_ids),
        provider_domain=source_entry.domain,
    )

    if source_entry.domain == "dwd_weather_warnings":
        assessed = _evaluate_dwd_warning_entities(hass, entity_ids)
    else:
        # Generic warning integrations are action-driven. Do not reinterpret a
        # foreign provider's event type/severity as DWD weather semantics. If an
        # authority tells the user to close windows or stop ventilation, the
        # instruction is authoritative; otherwise the warning does not override
        # the ventilation engine.
        assessed = _evaluate_nina_like_entities(hass, entry, entity_ids)

    result.weather_caution = assessed.weather_caution and not assessed.weather_danger
    result.weather_danger = assessed.weather_danger
    result.weather_reason_key = assessed.weather_reason_key
    result.weather_reason_args = dict(assessed.weather_reason_args)
    result.weather_original_reason = assessed.weather_original_reason
    result.nina_status = assessed.nina_status
    result.nina_reason_key = assessed.nina_reason_key
    result.nina_reason_args = dict(assessed.nina_reason_args)
    result.nina_original_reason = assessed.nina_original_reason
    result.warning_notice_kind = assessed.warning_notice_kind
    result.warning_notice_text = assessed.warning_notice_text
    result.official_close_instruction = assessed.official_close_instruction
    result.warning_ids = set(assessed.warning_ids)
    return result

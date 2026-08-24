"""Provider adapters for weather, radar and warning integrations."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    CONF_MANUAL_OUTDOOR,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMP,
    CONF_WARNING_SOURCE,
    CONF_WEATHER,
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

AIR_WORDS = (
    "brandrauch",
    "rauchentwicklung",
    "rauchgas",
    "rauchwolke",
    "rauchbelastung",
    "ausbreitung von rauch",
    "ausbreitung von brandrauch",
    "gefahrstoff",
    "schadstoff",
    "luftverunreinigung",
    "gasaustritt",
    "gaswolke",
    "chemieunfall",
    "chemikal",
    "giftige dämpfe",
    "giftige daempfe",
    "toxisch",
    "reizgas",
    "smoke",
    "hazardous substance",
    "toxic",
    "gas leak",
)

NO_DANGER_WORDS = (
    "keine gesundheitsgefahr",
    "keine gesundheitliche gefahr",
    "keine gefahr für die gesundheit",
    "keine gefahr fuer die gesundheit",
    "es besteht keine gefahr",
    "keine gefährdung",
    "keine gefaehrdung",
    "no health risk",
    "no danger",
)

CLEAR_WORDS = (
    "entwarnung",
    "warnung ist aufgehoben",
    "warnung wurde aufgehoben",
    "die warnung ist aufgehoben",
    "all-clear",
    "warning has been lifted",
)

PRECAUTION_WORDS = (
    "vorsorglich fenster",
    "vorsorglich die fenster",
    "vorsorglich türen",
    "vorsorglich tueren",
    "close windows as a precaution",
)

HARD_CLOSE_WORDS = (
    "fenster und türen geschlossen halten",
    "fenster und tueren geschlossen halten",
    "halten sie fenster und türen geschlossen",
    "halten sie fenster und tueren geschlossen",
    "fenster geschlossen halten",
    "keep windows and doors closed",
    "keep windows closed",
)

SEVERITY_DANGER = {"severe", "extreme"}


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
    source_entities: set[str] = field(default_factory=set)
    provider_domain: str | None = None


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
    if condition in WEATHER_DANGER_CONDITIONS or wind >= 50 or gust >= 65:
        result.weather_danger = True
        result.weather_caution = False

        if condition in {"lightning", "lightning-rainy"}:
            result.weather_reason_key = "weather_thunderstorm_danger"
        elif condition == "hail":
            result.weather_reason_key = "weather_hail_danger"
        elif condition == "exceptional":
            result.weather_reason_key = "weather_exceptional_danger"
        elif gust >= 65:
            result.weather_reason_key = "weather_wind_danger"
            result.weather_reason_args = {"speed_kmh": gust}
        elif wind >= 50:
            result.weather_reason_key = "weather_wind_danger"
            result.weather_reason_args = {"speed_kmh": wind}
    elif wind >= 39 or gust >= 50:
        result.weather_caution = True
        speed = gust if gust >= 50 else wind
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
    return _contains_any(text, CLEAR_WORDS)


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
    """Return none/caution/danger for an environmental-air warning."""
    alltext = " ".join((headline, description, actions)).lower()

    if _is_clear_warning(alltext):
        return "none"

    air = _contains_any(alltext, AIR_WORDS)
    if not air:
        return "none"

    no_danger = _contains_any(alltext, NO_DANGER_WORDS)
    precaution = _contains_any(actions, PRECAUTION_WORDS)
    hard_close = _contains_any(actions, HARD_CLOSE_WORDS)
    severity_low = severity.lower()

    if no_danger:
        # A warning text explicitly saying that there is no danger must not be
        # kept yellow merely because it also mentions smoke/fire. Only an actual
        # precautionary/close-windows instruction still warrants caution.
        return "caution" if (precaution or hard_close) else "none"

    if (
        severity_low in SEVERITY_DANGER
        or (hard_close and not precaution)
        or "gesundheitsgefahr" in alltext
        or "gesundheitliche gefahr" in alltext
        or "giftig" in alltext
        or "toxisch" in alltext
    ):
        return "danger"

    return "caution"



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
    entity_ids: list[str],
) -> WarningAssessment:
    result = WarningAssessment()
    air_rank = {"none": 0, "caution": 1, "danger": 2}
    slot_details = _nina_slot_sensor_values(hass, entity_ids)
    registry = _optional_entity_registry(hass) if slot_details else None

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state is None:
            continue

        if not entity_id.startswith("binary_sensor.") or state.state != "on":
            continue

        registry_entry = registry.async_get(entity_id) if registry is not None else None
        slot_id = registry_entry.unique_id if registry_entry else None
        detail = slot_details.get(slot_id, {}) if isinstance(slot_id, str) else {}

        headline = _text(state, "headline") or detail.get("headline", "")
        description = _text(state, "description")
        actions = (
            _text(state, "recommended_actions")
            or _text(state, "instruction")
        )
        severity = _text(state, "severity") or detail.get("severity", "") or "Unknown"
        alltext = " ".join((headline, description, actions))

        if _is_clear_warning(alltext):
            continue

        if _contains_any(alltext, WEATHER_WARNING_WORDS):
            severity_low = severity.lower()
            reason = headline or description
            if severity_low in {"severe", "extreme"}:
                result.weather_danger = True
                result.weather_caution = False
                if result.weather_reason_key is None:
                    result.weather_reason_key = _weather_reason_key(alltext, True)
                    result.weather_original_reason = reason or None
            elif not result.weather_danger:
                # Moderate, minor or providers without a usable CAP severity are
                # treated as caution. This prevents ordinary/markant rain
                # warnings from turning the whole advisor red.
                result.weather_caution = True
                if result.weather_reason_key is None:
                    result.weather_reason_key = _weather_reason_key(alltext, False)
                    result.weather_original_reason = reason or None

        air_state = _evaluate_air_warning(
            headline,
            description,
            actions,
            severity,
        )

        if air_rank[air_state] > air_rank[result.nina_status]:
            result.nina_status = air_state
            result.nina_reason_key = _air_reason_key(alltext, air_state)
            result.nina_original_reason = headline or description or None

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
            name = str(
                state.attributes.get(f"warning_{index}_name", "")
                or ""
            )
            headline = str(
                state.attributes.get(f"warning_{index}_headline", "")
                or ""
            )
            text = f"{name} {headline}"

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
        assessed = _evaluate_nina_like_entities(hass, entity_ids)
        dwd_like = _evaluate_dwd_warning_entities(hass, entity_ids)

        if dwd_like.weather_danger:
            assessed.weather_danger = True
            assessed.weather_caution = False
            if assessed.weather_reason_key is None:
                assessed.weather_reason_key = dwd_like.weather_reason_key
                assessed.weather_reason_args = dict(dwd_like.weather_reason_args)
                assessed.weather_original_reason = dwd_like.weather_original_reason
        elif dwd_like.weather_caution and not assessed.weather_danger:
            assessed.weather_caution = True
            if assessed.weather_reason_key is None:
                assessed.weather_reason_key = dwd_like.weather_reason_key
                assessed.weather_reason_args = dict(dwd_like.weather_reason_args)
                assessed.weather_original_reason = dwd_like.weather_original_reason

    result.weather_caution = assessed.weather_caution and not assessed.weather_danger
    result.weather_danger = assessed.weather_danger
    result.weather_reason_key = assessed.weather_reason_key
    result.weather_reason_args = dict(assessed.weather_reason_args)
    result.weather_original_reason = assessed.weather_original_reason
    result.nina_status = assessed.nina_status
    result.nina_reason_key = assessed.nina_reason_key
    result.nina_reason_args = dict(assessed.nina_reason_args)
    result.nina_original_reason = assessed.nina_original_reason
    return result

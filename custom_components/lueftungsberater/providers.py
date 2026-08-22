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
    "pouring",
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

SEVERITY_DANGER = {"moderate", "severe", "extreme"}


@dataclass(slots=True)
class WeatherAssessment:
    """Normalized data from the selected weather provider."""

    temperature: float | None = None
    humidity: float | None = None
    rain_now: bool = False
    rain_soon: bool = False
    weather_danger: bool = False
    weather_reason: str | None = None
    source_entities: set[str] = field(default_factory=set)
    source_temperature: str | None = None
    source_humidity: str | None = None
    provider_domain: str | None = None
    radar_current_entity: str | None = None
    radar_next_entity: str | None = None


@dataclass(slots=True)
class WarningAssessment:
    """Normalized data from the selected warning provider."""

    weather_danger: bool = False
    weather_reason: str | None = None
    nina_status: str = "none"
    nina_reason: str | None = None
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
        result.temperature = _state_float(
            hass.states.get(temp_override) if temp_override else None
        )
        result.humidity = _state_float(
            hass.states.get(humidity_override) if humidity_override else None
        )
        if temp_override:
            result.source_entities.add(temp_override)
            result.source_temperature = temp_override
        if humidity_override:
            result.source_entities.add(humidity_override)
            result.source_humidity = humidity_override
        return result

    state = hass.states.get(weather_entity_id)
    result.source_entities.add(weather_entity_id)
    result.provider_domain = _provider_domain_for_entity(
        hass,
        weather_entity_id,
    )

    temp_override = _manual_override(entry, CONF_OUTDOOR_TEMP)
    humidity_override = _manual_override(entry, CONF_OUTDOOR_HUMIDITY)

    if temp_override:
        result.temperature = _state_float(hass.states.get(temp_override))
        result.source_temperature = temp_override
        result.source_entities.add(temp_override)
    elif state is not None:
        result.temperature = _float(state.attributes.get("temperature"))
        result.source_temperature = weather_entity_id

    if humidity_override:
        result.humidity = _state_float(hass.states.get(humidity_override))
        result.source_humidity = humidity_override
        result.source_entities.add(humidity_override)
    elif state is not None:
        result.humidity = _float(state.attributes.get("humidity"))
        result.source_humidity = weather_entity_id

    if state is None:
        return result

    condition = state.state
    result.rain_now = condition in RAIN_CONDITIONS

    wind_unit = state.attributes.get("wind_speed_unit")
    wind = _wind_to_kmh(state.attributes.get("wind_speed"), wind_unit)
    gust = _wind_to_kmh(state.attributes.get("wind_gust_speed"), wind_unit)

    if (
        condition in WEATHER_DANGER_CONDITIONS
        or wind >= 50
        or gust >= 65
    ):
        result.weather_danger = True

        if condition == "lightning":
            result.weather_reason = "Gewitter"
        elif condition == "lightning-rainy":
            result.weather_reason = "Gewitter mit Regen"
        elif condition == "hail":
            result.weather_reason = "Hagel"
        elif condition == "pouring":
            result.weather_reason = "Starker Regen"
        elif condition == "exceptional":
            result.weather_reason = "Außergewöhnliche Wetterlage"
        elif gust >= 65:
            result.weather_reason = f"Starke Windböen ({gust:.0f} km/h)"
        elif wind >= 50:
            result.weather_reason = f"Starker Wind ({wind:.0f} km/h)"

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
            if now <= next_dt <= now + timedelta(hours=2):
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
        return "caution" if (precaution or air) else "none"

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


def _evaluate_nina_like_entities(
    hass: HomeAssistant,
    entity_ids: list[str],
) -> WarningAssessment:
    result = WarningAssessment()
    air_rank = {"none": 0, "caution": 1, "danger": 2}

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state is None:
            continue

        if not entity_id.startswith("binary_sensor.") or state.state != "on":
            continue

        headline = _text(state, "headline")
        description = _text(state, "description")
        actions = (
            _text(state, "recommended_actions")
            or _text(state, "instruction")
        )
        severity = _text(state, "severity") or "Unknown"
        alltext = " ".join((headline, description, actions))

        if _is_clear_warning(alltext):
            continue

        if _contains_any(alltext, WEATHER_WARNING_WORDS):
            if severity.lower() in SEVERITY_DANGER:
                result.weather_danger = True
                if result.weather_reason is None:
                    result.weather_reason = headline or description

        air_state = _evaluate_air_warning(
            headline,
            description,
            actions,
            severity,
        )

        if air_rank[air_state] > air_rank[result.nina_status]:
            result.nina_status = air_state
            result.nina_reason = headline or description

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
        level = _state_float(state) or 0.0

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

            if not is_advance and level >= 2:
                result.weather_danger = True
                if result.weather_reason is None:
                    result.weather_reason = headline or name

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
            assessed.weather_reason = (
                assessed.weather_reason
                or dwd_like.weather_reason
            )

    result.weather_danger = assessed.weather_danger
    result.weather_reason = assessed.weather_reason
    result.nina_status = assessed.nina_status
    result.nina_reason = assessed.nina_reason
    return result

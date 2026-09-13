"""Normalization helpers for optional indoor/outdoor air-quality sensors."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

SENSOR_MAX_AGE = timedelta(minutes=30)

# Same absolute particulate bands as the provider-side UBA LQI mapping.
PM_LIMITS = {
    "pm2_5": (5.0, 15.0, 30.0, 50.0),
    "pm10": (9.0, 27.0, 54.0, 90.0),
    "o3": (24.0, 72.0, 144.0, 240.0),
    # Same O₃ bands expressed in ppb. At 20 °C / 1013 hPa, 1 ppb O₃ is
    # approximately 2.0 µg/m³, so keeping a separate parts scale avoids
    # pretending the live sensor was measured as a mass concentration.
    "o3_parts": (12.0, 36.0, 72.0, 120.0),
    "no2": (10.0, 30.0, 60.0, 100.0),
    # Same NO₂ bands expressed directly in ppb (rounded room-air equivalents).
    # This avoids pretending ppm/ppb is a mass concentration while still making
    # a substance-specific physical NO₂ reading useful immediately.
    "no2_parts": (5.0, 16.0, 32.0, 53.0),
}
# Formaldehyde is normalized to mg/m³. The 0.1 mg/m³ band is the established
# short-term reference point; lower/higher bands are product-side presentation
# bands so one noisy sample does not jump directly from good to severe.
HCHO_LIMITS = (0.03, 0.05, 0.10, 0.20)

# Generic TVOC mass concentration is not a single-substance health metric. These
# bands are therefore deliberately used as hygienic / ventilation-oriented
# orientation only. They follow the long-established German TVOC staging, with
# the current AIR 950 µg/m³ reference value used for the second boundary.
VOC_MASS_LIMITS = (300.0, 950.0, 3000.0, 10000.0)  # µg/m³

PHYSICAL_MASS_UNITS = {"µg/m3", "ug/m3", "mg/m3"}
PHYSICAL_PART_UNITS = {"ppm", "ppb"}
RAW_DEVICE_CLASSES = {
    "volatile_organic_compounds",
    "volatile_organic_compounds_parts",
    "nitrogen_dioxide",
    "ozone",
}

QUALITY_RANK = {
    "unknown": -1,
    "very_good": 0,
    "good": 1,
    "moderate": 2,
    "poor": 3,
    "very_poor": 4,
}


@dataclass(slots=True)
class AirReading:
    value: float | None = None
    unit: str | None = None
    source: str | None = None
    fresh: bool = False
    measurement_type: str = "unknown"  # mass | parts | index | unknown
    pollutant_key: str | None = None


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def state_is_fresh(state: State | None, *, max_age: timedelta = SENSOR_MAX_AGE) -> bool:
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return False
    stamp = getattr(state, "last_reported", None) or getattr(state, "last_updated", None)
    if not isinstance(stamp, datetime):
        return True
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt_util.UTC)
    age = dt_util.utcnow() - stamp
    return timedelta(0) <= age <= max_age


def state_number(
    hass: HomeAssistant,
    entity_id: str | None,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    max_age: timedelta = SENSOR_MAX_AGE,
) -> AirReading:
    if not entity_id:
        return AirReading(source=entity_id)
    state = hass.states.get(entity_id)
    if not state_is_fresh(state, max_age=max_age):
        return AirReading(source=entity_id)
    value = _finite(state.state)
    if value is None:
        return AirReading(source=entity_id)
    if minimum is not None and value < minimum:
        return AirReading(source=entity_id)
    if maximum is not None and value > maximum:
        return AirReading(source=entity_id)
    return AirReading(
        value=value,
        unit=str(state.attributes.get("unit_of_measurement") or "") or None,
        source=entity_id,
        fresh=True,
    )



def _normalized_unit(value: str | None) -> str:
    return str(value or "").strip().lower().replace("μ", "µ").replace("³", "3")


def _device_class(state: State | None) -> str:
    if state is None:
        return ""
    value = state.attributes.get("device_class")
    return str(value or "").strip().lower()


def pollutant_reading(
    hass: HomeAssistant,
    entity_id: str | None,
    *,
    pollutant: str,
) -> AirReading:
    """Read VOC/NO₂/O₃ without crossing physical/index measurement scales.

    The sensor's unit is authoritative. Safe unit conversions are performed
    only within the same physical dimension (mg/m³ -> µg/m³ and ppm -> ppb).
    Unitless numeric values are treated as vendor indices unless the entity's
    device_class explicitly says it should be a physical concentration. In that
    malformed case the value is rejected rather than guessed.
    """
    if pollutant not in {"voc", "no2", "o3"}:
        raise ValueError(f"Unsupported pollutant: {pollutant}")
    raw = state_number(hass, entity_id, minimum=0.0, maximum=5_000_000.0)
    if raw.value is None:
        return raw
    state = hass.states.get(entity_id) if entity_id else None
    unit = _normalized_unit(raw.unit)
    device_class = _device_class(state)

    if unit in PHYSICAL_MASS_UNITS:
        value = raw.value * 1000.0 if unit == "mg/m3" else raw.value
        if not 0.0 <= value <= 50000.0:
            return AirReading(source=entity_id)
        return AirReading(
            value=value, unit="µg/m³", source=entity_id, fresh=True,
            measurement_type="mass", pollutant_key=pollutant,
        )

    if unit in PHYSICAL_PART_UNITS:
        value = raw.value * 1000.0 if unit == "ppm" else raw.value
        if not 0.0 <= value <= 5_000_000.0:
            return AirReading(source=entity_id)
        return AirReading(
            value=value, unit="ppb", source=entity_id, fresh=True,
            measurement_type="parts", pollutant_key=f"{pollutant}_parts",
        )

    # Ozone is always a physical gas measurement in this integration. A
    # unitless O₃ value is ambiguous and must never be guessed into an index.
    if pollutant == "o3":
        return AirReading(source=entity_id)

    # A supported physical device class without a usable physical unit is
    # malformed/incomplete. Do not silently reinterpret it as a vendor index.
    if device_class in RAW_DEVICE_CLASSES:
        return AirReading(source=entity_id)

    # Unitless (or explicitly index-like) numeric values are vendor indices.
    # Unknown foreign units are rejected so e.g. percentages are not mistaken
    # for an air-quality index.
    if unit not in {"", "index", "aqi"}:
        return AirReading(source=entity_id)
    return AirReading(
        value=raw.value, unit=None, source=entity_id, fresh=True,
        measurement_type="index", pollutant_key=f"{pollutant}_index",
    )

def concentration_ugm3(hass: HomeAssistant, entity_id: str | None) -> AirReading:
    raw = state_number(hass, entity_id, minimum=0.0, maximum=5_000_000.0)
    if raw.value is None:
        return raw
    unit = str(raw.unit or "").lower().replace("μ", "µ").replace("³", "3")
    if unit in {"µg/m3", "ug/m3"}:
        value = raw.value
    elif unit in {"mg/m3"}:
        value = raw.value * 1000.0
    else:
        return AirReading(source=entity_id)
    if not 0.0 <= value <= 5000.0:
        return AirReading(source=entity_id)
    return AirReading(value=value, unit="µg/m³", source=entity_id, fresh=True)


def formaldehyde_mgm3(hass: HomeAssistant, entity_id: str | None) -> AirReading:
    raw = state_number(hass, entity_id, minimum=0.0, maximum=5_000_000.0)
    if raw.value is None:
        return raw
    unit = str(raw.unit or "").lower().replace("μ", "µ").replace("³", "3")
    if unit in {"mg/m3"}:
        value = raw.value
    elif unit in {"µg/m3", "ug/m3"}:
        value = raw.value / 1000.0
    else:
        return AirReading(source=entity_id)
    if not 0.0 <= value <= 10.0:
        return AirReading(source=entity_id)
    return AirReading(value=value, unit="mg/m³", source=entity_id, fresh=True)


def relative_index(hass: HomeAssistant, entity_id: str | None) -> AirReading:
    """Read a vendor-specific numeric index without pretending it has a unit.

    Physical concentration units are intentionally rejected here. A value in
    µg/m³, mg/m³, ppm or ppb needs its own scientifically meaningful handling
    and must never silently be treated as a vendor index.
    """
    raw = state_number(hass, entity_id, minimum=0.0, maximum=1_000_000.0)
    if raw.value is None:
        return raw
    unit = str(raw.unit or "").lower().replace("μ", "µ").replace("³", "3")
    if unit in {"µg/m3", "ug/m3", "mg/m3", "ppm", "ppb"}:
        return AirReading(source=entity_id)
    return AirReading(value=raw.value, unit=raw.unit, source=entity_id, fresh=True)


def classify_absolute(kind: str, value: float | None) -> str:
    if value is None:
        return "unknown"
    if kind == "formaldehyde":
        limits = HCHO_LIMITS
    elif kind == "voc":
        limits = VOC_MASS_LIMITS
    else:
        limits = PM_LIMITS.get(kind)
    if limits is None:
        return "unknown"
    if value <= limits[0]:
        return "very_good"
    if value <= limits[1]:
        return "good"
    if value <= limits[2]:
        return "moderate"
    if value <= limits[3]:
        return "poor"
    return "very_poor"


def worst_quality(items: dict[str, tuple[str, float]]) -> tuple[str, str | None, float | None]:
    worst = "unknown"
    worst_kind = None
    worst_value = None
    for kind, (quality, value) in items.items():
        if QUALITY_RANK.get(quality, -1) > QUALITY_RANK.get(worst, -1):
            worst, worst_kind, worst_value = quality, kind, value
    return worst, worst_kind, worst_value


def classify_relative_context(
    current: float | None,
    *,
    baseline: float | None,
    unusual: bool,
    trend: str,
    samples: int,
) -> str:
    """Classify only relative change; never invent a universal vendor threshold."""
    if current is None or baseline is None or samples < 24:
        return "unknown"
    ratio = current / baseline if baseline > 0 else None
    if unusual and ratio is not None and ratio >= 2.0:
        return "very_poor"
    if unusual and ratio is not None and ratio >= 1.5:
        return "poor"
    if unusual or trend == "rising":
        return "moderate"
    return "good"

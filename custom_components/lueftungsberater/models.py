"""Pure data models for the ventilation engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RoomInput:
    indoor_temp: float
    indoor_humidity: float
    outdoor_temp: float
    outdoor_humidity: float
    target_temp: float = 21.0
    co2: float | None = None
    window_open: bool = False
    hours_since_airing: float | None = None
    rain_now: bool = False
    rain_soon: bool = False
    weather_caution: bool = False
    weather_danger: bool = False
    weather_reason_key: str | None = None
    weather_reason_args: dict[str, Any] = field(default_factory=dict)
    weather_original_reason: str | None = None
    nina_status: str = "none"  # none | caution | danger
    nina_reason_key: str | None = None
    nina_reason_args: dict[str, Any] = field(default_factory=dict)
    nina_original_reason: str | None = None
    surface_temp: float | None = None
    previous_mode: str | None = None


@dataclass(slots=True)
class VentilationResult:
    color: str
    mode: str
    recommendation_key: str
    reason_key: str
    reason_args: dict[str, Any]
    duration_key: str
    duration_args: dict[str, Any]
    original_reason: str | None
    indoor_absolute_humidity: float
    outdoor_absolute_humidity: float
    absolute_humidity_difference: float
    co2_status: str
    surface_relative_humidity: float | None = None
    mold_risk: bool = False

"""Pure data models for the ventilation engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


NinaStatus = Literal["none", "caution", "danger", "clear"]


@dataclass(slots=True)
class RoomInput:
    indoor_temp: float
    indoor_humidity: float
    outdoor_temp: float
    outdoor_humidity: float
    target_temp: float = 21.0
    co2: float | None = None
    outdoor_co2: float | None = None
    window_open: bool = False
    open_minutes: float | None = None
    hours_since_airing: float | None = None
    rain_now: bool = False
    rain_soon: bool = False
    rain_minutes_until: float | None = None
    weather_caution: bool = False
    weather_danger: bool = False
    weather_reason_key: str | None = None
    weather_reason_args: dict[str, Any] = field(default_factory=dict)
    weather_original_reason: str | None = None
    short_term_weather_change: str | None = None
    short_term_weather_kind: str | None = None
    short_term_weather_minutes: float | None = None
    short_term_weather_condition: str | None = None
    nina_status: NinaStatus = "none"
    nina_reason_key: str | None = None
    nina_reason_args: dict[str, Any] = field(default_factory=dict)
    nina_original_reason: str | None = None
    surface_temp: float | None = None
    mold_current_critical_minutes: float | None = None
    mold_critical_minutes_24h: float | None = None
    mold_persistent: bool = False
    air_quality: str = "unknown"
    air_quality_pollutant: str | None = None
    air_quality_value: float | None = None
    air_quality_baseline_value: float | None = None
    air_quality_typical: bool | None = None
    air_quality_unusual: bool = False
    air_quality_trend: str = "unknown"
    air_quality_history_samples: int = 0
    previous_mode: str | None = None
    previous_need: str | None = None
    co2_pending_hold: bool = False
    co2_airing_active: bool = False
    co2_finish_ready: bool = False
    co2_finish_target: float | None = None
    co2_near_target: float | None = None
    co2_rearm_threshold: float | None = None
    co2_minimum_airing_active: bool = False
    co2_minimum_airing_cautious: bool = False


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
    co2_session_target: float | None = None
    co2_session_need: str | None = None
    room_status_color: str = "green"
    room_recommendation_key: str = "room_good"
    room_reason_key: str = "room_perspective"
    room_reason_args: dict[str, Any] = field(default_factory=dict)
    primary_need: str = "none"
    decision_need: str = "none"
    safety_lock: bool = False
    surface_relative_humidity: float | None = None
    mold_risk: bool = False
    mold_persistent: bool = False
    mold_current_critical_minutes: float | None = None
    mold_critical_minutes_24h: float | None = None
    air_quality: str = "unknown"
    air_quality_pollutant: str | None = None
    air_quality_value: float | None = None
    outdoor_co2: float | None = None
    co2_difference: float | None = None
    air_quality_baseline_value: float | None = None
    air_quality_typical: bool | None = None
    air_quality_unusual: bool = False
    air_quality_trend: str = "unknown"
    air_quality_history_samples: int = 0

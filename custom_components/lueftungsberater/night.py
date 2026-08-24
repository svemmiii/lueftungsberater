"""Best-effort overnight ventilation advice from hourly weather forecasts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import median
from typing import Any

from .engine import AH_NEUTRAL, absolute_humidity

# The feature is deliberately an evening planning hint, not a command to leave
# a window unattended all night. Fine tuning can happen independently later.
NIGHT_ADVICE_START_HOUR = 22
NIGHT_ADVICE_END_HOUR = 1
NIGHT_WINDOW_END_HOUR = 7

_RAINY_CONDITIONS = {
    "rainy",
    "pouring",
    "lightning",
    "lightning-rainy",
    "hail",
    "snowy-rainy",
}


@dataclass(slots=True)
class NightAdvice:
    """Compact status shown as an optional extra line on the room card."""

    status: str = "unavailable"  # recommended | conditional | not_recommended | unavailable
    reason_key: str | None = None
    reason_args: dict[str, Any] = field(default_factory=dict)


def _is_evening(now: datetime) -> bool:
    return now.hour >= NIGHT_ADVICE_START_HOUR or now.hour < NIGHT_ADVICE_END_HOUR


def _night_end(now: datetime) -> datetime:
    # If it is already after midnight, the relevant end is this morning at 07:00.
    # Otherwise use the following morning.
    if now.hour < NIGHT_ADVICE_END_HOUR:
        return now.replace(hour=NIGHT_WINDOW_END_HOUR, minute=0, second=0, microsecond=0)
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=NIGHT_WINDOW_END_HOUR, minute=0, second=0, microsecond=0)


def evaluate_night_ventilation(
    *,
    now: datetime,
    indoor_temp: float | None,
    indoor_humidity: float | None,
    target_temp: float | None,
    hourly_forecast: list[dict[str, Any]],
    air_quality: str = "unknown",
    nina_status: str = "none",
    weather_caution: bool = False,
    weather_danger: bool = False,
) -> NightAdvice:
    """Return a conservative evening hint using only actually available data.

    Temperature drives the initial cooling use case. Optional forecast humidity,
    rain and wind can downgrade the advice. Missing optional forecast fields are
    never invented and therefore never count as either good or bad.
    """
    if not _is_evening(now):
        return NightAdvice()
    if indoor_temp is None or indoor_humidity is None or target_temp is None:
        return NightAdvice()
    if not hourly_forecast:
        return NightAdvice()

    end = _night_end(now)
    points: list[dict[str, Any]] = []
    for item in hourly_forecast:
        stamp = item.get("datetime")
        temp = item.get("temperature")
        if not isinstance(stamp, datetime) or temp is None:
            continue
        if now <= stamp <= end:
            points.append(item)

    # Avoid pretending that one isolated forecast point describes a whole night.
    if len(points) < 3:
        return NightAdvice()

    temperatures = [float(item["temperature"]) for item in points]
    minimum_temp = min(temperatures)
    useful_hours = sum(temp <= indoor_temp - 1.0 for temp in temperatures)

    common_args = {
        "indoor_temp": indoor_temp,
        "target_temp": target_temp,
        "minimum_temp": minimum_temp,
        "useful_hours": useful_hours,
    }

    # Current hard outdoor-health/safety conditions are enough to advise against
    # an unattended/long opening. A future version may incorporate warning expiry.
    if nina_status == "danger" or weather_danger or air_quality == "very_poor":
        return NightAdvice("not_recommended", "night_hard_conditions", common_args)
    if air_quality == "poor":
        return NightAdvice("not_recommended", "night_poor_air", common_args)

    # Night cooling is only useful when there is something to cool. This keeps
    # the feature personal by using the configured target instead of a fixed room
    # temperature that would not suit every user.
    if indoor_temp <= target_temp + 0.5:
        return NightAdvice("not_recommended", "night_target_already_ok", common_args)
    if useful_hours < 2:
        return NightAdvice("not_recommended", "night_not_cooler", common_args)

    rain_risk = False
    strong_wind = False
    forecast_abs_humidity: list[float] = []
    indoor_abs_humidity = absolute_humidity(indoor_temp, indoor_humidity)

    for item in points:
        condition = str(item.get("condition") or "").lower()
        precipitation_probability = item.get("precipitation_probability")
        precipitation = item.get("precipitation")
        if condition in _RAINY_CONDITIONS:
            rain_risk = True
        try:
            if precipitation_probability is not None and float(precipitation_probability) >= 50:
                rain_risk = True
        except (TypeError, ValueError):
            pass
        try:
            if precipitation is not None and float(precipitation) > 0.1:
                rain_risk = True
        except (TypeError, ValueError):
            pass

        try:
            wind = float(item.get("wind_speed")) if item.get("wind_speed") is not None else None
            gust = float(item.get("wind_gust_speed")) if item.get("wind_gust_speed") is not None else None
            if (wind is not None and wind >= 50) or (gust is not None and gust >= 65):
                strong_wind = True
        except (TypeError, ValueError):
            pass

        humidity = item.get("humidity")
        if humidity is not None:
            try:
                forecast_abs_humidity.append(
                    absolute_humidity(float(item["temperature"]), float(humidity))
                )
            except (TypeError, ValueError):
                pass

    humidity_disadvantage = False
    if len(forecast_abs_humidity) >= 2:
        # Median avoids one noisy forecast hour deciding the whole night.
        humidity_disadvantage = median(forecast_abs_humidity) > indoor_abs_humidity + AH_NEUTRAL

    if strong_wind:
        return NightAdvice("not_recommended", "night_strong_wind", common_args)

    if rain_risk or humidity_disadvantage or weather_caution or nina_status == "caution" or air_quality == "moderate":
        reason = "night_conditional"
        args = {
            **common_args,
            "rain_risk": rain_risk,
            "humidity_disadvantage": humidity_disadvantage,
            "weather_caution": weather_caution,
            "air_warning": nina_status == "caution",
            "air_quality_moderate": air_quality == "moderate",
        }
        return NightAdvice("conditional", reason, args)

    return NightAdvice("recommended", "night_recommended", common_args)

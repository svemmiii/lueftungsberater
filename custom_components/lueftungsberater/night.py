"""Best-effort overnight ventilation advice from hourly weather forecasts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import median
from typing import Any

from .engine import AH_NEUTRAL, absolute_humidity

NIGHT_MAX_TEMP_DELTA = 9.0
NIGHT_FORECAST_BUFFER = timedelta(hours=1)
NIGHT_FINAL_HOLD = timedelta(hours=1)

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
    """Compact optional night strategy shown below the normal recommendation."""

    status: str = "unavailable"  # now | later | conditional | blocked | unavailable
    reason_key: str | None = None
    reason_args: dict[str, Any] = field(default_factory=dict)
    safety_block: bool = False


def _advice_rank(advice: NightAdvice) -> int:
    """Higher means more restrictive for final-hour stabilization."""
    return {"now": 0, "later": 1, "conditional": 2, "blocked": 3}.get(
        advice.status, -1
    )


def _advance_held_advice(advice: NightAdvice, now: datetime) -> NightAdvice:
    """Turn a stored 'later' hint into 'now' once its planned start passed."""
    args = dict(advice.reason_args)
    raw_start = args.get("start_time")
    start: datetime | None = None
    if isinstance(raw_start, str):
        try:
            start = datetime.fromisoformat(raw_start)
        except ValueError:
            start = None
    if start is not None and start.tzinfo is not None and start <= now:
        if advice.status == "later":
            args["start_time"] = now.isoformat()
            return NightAdvice("now", "night_now", args)
        if advice.status == "conditional" and advice.reason_key == "night_later_conditional":
            args["start_time"] = now.isoformat()
            return NightAdvice("conditional", "night_now_conditional", args)
    return NightAdvice(advice.status, advice.reason_key, args)


def stabilize_night_advice(
    *,
    now: datetime,
    interval_end: datetime,
    raw: NightAdvice,
    previous: NightAdvice | None,
    planning_need: bool,
    current_delta_ok: bool,
) -> tuple[NightAdvice, NightAdvice | None]:
    """Keep an evening plan calm near the end without hiding new danger.

    The first return value is what the card should show now. The second is the
    non-safety base plan that should be kept for restart/final-hour memory.
    """
    if not planning_need or not current_delta_ok:
        return raw, None

    if raw.safety_block:
        # Hard official/weather protection always wins, but must not overwrite
        # the previous base plan. A late all-clear can therefore fall back to it.
        return raw, previous

    in_final_hour = interval_end - now <= NIGHT_FINAL_HOLD
    if in_final_hour:
        if previous is None:
            # Do not invent a brand-new positive strategy shortly before the
            # configured end; the night card is primarily a pre-sleep decision.
            return NightAdvice(), None
        held = _advance_held_advice(previous, now)
        if raw.status != "unavailable" and _advice_rank(raw) > _advice_rank(held):
            # Worsening conditions may still make the card more cautious.
            return raw, NightAdvice(raw.status, raw.reason_key, dict(raw.reason_args))
        return held, previous

    if raw.status != "unavailable":
        remembered = NightAdvice(raw.status, raw.reason_key, dict(raw.reason_args))
        return raw, remembered
    return raw, previous


def display_interval(
    now: datetime,
    start_minute: int,
    end_minute: int = 7 * 60,
) -> tuple[datetime, datetime] | None:
    """Return the configured daily interval containing ``now``.

    Both bounds are configurable and may cross midnight. Equal start/end is
    treated as a 24-hour window, which is useful for unusual shift schedules.
    """
    start_minute = max(0, min(1439, int(start_minute)))
    end_minute = max(0, min(1439, int(end_minute)))
    start_hour, start_min = divmod(start_minute, 60)
    end_hour, end_min = divmod(end_minute, 60)

    for offset in (-1, 0):
        day = now + timedelta(days=offset)
        start = day.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        end = day.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        if end_minute <= start_minute:
            end += timedelta(days=1)
        if start <= now < end:
            return start, end
    return None


def _rainy(item: dict[str, Any]) -> bool:
    condition = str(item.get("condition") or "").lower()
    if condition in _RAINY_CONDITIONS:
        return True
    for key, threshold in (("precipitation_probability", 50.0), ("precipitation", 0.1)):
        value = item.get(key)
        try:
            if value is not None and float(value) >= threshold:
                return True
        except (TypeError, ValueError):
            pass
    return False


def _wind_level(item: dict[str, Any]) -> int:
    """0 normal, 1 strong/caution, 2 unsafe for long unattended opening."""
    try:
        wind = float(item["wind_speed"]) if item.get("wind_speed") is not None else 0.0
    except (TypeError, ValueError):
        wind = 0.0
    try:
        gust = float(item["wind_gust_speed"]) if item.get("wind_gust_speed") is not None else 0.0
    except (TypeError, ValueError):
        gust = 0.0
    if wind >= 75 or gust >= 105:
        return 2
    if wind >= 50 or gust >= 65:
        return 1
    return 0


def _consecutive_segments(points: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    if not points:
        return []
    points = sorted(points, key=lambda item: item["datetime"])
    segments: list[list[dict[str, Any]]] = [[points[0]]]
    for item in points[1:]:
        if item["datetime"] - segments[-1][-1]["datetime"] <= timedelta(minutes=90):
            segments[-1].append(item)
        else:
            segments.append([item])
    return segments


def evaluate_night_ventilation(
    *,
    now: datetime,
    indoor_temp: float | None,
    indoor_humidity: float | None,
    target_temp: float | None,
    hourly_forecast: list[dict[str, Any]],
    start_minute: int = 22 * 60,
    start_hour: int | None = None,
    end_minute: int = 7 * 60,
    indoor_co2: float | None = None,
    outdoor_co2: float | None = None,
    outdoor_temp: float | None = None,
    outdoor_humidity: float | None = None,
    rain_now: bool = False,
    wind_speed_kmh: float | None = None,
    wind_gust_kmh: float | None = None,
    air_quality: str = "unknown",
    nina_status: str = "none",
    weather_caution: bool = False,
    weather_danger: bool = False,
    air_quality_typical: bool | None = None,
    air_quality_unusual: bool = False,
    air_quality_trend: str = "unknown",
) -> NightAdvice:
    """Return a natural evening strategy using only real forecast fields.

    The configured hour controls when the strategy becomes visible. It does not
    force ventilation to start then: the function searches the forecast for the
    first useful period later in the night. If there is no meaningful benefit,
    no extra line is shown at all.
    """
    if start_hour is not None:
        start_minute = max(0, min(23, int(start_hour))) * 60
    interval = display_interval(now, start_minute, end_minute)
    if interval is None:
        return NightAdvice()
    if indoor_temp is None or indoor_humidity is None or target_temp is None:
        return NightAdvice()
    if not hourly_forecast:
        return NightAdvice()

    _start, end = interval
    points: list[dict[str, Any]] = []
    for raw in hourly_forecast:
        stamp = raw.get("datetime")
        temp = raw.get("temperature")
        if not isinstance(stamp, datetime) or temp is None:
            continue
        try:
            number = float(temp)
        except (TypeError, ValueError):
            continue
        if now <= stamp <= end + NIGHT_FORECAST_BUFFER:
            item = dict(raw)
            item["temperature"] = number
            points.append(item)
    if len(points) < 2:
        return NightAdvice()

    thermal_need = indoor_temp > target_temp + 0.5
    co2_need = indoor_co2 is not None and indoor_co2 >= 1000
    humidity_need = indoor_humidity >= 60
    if not (thermal_need or co2_need or humidity_need):
        return NightAdvice()

    indoor_ah = absolute_humidity(indoor_temp, indoor_humidity)

    # Decide separately whether opening *right now* already helps. The first
    # hourly forecast point can be almost an hour away, so it must not be used
    # as a proxy for the current outdoor conditions.
    current_useful = False
    if outdoor_temp is not None:
        unattended_temp_ok = abs(outdoor_temp - indoor_temp) <= NIGHT_MAX_TEMP_DELTA
        if unattended_temp_ok and thermal_need and outdoor_temp <= indoor_temp - 0.7:
            current_useful = True
        if unattended_temp_ok and humidity_need and outdoor_humidity is not None:
            try:
                current_outdoor_ah = absolute_humidity(outdoor_temp, outdoor_humidity)
                if current_outdoor_ah <= indoor_ah - AH_NEUTRAL:
                    current_useful = True
            except (TypeError, ValueError):
                pass

    # A longer night opening needs a sustained reason. Temperature is the main
    # planning signal; high humidity can also create one when forecast humidity
    # shows real drying potential. CO2 alone is kept as supporting context: a
    # current high value justifies ordinary airing, but cannot predict overnight
    # occupancy and therefore does not by itself trigger an "all night" hint.
    candidate_points: list[dict[str, Any]] = []
    for item in points:
        useful = False
        # A night hint is meant for a longer, mostly unattended opening. Even a
        # thermodynamically helpful forecast is not a sensible all-night hint if
        # it is more than 9 K away from the current room temperature. Ordinary
        # live airing remains handled by the main advisor without this guard.
        if abs(float(item["temperature"]) - indoor_temp) > NIGHT_MAX_TEMP_DELTA:
            continue
        if thermal_need and item["temperature"] <= indoor_temp - 0.7:
            useful = True
        if humidity_need and item.get("humidity") is not None:
            try:
                outside_ah = absolute_humidity(item["temperature"], float(item["humidity"]))
                if outside_ah <= indoor_ah - AH_NEUTRAL:
                    useful = True
            except (TypeError, ValueError):
                pass
        if useful:
            candidate_points.append(item)

    segments = [
        segment
        for segment in _consecutive_segments(candidate_points)
        if len(segment) >= 2 and segment[0]["datetime"] < end
    ]
    if not segments:
        return NightAdvice()

    # Prefer the earliest useful segment; if two start at the same point the
    # longer one naturally wins because contiguous points are already merged.
    segment = segments[0]
    forecast_start_time = segment[0]["datetime"]
    end_time = segment[-1]["datetime"] + timedelta(hours=1)
    minimum_temp = min(float(item["temperature"]) for item in segment)

    # "Show from 22:00" is only the start of the night strategy display. It is
    # not an instruction to open the window at 22:00. Recommend "now" only
    # when live outdoor values already help and the forecast confirms that this
    # useful period continues. Otherwise name the later forecast start.
    starts_now = current_useful and forecast_start_time <= now + timedelta(minutes=90)
    start_time = now if starts_now else forecast_start_time

    forecast_ah: list[float] = []
    rain_risk = False
    max_wind_level = 0
    for item in segment:
        rain_risk = rain_risk or _rainy(item)
        max_wind_level = max(max_wind_level, _wind_level(item))
        humidity = item.get("humidity")
        if humidity is not None:
            try:
                forecast_ah.append(
                    absolute_humidity(float(item["temperature"]), float(humidity))
                )
            except (TypeError, ValueError):
                pass

    if starts_now:
        rain_risk = rain_risk or bool(rain_now)
        max_wind_level = max(
            max_wind_level,
            _wind_level(
                {
                    "wind_speed": wind_speed_kmh,
                    "wind_gust_speed": wind_gust_kmh,
                }
            ),
        )

    humidity_disadvantage = False
    humidity_advantage = False
    if len(forecast_ah) >= 2:
        typical_ah = median(forecast_ah)
        humidity_disadvantage = typical_ah > indoor_ah + AH_NEUTRAL
        humidity_advantage = typical_ah < indoor_ah - AH_NEUTRAL

    co2_difference = None
    if indoor_co2 is not None and outdoor_co2 is not None:
        co2_difference = indoor_co2 - outdoor_co2

    args = {
        "indoor_temp": indoor_temp,
        "target_temp": target_temp,
        "minimum_temp": minimum_temp,
        "start_time": start_time.isoformat(),
        "end_time": min(end_time, end).isoformat(),
        "rain_risk": rain_risk,
        "humidity_disadvantage": humidity_disadvantage,
        "humidity_advantage": humidity_advantage,
        "thermal_need": thermal_need,
        "humidity_need": humidity_need,
        "weather_caution": weather_caution,
        "air_warning": nina_status == "caution",
        "air_quality": air_quality,
        "air_quality_typical": air_quality_typical,
        "air_quality_unusual": air_quality_unusual,
        "air_quality_trend": air_quality_trend,
        "co2": indoor_co2,
        "outdoor_co2": outdoor_co2,
        "co2_difference": co2_difference,
    }

    # A true protection reason is stronger than a planning hint. Very poor LQI
    # alone is not a safety lock here, but it is enough to avoid recommending a
    # long unattended opening, especially when it is unusually bad locally.
    if nina_status == "danger" or weather_danger or max_wind_level >= 2:
        return NightAdvice(
            "blocked",
            "night_blocked",
            args,
            safety_block=(nina_status == "danger" or weather_danger),
        )
    if air_quality == "very_poor" and (air_quality_unusual or air_quality_trend == "rising"):
        return NightAdvice("blocked", "night_air_too_bad", args)

    drawbacks = (
        rain_risk
        or humidity_disadvantage
        or weather_caution
        or nina_status == "caution"
        or max_wind_level == 1
        or air_quality in {"moderate", "poor", "very_poor"}
    )

    later = not starts_now
    if drawbacks:
        key = "night_later_conditional" if later else "night_now_conditional"
        return NightAdvice("conditional", key, args)
    if later:
        return NightAdvice("later", "night_later", args)
    return NightAdvice("now", "night_now", args)

"""Best-effort overnight ventilation advice from hourly weather forecasts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from .engine import AH_NEUTRAL, absolute_humidity

NIGHT_MAX_TEMP_DELTA = 9.0
NIGHT_TARGET_OVERSHOOT_MARGIN = 4.0
NIGHT_MIN_LONG_WINDOW = timedelta(minutes=60)
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

_LIVE_OPEN_POSITIVE = {"open_now", "keep_open"}
_LIVE_OPEN_CAUTION = {"short_observation", "optional"}
_LIVE_CLOSE = {
    "can_close",
    "better_close",
    "caution_keep_closed",
    "keep_closed",
    "close_now",
    "wait",
}


@dataclass(slots=True)
class NightAdvice:
    """Compact optional night strategy shown below the normal recommendation."""

    status: str = "unavailable"  # now | later | conditional | short_only | not_recommended | blocked | unavailable
    reason_key: str | None = None
    reason_args: dict[str, Any] = field(default_factory=dict)
    safety_block: bool = False  # transient hard protection; do not replace stable night memory


@dataclass(slots=True)
class _PointAssessment:
    """Reason-aware usefulness of one current/forecast outdoor state."""

    item: dict[str, Any]
    temperature: float
    humidity_ah: float | None
    thermal_help: bool
    thermal_harm: bool
    humidity_help: bool
    humidity_harm: bool
    long_temp_ok: bool

    @property
    def thermal_compatible(self) -> bool:
        return self.thermal_help and not self.humidity_harm

    @property
    def humidity_compatible(self) -> bool:
        return self.humidity_help and not self.thermal_harm

    def reason_compatible(self, reason: str) -> bool:
        if reason == "temperature":
            return self.thermal_compatible
        if reason == "humidity":
            return self.humidity_compatible
        return False

    def reason_long_compatible(self, reason: str) -> bool:
        return self.long_temp_ok and self.reason_compatible(reason)


@dataclass(slots=True)
class _SegmentChoice:
    reason: str
    points: list[_PointAssessment]
    start: datetime
    end: datetime



def _advice_rank(advice: NightAdvice) -> int:
    """Higher means more restrictive for final-hour stabilization."""
    return {
        "now": 0,
        "later": 1,
        "conditional": 2,
        "short_only": 3,
        "not_recommended": 4,
        "blocked": 5,
    }.get(advice.status, -1)



def _timeline(value: datetime) -> datetime:
    """Return a chronological comparison value that respects ``fold``."""
    return value.astimezone(timezone.utc) if value.tzinfo is not None else value



def _parse_advice_time(advice: NightAdvice, key: str) -> datetime | None:
    raw = advice.reason_args.get(key)
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None



def _advice_expired(advice: NightAdvice, now: datetime) -> bool:
    """Return whether a remembered plan's own useful window already ended."""
    end = _parse_advice_time(advice, "end_time")
    return end is not None and _timeline(end) <= _timeline(now)



def _advance_held_advice(advice: NightAdvice, now: datetime) -> NightAdvice:
    """Turn a stored 'later' hint into 'now' once its valid start passed."""
    if _advice_expired(advice, now):
        return NightAdvice()

    args = dict(advice.reason_args)
    start = _parse_advice_time(advice, "start_time")
    if start is not None and _timeline(start) <= _timeline(now):
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

    ``short_only`` is a real night strategy too. A large temperature delta may
    therefore change the advice from long opening to short airing without
    clearing the final-hour memory altogether.
    """
    # Compatibility argument retained for callers/tests from v0.9.3. The night
    # strategy itself now distinguishes long-vs-short suitability.
    _ = current_delta_ok

    if not planning_need:
        return raw, None

    if previous is not None and _advice_expired(previous, now):
        previous = None

    if raw.safety_block:
        # Hard official/weather protection always wins, but must not overwrite
        # a still-valid base plan. A late all-clear can therefore fall back to it.
        return raw, previous

    in_final_hour = _timeline(interval_end) - _timeline(now) <= NIGHT_FINAL_HOLD
    if in_final_hour:
        if previous is None:
            # Do not invent a brand-new positive strategy shortly before the
            # configured end; cautious/blocking advice may still be shown raw.
            if raw.status in {"conditional", "short_only", "not_recommended", "blocked"}:
                remembered = (
                    NightAdvice(raw.status, raw.reason_key, dict(raw.reason_args))
                    if raw.status != "blocked"
                    else None
                )
                return raw, remembered
            return NightAdvice(), None
        held = _advance_held_advice(previous, now)
        if held.status == "unavailable":
            # The remembered plan itself has expired. Do not resurrect it merely
            # because the configured night-display interval is still active.
            if raw.status != "unavailable":
                remembered = NightAdvice(raw.status, raw.reason_key, dict(raw.reason_args))
                return raw, remembered
            return NightAdvice(), None
        if raw.status != "unavailable" and _advice_rank(raw) > _advice_rank(held):
            # Worsening conditions may still make the card more cautious.
            return raw, NightAdvice(raw.status, raw.reason_key, dict(raw.reason_args))
        return held, previous

    if raw.status != "unavailable":
        remembered = NightAdvice(raw.status, raw.reason_key, dict(raw.reason_args))
        return raw, remembered
    return raw, previous



def _local_wall_time(
    day: datetime,
    minute_of_day: int,
    *,
    end_bound: bool = False,
) -> datetime:
    """Build a DST-safe local wall time for the date represented by ``day``."""
    hour, minute = divmod(minute_of_day, 60)
    first = day.replace(hour=hour, minute=minute, second=0, microsecond=0, fold=0)
    if first.tzinfo is None:
        return first
    second = first.replace(fold=1)
    zone = first.tzinfo
    target = (first.year, first.month, first.day, hour, minute)

    def _roundtrip(candidate: datetime) -> tuple[datetime, bool]:
        back = candidate.astimezone(timezone.utc).astimezone(zone)
        valid = (back.year, back.month, back.day, back.hour, back.minute) == target
        return back, valid

    back0, valid0 = _roundtrip(first)
    back1, valid1 = _roundtrip(second)
    if valid0 and valid1 and first.utcoffset() != second.utcoffset():
        return second if end_bound else first
    if valid0:
        return first
    if valid1:
        return second

    options = [back0, back1]
    after = [
        item
        for item in options
        if (item.year, item.month, item.day, item.hour, item.minute) > target
    ]
    return min(after or options, key=lambda item: item.astimezone(timezone.utc))



def display_interval(
    now: datetime,
    start_minute: int,
    end_minute: int = 7 * 60,
) -> tuple[datetime, datetime] | None:
    """Return the configured daily interval containing ``now``."""
    start_minute = max(0, min(1439, int(start_minute)))
    end_minute = max(0, min(1439, int(end_minute)))
    for offset in (-1, 0):
        day = now + timedelta(days=offset)
        start = _local_wall_time(day, start_minute, end_bound=False)
        end_day = day + timedelta(days=1) if end_minute <= start_minute else day
        end = _local_wall_time(end_day, end_minute, end_bound=True)
        now_key = _timeline(now)
        if _timeline(start) <= now_key < _timeline(end):
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



def _consecutive_segments(points: list[_PointAssessment]) -> list[list[_PointAssessment]]:
    if not points:
        return []
    points = sorted(points, key=lambda item: _timeline(item.item["datetime"]))
    segments: list[list[_PointAssessment]] = [[points[0]]]
    for item in points[1:]:
        if (
            _timeline(item.item["datetime"])
            - _timeline(segments[-1][-1].item["datetime"])
            <= timedelta(minutes=90)
        ):
            segments[-1].append(item)
        else:
            segments.append([item])
    return segments



def _long_temperature_ok(
    *,
    outdoor_temp: float,
    indoor_temp: float,
    target_temp: float,
    thermal_need: bool,
    humidity_need: bool,
) -> bool:
    """Conservative guard for long/unattended opening.

    The 9 K room/outdoor delta remains the absolute product guard. In addition,
    long opening may not drive the room far past the personal target. This keeps
    a tiny cooling need from justifying hours of very cold air and keeps a dry,
    very hot night from being advertised as a long drying strategy.
    """
    if abs(outdoor_temp - indoor_temp) > NIGHT_MAX_TEMP_DELTA:
        return False

    # If cooling is genuinely needed, allow a wider undershoot the further the
    # room currently is above target, but never beyond the absolute 9 K guard.
    # A tiny 0.6 K cooling need therefore cannot justify hours of 9 K colder air,
    # while a genuinely overheated room still gets useful night-cooling range.
    if thermal_need:
        cooling_gap = max(0.0, indoor_temp - target_temp)
        allowed_below_target = min(
            NIGHT_MAX_TEMP_DELTA,
            NIGHT_TARGET_OVERSHOOT_MARGIN + 2.0 * cooling_gap,
        )
        return outdoor_temp >= target_temp - allowed_below_target
    if humidity_need:
        low = target_temp - NIGHT_TARGET_OVERSHOOT_MARGIN
        high = target_temp + NIGHT_TARGET_OVERSHOOT_MARGIN
        return low <= outdoor_temp <= high
    return True



def _assess_point(
    *,
    item: dict[str, Any],
    indoor_temp: float,
    indoor_ah: float,
    target_temp: float,
    thermal_need: bool,
    humidity_need: bool,
) -> _PointAssessment:
    temp = float(item["temperature"])
    humidity_ah: float | None = None
    humidity = item.get("humidity")
    if humidity is not None:
        try:
            humidity_ah = absolute_humidity(temp, float(humidity))
        except (TypeError, ValueError):
            humidity_ah = None

    thermal_help = thermal_need and temp <= indoor_temp - 0.7
    thermal_harm = thermal_need and temp > indoor_temp
    humidity_help = (
        humidity_need
        and humidity_ah is not None
        and humidity_ah <= indoor_ah - AH_NEUTRAL
    )
    humidity_harm = (
        humidity_need
        and humidity_ah is not None
        and humidity_ah > indoor_ah + AH_NEUTRAL
    )
    return _PointAssessment(
        item=item,
        temperature=temp,
        humidity_ah=humidity_ah,
        thermal_help=thermal_help,
        thermal_harm=thermal_harm,
        humidity_help=humidity_help,
        humidity_harm=humidity_harm,
        long_temp_ok=_long_temperature_ok(
            outdoor_temp=temp,
            indoor_temp=indoor_temp,
            target_temp=target_temp,
            thermal_need=thermal_need,
            humidity_need=humidity_need,
        ),
    )



def _visible_segment(
    reason: str,
    segment: list[_PointAssessment],
    interval_end: datetime,
) -> _SegmentChoice | None:
    start = segment[0].item["datetime"]
    end = min(segment[-1].item["datetime"] + timedelta(hours=1), interval_end)
    if _timeline(end) - _timeline(start) < NIGHT_MIN_LONG_WINDOW:
        return None
    return _SegmentChoice(reason=reason, points=segment, start=start, end=end)


def _points_before(
    points: list[_PointAssessment],
    end: datetime,
) -> list[_PointAssessment]:
    """Return forecast points that belong to the actual displayed plan.

    The night planner intentionally loads one extra forecast hour so a segment
    reaching the configured end can still be recognized. That buffer must never
    leak into risk, min/max or advantage/disadvantage evaluation.
    """
    return [
        item
        for item in points
        if _timeline(item.item["datetime"]) < _timeline(end)
    ]



def _live_opening_state(recommendation_key: str | None) -> tuple[bool, bool, bool]:
    """Return (positive, cautious, restrictive) for the current live advisor."""
    if recommendation_key in _LIVE_OPEN_POSITIVE:
        return True, False, False
    if recommendation_key in _LIVE_OPEN_CAUTION:
        return False, True, False
    if recommendation_key in _LIVE_CLOSE:
        return False, False, True
    return False, False, False



def _continuous_from_now(
    *,
    now: datetime,
    segment_start: datetime,
    reason: str,
    assessments: list[_PointAssessment],
) -> bool:
    """Do not bridge over a known bad point merely because a later window is good."""
    for assessment in assessments:
        stamp = assessment.item["datetime"]
        if _timeline(now) < _timeline(stamp) < _timeline(segment_start):
            if not assessment.reason_long_compatible(reason):
                return False
    return True



def _outdoor_co2_disadvantage(indoor_co2: float | None, outdoor_co2: float | None) -> tuple[float | None, bool]:
    if indoor_co2 is None or outdoor_co2 is None:
        return None, False
    difference = indoor_co2 - outdoor_co2
    return difference, outdoor_co2 >= indoor_co2 + 100.0



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
    live_recommendation_key: str | None = None,
    live_mode: str | None = None,
) -> NightAdvice:
    """Return a reason-aware night strategy using live state plus forecast.

    CO₂ remains a live-advisor responsibility because overnight occupancy is not
    predictable. The night card may reference an active live CO₂ instruction, but
    it never replaces it with an unattended all-night plan.
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

    _, interval_end = interval
    raw_points: list[dict[str, Any]] = []
    for raw in hourly_forecast:
        stamp = raw.get("datetime")
        temp = raw.get("temperature")
        if not isinstance(stamp, datetime) or temp is None:
            continue
        try:
            number = float(temp)
        except (TypeError, ValueError):
            continue
        if _timeline(now) <= _timeline(stamp) <= _timeline(interval_end + NIGHT_FORECAST_BUFFER):
            item = dict(raw)
            item["temperature"] = number
            raw_points.append(item)
    if len(raw_points) < 2:
        return NightAdvice()

    thermal_need = indoor_temp > target_temp + 0.5
    humidity_need = indoor_humidity >= 60
    if not (thermal_need or humidity_need):
        return NightAdvice()

    indoor_ah = absolute_humidity(indoor_temp, indoor_humidity)
    assessments = [
        _assess_point(
            item=item,
            indoor_temp=indoor_temp,
            indoor_ah=indoor_ah,
            target_temp=target_temp,
            thermal_need=thermal_need,
            humidity_need=humidity_need,
        )
        for item in raw_points
    ]

    current_assessment: _PointAssessment | None = None
    if outdoor_temp is not None:
        current_item: dict[str, Any] = {"temperature": float(outdoor_temp)}
        if outdoor_humidity is not None:
            current_item["humidity"] = float(outdoor_humidity)
        current_assessment = _assess_point(
            item=current_item,
            indoor_temp=indoor_temp,
            indoor_ah=indoor_ah,
            target_temp=target_temp,
            thermal_need=thermal_need,
            humidity_need=humidity_need,
        )

    live_positive, live_cautious, live_restrictive = _live_opening_state(
        live_recommendation_key
    )
    live_open_now = live_positive or live_cautious

    co2_difference, outdoor_co2_bad = _outdoor_co2_disadvantage(
        indoor_co2, outdoor_co2
    )
    current_wind_level = _wind_level(
        {"wind_speed": wind_speed_kmh, "wind_gust_speed": wind_gust_kmh}
    )

    current_thermal_advantage = bool(
        current_assessment and current_assessment.thermal_compatible
    )
    current_humidity_advantage = bool(
        current_assessment and current_assessment.humidity_compatible
    )
    current_thermal_disadvantage = bool(
        current_assessment and current_assessment.thermal_harm
    )
    current_humidity_disadvantage = bool(
        current_assessment and current_assessment.humidity_harm
    )
    current_any_compatible = current_thermal_advantage or current_humidity_advantage

    # Build independent, reason-stable segments. A temperature segment must stay
    # useful for temperature throughout, and a humidity segment must stay useful
    # for humidity throughout. A simultaneously active other need may be neutral,
    # but must never be actively worsened.
    segment_choices: list[_SegmentChoice] = []
    for reason, enabled in (("temperature", thermal_need), ("humidity", humidity_need)):
        if not enabled:
            continue
        reason_points = [
            item for item in assessments if item.reason_long_compatible(reason)
        ]
        for segment in _consecutive_segments(reason_points):
            if len(segment) < 2:
                continue
            visible = _visible_segment(reason, segment, interval_end)
            if visible is not None and _timeline(visible.start) < _timeline(interval_end):
                segment_choices.append(visible)

    segment_choices.sort(
        key=lambda choice: (
            _timeline(choice.start),
            -(_timeline(choice.end) - _timeline(choice.start)).total_seconds(),
            0 if choice.reason == "humidity" else 1,
        )
    )

    planned_assessments = _points_before(assessments, interval_end)
    helpful_points = [
        item
        for item in planned_assessments
        if item.thermal_compatible or item.humidity_compatible
    ]
    long_candidate_points = [
        item
        for item in helpful_points
        if item.long_temp_ok
    ]
    temperature_limited_points = [
        item for item in helpful_points if not item.long_temp_ok
    ]

    common_args: dict[str, Any] = {
        "indoor_temp": indoor_temp,
        "outdoor_temp": outdoor_temp,
        "target_temp": target_temp,
        "thermal_need": thermal_need,
        "humidity_need": humidity_need,
        "current_thermal_advantage": current_thermal_advantage,
        "current_humidity_advantage": current_humidity_advantage,
        "current_thermal_disadvantage": current_thermal_disadvantage,
        "current_humidity_disadvantage": current_humidity_disadvantage,
        "co2": indoor_co2,
        "outdoor_co2": outdoor_co2,
        "co2_difference": co2_difference,
        "outdoor_co2_disadvantage": outdoor_co2_bad,
        "weather_caution": weather_caution,
        "air_warning": nina_status == "caution",
        "air_quality": air_quality,
        "air_quality_typical": air_quality_typical,
        "air_quality_unusual": air_quality_unusual,
        "air_quality_trend": air_quality_trend,
        "live_open_now": live_open_now,
        "live_recommendation_key": live_recommendation_key,
        "live_mode": live_mode,
        "live_restrictive": live_restrictive,
        "current_wind_level": current_wind_level,
        "current_rain_risk": bool(rain_now),
        "rain_risk": bool(rain_now),
    }

    # Hard current protection is independent of whether a long forecast segment
    # exists. Very poor but locally normal/stable air remains a strong drawback,
    # not a safety lock.
    if nina_status == "danger" or weather_danger or current_wind_level >= 2:
        return NightAdvice(
            "blocked",
            "night_blocked",
            dict(common_args),
            # Current hard wind is just as transient as an official/weather
            # safety block: show it immediately, but keep the previous stable
            # plan available for a later all-clear. Forecast wind is handled
            # below and may still replace the plan when the future window itself
            # becomes unsafe.
            safety_block=True,
        )
    if air_quality == "very_poor" and (
        air_quality_unusual or air_quality_trend == "rising"
    ):
        return NightAdvice(
            "blocked",
            "night_air_too_bad",
            dict(common_args),
            safety_block=True,
        )

    if not segment_choices:
        visible_temperatures = [item.temperature for item in planned_assessments]
        if not visible_temperatures and current_assessment is not None:
            visible_temperatures = [current_assessment.temperature]
        minimum_temp = min(visible_temperatures, default=None)
        maximum_temp = max(visible_temperatures, default=None)
        limited_point = min(
            temperature_limited_points,
            key=lambda item: _timeline(item.item["datetime"]),
            default=None,
        )
        limit_direction = None
        limit_time = None
        if current_assessment is not None and current_any_compatible and not current_assessment.long_temp_ok:
            limit_direction = "cold" if current_assessment.temperature < indoor_temp else "warm"
        elif limited_point is not None:
            limit_direction = "cold" if limited_point.temperature < indoor_temp else "warm"
            limit_time = limited_point.item["datetime"].isoformat()

        args = dict(common_args)
        args.update(
            {
                "minimum_temp": minimum_temp,
                "maximum_temp": maximum_temp,
                "start_time": now.isoformat(),
                "end_time": interval_end.isoformat(),
                "limit_time": limit_time,
                "temperature_limit_direction": limit_direction,
                "max_temp_delta": NIGHT_MAX_TEMP_DELTA,
                "target_overshoot_margin": NIGHT_TARGET_OVERSHOOT_MARGIN,
                "has_helpful_forecast": bool(helpful_points),
                "has_long_candidate_points": bool(long_candidate_points),
                "no_contiguous_window": bool(helpful_points),
                "forecast_humidity_advantage": any(
                    item.humidity_compatible for item in planned_assessments
                ),
                "forecast_humidity_disadvantage": any(
                    item.humidity_harm for item in planned_assessments
                ),
                "forecast_thermal_advantage": any(
                    item.thermal_compatible for item in planned_assessments
                ),
                "forecast_thermal_disadvantage": any(
                    item.thermal_harm for item in planned_assessments
                ),
                "forecast_rain_risk": any(_rainy(item.item) for item in helpful_points),
                "forecast_max_wind_level": max(
                    [_wind_level(item.item) for item in helpful_points],
                    default=0,
                ),
                "max_wind_level": max(
                    [current_wind_level]
                    + [_wind_level(item.item) for item in helpful_points]
                ),
            }
        )

        # A friendly short-airing instruction is only allowed when the current
        # live advisor is not explicitly telling the user to close/wait. Soft
        # drawbacks stay visible in the text instead of being ignored.
        if current_any_compatible and not live_restrictive:
            return NightAdvice("short_only", "night_short_only", args)
        return NightAdvice("not_recommended", "night_not_recommended", args)

    choice = segment_choices[0]
    forecast_start_time = choice.start
    end_time = choice.end
    segment = _points_before(choice.points, end_time)
    if not segment:
        # Defensive fallback: _visible_segment guarantees start < end, so this
        # should not occur for valid hourly data. Never evaluate buffer-only
        # points as though they belonged to the displayed plan.
        return NightAdvice()
    minimum_temp = min(item.temperature for item in segment)

    if choice.reason == "temperature":
        current_reason_long = bool(
            current_assessment
            and current_assessment.reason_long_compatible("temperature")
        )
    else:
        current_reason_long = bool(
            current_assessment
            and current_assessment.reason_long_compatible("humidity")
        )

    # A current strategy may only bridge into a later segment when every known
    # point in between is compatible with that same reason. This prevents
    # "22:31 good -> 23:00 bad -> 00:00 good" from becoming one continuous plan.
    continuous_to_segment = _continuous_from_now(
        now=now,
        segment_start=forecast_start_time,
        reason=choice.reason,
        assessments=assessments,
    )
    starts_now = (
        current_reason_long
        and not live_restrictive
        and _timeline(forecast_start_time) <= _timeline(now + timedelta(minutes=90))
        and continuous_to_segment
    )
    # If runtime supplied the live card, require it to agree that opening is at
    # least reasonable. Pure unit callers without live context retain legacy use.
    if live_recommendation_key is not None and not (live_positive or live_cautious):
        starts_now = False

    start_time = now if starts_now else forecast_start_time

    forecast_rain_risk = False
    forecast_max_wind_level = 0
    segment_ah: list[float] = []
    for item in segment:
        forecast_rain_risk = forecast_rain_risk or _rainy(item.item)
        forecast_max_wind_level = max(
            forecast_max_wind_level, _wind_level(item.item)
        )
        if item.humidity_ah is not None:
            segment_ah.append(item.humidity_ah)

    rain_risk = forecast_rain_risk or (starts_now and bool(rain_now))
    max_wind_level = max(
        forecast_max_wind_level,
        current_wind_level if starts_now else 0,
    )

    # Long, mostly unattended opening is judged conservatively: one clearly wet
    # hour is enough to count as a humidity drawback. "Drier" is only claimed if
    # every available humidity point in the planned segment is genuinely drier.
    forecast_humidity_disadvantage = any(
        value > indoor_ah + AH_NEUTRAL for value in segment_ah
    )
    forecast_humidity_advantage = bool(segment_ah) and all(
        value <= indoor_ah - AH_NEUTRAL for value in segment_ah
    )
    forecast_thermal_advantage = all(
        item.temperature <= indoor_temp - 0.7 for item in segment
    )
    forecast_thermal_disadvantage = any(
        item.temperature > indoor_temp for item in segment
    )

    args = dict(common_args)
    args.update(
        {
            "minimum_temp": minimum_temp,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "rain_risk": rain_risk,
            "forecast_rain_risk": forecast_rain_risk,
            "forecast_max_wind_level": forecast_max_wind_level,
            "forecast_humidity_disadvantage": forecast_humidity_disadvantage,
            "forecast_humidity_advantage": forecast_humidity_advantage,
            "forecast_thermal_advantage": forecast_thermal_advantage,
            "forecast_thermal_disadvantage": forecast_thermal_disadvantage,
            "segment_reason": choice.reason,
            "max_wind_level": max_wind_level,
            "max_temp_delta": NIGHT_MAX_TEMP_DELTA,
            "target_overshoot_margin": NIGHT_TARGET_OVERSHOOT_MARGIN,
        }
    )

    if nina_status == "danger" or weather_danger or max_wind_level >= 2:
        return NightAdvice(
            "blocked",
            "night_blocked",
            args,
            safety_block=(nina_status == "danger" or weather_danger),
        )
    if air_quality == "very_poor" and (
        air_quality_unusual or air_quality_trend == "rising"
    ):
        return NightAdvice("blocked", "night_air_too_bad", args)

    drawbacks = (
        rain_risk
        or forecast_humidity_disadvantage
        or weather_caution
        or nina_status == "caution"
        or max_wind_level == 1
        or air_quality in {"moderate", "poor", "very_poor"}
        or outdoor_co2_bad
    )

    later = not starts_now
    if drawbacks:
        key = "night_later_conditional" if later else "night_now_conditional"
        return NightAdvice("conditional", key, args)
    if later:
        return NightAdvice("later", "night_later", args)
    return NightAdvice("now", "night_now", args)

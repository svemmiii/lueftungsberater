"""Home-Assistant-independent ventilation decision engine.

The engine returns semantic keys plus raw values instead of pre-rendered
language. Decisions deliberately use a hierarchy of evidence instead of a
single additive score: safety/health constraints first, then the strongest
current ventilation need, then expected humidity/temperature/comfort effects.
"""
from __future__ import annotations

import math

from .models import RoomInput, VentilationResult

# Absolute-humidity differences are continuous physics, not health thresholds.
# This small dead-band is only a technical neutral zone to avoid treating sensor
# noise and tiny practical differences as a strong reason for/against airing.
AH_NEUTRAL = 0.5
AH_CONTINUE = 0.3


def absolute_humidity(temp_c: float, rh: float) -> float:
    """Return absolute humidity in g/m³ using the Magnus approximation."""
    vapor_pressure = (rh / 100.0) * 6.112 * math.exp((17.62 * temp_c) / (243.12 + temp_c))
    return 216.7 * vapor_pressure / (273.15 + temp_c)


def surface_relative_humidity(
    indoor_temp_c: float,
    indoor_rh: float,
    surface_temp_c: float | None,
) -> float | None:
    """Estimate RH directly at an actually measured cold surface."""
    if surface_temp_c is None:
        return None
    actual_vapor_pressure = (indoor_rh / 100.0) * 6.112 * math.exp(
        (17.62 * indoor_temp_c) / (243.12 + indoor_temp_c)
    )
    saturation_surface = 6.112 * math.exp(
        (17.62 * surface_temp_c) / (243.12 + surface_temp_c)
    )
    if saturation_surface <= 0:
        return None
    return max(0.0, min(100.0, actual_vapor_pressure / saturation_surface * 100.0))


def co2_status(ppm: float | None) -> str:
    if ppm is None:
        return "unknown"
    if ppm > 2000:
        return "critical"
    if ppm >= 1400:
        return "high"
    if ppm >= 1000:
        return "elevated"
    if ppm >= 800:
        return "good"
    return "very_good"


def _normal_airing_duration(outdoor_temp: float) -> str:
    """Return a compact practical airing band with a >=5 min lower bound."""
    if outdoor_temp < 0:
        return "5_8"
    if outdoor_temp < 10:
        return "5_10"
    if outdoor_temp < 18:
        return "8_12"
    if outdoor_temp <= 25:
        return "10_15"
    return "10_20"


def _duration_key(mode: str, outdoor_temp: float) -> str:
    if mode == "weiter_lueften":
        return "until_targets"
    if mode == "lueftung_fertig":
        return "can_end"
    if mode in {"co2_kritisch_vorsicht", "co2_abwaegung"}:
        return "brief_observation"
    if mode == "co2_kritisch":
        return "co2_recheck"
    if mode == "co2_lueften":
        return "co2_until_good"
    if mode == "kuehlen":
        return "cooling"
    if mode == "erwaermen":
        return "warming"
    if mode in {
        "feuchte_lueften",
        "schimmel_lueften",
        "schimmel_langzeit_lueften",
        "routine_lueften",
    }:
        return _normal_airing_duration(outdoor_temp)
    return "not_needed"


def _duration_max_minutes(mode: str, outdoor_temp: float) -> float:
    key = _duration_key(mode, outdoor_temp)
    return {
        "brief_observation": 5,
        "co2_recheck": 10,
        "co2_until_good": 10,
        "cooling": 30,
        "warming": 10,
        "5_8": 8,
        "5_10": 10,
        "8_12": 12,
        "10_15": 15,
        "10_20": 20,
        "until_targets": 10,
    }.get(key, 10)


def _color(mode: str) -> str:
    if mode in {
        "co2_kritisch",
        "co2_lueften",
        "weiter_lueften",
        "feuchte_lueften",
        "schimmel_lueften",
        "schimmel_langzeit_lueften",
        "kuehlen",
        "erwaermen",
        "routine_lueften",
    }:
        return "green"
    if mode in {
        "co2_kritisch_vorsicht",
        "co2_abwaegung",
        "feuchte_neutral",
        "schimmel_neutral",
        "komfort_abwaegung",
        "lueftung_fertig",
        "normal",
    }:
        return "yellow"
    # Red deliberately means "keep closed / overall disadvantage", not only
    # an emergency. That includes severe weather as well as simply worsening an
    # otherwise good room for no useful reason.
    return "red"


def _recommendation_key(color: str, mode: str, window_open: bool) -> str:
    if color == "green":
        return "keep_open" if window_open else "open_now"
    if color == "red":
        return "close_now" if window_open else "keep_closed"
    if mode in {"co2_kritisch_vorsicht", "co2_abwaegung", "komfort_abwaegung"}:
        return "short_observation"
    if window_open:
        return "can_close"
    if mode in {"normal", "feuchte_neutral", "schimmel_neutral"}:
        return "optional"
    return "wait"


def _rain_relevant(data: RoomInput, candidate_mode: str, outdoor_temp: float) -> bool:
    """Return whether predicted rain can realistically overlap this airing."""
    if data.rain_now:
        return True
    if data.rain_minutes_until is not None:
        return 0 <= data.rain_minutes_until <= _duration_max_minutes(candidate_mode, outdoor_temp) + 5
    # Legacy/manual rain-soon binary sensors do not carry a timestamp. Keep them
    # as a conservative advisory because the engine cannot know the lead time.
    return bool(data.rain_soon)


def _temperature_moves_toward_target(ti: float, ta: float, target: float) -> bool:
    """Return whether airing initially moves room temperature toward target.

    Outdoor air does not need to be numerically closer to the target than the
    current room temperature. If a room is too warm, any sufficiently cooler
    outdoor air moves it in the correct direction until the target is reached;
    the same applies vice versa for warming.
    """
    if ti > target:
        return ta <= ti - 0.7
    if ti < target:
        return ta >= ti + 0.7
    return False


def _temperature_moves_away(ti: float, ta: float, target: float) -> bool:
    """Return whether airing would move an otherwise comfortable room away.

    Once the room is already above/below target, outdoor air on the useful
    side of the current temperature must never be treated as a disadvantage
    merely because it lies far beyond the target. Overshoot is controlled by
    the airing hysteresis/duration instead.
    """
    if ti > target + 0.5:
        return ta >= ti + 2.0
    if ti < target - 0.5:
        return ta <= ti - 2.0
    return abs(ta - target) >= 2.0 and abs(ta - ti) >= 2.0


def _primary_need(
    *,
    co2: float | None,
    hi: float,
    ti: float,
    ta: float,
    target: float,
    diff: float,
    mold_risk: bool,
    mold_persistent: bool,
    hours: float,
    previous_mode: str,
    window_open: bool,
) -> tuple[str, int]:
    """Return the strongest current reason and a small ordinal urgency level."""
    if co2 is not None and co2 > 2000:
        return "co2_critical", 3

    # Personal target remains the comfort reference, but very hot indoor air can
    # still justify cooling even if an unusually high target was configured.
    if ti >= 30 and ta <= ti - 1:
        return "heat", 3

    if mold_persistent:
        return "mold_persistent", 3
    if hi >= 65:
        return "humidity_urgent", 2
    if co2 is not None and co2 >= 1400:
        return "co2_high", 2
    if mold_risk:
        return "mold", 2
    if hi >= 60 or (
        previous_mode in {"feuchte_lueften", "weiter_lueften"}
        and hi >= 58
        and diff >= AH_CONTINUE
    ):
        return "humidity", 2
    if co2 is not None and (
        co2 >= 1000
        or (
            previous_mode in {"co2_lueften", "co2_abwaegung", "co2_warten", "weiter_lueften"}
            and co2 >= 950
        )
    ):
        return "co2_elevated", 1

    # Warm + humid rooms can be noticeably uncomfortable even below the hard
    # heat-protection layer, but only use ventilation when outdoor air helps.
    if ti >= 26 and hi >= 65 and ta <= ti - 1 and diff >= -AH_NEUTRAL:
        return "humid_heat", 1
    temperature_start = (
        abs(ti - target) >= 1
        and _temperature_moves_toward_target(ti, ta, target)
    )
    temperature_continue = window_open and previous_mode in {
        "kuehlen",
        "erwaermen",
        "weiter_lueften",
    } and (
        (ti > target + 0.2 and ta <= ti - 0.5)
        or (ti < target - 0.2 and ta >= ti + 0.5)
    )
    if temperature_start or temperature_continue:
        return "temperature", 1
    if hours >= 24:
        return "routine", 1
    return "none", 0


def _outdoor_soft_caution(data: RoomInput) -> str | None:
    if data.air_quality == "moderate":
        return "air_quality"
    if data.nina_status == "caution":
        return "air_warning"
    if data.weather_caution:
        return "weather"
    return None


def evaluate_room(data: RoomInput) -> VentilationResult:
    ti, hi, ta = data.indoor_temp, data.indoor_humidity, data.outdoor_temp
    target = data.target_temp
    ahi = absolute_humidity(ti, hi)
    aha = absolute_humidity(ta, data.outdoor_humidity)
    diff = ahi - aha  # positive = outdoor air is drier
    co2 = data.co2
    hours = data.hours_since_airing or 0.0
    previous_mode = data.previous_mode or ""

    co2_critical = co2 is not None and co2 > 2000
    co2_high = co2 is not None and co2 >= 1400
    co2_elevated = co2 is not None and (
        co2 >= 1000
        or (previous_mode in {"co2_lueften", "co2_abwaegung", "co2_warten", "weiter_lueften"} and co2 >= 950)
    )

    surface_rh = surface_relative_humidity(ti, hi, data.surface_temp)
    mold_risk = surface_rh is not None and (
        surface_rh >= 80.0
        or (
            previous_mode in {
                "schimmel_lueften",
                "schimmel_langzeit_lueften",
                "schimmel_warten",
                "schimmel_neutral",
                "weiter_lueften",
            }
            and surface_rh >= 78.0
        )
    )
    mold_persistent = bool(data.mold_persistent and mold_risk)

    need, urgency = _primary_need(
        co2=co2,
        hi=hi,
        ti=ti,
        ta=ta,
        target=target,
        diff=diff,
        mold_risk=mold_risk,
        mold_persistent=mold_persistent,
        hours=hours,
        previous_mode=previous_mode,
        window_open=data.window_open,
    )

    # True external hazards beat ordinary ventilation goals. Poor UBA-LQI air
    # also remains closed: typical indoor CO₂ levels are a ventilation-quality
    # indicator, not a reason to deliberately import substantially polluted air.
    hard_mode: str | None = None
    if data.nina_status == "danger":
        hard_mode = "nina_aussenluftgefahr"
    elif data.weather_danger:
        hard_mode = "wettergefahr"
    elif data.air_quality == "very_poor":
        hard_mode = "luftqualitaet_sehr_schlecht"
    elif data.air_quality == "poor":
        hard_mode = "luftqualitaet_schlecht"

    mode: str
    caution_kind = _outdoor_soft_caution(data)

    if hard_mode is not None:
        mode = hard_mode

    elif need == "co2_critical":
        # Critical CO₂ may justify accepting modest humidity/temperature costs,
        # but official/advisory outdoor hazards keep the recommendation cautious.
        if caution_kind is not None:
            mode = "co2_kritisch_vorsicht"
        elif hi >= 65 and diff <= -2.0:
            mode = "co2_kritisch_vorsicht"
            caution_kind = "humidity"
        elif (
            (ti >= target + 1 and ta >= ti + 5)
            or (ti <= target - 1 and ta <= ti - 8)
        ):
            mode = "co2_kritisch_vorsicht"
            caution_kind = "temperature"
        else:
            mode = "co2_kritisch"

    elif need == "co2_high":
        if caution_kind is not None:
            mode = "co2_abwaegung"
        elif mold_persistent and diff <= -AH_NEUTRAL:
            mode = "co2_warten"
        elif hi >= 65 and diff <= -1.5:
            mode = "co2_warten"
        elif hi >= 60 and diff < -AH_NEUTRAL:
            mode = "co2_abwaegung"
            caution_kind = "humidity"
        elif (
            (ti >= target + 1 and ta >= ti + 5)
            or (ti <= target - 1 and ta <= ti - 8)
        ):
            mode = "co2_abwaegung"
            caution_kind = "temperature"
        else:
            mode = "co2_lueften"

    elif need == "co2_elevated":
        if caution_kind is not None:
            mode = "co2_abwaegung"
        elif mold_persistent and diff <= -AH_NEUTRAL:
            mode = "co2_warten"
        elif hi >= 60 and diff <= -1.0:
            mode = "co2_warten"
        elif diff < -AH_NEUTRAL and hi >= 55:
            mode = "co2_abwaegung"
            caution_kind = "humidity"
        elif (
            (ti >= target + 1 and ta >= ti + 3)
            or (ti <= target - 1 and ta <= ti - 6)
        ):
            mode = "co2_abwaegung"
            caution_kind = "temperature"
        else:
            mode = "co2_lueften"

    elif need in {"mold_persistent", "mold"}:
        if diff > AH_NEUTRAL:
            mode = (
                "schimmel_langzeit_lueften"
                if need == "mold_persistent"
                else "schimmel_lueften"
            )
            if caution_kind is not None:
                mode = "komfort_abwaegung"
        elif diff < -AH_NEUTRAL:
            mode = "schimmel_warten"
        else:
            mode = "schimmel_neutral"

    elif need in {"humidity_urgent", "humidity"}:
        humidity_continuation = (
            previous_mode in {"feuchte_lueften", "weiter_lueften"}
            and hi >= 58
            and diff >= AH_CONTINUE
        )
        if diff > AH_NEUTRAL or humidity_continuation:
            mode = "feuchte_lueften"
            if caution_kind is not None:
                mode = "komfort_abwaegung"
        elif diff < -AH_NEUTRAL:
            mode = "feuchte_warten"
        else:
            mode = "feuchte_neutral"

    elif need in {"heat", "humid_heat", "temperature"}:
        temperature_help = _temperature_moves_toward_target(ti, ta, target) or (
            need == "heat" and ta <= ti - 1
        )
        if not temperature_help:
            mode = "normal"
        elif caution_kind is not None:
            # Comfort-only gains do not justify knowingly importing moderate
            # air pollution or opening into an active warning situation.
            mode = (
                "luftqualitaet_maessig"
                if caution_kind == "air_quality"
                else ("nina_vorsicht" if caution_kind == "air_warning" else "wetter_vorsicht")
            )
        elif diff < -1.0 and hi >= 55:
            mode = "komfort_abwaegung"
            caution_kind = "humidity"
        elif ta < ti:
            mode = "kuehlen"
        else:
            mode = "erwaermen"

    elif need == "routine":
        routine_bad = (
            caution_kind is not None
            or diff < -AH_NEUTRAL
            or hi < 40 and diff > AH_NEUTRAL
            or _temperature_moves_away(ti, ta, target)
        )
        mode = "routine_warten" if routine_bad else "routine_lueften"

    else:
        # No ventilation need: only show yellow when opening would be essentially
        # neutral. Any meaningful downside makes red exactly as the UI defines it.
        if data.air_quality == "moderate":
            mode = "luftqualitaet_maessig"
        elif data.nina_status == "caution":
            mode = "nina_vorsicht"
        elif data.weather_caution:
            mode = "wetter_vorsicht"
        elif (hi < 40 and diff > AH_NEUTRAL) or (
            previous_mode == "innen_zu_trocken"
            and hi < 42
            and diff >= AH_CONTINUE
        ):
            mode = "innen_zu_trocken"
        elif diff < -AH_NEUTRAL:
            mode = "aussen_deutlich_feuchter"
        elif _temperature_moves_away(ti, ta, target):
            mode = "aussen_zu_warm" if ta > ti else "aussen_zu_kalt"
        else:
            mode = "normal"

    # Rain is a practical window-opening disadvantage, never a proxy for
    # moisture physics. Only near-term rain that can overlap the actual airing
    # is relevant. Strong reasons can still justify a short exchange.
    rain_relevant = _rain_relevant(data, mode, ta)
    if hard_mode is None and rain_relevant:
        if mode == "co2_kritisch":
            # Light/current rain does not erase a very strong indoor-air need.
            # Keep green but use a short, explicit rain reason.
            mode = "co2_kritisch"
            caution_kind = "rain"
        elif mode in {"co2_lueften", "feuchte_lueften", "schimmel_lueften", "schimmel_langzeit_lueften", "kuehlen", "erwaermen", "routine_lueften"}:
            if urgency >= 2:
                mode = "co2_abwaegung" if need.startswith("co2") else "komfort_abwaegung"
                caution_kind = "rain"
            else:
                mode = "komfort_abwaegung"
                caution_kind = "rain"
        elif mode == "normal":
            mode = "regen" if data.rain_now else "regen_bald"

    # If a window is already open, keep green goals going, mark a finished
    # neutral session as done, and preserve red/yellow trade-off modes so the
    # user sees why closing may now be sensible.
    if data.window_open:
        if _color(mode) == "green":
            continue_co2 = co2 is not None and (
                co2 >= 1000 or (previous_mode == "weiter_lueften" and co2 >= 950)
            )
            continue_moisture = (
                (hi >= 60 and diff > AH_NEUTRAL)
                or (
                    previous_mode == "weiter_lueften"
                    and hi >= 58
                    and diff >= AH_CONTINUE
                )
                or (mold_risk and diff > AH_NEUTRAL)
            )
            # Once temperature-driven airing has started, keep it active until
            # the personal target is effectively reached. A small 0.2 K margin
            # avoids flicker from sensor noise while preventing the old behaviour
            # where cooling was declared finished noticeably above target.
            continue_cooling = ti > target + 0.2 and ta <= ti - 0.5
            continue_warming = ti < target - 0.2 and ta >= ti + 0.5 and ta <= target + 4
            if continue_co2 or continue_moisture or continue_cooling or continue_warming:
                mode = "weiter_lueften"
            else:
                mode = "lueftung_fertig"
        elif mode == "normal" or (
            need == "none"
            and previous_mode in {
                "co2_lueften",
                "feuchte_lueften",
                "schimmel_lueften",
                "schimmel_langzeit_lueften",
                "kuehlen",
                "erwaermen",
                "weiter_lueften",
            }
            and mode in {
                "aussen_zu_kalt",
                "aussen_zu_warm",
                "aussen_deutlich_feuchter",
                "innen_zu_trocken",
            }
        ):
            # The active ventilation goal has been reached. A now-unfavourable
            # outdoor condition is a reason to finish, not a reason to make the
            # session look as if airing had suddenly become a failure.
            mode = "lueftung_fertig"

    color = _color(mode)
    recommendation_key = _recommendation_key(color, mode, data.window_open)
    original_reason: str | None = None

    if mode == "nina_aussenluftgefahr":
        reason_key = data.nina_reason_key or "nina_air_danger"
        reason_args = dict(data.nina_reason_args)
        original_reason = data.nina_original_reason
    elif mode == "nina_vorsicht":
        reason_key = data.nina_reason_key or "nina_air_caution"
        reason_args = dict(data.nina_reason_args)
        original_reason = data.nina_original_reason
    elif mode == "wettergefahr":
        reason_key = data.weather_reason_key or "weather_danger"
        reason_args = dict(data.weather_reason_args)
        original_reason = data.weather_original_reason
    elif mode == "wetter_vorsicht":
        reason_key = data.weather_reason_key or "weather_caution"
        reason_args = dict(data.weather_reason_args)
        original_reason = data.weather_original_reason
    elif mode in {"luftqualitaet_maessig", "luftqualitaet_schlecht", "luftqualitaet_sehr_schlecht"}:
        reason_key = {
            "luftqualitaet_maessig": "air_quality_moderate",
            "luftqualitaet_schlecht": "air_quality_poor",
            "luftqualitaet_sehr_schlecht": "air_quality_very_poor",
        }[mode]
        reason_args = {
            "pollutant": data.air_quality_pollutant,
            "value": data.air_quality_value,
            "co2": co2,
        }
    elif mode == "weiter_lueften":
        reason_key = "continue_airing"
        reason_args = {
            "continue_co2": co2 is not None and co2 >= 950,
            "continue_moisture": (
                (hi >= 60 and diff > AH_NEUTRAL)
                or (previous_mode == "weiter_lueften" and hi >= 58 and diff >= AH_CONTINUE)
                or (mold_risk and diff > AH_NEUTRAL)
            ),
            "continue_cooling": ti > target + 0.2 and ta <= ti - 0.5,
            "continue_warming": ti < target - 0.2 and ta >= ti + 0.5,
            "co2": co2,
            "diff": diff,
            "ti": ti,
            "target": target,
        }
    elif mode == "lueftung_fertig":
        reason_key, reason_args = "airing_finished", {}
    elif mode == "co2_kritisch":
        if caution_kind == "rain":
            reason_key, reason_args = "co2_critical_rain", {"co2": co2}
        else:
            reason_key, reason_args = "co2_critical", {"co2": co2}
    elif mode in {"co2_kritisch_vorsicht", "co2_abwaegung"}:
        reason_key = "co2_tradeoff"
        reason_args = {
            "co2": co2,
            "caution": caution_kind or "conditions",
            "diff": diff,
            "ti": ti,
            "ta": ta,
            "air_quality": data.air_quality,
        }
    elif mode == "co2_lueften":
        reason_key, reason_args = "co2_ventilate", {"co2": co2}
    elif mode == "co2_warten":
        reason_key, reason_args = "co2_wait", {"co2": co2, "diff": diff}
    elif mode == "schimmel_langzeit_lueften":
        reason_key = "surface_moisture_persistent_ventilate"
        reason_args = {
            "surface_humidity": surface_rh,
            "current_minutes": data.mold_current_critical_minutes,
            "minutes_24h": data.mold_critical_minutes_24h,
            "diff": diff,
        }
    elif mode == "schimmel_lueften":
        # Short-term surface protection stays intentionally low-key; this is not
        # worded as a mould diagnosis.
        reason_key = "surface_moisture_ventilate"
        reason_args = {"surface_humidity": surface_rh, "diff": diff}
    elif mode == "schimmel_warten":
        reason_key = "surface_moisture_wait"
        reason_args = {
            "surface_humidity": surface_rh,
            "persistent": mold_persistent,
            "current_minutes": data.mold_current_critical_minutes,
        }
    elif mode == "schimmel_neutral":
        reason_key = "surface_moisture_neutral"
        reason_args = {"surface_humidity": surface_rh}
    elif mode == "feuchte_lueften":
        reason_key, reason_args = "humidity_ventilate", {"humidity": hi, "diff": diff}
    elif mode == "feuchte_warten":
        reason_key, reason_args = "humidity_wait", {"humidity": hi, "diff": diff}
    elif mode == "feuchte_neutral":
        reason_key, reason_args = "humidity_neutral", {"humidity": hi, "diff": diff}
    elif mode == "komfort_abwaegung":
        reason_key = "comfort_tradeoff"
        reason_args = {
            "need": need,
            "caution": caution_kind or "conditions",
            "humidity": hi,
            "diff": diff,
            "ti": ti,
            "ta": ta,
            "target": target,
            "surface_humidity": surface_rh,
        }
    elif mode == "kuehlen":
        reason_key, reason_args = "cooling", {
            "ti": ti,
            "target": target,
            "ta": ta,
            "health_heat": ti >= 30,
        }
    elif mode == "erwaermen":
        reason_key, reason_args = "warming", {"ti": ti, "target": target, "ta": ta}
    elif mode == "routine_lueften":
        reason_key, reason_args = "routine_ventilate", {"hours": hours}
    elif mode == "routine_warten":
        reason_key, reason_args = "routine_wait", {"hours": hours}
    elif mode == "aussen_zu_warm":
        reason_key, reason_args = "outside_too_hot", {"ti": ti, "ta": ta, "target": target}
    elif mode == "aussen_zu_kalt":
        reason_key, reason_args = "outside_too_cold", {"ti": ti, "ta": ta, "target": target}
    elif mode == "aussen_deutlich_feuchter":
        reason_key, reason_args = "outside_more_humid", {"amount": abs(diff)}
    elif mode == "innen_zu_trocken":
        reason_key, reason_args = "inside_too_dry", {"humidity": hi, "diff": diff}
    elif mode == "regen":
        reason_key = data.weather_reason_key or "rain_now"
        reason_args = dict(data.weather_reason_args)
        original_reason = data.weather_original_reason
    elif mode == "regen_bald":
        reason_key, reason_args = "rain_soon", {"minutes": data.rain_minutes_until}
    else:
        reason_key, reason_args = "normal", {}

    return VentilationResult(
        color=color,
        mode=mode,
        recommendation_key=recommendation_key,
        reason_key=reason_key,
        reason_args=reason_args,
        duration_key=_duration_key(mode, ta),
        duration_args={},
        original_reason=original_reason,
        indoor_absolute_humidity=round(ahi, 2),
        outdoor_absolute_humidity=round(aha, 2),
        absolute_humidity_difference=round(diff, 2),
        co2_status=co2_status(co2),
        surface_relative_humidity=(round(surface_rh, 1) if surface_rh is not None else None),
        mold_risk=mold_risk,
        mold_persistent=mold_persistent,
        mold_current_critical_minutes=(
            round(data.mold_current_critical_minutes, 1)
            if data.mold_current_critical_minutes is not None
            else None
        ),
        mold_critical_minutes_24h=(
            round(data.mold_critical_minutes_24h, 1)
            if data.mold_critical_minutes_24h is not None
            else None
        ),
        air_quality=data.air_quality,
        air_quality_pollutant=data.air_quality_pollutant,
        air_quality_value=data.air_quality_value,
    )

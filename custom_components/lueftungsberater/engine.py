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
TEMP_NEED_ON = 1.0
TEMP_NEED_OFF = 0.6


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
    if mode in {"co2_lueften", "co2_lueften_mit_nachteil"}:
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
        "co2_lueften_mit_nachteil",
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
    if mode in {
        "nina_vorsicht",
        "wetter_vorsicht",
        "luftqualitaet_maessig",
        "luftqualitaet_schlecht",
        "luftqualitaet_sehr_schlecht_typisch",
        "co2_warten",
        "schimmel_warten",
        "feuchte_warten",
        "routine_warten",
        "aussen_zu_warm",
        "aussen_zu_kalt",
        "aussen_deutlich_feuchter",
        "innen_zu_trocken",
        "regen",
        "regen_bald",
    }:
        return "orange"
    # Red is now reserved for a genuinely strong keep-closed reason: an explicit
    # outdoor-air danger, severe weather, very poor air quality, or another hard
    # safety/health constraint.
    return "red"


def _recommendation_key(color: str, mode: str, window_open: bool) -> str:
    if color == "green":
        return "keep_open" if window_open else "open_now"
    if color == "red":
        return "close_now" if window_open else "keep_closed"
    if color == "orange":
        return "better_close" if window_open else "caution_keep_closed"
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
    previous_need: str,
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
    temperature_delta = abs(ti - target)
    temperature_hysteresis = previous_need == "temperature"
    temperature_start = (
        temperature_delta >= (TEMP_NEED_OFF if temperature_hysteresis else TEMP_NEED_ON)
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


def _air_quality_penalty(data: RoomInput) -> int:
    """Return an outdoor-air disadvantage without changing the UBA class.

    0 = none, 1 = mild, 2 = strong, 3 = unusually/severely strong. A location
    where poor air is unfortunately typical stays medically "poor"; local
    history only prevents every ordinary day there from looking like an acute
    exceptional event.
    """
    if data.air_quality in {"unknown", "very_good", "good"}:
        return 0
    if data.air_quality == "moderate":
        return 1
    if data.air_quality == "poor":
        if data.air_quality_unusual or data.air_quality_trend == "rising":
            return 3
        return 2
    if data.air_quality == "very_poor":
        if data.air_quality_typical is True and not data.air_quality_unusual and data.air_quality_trend != "rising":
            return 2
        return 3
    return 0


def _outdoor_soft_caution(data: RoomInput) -> str | None:
    if _air_quality_penalty(data) > 0:
        return "air_quality"
    if data.nina_status == "caution":
        return "air_warning"
    if data.weather_caution:
        return "weather"
    return None


def _co2_outdoor_limited(data: RoomInput) -> bool:
    """Return whether measured outdoor CO2 offers very little reduction.

    The 100 ppm band is only a technical sensor/noise guard. It is not a health
    threshold and it never turns an extreme indoor value into "good".
    """
    if data.co2 is None or data.outdoor_co2 is None:
        return False
    return data.outdoor_co2 >= data.co2 - 100.0


def _room_status_color(urgency: int, ventilation_color: str) -> str:
    """Return the optional room-status colour without creating unsafe meanings.

    In room-status mode red must *always* mean that airing is urgently useful.
    If the normal ventilation decision is a trade-off or recommends keeping the
    window closed, an indoor problem is therefore capped at orange/yellow. A
    true outside protection reason is rendered separately as ``locked`` by the
    UI and never reuses red for the opposite action.
    """
    if ventilation_color == "green":
        if urgency >= 3:
            return "red"
        if urgency >= 2:
            return "orange"
        if urgency >= 1:
            return "yellow"
        return "green"

    if ventilation_color == "yellow":
        if urgency >= 2:
            return "orange"
        if urgency >= 1:
            return "yellow"
        return "green"

    # When airing is currently disadvantageous, never show red in room-status
    # mode: a user who chose this view learns red as "air now".
    if urgency >= 2:
        return "orange"
    if urgency >= 1:
        return "yellow"
    return "green"


def _temperature_drawback(ti: float, ta: float, target: float) -> float:
    if not _temperature_moves_away(ti, ta, target):
        return 0.0
    return abs(ta - ti)


def _strong_no_need_disadvantage(
    *, ti: float, hi: float, ta: float, target: float, diff: float
) -> bool:
    """Detect a clearly bad combination, never from temperature alone at 10 K.

    This keeps the user's agreed behaviour: a 5 K mismatch is normally orange;
    around 10 K can become red only when another meaningful disadvantage points
    the same way. An extreme ~18 K move away from an already good target is
    strong enough on its own.
    """
    gap = _temperature_drawback(ti, ta, target)
    if gap >= 18.0:
        return True
    if gap < 10.0:
        return False
    wetter_when_not_needed = diff <= -1.5 and hi >= 45.0
    drier_when_not_needed = diff >= 1.5 and hi <= 45.0
    return wetter_when_not_needed or drier_when_not_needed


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
        previous_need=data.previous_need or "",
        window_open=data.window_open,
    )

    # A true protection instruction is outside the normal four-colour scale.
    # The result still carries red for backwards compatibility, while
    # safety_lock lets the UI render a separate lock state in either display
    # mode. Poor measured air quality is a strong disadvantage, not by itself a
    # hard lock instruction.
    hard_mode: str | None = None
    if data.nina_status == "danger":
        hard_mode = "nina_aussenluftgefahr"
    elif data.weather_danger:
        hard_mode = "wettergefahr"

    mode: str
    caution_kind = _outdoor_soft_caution(data)
    air_penalty = _air_quality_penalty(data)
    temp_drawback = _temperature_drawback(ti, ta, target)
    humidity_drawback = diff < -AH_NEUTRAL
    humidity_drawback_strong = diff <= -1.5
    outdoor_co2_limited = _co2_outdoor_limited(data)

    if hard_mode is not None:
        mode = hard_mode

    elif need == "co2_critical":
        # Critical indoor CO2 justifies accepting ordinary heat/moisture costs,
        # but not a protection warning. Strong wind/moderate pollution stays a
        # visible trade-off. Extremely bad combinations also remain cautious.
        if air_penalty >= 2 or data.nina_status == "caution" or data.weather_caution:
            mode = "co2_kritisch_vorsicht"
            caution_kind = caution_kind or "conditions"
        elif outdoor_co2_limited:
            mode = "co2_kritisch_vorsicht"
            caution_kind = "outdoor_co2"
        elif humidity_drawback and diff <= -3.0 and hi >= 65:
            mode = "co2_kritisch_vorsicht"
            caution_kind = "humidity"
        elif temp_drawback >= 15.0:
            mode = "co2_kritisch_vorsicht"
            caution_kind = "temperature"
        else:
            mode = "co2_kritisch"

    elif need == "co2_high":
        if air_penalty >= 2 or data.nina_status == "caution" or data.weather_caution:
            mode = "co2_abwaegung"
            caution_kind = caution_kind or "conditions"
        elif outdoor_co2_limited:
            mode = "co2_warten"
            caution_kind = "outdoor_co2"
        elif mold_persistent and humidity_drawback:
            mode = "co2_warten"
        elif co2 is not None and co2 >= 1700:
            # Agreed test behaviour: around 1800 ppm the indoor-air benefit can
            # outweigh a ~9 K and ~1 g/m³ outdoor disadvantage. The reason still
            # mentions that trade-off instead of pretending outside is ideal.
            if temp_drawback >= 15.0 or (humidity_drawback_strong and hi >= 65):
                mode = "co2_abwaegung"
                caution_kind = "temperature" if temp_drawback >= 15.0 else "humidity"
            elif temp_drawback >= 3.0 or humidity_drawback:
                mode = "co2_lueften_mit_nachteil"
                caution_kind = "temperature" if temp_drawback >= 3.0 else "humidity"
            else:
                mode = "co2_lueften"
        elif hi >= 65 and humidity_drawback_strong:
            mode = "co2_warten"
        elif (hi >= 60 and humidity_drawback) or temp_drawback >= 5.0:
            mode = "co2_abwaegung"
            caution_kind = "humidity" if hi >= 60 and humidity_drawback else "temperature"
        else:
            mode = "co2_lueften"

    elif need == "co2_elevated":
        if air_penalty >= 2 or data.nina_status == "caution" or data.weather_caution:
            mode = "co2_warten" if air_penalty >= 2 else "co2_abwaegung"
            caution_kind = caution_kind or "conditions"
        elif outdoor_co2_limited:
            mode = "co2_warten"
            caution_kind = "outdoor_co2"
        elif mold_persistent and humidity_drawback:
            mode = "co2_warten"
        elif temp_drawback >= 6.0 and humidity_drawback:
            # Agreed case: ~1250 ppm does not justify importing markedly hotter
            # and wetter air when the room is otherwise comfortable.
            mode = "co2_warten"
            caution_kind = "combined"
        elif hi >= 60 and diff <= -1.0:
            mode = "co2_warten"
            caution_kind = "humidity"
        elif humidity_drawback or temp_drawback >= 3.0:
            mode = "co2_abwaegung"
            caution_kind = "humidity" if humidity_drawback else "temperature"
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
        # No ventilation need: yellow is genuinely neutral, orange means a
        # meaningful downside, and red is reserved for a clearly strong
        # combination. UBA-LQI stays absolute; local history only distinguishes
        # ordinary local pollution from an unusually bad episode.
        if data.air_quality == "very_poor":
            mode = (
                "luftqualitaet_sehr_schlecht_typisch"
                if air_penalty == 2
                else "luftqualitaet_sehr_schlecht"
            )
        elif data.air_quality == "poor":
            mode = "luftqualitaet_schlecht"
        elif data.air_quality == "moderate":
            mode = "luftqualitaet_maessig"
        elif data.nina_status == "caution":
            mode = "nina_vorsicht"
        elif data.weather_caution:
            mode = "wetter_vorsicht"
        elif _strong_no_need_disadvantage(ti=ti, hi=hi, ta=ta, target=target, diff=diff):
            mode = "aussen_stark_unpassend"
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

    # CO₂-driven airing gets its own closing hysteresis. If a session started
    # because indoor CO₂ was clearly high, ordinary heat/moisture drawbacks do
    # not suddenly flip the card to orange halfway through. As CO₂ approaches
    # the good range we move through yellow, then after the window is closed the
    # normal outdoor disadvantages can become orange again.
    co2_airing_modes = {
        "co2_kritisch",
        "co2_lueften",
        "co2_lueften_mit_nachteil",
        "weiter_lueften",
    }
    if (
        data.window_open
        and hard_mode is None
        and previous_mode in co2_airing_modes
        and co2 is not None
        and air_penalty < 2
        and data.nina_status != "caution"
        and not data.weather_caution
        and not outdoor_co2_limited
    ):
        if co2 < 950:
            mode = "lueftung_fertig"
        elif co2 < 1100:
            mode = "co2_abwaegung"
            caution_kind = "near_target"
        elif co2 >= 1100:
            mode = "weiter_lueften"

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
    elif mode in {"luftqualitaet_maessig", "luftqualitaet_schlecht", "luftqualitaet_sehr_schlecht", "luftqualitaet_sehr_schlecht_typisch"}:
        reason_key = {
            "luftqualitaet_maessig": "air_quality_moderate",
            "luftqualitaet_schlecht": "air_quality_poor",
            "luftqualitaet_sehr_schlecht": "air_quality_very_poor",
            "luftqualitaet_sehr_schlecht_typisch": "air_quality_very_poor",
        }[mode]
        reason_args = {
            "pollutant": data.air_quality_pollutant,
            "value": data.air_quality_value,
            "co2": co2,
            "baseline": data.air_quality_baseline_value,
            "typical": data.air_quality_typical,
            "unusual": data.air_quality_unusual,
            "trend": data.air_quality_trend,
            "history_samples": data.air_quality_history_samples,
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
            "outdoor_co2": data.outdoor_co2,
            "air_quality_baseline": data.air_quality_baseline_value,
            "air_quality_typical": data.air_quality_typical,
            "air_quality_unusual": data.air_quality_unusual,
            "air_quality_trend": data.air_quality_trend,
        }
    elif mode == "co2_lueften_mit_nachteil":
        reason_key = "co2_ventilate_tradeoff"
        reason_args = {
            "co2": co2,
            "caution": caution_kind or "conditions",
            "diff": diff,
            "ti": ti,
            "ta": ta,
            "outdoor_co2": data.outdoor_co2,
        }
    elif mode == "co2_lueften":
        reason_key, reason_args = "co2_ventilate", {
            "co2": co2,
            "outdoor_co2": data.outdoor_co2,
        }
    elif mode == "co2_warten":
        reason_key, reason_args = "co2_wait", {
            "co2": co2,
            "diff": diff,
            "caution": caution_kind,
            "outdoor_co2": data.outdoor_co2,
            "ti": ti,
            "ta": ta,
        }
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
    elif mode == "aussen_stark_unpassend":
        reason_key, reason_args = "outside_strongly_unhelpful", {
            "ti": ti, "ta": ta, "target": target, "diff": diff, "humidity": hi
        }
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
        room_status_color=_room_status_color(urgency, color),
        primary_need=need,
        safety_lock=hard_mode is not None,
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
        outdoor_co2=data.outdoor_co2,
        co2_difference=(round(co2 - data.outdoor_co2, 0) if co2 is not None and data.outdoor_co2 is not None else None),
        air_quality_baseline_value=data.air_quality_baseline_value,
        air_quality_typical=data.air_quality_typical,
        air_quality_unusual=data.air_quality_unusual,
        air_quality_trend=data.air_quality_trend,
        air_quality_history_samples=data.air_quality_history_samples,
    )

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


def _previous_co2_context(previous_mode: str, previous_need: str) -> bool:
    return previous_need in {"co2_elevated", "co2_high", "co2_critical"} or previous_mode in {
        "co2_kritisch",
        "co2_kritisch_vorsicht",
        "co2_lueften",
        "co2_lueften_mit_nachteil",
        "co2_abwaegung",
        "co2_warten",
    }


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
    if mode in {"co2_mindestlueftung", "co2_mindestlueftung_vorsicht"}:
        return "co2_minimum"
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


def _co2_session_target_for_decision(
    *,
    need: str,
    mode: str,
    co2: float | None,
    temp_drawback: float,
    humidity_drawback: bool,
    humidity_drawback_strong: bool,
    indoor_humidity: float,
    caution_kind: str | None,
) -> float | None:
    """Choose the CO₂ finish target from the situation that caused the advice.

    This is deliberately not based only on the current ppm. If outdoor
    conditions are good enough that the advisor would already have recommended
    airing around 1000 ppm, a user who waited until 1500 ppm still gets the
    normal 850 ppm target. If the outdoor trade-off only made airing worthwhile
    from a higher decision band, the target moves up with that band.
    """
    if need not in {"co2_elevated", "co2_high", "co2_critical"}:
        return None
    if mode not in {
        "co2_kritisch",
        "co2_kritisch_vorsicht",
        "co2_lueften",
        "co2_lueften_mit_nachteil",
        "co2_abwaegung",
    }:
        return None

    if need == "co2_elevated":
        return 850.0

    if need == "co2_high":
        # With genuinely good outside conditions the elevated 1000-ppm band
        # would already have produced a green CO₂ recommendation. Keep the
        # original 850-ppm finish target even if the user opened later.
        if (
            mode == "co2_lueften"
            and not humidity_drawback
            and temp_drawback < 3.0
        ):
            return 850.0

        # The explicit >=1700-ppm override is used when a stronger outdoor
        # disadvantage had to be accepted. Preserve the same 150-ppm buffer.
        if co2 is not None and co2 >= 1700.0 and mode in {
            "co2_lueften_mit_nachteil",
            "co2_abwaegung",
        }:
            return 1550.0
        return 1250.0

    # Critical CO₂: if outside was genuinely good, the advisor would already
    # have wanted airing from the 1000-ppm band, so do not reward a late opening
    # with an artificially high target. Ordinary drawbacks use the 1700 band;
    # only a genuinely critical/cautious trade-off uses 2000 -> 1850 ppm.
    if mode == "co2_kritisch" and caution_kind is None:
        if not humidity_drawback and temp_drawback < 3.0:
            return 850.0
        if temp_drawback < 15.0 and not (
            humidity_drawback_strong and indoor_humidity >= 65.0
        ):
            return 1550.0
    return 1850.0


def _color(mode: str) -> str:
    if mode in {
        "co2_kritisch",
        "co2_lueften",
        "co2_lueften_mit_nachteil",
        "co2_mindestlueftung",
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
        "co2_mindestlueftung_vorsicht",
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
    if mode in {
        "co2_kritisch_vorsicht",
        "co2_abwaegung",
        "co2_mindestlueftung_vorsicht",
        "komfort_abwaegung",
    }:
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
    co2_pending_hold: bool,
    co2_airing_active: bool,
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
            _previous_co2_context(previous_mode, previous_need)
            and co2 >= 900
        )
        or co2_pending_hold
        or co2_airing_active
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


def _room_display_urgency(need: str, data: RoomInput) -> int:
    """Return display urgency for the inverted room-air perspective.

    This does *not* decide whether to ventilate. The actual engine decision has
    already considered all indoor and outdoor inputs. This level only translates
    that decision into the optional "green = fine / red = air now" view.
    Slight deviations therefore stay deliberately calm when the outdoor side is
    clearly unsuitable, while stronger indoor needs can progressively overcome
    that visual calm.
    """
    co2 = data.co2
    if need == "co2_critical":
        return 3
    if need == "co2_high":
        return 3 if co2 is not None and co2 >= 1800 else 2
    if need == "co2_elevated":
        return 1
    if need == "heat":
        return 3
    if need == "mold_persistent":
        return 3
    if need == "mold":
        return 2
    if need == "humidity_urgent":
        return 3 if data.indoor_humidity >= 75 else 2
    if need == "humidity":
        # Around the normal 60 % edge this is intentionally only a mild signal.
        # It must not turn a room with otherwise good values orange merely
        # because outdoor air is even less suitable (the v0.7.5 double-orange
        # problem).
        return 1 if data.indoor_humidity < 63 else 2
    if need == "humid_heat":
        return 2
    if need == "temperature":
        return 2 if abs(data.indoor_temp - data.target_temp) >= 3.0 else 1
    if need == "routine":
        return 1
    return 0


def _room_status_color(urgency: int, ventilation_color: str) -> str:
    """Translate the final ventilation judgement into the room-air colour view.

    The two traffic-light modes are perspectives on one shared engine decision,
    not two independent decision engines. Green ventilation conditions expose
    indoor urgency directly. When ventilation is a trade-off or clearly
    disadvantageous, mild indoor deviations remain green and stronger needs
    climb gradually through yellow/orange. Red is only used when the room need
    is severe *and* the actual ventilation decision is green. Hard official
    protection instructions are rendered separately as ``locked`` by the UI.
    """
    urgency = max(0, min(3, int(urgency)))
    if ventilation_color == "green":
        return ("green", "yellow", "orange", "red")[urgency]

    if ventilation_color == "yellow":
        if urgency >= 3:
            return "orange"
        if urgency >= 1:
            return "yellow"
        return "green"

    # Outdoor conditions currently argue against opening. A small indoor
    # deviation is therefore still a green "no useful pressure to act" state;
    # only a stronger indoor need moves the inverted view upward.
    if urgency >= 3:
        return "orange"
    if urgency >= 2:
        return "yellow"
    return "green"


def _room_recommendation_key(color: str, window_open: bool) -> str:
    if window_open:
        if color == "green":
            return "can_close"
        if color == "yellow":
            return "room_keep_brief"
        return "keep_open"
    return {
        "green": "room_good",
        "yellow": "room_watch",
        "orange": "room_need",
        "red": "room_urgent",
    }.get(color, "room_watch")


def _temperature_drawback(ti: float, ta: float, target: float) -> float:
    if not _temperature_moves_away(ti, ta, target):
        return 0.0
    return abs(ta - ti)


def co2_outdoor_context(data: RoomInput) -> dict[str, int | bool]:
    """Return coarse outdoor-disadvantage bands for a running CO₂ airing.

    The bands intentionally reuse thresholds that already influence the normal
    engine. They are not a second decision system; they only let the coordinator
    distinguish an already accepted drawback from a genuinely new worsening
    while the five-minute minimum airing phase is active.
    """
    indoor_ah = absolute_humidity(data.indoor_temp, data.indoor_humidity)
    outdoor_ah = absolute_humidity(data.outdoor_temp, data.outdoor_humidity)
    diff = indoor_ah - outdoor_ah
    temp_drawback = _temperature_drawback(
        data.indoor_temp, data.outdoor_temp, data.target_temp
    )

    temperature = 0
    if temp_drawback >= 15.0:
        temperature = 3
    elif temp_drawback >= 5.0:
        temperature = 2
    elif temp_drawback >= 3.0:
        temperature = 1

    humidity = 0
    if diff <= -3.0:
        humidity = 4
    elif diff <= -1.5:
        humidity = 3
    elif diff <= -1.0:
        humidity = 2
    elif diff < -AH_NEUTRAL:
        humidity = 1

    outdoor_co2 = 0
    if data.outdoor_co2 is not None:
        if data.outdoor_co2 >= 1200:
            outdoor_co2 = 3
        elif data.outdoor_co2 >= 1000:
            outdoor_co2 = 2
        elif data.outdoor_co2 >= 800:
            outdoor_co2 = 1

    rain = bool(data.rain_now)
    if not rain and data.rain_minutes_until is not None:
        rain = 0 <= data.rain_minutes_until <= 15
    if not rain:
        rain = bool(data.rain_soon)

    temp_direction = "neutral"
    if temp_drawback > 0:
        temp_direction = "hot" if data.outdoor_temp > data.indoor_temp else "cold"

    return {
        "temperature": temperature,
        "outdoor_temp": round(float(data.outdoor_temp), 2),
        "temperature_direction": temp_direction,
        "humidity": humidity,
        "outdoor_absolute_humidity": round(float(outdoor_ah), 2),
        "air_quality": _air_quality_penalty(data),
        "outdoor_co2": outdoor_co2,
        "nina_caution": data.nina_status == "caution",
        "weather_caution": bool(data.weather_caution),
        "rain": rain,
    }


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
    previous_need = data.previous_need or ""

    co2_critical = co2 is not None and co2 > 2000
    co2_high = co2 is not None and co2 >= 1400
    co2_elevated = co2 is not None and (
        co2 >= 1000
        or (_previous_co2_context(previous_mode, previous_need) and co2 >= 900)
        or data.co2_pending_hold
        or data.co2_airing_active
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
        previous_need=previous_need,
        window_open=data.window_open,
        co2_pending_hold=data.co2_pending_hold,
        co2_airing_active=data.co2_airing_active,
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

    co2_session_target = _co2_session_target_for_decision(
        need=need,
        mode=mode,
        co2=co2,
        temp_drawback=temp_drawback,
        humidity_drawback=humidity_drawback,
        humidity_drawback_strong=humidity_drawback_strong,
        indoor_humidity=hi,
        caution_kind=caution_kind,
    )

    # CO₂-driven airing is treated as an explicit user session, not as a fresh
    # threshold decision on every sensor update. The finish target is fixed when
    # the user starts airing and follows the CO₂ band that justified the action:
    # normally 850 ppm, 1250 ppm for a 1400-ppm high-band start, 1550 ppm when
    # the >=1700 trade-off override was needed, and 1850 ppm for a critical start.
    # The last 50 ppm above that target are shown as a yellow near-target band.
    if (
        data.window_open
        and hard_mode is None
        and data.co2_airing_active
        and co2 is not None
        and air_penalty < 2
        and data.nina_status != "caution"
        and not data.weather_caution
        and not outdoor_co2_limited
    ):
        finish_target = data.co2_finish_target or 850.0
        near_target = data.co2_near_target or (finish_target + 50.0)
        if data.co2_finish_ready:
            mode = "lueftung_fertig"
        elif co2 <= near_target:
            mode = "co2_abwaegung"
            caution_kind = "near_target"
        else:
            mode = "weiter_lueften"

    # If the user followed an actual CO₂ recommendation, give that airing
    # at least five minutes before a fast indoor CO₂ drop is allowed to finish
    # the session. The coordinator only sets this flag while the outdoor
    # situation has not entered a newly worse category; hard locks were already
    # handled above and therefore always win immediately.
    if (
        data.window_open
        and hard_mode is None
        and data.co2_minimum_airing_active
    ):
        mode = (
            "co2_mindestlueftung_vorsicht"
            if data.co2_minimum_airing_cautious
            else "co2_mindestlueftung"
        )
        caution_kind = "minimum_airing"

    # If a window is already open, keep green goals going, mark a finished
    # neutral session as done, and preserve red/yellow trade-off modes so the
    # user sees why closing may now be sensible.
    if data.window_open:
        if mode == "co2_mindestlueftung":
            pass
        elif _color(mode) == "green":
            continue_co2 = co2 is not None and (
                (not data.co2_finish_ready)
                if data.co2_airing_active
                else co2 >= 1000
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
            "continue_co2": co2 is not None and (
                (not data.co2_finish_ready)
                if data.co2_airing_active
                else co2 >= 1000
            ),
            "continue_moisture": (
                (hi >= 60 and diff > AH_NEUTRAL)
                or (previous_mode == "weiter_lueften" and hi >= 58 and diff >= AH_CONTINUE)
                or (mold_risk and diff > AH_NEUTRAL)
            ),
            "continue_cooling": ti > target + 0.2 and ta <= ti - 0.5,
            "continue_warming": ti < target - 0.2 and ta >= ti + 0.5,
            "co2": co2,
            "co2_target": data.co2_finish_target,
            "diff": diff,
            "ti": ti,
            "target": target,
        }
    elif mode == "lueftung_fertig":
        reason_key, reason_args = "airing_finished", {}
    elif mode in {"co2_mindestlueftung", "co2_mindestlueftung_vorsicht"}:
        reason_key = "co2_minimum_airing"
        reason_args = {
            "co2": co2,
            "co2_target": data.co2_finish_target,
            "cautious": mode == "co2_mindestlueftung_vorsicht",
        }
    elif mode == "co2_kritisch":
        if caution_kind == "rain":
            reason_key, reason_args = "co2_critical_rain", {"co2": co2}
        else:
            reason_key, reason_args = "co2_critical", {"co2": co2}
    elif mode in {"co2_kritisch_vorsicht", "co2_abwaegung"}:
        reason_key = "co2_tradeoff"
        reason_args = {
            "co2": co2,
            "co2_target": data.co2_finish_target,
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

    room_urgency = _room_display_urgency(need, data)
    room_color = _room_status_color(room_urgency, color)
    room_recommendation_key = _room_recommendation_key(room_color, data.window_open)
    room_reason_args = {
        "need": need,
        "level": room_urgency,
        "ventilation_color": color,
        "mode": mode,
        "co2": co2,
        "humidity": hi,
        "ti": ti,
        "ta": ta,
        "target": target,
        "diff": diff,
        "hours": hours,
        "surface_humidity": surface_rh,
        "caution": caution_kind,
        "air_quality": data.air_quality,
        "window_open": data.window_open,
    }

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
        co2_session_target=co2_session_target,
        room_status_color=room_color,
        room_recommendation_key=room_recommendation_key,
        room_reason_key="room_perspective",
        room_reason_args=room_reason_args,
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

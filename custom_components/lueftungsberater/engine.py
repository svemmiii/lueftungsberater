"""Home-Assistant-independent ventilation decision engine.

The engine returns semantic keys plus raw values instead of pre-rendered
language. Decisions deliberately use a hierarchy of evidence instead of a
single additive score: safety/health constraints first, then all active indoor
ventilation needs against the same outdoor conditions, then a combined action.
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

    # Critical CO₂: the visible decision is the source of truth for the session
    # target. A merely soft caveat (for example moderate outdoor air quality)
    # must not silently turn a green critical recommendation into a 1850-ppm
    # finish target. Only an explicitly cautious critical mode uses that band.
    if mode == "co2_kritisch":
        if not humidity_drawback and temp_drawback < 3.0:
            return 850.0
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
        "aussen_co2_hoeher",
        "innen_zu_trocken",
        "regen",
        "regen_bald",
    }:
        return "orange"
    # Red is now reserved for a genuinely strong keep-closed reason: an explicit
    # outdoor-air danger, severe weather, very poor air quality, or another hard
    # safety/health constraint.
    return "red"


_TRADEOFF_MODES = {
    "co2_kritisch_vorsicht",
    "co2_abwaegung",
    "co2_mindestlueftung_vorsicht",
    "komfort_abwaegung",
}


def _action_semantic(mode: str) -> str:
    """Classify what a mode means for the act of opening a window.

    Color alone is not sufficient: yellow is used both for a genuine trade-off
    and for a neutral "airing does not help this reason" state. Keeping those
    meanings separate prevents a neutral secondary need from relaxing an
    existing keep-closed recommendation.
    """
    color = _color(mode)
    if color == "green":
        return "beneficial"
    if color == "red":
        # Hard NINA/weather locks are handled before candidate evaluation. A red
        # candidate here therefore represents a *strong measured disadvantage*
        # (for example unusually very poor outdoor air), not an absolute lock.
        # Keeping that distinction lets critical indoor needs still form a real
        # trade-off without allowing weak comfort reasons to ignore severe air.
        return "strong_harmful"
    if color == "orange":
        return "harmful"
    if mode in _TRADEOFF_MODES:
        return "tradeoff"
    return "neutral"


def _need_protection_level(need: str) -> int:
    """Return a tie-break protection level independent of traffic-light color.

    Urgency remains the primary merge dimension.  This level only resolves
    equally urgent pro/con reasons so a health-relevant surface/mold warning is
    not treated like a comfort drawback, while CO2 and ordinary humidity can
    still form a genuine yellow trade-off at equal urgency.
    """
    if need == "mold_persistent":
        return 3
    if need == "mold":
        return 2
    if need.startswith("co2_") or need in {"humidity_urgent", "humidity"}:
        return 1
    return 0


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


def _short_term_weather_worsening_relevant(
    data: RoomInput, candidate_mode: str, outdoor_temp: float
) -> bool:
    """Return whether the next-hour forecast can overlap the planned airing.

    The hourly forecast is only a soft planning signal. It never creates a
    hard lock, and distant changes are ignored when a short airing would be
    finished well before them.
    """
    if data.short_term_weather_change != "worsening":
        return False
    if data.short_term_weather_minutes is None:
        return False
    lead = float(data.short_term_weather_minutes)
    if lead < 0 or lead > 60:
        return False
    return lead <= _duration_max_minutes(candidate_mode, outdoor_temp) + 5


def _short_term_weather_args(data: RoomInput) -> dict[str, object]:
    """Return compact forecast context for localized one-line explanations."""
    return {
        "forecast_change": data.short_term_weather_change,
        "forecast_kind": data.short_term_weather_kind,
        "forecast_minutes": data.short_term_weather_minutes,
        "forecast_condition": data.short_term_weather_condition,
    }


def _temperature_moves_toward_target(ti: float, ta: float, target: float) -> bool:
    """Return whether airing initially moves room temperature toward target.

    Cooling may use substantially colder outdoor air because the user can stop
    once the target is reached. For warming, however, very hot outdoor air can
    overshoot a small heating need immediately. Use the same +4 K ceiling that
    governs an already running warming session so start and continuation cannot
    contradict each other with unchanged sensor values.
    """
    if ti > target:
        return ta <= ti - 0.7
    if ti < target:
        return ta >= ti + 0.7 and ta <= target + 4.0
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


def _active_needs(
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
    co2_rearm_threshold: float | None,
    consider_co2: bool = True,
) -> list[tuple[str, int]]:
    """Return all currently active indoor needs in deterministic priority order."""
    needs: list[tuple[str, int]] = []
    co2_allowed = consider_co2 and (
        co2_airing_active
        or co2_rearm_threshold is None
        or (co2 is not None and co2 >= co2_rearm_threshold)
    )

    if co2_allowed and co2 is not None and co2 > 2000:
        needs.append(("co2_critical", 3))
    elif co2_allowed and co2 is not None and co2 >= 1400:
        needs.append(("co2_high", 2))
    elif co2_allowed and co2 is not None and (
        co2 >= 1000
        or (_previous_co2_context(previous_mode, previous_need) and co2 >= 900)
        or co2_pending_hold
        or co2_airing_active
    ):
        needs.append(("co2_elevated", 1))

    if ti >= 30 and ta <= ti - 1:
        needs.append(("heat", 3))

    if mold_persistent:
        needs.append(("mold_persistent", 3))
    elif mold_risk:
        needs.append(("mold", 2))

    if hi >= 65:
        needs.append(("humidity_urgent", 2))
    elif hi >= 60 or (
        previous_mode in {"feuchte_lueften", "weiter_lueften"}
        and hi >= 58
        and diff >= AH_CONTINUE
    ):
        needs.append(("humidity", 2))

    if ti >= 26 and hi >= 65 and ta <= ti - 1 and diff >= -AH_NEUTRAL:
        needs.append(("humid_heat", 1))

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
        or (ti < target - 0.2 and ta >= ti + 0.5 and ta <= target + 4.0)
    )
    if temperature_start or temperature_continue:
        needs.append(("temperature", 1))

    # Routine is a fallback, not a peer health/comfort signal. If a concrete
    # indoor need is already active, reaching the 24 h mark must not inject a
    # new candidate that can change the existing multi-need conflict.
    if hours >= 24 and not needs:
        needs.append(("routine", 1))

    # Preserve the previous primary ordering for equal urgency. The ordering is
    # now only a display/tie-break rule; it no longer erases secondary reasons.
    priority = {
        "co2_critical": 0,
        "heat": 1,
        "mold_persistent": 2,
        "humidity_urgent": 3,
        "co2_high": 4,
        "mold": 5,
        "humidity": 6,
        "co2_elevated": 7,
        "humid_heat": 8,
        "temperature": 9,
        "routine": 10,
    }
    needs.sort(key=lambda item: (-item[1], priority.get(item[0], 99)))
    return needs


def _non_co2_mode_for_need(
    *,
    need: str,
    data: RoomInput,
    hi: float,
    ti: float,
    ta: float,
    target: float,
    diff: float,
    previous_mode: str,
) -> tuple[str, str | None]:
    """Evaluate one non-CO₂ need independently against outdoor conditions."""
    caution_kind = _outdoor_soft_caution(data)
    air_quality_mode = _air_quality_mode(data)

    if need in {"mold_persistent", "mold"}:
        if diff > AH_NEUTRAL:
            mode = (
                "schimmel_langzeit_lueften"
                if need == "mold_persistent"
                else "schimmel_lueften"
            )
            if air_quality_mode is not None:
                # Moderate air can remain a real trade-off when airing solves a
                # health-relevant moisture problem. Poor/very-poor AQ retains
                # its actual class and severity instead of being downgraded.
                if data.air_quality == "moderate":
                    mode = "komfort_abwaegung"
                else:
                    mode = air_quality_mode
            elif caution_kind is not None:
                mode = "komfort_abwaegung"
            return mode, caution_kind
        if diff < -AH_NEUTRAL:
            return "schimmel_warten", "humidity"
        return "schimmel_neutral", None

    if need in {"humidity_urgent", "humidity"}:
        continuation = (
            previous_mode in {"feuchte_lueften", "weiter_lueften"}
            and hi >= 58
            and diff >= AH_CONTINUE
        )
        if diff > AH_NEUTRAL or continuation:
            mode = "feuchte_lueften"
            if air_quality_mode is not None:
                # Moderate AQ is only a mild outside disadvantage. If outdoor
                # air is actually dry enough to improve an active humidity need,
                # that mild AQ band must not turn a newly-active moisture reason
                # into a weaker recommendation than an already-green CO2 reason
                # at the 60 % threshold. Poor/very-poor AQ still keeps its real
                # class/severity and participates in the closing side of the
                # merger.
                if (
                    data.air_quality == "moderate"
                    and data.nina_status != "caution"
                    and not data.weather_caution
                    and not _outdoor_co2_general_disadvantage(data)
                ):
                    mode = "feuchte_lueften"
                else:
                    mode = (
                        "komfort_abwaegung"
                        if data.air_quality == "moderate"
                        else air_quality_mode
                    )
            elif caution_kind is not None:
                mode = "komfort_abwaegung"
            return mode, caution_kind
        if diff < -AH_NEUTRAL:
            return "feuchte_warten", "humidity"
        return "feuchte_neutral", None

    if need in {"heat", "humid_heat", "temperature"}:
        helps = _temperature_moves_toward_target(ti, ta, target) or (
            need == "heat" and ta <= ti - 1
        )
        if not helps:
            return "normal", None
        if caution_kind is not None:
            if caution_kind == "air_quality":
                return air_quality_mode or "luftqualitaet_maessig", caution_kind
            if caution_kind == "air_warning":
                return "nina_vorsicht", caution_kind
            if caution_kind == "weather":
                return "wetter_vorsicht", caution_kind
            return "komfort_abwaegung", caution_kind
        if diff < -1.0 and hi >= 55:
            return "komfort_abwaegung", "humidity"
        return ("kuehlen" if ta < ti else "erwaermen"), None

    if need == "routine":
        if air_quality_mode is not None:
            return air_quality_mode, "air_quality"
        bad = (
            caution_kind is not None
            or diff < -AH_NEUTRAL
            or (hi < 40 and diff > AH_NEUTRAL)
            or _temperature_moves_away(ti, ta, target)
        )
        return ("routine_warten" if bad else "routine_lueften"), caution_kind

    raise ValueError(f"Unsupported non-CO2 need: {need}")

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


def _outdoor_co2_general_disadvantage(data: RoomInput) -> bool:
    """Return whether measured outdoor CO₂ is materially worse than indoors."""
    if data.co2 is None or data.outdoor_co2 is None:
        return False
    # Technical margin only: avoid turning normal sensor noise into a decision.
    return data.outdoor_co2 >= data.co2 + 100.0


def _air_quality_mode(data: RoomInput) -> str | None:
    """Return the exact visible mode for the current outdoor AQ class.

    Multi-need evaluation must not collapse poor/very-poor air into a generic
    caution and later relabel it as merely moderate. The UBA class therefore
    survives intact until the final conflict merge.
    """
    penalty = _air_quality_penalty(data)
    if data.air_quality == "very_poor":
        return (
            "luftqualitaet_sehr_schlecht_typisch"
            if penalty == 2
            else "luftqualitaet_sehr_schlecht"
        )
    if data.air_quality == "poor":
        return "luftqualitaet_schlecht"
    if data.air_quality == "moderate":
        return "luftqualitaet_maessig"
    return None


def _outdoor_soft_caution(data: RoomInput) -> str | None:
    if _air_quality_penalty(data) > 0:
        return "air_quality"
    if data.nina_status == "caution":
        return "air_warning"
    if data.weather_caution:
        return "weather"
    if _outdoor_co2_general_disadvantage(data):
        return "outdoor_co2"
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


def _room_status_color(urgency: int, ventilation_color: str, need: str) -> str:
    """Translate the final ventilation judgement into the room-air colour view.

    The two traffic-light modes are perspectives on one shared engine decision,
    not two independent decision engines. Mild indoor deviations deliberately
    remain green: this view is an action indicator, not a school grade for every
    sensor. Yellow means "watch it", orange means airing is meaningfully useful,
    and red is reserved for a truly urgent need under usable outside conditions.
    Hard official protection instructions are rendered separately as ``locked``
    by the UI.
    """
    urgency = max(0, min(3, int(urgency)))

    # The 24-hour fallback exists specifically to become noticeable when no
    # stronger sensor reason appeared. Keep it yellow instead of hiding it in
    # the deliberately calm level-1 green band.
    if need == "routine" and urgency > 0:
        return "yellow"

    if ventilation_color == "green":
        # Mild deviations are information, not a command to act. Orange starts
        # where airing is meaningfully useful; red remains the truly urgent end.
        return ("green", "green", "orange", "red")[urgency]

    if ventilation_color == "yellow":
        if urgency >= 3:
            return "orange"
        if urgency >= 2:
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
        "weather_forecast": bool(
            data.short_term_weather_change == "worsening"
            and data.short_term_weather_minutes is not None
            and 0 <= float(data.short_term_weather_minutes) <= 15
        ),
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


def _outside_baseline_mode(
    *,
    data: RoomInput,
    ti: float,
    hi: float,
    ta: float,
    target: float,
    diff: float,
    previous_mode: str,
) -> tuple[str, str | None]:
    """Return the strongest outside-only reason against unnecessary airing.

    These reasons are intentionally merged by *restriction* rather than by the
    normal traffic-light ordering. Adding a caution must therefore never turn a
    pre-existing stronger keep-closed reason into a more opening-friendly one.
    """
    candidates: list[tuple[str, str | None]] = []
    air_penalty = _air_quality_penalty(data)

    if data.air_quality == "very_poor":
        candidates.append(
            (
                "luftqualitaet_sehr_schlecht_typisch"
                if air_penalty == 2
                else "luftqualitaet_sehr_schlecht",
                "air_quality",
            )
        )
    elif data.air_quality == "poor":
        candidates.append(("luftqualitaet_schlecht", "air_quality"))
    elif data.air_quality == "moderate":
        candidates.append(("luftqualitaet_maessig", "air_quality"))

    if data.nina_status == "caution":
        candidates.append(("nina_vorsicht", "air_warning"))
    if data.weather_caution:
        candidates.append(("wetter_vorsicht", "weather"))
    if _strong_no_need_disadvantage(ti=ti, hi=hi, ta=ta, target=target, diff=diff):
        candidates.append(("aussen_stark_unpassend", "conditions"))
    if _outdoor_co2_general_disadvantage(data):
        candidates.append(("aussen_co2_hoeher", "outdoor_co2"))
    if (hi < 40 and diff > AH_NEUTRAL) or (
        previous_mode == "innen_zu_trocken"
        and hi < 42
        and diff >= AH_CONTINUE
    ):
        candidates.append(("innen_zu_trocken", "humidity"))
    if diff < -AH_NEUTRAL:
        candidates.append(("aussen_deutlich_feuchter", "humidity"))
    if _temperature_moves_away(ti, ta, target):
        candidates.append(
            ("aussen_zu_warm" if ta > ti else "aussen_zu_kalt", "temperature")
        )

    if not candidates:
        return "normal", None

    restriction_rank = {"green": 0, "yellow": 1, "orange": 2, "red": 3}
    return max(candidates, key=lambda item: restriction_rank.get(_color(item[0]), 0))


def _co2_mode_for_need(
    *,
    need: str,
    data: RoomInput,
    co2: float | None,
    hi: float,
    diff: float,
    mold_persistent: bool,
    air_penalty: int,
    temp_drawback: float,
    humidity_drawback: bool,
    humidity_drawback_strong: bool,
    outdoor_co2_limited: bool,
) -> tuple[str, str | None]:
    """Evaluate one active CO₂ need without allowing cautions to relax it.

    Physical outside drawbacks are evaluated first. Official/weather/air-
    quality cautions may then keep or strengthen that result, but can never
    turn an existing orange wait-state into a yellow trade-off.
    """
    soft_caution = _outdoor_soft_caution(data)
    external_caution = (
        "air_quality"
        if air_penalty >= 2
        else "air_warning"
        if data.nina_status == "caution"
        else "weather"
        if data.weather_caution
        else None
    )

    if need == "co2_critical":
        if outdoor_co2_limited:
            mode, caution = "co2_kritisch_vorsicht", "outdoor_co2"
        elif hi >= 60 and diff <= -3.0:
            mode, caution = "co2_kritisch_vorsicht", "humidity"
        elif temp_drawback >= 15.0:
            mode, caution = "co2_kritisch_vorsicht", "temperature"
        else:
            mode, caution = "co2_kritisch", soft_caution

        if external_caution is not None and _color(mode) == "green":
            return "co2_kritisch_vorsicht", external_caution
        return mode, caution

    if need == "co2_high":
        if mold_persistent and humidity_drawback:
            mode, caution = "co2_warten", "humidity"
        elif _outdoor_co2_general_disadvantage(data):
            mode, caution = "co2_warten", "outdoor_co2"
        elif co2 is not None and co2 >= 1700:
            # Continuous disadvantages only: crossing an unrelated RH threshold
            # must not make a higher CO₂ reading produce a weaker recommendation.
            if temp_drawback >= 15.0 or (hi >= 60 and diff <= -3.0):
                mode, caution = (
                    "co2_abwaegung",
                    "temperature" if temp_drawback >= 15.0 else "humidity",
                )
            elif outdoor_co2_limited:
                mode, caution = "co2_abwaegung", "outdoor_co2"
            elif temp_drawback >= 3.0 or humidity_drawback:
                mode, caution = (
                    "co2_lueften_mit_nachteil",
                    "temperature" if temp_drawback >= 3.0 else "humidity",
                )
            else:
                mode, caution = "co2_lueften", soft_caution
        elif hi >= 65 and humidity_drawback_strong:
            mode, caution = "co2_warten", "humidity"
        elif (hi >= 60 and humidity_drawback) or temp_drawback >= 5.0:
            mode, caution = (
                "co2_abwaegung",
                "humidity" if hi >= 60 and humidity_drawback else "temperature",
            )
        elif outdoor_co2_limited:
            mode, caution = "co2_abwaegung", "outdoor_co2"
        else:
            mode, caution = "co2_lueften", soft_caution

        # A new external warning can only keep or reduce the willingness to
        # open. In particular, an existing co2_warten state stays orange.
        if external_caution is not None and _color(mode) == "green":
            return "co2_abwaegung", external_caution
        return mode, caution

    if need == "co2_elevated":
        if mold_persistent and humidity_drawback:
            mode, caution = "co2_warten", "humidity"
        elif _outdoor_co2_general_disadvantage(data):
            mode, caution = "co2_warten", "outdoor_co2"
        elif temp_drawback >= 6.0 and humidity_drawback:
            mode, caution = "co2_warten", "combined"
        elif diff <= -1.0:
            mode, caution = "co2_warten", "humidity"
        elif humidity_drawback or temp_drawback >= 3.0:
            mode, caution = (
                "co2_abwaegung",
                "humidity" if humidity_drawback else "temperature",
            )
        elif outdoor_co2_limited:
            mode, caution = "co2_abwaegung", "outdoor_co2"
        else:
            mode, caution = "co2_lueften", soft_caution

        if air_penalty >= 2 and _color(mode) != "orange":
            return "co2_warten", "air_quality"
        if (
            (data.nina_status == "caution" or data.weather_caution)
            and _color(mode) == "green"
        ):
            return "co2_abwaegung", external_caution or "conditions"
        return mode, caution

    raise ValueError(f"Unsupported CO2 need: {need}")


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

    active_needs = _active_needs(
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
        co2_rearm_threshold=data.co2_rearm_threshold,
    )
    # Strongest indoor signal remains the room/display perspective. The actual
    # recommendation below is merged from every independently evaluated need.
    need, urgency = active_needs[0] if active_needs else ("none", 0)

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

    decision_need = need
    decision_urgency = urgency
    co2_candidate_need: str | None = None
    co2_candidate_mode: str | None = None
    co2_candidate_caution: str | None = None

    if hard_mode is not None:
        mode = hard_mode
        decision_need = "safety"

    elif active_needs:
        # Evaluate every active indoor reason independently. Merge by semantic
        # action, not by color alone: a yellow trade-off is opening-friendly,
        # while a yellow neutral state is not. A neutral secondary reason must
        # therefore never relax an existing keep-closed reason.
        candidates: list[tuple[str, int, str, str | None]] = []
        for candidate_need, candidate_urgency in active_needs:
            if candidate_need.startswith("co2_"):
                candidate_mode, candidate_caution = _co2_mode_for_need(
                    need=candidate_need,
                    data=data,
                    co2=co2,
                    hi=hi,
                    diff=diff,
                    mold_persistent=mold_persistent,
                    air_penalty=air_penalty,
                    temp_drawback=temp_drawback,
                    humidity_drawback=humidity_drawback,
                    humidity_drawback_strong=humidity_drawback_strong,
                    outdoor_co2_limited=outdoor_co2_limited,
                )
                if co2_candidate_need is None:
                    co2_candidate_need = candidate_need
                    co2_candidate_mode = candidate_mode
                    co2_candidate_caution = candidate_caution
            else:
                candidate_mode, candidate_caution = _non_co2_mode_for_need(
                    need=candidate_need,
                    data=data,
                    hi=hi,
                    ti=ti,
                    ta=ta,
                    target=target,
                    diff=diff,
                    previous_mode=previous_mode,
                )
            candidates.append(
                (candidate_need, candidate_urgency, candidate_mode, candidate_caution)
            )

        # Outdoor conditions are global, not something that should suddenly
        # appear only because a secondary indoor need (such as the 24 h routine)
        # becomes active. Add the strongest outside-only disadvantage once with
        # zero indoor urgency; semantic protection below decides how strongly it
        # competes with the actual indoor reasons.
        baseline_mode, baseline_caution = _outside_baseline_mode(
            data=data,
            ti=ti,
            hi=hi,
            ta=ta,
            target=target,
            diff=diff,
            previous_mode=previous_mode,
        )
        global_outdoor_modes = {
            "nina_vorsicht",
            "wetter_vorsicht",
            "luftqualitaet_maessig",
            "luftqualitaet_schlecht",
            "luftqualitaet_sehr_schlecht_typisch",
            "luftqualitaet_sehr_schlecht",
            "aussen_co2_hoeher",
        }
        if baseline_mode in global_outdoor_modes:
            baseline_urgency = (
                2 if baseline_mode == "luftqualitaet_sehr_schlecht" else 1
            )
            candidates.append(
                ("outside", baseline_urgency, baseline_mode, baseline_caution)
            )

        beneficial = [item for item in candidates if _action_semantic(item[2]) == "beneficial"]
        tradeoffs = [item for item in candidates if _action_semantic(item[2]) == "tradeoff"]
        harmful = [item for item in candidates if _action_semantic(item[2]) == "harmful"]
        strong_harmful = [
            item for item in candidates if _action_semantic(item[2]) == "strong_harmful"
        ]
        neutral = [item for item in candidates if _action_semantic(item[2]) == "neutral"]

        # Resolve *all* candidates through the same two-sided merge. The best
        # opening signal is chosen from beneficial + genuine trade-offs, while
        # the best closing signal is chosen from ordinary + strong measured
        # disadvantages. Merely adding a third category can therefore never
        # switch the engine to a different selection algorithm.
        opening_candidates = beneficial + tradeoffs
        closing_candidates = harmful + strong_harmful

        opening_conflict = (
            max(
                opening_candidates,
                key=lambda item: (
                    item[1],
                    # CO2 monotonicity and independent-benefit stability: at
                    # equal urgency an already useful green reason must not be
                    # weakened merely because a peer need enters a yellow band.
                    1 if _action_semantic(item[2]) == "beneficial" else 0,
                    _need_protection_level(item[0]),
                ),
            )
            if opening_candidates
            else None
        )

        opening = opening_conflict
        if (
            opening_conflict is not None
            and opening_conflict[0].startswith("co2_")
            and _action_semantic(opening_conflict[2]) == "tradeoff"
            and beneficial
        ):
            # An independent green indoor reason proves that opening remains
            # useful even when the current CO2 band itself carries a drawback.
            # Keep CO2 as the decision/session driver, but preserve the existing
            # monotonic behaviour as a green "with disadvantage" result.
            opening = (
                opening_conflict[0],
                opening_conflict[1],
                "co2_lueften_mit_nachteil",
                opening_conflict[3] or "combined",
            )

        # Two closing representatives are useful for different purposes:
        # ``closing_conflict`` supplies the urgency/protection that competes with
        # opening, while ``closing_display`` preserves the strongest visible
        # protection class (red strong_harmful > orange harmful). Thus a severe
        # measured AQ warning cannot be relabelled orange merely because another
        # indoor reason has higher urgency.
        def _closing_effective_urgency(
            item: tuple[str, int, str, str | None],
        ) -> int:
            # When CO2 says "wait" solely because measured outdoor CO2 is
            # higher, the *closing* disadvantage is the outside delta, not the
            # indoor CO2 band that happened to activate the need. Do not let the
            # 1000/1400 ppm indoor thresholds artificially strengthen the same
            # unchanged outdoor disadvantage. This keeps CO2 monotonic while the
            # normal conflict resolver can still compare a real opening trade-off
            # against that disadvantage.
            if (
                item[0].startswith("co2_")
                and item[2] == "co2_warten"
                and item[3] == "outdoor_co2"
            ):
                return 1

            # Unusually very poor measured outdoor air is not a hard lock, but
            # it is stronger than a weak comfort/routine reason. Give such a red
            # measured disadvantage a floor of urgency 2. Critical indoor needs
            # (urgency 3) can still outweigh it into a genuine trade-off.
            strong_floor = (
                2
                if item[2] == "luftqualitaet_sehr_schlecht"
                else 1
                if _action_semantic(item[2]) == "strong_harmful"
                else 0
            )
            return max(item[1], strong_floor)

        closing_conflict = (
            max(
                closing_candidates,
                key=lambda item: (
                    _closing_effective_urgency(item),
                    _need_protection_level(item[0]),
                    1 if _action_semantic(item[2]) == "strong_harmful" else 0,
                ),
            )
            if closing_candidates
            else None
        )
        closing_display = (
            max(
                closing_candidates,
                key=lambda item: (
                    1 if _action_semantic(item[2]) == "strong_harmful" else 0,
                    item[1],
                    _need_protection_level(item[0]),
                ),
            )
            if closing_candidates
            else None
        )

        def _select_closing() -> tuple[str, int, str, str | None]:
            assert closing_conflict is not None and closing_display is not None
            conflict_need, conflict_urgency, _conflict_mode, _conflict_caution = closing_conflict
            _display_need, _display_urgency, display_mode, display_caution = closing_display
            # Keep the strongest *decision* reason in memory, while showing the
            # strongest actual protection class to the user.
            return (conflict_need, conflict_urgency, display_mode, display_caution)

        if opening is not None and opening_conflict is not None and closing_conflict is not None:
            opening_semantic = _action_semantic(opening_conflict[2])
            closing_semantic = _action_semantic(closing_display[2]) if closing_display else "harmful"

            if closing_conflict[0].startswith("co2_") and (
                opening_semantic == "beneficial"
                or (
                    opening_semantic == "tradeoff"
                    and _closing_effective_urgency(closing_conflict)
                    <= opening_conflict[1]
                )
            ):
                # CO2 monotonicity: crossing into a higher CO2 band must not
                # erase an already independent useful reason to air merely
                # because the CO2 branch itself dislikes an outdoor drawback.
                # A yellow opening trade-off only receives that protection at
                # equal/lower CO2 closing urgency. A more urgent CO2 wait-state
                # still competes through the normal priority rules.
                selected = opening
            elif _closing_effective_urgency(closing_conflict) > opening_conflict[1]:
                selected = _select_closing()
            elif _closing_effective_urgency(closing_conflict) < opening_conflict[1]:
                selected = opening
            else:
                opening_protection = _need_protection_level(opening_conflict[0])
                closing_protection = _need_protection_level(closing_conflict[0])
                if closing_semantic == "strong_harmful":
                    # At equal effective urgency, unusually very poor measured
                    # air remains the stronger protection message. Only urgency
                    # 3 indoor needs can outrank it before reaching this tie.
                    selected = _select_closing()
                elif closing_protection > opening_protection:
                    selected = _select_closing()
                elif opening_protection > closing_protection:
                    selected = opening
                elif (
                    opening_conflict[0].startswith("co2_")
                    and opening_semantic == "beneficial"
                ):
                    # Once CO2 itself becomes clearly worth airing at the same
                    # urgency as an ordinary humidity/comfort drawback, raising
                    # CO2 must not make the overall recommendation weaker.
                    selected = opening
                elif opening_semantic == "tradeoff":
                    # Equal urgency/protection with an already cautious opening
                    # signal remains a genuine trade-off.
                    selected = opening
                else:
                    # Equal green-vs-closing urgency is a genuine conflict. A
                    # red measured disadvantage is still not a hard safety lock;
                    # represent the tie as an explicit yellow trade-off.
                    o_need, o_urgency, _o_mode, _o_caution = opening_conflict
                    selected = (
                        o_need,
                        o_urgency,
                        "co2_abwaegung" if o_need.startswith("co2_") else "komfort_abwaegung",
                        "air_quality" if closing_semantic == "strong_harmful" else "combined",
                    )
        elif opening is not None:
            selected = opening
        elif closing_conflict is not None:
            selected = _select_closing()
        else:
            # Outside-only disadvantages participate when active reasons are
            # neutral. This prevents feuchte_neutral/schimmel_neutral from
            # overwriting an independently meaningful keep-closed condition.
            baseline_mode, baseline_caution = _outside_baseline_mode(
                data=data,
                ti=ti,
                hi=hi,
                ta=ta,
                target=target,
                diff=diff,
                previous_mode=previous_mode,
            )
            if neutral and baseline_mode in {
                "nina_vorsicht",
                "wetter_vorsicht",
                "luftqualitaet_maessig",
                "luftqualitaet_schlecht",
                "luftqualitaet_sehr_schlecht_typisch",
                "luftqualitaet_sehr_schlecht",
                "aussen_stark_unpassend",
                "aussen_co2_hoeher",
            }:
                selected = ("outside", 0, baseline_mode, baseline_caution)
            elif neutral:
                selected = neutral[0]
            else:
                selected = ("none", 0, "normal", None)

        decision_need, decision_urgency, mode, caution_kind = selected

        # The 24-hour routine remains a fallback and therefore never re-enters
        # the normal multi-need candidate set. Its already-established positive
        # airing value must nevertheless not disappear exactly when the first,
        # low CO2 band becomes active. If routine airing would be green under the
        # same outside conditions and elevated CO2 only says "trade-off" because
        # outdoor CO2 offers limited reduction, preserve the recommendation as a
        # green CO2 airing with an explicit disadvantage. Higher CO2 bands and
        # real outside warnings are unaffected.
        if (
            hours >= 24.0
            and decision_need == "co2_elevated"
            and mode == "co2_abwaegung"
            and caution_kind == "outdoor_co2"
        ):
            routine_mode, _routine_caution = _non_co2_mode_for_need(
                need="routine",
                data=data,
                hi=hi,
                ti=ti,
                ta=ta,
                target=target,
                diff=diff,
                previous_mode=previous_mode,
            )
            if _action_semantic(routine_mode) == "beneficial":
                mode = "co2_lueften_mit_nachteil"

        # When CO₂ is the strongest indoor signal and its own judgement is a
        # genuine yellow trade-off, an independently green reason proves that
        # opening is still clearly useful overall. Keep CO₂ as the session
        # driver without hiding its drawback. A true orange wait-state is never
        # promoted.
        if (
            need.startswith("co2_")
            and decision_need != need
            and _color(mode) == "green"
            and co2_candidate_mode is not None
            and _action_semantic(co2_candidate_mode) == "tradeoff"
        ):
            decision_need = need
            decision_urgency = urgency
            mode = "co2_lueften_mit_nachteil"
            caution_kind = co2_candidate_caution or "combined"

    else:
        mode, caution_kind = _outside_baseline_mode(
            data=data,
            ti=ti,
            hi=hi,
            ta=ta,
            target=target,
            diff=diff,
            previous_mode=previous_mode,
        )
        # No indoor need is driving the decision. Keep the decision memory at
        # "none" so later short-term weather post-processing can still replace a
        # mild outside inconvenience with the more relevant imminent warning.
        decision_need = "none"
        decision_urgency = 0

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
        elif mode in {"co2_lueften", "co2_lueften_mit_nachteil", "feuchte_lueften", "schimmel_lueften", "schimmel_langzeit_lueften", "kuehlen", "erwaermen", "routine_lueften"}:
            if urgency >= 2:
                mode = "co2_abwaegung" if decision_need.startswith("co2") else "komfort_abwaegung"
                caution_kind = "rain"
            else:
                mode = "komfort_abwaegung"
                caution_kind = "rain"
        elif mode == "normal":
            mode = "regen" if data.rain_now else "regen_bald"

    # A material weather change in the next hour may matter before it becomes
    # the current condition. Keep this deliberately softer than live weather or
    # an official warning: it can turn a good opening window into a trade-off,
    # but it never becomes a safety lock on forecast data alone.
    short_term_weather_relevant = _short_term_weather_worsening_relevant(
        data, mode, ta
    )
    if hard_mode is None and short_term_weather_relevant:
        # A concrete current/radar rain signal remains the more immediate reason.
        forecast_kind = str(data.short_term_weather_kind or "weather")
        forecast_is_stronger_than_rain = forecast_kind in {
            "thunderstorm",
            "hail",
            "severe_weather",
            "wind",
        }
        if caution_kind != "rain" or forecast_is_stronger_than_rain:
            if mode == "co2_kritisch":
                mode = "co2_kritisch_vorsicht"
                caution_kind = "weather_forecast"
            elif _color(mode) == "green":
                mode = (
                    "co2_abwaegung"
                    if decision_need.startswith("co2")
                    else "komfort_abwaegung"
                )
                caution_kind = "weather_forecast"
            elif decision_need == "none" or mode in {
                "normal",
                "feuchte_neutral",
                "schimmel_neutral",
            }:
                mode = "wetter_vorsicht"
                caution_kind = "weather_forecast"
            elif _color(mode) == "yellow" and caution_kind is None:
                caution_kind = "weather_forecast"

    co2_session_need: str | None = None
    co2_session_target: float | None = None
    if hard_mode is None and co2_candidate_need is not None and co2_candidate_mode is not None:
        co2_session_target = _co2_session_target_for_decision(
            need=co2_candidate_need,
            mode=co2_candidate_mode,
            co2=co2,
            temp_drawback=temp_drawback,
            humidity_drawback=humidity_drawback,
            humidity_drawback_strong=humidity_drawback_strong,
            indoor_humidity=hi,
            caution_kind=co2_candidate_caution,
        )
        if co2_session_target is not None:
            if outdoor_co2_limited and co2_candidate_caution == "outdoor_co2":
                co2_session_target = None
            elif data.outdoor_co2 is not None and co2_session_target <= data.outdoor_co2:
                co2_session_target = min(
                    float(co2) if co2 is not None else data.outdoor_co2 + 50.0,
                    data.outdoor_co2 + 50.0,
                )
            if co2_session_target is not None:
                co2_session_need = co2_candidate_need

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
            # A routine-airing recommendation is only considered fulfilled
            # after a real minimum exchange time. The airing tracker confirms
            # sessions at five minutes; mirror that threshold here so the UI
            # cannot say "done" seconds after the user opens the window.
            continue_routine = (
                decision_need == "routine"
                and (data.open_minutes is None or data.open_minutes < 5.0)
            )
            if (
                continue_co2
                or continue_moisture
                or continue_cooling
                or continue_warming
                or continue_routine
            ):
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
        reason_args.update(_short_term_weather_args(data))
        original_reason = data.weather_original_reason
    elif mode == "wetter_vorsicht":
        reason_key = (
            "weather_forecast_worsening"
            if caution_kind == "weather_forecast"
            else (data.weather_reason_key or "weather_caution")
        )
        reason_args = dict(data.weather_reason_args)
        reason_args.update(_short_term_weather_args(data))
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
            "continue_warming": (
                ti < target - 0.2 and ta >= ti + 0.5 and ta <= target + 4.0
            ),
            "continue_routine": (
                decision_need == "routine"
                and (data.open_minutes is None or data.open_minutes < 5.0)
            ),
            "open_minutes": data.open_minutes,
            "routine_min_minutes": 5.0,
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
            **_short_term_weather_args(data),
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
            "need": decision_need,
            "caution": caution_kind or "conditions",
            "humidity": hi,
            "diff": diff,
            "ti": ti,
            "ta": ta,
            "target": target,
            "surface_humidity": surface_rh,
            **_short_term_weather_args(data),
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
    elif mode == "aussen_co2_hoeher":
        reason_key, reason_args = "outdoor_co2_worse", {
            "co2": co2,
            "outdoor_co2": data.outdoor_co2,
        }
    elif mode == "aussen_stark_unpassend":
        reason_key, reason_args = "outside_strongly_unhelpful", {
            "ti": ti, "ta": ta, "target": target, "diff": diff, "humidity": hi
        }
    elif mode == "innen_zu_trocken":
        reason_key, reason_args = "inside_too_dry", {"humidity": hi, "diff": diff}
    elif mode == "regen":
        reason_key = data.weather_reason_key or "rain_now"
        reason_args = dict(data.weather_reason_args)
        reason_args.update(_short_term_weather_args(data))
        original_reason = data.weather_original_reason
    elif mode == "regen_bald":
        reason_key, reason_args = "rain_soon", {"minutes": data.rain_minutes_until}
    else:
        reason_key, reason_args = "normal", {}

    room_urgency = _room_display_urgency(need, data)
    room_color = _room_status_color(room_urgency, color, need)
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
        "room_color": room_color,
        "weather_reason_key": data.weather_reason_key,
        "weather_reason_args": dict(data.weather_reason_args),
        **_short_term_weather_args(data),
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
        co2_session_need=co2_session_need,
        room_status_color=room_color,
        room_recommendation_key=room_recommendation_key,
        room_reason_key="room_perspective",
        room_reason_args=room_reason_args,
        primary_need=need,
        decision_need=decision_need,
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

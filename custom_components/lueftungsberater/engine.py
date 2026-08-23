"""Home-Assistant-independent ventilation decision engine.

The engine deliberately returns semantic keys plus raw values instead of
pre-rendered language. Home Assistant and the frontend can therefore render the
same decision naturally in the user's language without changing the logic.
"""
from __future__ import annotations

import math

from .models import RoomInput, VentilationResult


def absolute_humidity(temp_c: float, rh: float) -> float:
    """Return absolute humidity in g/m³ using the Magnus approximation."""
    vapor_pressure = (rh / 100.0) * 6.112 * math.exp((17.62 * temp_c) / (243.12 + temp_c))
    return 216.7 * vapor_pressure / (273.15 + temp_c)


def surface_relative_humidity(indoor_temp_c: float, indoor_rh: float, surface_temp_c: float | None) -> float | None:
    """Estimate RH directly at a measured cold surface.

    The indoor vapour pressure is compared with the saturation vapour pressure
    at the surface temperature. Values are capped at 100 %, where condensation
    would begin.
    """
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


def _duration_key(mode: str, outdoor_temp: float) -> str:
    if mode == "weiter_lueften":
        return "until_targets"
    if mode == "lueftung_fertig":
        return "can_end"
    if mode == "co2_kritisch_vorsicht":
        return "brief_observation"
    if mode == "co2_kritisch":
        return "co2_recheck"
    if mode == "co2_lueften":
        return "co2_until_good"
    if mode == "kuehlen":
        return "cooling"
    if mode == "erwaermen":
        return "warming"
    if mode in {"feuchte_lueften", "schimmel_lueften", "routine_lueften"}:
        if outdoor_temp < -5:
            return "2_4"
        if outdoor_temp < 0:
            return "3_5"
        if outdoor_temp < 5:
            return "4_6"
        if outdoor_temp < 10:
            return "5_8"
        if outdoor_temp < 18:
            return "8_12"
        if outdoor_temp <= 25:
            return "10_15"
        return "5_10"
    return "not_needed"


def _color(mode: str) -> str:
    if mode in {
        "co2_kritisch", "co2_lueften", "weiter_lueften", "feuchte_lueften",
        "schimmel_lueften", "kuehlen", "erwaermen", "routine_lueften",
    }:
        return "green"
    if mode in {
        "nina_aussenluftgefahr", "wettergefahr", "aussen_zu_warm",
        "aussen_zu_kalt", "aussen_deutlich_feuchter", "innen_zu_trocken",
    }:
        return "red"
    return "yellow"


def _recommendation_key(color: str, mode: str, window_open: bool) -> str:
    if color == "green":
        return "keep_open" if window_open else "open_now"
    if color == "red":
        return "close_now" if window_open else "keep_closed"
    if mode in {"nina_vorsicht", "wetter_vorsicht"}:
        return "better_close" if window_open else "caution_keep_closed"
    if window_open:
        return "short_observation" if mode == "co2_kritisch_vorsicht" else "can_close"
    return "wait"


def evaluate_room(data: RoomInput) -> VentilationResult:
    ti, hi, ta = data.indoor_temp, data.indoor_humidity, data.outdoor_temp
    target = data.target_temp
    ahi = absolute_humidity(ti, hi)
    aha = absolute_humidity(ta, data.outdoor_humidity)
    diff = ahi - aha
    co2 = data.co2
    hours = data.hours_since_airing or 0.0
    previous_mode = data.previous_mode or ""

    # Small hysteresis bands keep recommendations from bouncing when a sensor
    # sits directly on a threshold. Critical CO₂ remains immediate.
    co2_critical = co2 is not None and co2 > 2000
    co2_high = co2 is not None and co2 >= 1400
    co2_elevated = co2 is not None and (
        co2 >= 1000
        or (previous_mode in {"co2_lueften", "co2_warten"} and co2 >= 950)
    )
    moisture_urgent = hi >= 65 and diff >= 0.3
    moisture_good = (
        hi >= 60 and diff >= 1.0
    ) or (
        previous_mode == "feuchte_lueften" and hi >= 58 and diff >= 0.5
    )
    too_hot = ti >= target + 1
    too_cold = ti <= target - 1
    cooling_good = (
        too_hot and ta <= ti - 1 and diff >= -0.5
    ) or (
        previous_mode == "kuehlen"
        and ti >= target + 0.5
        and ta <= ti - 0.7
        and diff >= -0.5
    )
    warming_good = (
        too_cold and ta >= ti + 1 and ta <= target + 4 and diff >= -0.5
    ) or (
        previous_mode == "erwaermen"
        and ti <= target - 0.5
        and ta >= ti + 0.7
        and ta <= target + 4
        and diff >= -0.5
    )

    surface_rh = surface_relative_humidity(ti, hi, data.surface_temp)
    mold_risk = surface_rh is not None and (
        surface_rh >= 80.0
        or (
            previous_mode in {"schimmel_lueften", "schimmel_warten", "weiter_lueften"}
            and surface_rh >= 78.0
        )
    )
    mold_can_improve = mold_risk and diff >= 0.5
    outside_too_hot_bad = (
        too_hot and ta >= ti + 1
    ) or (
        previous_mode == "aussen_zu_warm"
        and ti >= target + 0.5
        and ta >= ti + 0.5
    )
    outside_too_cold_bad = (
        too_cold and ta <= ti - 1
    ) or (
        previous_mode == "aussen_zu_kalt"
        and ti <= target - 0.5
        and ta <= ti - 0.5
    )
    outside_much_wetter = diff <= -1.0 or (
        previous_mode == "aussen_deutlich_feuchter" and diff <= -0.5
    )
    inside_too_dry = (hi < 40 and diff >= 0.5) or (
        previous_mode == "innen_zu_trocken" and hi < 42 and diff >= 0.3
    )
    climate_ok = ta <= ti + 3 and diff >= -1.0
    routine = hours >= 24 and (co2 is None or co2 < 1000) and climate_ok

    continue_co2 = data.window_open and co2 is not None and (
        co2 >= 1000 or (previous_mode == "weiter_lueften" and co2 >= 950)
    )
    continue_moisture = data.window_open and (
        (hi >= 60 and diff >= 0.5)
        or (previous_mode == "weiter_lueften" and hi >= 58 and diff >= 0.5)
        or mold_can_improve
    )
    continue_cooling = data.window_open and ti > target + 0.5 and ta <= ti - 0.7 and diff >= -0.5
    continue_warming = data.window_open and ti < target - 0.5 and ta >= ti + 0.7 and ta <= target + 4 and diff >= -0.5
    continue_airing = continue_co2 or continue_moisture or continue_cooling or continue_warming

    if data.nina_status == "danger":
        mode = "nina_aussenluftgefahr"
    elif data.weather_danger:
        mode = "wettergefahr"
    elif data.nina_status == "caution":
        mode = "nina_vorsicht"
    elif data.weather_caution:
        mode = "wetter_vorsicht"
    elif data.window_open and continue_airing and not data.rain_now:
        mode = "weiter_lueften"
    elif data.window_open and not continue_airing:
        mode = "lueftung_fertig"
    elif co2_critical and (data.rain_now or data.rain_soon):
        mode = "co2_kritisch_vorsicht"
    elif co2_critical:
        mode = "co2_kritisch"
    elif co2_high and climate_ok and not data.rain_now:
        mode = "co2_lueften"
    elif co2_high:
        mode = "co2_warten"
    elif co2_elevated and climate_ok and not data.rain_now and not data.rain_soon:
        mode = "co2_lueften"
    elif co2_elevated:
        mode = "co2_warten"
    elif mold_can_improve and not data.rain_now and not data.rain_soon:
        mode = "schimmel_lueften"
    elif moisture_urgent and not data.rain_now and not data.rain_soon:
        mode = "feuchte_lueften"
    elif moisture_good and not data.rain_now and not data.rain_soon:
        mode = "feuchte_lueften"
    elif mold_risk:
        mode = "schimmel_warten"
    elif cooling_good and not data.rain_now:
        mode = "kuehlen"
    elif warming_good and not data.rain_now:
        mode = "erwaermen"
    elif routine and not data.rain_now and not data.rain_soon:
        mode = "routine_lueften"
    elif hi >= 65 and diff < 0.3:
        mode = "feuchte_warten"
    elif outside_too_hot_bad:
        mode = "aussen_zu_warm"
    elif outside_too_cold_bad:
        mode = "aussen_zu_kalt"
    elif outside_much_wetter:
        mode = "aussen_deutlich_feuchter"
    elif inside_too_dry:
        mode = "innen_zu_trocken"
    elif data.rain_now:
        mode = "regen"
    elif data.rain_soon:
        mode = "regen_bald"
    elif hours >= 24:
        mode = "routine_warten"
    else:
        mode = "normal"

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
    elif mode == "weiter_lueften":
        reason_key = "continue_airing"
        reason_args = {
            "continue_co2": continue_co2,
            "continue_moisture": continue_moisture,
            "continue_cooling": continue_cooling,
            "continue_warming": continue_warming,
            "co2": co2,
            "diff": diff,
            "ti": ti,
            "target": target,
        }
    elif mode == "lueftung_fertig":
        reason_key, reason_args = "airing_finished", {}
    elif mode == "co2_kritisch_vorsicht":
        reason_key, reason_args = "co2_critical_rain", {"co2": co2}
    elif mode == "co2_kritisch":
        reason_key, reason_args = "co2_critical", {"co2": co2}
    elif mode == "co2_lueften":
        reason_key, reason_args = "co2_ventilate", {"co2": co2}
    elif mode == "co2_warten":
        reason_key, reason_args = "co2_wait", {"co2": co2}
    elif mode == "schimmel_lueften":
        reason_key, reason_args = "mold_prevention", {"surface_humidity": surface_rh, "diff": diff}
    elif mode == "schimmel_warten":
        reason_key, reason_args = "mold_wait", {"surface_humidity": surface_rh}
    elif mode == "feuchte_lueften":
        reason_key, reason_args = "humidity_ventilate", {"humidity": hi, "diff": diff}
    elif mode == "feuchte_warten":
        reason_key, reason_args = "humidity_wait", {}
    elif mode == "kuehlen":
        reason_key, reason_args = "cooling", {"ti": ti, "target": target, "ta": ta}
    elif mode == "erwaermen":
        reason_key, reason_args = "warming", {"ti": ti, "target": target, "ta": ta}
    elif mode == "routine_lueften":
        reason_key, reason_args = "routine_ventilate", {"hours": hours}
    elif mode == "routine_warten":
        reason_key, reason_args = "routine_wait", {"hours": hours}
    elif mode == "aussen_zu_warm":
        reason_key, reason_args = "outside_too_hot", {"ti": ti, "ta": ta}
    elif mode == "aussen_zu_kalt":
        reason_key, reason_args = "outside_too_cold", {"ti": ti, "ta": ta}
    elif mode == "aussen_deutlich_feuchter":
        reason_key, reason_args = "outside_more_humid", {"amount": abs(diff)}
    elif mode == "innen_zu_trocken":
        reason_key, reason_args = "inside_too_dry", {}
    elif mode == "regen":
        reason_key = data.weather_reason_key or "rain_now"
        reason_args = dict(data.weather_reason_args)
        original_reason = data.weather_original_reason
    elif mode == "regen_bald":
        reason_key, reason_args = "rain_soon", {}
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
    )

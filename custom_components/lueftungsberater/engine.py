"""Home-Assistant-independent ventilation decision engine.

The thresholds intentionally mirror the current YAML Lüftungsberater as closely as
possible. Home Assistant entity handling belongs outside this module so the same
engine can be unit-tested and reused for every room.
"""
from __future__ import annotations
import math
from .models import RoomInput, VentilationResult


def absolute_humidity(temp_c: float, rh: float) -> float:
    """Return absolute humidity in g/m³ using the Magnus approximation."""
    vapor_pressure = (rh / 100.0) * 6.112 * math.exp((17.62 * temp_c) / (243.12 + temp_c))
    return 216.7 * vapor_pressure / (273.15 + temp_c)


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


def _duration(mode: str, outdoor_temp: float) -> str:
    if mode == "weiter_lueften":
        return "Bis die offenen Lüftungsziele erreicht sind"
    if mode == "lueftung_fertig":
        return "Lüften kann beendet werden"
    if mode == "co2_kritisch_vorsicht":
        return "3–5 Minuten unter Beobachtung"
    if mode == "co2_kritisch":
        return "10–15 Minuten, danach CO₂ erneut prüfen"
    if mode == "co2_lueften":
        return "5–10 Minuten, bis CO₂ unter etwa 1000 ppm fällt"
    if mode == "kuehlen":
        return "15–30 Minuten bzw. solange draußen günstiger bleibt"
    if mode == "erwaermen":
        return "5–10 Minuten"
    if mode in {"feuchte_lueften", "routine_lueften"}:
        if outdoor_temp < -5: return "2–4 Minuten"
        if outdoor_temp < 0: return "3–5 Minuten"
        if outdoor_temp < 5: return "4–6 Minuten"
        if outdoor_temp < 10: return "5–8 Minuten"
        if outdoor_temp < 18: return "8–12 Minuten"
        if outdoor_temp <= 25: return "10–15 Minuten"
        return "5–10 Minuten"
    return "Jetzt nicht nötig"


def _color(mode: str) -> str:
    if mode in {
        "co2_kritisch", "co2_lueften", "weiter_lueften", "feuchte_lueften",
        "kuehlen", "erwaermen", "routine_lueften",
    }:
        return "green"
    if mode in {
        "nina_aussenluftgefahr", "wettergefahr", "aussen_zu_warm",
        "aussen_zu_kalt", "aussen_deutlich_feuchter", "innen_zu_trocken",
    }:
        return "red"
    return "yellow"


def evaluate_room(data: RoomInput) -> VentilationResult:
    ti, hi, ta = data.indoor_temp, data.indoor_humidity, data.outdoor_temp
    target = data.target_temp
    ahi = absolute_humidity(ti, hi)
    aha = absolute_humidity(ta, data.outdoor_humidity)
    diff = ahi - aha
    co2 = data.co2
    hours = data.hours_since_airing or 0.0

    co2_critical = co2 is not None and co2 > 2000
    co2_high = co2 is not None and co2 >= 1400
    co2_elevated = co2 is not None and co2 >= 1000
    moisture_urgent = hi >= 65 and diff >= 0.3
    moisture_good = hi >= 60 and diff >= 1.0
    too_hot = ti >= target + 1
    too_cold = ti <= target - 1
    cooling_good = too_hot and ta <= ti - 1 and diff >= -0.5
    warming_good = too_cold and ta >= ti + 1 and ta <= target + 4 and diff >= -0.5
    climate_ok = ta <= ti + 3 and diff >= -1.0
    routine = hours >= 24 and (co2 is None or co2 < 1000) and climate_ok

    continue_co2 = data.window_open and co2 is not None and co2 >= 1000
    continue_moisture = data.window_open and hi >= 60 and diff >= 0.5
    continue_cooling = data.window_open and ti > target + 0.5 and ta <= ti - 0.7 and diff >= -0.5
    continue_warming = data.window_open and ti < target - 0.5 and ta >= ti + 0.7 and ta <= target + 4 and diff >= -0.5
    continue_airing = continue_co2 or continue_moisture or continue_cooling or continue_warming

    if data.nina_status == "danger":
        mode = "nina_aussenluftgefahr"
    elif data.weather_danger:
        mode = "wettergefahr"
    elif data.nina_status == "caution":
        mode = "nina_vorsicht"
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
    elif moisture_urgent and not data.rain_now and not data.rain_soon:
        mode = "feuchte_lueften"
    elif moisture_good and not data.rain_now and not data.rain_soon:
        mode = "feuchte_lueften"
    elif cooling_good and not data.rain_now:
        mode = "kuehlen"
    elif warming_good and not data.rain_now:
        mode = "erwaermen"
    elif routine and not data.rain_now and not data.rain_soon:
        mode = "routine_lueften"
    elif hi >= 65 and diff < 0.3:
        mode = "feuchte_warten"
    elif too_hot and ta >= ti + 1:
        mode = "aussen_zu_warm"
    elif too_cold and ta <= ti - 1:
        mode = "aussen_zu_kalt"
    elif diff <= -1.0:
        mode = "aussen_deutlich_feuchter"
    elif hi < 40 and diff >= 0.5:
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
    if color == "green":
        recommendation = "Weiter lüften" if data.window_open else "Jetzt lüften"
    elif color == "red":
        recommendation = "Jetzt schließen" if data.window_open else "Geschlossen lassen"
    elif mode == "nina_vorsicht":
        recommendation = "Besser schließen" if data.window_open else "Vorsicht – lieber geschlossen lassen"
    elif data.window_open:
        recommendation = "Nur kurz unter Beobachtung" if mode == "co2_kritisch_vorsicht" else "Lüften kann beendet werden"
    else:
        recommendation = "Noch nicht nötig / besser warten"

    # Concrete, user-facing reason. Provider adapters can inject exact warning text.
    if mode == "nina_aussenluftgefahr":
        reason = data.nina_reason or "NINA meldet eine relevante Gefahr für die Außenluft."
    elif mode == "nina_vorsicht":
        reason = data.nina_reason or "NINA empfiehlt vorsorglich, Fenster und Türen geschlossen zu halten."
    elif mode == "wettergefahr":
        reason = data.weather_reason or "Es besteht aktuell eine für offene Fenster relevante Wettergefahr."
    elif mode == "weiter_lueften":
        reasons: list[str] = []
        if continue_co2: reasons.append(f"CO₂ liegt noch bei {co2:.0f} ppm")
        if continue_moisture: reasons.append(f"außen ist die Luft etwa {diff:.1f} g/m³ trockener")
        if continue_cooling: reasons.append(f"Abkühlung von {ti:.1f} °C Richtung {target:.1f} °C ist weiter sinnvoll")
        if continue_warming: reasons.append(f"Erwärmung von {ti:.1f} °C Richtung {target:.1f} °C ist weiter sinnvoll")
        reason = "Weiter lüften: " + "; ".join(reasons) + "."
    elif mode == "lueftung_fertig":
        reason = "Der Luftaustausch ist ausreichend; aktuell besteht kein ausreichender Grund, weiter zu lüften."
    elif mode == "co2_kritisch_vorsicht":
        reason = f"CO₂ liegt bei {co2:.0f} ppm und ist sehr hoch; wegen Regen nur kurz und unter Beobachtung lüften."
    elif mode == "co2_kritisch":
        reason = f"CO₂ liegt bei {co2:.0f} ppm. Der Luftaustausch hat hohe Priorität."
    elif mode == "co2_lueften":
        reason = f"CO₂ liegt bei {co2:.0f} ppm und ist erhöht; die Außenbedingungen sind ausreichend geeignet."
    elif mode == "co2_warten":
        reason = f"CO₂ liegt bei {co2:.0f} ppm, die Außenbedingungen sind momentan aber ungünstig."
    elif mode == "feuchte_lueften":
        reason = f"Innen liegen {hi:.0f} % relative Feuchte an; außen enthält die Luft etwa {diff:.1f} g/m³ weniger Wasser."
    elif mode == "feuchte_warten":
        reason = "Die Innenfeuchte ist erhöht, draußen besteht momentan aber kaum Trocknungsvorteil."
    elif mode == "kuehlen":
        reason = f"Innen sind {ti:.1f} °C bei {target:.1f} °C Soll; draußen sind {ta:.1f} °C und Lüften hilft beim Abkühlen."
    elif mode == "erwaermen":
        reason = f"Innen sind {ti:.1f} °C bei {target:.1f} °C Soll; die Außenluft ist wärmer und geeignet."
    elif mode == "routine_lueften":
        reason = f"Seit rund {hours:.1f} Stunden wurde nicht bestätigt gelüftet und die Außenbedingungen sind günstig."
    elif mode == "routine_warten":
        reason = f"Seit rund {hours:.1f} Stunden wurde nicht bestätigt gelüftet, aber die Bedingungen sind gerade nicht gut genug."
    elif mode == "aussen_zu_warm":
        reason = f"Draußen sind {ta:.1f} °C und damit deutlich mehr als innen; die Wärme sollte draußen bleiben."
    elif mode == "aussen_zu_kalt":
        reason = f"Draußen sind {ta:.1f} °C und damit deutlich weniger als innen; unnötiges Auskühlen vermeiden."
    elif mode == "aussen_deutlich_feuchter":
        reason = f"Die Außenluft enthält etwa {abs(diff):.1f} g/m³ mehr Wasser als die Innenluft."
    elif mode == "innen_zu_trocken":
        reason = "Die Innenluft ist bereits trocken; Lüften würde sie momentan weiter austrocknen."
    elif mode == "regen":
        reason = "Aktuell wird Niederschlag erkannt."
    elif mode == "regen_bald":
        reason = "Kurzfristig wird Niederschlag erwartet."
    else:
        reason = "CO₂, Feuchtigkeit und Temperatur geben aktuell keinen ausreichenden Lüftungsgrund."

    return VentilationResult(
        color=color, mode=mode, recommendation=recommendation, reason=reason,
        duration=_duration(mode, ta), indoor_absolute_humidity=round(ahi, 2),
        outdoor_absolute_humidity=round(aha, 2), absolute_humidity_difference=round(diff, 2),
        co2_status=co2_status(co2),
    )

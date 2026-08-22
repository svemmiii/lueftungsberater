"""Natural-language rendering for Lüftungsberater recommendations."""
from __future__ import annotations

from typing import Any

SUPPORTED_LANGUAGES = ("de", "en")

RECOMMENDATIONS = {
    "de": {
        "open_now": "Jetzt lüften",
        "keep_open": "Weiter lüften",
        "can_close": "Lüften kann beendet werden",
        "short_observation": "Nur kurz lüften und im Blick behalten",
        "better_close": "Besser schließen",
        "caution_keep_closed": "Vorsicht – lieber geschlossen lassen",
        "keep_closed": "Geschlossen lassen",
        "close_now": "Jetzt schließen",
        "wait": "Besser noch etwas warten",
    },
    "en": {
        "open_now": "Open the windows now",
        "keep_open": "Keep the windows open a little longer",
        "can_close": "You can close the windows now",
        "short_observation": "Open the windows briefly and keep an eye on it",
        "better_close": "Better close the windows",
        "caution_keep_closed": "Better keep the windows closed for now",
        "keep_closed": "Keep the windows closed",
        "close_now": "Close the windows now",
        "wait": "Better wait a little longer",
    },
}

DURATIONS = {
    "de": {
        "until_targets": "Bis die offenen Lüftungsziele erreicht sind",
        "can_end": "Die Lüftung kann jetzt beendet werden",
        "brief_observation": "3–5 Minuten und dabei die Situation im Blick behalten",
        "co2_recheck": "10–15 Minuten, danach CO₂ erneut prüfen",
        "co2_until_good": "5–10 Minuten bzw. bis CO₂ unter etwa 1000 ppm fällt",
        "cooling": "15–30 Minuten – oder länger, solange die Außenluft weiterhin beim Abkühlen hilft",
        "warming": "5–10 Minuten",
        "2_4": "2–4 Minuten",
        "3_5": "3–5 Minuten",
        "4_6": "4–6 Minuten",
        "5_8": "5–8 Minuten",
        "8_12": "8–12 Minuten",
        "10_15": "10–15 Minuten",
        "5_10": "5–10 Minuten",
        "not_needed": "Aktuell keine Lüftungsdauer nötig",
    },
    "en": {
        "until_targets": "Until the remaining ventilation targets are reached",
        "can_end": "You can stop ventilating now",
        "brief_observation": "3–5 minutes while keeping an eye on the conditions",
        "co2_recheck": "10–15 minutes, then check CO₂ again",
        "co2_until_good": "5–10 minutes, or until CO₂ drops below roughly 1000 ppm",
        "cooling": "15–30 minutes, or longer while the outdoor air is still helping to cool the room",
        "warming": "5–10 minutes",
        "2_4": "2–4 minutes",
        "3_5": "3–5 minutes",
        "4_6": "4–6 minutes",
        "5_8": "5–8 minutes",
        "8_12": "8–12 minutes",
        "10_15": "10–15 minutes",
        "5_10": "5–10 minutes",
        "not_needed": "No ventilation duration is needed right now",
    },
}


def normalize_language(language: str | None) -> str:
    """Return one of the languages bundled with the integration."""
    low = (language or "en").lower().replace("_", "-")
    if low.startswith("de"):
        return "de"
    return "en"


def _number(value: Any, language: str, digits: int = 1) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "?"
    text = f"{number:.{digits}f}"
    return text.replace(".", ",") if language == "de" else text


NNBSP = "\u202f"


def _measurement(value: str, unit: str) -> str:
    """Keep a numeric value and its unit together across line wrapping."""
    return f"{value}{NNBSP}{unit}"


def _temperature(value_c: Any, language: str, unit: str) -> str:
    try:
        number = float(value_c)
    except (TypeError, ValueError):
        return "?"
    if str(unit).upper() in {"°F", "F", "FAHRENHEIT"}:
        number = number * 9 / 5 + 32
        unit = "°F"
    else:
        unit = "°C"
    return _measurement(_number(number, language, 1), unit)


def recommendation_text(key: str, language: str | None) -> str:
    lang = normalize_language(language)
    return RECOMMENDATIONS[lang].get(key, key)


def duration_text(key: str, language: str | None) -> str:
    lang = normalize_language(language)
    return DURATIONS[lang].get(key, key)


def _continue_reason(args: dict[str, Any], lang: str, unit: str) -> str:
    parts: list[str] = []
    if args.get("continue_co2"):
        ppm = _number(args.get("co2"), lang, 0)
        parts.append(
            f"CO₂ liegt noch bei {_measurement(ppm, 'ppm')}"
            if lang == "de"
            else f"CO₂ is still at {_measurement(ppm, 'ppm')}"
        )
    if args.get("continue_moisture"):
        diff = _number(args.get("diff"), lang, 1)
        parts.append(
            f"die Außenluft ist rund {_measurement(diff, 'g/m³')} trockener"
            if lang == "de"
            else f"the outdoor air is about {_measurement(diff, 'g/m³')} drier"
        )
    if args.get("continue_cooling"):
        ti = _temperature(args.get("ti"), lang, unit)
        target = _temperature(args.get("target"), lang, unit)
        parts.append(
            f"der Raum kann von {ti} weiter Richtung {target} abkühlen"
            if lang == "de"
            else f"the room can keep cooling from {ti} toward {target}"
        )
    if args.get("continue_warming"):
        ti = _temperature(args.get("ti"), lang, unit)
        target = _temperature(args.get("target"), lang, unit)
        parts.append(
            f"der Raum kann von {ti} weiter Richtung {target} wärmer werden"
            if lang == "de"
            else f"the room can keep warming from {ti} toward {target}"
        )

    if not parts:
        return (
            "Lüfte noch etwas weiter; mindestens ein Lüftungsziel ist noch offen."
            if lang == "de"
            else "Keep ventilating a little longer; at least one ventilation target is still open."
        )

    if len(parts) == 1:
        joined = parts[0]
    elif len(parts) == 2:
        joined = f"{parts[0]} und {parts[1]}" if lang == "de" else f"{parts[0]}, and {parts[1]}"
    else:
        connector = " und " if lang == "de" else ", and "
        joined = "; ".join(parts[:-1]) + connector + parts[-1]

    return (
        f"Lüfte ruhig noch etwas weiter: {joined}."
        if lang == "de"
        else f"Keep ventilating for a little longer: {joined}."
    )


def reason_text(
    key: str,
    args: dict[str, Any] | None,
    language: str | None,
    temperature_unit: str = "°C",
) -> str:
    """Render one natural recommendation reason from semantic engine data."""
    lang = normalize_language(language)
    a = args or {}
    t = lambda value: _temperature(value, lang, temperature_unit)
    n = lambda value, digits=1: _number(value, lang, digits)

    if key == "continue_airing":
        return _continue_reason(a, lang, temperature_unit)

    if lang == "de":
        texts = {
            "nina_air_danger": "Für die Außenluft liegt aktuell eine relevante Warnung vor. Lass Fenster und Türen deshalb besser geschlossen.",
            "nina_air_caution": "Für die Außenluft gilt aktuell ein Vorsichtshinweis. Lüfte im Moment besser nur, wenn es wirklich nötig ist.",
            "air_smoke_danger": "In der Umgebung wird Rauch oder Brandrauch gemeldet. Lass Fenster und Türen besser geschlossen, damit möglichst wenig davon hereinkommt.",
            "air_smoke_caution": "In der Umgebung wird Rauch oder Brandrauch gemeldet. Wenn es nicht dringend nötig ist, warte mit dem Lüften besser noch etwas.",
            "air_hazard_danger": "Es gibt eine Warnung vor Schadstoffen oder einem Gasaustritt in der Außenluft. Lass Fenster und Türen deshalb geschlossen.",
            "air_hazard_caution": "Es gibt einen Hinweis auf mögliche Schadstoffe in der Außenluft. Lüfte vorsichtshalber nur, wenn es wirklich nötig ist.",
            "weather_danger": "Draußen ist eine Unwetterlage aktiv, bei der offene Fenster keine gute Idee sind. Lass sie vorerst geschlossen.",
            "weather_caution": "Es gibt aktuell eine Wetterwarnung. Lüften ist nicht grundsätzlich ausgeschlossen, aber im Moment eher ungünstig.",
            "weather_heavy_rain_current": "Draußen regnet es gerade kräftig. Lüften ist nicht grundsätzlich ausgeschlossen, aber im Moment eher unpraktisch.",
            "weather_heavy_rain_caution": "Es wird vor Starkregen gewarnt. Wenn es nicht dringend nötig ist, warte mit dem Lüften besser noch etwas.",
            "weather_heavy_rain_danger": "Es gilt eine Unwetterwarnung vor heftigem Starkregen. Lass die Fenster besser geschlossen, bis sich die Lage beruhigt.",
            "weather_continuous_rain_caution": "Es wird vor länger anhaltendem kräftigem Regen gewarnt. Wenn es nicht nötig ist, warte mit dem Lüften besser noch etwas.",
            "weather_continuous_rain_danger": "Es gilt eine Unwetterwarnung vor ergiebigem Dauerregen. Lass die Fenster vorerst besser geschlossen.",
            "weather_thunderstorm_caution": "Es wird vor Gewittern gewarnt. Lüften ist gerade eher ungünstig; warte wenn möglich, bis die Gewitterlage vorbeigezogen ist.",
            "weather_thunderstorm_danger": "Es gilt eine Unwetterwarnung vor Gewittern. Lass die Fenster geschlossen, bis die Lage wieder ruhiger ist.",
            "weather_hail_caution": "Es besteht eine Hagelwarnung. Wenn möglich, lass die Fenster geschlossen, bis die Warnung vorbei ist.",
            "weather_hail_danger": "Es gilt eine Unwetterwarnung mit Hagel. Lass die Fenster geschlossen, bis die Lage vorbei ist.",
            "weather_storm_caution": "Es wird vor stürmischem Wetter gewarnt. Offene Fenster sind gerade keine gute Idee; warte besser noch etwas.",
            "weather_storm_danger": "Es gilt eine Unwetterwarnung vor Sturm. Lass Fenster und Türen geschlossen, bis sich die Lage beruhigt.",
            "weather_wind_caution": "Es wird vor starkem Wind gewarnt. Lüften ist gerade eher ungünstig; warte wenn möglich noch etwas.",
            "weather_wind_danger": "Es gilt eine Unwetterwarnung vor starkem Wind. Lass die Fenster besser geschlossen.",
            "weather_exceptional_danger": "Der Wetterdienst meldet eine außergewöhnliche Wetterlage. Lass die Fenster vorsichtshalber geschlossen.",
            "airing_finished": "Der Luftaustausch reicht im Moment aus. Du kannst die Fenster wieder schließen.",
            "co2_critical_rain": f"CO₂ liegt bei {_measurement(n(a.get('co2'), 0), 'ppm')} und ist damit sehr hoch. Trotz des Regens ist ein kurzer Luftaustausch sinnvoll – aber nur kurz und unter Beobachtung.",
            "co2_critical": f"CO₂ liegt bei {_measurement(n(a.get('co2'), 0), 'ppm')} und ist damit sehr hoch. Jetzt zu lüften hat klare Priorität.",
            "co2_ventilate": f"CO₂ liegt bei {_measurement(n(a.get('co2'), 0), 'ppm')} und ist erhöht. Draußen passen die Bedingungen, deshalb lohnt sich jetzt ein Luftaustausch.",
            "co2_wait": f"CO₂ liegt bei {_measurement(n(a.get('co2'), 0), 'ppm')} und ist erhöht. Die Außenbedingungen sind gerade aber ungünstig, deshalb ist kurzes Warten die bessere Wahl.",
            "humidity_ventilate": f"Drinnen liegen {_measurement(n(a.get('humidity'), 0), '%')} relative Feuchte an. Draußen enthält die Luft rund {_measurement(n(a.get('diff'), 1), 'g/m³')} weniger Wasser – Lüften hilft also beim Trocknen.",
            "humidity_wait": "Die Luftfeuchte drinnen ist erhöht, draußen gibt es im Moment aber kaum einen Trocknungsvorteil. Warte besser noch etwas.",
            "cooling": f"Drinnen sind es {t(a.get('ti'))}, bei einem Soll von {t(a.get('target'))}. Draußen sind es {t(a.get('ta'))} – Lüften hilft jetzt beim Abkühlen.",
            "warming": f"Drinnen sind es {t(a.get('ti'))}, bei einem Soll von {t(a.get('target'))}. Draußen ist es wärmer und die Außenluft eignet sich gerade zum Lüften.",
            "routine_ventilate": f"Seit rund {n(a.get('hours'), 1)} Stunden wurde keine bestätigte Lüftung erfasst. Die Außenbedingungen passen gerade gut, deshalb ist jetzt ein kurzer Luftaustausch sinnvoll.",
            "routine_wait": f"Seit rund {n(a.get('hours'), 1)} Stunden wurde keine bestätigte Lüftung erfasst. Die Bedingungen draußen passen gerade aber nicht gut genug – warte lieber noch etwas.",
            "outside_too_hot": f"Drinnen sind es {t(a.get('ti'))}, draußen {t(a.get('ta'))}. Beim Lüften würdest du gerade zusätzliche Wärme hereinholen – die Fenster bleiben besser zu.",
            "outside_too_cold": f"Drinnen sind es {t(a.get('ti'))}, draußen {t(a.get('ta'))}. Lüften würde den Raum gerade unnötig auskühlen – deshalb besser geschlossen lassen.",
            "outside_more_humid": f"Die Außenluft enthält rund {_measurement(n(a.get('amount'), 1), 'g/m³')} mehr Wasser als die Luft drinnen. Lüften würde die Feuchte eher hereinholen als herausbringen.",
            "inside_too_dry": "Die Luft drinnen ist bereits ziemlich trocken. Lüften würde sie im Moment noch weiter austrocknen – deshalb besser warten.",
            "rain_now": "Draußen fällt gerade Niederschlag. Wenn es nicht dringend nötig ist, warte mit dem Lüften besser kurz.",
            "rain_soon": "In Kürze wird Niederschlag erwartet. Wenn es nicht dringend nötig ist, ist ein etwas späterer Zeitpunkt zum Lüften wahrscheinlich besser.",
            "normal": "CO₂, Luftfeuchte und Temperatur geben gerade keinen ausreichenden Grund zum Lüften. Du kannst die Fenster erstmal geschlossen lassen.",
        }
    else:
        texts = {
            "nina_air_danger": "There is an active warning affecting the outdoor air. It is better to keep windows and doors closed for now.",
            "nina_air_caution": "There is currently an advisory affecting the outdoor air. Ventilate only if you really need to for the moment.",
            "air_smoke_danger": "Smoke or fire smoke has been reported nearby. Keep windows and doors closed to reduce how much of it gets indoors.",
            "air_smoke_caution": "Smoke or fire smoke has been reported nearby. Unless ventilation is urgent, it is better to wait a little longer.",
            "air_hazard_danger": "There is a warning about hazardous substances or a gas release in the outdoor air. Keep windows and doors closed for now.",
            "air_hazard_caution": "There is an advisory about possible pollutants in the outdoor air. Ventilate only if you really need to for now.",
            "weather_danger": "Severe weather is active outside and open windows are a bad idea right now. Keep them closed until conditions improve.",
            "weather_caution": "There is an active weather warning. Ventilation is not completely ruled out, but the conditions are not ideal right now.",
            "weather_heavy_rain_current": "It is raining heavily outside. Ventilation is not completely ruled out, but it is rather impractical right now.",
            "weather_heavy_rain_caution": "There is a heavy-rain warning. Unless ventilation is urgent, it is better to wait a little longer.",
            "weather_heavy_rain_danger": "A severe-weather warning for intense heavy rain is active. Keep the windows closed until conditions settle down.",
            "weather_continuous_rain_caution": "There is a warning for prolonged heavy rain. Unless ventilation is necessary, it is better to wait a little longer.",
            "weather_continuous_rain_danger": "A severe-weather warning for prolonged heavy rain is active. Keep the windows closed for now.",
            "weather_thunderstorm_caution": "There is a thunderstorm warning. Ventilation is not ideal right now; if possible, wait until the storms have passed.",
            "weather_thunderstorm_danger": "A severe thunderstorm warning is active. Keep the windows closed until conditions calm down.",
            "weather_hail_caution": "There is a hail warning. If possible, keep the windows closed until the warning has passed.",
            "weather_hail_danger": "A severe-weather warning with hail is active. Keep the windows closed until it has passed.",
            "weather_storm_caution": "Stormy weather is expected. Open windows are not a good idea right now, so it is better to wait.",
            "weather_storm_danger": "A severe storm warning is active. Keep windows and doors closed until conditions settle down.",
            "weather_wind_caution": "There is a strong-wind warning. Ventilation is not ideal right now; wait a little longer if you can.",
            "weather_wind_danger": "A severe strong-wind warning is active. It is better to keep the windows closed.",
            "weather_exceptional_danger": "The weather service is reporting exceptional conditions. Keep the windows closed as a precaution.",
            "airing_finished": "The air exchange is sufficient for now. You can close the windows again.",
            "co2_critical_rain": f"CO₂ is at {_measurement(n(a.get('co2'), 0), 'ppm')}, which is very high. A short air exchange is still worthwhile despite the rain, but keep it brief and monitor the situation.",
            "co2_critical": f"CO₂ is at {_measurement(n(a.get('co2'), 0), 'ppm')}, which is very high. Opening the windows now should take priority.",
            "co2_ventilate": f"CO₂ is at {_measurement(n(a.get('co2'), 0), 'ppm')} and is elevated. Outdoor conditions are suitable, so this is a good time to open the windows and exchange the air.",
            "co2_wait": f"CO₂ is at {_measurement(n(a.get('co2'), 0), 'ppm')} and is elevated, but outdoor conditions are unfavorable right now. Waiting briefly is the better choice.",
            "humidity_ventilate": f"Indoor relative humidity is {_measurement(n(a.get('humidity'), 0), '%')}. The outdoor air contains about {_measurement(n(a.get('diff'), 1), 'g/m³')} less water, so opening the windows will help dry the room.",
            "humidity_wait": "Indoor humidity is elevated, but the outdoor air offers very little drying benefit right now. It is better to wait a little longer.",
            "cooling": f"It is {t(a.get('ti'))} indoors with a target of {t(a.get('target'))}. Outside it is {t(a.get('ta'))}, so ventilating will help cool the room.",
            "warming": f"It is {t(a.get('ti'))} indoors with a target of {t(a.get('target'))}. The outdoor air is warmer and suitable for ventilation right now.",
            "routine_ventilate": f"No confirmed ventilation has been recorded for about {n(a.get('hours'), 1)} hours. Outdoor conditions are good, so a short air exchange makes sense now.",
            "routine_wait": f"No confirmed ventilation has been recorded for about {n(a.get('hours'), 1)} hours, but outdoor conditions are not good enough right now. It is better to wait a little longer.",
            "outside_too_hot": f"It is {t(a.get('ti'))} indoors and {t(a.get('ta'))} outside. Opening the windows now would bring extra heat in, so it is better to keep them closed.",
            "outside_too_cold": f"It is {t(a.get('ti'))} indoors and {t(a.get('ta'))} outside. Opening the windows now would cool the room unnecessarily, so it is better to keep them closed.",
            "outside_more_humid": f"The outdoor air contains about {_measurement(n(a.get('amount'), 1), 'g/m³')} more water than the indoor air. Opening the windows would bring moisture in rather than remove it.",
            "inside_too_dry": "The indoor air is already quite dry. Opening the windows now would dry it out even further, so it is better to wait.",
            "rain_now": "Precipitation is falling outside right now. Unless ventilation is urgent, it is better to wait a little.",
            "rain_soon": "Precipitation is expected shortly. Unless ventilation is urgent, a slightly later time will probably be better.",
            "normal": "CO₂, humidity, and temperature do not provide a strong enough reason to ventilate right now. You can keep the windows closed for the moment.",
        }

    return texts.get(key, key)


def localized_bundle(
    recommendation_key: str,
    reason_key: str,
    reason_args: dict[str, Any],
    duration_key: str,
    temperature_unit: str,
) -> dict[str, dict[str, str]]:
    """Render all bundled languages for per-user frontend selection."""
    return {
        language: {
            "recommendation": recommendation_text(recommendation_key, language),
            "reason": reason_text(reason_key, reason_args, language, temperature_unit),
            "duration": duration_text(duration_key, language),
        }
        for language in SUPPORTED_LANGUAGES
    }

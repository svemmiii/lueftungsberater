"""Natural-language rendering for Lüftungsberater recommendations."""
from __future__ import annotations

from typing import Any

SUPPORTED_LANGUAGES = ("de", "en", "tr")
NNBSP = "\u202f"

RECOMMENDATIONS = {
    "de": {
        "open_now": "Jetzt lüften",
        "keep_open": "Weiter lüften",
        "can_close": "Lüften kann beendet werden",
        "short_observation": "Nur kurz lüften und die Situation im Blick behalten",
        "optional": "Lüften ist aktuell optional",
        "better_close": "Besser wieder schließen",
        "caution_keep_closed": "Vorsicht – lieber geschlossen lassen",
        "keep_closed": "Geschlossen lassen",
        "close_now": "Jetzt schließen",
        "wait": "Besser noch etwas warten",
        "unknown": "Aktuell keine zuverlässige Empfehlung möglich",
        "room_good": "Aktuell kein Lüftungsgrund",
        "room_watch": "Werte im Blick behalten",
        "room_need": "Lüften ist sinnvoll",
        "room_urgent": "Jetzt lüften",
        "room_keep_brief": "Noch kurz weiterlüften",
    },
    "en": {
        "open_now": "Open the windows now",
        "keep_open": "Keep the windows open a little longer",
        "can_close": "You can close the windows now",
        "short_observation": "Open the windows briefly and keep an eye on it",
        "optional": "Ventilation is optional",
        "better_close": "Better close the windows",
        "caution_keep_closed": "Better keep the windows closed for now",
        "keep_closed": "Keep the windows closed",
        "close_now": "Close the windows now",
        "wait": "Better wait a little longer",
        "unknown": "No reliable recommendation is available right now",
        "room_good": "No current reason to ventilate",
        "room_watch": "Keep an eye on the values",
        "room_need": "Ventilation is worthwhile",
        "room_urgent": "Ventilate now",
        "room_keep_brief": "Keep ventilating briefly",
    },
    "tr": {
        "open_now": "Şimdi pencereleri aç",
        "keep_open": "Pencereleri biraz daha açık tut",
        "can_close": "Artık pencereleri kapatabilirsin",
        "short_observation": "Kısa süre havalandır ve durumu takip et",
        "optional": "Havalandırma isteğe bağlı",
        "better_close": "Pencereleri kapatmak daha iyi",
        "caution_keep_closed": "Şimdilik pencereleri kapalı tutmak daha iyi",
        "keep_closed": "Pencereleri kapalı tut",
        "close_now": "Pencereleri şimdi kapat",
        "wait": "Biraz daha beklemek daha iyi",
        "unknown": "Şu anda güvenilir bir öneri verilemiyor",
        "room_good": "Şu anda havalandırma nedeni yok",
        "room_watch": "Değerleri takip et",
        "room_need": "Havalandırmak faydalı",
        "room_urgent": "Şimdi havalandır",
        "room_keep_brief": "Kısa süre daha havalandır",
    },
}

DURATIONS = {
    "de": {
        "until_targets": "Bis die noch offenen Lüftungsziele erreicht sind",
        "can_end": "Die Lüftung kann jetzt beendet werden",
        "brief_observation": "Etwa 5 Minuten – dabei die Situation im Blick behalten",
        "co2_recheck": "5–10 Minuten, danach CO₂ erneut prüfen",
        "co2_until_good": "5–10 Minuten, danach CO₂ erneut prüfen",
        "co2_minimum": "Mindestens 5 Minuten ab dem Öffnen",
        "cooling": "15–30 Minuten – oder länger, solange die Außenluft weiterhin beim Abkühlen hilft",
        "warming": "5–10 Minuten",
        "2_4": "2–4 Minuten",
        "3_5": "3–5 Minuten",
        "4_6": "4–6 Minuten",
        "5_8": "5–8 Minuten",
        "8_12": "8–12 Minuten",
        "10_15": "10–15 Minuten",
        "10_20": "10–20 Minuten",
        "5_10": "5–10 Minuten",
        "not_needed": "Aktuell keine Lüftungsdauer nötig",
        "incomplete_data": "Eine Lüftungsdauer lässt sich mit den aktuellen Sensordaten noch nicht zuverlässig bestimmen.",
    },
    "en": {
        "until_targets": "Until the remaining ventilation targets are reached",
        "can_end": "You can close the windows now",
        "brief_observation": "About 5 minutes, while keeping an eye on the conditions",
        "co2_recheck": "5–10 minutes, then check CO₂ again",
        "co2_until_good": "5–10 minutes, then check CO₂ again",
        "co2_minimum": "At least 5 minutes from opening the window",
        "cooling": "15–30 minutes, or longer if the cooler outdoor air continues to help",
        "warming": "5–10 minutes",
        "2_4": "2–4 minutes",
        "3_5": "3–5 minutes",
        "4_6": "4–6 minutes",
        "5_8": "5–8 minutes",
        "8_12": "8–12 minutes",
        "10_15": "10–15 minutes",
        "10_20": "10–20 minutes",
        "5_10": "5–10 minutes",
        "not_needed": "No window-opening time is needed right now",
        "incomplete_data": "A reliable window-opening time cannot be determined from the current sensor data yet.",
    },
    "tr": {
        "until_targets": "Kalan havalandırma hedeflerine ulaşılana kadar",
        "can_end": "Artık pencereleri kapatabilirsin",
        "brief_observation": "Yaklaşık 5 dakika; bu sırada durumu takip et",
        "co2_recheck": "5–10 dakika, ardından CO₂ seviyesini yeniden kontrol et",
        "co2_until_good": "5–10 dakika, ardından CO₂ seviyesini yeniden kontrol et",
        "co2_minimum": "Pencere açıldıktan sonra en az 5 dakika",
        "cooling": "15–30 dakika; dışarıdaki serin hava işe yaramaya devam ederse daha uzun da olabilir",
        "warming": "5–10 dakika",
        "2_4": "2–4 dakika",
        "3_5": "3–5 dakika",
        "4_6": "4–6 dakika",
        "5_8": "5–8 dakika",
        "8_12": "8–12 dakika",
        "10_15": "10–15 dakika",
        "10_20": "10–20 dakika",
        "5_10": "5–10 dakika",
        "not_needed": "Şu anda pencereleri açmaya gerek yok",
        "incomplete_data": "Mevcut sensör verileriyle güvenilir bir havalandırma süresi henüz belirlenemiyor.",
    },
}


def normalize_language(language: str | None) -> str:
    """Return one of the languages bundled with the integration."""
    low = (language or "en").lower().replace("_", "-")
    if low.startswith("de"):
        return "de"
    if low.startswith("tr"):
        return "tr"
    return "en"


def _number(value: Any, language: str, digits: int = 1) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "?"
    text = f"{number:.{digits}f}"
    return text.replace(".", ",") if language in {"de", "tr"} else text


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


def _join_reason_parts(parts: list[str], lang: str) -> str:
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        connector = {"de": " und ", "en": ", and ", "tr": " ve "}[lang]
        return f"{parts[0]}{connector}{parts[1]}"
    if lang == "en":
        return "; ".join(parts[:-1]) + ", and " + parts[-1]
    connector = " und " if lang == "de" else " ve "
    return "; ".join(parts[:-1]) + connector + parts[-1]


def _continue_reason(args: dict[str, Any], lang: str, unit: str) -> str:
    parts: list[str] = []
    if args.get("continue_co2"):
        ppm = _measurement(_number(args.get("co2"), lang, 0), "ppm")
        target_raw = args.get("co2_target")
        if target_raw is not None:
            target_ppm = _measurement(_number(target_raw, lang, 0), "ppm")
            parts.append(
                {
                    "de": f"CO₂ liegt noch bei {ppm}; Ziel dieser Lüftung sind etwa {target_ppm}",
                    "en": f"CO₂ is still at {ppm}; this airing session is aiming for about {target_ppm}",
                    "tr": f"CO₂ hâlâ {ppm}; bu havalandırmanın hedefi yaklaşık {target_ppm}",
                }[lang]
            )
        else:
            parts.append(
                {"de": f"CO₂ liegt noch bei {ppm}", "en": f"CO₂ is still at {ppm}", "tr": f"CO₂ hâlâ {ppm}"}[lang]
            )
    if args.get("continue_moisture"):
        diff = _measurement(_number(args.get("diff"), lang, 1), "g/m³")
        parts.append(
            {
                "de": f"die Außenluft ist rund {diff} trockener",
                "en": f"the outdoor air is about {diff} drier",
                "tr": f"dış hava yaklaşık {diff} daha kuru",
            }[lang]
        )
    if args.get("continue_cooling"):
        ti = _temperature(args.get("ti"), lang, unit)
        target = _temperature(args.get("target"), lang, unit)
        parts.append(
            {
                "de": f"der Raum kann von {ti} weiter Richtung {target} abkühlen",
                "en": f"the room can keep cooling from {ti} toward {target}",
                "tr": f"oda {ti} seviyesinden {target} hedefine doğru serinlemeye devam edebilir",
            }[lang]
        )
    if args.get("continue_warming"):
        ti = _temperature(args.get("ti"), lang, unit)
        target = _temperature(args.get("target"), lang, unit)
        parts.append(
            {
                "de": f"der Raum kann von {ti} weiter Richtung {target} wärmer werden",
                "en": f"the room can keep warming from {ti} toward {target}",
                "tr": f"oda {ti} seviyesinden {target} hedefine doğru ısınmaya devam edebilir",
            }[lang]
        )
    if args.get("continue_routine"):
        open_minutes = _number(args.get("open_minutes"), lang, 1)
        minimum = _number(args.get("routine_min_minutes"), lang, 0)
        if args.get("open_minutes") is None:
            text = {
                "de": f"die Routinelüftung soll mindestens etwa {minimum} Minuten laufen",
                "en": f"the routine airing should run for at least about {minimum} minutes",
                "tr": f"rutin havalandırma en az yaklaşık {minimum} dakika sürmeli",
            }[lang]
        else:
            text = {
                "de": f"die Routinelüftung läuft erst seit {open_minutes} Minuten und soll mindestens etwa {minimum} Minuten dauern",
                "en": f"the routine airing has only run for {open_minutes} minutes and should last at least about {minimum} minutes",
                "tr": f"rutin havalandırma yalnızca {open_minutes} dakikadır sürüyor ve en az yaklaşık {minimum} dakika sürmeli",
            }[lang]
        parts.append(text)

    if not parts:
        return {
            "de": "Lüfte noch etwas weiter; mindestens ein Lüftungsziel ist noch offen.",
            "en": "Keep the windows open a little longer; at least one ventilation target has not been reached yet.",
            "tr": "Pencereleri biraz daha açık tut; en az bir havalandırma hedefi henüz tamamlanmadı.",
        }[lang]

    joined = _join_reason_parts(parts, lang)
    return {
        "de": f"Lüfte noch etwas weiter: {joined}.",
        "en": f"Keep the windows open a little longer: {joined}.",
        "tr": f"Pencereleri biraz daha açık tutabilirsin: {joined}.",
    }[lang]


def _pollutant_label(value: Any) -> str:
    return {
        "pm2_5": "PM2.5",
        "pm10": "PM10",
        "no2": "NO₂",
        "o3": "O₃",
        "so2": "SO₂",
    }.get(str(value or ""), str(value or "").upper() or "—")


def _air_quality_reason(key: str, a: dict[str, Any], lang: str) -> str:
    pollutant = _pollutant_label(a.get("pollutant"))
    value = a.get("value")
    measured = ""
    if value is not None:
        measured = f" ({pollutant} {_measurement(_number(value, lang, 0), 'µg/m³')})"
    elif pollutant != "—":
        measured = f" ({pollutant})"

    baseline = a.get("baseline")
    typical = a.get("typical")
    unusual = bool(a.get("unusual"))
    trend = str(a.get("trend") or "unknown")
    context = ""
    if baseline is not None and typical is not None:
        if unusual:
            context = {
                "de": " Das ist hier deutlich schlechter als sonst.",
                "en": " That is clearly worse than usual for this location.",
                "tr": " Bu değer bu konum için alışılmıştan belirgin biçimde daha kötü.",
            }[lang]
        elif typical:
            context = {
                "de": " Die Belastung liegt ungefähr im üblichen Bereich dieses Standorts – gut wird sie dadurch aber nicht.",
                "en": " This is roughly typical for this location, but that does not make the pollution healthy.",
                "tr": " Bu seviye bu konum için yaklaşık olarak alışılmış düzeyde, ancak bu onu sağlıklı yapmaz.",
            }[lang]
    if trend == "rising":
        context += {"de": " Die Werte steigen gerade.", "en": " Levels are rising right now.", "tr": " Değerler şu anda yükseliyor."}[lang]
    elif trend == "falling":
        context += {"de": " Die Werte fallen gerade.", "en": " Levels are falling right now.", "tr": " Değerler şu anda düşüyor."}[lang]

    if key == "air_quality_moderate":
        return {
            "de": f"Die Außenluft ist aktuell mäßig belastet{measured}. Wenn die Innenwerte passen, kannst du die Fenster geschlossen lassen.{context}",
            "en": f"Outdoor air quality is moderate right now{measured}. If the indoor values are fine, you can keep the windows closed.{context}",
            "tr": f"Dış hava kalitesi şu anda orta düzeyde{measured}. İç değerler uygunsa pencereleri kapalı tutabilirsin.{context}",
        }[lang]

    very_poor = key == "air_quality_very_poor"
    level = {
        "de": "sehr schlecht" if very_poor else "schlecht",
        "en": "very poor" if very_poor else "poor",
        "tr": "çok kötü" if very_poor else "kötü",
    }[lang]
    return {
        "de": f"Die Außenluft ist aktuell {level}{measured}. Wenn drinnen kein wichtiger Lüftungsgrund besteht, lass die Fenster lieber geschlossen.{context}",
        "en": f"Outdoor air is {level} right now{measured}. If there is no important reason to air the room, it is better to keep the windows closed.{context}",
        "tr": f"Dış hava şu anda {level}{measured}. İçeride önemli bir havalandırma nedeni yoksa pencereleri kapalı tutmak daha iyi.{context}",
    }[lang]


def _short_term_weather_sentence(
    a: dict[str, Any], lang: str, *, expected_change: str | None = None
) -> str:
    """Render a plain-language next-hour weather hint.

    The minute value points to the next hourly forecast slot showing a change;
    wording intentionally avoids claiming minute-accurate storm timing.
    """
    change = str(a.get("forecast_change") or "")
    if not change or (expected_change is not None and change != expected_change):
        return ""
    kind = str(a.get("forecast_kind") or "weather")
    try:
        minutes = max(0, round(float(a.get("forecast_minutes"))))
    except (TypeError, ValueError):
        minutes = None

    soon = minutes is not None and minutes <= 20
    when = {
        "de": "in Kürze" if soon else "innerhalb der nächsten Stunde",
        "en": "shortly" if soon else "within the next hour",
        "tr": "yakında" if soon else "önümüzdeki bir saat içinde",
    }[lang]
    when_start = {
        "de": "In Kürze" if soon else "Innerhalb der nächsten Stunde",
        "en": "Shortly" if soon else "Within the next hour",
        "tr": "Yakında" if soon else "Önümüzdeki bir saat içinde",
    }[lang]

    if change == "worsening":
        texts = {
            "thunderstorm": {
                "de": f"{when_start} wird Gewitter erwartet.",
                "en": f"A thunderstorm is expected {when}.",
                "tr": f"{when_start} gök gürültülü fırtına bekleniyor.",
            },
            "hail": {
                "de": f"{when_start} wird Hagel bzw. eine deutlich schlechtere Wetterlage erwartet.",
                "en": f"Hail or clearly worse weather is expected {when}.",
                "tr": f"{when_start} dolu veya belirgin biçimde daha kötü hava bekleniyor.",
            },
            "wind": {
                "de": f"{when_start} wird deutlich stärkerer Wind erwartet.",
                "en": f"Much stronger wind is expected {when}.",
                "tr": f"{when_start} belirgin biçimde daha güçlü rüzgâr bekleniyor.",
            },
            "heavy_rain": {
                "de": f"{when_start} wird kräftiger Regen erwartet.",
                "en": f"Heavy rain is expected {when}.",
                "tr": f"{when_start} kuvvetli yağmur bekleniyor.",
            },
            "rain": {
                "de": f"{when_start} wird Regen erwartet.",
                "en": f"Rain is expected {when}.",
                "tr": f"{when_start} yağmur bekleniyor.",
            },
        }
        return texts.get(kind, {
            "de": f"Die Wetterlage wird {when} voraussichtlich ungünstiger.",
            "en": f"Weather conditions are expected to become less favorable {when}.",
            "tr": f"Hava koşullarının {when} daha elverişsiz hâle gelmesi bekleniyor.",
        })[lang]

    if change == "improving":
        texts = {
            "thunderstorm": {
                "de": f"Die Gewitterlage soll sich {when} beruhigen.",
                "en": f"The thunderstorm conditions are expected to ease {when}.",
                "tr": f"Gök gürültülü hava koşullarının {when} sakinleşmesi bekleniyor.",
            },
            "hail": {
                "de": f"Die Hagel-/Unwetterlage soll sich {when} bessern.",
                "en": f"The hail/severe-weather situation is expected to improve {when}.",
                "tr": f"Dolu/şiddetli hava durumunun {when} iyileşmesi bekleniyor.",
            },
            "wind": {
                "de": f"Der starke Wind soll {when} nachlassen.",
                "en": f"The strong wind is expected to ease {when}.",
                "tr": f"Kuvvetli rüzgârın {when} azalması bekleniyor.",
            },
            "heavy_rain": {
                "de": f"Der kräftige Regen soll {when} nachlassen.",
                "en": f"The heavy rain is expected to ease {when}.",
                "tr": f"Kuvvetli yağmurun {when} azalması bekleniyor.",
            },
            "rain": {
                "de": f"Der Regen soll {when} nachlassen.",
                "en": f"The rain is expected to ease {when}.",
                "tr": f"Yağmurun {when} azalması bekleniyor.",
            },
        }
        return texts.get(kind, {
            "de": f"Die Wetterlage soll sich {when} bessern.",
            "en": f"Weather conditions are expected to improve {when}.",
            "tr": f"Hava koşullarının {when} iyileşmesi bekleniyor.",
        })[lang]

    return ""


def _tradeoff_reason(key: str, a: dict[str, Any], lang: str, unit: str) -> str:
    caution = str(a.get("caution") or "conditions")
    co2 = a.get("co2")
    if key == "co2_tradeoff":
        ppm = _measurement(_number(co2, lang, 0), "ppm")
        detail_options = {
            "rain": {
                "de": "Es regnet oder während der kurzen Lüftung könnte Regen einsetzen.",
                "en": "It is raining or rain may begin during the short ventilation period.",
                "tr": "Yağmur yağıyor veya kısa havalandırma sırasında yağmur başlayabilir.",
            },
            "humidity": {
                "de": "Die Außenluft ist dabei feuchter und würde die Feuchtesituation verschlechtern.",
                "en": "The outdoor air is wetter and would worsen the moisture situation.",
                "tr": "Dış hava daha nemli ve içerideki nem durumunu kötüleştirebilir.",
            },
            "temperature": {
                "de": "Die Außentemperatur würde den Raum spürbar vom Sollwert wegbewegen.",
                "en": "The outdoor temperature would noticeably move the room away from its target.",
                "tr": "Dış sıcaklık oda sıcaklığını hedeften belirgin biçimde uzaklaştırır.",
            },
            "combined": {
                "de": "Draußen passen Temperatur und Feuchte gleichzeitig deutlich schlechter.",
                "en": "Outside is also clearly worse for both temperature and humidity.",
                "tr": "Dışarısı aynı anda hem sıcaklık hem de nem açısından belirgin biçimde daha kötü.",
            },
            "outdoor_co2": {
                "de": "Auch draußen ist der CO₂-Wert hoch, daher würde Lüften ihn nur wenig senken.",
                "en": "Outdoor CO₂ is high as well, so airing would only reduce it a little.",
                "tr": "Dışarıdaki CO₂ de yüksek, bu yüzden havalandırma değeri yalnızca biraz düşürür.",
            },
            "near_target": {
                "de": "Das Ziel dieser Lüftung ist fast erreicht. Du kannst die Lüftung gleich beenden.",
                "en": "The target for this airing session is almost reached. You can finish airing soon.",
                "tr": "Bu havalandırmanın hedefi neredeyse tamamlandı. Havalandırmayı yakında bitirebilirsin.",
            },
            "air_quality": {
                "de": "Die Außenluftqualität ist nur mäßig.",
                "en": "Outdoor air quality is only moderate.",
                "tr": "Dış hava kalitesi yalnızca orta düzeyde.",
            },
            "air_warning": {
                "de": "Für die Außenluft gilt gleichzeitig ein Vorsichtshinweis.",
                "en": "There is also an outdoor-air advisory.",
                "tr": "Aynı zamanda dış hava için bir dikkat uyarısı var.",
            },
            "weather": {
                "de": "Gleichzeitig sind die Wetterbedingungen ungünstig.",
                "en": "Weather conditions are unfavorable at the same time.",
                "tr": "Aynı zamanda hava koşulları elverişsiz.",
            },
        }
        detail = (
            _short_term_weather_sentence(a, lang, expected_change="worsening")
            if caution == "weather_forecast"
            else ""
        ) or detail_options.get(caution, {
            "de": "Die Außenbedingungen sind gerade ungünstig.",
            "en": "Outdoor conditions are unfavorable right now.",
            "tr": "Dış koşullar şu anda elverişsiz.",
        })[lang]
        if caution == "near_target" and a.get("co2_target") is not None:
            target_ppm = _measurement(_number(a.get("co2_target"), lang, 0), "ppm")
            detail = {
                "de": f"Das für diese Lüftung festgelegte Ziel von etwa {target_ppm} ist fast erreicht. Du kannst die Lüftung gleich beenden.",
                "en": f"The target of about {target_ppm} set for this airing session is almost reached. You can finish airing soon.",
                "tr": f"Bu havalandırma için belirlenen yaklaşık {target_ppm} hedefi neredeyse tamamlandı. Havalandırmayı yakında bitirebilirsin.",
            }[lang]
        return {
            "de": f"CO₂ liegt bei {ppm} und spricht fürs Lüften. {detail}",
            "en": f"CO₂ is at {ppm}, so fresh air would help. {detail}",
            "tr": f"CO₂ {ppm} seviyesinde ve havalandırma faydalı olur. {detail}",
        }[lang]

    need = str(a.get("need") or "")
    need_text = {
        "humidity": {"de": "Die Raumfeuchte spricht fürs Lüften.", "en": "Indoor humidity would benefit from airing.", "tr": "İç nem havalandırmadan fayda görür."},
        "humidity_urgent": {"de": "Die Raumfeuchte ist deutlich erhöht.", "en": "Indoor humidity is clearly elevated.", "tr": "İç nem belirgin şekilde yüksek."},
        "mold": {"de": "Die Feuchtesituation an der überwachten Oberfläche kann von Luftaustausch profitieren.", "en": "The moisture situation at the monitored surface would benefit from air exchange.", "tr": "İzlenen yüzeydeki nem durumu hava değişiminden fayda görür."},
        "mold_persistent": {"de": "Die kritische Oberflächenfeuchte hält bereits länger an.", "en": "The critical surface humidity has persisted for a longer period.", "tr": "Kritik yüzey nemi daha uzun süredir devam ediyor."},
        "heat": {"de": "Der Raum ist deutlich aufgeheizt und könnte abkühlen.", "en": "The room is very warm and could benefit from cooling.", "tr": "Oda belirgin biçimde sıcak ve serinlemeden fayda görebilir."},
        "humid_heat": {"de": "Wärme und hohe Feuchte belasten den Raumkomfort.", "en": "Heat and high humidity are reducing comfort.", "tr": "Sıcaklık ve yüksek nem konforu azaltıyor."},
        "temperature": {"de": "Die Außenluft würde die Raumtemperatur Richtung Wunschwert bewegen.", "en": "The outdoor air would move the temperature toward your preferred value.", "tr": "Dış hava sıcaklığı tercih edilen değere yaklaştırabilir."},
        "routine": {"de": "Ein kurzer Luftaustausch wäre grundsätzlich sinnvoll.", "en": "A short air exchange would generally make sense.", "tr": "Kısa bir hava değişimi genel olarak mantıklı olur."},
    }.get(need, {"de": "Lüften hätte einen Vorteil.", "en": "Airing would have a benefit.", "tr": "Havalandırmanın bir faydası olur."})[lang]
    drawback_options = {
        "rain": {"de": "Regen macht das offene Fenster gerade unpraktisch.", "en": "Rain makes an open window impractical right now.", "tr": "Yağmur şu anda açık pencereyi pratik olmaktan çıkarıyor."},
        "humidity": {"de": "Die Außenluft würde gleichzeitig zusätzliche Feuchte eintragen.", "en": "The outdoor air would also add moisture.", "tr": "Dış hava aynı zamanda içeri ek nem getirir."},
        "air_quality": {"de": "Die Außenluftqualität ist jedoch nur mäßig.", "en": "Outdoor air quality is only moderate, though.", "tr": "Ancak dış hava kalitesi yalnızca orta düzeyde."},
        "air_warning": {"de": "Es gilt jedoch ein Außenluft-Hinweis.", "en": "There is an outdoor-air advisory, though.", "tr": "Ancak dış hava için bir uyarı var."},
        "weather": {"de": "Die Wetterlage spricht gleichzeitig gegen ein offenes Fenster.", "en": "The weather also argues against an open window.", "tr": "Hava koşulları aynı zamanda açık pencereye karşı."},
        "temperature": {"de": "Dabei würde sich die Raumtemperatur spürbar verschlechtern.", "en": "Room temperature would noticeably worsen at the same time.", "tr": "Oda sıcaklığı aynı zamanda belirgin biçimde kötüleşir."},
        "combined": {"de": "Temperatur und Feuchte draußen wären gleichzeitig deutlich ungünstiger.", "en": "Outdoor temperature and humidity would both be a noticeably worse fit.", "tr": "Dış sıcaklık ve nem aynı anda belirgin biçimde daha kötü uyuyor."},
        "outdoor_co2": {"de": "Auch draußen ist CO₂ hoch, dadurch bringt der Luftaustausch dafür nur wenig.", "en": "Outdoor CO₂ is high as well, so the air exchange would do little for that.", "tr": "Dışarıdaki CO₂ de yüksek; bu yüzden hava değişimi bu açıdan çok az fayda sağlar."},
    }
    drawback = (
        _short_term_weather_sentence(a, lang, expected_change="worsening")
        if caution == "weather_forecast"
        else ""
    ) or drawback_options.get(caution, {
        "de": "Draußen passt es gleichzeitig nicht besonders gut.",
        "en": "Outside is not a particularly good fit at the same time.",
        "tr": "Dışarısı aynı anda pek uygun değil.",
    })[lang]
    return f"{need_text} {drawback}"



def _room_perspective_reason(a: dict[str, Any], lang: str, unit: str) -> str:
    """Render the inverted traffic-light perspective without changing decisions."""
    need = str(a.get("need") or "none")
    level = int(a.get("level") or 0)
    room_color = str(a.get("room_color") or "green")
    ventilation_color = str(a.get("ventilation_color") or "yellow")
    mode = str(a.get("mode") or "normal")
    caution = str(a.get("caution") or "")

    co2 = _measurement(_number(a.get("co2"), lang, 0), "ppm")
    humidity = _measurement(_number(a.get("humidity"), lang, 1), "%")
    ti = _temperature(a.get("ti"), lang, unit)
    ta = _temperature(a.get("ta"), lang, unit)
    target = _temperature(a.get("target"), lang, unit)
    hours = _number(a.get("hours"), lang, 0)
    surface = _measurement(_number(a.get("surface_humidity"), lang, 0), "%")

    if need == "co2_critical":
        inside = {
            "de": f"CO₂ liegt mit {co2} sehr hoch. Dadurch ist Lüften dringend nötig.",
            "en": f"CO₂ is very high at {co2}. Ventilation is urgently needed.",
            "tr": f"CO₂ {co2} ile çok yüksek. Bu nedenle havalandırma acilen gerekli.",
        }[lang]
    elif need in {"co2_high", "co2_elevated"}:
        if room_color == "green" and level <= 1:
            inside = {
                "de": f"CO₂ liegt bei {co2} und ist leicht erhöht. Aktuell ist deshalb noch kein Lüften nötig.",
                "en": f"CO₂ is slightly elevated at {co2}. There is no need to ventilate yet.",
                "tr": f"CO₂ {co2} ile biraz yüksek. Şimdilik havalandırmak gerekmiyor.",
            }[lang]
        else:
            inside = {
                "de": f"CO₂ liegt bei {co2} und erhöht den Lüftungsbedarf.",
                "en": f"CO₂ is at {co2}, increasing the need for fresh air.",
                "tr": f"CO₂ {co2} seviyesinde ve havalandırma ihtiyacını artırıyor.",
            }[lang]
    elif need in {"humidity", "humidity_urgent"}:
        qualifier = {
            "de": "leicht erhöht" if level <= 1 else "deutlich erhöht",
            "en": "slightly elevated" if level <= 1 else "clearly elevated",
            "tr": "biraz yüksek" if level <= 1 else "belirgin biçimde yüksek",
        }[lang]
        if room_color == "green" and level <= 1:
            inside = {
                "de": f"Die Raumfeuchte liegt mit {humidity} leicht erhöht. Aktuell ist deshalb noch kein Lüften nötig.",
                "en": f"Indoor humidity is slightly elevated at {humidity}. There is no need to ventilate yet.",
                "tr": f"İç nem {humidity} ile biraz yüksek. Şimdilik havalandırmak gerekmiyor.",
            }[lang]
        else:
            inside = {
                "de": f"Die Raumfeuchte liegt mit {humidity} {qualifier}.",
                "en": f"Indoor humidity is {qualifier} at {humidity}.",
                "tr": f"İç nem {humidity} ile {qualifier}.",
            }[lang]
    elif need == "mold_persistent":
        inside = {
            "de": f"An der überwachten Oberfläche liegt die relative Feuchte seit längerer Zeit bei rund {surface} und bleibt damit auffällig.",
            "en": f"Relative humidity at the monitored surface has remained elevated at around {surface} for a longer period.",
            "tr": f"İzlenen yüzeyde bağıl nem uzun süredir yaklaşık {surface} seviyesinde ve yüksek kalıyor.",
        }[lang]
    elif need == "mold":
        inside = {
            "de": f"An der überwachten Oberfläche liegt die relative Feuchte bei rund {surface} und ist erhöht.",
            "en": f"Humidity at the monitored surface is elevated at around {surface}.",
            "tr": f"İzlenen yüzeydeki nem yaklaşık {surface} ile yüksek.",
        }[lang]
    elif need == "heat":
        inside = {
            "de": f"Der Raum liegt mit {ti} deutlich über dem Sollwert von {target}.",
            "en": f"The room is at {ti}, clearly above the target of {target}.",
            "tr": f"Oda {ti} ile {target} hedefinin belirgin biçimde üzerinde.",
        }[lang]
    elif need == "humid_heat":
        inside = {
            "de": f"Im Raum sind mit {ti} und {humidity} sowohl Temperatur als auch Feuchte erhöht.",
            "en": f"At {ti} and {humidity}, heat and humidity are elevated together.",
            "tr": f"{ti} ve {humidity} ile sıcaklık ve nem birlikte yüksek.",
        }[lang]
    elif need == "temperature":
        if room_color == "green" and level <= 1:
            inside = {
                "de": f"Die Raumtemperatur liegt bei {ti}, der Sollwert bei {target}. Die Abweichung ist noch klein – aktuell musst du deshalb nicht lüften.",
                "en": f"Room temperature is {ti}, with a target of {target}. The difference is still small, so there is no need to ventilate yet.",
                "tr": f"Oda sıcaklığı {ti}, hedef {target}. Fark hâlâ küçük; şimdilik havalandırmak gerekmiyor.",
            }[lang]
        else:
            inside = {
                "de": f"Die Raumtemperatur liegt bei {ti} statt nahe am Sollwert von {target}. Lüften kann sie wieder Richtung Soll bewegen.",
                "en": f"Room temperature is {ti}, away from the target of {target}. Ventilation can move it back toward the target.",
                "tr": f"Oda sıcaklığı {ti}, hedef ise {target}. Havalandırma sıcaklığı yeniden hedefe yaklaştırabilir.",
            }[lang]
    elif need == "routine":
        inside = {
            "de": f"Seit rund {hours} Stunden wurde keine bestätigte Lüftung erkannt. Damit gibt es einen zusätzlichen Grund für einen kurzen Luftaustausch.",
            "en": f"No confirmed airing has been detected for about {hours} hours. That adds a reason for a short air exchange.",
            "tr": f"Yaklaşık {hours} saattir doğrulanmış havalandırma algılanmadı. Bu, kısa bir hava değişimi için ek bir neden oluşturuyor.",
        }[lang]
    else:
        inside = {
            "de": "Die Innenwerte geben aktuell keinen relevanten Grund zum Lüften.",
            "en": "The indoor values do not indicate a relevant reason to ventilate right now.",
            "tr": "İç değerler şu anda belirgin bir havalandırma nedeni göstermiyor.",
        }[lang]

    # Keep the front of the card short: add only the outdoor factor that best
    # explains why the same engine judgement looks calmer/stronger in this view.
    outside = ""
    if mode in {"aussen_deutlich_feuchter", "feuchte_warten", "schimmel_warten"} or caution == "humidity":
        if ventilation_color == "green" and level > 0 and caution == "humidity":
            outside = {
                "de": " Die Außenluft ist zwar feuchter, trotzdem ist Lüften wegen der Innenwerte hier wichtiger.",
                "en": " Outdoor air is more humid, but the indoor values still make ventilation more important here.",
                "tr": " Dış hava daha nemli olsa da iç değerler nedeniyle havalandırmak burada daha önemli.",
            }[lang]
        else:
            outside = {
                "de": " Die Außenluft ist derzeit feuchter und spricht gegen längeres Lüften.",
                "en": " Outdoor air is currently more humid, which argues against prolonged airing.",
                "tr": " Dış hava şu anda daha nemli ve uzun süre havalandırmayı daha az uygun hâle getiriyor.",
            }[lang]
    elif caution == "temperature":
        if ventilation_color == "green" and level > 0:
            outside = {
                "de": " Die Außentemperatur ist zwar ungünstig, trotzdem ist Lüften wegen der Innenwerte hier wichtiger.",
                "en": " The outdoor temperature is unfavorable, but the indoor values still make ventilation more important here.",
                "tr": " Dış sıcaklık elverişsiz olsa da iç değerler nedeniyle havalandırmak burada daha önemli.",
            }[lang]
        else:
            outside = {
                "de": " Die Außentemperatur ist derzeit ungünstig und spricht gegen längeres Lüften.",
                "en": " The outdoor temperature is currently unfavorable and argues against prolonged airing.",
                "tr": " Dış sıcaklık şu anda elverişsiz ve uzun süre havalandırmayı daha az uygun hâle getiriyor.",
            }[lang]
    elif mode == "aussen_zu_warm":
        outside = {
            "de": f" Draußen sind es {ta}; Lüften würde den Raum aktuell eher weiter aufheizen.",
            "en": f" It is {ta} outside; ventilation would currently warm the room further.",
            "tr": f" Dışarısı {ta}; havalandırma şu anda odayı daha da ısıtır.",
        }[lang]
    elif mode == "aussen_zu_kalt":
        outside = {
            "de": f" Draußen sind es {ta}; längeres Lüften würde den Raum unnötig auskühlen.",
            "en": f" It is {ta} outside; prolonged airing would cool the room unnecessarily.",
            "tr": f" Dışarısı {ta}; uzun havalandırma odayı gereksiz yere soğutur.",
        }[lang]
    elif mode in {"luftqualitaet_maessig", "luftqualitaet_schlecht", "luftqualitaet_sehr_schlecht", "luftqualitaet_sehr_schlecht_typisch"} or caution == "air_quality":
        outside = {
            "de": " Die Außenluftqualität ist momentan ein Nachteil beim Lüften.",
            "en": " Outdoor air quality currently makes ventilation less favorable.",
            "tr": " Dış hava kalitesi şu anda havalandırmayı daha az uygun hâle getiriyor.",
        }[lang]
    elif caution == "weather_forecast":
        forecast = _short_term_weather_sentence(
            a, lang, expected_change="worsening"
        )
        outside = f" {forecast}" if forecast else {
            "de": " In Kürze werden ungünstigere Wetterbedingungen erwartet.",
            "en": " Less favorable weather is expected shortly.",
            "tr": " Yakında daha elverişsiz hava koşulları bekleniyor.",
        }[lang]
    elif mode in {"regen", "regen_bald"} or caution == "rain":
        if mode == "regen_bald":
            outside = {
                "de": " In Kürze wird Regen erwartet; ein offenes Fenster wäre dann unpraktisch.",
                "en": " Rain is expected shortly, so an open window would soon become impractical.",
                "tr": " Yakında yağmur bekleniyor; açık pencere kısa süre sonra pratik olmayabilir.",
            }[lang]
        else:
            outside = {
                "de": " Draußen regnet es gerade; ein offenes Fenster ist deshalb unpraktisch.",
                "en": " It is raining outside right now, so an open window is impractical.",
                "tr": " Dışarıda şu anda yağmur yağıyor; bu yüzden açık pencere pratik değil.",
            }[lang]
    elif mode == "nina_vorsicht" or caution == "air_warning":
        outside = {
            "de": " Ein aktueller Außenluft-Hinweis spricht gegen unnötiges Lüften.",
            "en": " A current outdoor-air advisory argues against unnecessary ventilation.",
            "tr": " Güncel bir dış hava uyarısı gereksiz havalandırmaya karşı.",
        }[lang]
    elif mode == "wetter_vorsicht" or caution == "weather":
        weather_key = str(a.get("weather_reason_key") or "")
        weather_texts = {
            "weather_thunderstorm_caution": {
                "de": " Die aktuelle Gewitterlage spricht gegen ein offenes Fenster.",
                "en": " The current thunderstorm conditions argue against an open window.",
                "tr": " Mevcut gök gürültülü hava açık pencereye karşı.",
            },
            "weather_thunderstorm_danger": {
                "de": " Draußen gibt es aktuell Gewitter; die Fenster sollten geschlossen bleiben.",
                "en": " There is a thunderstorm outside right now, so the windows should stay closed.",
                "tr": " Dışarıda şu anda gök gürültülü fırtına var; pencereler kapalı kalmalı.",
            },
            "weather_heavy_rain_current": {
                "de": " Draußen regnet es kräftig; ein offenes Fenster ist gerade unpraktisch.",
                "en": " It is raining heavily outside, so an open window is impractical right now.",
                "tr": " Dışarıda kuvvetli yağmur yağıyor; açık pencere şu anda pratik değil.",
            },
            "weather_wind_caution": {
                "de": " Starker Wind macht ein offenes Fenster gerade ungünstig.",
                "en": " Strong wind makes an open window unfavorable right now.",
                "tr": " Kuvvetli rüzgâr açık pencereyi şu anda elverişsiz hâle getiriyor.",
            },
            "weather_hail_caution": {
                "de": " Die aktuelle Hagellage spricht gegen ein offenes Fenster.",
                "en": " The current hail conditions argue against an open window.",
                "tr": " Mevcut dolu durumu açık pencereye karşı.",
            },
        }
        outside = weather_texts.get(weather_key, {
            "de": " Die aktuellen Wetterbedingungen sind fürs Lüften ungünstig.",
            "en": " Current weather conditions are unfavorable for ventilation.",
            "tr": " Mevcut hava koşulları havalandırma için elverişsiz.",
        })[lang]
    elif caution == "outdoor_co2":
        outside = {
            "de": " Der gemessene CO₂-Wert draußen ist im Vergleich ungünstig; der Luftaustausch bringt dafür nur begrenzt etwas.",
            "en": " The measured outdoor CO₂ level is unfavorable by comparison, so air exchange offers only limited benefit for it.",
            "tr": " Ölçülen dış ortam CO₂ değeri karşılaştırmada elverişsiz; bu nedenle hava değişiminin bu açıdan faydası sınırlı olur.",
        }[lang]
    elif caution == "combined":
        outside = {
            "de": " Temperatur und Feuchte draußen sind gleichzeitig deutlich ungünstiger.",
            "en": " Outdoor temperature and humidity are both clearly unfavorable.",
            "tr": " Dış sıcaklık ve nem aynı anda belirgin biçimde elverişsiz.",
        }[lang]
    elif ventilation_color == "green" and level > 0 and room_color != "green":
        outside = {
            "de": " Draußen passen die Bedingungen dafür aktuell gut genug.",
            "en": " Outdoor conditions are currently suitable enough for that.",
            "tr": " Dış koşullar şu anda bunun için yeterince uygun.",
        }[lang]

    if mode in {"wetter_vorsicht", "regen", "regen_bald"} or caution in {
        "weather",
        "rain",
    }:
        improvement = _short_term_weather_sentence(
            a, lang, expected_change="improving"
        )
        if improvement:
            outside += f" {improvement}"

    return inside + outside

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
    m = lambda value, unit, digits=1: _measurement(n(value, digits), unit)

    if key == "room_perspective":
        return _room_perspective_reason(a, lang, temperature_unit)

    if key == "co2_minimum_airing":
        ppm = m(a.get("co2"), "ppm", 0) if a.get("co2") is not None else None
        cautious = bool(a.get("cautious"))
        if lang == "de":
            value = f" CO₂ liegt aktuell bei {ppm}." if ppm else ""
            target = (
                f" Ziel dieser Lüftung sind etwa {m(a.get('co2_target'), 'ppm', 0)}."
                if a.get("co2_target") is not None
                else ""
            )
            tail = (
                " Die bereits bekannten ungünstigen Außenbedingungen sind dabei schon berücksichtigt."
                if cautious
                else ""
            )
            return (
                "Die gestartete CO₂-Lüftung läuft noch keine fünf Minuten. "
                "Lüfte noch kurz weiter, damit der Luftaustausch Zeit hat zu wirken."
                + value
                + target
                + tail
            )
        if lang == "tr":
            value = f" CO₂ şu anda {ppm}." if ppm else ""
            target = (
                f" Bu havalandırmanın hedefi yaklaşık {m(a.get('co2_target'), 'ppm', 0)}."
                if a.get("co2_target") is not None
                else ""
            )
            tail = (
                " Başlangıçta bilinen elverişsiz dış koşullar bu öneride zaten dikkate alındı."
                if cautious
                else ""
            )
            return (
                "Başlatılan CO₂ havalandırması henüz beş dakika sürmedi. "
                "Hava değişiminin etkili olması için biraz daha havalandır."
                + value
                + target
                + tail
            )
        value = f" CO₂ is currently at {ppm}." if ppm else ""
        target = (
            f" This airing session is aiming for about {m(a.get('co2_target'), 'ppm', 0)}."
            if a.get("co2_target") is not None
            else ""
        )
        tail = (
            " The unfavorable outdoor conditions already known at the start are already accounted for."
            if cautious
            else ""
        )
        return (
            "The CO₂ airing session has not yet run for five minutes. "
            "Keep ventilating a little longer so the air exchange has time to work."
            + value
            + target
            + tail
        )

    if key == "continue_airing":
        return _continue_reason(a, lang, temperature_unit)

    if key in {"air_quality_moderate", "air_quality_poor", "air_quality_very_poor"}:
        return _air_quality_reason(key, a, lang)

    if key in {"co2_tradeoff", "comfort_tradeoff"}:
        return _tradeoff_reason(key, a, lang, temperature_unit)

    if key == "co2_ventilate_tradeoff":
        ppm = m(a.get("co2"), "ppm", 0)
        caution = str(a.get("caution") or "conditions")
        detail = {
            "humidity": {"de": "Draußen ist die Luft etwas feuchter.", "en": "Outdoor air is a little more humid.", "tr": "Dış hava biraz daha nemli."},
            "temperature": {"de": "Die Außentemperatur ist gerade ungünstig.", "en": "The outdoor temperature is unfavorable right now.", "tr": "Dış sıcaklık şu anda elverişsiz."},
        }.get(caution, {"de": "Die Außenbedingungen sind gerade ungünstig.", "en": "Outdoor conditions are unfavorable right now.", "tr": "Dış koşullar şu anda elverişsiz."})[lang]
        return {
            "de": f"CO₂ liegt bei {ppm}. Lüften ist trotzdem sinnvoll. {detail}",
            "en": f"CO₂ is at {ppm}. Ventilation still makes sense. {detail}",
            "tr": f"CO₂ {ppm}. Buna rağmen havalandırmak mantıklı. {detail}",
        }[lang]

    if key == "outdoor_co2_worse":
        indoor = m(a.get("co2"), "ppm", 0)
        outdoor = m(a.get("outdoor_co2"), "ppm", 0)
        return {
            "de": f"Drinnen liegt CO₂ bei {indoor}, draußen bei etwa {outdoor}. Ohne anderen Lüftungsgrund würde ein Luftaustausch den CO₂-Wert derzeit eher verschlechtern.",
            "en": f"Indoor CO₂ is {indoor} and outdoor CO₂ is about {outdoor}. Without another reason to air, exchanging air would currently tend to worsen the CO₂ level.",
            "tr": f"İçeride CO₂ {indoor}, dışarıda ise yaklaşık {outdoor}. Başka bir havalandırma nedeni yoksa hava değişimi şu anda CO₂ seviyesini kötüleştirme eğiliminde olur.",
        }[lang]

    if key == "outside_strongly_unhelpful":
        return {
            "de": f"Die Innenwerte liegen bereits im guten Bereich. Draußen sind es {t(a.get('ta'))}; zusätzlich würde sich die Feuchtesituation deutlich verschlechtern. Lass die Fenster lieber geschlossen.",
            "en": f"The room is already in a good range. It is {t(a.get('ta'))} outside and humidity would also get noticeably worse, so keep the windows closed.",
            "tr": f"İçeride durum zaten iyi. Dışarısı {t(a.get('ta'))} ve nem de belirgin biçimde kötüleşir; pencereleri kapalı tutmak daha iyi.",
        }[lang]

    if key == "surface_moisture_persistent_ventilate":
        surface = m(a.get("surface_humidity"), "%", 0)
        return {
            "de": f"An der überwachten Oberfläche liegt die relative Feuchte bei etwa {surface}; der erhöhte Wert hält bereits länger an. Die trockenere Außenluft kann die Feuchte dort senken.",
            "en": f"The monitored surface is at about {surface} relative humidity and the condition has persisted for a longer period. Drier outdoor air can help reduce it.",
            "tr": f"İzlenen yüzeyde bağıl nem yaklaşık {surface} ve bu durum daha uzun süredir devam ediyor. Daha kuru dış hava nemi azaltmaya yardımcı olur.",
        }[lang]

    if key == "surface_moisture_ventilate":
        return {
            "de": "Die trockenere Außenluft kann die Feuchtesituation an der überwachten Oberfläche aktuell verbessern.",
            "en": "The current moisture situation benefits from the drier outdoor air.",
            "tr": "Mevcut nem durumu daha kuru dış havadan fayda görür.",
        }[lang]

    if key == "surface_moisture_wait":
        persistent = bool(a.get("persistent"))
        if persistent:
            return {
                "de": "Die überwachte Oberfläche ist bereits länger kritisch feucht, aber die Außenluft würde die Situation derzeit nicht verbessern.",
                "en": "The monitored surface has remained critically humid for a longer period, but the outdoor air would not improve it right now.",
                "tr": "İzlenen yüzey daha uzun süredir kritik derecede nemli, ancak dış hava şu anda durumu iyileştirmez.",
            }[lang]
        return {
            "de": "Lüften würde die aktuelle Feuchtesituation an der überwachten Oberfläche derzeit nicht verbessern.",
            "en": "Opening the windows would not improve the current moisture situation at the monitored surface right now.",
            "tr": "Pencereleri açmak izlenen yüzeydeki mevcut nem durumunu şu anda iyileştirmez.",
        }[lang]

    if key == "surface_moisture_neutral":
        return {
            "de": "Innen- und Außenluft sind hinsichtlich der Feuchte nahezu ausgeglichen. Lüften ist dafür weder klar hilfreich noch deutlich nachteilig.",
            "en": "Indoor and outdoor air are nearly balanced for the current moisture situation. Airing is neither clearly helpful nor clearly harmful for it.",
            "tr": "İç ve dış hava mevcut nem durumu açısından neredeyse dengeli. Havalandırma ne açıkça faydalı ne de belirgin biçimde zararlı.",
        }[lang]

    if key == "humidity_wait":
        diff = a.get("diff")
        try:
            wetter = float(diff) < -0.5
        except (TypeError, ValueError):
            wetter = False
        if wetter:
            amount = m(abs(float(diff)), "g/m³", 1)
            return {
                "de": f"Die Raumfeuchte ist erhöht, aber die Außenluft enthält etwa {amount} mehr Wasser. Lüften würde die Feuchtesituation derzeit eher verschlechtern.",
                "en": f"Indoor humidity is elevated, but the outdoor air contains about {amount} more water. Airing would currently make the moisture situation worse.",
                "tr": f"İç nem yüksek, ancak dış hava yaklaşık {amount} daha fazla su içeriyor. Havalandırma şu anda nem durumunu kötüleştirebilir.",
            }[lang]
        return {
            "de": "Die Raumfeuchte ist erhöht, aber die Außenluft bietet aktuell keinen verlässlichen Trocknungsvorteil. Warte besser noch etwas.",
            "en": "Indoor humidity is elevated, but the outdoor air currently offers no reliable drying benefit. It is better to wait a little longer.",
            "tr": "İç nem yüksek, ancak dış hava şu anda güvenilir bir kurutma avantajı sunmuyor. Biraz daha beklemek daha iyi.",
        }[lang]

    if key == "humidity_neutral":
        return {
            "de": f"Die Raumfeuchte liegt bei {m(a.get('humidity'), '%', 0)}, die absolute Feuchte ist innen und außen aber nahezu gleich. Lüften würde daran kaum etwas ändern.",
            "en": f"Indoor relative humidity is {m(a.get('humidity'), '%', 0)}, but absolute humidity indoors and outdoors is very similar. Airing would hardly change it.",
            "tr": f"İç bağıl nem {m(a.get('humidity'), '%', 0)}, ancak içeride ve dışarıda mutlak nem birbirine çok yakın. Havalandırma nemi pek değiştirmez.",
        }[lang]

    if key in {"weather_wind_caution", "weather_wind_danger"}:
        speed = a.get("speed_kmh")
        speed_text = f" ({m(speed, 'km/h', 0)})" if speed is not None else ""
        danger = key.endswith("danger")
        if danger:
            return {
                "de": f"Wind bzw. Böen sind aktuell sehr kräftig{speed_text}. Ein offenes Fenster ist unter diesen Bedingungen ungünstig; lass es besser geschlossen.",
                "en": f"Wind or gusts are very strong right now{speed_text}. An open window is unfavorable in these conditions, so keep it closed.",
                "tr": f"Rüzgâr veya rüzgâr hamleleri şu anda çok kuvvetli{speed_text}. Bu koşullarda pencereyi açık bırakmak uygun değil; kapalı tutmak daha iyi.",
            }[lang]
        return {
            "de": f"Es ist deutlich windig{speed_text}. Lüften ist möglich, aber sichere das Fenster und behalte die Situation im Blick.",
            "en": f"It is noticeably windy{speed_text}. Airing is possible, but secure the window and keep an eye on conditions.",
            "tr": f"Hava belirgin biçimde rüzgârlı{speed_text}. Havalandırma mümkün, ancak pencereyi sabitlemek ve durumu izlemek gerekir.",
        }[lang]

    if key == "rain_soon" and a.get("minutes") is not None:
        minutes = max(0, round(float(a.get("minutes"))))
        return {
            "de": f"In etwa {minutes} Minuten wird Niederschlag erwartet und könnte während der Lüftung einsetzen. Wenn es nicht dringend ist, warte besser kurz.",
            "en": f"Precipitation is expected in about {minutes} minutes and may begin while the windows are open. If it is not urgent, wait a little.",
            "tr": f"Yaklaşık {minutes} dakika içinde yağış bekleniyor ve pencereler açıkken başlayabilir. Acil değilse biraz beklemek daha iyi.",
        }[lang]

    if key == "weather_forecast_worsening":
        forecast = _short_term_weather_sentence(
            a, lang, expected_change="worsening"
        )
        if forecast:
            return {
                "de": f"{forecast} Wenn Lüften nicht dringend nötig ist, warte besser noch etwas.",
                "en": f"{forecast} If ventilation is not urgent, it is better to wait a little.",
                "tr": f"{forecast} Havalandırma acil değilse biraz beklemek daha iyi.",
            }[lang]

    if lang == "de":
        texts = {
            "official_close_instruction": "Eine offizielle Warnquelle weist ausdrücklich an, Fenster und Türen geschlossen zu halten oder die Außenluftzufuhr abzuschalten. Diese Schutzanweisung hat Vorrang vor der normalen Lüftungsbewertung.",
            "nina_air_danger": "Für die Außenluft liegt aktuell eine relevante Warnung vor. Lass Fenster und Türen deshalb besser geschlossen.",
            "nina_air_caution": "Für die Außenluft gilt aktuell ein Vorsichtshinweis. Lüfte im Moment besser nur, wenn es wirklich nötig ist.",
            "air_smoke_danger": "In der Umgebung wird Rauch oder Brandrauch gemeldet. Lass Fenster und Türen besser geschlossen, damit möglichst wenig davon hereinkommt.",
            "air_smoke_caution": "In der Umgebung wird Rauch oder Brandrauch gemeldet. Wenn es nicht dringend nötig ist, warte mit dem Lüften besser noch etwas.",
            "air_hazard_danger": "Es gibt eine Warnung vor Schadstoffen oder einem Gasaustritt in der Außenluft. Lass Fenster und Türen deshalb geschlossen.",
            "air_hazard_caution": "Es gibt einen Hinweis auf mögliche Schadstoffe in der Außenluft. Lüfte vorsichtshalber nur, wenn es wirklich nötig ist.",
            "weather_danger": "Aktuell gilt eine Unwetterwarnung, bei der offene Fenster ungünstig sind. Lass sie vorerst geschlossen.",
            "weather_caution": "Die Wetterlage ist aktuell ungünstig für ein offenes Fenster. Wenn Lüften nicht nötig ist, warte besser noch etwas.",
            "weather_heavy_rain_current": "Draußen regnet es gerade kräftig. Wenn Lüften nicht nötig ist, warte besser, bis der Regen nachlässt.",
            "weather_heavy_rain_caution": "Es wird vor Starkregen gewarnt. Wenn es nicht dringend nötig ist, warte mit dem Lüften besser noch etwas.",
            "weather_heavy_rain_danger": "Es gilt eine Unwetterwarnung vor heftigem Starkregen. Lass die Fenster besser geschlossen, bis sich die Lage beruhigt.",
            "weather_continuous_rain_caution": "Es wird vor länger anhaltendem kräftigem Regen gewarnt. Wenn es nicht nötig ist, warte mit dem Lüften besser noch etwas.",
            "weather_continuous_rain_danger": "Es gilt eine Unwetterwarnung vor ergiebigem Dauerregen. Lass die Fenster vorerst besser geschlossen.",
            "weather_thunderstorm_caution": "Bei der aktuellen Gewitterlage ist ein offenes Fenster ungünstig. Warte wenn möglich mit dem Lüften, bis es ruhiger ist.",
            "weather_thunderstorm_danger": "Aktuell spricht eine Gewitterlage klar gegen offene Fenster. Lass die Fenster geschlossen, bis es wieder ruhiger ist.",
            "weather_hail_caution": "Es besteht eine Hagelwarnung. Wenn möglich, lass die Fenster geschlossen, bis die Warnung vorbei ist.",
            "weather_hail_danger": "Es gilt eine Unwetterwarnung mit Hagel. Lass die Fenster geschlossen, bis die Lage vorbei ist.",
            "weather_storm_caution": "Es wird vor stürmischem Wetter gewarnt. Offene Fenster sind gerade keine gute Idee; warte besser noch etwas.",
            "weather_storm_danger": "Es gilt eine Unwetterwarnung vor Sturm. Lass Fenster und Türen geschlossen, bis sich die Lage beruhigt.",
            "weather_wind_caution": "Es wird vor starkem Wind gewarnt. Lüften ist gerade eher ungünstig; warte wenn möglich noch etwas.",
            "weather_wind_danger": "Es gilt eine Unwetterwarnung vor starkem Wind. Lass die Fenster besser geschlossen.",
            "weather_exceptional_danger": "Der Wetterdienst meldet eine außergewöhnliche Wetterlage. Lass die Fenster vorsichtshalber geschlossen.",
            "airing_finished": "Der Luftaustausch reicht im Moment aus. Du kannst die Fenster wieder schließen.",
            "co2_critical_rain": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist damit sehr hoch. Trotz des Regens ist ein kurzer Luftaustausch sinnvoll – aber nur kurz und unter Beobachtung.",
            "co2_critical": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist damit sehr hoch. Jetzt zu lüften hat klare Priorität.",
            "co2_ventilate": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist erhöht. Draußen passen die Bedingungen, deshalb lohnt sich jetzt ein Luftaustausch.",
            "co2_wait": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist erhöht. Die Außenbedingungen sind gerade aber ungünstig, deshalb ist kurzes Warten die bessere Wahl.",
            "mold_prevention": f"An der überwachten kalten Oberfläche liegt die berechnete relative Feuchte bei etwa {m(a.get('surface_humidity'), '%', 0)}. Da die Außenluft trockener ist, hilft Lüften dabei, die Feuchte dort wieder zu senken.",
            "mold_wait": f"An der überwachten kalten Oberfläche liegt die berechnete relative Feuchte bei etwa {m(a.get('surface_humidity'), '%', 0)}. Lüften würde die Feuchte im Moment aber nicht zuverlässig verbessern; behalte die Situation im Blick.",
            "humidity_ventilate": f"Die relative Luftfeuchtigkeit innen liegt bei {m(a.get('humidity'), '%', 0)}. Draußen enthält die Luft rund {m(a.get('diff'), 'g/m³')} weniger Wasser – Lüften hilft also beim Trocknen.",
            "humidity_wait": "Die Luftfeuchte drinnen ist erhöht, draußen gibt es im Moment aber kaum einen Trocknungsvorteil. Warte besser noch etwas.",
            "cooling": f"Drinnen sind es {t(a.get('ti'))}, bei einem Soll von {t(a.get('target'))}. Draußen sind es {t(a.get('ta'))} – Lüften hilft jetzt beim Abkühlen.",
            "warming": f"Drinnen sind es {t(a.get('ti'))}, bei einem Soll von {t(a.get('target'))}. Draußen ist es wärmer und kann den Raum beim Lüften Richtung Solltemperatur bringen.",
            "routine_ventilate": f"Seit rund {n(a.get('hours'), 1)} Stunden wurde keine bestätigte Lüftung erfasst. Die Außenbedingungen passen gerade gut, deshalb ist jetzt ein kurzer Luftaustausch sinnvoll.",
            "routine_wait": f"Seit rund {n(a.get('hours'), 1)} Stunden wurde keine bestätigte Lüftung erfasst. Die Bedingungen draußen passen gerade aber nicht gut genug – warte lieber noch etwas.",
            "outside_too_hot": f"Drinnen sind es {t(a.get('ti'))}, draußen {t(a.get('ta'))}. Beim Lüften würdest du gerade zusätzliche Wärme hereinholen – die Fenster bleiben besser zu.",
            "outside_too_cold": f"Drinnen sind es {t(a.get('ti'))}, draußen {t(a.get('ta'))}. Lüften würde den Raum gerade unnötig auskühlen – deshalb besser geschlossen lassen.",
            "outside_more_humid": f"Die Außenluft enthält rund {m(a.get('amount'), 'g/m³')} mehr Wasser als die Luft drinnen. Lüften würde aktuell eher Feuchte hineinbringen als abführen.",
            "inside_too_dry": "Die Luft drinnen ist bereits ziemlich trocken. Lüften würde sie im Moment noch weiter austrocknen – deshalb besser warten.",
            "rain_now": "Draußen fällt gerade Niederschlag. Das verändert den Trocknungseffekt nicht automatisch, macht ein offenes Fenster aber unpraktischer. Wenn Lüften nicht nötig ist, warte besser kurz.",
            "rain_soon": "In Kürze wird Niederschlag erwartet. Wenn es nicht dringend nötig ist, ist ein etwas späterer Zeitpunkt zum Lüften wahrscheinlich besser.",
            "normal": "Aktuell gibt es keinen klaren Grund zum Lüften, und die Außenbedingungen bringen keinen deutlichen Vorteil. Lüften ist möglich, aber nicht nötig.",
            "incomplete_data": "Mindestens ein benötigter Temperatur- oder Feuchtewert ist gerade nicht verfügbar. Sobald die Sensordaten wieder vollständig sind, wird die Empfehlung automatisch aktualisiert.",
        }
    elif lang == "tr":
        texts = {
            "official_close_instruction": "Resmî bir uyarı kaynağı pencerelerin ve kapıların kapalı tutulmasını veya dış hava girişinin kapatılmasını açıkça istiyor. Bu koruma talimatı normal havalandırma değerlendirmesinden önceliklidir.",
            "nina_air_danger": "Dış havayı etkileyen önemli bir uyarı var. Bu yüzden pencereleri ve kapıları şimdilik kapalı tutman daha iyi.",
            "nina_air_caution": "Dış havayla ilgili bir dikkat uyarısı var. Gerçekten gerekmedikçe şimdilik pencereleri açmamak daha iyi.",
            "air_smoke_danger": "Yakın çevrede duman veya yangın dumanı bildiriliyor. İçeri mümkün olduğunca az girmesi için pencereleri ve kapıları kapalı tut.",
            "air_smoke_caution": "Yakın çevrede duman veya yangın dumanı bildiriliyor. Acil değilse pencereleri açmadan önce biraz daha beklemek daha iyi.",
            "air_hazard_danger": "Dış havada zararlı madde veya gaz kaçağına ilişkin bir uyarı var. Pencereleri ve kapıları şimdilik kapalı tut.",
            "air_hazard_caution": "Dış havada olası kirletici maddelere ilişkin bir uyarı var. Gerçekten gerekmedikçe şimdilik pencereleri açma.",
            "weather_danger": "Ciddi bir hava durumu uyarısı aktif ve pencereleri açık bırakmak uygun değil. Koşullar düzelene kadar pencereleri kapalı tut.",
            "weather_caution": "Hava koşulları şu anda açık pencere için elverişsiz. Havalandırma gerekli değilse biraz beklemek daha iyi.",
            "weather_heavy_rain_current": "Dışarıda şu anda kuvvetli yağmur yağıyor. Havalandırma gerekli değilse yağmur azalıncaya kadar beklemek daha iyi.",
            "weather_heavy_rain_caution": "Kuvvetli yağmur uyarısı var. Acil değilse pencereleri açmadan önce biraz daha beklemek daha iyi.",
            "weather_heavy_rain_danger": "Çok şiddetli yağmur için ciddi hava uyarısı var. Koşullar sakinleşene kadar pencereleri kapalı tut.",
            "weather_continuous_rain_caution": "Uzun süreli kuvvetli yağmur uyarısı var. Gerekli değilse pencereleri açmadan önce biraz daha bekle.",
            "weather_continuous_rain_danger": "Uzun süreli ve çok yoğun yağmur için ciddi hava uyarısı var. Pencereleri şimdilik kapalı tut.",
            "weather_thunderstorm_caution": "Mevcut gök gürültülü havada pencereyi açık bırakmak uygun değil. Mümkünse hava sakinleşene kadar bekle.",
            "weather_thunderstorm_danger": "Gök gürültülü hava şu anda açık pencereler için uygun değil. Hava sakinleşene kadar pencereleri kapalı tut.",
            "weather_hail_caution": "Dolu uyarısı var. Mümkünse uyarı geçene kadar pencereleri kapalı tut.",
            "weather_hail_danger": "Dolu içeren ciddi bir hava uyarısı var. Geçene kadar pencereleri kapalı tut.",
            "weather_storm_caution": "Fırtınalı hava bekleniyor. Açık pencereler şu anda iyi fikir değil; biraz daha beklemek daha iyi.",
            "weather_storm_danger": "Şiddetli fırtına uyarısı var. Koşullar sakinleşene kadar pencereleri ve kapıları kapalı tut.",
            "weather_wind_caution": "Kuvvetli rüzgâr uyarısı var. Şu anda pencereleri açmak pek uygun değil; mümkünse biraz daha bekle.",
            "weather_wind_danger": "Çok kuvvetli rüzgâr için ciddi bir uyarı var. Pencereleri kapalı tutmak daha iyi.",
            "weather_exceptional_danger": "Hava durumu hizmeti olağan dışı koşullar bildiriyor. Önlem olarak pencereleri kapalı tut.",
            "airing_finished": "Şimdilik yeterince hava değişimi oldu. Pencereleri tekrar kapatabilirsin.",
            "co2_critical_rain": f"CO₂ seviyesi {m(a.get('co2'), 'ppm', 0)} ve bu oldukça yüksek. Yağmura rağmen kısa bir hava değişimi faydalı olur; pencereleri kısa süre açık tutup durumu gözlemle.",
            "co2_critical": f"CO₂ seviyesi {m(a.get('co2'), 'ppm', 0)} ve bu oldukça yüksek. Şimdi pencereleri açmak öncelikli.",
            "co2_ventilate": f"CO₂ seviyesi {m(a.get('co2'), 'ppm', 0)} ve yükselmiş durumda. Dışarıdaki koşullar uygun; pencereleri açıp havayı değiştirmek için iyi bir zaman.",
            "co2_wait": f"CO₂ seviyesi {m(a.get('co2'), 'ppm', 0)} ve yükselmiş durumda, ancak dışarıdaki koşullar şu an uygun değil. Biraz beklemek daha iyi.",
            "mold_prevention": f"İzlenen soğuk yüzeyde hesaplanan bağıl nem yaklaşık {m(a.get('surface_humidity'), '%', 0)}. Dış hava daha kuru olduğu için pencereleri açmak yüzey çevresindeki nemi azaltmaya yardımcı olur.",
            "mold_wait": f"İzlenen soğuk yüzeyde hesaplanan bağıl nem yaklaşık {m(a.get('surface_humidity'), '%', 0)}. Şu anda pencereleri açmak nemi güvenilir biçimde azaltmayacağından durumu takip etmek daha iyi.",
            "humidity_ventilate": f"İçeride bağıl nem {m(a.get('humidity'), '%', 0)}. Dış hava yaklaşık {m(a.get('diff'), 'g/m³')} daha az su içeriyor; pencereleri açmak odanın kurumasına yardımcı olur.",
            "humidity_wait": "İçeride nem yüksek, ancak dış hava şu anda odayı belirgin şekilde kurutacak kadar avantajlı değil. Biraz daha beklemek daha iyi.",
            "cooling": f"İçeride sıcaklık {t(a.get('ti'))}, hedefin ise {t(a.get('target'))}. Dışarısı {t(a.get('ta'))}; pencereleri açmak odayı serinletmeye yardımcı olur.",
            "warming": f"İçeride sıcaklık {t(a.get('ti'))}, hedefin ise {t(a.get('target'))}. Dışarısı daha sıcak; pencereleri açmak odayı hedef sıcaklığa yaklaştırmaya yardımcı olabilir.",
            "routine_ventilate": f"Yaklaşık {n(a.get('hours'), 1)} saattir doğrulanmış bir havalandırma kaydedilmedi. Dışarıdaki koşullar uygun, bu yüzden kısa bir hava değişimi iyi olur.",
            "routine_wait": f"Yaklaşık {n(a.get('hours'), 1)} saattir doğrulanmış bir havalandırma kaydedilmedi, ancak dışarıdaki koşullar şu anda yeterince uygun değil. Biraz daha beklemek daha iyi.",
            "outside_too_hot": f"İçeride {t(a.get('ti'))}, dışarıda {t(a.get('ta'))}. Pencereleri açmak şu anda içeri ekstra sıcaklık getirir; kapalı tutmak daha iyi.",
            "outside_too_cold": f"İçeride {t(a.get('ti'))}, dışarıda {t(a.get('ta'))}. Pencereleri açmak odayı gereksiz yere soğutur; kapalı tutmak daha iyi.",
            "outside_more_humid": f"Dış hava, içerideki havadan yaklaşık {m(a.get('amount'), 'g/m³')} daha fazla su içeriyor. Pencereleri açmak nemi dışarı atmak yerine içeri getirir.",
            "inside_too_dry": "İçerideki hava zaten oldukça kuru. Pencereleri açmak şu anda havayı daha da kurutur; biraz beklemek daha iyi.",
            "rain_now": "Dışarıda şu anda yağış var. Bu, kurutma etkisini belirlemez ancak açık pencereyi daha az pratik hâle getirir; havalandırma gerekmiyorsa beklemek daha iyi.",
            "rain_soon": "Kısa süre içinde yağış bekleniyor. Acil değilse pencereleri biraz daha sonra açmak muhtemelen daha iyi olur.",
            "normal": "Şu anda odayı havalandırmak için açık bir neden yok ve dış koşullar belirgin bir avantaj sağlamıyor. Havalandırmak mümkün, ancak gerekli değil.",
            "incomplete_data": "Gerekli sıcaklık veya nem değerlerinden en az biri şu anda kullanılamıyor. Sensör verileri tekrar tamamlandığında öneri otomatik olarak güncellenecek.",
        }
    else:
        texts = {
            "official_close_instruction": "An official warning source explicitly instructs you to keep windows and doors closed or switch off the outdoor-air supply. This protection instruction takes priority over the normal ventilation assessment.",
            "nina_air_danger": "There is an active warning affecting the outdoor air. It is better to keep windows and doors closed for now.",
            "nina_air_caution": "There is currently an advisory affecting the outdoor air. Unless you really need fresh air, it is better to keep the windows closed for now.",
            "air_smoke_danger": "Smoke or fire smoke has been reported nearby. Keep windows and doors closed to reduce how much of it gets indoors.",
            "air_smoke_caution": "Smoke or fire smoke has been reported nearby. Unless opening the windows is urgent, it is better to wait a little longer.",
            "air_hazard_danger": "There is a warning about hazardous substances or a gas release in the outdoor air. Keep windows and doors closed for now.",
            "air_hazard_caution": "There is an advisory about possible pollutants in the outdoor air. Unless you really need fresh air, keep the windows closed for now.",
            "weather_danger": "A severe-weather warning is active and open windows are unfavorable. Keep them closed until conditions improve.",
            "weather_caution": "Current weather is unfavorable for an open window. If ventilation is not needed, it is better to wait a little.",
            "weather_heavy_rain_current": "It is raining heavily outside. If ventilation is not needed, it is better to wait until the rain eases.",
            "weather_heavy_rain_caution": "There is a heavy-rain warning. Unless opening the windows is urgent, it is better to wait a little longer.",
            "weather_heavy_rain_danger": "A severe-weather warning for intense heavy rain is active. Keep the windows closed until conditions settle down.",
            "weather_continuous_rain_caution": "There is a warning for prolonged heavy rain. Unless fresh air is really needed, it is better to wait a little longer.",
            "weather_continuous_rain_danger": "A severe-weather warning for prolonged heavy rain is active. Keep the windows closed for now.",
            "weather_thunderstorm_caution": "An open window is a poor choice during the current thunderstorm conditions. If possible, wait until conditions calm down.",
            "weather_thunderstorm_danger": "Thunderstorm conditions currently make open windows a bad idea. Keep them closed until conditions calm down.",
            "weather_hail_caution": "There is a hail warning. If possible, keep the windows closed until the warning has passed.",
            "weather_hail_danger": "A severe-weather warning with hail is active. Keep the windows closed until it has passed.",
            "weather_storm_caution": "Stormy weather is expected. Open windows are not a good idea right now, so it is better to wait.",
            "weather_storm_danger": "A severe storm warning is active. Keep windows and doors closed until conditions settle down.",
            "weather_wind_caution": "There is a strong-wind warning. Opening the windows is not ideal right now; wait a little longer if you can.",
            "weather_wind_danger": "A severe strong-wind warning is active. It is better to keep the windows closed.",
            "weather_exceptional_danger": "The weather service is reporting exceptional conditions. Keep the windows closed as a precaution.",
            "airing_finished": "The air exchange is sufficient for now. You can close the windows again.",
            "co2_critical_rain": f"CO₂ is at {m(a.get('co2'), 'ppm', 0)}, which is very high. A short air exchange is still worthwhile despite the rain, but keep it brief and monitor the situation.",
            "co2_critical": f"CO₂ is at {m(a.get('co2'), 'ppm', 0)}, which is very high. Opening the windows now should take priority.",
            "co2_ventilate": f"CO₂ is at {m(a.get('co2'), 'ppm', 0)} and is elevated. Outdoor conditions are suitable, so this is a good time to open the windows and exchange the air.",
            "co2_wait": f"CO₂ is at {m(a.get('co2'), 'ppm', 0)} and is elevated, but outdoor conditions are unfavorable right now. Waiting briefly is the better choice.",
            "mold_prevention": f"The calculated relative humidity at the monitored cold surface is about {m(a.get('surface_humidity'), '%', 0)}. Because the outdoor air is drier, opening the windows will help lower the moisture level there.",
            "mold_wait": f"The calculated relative humidity at the monitored cold surface is about {m(a.get('surface_humidity'), '%', 0)}. Opening the windows would not reliably improve it right now, so keep an eye on the situation for the moment.",
            "humidity_ventilate": f"Indoor relative humidity is {m(a.get('humidity'), '%', 0)}. The outdoor air contains about {m(a.get('diff'), 'g/m³')} less water, so opening the windows will help dry the room.",
            "humidity_wait": "Indoor humidity is elevated, but the outdoor air offers very little drying benefit right now. It is better to wait a little longer.",
            "cooling": f"It is {t(a.get('ti'))} indoors, while your target is {t(a.get('target'))}. It is {t(a.get('ta'))} outside, so opening the windows will help cool the room down.",
            "warming": f"It is {t(a.get('ti'))} indoors, while your target is {t(a.get('target'))}. It is warmer outside, so opening the windows can help bring the room closer to your target.",
            "routine_ventilate": f"No confirmed window airing has been recorded for about {n(a.get('hours'), 1)} hours. Outdoor conditions are good, so a short air exchange makes sense now.",
            "routine_wait": f"No confirmed window airing has been recorded for about {n(a.get('hours'), 1)} hours, but outdoor conditions are not good enough right now. It is better to wait a little longer.",
            "outside_too_hot": f"It is {t(a.get('ti'))} indoors and {t(a.get('ta'))} outside. Opening the windows now would bring extra heat in, so it is better to keep them closed.",
            "outside_too_cold": f"It is {t(a.get('ti'))} indoors and {t(a.get('ta'))} outside. Opening the windows now would cool the room unnecessarily, so it is better to keep them closed.",
            "outside_more_humid": f"The outdoor air contains about {m(a.get('amount'), 'g/m³')} more water than the indoor air. Opening the windows would bring moisture in rather than remove it.",
            "inside_too_dry": "The indoor air is already quite dry. Opening the windows now would dry it out even further, so it is better to wait.",
            "rain_now": "Precipitation is falling outside right now. It does not determine the drying effect, but it makes an open window less practical; if airing is not needed, wait.",
            "rain_soon": "Precipitation is expected shortly. Unless opening the windows is urgent, a slightly later time will probably be better.",
            "normal": "There is no clear reason to air the room right now, and the outdoor conditions offer no clear advantage. Airing is possible, but not necessary.",
            "incomplete_data": "At least one required temperature or humidity value is unavailable right now. The recommendation will update automatically as soon as the sensor data is complete again.",
        }

    text = texts.get(key, key)
    if key.startswith("weather_") or key in {"rain_now"}:
        improvement = _short_term_weather_sentence(
            a, lang, expected_change="improving"
        )
        if improvement:
            text = f"{text} {improvement}"
    return text



def _clock(value: Any, lang: str) -> str:
    from datetime import datetime
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return "?"
    if not isinstance(value, datetime):
        return "?"
    return value.strftime("%H:%M") if lang in {"de", "tr"} else value.strftime("%H:%M")


def night_advice_text(
    key: str | None,
    args: dict[str, Any] | None,
    language: str | None,
    temperature_unit: str = "°C",
) -> str:
    """Render a short, natural night strategy rather than a technical forecast."""
    if not key:
        return ""
    lang = normalize_language(language)
    a = args or {}
    start = _clock(a.get("start_time"), lang)
    end = _clock(a.get("end_time"), lang)
    thermal = bool(a.get("thermal_need"))
    humidity = bool(a.get("humidity_need"))
    drier = bool(a.get("humidity_advantage"))

    if thermal and drier:
        change = {
            "de": "kühler und trockener",
            "en": "cooler and drier",
            "tr": "daha serin ve daha kuru",
        }[lang]
    elif thermal:
        change = {"de": "kühler", "en": "cooler", "tr": "daha serin"}[lang]
    elif humidity:
        change = {"de": "trockener", "en": "drier", "tr": "daha kuru"}[lang]
    else:
        change = {"de": "passender", "en": "better", "tr": "daha uygun"}[lang]

    if key == "night_now":
        return {
            "de": f"🌙 Heute Nacht lüften: Draußen ist es bereits {change}. Bis etwa {end} bleiben die Bedingungen voraussichtlich günstig.",
            "en": f"🌙 Ventilate tonight: it is already {change} outside. Conditions should remain suitable until around {end}.",
            "tr": f"🌙 Bu gece havalandır: dışarısı şimdiden {change}. Koşulların yaklaşık {end} saatine kadar uygun kalması bekleniyor.",
        }[lang]
    if key == "night_later":
        return {
            "de": f"🌙 Später lüften: Ab etwa {start} wird es draußen deutlich {change}. Bis dahin kannst du die Fenster geschlossen lassen.",
            "en": f"🌙 Air later: from around {start}, it should become noticeably {change} outside. Keep the windows closed until then.",
            "tr": f"🌙 Daha sonra havalandır: yaklaşık {start} itibarıyla dışarısı belirgin şekilde {change} olacak. O zamana kadar pencereleri kapalı tutabilirsin.",
        }[lang]
    if key in {"night_now_conditional", "night_later_conditional"}:
        details: list[str] = []
        if a.get("rain_risk"):
            details.append({"de": "Regen möglich", "en": "rain is possible", "tr": "yağmur olabilir"}[lang])
        if a.get("humidity_disadvantage"):
            details.append({"de": "Außenluft eher feuchter", "en": "outdoor air is more humid", "tr": "dış hava daha nemli"}[lang])
        if a.get("weather_caution"):
            details.append({"de": "Wetterhinweis aktiv", "en": "a weather advisory is active", "tr": "hava durumu uyarısı aktif"}[lang])
        if a.get("air_warning"):
            details.append({"de": "Außenluft-Hinweis aktiv", "en": "an outdoor-air advisory is active", "tr": "dış hava uyarısı aktif"}[lang])
        if str(a.get("air_quality")) in {"moderate", "poor", "very_poor"}:
            details.append({"de": "Außenluft belastet", "en": "outdoor air is polluted", "tr": "dış hava kirli"}[lang])
        detail = ", ".join(details) or {
            "de": "ein paar Punkte sprechen dagegen",
            "en": "there are a few drawbacks",
            "tr": "bazı noktalar buna karşı",
        }[lang]
        if key == "night_later_conditional":
            return {
                "de": f"🌙 Später könnte sich Lüften lohnen: Ab etwa {start} wird es draußen {change}. Allerdings: {detail}.",
                "en": f"🌙 Ventilation may make sense later: from around {start}, it should be {change} outside. However: {detail}.",
                "tr": f"🌙 Daha sonra havalandırmak işe yarayabilir: yaklaşık {start} itibarıyla dışarısı {change} olacak. Ancak: {detail}.",
            }[lang]
        return {
            "de": f"🌙 Heute Nacht könnte Lüften sinnvoll sein, allerdings mit Einschränkungen: {detail}.",
            "en": f"🌙 Ventilation tonight may make sense, but there are some drawbacks: {detail}.",
            "tr": f"🌙 Bu gece havalandırmak mantıklı olabilir, ancak bazı kısıtlamalar var: {detail}.",
        }[lang]
    if key == "night_blocked":
        return {
            "de": "🌙 Heute Nacht lieber nicht länger lüften: Wind, Wetter oder eine Warnung sprechen klar dagegen.",
            "en": "🌙 Better avoid long airing tonight: wind, weather, or an active warning clearly argues against it.",
            "tr": "🌙 Bu gece uzun süre havalandırmamak daha iyi: rüzgâr, hava koşulları veya aktif bir uyarı buna açıkça karşı.",
        }[lang]
    if key == "night_air_too_bad":
        return {
            "de": "🌙 Heute Nacht lieber nicht länger lüften: Die Außenluft ist gerade sehr stark belastet.",
            "en": "🌙 Better avoid long airing tonight: outdoor air is heavily polluted right now.",
            "tr": "🌙 Bu gece uzun süre havalandırmamak daha iyi: dış hava şu anda çok kirli.",
        }[lang]
    return ""


def localized_bundle(
    recommendation_key: str,
    reason_key: str,
    reason_args: dict[str, Any],
    duration_key: str,
    temperature_unit: str,
    night_key: str | None = None,
    night_args: dict[str, Any] | None = None,
) -> dict[str, dict[str, str]]:
    """Render all bundled languages for per-user frontend selection."""
    return {
        language: {
            "recommendation": recommendation_text(recommendation_key, language),
            "reason": reason_text(reason_key, reason_args, language, temperature_unit),
            "duration": duration_text(duration_key, language),
            "night": night_advice_text(night_key, night_args, language, temperature_unit),
        }
        for language in SUPPORTED_LANGUAGES
    }

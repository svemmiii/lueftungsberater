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
        "short_observation": "Nur kurz lüften und im Blick behalten",
        "optional": "Lüften ist optional",
        "better_close": "Besser schließen",
        "caution_keep_closed": "Vorsicht – lieber geschlossen lassen",
        "keep_closed": "Geschlossen lassen",
        "close_now": "Jetzt schließen",
        "wait": "Besser noch etwas warten",
        "unknown": "Aktuell keine zuverlässige Empfehlung möglich",
    },
    "en": {
        "open_now": "Open the windows now",
        "keep_open": "Keep the windows open a little longer",
        "can_close": "You can close the windows now",
        "short_observation": "Open the windows briefly and keep an eye on it",
        "optional": "Airing is optional",
        "better_close": "Better close the windows",
        "caution_keep_closed": "Better keep the windows closed for now",
        "keep_closed": "Keep the windows closed",
        "close_now": "Close the windows now",
        "wait": "Better wait a little longer",
        "unknown": "No reliable recommendation is available right now",
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
    },
}

DURATIONS = {
    "de": {
        "until_targets": "Bis die offenen Lüftungsziele erreicht sind",
        "can_end": "Die Lüftung kann jetzt beendet werden",
        "brief_observation": "Etwa 5 Minuten und dabei die Situation im Blick behalten",
        "co2_recheck": "5–10 Minuten, danach CO₂ erneut prüfen",
        "co2_until_good": "5–10 Minuten bzw. bis CO₂ unter etwa 1000 ppm fällt",
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
        "brief_observation": "About 5 minutes while keeping an eye on the conditions",
        "co2_recheck": "5–10 minutes, then check CO₂ again",
        "co2_until_good": "5–10 minutes, or until CO₂ drops below roughly 1000 ppm",
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
        "co2_until_good": "5–10 dakika veya CO₂ yaklaşık 1000 ppm'in altına düşene kadar",
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

    if not parts:
        return {
            "de": "Lüfte noch etwas weiter; mindestens ein Lüftungsziel ist noch offen.",
            "en": "Keep the windows open a little longer; at least one ventilation target has not been reached yet.",
            "tr": "Pencereleri biraz daha açık tut; en az bir havalandırma hedefi henüz tamamlanmadı.",
        }[lang]

    joined = _join_reason_parts(parts, lang)
    return {
        "de": f"Lüfte ruhig noch etwas weiter: {joined}.",
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
    co2 = a.get("co2")
    measured = ""
    if value is not None:
        measured = f" ({pollutant} {_measurement(_number(value, lang, 0), 'µg/m³')})"
    elif pollutant != "—":
        measured = f" ({pollutant})"
    high_co2 = False
    try:
        high_co2 = float(co2) > 2000
    except (TypeError, ValueError):
        pass
    if key == "air_quality_moderate":
        return {
            "de": f"Die Außenluftqualität ist derzeit nur mäßig{measured}. Ohne wichtigen Lüftungsgrund ist Warten günstiger.",
            "en": f"Outdoor air quality is only moderate right now{measured}. If there is no important reason to air the room, waiting is preferable.",
            "tr": f"Dış hava kalitesi şu anda yalnızca orta düzeyde{measured}. Önemli bir havalandırma gereksinimi yoksa beklemek daha uygundur.",
        }[lang]
    level = "sehr schlecht" if key == "air_quality_very_poor" else "schlecht"
    level_en = "very poor" if key == "air_quality_very_poor" else "poor"
    level_tr = "çok kötü" if key == "air_quality_very_poor" else "kötü"
    extra = {
        "de": " Auch bei hohem CO₂ ist die belastete Außenluft momentan der stärkere Nachteil." if high_co2 else "",
        "en": " Even with high CO₂, the polluted outdoor air is the stronger disadvantage right now." if high_co2 else "",
        "tr": " CO₂ yüksek olsa bile kirli dış hava şu anda daha büyük dezavantajdır." if high_co2 else "",
    }[lang]
    return {
        "de": f"Die Außenluftqualität ist {level}{measured}. Lass die Fenster vorerst geschlossen.{extra}",
        "en": f"Outdoor air quality is {level_en}{measured}. Keep the windows closed for now.{extra}",
        "tr": f"Dış hava kalitesi {level_tr}{measured}. Şimdilik pencereleri kapalı tut.{extra}",
    }[lang]


def _tradeoff_reason(key: str, a: dict[str, Any], lang: str, unit: str) -> str:
    caution = str(a.get("caution") or "conditions")
    co2 = a.get("co2")
    if key == "co2_tradeoff":
        ppm = _measurement(_number(co2, lang, 0), "ppm")
        detail_options = {
            "rain": {
                "de": "Es regnet bzw. Regen kann die kurze Lüftung treffen.",
                "en": "It is raining or rain may overlap the short airing period.",
                "tr": "Yağmur yağıyor veya yağmur kısa havalandırma süresine denk gelebilir.",
            },
            "humidity": {
                "de": "Die Außenluft ist dabei feuchter und würde die Feuchtesituation verschlechtern.",
                "en": "The outdoor air is wetter and would worsen the moisture situation.",
                "tr": "Dış hava daha nemli ve içerideki nem durumunu kötüleştirebilir.",
            },
            "temperature": {
                "de": "Die Außenluft würde die Raumtemperatur spürbar vom gewünschten Bereich wegbewegen.",
                "en": "The outdoor air would noticeably move the room temperature away from the preferred range.",
                "tr": "Dış hava oda sıcaklığını istenen aralıktan belirgin biçimde uzaklaştırabilir.",
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
        detail = detail_options.get(caution, {
            "de": "Die Außenbedingungen sind nicht ideal.",
            "en": "Outdoor conditions are not ideal.",
            "tr": "Dış koşullar ideal değil.",
        })[lang]
        return {
            "de": f"CO₂ liegt bei {ppm} und spricht fürs Lüften. {detail}",
            "en": f"CO₂ is at {ppm}, so fresh air would help. {detail}",
            "tr": f"CO₂ {ppm} seviyesinde ve havalandırma faydalı olur. {detail}",
        }[lang]

    need = str(a.get("need") or "")
    need_text = {
        "humidity": {"de": "Die Raumfeuchte spricht fürs Lüften.", "en": "Indoor humidity would benefit from airing.", "tr": "İç nem havalandırmadan fayda görür."},
        "humidity_urgent": {"de": "Die Raumfeuchte ist deutlich erhöht.", "en": "Indoor humidity is clearly elevated.", "tr": "İç nem belirgin şekilde yüksek."},
        "mold": {"de": "Die Feuchtesituation an der überwachten Oberfläche würde von Luftaustausch profitieren.", "en": "The moisture situation at the monitored surface would benefit from air exchange.", "tr": "İzlenen yüzeydeki nem durumu hava değişiminden fayda görür."},
        "mold_persistent": {"de": "Die kritische Oberflächenfeuchte hält bereits länger an.", "en": "The critical surface humidity has persisted for a longer period.", "tr": "Kritik yüzey nemi daha uzun süredir devam ediyor."},
        "heat": {"de": "Der Raum ist deutlich aufgeheizt und könnte abkühlen.", "en": "The room is very warm and could benefit from cooling.", "tr": "Oda belirgin biçimde sıcak ve serinlemeden fayda görebilir."},
        "humid_heat": {"de": "Wärme und hohe Feuchte belasten den Raumkomfort.", "en": "Heat and high humidity are reducing comfort.", "tr": "Sıcaklık ve yüksek nem konforu azaltıyor."},
        "temperature": {"de": "Die Außenluft würde die Temperatur Richtung Wunschwert bewegen.", "en": "The outdoor air would move the temperature toward your preferred value.", "tr": "Dış hava sıcaklığı tercih edilen değere yaklaştırabilir."},
        "routine": {"de": "Ein kurzer Luftaustausch wäre grundsätzlich sinnvoll.", "en": "A short air exchange would generally make sense.", "tr": "Kısa bir hava değişimi genel olarak mantıklı olur."},
    }.get(need, {"de": "Lüften hätte einen Vorteil.", "en": "Airing would have a benefit.", "tr": "Havalandırmanın bir faydası olur."})[lang]
    drawback_options = {
        "rain": {"de": "Regen macht das offene Fenster gerade unpraktisch.", "en": "Rain makes an open window impractical right now.", "tr": "Yağmur şu anda açık pencereyi pratik olmaktan çıkarıyor."},
        "humidity": {"de": "Die Außenluft würde gleichzeitig zusätzliche Feuchte eintragen.", "en": "The outdoor air would also add moisture.", "tr": "Dış hava aynı zamanda içeri ek nem getirir."},
        "air_quality": {"de": "Die Außenluftqualität ist jedoch nur mäßig.", "en": "Outdoor air quality is only moderate, though.", "tr": "Ancak dış hava kalitesi yalnızca orta düzeyde."},
        "air_warning": {"de": "Es gilt jedoch ein Außenluft-Hinweis.", "en": "There is an outdoor-air advisory, though.", "tr": "Ancak dış hava için bir uyarı var."},
        "weather": {"de": "Die Wetterlage spricht gleichzeitig gegen ein offenes Fenster.", "en": "The weather also argues against an open window.", "tr": "Hava koşulları aynı zamanda açık pencereye karşı."},
        "temperature": {"de": "Die Raumtemperatur würde sich dabei spürbar verschlechtern.", "en": "Room temperature would noticeably worsen at the same time.", "tr": "Oda sıcaklığı aynı zamanda belirgin biçimde kötüleşir."},
    }
    drawback = drawback_options.get(caution, {
        "de": "Die Außenbedingungen sind gleichzeitig nicht ideal.",
        "en": "Outdoor conditions are not ideal at the same time.",
        "tr": "Dış koşullar aynı zamanda ideal değil.",
    })[lang]
    return f"{need_text} {drawback}"


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

    if key == "continue_airing":
        return _continue_reason(a, lang, temperature_unit)

    if key in {"air_quality_moderate", "air_quality_poor", "air_quality_very_poor"}:
        return _air_quality_reason(key, a, lang)

    if key in {"co2_tradeoff", "comfort_tradeoff"}:
        return _tradeoff_reason(key, a, lang, temperature_unit)

    if key == "surface_moisture_persistent_ventilate":
        surface = m(a.get("surface_humidity"), "%", 0)
        return {
            "de": f"Die überwachte Oberfläche liegt bei etwa {surface} relativer Feuchte und die Belastung hält bereits länger an. Trocknere Außenluft hilft beim Entlasten.",
            "en": f"The monitored surface is at about {surface} relative humidity and the condition has persisted for a longer period. Drier outdoor air can help reduce it.",
            "tr": f"İzlenen yüzeyde bağıl nem yaklaşık {surface} ve bu durum daha uzun süredir devam ediyor. Daha kuru dış hava nemi azaltmaya yardımcı olur.",
        }[lang]

    if key == "surface_moisture_ventilate":
        return {
            "de": "Die Feuchtesituation profitiert aktuell von der trockeneren Außenluft.",
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
            "de": "Innen- und Außenluft sind für die aktuelle Feuchtesituation nahezu ausgeglichen. Lüften ist dafür weder klar hilfreich noch deutlich nachteilig.",
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
            "de": f"Die Raumfeuchte liegt bei {m(a.get('humidity'), '%', 0)}, aber innen und außen unterscheiden sich absolut nur wenig. Lüften würde die Feuchte kaum verändern.",
            "en": f"Indoor relative humidity is {m(a.get('humidity'), '%', 0)}, but absolute humidity indoors and outdoors is very similar. Airing would hardly change it.",
            "tr": f"İç bağıl nem {m(a.get('humidity'), '%', 0)}, ancak içeride ve dışarıda mutlak nem birbirine çok yakın. Havalandırma nemi pek değiştirmez.",
        }[lang]

    if key in {"weather_wind_caution", "weather_wind_danger"}:
        speed = a.get("speed_kmh")
        speed_text = f" ({m(speed, 'km/h', 0)})" if speed is not None else ""
        danger = key.endswith("danger")
        if danger:
            return {
                "de": f"Wind bzw. Böen sind aktuell sehr kräftig{speed_text}. Ein offenes Fenster ist damit eher nachteilig; lass es besser geschlossen.",
                "en": f"Wind or gusts are very strong right now{speed_text}. An open window is more disadvantageous in these conditions, so keep it closed.",
                "tr": f"Rüzgâr veya rüzgâr hamleleri şu anda çok kuvvetli{speed_text}. Bu koşullarda açık pencere daha çok dezavantaj yaratır; kapalı tutmak daha iyi.",
            }[lang]
        return {
            "de": f"Es ist deutlich windig{speed_text}. Lüften ist möglich, aber das Fenster sollte gesichert und die Situation beobachtet werden.",
            "en": f"It is noticeably windy{speed_text}. Airing is possible, but secure the window and keep an eye on conditions.",
            "tr": f"Hava belirgin biçimde rüzgârlı{speed_text}. Havalandırma mümkün, ancak pencereyi sabitlemek ve durumu izlemek gerekir.",
        }[lang]

    if key == "rain_soon" and a.get("minutes") is not None:
        minutes = max(0, round(float(a.get("minutes"))))
        return {
            "de": f"In etwa {minutes} Minuten wird Niederschlag erwartet und könnte die Lüftung treffen. Wenn es nicht dringend ist, warte besser kurz.",
            "en": f"Precipitation is expected in about {minutes} minutes and may overlap the airing period. If it is not urgent, wait a little.",
            "tr": f"Yaklaşık {minutes} dakika içinde yağış bekleniyor ve havalandırmaya denk gelebilir. Acil değilse biraz beklemek daha iyi.",
        }[lang]

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
            "co2_critical_rain": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist damit sehr hoch. Trotz des Regens ist ein kurzer Luftaustausch sinnvoll – aber nur kurz und unter Beobachtung.",
            "co2_critical": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist damit sehr hoch. Jetzt zu lüften hat klare Priorität.",
            "co2_ventilate": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist erhöht. Draußen passen die Bedingungen, deshalb lohnt sich jetzt ein Luftaustausch.",
            "co2_wait": f"CO₂ liegt bei {m(a.get('co2'), 'ppm', 0)} und ist erhöht. Die Außenbedingungen sind gerade aber ungünstig, deshalb ist kurzes Warten die bessere Wahl.",
            "mold_prevention": f"An der überwachten kalten Oberfläche liegt die berechnete relative Feuchte bei etwa {m(a.get('surface_humidity'), '%', 0)}. Da die Außenluft trockener ist, hilft Lüften dabei, die Feuchte dort wieder zu senken.",
            "mold_wait": f"An der überwachten kalten Oberfläche liegt die berechnete relative Feuchte bei etwa {m(a.get('surface_humidity'), '%', 0)}. Lüften würde die Feuchte im Moment aber nicht zuverlässig verbessern; behalte die Situation im Blick.",
            "humidity_ventilate": f"Drinnen liegen {m(a.get('humidity'), '%', 0)} relative Feuchte an. Draußen enthält die Luft rund {m(a.get('diff'), 'g/m³')} weniger Wasser – Lüften hilft also beim Trocknen.",
            "humidity_wait": "Die Luftfeuchte drinnen ist erhöht, draußen gibt es im Moment aber kaum einen Trocknungsvorteil. Warte besser noch etwas.",
            "cooling": f"Drinnen sind es {t(a.get('ti'))}, bei einem Soll von {t(a.get('target'))}. Draußen sind es {t(a.get('ta'))} – Lüften hilft jetzt beim Abkühlen.",
            "warming": f"Drinnen sind es {t(a.get('ti'))}, bei einem Soll von {t(a.get('target'))}. Draußen ist es wärmer und die Außenluft eignet sich gerade zum Lüften.",
            "routine_ventilate": f"Seit rund {n(a.get('hours'), 1)} Stunden wurde keine bestätigte Lüftung erfasst. Die Außenbedingungen passen gerade gut, deshalb ist jetzt ein kurzer Luftaustausch sinnvoll.",
            "routine_wait": f"Seit rund {n(a.get('hours'), 1)} Stunden wurde keine bestätigte Lüftung erfasst. Die Bedingungen draußen passen gerade aber nicht gut genug – warte lieber noch etwas.",
            "outside_too_hot": f"Drinnen sind es {t(a.get('ti'))}, draußen {t(a.get('ta'))}. Beim Lüften würdest du gerade zusätzliche Wärme hereinholen – die Fenster bleiben besser zu.",
            "outside_too_cold": f"Drinnen sind es {t(a.get('ti'))}, draußen {t(a.get('ta'))}. Lüften würde den Raum gerade unnötig auskühlen – deshalb besser geschlossen lassen.",
            "outside_more_humid": f"Die Außenluft enthält rund {m(a.get('amount'), 'g/m³')} mehr Wasser als die Luft drinnen. Lüften würde die Feuchte eher hereinholen als herausbringen.",
            "inside_too_dry": "Die Luft drinnen ist bereits ziemlich trocken. Lüften würde sie im Moment noch weiter austrocknen – deshalb besser warten.",
            "rain_now": "Draußen fällt gerade Niederschlag. Das sagt nichts über den Trocknungseffekt aus, macht ein offenes Fenster aber unpraktischer; wenn Lüften nicht nötig ist, warte besser kurz.",
            "rain_soon": "In Kürze wird Niederschlag erwartet. Wenn es nicht dringend nötig ist, ist ein etwas späterer Zeitpunkt zum Lüften wahrscheinlich besser.",
            "normal": "Aktuell gibt es keinen klaren Grund zum Lüften, und die Außenbedingungen bringen keinen deutlichen Vorteil. Lüften ist möglich, aber nicht nötig.",
            "incomplete_data": "Mindestens ein benötigter Temperatur- oder Feuchtewert ist gerade nicht verfügbar. Sobald die Sensordaten wieder vollständig sind, wird die Empfehlung automatisch aktualisiert.",
        }
    elif lang == "tr":
        texts = {
            "nina_air_danger": "Dış havayı etkileyen önemli bir uyarı var. Bu yüzden pencereleri ve kapıları şimdilik kapalı tutman daha iyi.",
            "nina_air_caution": "Dış havayla ilgili bir dikkat uyarısı var. Gerçekten gerekmedikçe şimdilik pencereleri açmamak daha iyi.",
            "air_smoke_danger": "Yakın çevrede duman veya yangın dumanı bildiriliyor. İçeri mümkün olduğunca az girmesi için pencereleri ve kapıları kapalı tut.",
            "air_smoke_caution": "Yakın çevrede duman veya yangın dumanı bildiriliyor. Acil değilse pencereleri açmadan önce biraz daha beklemek daha iyi.",
            "air_hazard_danger": "Dış havada zararlı madde veya gaz kaçağına ilişkin bir uyarı var. Pencereleri ve kapıları şimdilik kapalı tut.",
            "air_hazard_caution": "Dış havada olası kirletici maddelere ilişkin bir uyarı var. Gerçekten gerekmedikçe şimdilik pencereleri açma.",
            "weather_danger": "Dışarıda açık pencerenin iyi fikir olmadığı ciddi bir hava durumu var. Koşullar düzelene kadar pencereleri kapalı tut.",
            "weather_caution": "Şu anda bir hava durumu uyarısı var. Pencereleri açmak tamamen yanlış değil, ancak koşullar pek uygun değil.",
            "weather_heavy_rain_current": "Dışarıda şu anda kuvvetli yağmur yağıyor. Pencereleri açmak tamamen yanlış değil ama şu an pek pratik değil.",
            "weather_heavy_rain_caution": "Kuvvetli yağmur uyarısı var. Acil değilse pencereleri açmadan önce biraz daha beklemek daha iyi.",
            "weather_heavy_rain_danger": "Çok şiddetli yağmur için ciddi hava uyarısı var. Koşullar sakinleşene kadar pencereleri kapalı tut.",
            "weather_continuous_rain_caution": "Uzun süreli kuvvetli yağmur uyarısı var. Gerekli değilse pencereleri açmadan önce biraz daha bekle.",
            "weather_continuous_rain_danger": "Uzun süreli ve çok yoğun yağmur için ciddi hava uyarısı var. Pencereleri şimdilik kapalı tut.",
            "weather_thunderstorm_caution": "Gök gürültülü fırtına uyarısı var. Şu anda pencereleri açmak pek uygun değil; mümkünse fırtına geçene kadar bekle.",
            "weather_thunderstorm_danger": "Şiddetli gök gürültülü fırtına uyarısı var. Koşullar sakinleşene kadar pencereleri kapalı tut.",
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
            "nina_air_danger": "There is an active warning affecting the outdoor air. It is better to keep windows and doors closed for now.",
            "nina_air_caution": "There is currently an advisory affecting the outdoor air. Unless you really need fresh air, it is better to keep the windows closed for now.",
            "air_smoke_danger": "Smoke or fire smoke has been reported nearby. Keep windows and doors closed to reduce how much of it gets indoors.",
            "air_smoke_caution": "Smoke or fire smoke has been reported nearby. Unless opening the windows is urgent, it is better to wait a little longer.",
            "air_hazard_danger": "There is a warning about hazardous substances or a gas release in the outdoor air. Keep windows and doors closed for now.",
            "air_hazard_caution": "There is an advisory about possible pollutants in the outdoor air. Unless you really need fresh air, keep the windows closed for now.",
            "weather_danger": "Severe weather is active outside and open windows are a bad idea right now. Keep them closed until conditions improve.",
            "weather_caution": "There is an active weather warning. Opening the windows is not completely ruled out, but the conditions are not ideal right now.",
            "weather_heavy_rain_current": "It is raining heavily outside. Opening the windows is not completely ruled out, but it is rather impractical right now.",
            "weather_heavy_rain_caution": "There is a heavy-rain warning. Unless opening the windows is urgent, it is better to wait a little longer.",
            "weather_heavy_rain_danger": "A severe-weather warning for intense heavy rain is active. Keep the windows closed until conditions settle down.",
            "weather_continuous_rain_caution": "There is a warning for prolonged heavy rain. Unless fresh air is really needed, it is better to wait a little longer.",
            "weather_continuous_rain_danger": "A severe-weather warning for prolonged heavy rain is active. Keep the windows closed for now.",
            "weather_thunderstorm_caution": "There is a thunderstorm warning. Opening the windows is not ideal right now; if possible, wait until the storms have passed.",
            "weather_thunderstorm_danger": "A severe thunderstorm warning is active. Keep the windows closed until conditions calm down.",
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

    return texts.get(key, key)



def night_advice_text(
    key: str | None,
    args: dict[str, Any] | None,
    language: str | None,
    temperature_unit: str = "°C",
) -> str:
    """Render the compact evening night-ventilation hint."""
    if not key:
        return ""
    lang = normalize_language(language)
    a = args or {}
    indoor = _temperature(a.get("indoor_temp"), lang, temperature_unit)
    target = _temperature(a.get("target_temp"), lang, temperature_unit)
    minimum = _temperature(a.get("minimum_temp"), lang, temperature_unit)

    if key == "night_recommended":
        return {
            "de": f"🌙 Nachtlüftung sinnvoll: Von {indoor} Richtung {target} kann die kühlere Nachtluft gut helfen (nachts bis etwa {minimum}).",
            "en": f"🌙 Night airing is useful: cooler night air can help move the room from {indoor} toward {target} (down to about {minimum} outside).",
            "tr": f"🌙 Gece havalandırması uygun: daha serin gece havası odayı {indoor} seviyesinden {target} hedefine yaklaştırabilir (dışarıda yaklaşık {minimum} seviyesine kadar).",
        }[lang]
    if key == "night_conditional":
        details: list[str] = []
        if a.get("rain_risk"):
            details.append({"de": "Regen möglich", "en": "rain is possible", "tr": "yağmur mümkün"}[lang])
        if a.get("humidity_disadvantage"):
            details.append({"de": "Außenluft eher feuchter", "en": "outdoor air is rather wetter", "tr": "dış hava daha nemli"}[lang])
        if a.get("weather_caution"):
            details.append({"de": "Wetterhinweis aktiv", "en": "weather advisory active", "tr": "hava uyarısı aktif"}[lang])
        if a.get("air_warning"):
            details.append({"de": "Außenluft-Hinweis aktiv", "en": "outdoor-air advisory active", "tr": "dış hava uyarısı aktif"}[lang])
        if a.get("air_quality_moderate"):
            details.append({"de": "Außenluftqualität nur mäßig", "en": "outdoor air quality only moderate", "tr": "dış hava kalitesi yalnızca orta"}[lang])
        detail = ", ".join(details) or {"de": "Bedingungen nicht ideal", "en": "conditions are not ideal", "tr": "koşullar ideal değil"}[lang]
        return {
            "de": f"🌙 Nachtlüftung nur bedingt sinnvoll: Abkühlung wäre möglich, aber {detail}.",
            "en": f"🌙 Night airing is only conditionally useful: cooling would help, but {detail}.",
            "tr": f"🌙 Gece havalandırması yalnızca koşullu olarak uygun: serinleme faydalı olurdu ancak {detail}.",
        }[lang]
    if key == "night_target_already_ok":
        return {
            "de": f"🌙 Nachtlüftung eher nicht nötig: Der Raum liegt mit {indoor} bereits nahe am Wunschwert {target}.",
            "en": f"🌙 Night airing is probably unnecessary: the room is already near the {target} target at {indoor}.",
            "tr": f"🌙 Gece havalandırması pek gerekli değil: oda {indoor} ile {target} hedef değerine zaten yakın.",
        }[lang]
    if key == "night_not_cooler":
        return {
            "de": f"🌙 Nachtlüftung eher nicht sinnvoll: Die kommende Nacht bietet voraussichtlich zu wenig Abkühlung (Minimum etwa {minimum}).",
            "en": f"🌙 Night airing is probably not useful: the coming night is not expected to provide much cooling (minimum about {minimum}).",
            "tr": f"🌙 Gece havalandırması pek uygun değil: bu gece yeterli serinleme beklenmiyor (minimum yaklaşık {minimum}).",
        }[lang]
    if key == "night_strong_wind":
        return {
            "de": "🌙 Nachtlüftung nicht empfohlen: Für längeres unbeaufsichtigtes Öffnen ist zu starker Wind vorhergesagt.",
            "en": "🌙 Night airing is not recommended: winds are forecast to be too strong for a long unattended opening.",
            "tr": "🌙 Gece havalandırması önerilmez: uzun süre gözetimsiz açık bırakmak için çok güçlü rüzgâr bekleniyor.",
        }[lang]
    if key == "night_poor_air":
        return {
            "de": "🌙 Nachtlüftung nicht empfohlen: Die aktuelle Außenluftqualität spricht gegen ein längeres Öffnen.",
            "en": "🌙 Night airing is not recommended: current outdoor air quality argues against leaving the window open for longer.",
            "tr": "🌙 Gece havalandırması önerilmez: mevcut dış hava kalitesi pencerenin uzun süre açık kalmasına karşı.",
        }[lang]
    if key == "night_hard_conditions":
        return {
            "de": "🌙 Nachtlüftung nicht empfohlen: Aktuell besteht ein deutlicher Außenluft- oder Wetterschutzgrund.",
            "en": "🌙 Night airing is not recommended: there is currently a clear outdoor-air or weather safety reason to keep closed.",
            "tr": "🌙 Gece havalandırması önerilmez: şu anda pencereleri kapalı tutmak için belirgin bir dış hava veya hava durumu güvenlik nedeni var.",
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

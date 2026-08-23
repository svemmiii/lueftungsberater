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
    "tr": {
        "open_now": "Şimdi pencereleri aç",
        "keep_open": "Pencereleri biraz daha açık tut",
        "can_close": "Artık pencereleri kapatabilirsin",
        "short_observation": "Kısa süre havalandır ve durumu takip et",
        "better_close": "Pencereleri kapatmak daha iyi",
        "caution_keep_closed": "Şimdilik pencereleri kapalı tutmak daha iyi",
        "keep_closed": "Pencereleri kapalı tut",
        "close_now": "Pencereleri şimdi kapat",
        "wait": "Biraz daha beklemek daha iyi",
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
        "can_end": "You can close the windows now",
        "brief_observation": "3–5 minutes while keeping an eye on the conditions",
        "co2_recheck": "10–15 minutes, then check CO₂ again",
        "co2_until_good": "5–10 minutes, or until CO₂ drops below roughly 1000 ppm",
        "cooling": "15–30 minutes, or longer if the cooler outdoor air continues to help",
        "warming": "5–10 minutes",
        "2_4": "2–4 minutes",
        "3_5": "3–5 minutes",
        "4_6": "4–6 minutes",
        "5_8": "5–8 minutes",
        "8_12": "8–12 minutes",
        "10_15": "10–15 minutes",
        "5_10": "5–10 minutes",
        "not_needed": "No window-opening time is needed right now",
    },
    "tr": {
        "until_targets": "Kalan havalandırma hedeflerine ulaşılana kadar",
        "can_end": "Artık pencereleri kapatabilirsin",
        "brief_observation": "3–5 dakika; bu sırada durumu takip et",
        "co2_recheck": "10–15 dakika, ardından CO₂ seviyesini yeniden kontrol et",
        "co2_until_good": "5–10 dakika veya CO₂ yaklaşık 1000 ppm'in altına düşene kadar",
        "cooling": "15–30 dakika; dışarıdaki serin hava işe yaramaya devam ederse daha uzun da olabilir",
        "warming": "5–10 dakika",
        "2_4": "2–4 dakika",
        "3_5": "3–5 dakika",
        "4_6": "4–6 dakika",
        "5_8": "5–8 dakika",
        "8_12": "8–12 dakika",
        "10_15": "10–15 dakika",
        "5_10": "5–10 dakika",
        "not_needed": "Şu anda pencereleri açmaya gerek yok",
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
            "rain_now": "Draußen fällt gerade Niederschlag. Wenn es nicht dringend nötig ist, warte mit dem Lüften besser kurz.",
            "rain_soon": "In Kürze wird Niederschlag erwartet. Wenn es nicht dringend nötig ist, ist ein etwas späterer Zeitpunkt zum Lüften wahrscheinlich besser.",
            "normal": "CO₂, Luftfeuchte und Temperatur geben gerade keinen ausreichenden Grund zum Lüften. Du kannst die Fenster erstmal geschlossen lassen.",
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
            "rain_now": "Dışarıda şu anda yağış var. Acil değilse pencereleri açmadan önce biraz beklemek daha iyi.",
            "rain_soon": "Kısa süre içinde yağış bekleniyor. Acil değilse pencereleri biraz daha sonra açmak muhtemelen daha iyi olur.",
            "normal": "CO₂, nem ve sıcaklık şu anda pencereleri açmak için yeterli bir neden göstermiyor. Şimdilik kapalı tutabilirsin.",
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
            "rain_now": "Precipitation is falling outside right now. Unless opening the windows is urgent, it is better to wait a little.",
            "rain_soon": "Precipitation is expected shortly. Unless opening the windows is urgent, a slightly later time will probably be better.",
            "normal": "CO₂, humidity, and temperature do not give you a strong enough reason to open the windows right now. You can keep them closed for the moment.",
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

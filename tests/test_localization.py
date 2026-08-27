from custom_components.lueftungsberater.localization import reason_text


def test_temperature_unit_does_not_wrap_away_from_value() -> None:
    text = reason_text(
        "cooling",
        {"ti": 24.3, "target": 21.0, "ta": 18.0},
        "de",
        "°F",
    )

    assert "75,7\u202f°F" in text
    assert "69,8\u202f°F" in text
    assert " °F" not in text


def test_other_measurement_units_are_non_breaking() -> None:
    co2 = reason_text("co2_critical", {"co2": 1400}, "de", "°C")
    humidity = reason_text(
        "humidity_ventilate",
        {"humidity": 65, "diff": 2.4},
        "de",
        "°C",
    )

    assert "1400\u202fppm" in co2
    assert "65\u202f%" in humidity
    assert "2,4\u202fg/m³" in humidity


def test_turkish_reasons_are_natural_and_unit_aware() -> None:
    text = reason_text(
        "cooling",
        {"ti": 24.3, "target": 21.0, "ta": 18.0},
        "tr",
        "°C",
    )

    assert "hedefin ise" in text
    assert "pencereleri açmak" in text
    assert "24,3\u202f°C" in text


def test_incomplete_sensor_data_has_natural_text_in_all_languages() -> None:
    from custom_components.lueftungsberater.localization import (
        duration_text,
        recommendation_text,
    )

    expected = {
        "de": "Aktuell keine zuverlässige Empfehlung möglich",
        "en": "No reliable recommendation is available right now",
        "tr": "Şu anda güvenilir bir öneri verilemiyor",
    }
    for language, recommendation in expected.items():
        assert recommendation_text("unknown", language) == recommendation
        assert "incomplete_data" not in reason_text(
            "incomplete_data", {}, language, "°C"
        )
        assert "incomplete_data" not in duration_text("incomplete_data", language)


def test_night_advice_text_is_localized() -> None:
    from custom_components.lueftungsberater.localization import night_advice_text

    expected_fragments = {
        "de": "Heute Nacht lüften",
        "en": "Air tonight",
        "tr": "Bu gece havalandır",
    }
    args = {
        "start_time": "2026-08-25T22:00:00+02:00",
        "end_time": "2026-08-26T03:00:00+02:00",
        "thermal_need": True,
        "humidity_need": False,
        "humidity_advantage": False,
    }
    for language, fragment in expected_fragments.items():
        text = night_advice_text("night_now", args, language, "°C")
        assert fragment in text
        assert "03:00" in text


def test_room_perspective_text_is_short_and_localized_in_all_languages() -> None:
    from custom_components.lueftungsberater.localization import recommendation_text

    args = {
        "need": "humidity",
        "level": 1,
        "ventilation_color": "orange",
        "mode": "feuchte_warten",
        "humidity": 60.6,
        "ti": 23.0,
        "ta": 24.0,
        "target": 22.0,
    }
    for language in ("de", "en", "tr"):
        recommendation = recommendation_text("room_good", language)
        reason = reason_text("room_perspective", args, language, "°C")
        assert recommendation
        assert reason
        assert "room_" not in recommendation
        assert "room_" not in reason


def test_room_perspective_green_tradeoff_does_not_claim_outside_is_good() -> None:
    args = {
        "need": "co2_high",
        "level": 3,
        "ventilation_color": "green",
        "mode": "co2_lueften_mit_nachteil",
        "caution": "temperature",
        "co2": 1900,
        "humidity": 50.0,
        "ti": 25.0,
        "ta": 38.0,
        "target": 22.0,
    }
    expected = {
        "de": ("Außentemperatur ist zwar ungünstig", "Lüftungsbedarf wiegt hier aber stärker"),
        "en": ("outdoor temperature is unfavorable", "need for air exchange outweighs"),
        "tr": ("Dış sıcaklık elverişsiz", "havalandırma ihtiyacı bu dezavantajdan daha ağır basıyor"),
    }
    for language, fragments in expected.items():
        text = reason_text("room_perspective", args, language, "°C")
        assert fragments[0] in text
        assert fragments[1] in text
        assert "ausreichend gut" not in text
        assert "suitable enough" not in text
        assert "yeterince uygun" not in text


def test_room_perspective_green_humidity_tradeoff_mentions_outweighed_drawback() -> None:
    args = {
        "need": "co2_high",
        "level": 3,
        "ventilation_color": "green",
        "mode": "co2_lueften_mit_nachteil",
        "caution": "humidity",
        "co2": 1900,
        "humidity": 50.0,
        "ti": 23.0,
        "ta": 23.0,
        "target": 22.0,
    }
    expected = {
        "de": ("Außenluft ist zwar feuchter", "Lüftungsbedarf wiegt hier aber stärker"),
        "en": ("Outdoor air is more humid", "need for air exchange outweighs"),
        "tr": ("Dış hava daha nemli", "havalandırma ihtiyacı bu dezavantajdan daha ağır basıyor"),
    }
    for language, fragments in expected.items():
        text = reason_text("room_perspective", args, language, "°C")
        assert fragments[0] in text
        assert fragments[1] in text

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

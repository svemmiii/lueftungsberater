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



def test_room_good_uses_clear_reason_wording_in_all_languages() -> None:
    from custom_components.lueftungsberater.localization import recommendation_text

    assert recommendation_text("room_good", "de") == "Aktuell kein Lüftungsgrund"
    assert recommendation_text("room_good", "en") == "No current reason to ventilate"
    assert recommendation_text("room_good", "tr") == "Şu anda havalandırma nedeni yok"

def test_night_advice_text_is_localized() -> None:
    from custom_components.lueftungsberater.localization import night_advice_text

    expected_fragments = {
        "de": "Heute Nacht lüften",
        "en": "Ventilate tonight",
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


def test_later_night_advice_includes_start_and_end_in_all_languages() -> None:
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "start_time": "2026-08-26T01:00:00+02:00",
        "end_time": "2026-08-26T03:00:00+02:00",
        "thermal_need": True,
    }
    for key in ("night_later", "night_later_conditional"):
        for language in ("de", "en", "tr"):
            text = night_advice_text(key, args, language, "°C")
            assert "01:00" in text
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
        "de": ("Außentemperatur ist zwar ungünstig", "wegen der Innenwerte hier wichtiger"),
        "en": ("outdoor temperature is unfavorable", "indoor values still make ventilation more important"),
        "tr": ("Dış sıcaklık elverişsiz", "iç değerler nedeniyle havalandırmak burada daha önemli"),
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
        "de": ("Außenluft ist zwar feuchter", "wegen der Innenwerte hier wichtiger"),
        "en": ("Outdoor air is more humid", "indoor values still make ventilation more important"),
        "tr": ("Dış hava daha nemli", "iç değerler nedeniyle havalandırmak burada daha önemli"),
    }
    for language, fragments in expected.items():
        text = reason_text("room_perspective", args, language, "°C")
        assert fragments[0] in text
        assert fragments[1] in text


def test_room_perspective_mild_green_value_explicitly_says_no_action_needed() -> None:
    args = {
        "need": "co2_elevated",
        "level": 1,
        "room_color": "green",
        "ventilation_color": "green",
        "mode": "co2_lueften",
        "co2": 1100,
        "humidity": 50.0,
        "ti": 22.0,
        "ta": 20.0,
        "target": 22.0,
    }
    text = reason_text("room_perspective", args, "de", "°C")
    assert "leicht erhöht" in text
    assert "noch kein Lüften nötig" in text


def test_short_term_weather_text_is_plain_and_specific_in_all_languages() -> None:
    args = {
        "forecast_change": "worsening",
        "forecast_kind": "thunderstorm",
        "forecast_minutes": 10,
    }
    expected = {
        "de": "Gewitter",
        "en": "thunderstorm",
        "tr": "fırtına",
    }
    for language, fragment in expected.items():
        text = reason_text("weather_forecast_worsening", args, language, "°C")
        assert fragment in text
        assert "Außen- oder Wetterlage" not in text


def test_current_thunderstorm_can_mention_expected_improvement_without_unlocking() -> None:
    args = {
        "forecast_change": "improving",
        "forecast_kind": "thunderstorm",
        "forecast_minutes": 10,
    }
    text = reason_text("weather_thunderstorm_danger", args, "de", "°C")
    assert "Fenster geschlossen" in text
    assert "beruhigen" in text


def test_co2_minimum_airing_text_exists_in_all_languages():
    for language in ("de", "en", "tr"):
        text = reason_text(
            "co2_minimum_airing",
            {"co2": 820, "cautious": True},
            language,
        )
        assert "820" in text
        assert len(text) > 30


def test_dynamic_co2_session_target_text_is_natural_in_all_languages() -> None:
    expected = {
        "de": "1250\u202fppm",
        "en": "1250\u202fppm",
        "tr": "1250\u202fppm",
    }
    for language, fragment in expected.items():
        minimum = reason_text(
            "co2_minimum_airing",
            {"co2": 1380, "co2_target": 1250, "cautious": True},
            language,
        )
        near = reason_text(
            "co2_tradeoff",
            {"co2": 1280, "co2_target": 1250, "caution": "near_target"},
            language,
        )
        assert fragment in minimum
        assert fragment in near

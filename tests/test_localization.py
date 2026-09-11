from custom_components.lueftungsberater.localization import duration_text, reason_text


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


def test_later_night_advice_includes_start_and_end_in_all_languages():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "start_time": "2026-09-06T00:00:00+02:00",
        "end_time": "2026-09-06T04:00:00+02:00",
        "thermal_need": True,
    }
    for language in ("de", "en", "tr"):
        text = night_advice_text("night_later", args, language)
        assert "00:00" in text
        assert "04:00" in text


def test_temperature_continuation_duration_does_not_promise_reaching_unreachable_target():
    for language in ("de", "en", "tr"):
        text = duration_text("while_temperature_helps", language)
        assert text
    assert "nicht zwingend" in duration_text("while_temperature_helps", "de")


def test_short_only_night_advice_is_localized_in_all_languages():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "start_time": "2026-09-09T21:20:00+02:00",
        "end_time": "2026-09-10T07:00:00+02:00",
        "limit_time": "2026-09-09T23:00:00+02:00",
        "temperature_limit_direction": "cold",
        "thermal_need": True,
        "humidity_need": False,
        "current_thermal_advantage": True,
        "indoor_temp": 23.7,
    }
    expected = {
        "de": ("kurz lüften", "23:00"),
        "en": ("short airing", "23:00"),
        "tr": ("kısa süre havalandır", "23:00"),
    }
    for language, fragments in expected.items():
        text = night_advice_text("night_short_only", args, language, "°C")
        for fragment in fragments:
            assert fragment.lower() in text.lower()


def test_not_recommended_night_advice_is_localized_in_all_languages():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "thermal_need": True,
        "humidity_need": False,
        "has_helpful_forecast": False,
        "indoor_temp": 25.0,
    }
    for language in ("de", "en", "tr"):
        text = night_advice_text("night_not_recommended", args, language, "°C")
        assert text


def test_short_only_humidity_text_does_not_claim_cooling_when_outside_is_hotter():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "limit_time": "2026-09-09T21:20:00+02:00",
        "temperature_limit_direction": "warm",
        "thermal_need": True,
        "humidity_need": True,
        "current_thermal_advantage": False,
        "humidity_advantage": True,
        "indoor_temp": 25.0,
    }
    text = night_advice_text("night_short_only", args, "de", "°C")
    assert "Trocknen" in text
    assert "abkühlen" not in text


def test_later_night_text_never_says_keep_closed_when_live_card_says_open_now():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "start_time": "2026-09-10T01:00:00+02:00",
        "end_time": "2026-09-10T03:00:00+02:00",
        "thermal_need": True,
        "forecast_thermal_advantage": True,
        "live_open_now": True,
    }
    text = night_advice_text("night_later", args, "de")
    assert "Hauptkarte" in text
    assert "geschlossen lassen" not in text


def test_short_only_text_names_wind_and_outdoor_co2_drawbacks():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "temperature_limit_direction": "cold",
        "thermal_need": True,
        "current_thermal_advantage": True,
        "max_wind_level": 1,
        "outdoor_co2_disadvantage": True,
    }
    text = night_advice_text("night_short_only", args, "de")
    assert "Wind" in text
    assert "Außen-CO₂" in text


def test_not_recommended_text_explains_missing_contiguous_window_not_missing_cooling():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "thermal_need": True,
        "humidity_need": False,
        "has_helpful_forecast": True,
        "no_contiguous_window": True,
        "indoor_temp": 25.0,
    }
    text = night_advice_text("night_not_recommended", args, "de")
    assert "einzelne hilfreiche Phasen" in text
    assert "nicht ausreichend kühler" not in text


def test_night_now_uses_current_not_future_humidity_wording():
    from custom_components.lueftungsberater.localization import night_advice_text

    args = {
        "start_time": "2026-09-09T22:00:00+02:00",
        "end_time": "2026-09-10T02:00:00+02:00",
        "thermal_need": True,
        "humidity_need": True,
        "current_thermal_advantage": True,
        "current_humidity_advantage": False,
        "forecast_humidity_advantage": True,
    }
    text = night_advice_text("night_now", args, "de")
    assert "bereits kühler" in text
    assert "bereits kühler und trockener" not in text


def test_multi_need_not_recommended_text_is_not_monocausal():
    from custom_components.lueftungsberater.localization import night_advice_text

    text = night_advice_text(
        "night_not_recommended",
        {
            "thermal_need": True,
            "humidity_need": True,
            "has_helpful_forecast": False,
            "indoor_temp": 25.0,
        },
        "de",
    )
    assert "Kühlung" in text
    assert "Trocknung" in text


def test_later_conditional_does_not_describe_only_current_humidity_as_future_drawback():
    from custom_components.lueftungsberater.localization import night_advice_text

    text = night_advice_text(
        "night_later_conditional",
        {
            "start_time": "2026-09-11T23:00:00+02:00",
            "end_time": "2026-09-12T02:00:00+02:00",
            "thermal_need": True,
            "forecast_thermal_advantage": True,
            "current_humidity_disadvantage": True,
            "forecast_humidity_disadvantage": False,
            "weather_caution": True,
        },
        "de",
    )
    assert "Wetterhinweis" in text
    assert "Außenluft eher feuchter" not in text


def test_short_only_does_not_describe_only_future_humidity_as_current_drawback():
    from custom_components.lueftungsberater.localization import night_advice_text

    text = night_advice_text(
        "night_short_only",
        {
            "thermal_need": True,
            "current_thermal_advantage": True,
            "current_humidity_disadvantage": False,
            "forecast_humidity_disadvantage": True,
            "temperature_limit_direction": "cold",
        },
        "de",
    )
    assert "Außenluft eher feuchter" not in text

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

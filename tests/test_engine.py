from custom_components.lueftungsberater.engine import (
    absolute_humidity,
    evaluate_room,
    surface_relative_humidity,
)
from custom_components.lueftungsberater.localization import reason_text
from custom_components.lueftungsberater.models import RoomInput


def base(**kw):
    data = dict(
        indoor_temp=23,
        indoor_humidity=50,
        outdoor_temp=15,
        outdoor_humidity=70,
        target_temp=22,
    )
    data.update(kw)
    return RoomInput(**data)


def test_absolute_humidity_cold_humid_air_can_be_drier():
    assert absolute_humidity(15, 90) < absolute_humidity(23, 60)


def test_high_co2_good_conditions_is_green():
    r = evaluate_room(base(co2=1500))
    assert r.color == "green" and r.mode == "co2_lueften"
    assert r.recommendation_key == "open_now"


def test_nina_danger_wins():
    r = evaluate_room(
        base(
            co2=1800,
            nina_status="danger",
            nina_reason_key="air_smoke_danger",
            nina_original_reason="Brandrauch",
        )
    )
    assert r.color == "red" and r.mode == "nina_aussenluftgefahr"
    assert r.reason_key == "air_smoke_danger"


def test_nina_caution_is_yellow():
    r = evaluate_room(base(co2=900, nina_status="caution"))
    assert r.color == "yellow" and r.mode == "nina_vorsicht"


def test_weather_danger_keeps_specific_semantic_reason():
    r = evaluate_room(
        base(
            co2=1500,
            weather_danger=True,
            weather_reason_key="weather_heavy_rain_danger",
            weather_original_reason="DWD Unwetterwarnung vor heftigem Starkregen",
        )
    )
    assert r.color == "red"
    assert r.reason_key == "weather_heavy_rain_danger"
    assert "Starkregen" in reason_text(r.reason_key, r.reason_args, "de")
    assert "heavy rain" in reason_text(r.reason_key, r.reason_args, "en").lower()


def test_weather_caution_is_yellow_and_specific():
    r = evaluate_room(
        base(
            weather_caution=True,
            weather_reason_key="weather_heavy_rain_caution",
        )
    )
    assert r.color == "yellow"
    assert r.mode == "wetter_vorsicht"
    assert "Starkregen" in reason_text(r.reason_key, r.reason_args, "de")


def test_hotter_outside_can_be_red_without_being_a_danger_alert():
    r = evaluate_room(base(indoor_temp=23, outdoor_temp=38, target_temp=22))
    assert r.color == "red"
    assert r.mode == "aussen_zu_warm"
    assert r.reason_key == "outside_too_hot"


def test_window_open_keeps_airing_for_co2():
    r = evaluate_room(base(co2=1200, window_open=True))
    assert r.mode == "weiter_lueften"
    assert r.reason_key == "continue_airing"


def test_window_open_finished_when_goals_are_done():
    r = evaluate_room(
        base(
            indoor_temp=22,
            indoor_humidity=50,
            outdoor_temp=21.5,
            outdoor_humidity=55,
            co2=850,
            window_open=True,
        )
    )
    assert r.mode == "lueftung_fertig"


def test_co2_optional():
    r = evaluate_room(base(co2=None, indoor_humidity=65, outdoor_humidity=50))
    assert r.mode == "feuchte_lueften"


def test_german_and_english_reasons_are_natural_and_unit_aware():
    r = evaluate_room(base(indoor_temp=23, outdoor_temp=38, target_temp=22))
    de = reason_text(r.reason_key, r.reason_args, "de", "°C")
    en = reason_text(r.reason_key, r.reason_args, "en", "°F")
    assert "Beim Lüften würdest du" in de
    assert "Opening the windows now would" in en
    assert "38" in de and "100" in en


def test_surface_relative_humidity_detects_cold_surface_risk():
    value = surface_relative_humidity(20.0, 50.0, 12.0)
    assert value is not None
    assert value >= 80.0


def test_mold_risk_uses_drier_outdoor_air_for_quiet_prevention():
    r = evaluate_room(
        base(
            indoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_temp=10.0,
            outdoor_humidity=50.0,
            target_temp=20.0,
            surface_temp=12.0,
        )
    )
    assert r.mold_risk is True
    assert r.mode == "schimmel_lueften"
    assert r.color == "green"
    assert r.surface_relative_humidity is not None and r.surface_relative_humidity >= 80.0


def test_mold_risk_waits_when_outdoor_air_would_not_help():
    r = evaluate_room(
        base(
            indoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_temp=19.0,
            outdoor_humidity=95.0,
            target_temp=20.0,
            surface_temp=12.0,
        )
    )
    assert r.mold_risk is True
    assert r.mode == "schimmel_warten"
    assert r.color == "yellow"


def test_open_window_keeps_airing_for_surface_mold_risk():
    r = evaluate_room(
        base(
            indoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_temp=10.0,
            outdoor_humidity=50.0,
            target_temp=20.0,
            surface_temp=12.0,
            window_open=True,
        )
    )
    assert r.mode == "weiter_lueften"


def test_co2_hysteresis_keeps_advice_stable_near_threshold():
    kept = evaluate_room(base(co2=980, previous_mode="co2_lueften"))
    released = evaluate_room(base(co2=940, previous_mode="co2_lueften"))
    assert kept.mode == "co2_lueften"
    assert released.mode != "co2_lueften"


def test_humidity_hysteresis_keeps_drying_advice_stable_near_threshold():
    kept = evaluate_room(
        base(
            indoor_humidity=59.0,
            outdoor_temp=15.0,
            outdoor_humidity=70.0,
            previous_mode="feuchte_lueften",
        )
    )
    fresh = evaluate_room(
        base(
            indoor_humidity=59.0,
            outdoor_temp=15.0,
            outdoor_humidity=70.0,
        )
    )
    assert kept.mode == "feuchte_lueften"
    assert fresh.mode != "feuchte_lueften"


def test_temperature_hysteresis_keeps_hot_outdoor_block_stable():
    kept = evaluate_room(
        base(
            indoor_temp=23.0,
            outdoor_temp=23.6,
            outdoor_humidity=40.0,
            target_temp=22.0,
            previous_mode="aussen_zu_warm",
        )
    )
    fresh = evaluate_room(
        base(
            indoor_temp=23.0,
            outdoor_temp=23.6,
            outdoor_humidity=40.0,
            target_temp=22.0,
        )
    )
    assert kept.mode == "aussen_zu_warm"
    assert fresh.mode != "aussen_zu_warm"


def test_open_window_co2_hysteresis_avoids_flapping_at_1000_ppm():
    kept = evaluate_room(
        base(
            co2=980,
            target_temp=23,
            window_open=True,
            previous_mode="weiter_lueften",
        )
    )
    released = evaluate_room(
        base(
            co2=940,
            target_temp=23,
            window_open=True,
            previous_mode="weiter_lueften",
        )
    )
    assert kept.mode == "weiter_lueften"
    assert released.mode == "lueftung_fertig"

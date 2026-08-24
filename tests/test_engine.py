from custom_components.lueftungsberater.engine import (
    absolute_humidity,
    evaluate_room,
    surface_relative_humidity,
)
from custom_components.lueftungsberater.localization import reason_text
from custom_components.lueftungsberater.models import RoomInput


def base(**kw):
    data = dict(
        indoor_temp=22,
        indoor_humidity=50,
        outdoor_temp=20,
        outdoor_humidity=50,
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


def test_nina_danger_wins_even_against_high_co2():
    r = evaluate_room(
        base(
            co2=2500,
            nina_status="danger",
            nina_reason_key="air_smoke_danger",
            nina_original_reason="Brandrauch",
        )
    )
    assert r.color == "red" and r.mode == "nina_aussenluftgefahr"
    assert r.reason_key == "air_smoke_danger"


def test_nina_caution_is_orange_when_there_is_no_reason_to_air():
    r = evaluate_room(base(nina_status="caution"))
    assert r.color == "orange" and r.mode == "nina_vorsicht"


def test_nina_caution_becomes_tradeoff_with_high_co2():
    r = evaluate_room(base(co2=1500, nina_status="caution"))
    assert r.color == "yellow" and r.mode == "co2_abwaegung"
    assert r.recommendation_key == "short_observation"


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


def test_weather_caution_is_orange_without_a_ventilation_need():
    r = evaluate_room(
        base(
            weather_caution=True,
            weather_reason_key="weather_heavy_rain_caution",
        )
    )
    assert r.color == "orange"
    assert r.mode == "wetter_vorsicht"


def test_about_point_nine_grams_drying_advantage_is_useful_at_60_percent():
    # 22 °C / 60 % indoors vs 20 °C / 62 % outdoors is about +0.93 g/m³.
    r = evaluate_room(
        base(
            indoor_humidity=60,
            outdoor_temp=20,
            outdoor_humidity=62,
        )
    )
    assert 0.8 < r.absolute_humidity_difference < 1.0
    assert r.color == "green"
    assert r.mode == "feuchte_lueften"


def test_small_absolute_humidity_delta_is_neutral_not_a_fake_threshold():
    # About +0.41 g/m³ is deliberately inside the technical ±0.5 dead-band.
    r = evaluate_room(
        base(
            indoor_humidity=60,
            outdoor_temp=20,
            outdoor_humidity=65,
        )
    )
    assert 0 < r.absolute_humidity_difference < 0.5
    assert r.color == "yellow"
    assert r.mode == "feuchte_neutral"
    assert r.recommendation_key == "optional"


def test_wetter_outdoor_air_is_orange_when_everything_inside_is_already_good():
    r = evaluate_room(
        base(
            indoor_temp=22,
            indoor_humidity=50,
            outdoor_temp=22,
            outdoor_humidity=55,
        )
    )
    assert -1.1 < r.absolute_humidity_difference < -0.8
    assert r.color == "orange"
    assert r.mode == "aussen_deutlich_feuchter"


def test_high_co2_can_outweigh_a_modest_humidity_disadvantage():
    r = evaluate_room(
        base(
            indoor_humidity=60,
            outdoor_temp=20,
            outdoor_humidity=73,
            co2=1500,
        )
    )
    assert r.absolute_humidity_difference < -0.5
    assert r.color == "yellow"
    assert r.mode == "co2_abwaegung"


def test_critical_co2_accepts_modest_humidity_disadvantage():
    r = evaluate_room(
        base(
            indoor_humidity=60,
            outdoor_temp=20,
            outdoor_humidity=73,
            co2=2500,
        )
    )
    assert r.color == "green"
    assert r.mode == "co2_kritisch"


def test_critical_co2_does_not_override_real_weather_danger():
    r = evaluate_room(base(co2=2500, weather_danger=True))
    assert r.color == "red"
    assert r.mode == "wettergefahr"


def test_light_rain_does_not_erase_critical_co2_need():
    r = evaluate_room(base(co2=2500, rain_now=True))
    assert r.color == "green"
    assert r.reason_key == "co2_critical_rain"


def test_rain_in_90_minutes_does_not_block_a_short_airing_now():
    r = evaluate_room(base(co2=1500, rain_soon=True, rain_minutes_until=90))
    assert r.color == "green"
    assert r.mode == "co2_lueften"


def test_rain_that_can_overlap_airing_creates_a_tradeoff():
    r = evaluate_room(base(co2=1500, rain_soon=True, rain_minutes_until=8))
    assert r.color == "yellow"
    assert r.mode == "co2_abwaegung"
    assert r.reason_args["caution"] == "rain"


def test_personal_target_is_the_normal_temperature_reference():
    r = evaluate_room(
        base(
            indoor_temp=27,
            target_temp=27,
            outdoor_temp=20,
            outdoor_humidity=50,
        )
    )
    assert r.mode == "aussen_zu_kalt"
    assert r.color == "orange"


def test_very_hot_room_can_be_cooled_even_if_target_was_set_very_high():
    r = evaluate_room(
        base(
            indoor_temp=30,
            target_temp=30,
            outdoor_temp=25,
            outdoor_humidity=50,
        )
    )
    assert r.color == "green"
    assert r.mode == "kuehlen"
    assert r.reason_args["health_heat"] is True


def test_surface_relative_humidity_detects_cold_surface_risk():
    value = surface_relative_humidity(20.0, 50.0, 12.0)
    assert value is not None
    assert value >= 80.0


def test_no_surface_sensor_means_no_surface_claim():
    r = evaluate_room(base(surface_temp=None))
    assert r.surface_relative_humidity is None
    assert r.mold_risk is False
    assert r.mold_persistent is False


def test_surface_moisture_can_quietly_influence_the_ampel():
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
    assert r.reason_key == "surface_moisture_ventilate"


def test_persistent_surface_moisture_gets_explicit_context():
    r = evaluate_room(
        base(
            indoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_temp=10.0,
            outdoor_humidity=50.0,
            target_temp=20.0,
            surface_temp=12.0,
            mold_persistent=True,
            mold_critical_minutes_24h=720,
        )
    )
    assert r.mold_persistent is True
    assert r.mode == "schimmel_langzeit_lueften"
    assert r.reason_key == "surface_moisture_persistent_ventilate"


def test_surface_moisture_waits_when_outdoor_air_is_wetter():
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
    assert r.color == "orange"


def test_air_quality_moderate_is_a_disadvantage_not_a_hard_hazard():
    no_need = evaluate_room(base(air_quality="moderate", air_quality_pollutant="o3", air_quality_value=100))
    high_co2 = evaluate_room(base(co2=2500, air_quality="moderate", air_quality_pollutant="o3", air_quality_value=100))
    assert no_need.color == "orange" and no_need.mode == "luftqualitaet_maessig"
    assert high_co2.color == "yellow" and high_co2.mode == "co2_kritisch_vorsicht"


def test_poor_air_quality_is_orange_even_with_critical_co2():
    r = evaluate_room(
        base(
            co2=2500,
            air_quality="poor",
            air_quality_pollutant="pm2_5",
            air_quality_value=35,
        )
    )
    assert r.color == "orange"
    assert r.mode == "luftqualitaet_schlecht"


def test_24_hour_routine_fallback_is_kept():
    r = evaluate_room(
        base(
            indoor_temp=22,
            indoor_humidity=50,
            outdoor_temp=22,
            outdoor_humidity=50,
            hours_since_airing=25,
        )
    )
    assert r.color == "green"
    assert r.mode == "routine_lueften"


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
            outdoor_humidity=50,
            co2=850,
            window_open=True,
        )
    )
    assert r.mode == "lueftung_fertig"


def test_co2_optional():
    r = evaluate_room(base(co2=None, indoor_humidity=65, outdoor_humidity=40))
    assert r.mode == "feuchte_lueften"


def test_co2_hysteresis_keeps_advice_stable_near_threshold():
    kept = evaluate_room(base(co2=980, previous_mode="co2_lueften"))
    released = evaluate_room(base(co2=940, previous_mode="co2_lueften"))
    assert kept.mode == "co2_lueften"
    assert released.mode != "co2_lueften"


def test_humidity_hysteresis_keeps_active_drying_advice_stable():
    # At 59 % the start threshold is no longer met, but a running drying
    # recommendation may continue down to the smaller 0.3 g/m³ dead-band.
    kept = evaluate_room(
        base(
            indoor_humidity=59.0,
            outdoor_temp=20.0,
            outdoor_humidity=64.0,
            previous_mode="feuchte_lueften",
        )
    )
    fresh = evaluate_room(
        base(
            indoor_humidity=59.0,
            outdoor_temp=20.0,
            outdoor_humidity=64.0,
        )
    )
    assert kept.mode == "feuchte_lueften"
    assert fresh.mode != "feuchte_lueften"


def test_open_window_co2_hysteresis_avoids_flapping_at_1000_ppm():
    kept = evaluate_room(
        base(co2=980, window_open=True, previous_mode="weiter_lueften")
    )
    released = evaluate_room(
        base(co2=940, window_open=True, previous_mode="weiter_lueften")
    )
    assert kept.mode == "weiter_lueften"
    assert released.mode == "lueftung_fertig"


def test_cold_outdoor_air_cools_warm_room_toward_personal_target():
    r = evaluate_room(
        base(
            indoor_temp=23.5,
            target_temp=22.0,
            outdoor_temp=16.0,
            outdoor_humidity=50,
        )
    )
    assert r.color == "green"
    assert r.mode == "kuehlen"


def test_open_window_keeps_cooling_until_target_is_effectively_reached():
    r = evaluate_room(
        base(
            indoor_temp=22.4,
            target_temp=22.0,
            outdoor_temp=16.0,
            outdoor_humidity=50,
            window_open=True,
            previous_mode="weiter_lueften",
        )
    )
    assert r.color == "green"
    assert r.mode == "weiter_lueften"
    assert r.reason_args["continue_cooling"] is True


def test_closed_window_does_not_reopen_for_small_temperature_deviation():
    r = evaluate_room(
        base(
            indoor_temp=22.4,
            target_temp=22.0,
            outdoor_temp=16.0,
            outdoor_humidity=50,
            window_open=False,
        )
    )
    # Starting threshold remains 1 K; hysteresis only applies to an airing that
    # is already in progress.
    assert r.color == "orange"
    assert r.mode == "aussen_zu_kalt"


def test_temperature_airing_finishes_cleanly_at_target_instead_of_turning_red():
    r = evaluate_room(
        base(
            indoor_temp=22.1,
            target_temp=22.0,
            outdoor_temp=16.0,
            outdoor_humidity=50,
            window_open=True,
            previous_mode="weiter_lueften",
        )
    )
    assert r.color == "yellow"
    assert r.mode == "lueftung_fertig"
    assert r.recommendation_key == "can_close"

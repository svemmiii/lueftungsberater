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
    assert high_co2.color == "green" and high_co2.mode == "co2_kritisch"


def test_poor_air_quality_creates_a_cautious_tradeoff_with_critical_co2():
    r = evaluate_room(
        base(
            co2=2500,
            air_quality="poor",
            air_quality_pollutant="pm2_5",
            air_quality_value=35,
        )
    )
    assert r.color == "yellow"
    assert r.mode == "co2_kritisch_vorsicht"
    assert r.safety_lock is False


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


def test_co2_hysteresis_keeps_advice_stable_down_to_900_ppm():
    kept = evaluate_room(base(co2=920, previous_mode="co2_lueften", previous_need="co2_elevated"))
    released = evaluate_room(base(co2=899, previous_mode="co2_lueften", previous_need="co2_elevated"))
    held_below_threshold = evaluate_room(
        base(
            co2=850,
            previous_mode="co2_lueften",
            previous_need="co2_elevated",
            co2_pending_hold=True,
        )
    )
    assert kept.primary_need == "co2_elevated"
    assert released.primary_need != "co2_elevated"
    assert held_below_threshold.primary_need == "co2_elevated"


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


def test_open_window_co2_hysteresis_uses_900_to_850_finish_band():
    continuing = evaluate_room(
        base(
            co2=930,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
        )
    )
    transition = evaluate_room(
        base(
            co2=880,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
        )
    )
    waiting_at_target = evaluate_room(
        base(
            co2=845,
            window_open=True,
            previous_mode="co2_abwaegung",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_ready=False,
        )
    )
    released = evaluate_room(
        base(
            co2=845,
            window_open=True,
            previous_mode="co2_abwaegung",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_ready=True,
        )
    )
    assert continuing.mode == "weiter_lueften"
    assert transition.color == "yellow"
    assert transition.mode == "co2_abwaegung"
    assert transition.reason_args["caution"] == "near_target"
    assert waiting_at_target.mode == "co2_abwaegung"
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


def test_closed_room_temperature_hysteresis_avoids_yellow_green_flicker():
    kept = evaluate_room(
        base(
            indoor_temp=22.7,
            target_temp=22.0,
            outdoor_temp=16.0,
            outdoor_humidity=50,
            window_open=False,
            previous_mode="aussen_deutlich_feuchter",
            previous_need="temperature",
        )
    )
    fresh = evaluate_room(
        base(
            indoor_temp=22.7,
            target_temp=22.0,
            outdoor_temp=16.0,
            outdoor_humidity=50,
            window_open=False,
            previous_mode="aussen_deutlich_feuchter",
            previous_need=None,
        )
    )
    assert kept.primary_need == "temperature"
    assert kept.room_status_color == "yellow"
    assert fresh.primary_need != "temperature"
    assert fresh.room_status_color == "green"


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
    # A fresh recommendation still starts at 1 K; the lower band is only used
    # after an existing temperature recommendation so sensor noise cannot start it.
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


# Agreed real-world colour matrix for the four-stage advisor. These tests are
# intentionally scenario-based: no single sensor is allowed to choose a colour
# without the rest of the room/outdoor context.
def test_agreed_matrix_1_neutral_conditions_are_yellow():
    r = evaluate_room(base(outdoor_temp=21, outdoor_humidity=50, co2=700))
    assert r.color == "yellow"


def test_agreed_matrix_2_cooler_outside_without_need_is_orange():
    r = evaluate_room(base(outdoor_temp=17, outdoor_humidity=50, co2=700))
    assert r.color == "orange"


def test_agreed_matrix_3_strong_cooling_and_drying_without_need_can_be_red():
    r = evaluate_room(base(indoor_humidity=45, outdoor_temp=8, outdoor_humidity=40, co2=700))
    assert r.color == "red"
    assert r.safety_lock is False


def test_agreed_matrix_4_cooling_toward_target_is_green():
    r = evaluate_room(base(indoor_temp=25, target_temp=22, outdoor_temp=14, outdoor_humidity=45, co2=700))
    assert r.color == "green"


def test_agreed_matrix_5_mild_co2_does_not_justify_hotter_wetter_air():
    r = evaluate_room(base(outdoor_temp=31, outdoor_humidity=34, co2=1250))
    assert r.color == "orange"


def test_agreed_matrix_6_high_co2_can_outweigh_hotter_wetter_air():
    r = evaluate_room(base(outdoor_temp=31, outdoor_humidity=34, co2=1800))
    assert r.color == "green"


def test_agreed_matrix_7_critical_co2_can_outweigh_hotter_wetter_air():
    r = evaluate_room(base(outdoor_temp=31, outdoor_humidity=34, co2=2600))
    assert r.color == "green"


def test_co2_session_transitions_green_to_yellow_then_outdoor_disadvantage_after_close():
    green = evaluate_room(
        base(
            outdoor_temp=31,
            outdoor_humidity=34,
            co2=930,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
        )
    )
    yellow = evaluate_room(
        base(
            outdoor_temp=31,
            outdoor_humidity=34,
            co2=880,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
        )
    )
    orange = evaluate_room(
        base(
            outdoor_temp=31,
            outdoor_humidity=34,
            co2=850,
            window_open=False,
            previous_mode="lueftung_fertig",
        )
    )
    assert green.color == "green"
    assert yellow.color == "yellow"
    assert orange.color == "orange"


def test_agreed_matrix_9_high_humidity_with_drier_outdoor_air_is_green():
    r = evaluate_room(base(indoor_humidity=66, outdoor_temp=18, outdoor_humidity=40, co2=800))
    assert r.color == "green"


def test_agreed_matrix_10_high_humidity_with_wetter_outdoor_air_is_orange():
    r = evaluate_room(base(indoor_humidity=66, outdoor_temp=24, outdoor_humidity=80, co2=800))
    assert r.color == "orange"


def test_agreed_matrix_11_critical_co2_with_light_rain_stays_green():
    r = evaluate_room(base(co2=2300, rain_now=True))
    assert r.color == "green"


def test_agreed_matrix_13_critical_co2_with_wind_caution_is_yellow():
    r = evaluate_room(base(co2=2600, weather_caution=True, weather_reason_key="weather_wind_caution"))
    assert r.color == "yellow"
    assert r.safety_lock is False


def test_agreed_matrix_14_severe_weather_uses_the_separate_safety_lock():
    r = evaluate_room(base(co2=2600, weather_danger=True, weather_reason_key="weather_wind_danger"))
    assert r.safety_lock is True
    assert r.color == "red"


def test_very_poor_air_quality_keeps_absolute_health_class_but_local_context_changes_urgency():
    typical = evaluate_room(base(air_quality="very_poor", air_quality_typical=True, air_quality_unusual=False, air_quality_trend="stable"))
    episode = evaluate_room(base(air_quality="very_poor", air_quality_typical=False, air_quality_unusual=True, air_quality_trend="rising"))
    assert typical.air_quality == "very_poor" and episode.air_quality == "very_poor"
    assert typical.color == "orange"
    assert episode.color == "red"
    assert episode.safety_lock is False


def test_outdoor_co2_is_context_not_a_fake_good_indoor_value():
    r = evaluate_room(base(co2=2500, outdoor_co2=2450))
    assert r.co2_status == "critical"
    assert r.color == "yellow"
    assert r.reason_args["caution"] == "outdoor_co2"
    assert r.co2_difference == 50


def test_room_status_colour_is_independent_from_ventilation_colour():
    good_room_bad_outside = evaluate_room(base(co2=700, outdoor_temp=17))
    bad_room_good_outside = evaluate_room(base(co2=2600))
    assert good_room_bad_outside.room_status_color == "green"
    assert good_room_bad_outside.color == "orange"
    assert bad_room_good_outside.room_status_color == "red"
    assert bad_room_good_outside.color == "green"


def test_room_status_never_uses_red_when_ventilation_is_not_recommended():
    tradeoff = evaluate_room(
        base(
            co2=2600,
            outdoor_temp=31,
            outdoor_humidity=34,
            weather_caution=True,
            weather_reason_key="weather_wind_caution",
        )
    )
    assert tradeoff.color == "yellow"
    assert tradeoff.room_status_color != "red"


def test_room_status_keeps_external_disadvantage_green_when_indoor_air_is_good():
    result = evaluate_room(base(co2=700, outdoor_temp=8, outdoor_humidity=40))
    assert result.color in {"orange", "red"}
    assert result.safety_lock is False
    assert result.room_status_color == "green"


def test_room_view_keeps_borderline_humidity_green_when_outside_is_worse():
    """Regression for the v0.7.5 double-orange card shown by the user."""
    result = evaluate_room(
        base(
            indoor_temp=23.0,
            target_temp=22.0,
            indoor_humidity=60.6,
            outdoor_temp=24.0,
            outdoor_humidity=67.0,
            co2=791,
        )
    )
    assert result.color == "orange"
    assert result.mode == "feuchte_warten"
    assert result.room_status_color == "green"
    assert result.room_recommendation_key == "room_good"
    text = reason_text(result.room_reason_key, result.room_reason_args, "de")
    assert "leicht erhöht" in text
    assert "Außenluft" in text


def test_room_view_mild_indoor_need_stays_green_when_outside_is_very_bad():
    result = evaluate_room(
        base(
            indoor_temp=23.0,
            target_temp=22.0,
            indoor_humidity=50.0,
            outdoor_temp=38.0,
            outdoor_humidity=50.0,
            co2=1100,
        )
    )
    assert result.color == "orange"
    assert result.mode == "co2_warten"
    assert result.room_status_color == "green"


def test_room_view_rises_when_indoor_need_becomes_stronger_despite_bad_outside():
    result = evaluate_room(
        base(
            indoor_temp=23.0,
            target_temp=22.0,
            indoor_humidity=50.0,
            outdoor_temp=38.0,
            outdoor_humidity=50.0,
            co2=1500,
        )
    )
    assert result.color == "yellow"
    assert result.room_status_color == "yellow"
    assert result.room_recommendation_key == "room_watch"


def test_minimum_co2_airing_keeps_green_session_open_even_after_fast_co2_drop():
    r = evaluate_room(
        base(
            co2=500,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_ready=True,
            co2_minimum_airing_active=True,
        )
    )
    assert r.color == "green"
    assert r.mode == "co2_mindestlueftung"
    assert r.recommendation_key == "keep_open"
    assert r.reason_key == "co2_minimum_airing"
    assert r.duration_key == "co2_minimum"


def test_minimum_co2_airing_preserves_cautious_yellow_session():
    r = evaluate_room(
        base(
            co2=700,
            window_open=True,
            previous_mode="co2_abwaegung",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_ready=True,
            co2_minimum_airing_active=True,
            co2_minimum_airing_cautious=True,
        )
    )
    assert r.color == "yellow"
    assert r.mode == "co2_mindestlueftung_vorsicht"
    assert r.recommendation_key == "short_observation"


def test_minimum_co2_airing_never_overrides_hard_nina_lock():
    r = evaluate_room(
        base(
            co2=700,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_ready=True,
            co2_minimum_airing_active=True,
            nina_status="danger",
        )
    )
    assert r.safety_lock is True
    assert r.mode == "nina_aussenluftgefahr"
    assert r.color == "red"


def test_co2_session_target_depends_on_why_airing_became_worthwhile():
    # Good outside conditions: even if the user waits until 1500 ppm, the
    # advisor would already have recommended airing from the 1000-ppm band.
    good = evaluate_room(base(co2=1500))
    assert good.mode == "co2_lueften"
    assert good.co2_session_target == 850

    # Moderate humidity drawback: the elevated band is only a trade-off, while
    # the high band makes the recommendation clear. Use 1400 - 150 = 1250 ppm.
    moderate = evaluate_room(
        base(
            indoor_humidity=50,
            outdoor_temp=22,
            outdoor_humidity=65,
            co2=1450,
        )
    )
    assert moderate.mode == "co2_lueften"
    assert moderate.absolute_humidity_difference < -0.5
    assert moderate.co2_session_target == 1250

    # Stronger drawback that needs the explicit >=1700 override.
    stronger = evaluate_room(
        base(
            indoor_temp=25,
            target_temp=22,
            indoor_humidity=50,
            outdoor_temp=31,
            outdoor_humidity=34,
            co2=1800,
        )
    )
    assert stronger.mode == "co2_lueften_mit_nachteil"
    assert stronger.co2_session_target == 1550


def test_dynamic_co2_finish_target_can_end_above_1000_without_reopening_same_session():
    continuing = evaluate_room(
        base(
            co2=1390,
            window_open=True,
            previous_mode="co2_mindestlueftung",
            previous_need="humidity",
            co2_airing_active=True,
            co2_finish_target=1250,
            co2_near_target=1300,
        )
    )
    near = evaluate_room(
        base(
            co2=1280,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_high",
            co2_airing_active=True,
            co2_finish_target=1250,
            co2_near_target=1300,
        )
    )
    finished = evaluate_room(
        base(
            co2=1240,
            window_open=True,
            previous_mode="co2_abwaegung",
            previous_need="co2_high",
            co2_airing_active=True,
            co2_finish_ready=True,
            co2_finish_target=1250,
            co2_near_target=1300,
        )
    )
    assert continuing.mode == "weiter_lueften"
    assert near.mode == "co2_abwaegung"
    assert near.reason_args["caution"] == "near_target"
    assert near.reason_args["co2_target"] == 1250
    assert finished.mode == "lueftung_fertig"

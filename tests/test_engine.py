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




def test_temperature_session_does_not_invent_humidity_hysteresis_below_start_threshold():
    """Generic weiter_lueften must not turn 59 % into a new humidity session."""
    closed = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=21.0,
            outdoor_temp=20.0,
            indoor_humidity=59.0,
            outdoor_humidity=40.0,
            co2=700.0,
        )
    )
    assert closed.mode == "kuehlen"
    assert closed.decision_need == "temperature"

    opened = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=21.0,
            outdoor_temp=20.0,
            indoor_humidity=59.0,
            outdoor_humidity=40.0,
            co2=700.0,
            window_open=True,
            previous_mode=closed.mode,
            previous_need=closed.decision_need,
        )
    )
    assert opened.mode == "weiter_lueften"
    assert opened.decision_need == "temperature"

    finished_temperature = evaluate_room(
        base(
            indoor_temp=21.1,
            target_temp=21.0,
            outdoor_temp=20.0,
            indoor_humidity=59.0,
            outdoor_humidity=40.0,
            co2=700.0,
            window_open=True,
            previous_mode=opened.mode,
            previous_need=opened.decision_need,
        )
    )
    assert finished_temperature.mode == "lueftung_fertig"
    assert finished_temperature.decision_need != "humidity"
    assert finished_temperature.primary_need != "humidity"
    assert finished_temperature.reason_args.get("continue_moisture") is not True


def test_temperature_session_does_not_invent_mold_hysteresis_below_start_threshold():
    """A 79 % surface RH may only be held if mold actually drove the prior session."""
    closed = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=21.0,
            outdoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_humidity=40.0,
            surface_temp=16.6,  # ~79 % surface RH: below the 80 % start threshold
            co2=700.0,
        )
    )
    assert closed.mode == "kuehlen"
    assert closed.mold_risk is False

    opened = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=21.0,
            outdoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_humidity=40.0,
            surface_temp=16.6,
            co2=700.0,
            window_open=True,
            previous_mode=closed.mode,
            previous_need=closed.decision_need,
        )
    )
    assert opened.mode == "weiter_lueften"
    assert opened.decision_need == "temperature"
    assert opened.mold_risk is False

    cooling_exhausted = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=21.0,
            outdoor_temp=23.7,
            indoor_humidity=50.0,
            outdoor_humidity=40.0,
            surface_temp=16.6,
            co2=700.0,
            window_open=True,
            previous_mode=opened.mode,
            previous_need=opened.decision_need,
        )
    )
    assert cooling_exhausted.mode == "lueftung_fertig"
    assert cooling_exhausted.mold_risk is False
    assert cooling_exhausted.decision_need not in {"mold", "mold_persistent"}


def test_real_humidity_session_keeps_58_percent_continuation_hysteresis():
    """The fix must preserve the intended 60 -> 58 % humidity hysteresis."""
    result = evaluate_room(
        base(
            indoor_humidity=59.0,
            outdoor_temp=20.0,
            outdoor_humidity=64.0,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="humidity",
        )
    )
    assert result.mode == "weiter_lueften"
    assert result.decision_need == "humidity"
    assert result.reason_args["continue_moisture"] is True


def test_real_mold_session_keeps_78_percent_surface_hysteresis():
    """The fix must preserve the intended 80 -> 78 % mold hysteresis."""
    result = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=24.0,
            outdoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_humidity=40.0,
            surface_temp=16.6,  # ~79 %
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="mold",
        )
    )
    assert result.mold_risk is True
    assert result.decision_need == "mold"
    assert result.mode == "weiter_lueften"
    assert result.reason_args["continue_moisture"] is True


def test_non_temperature_session_does_not_inherit_temperature_continuation_band():
    """A generic weiter_lueften from another reason must not start at 0.4 K delta."""
    result = evaluate_room(
        base(
            indoor_temp=22.4,
            target_temp=22.0,
            outdoor_temp=16.0,
            indoor_humidity=50.0,
            outdoor_humidity=50.0,
            co2=850.0,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
        )
    )
    assert result.mode == "lueftung_fertig"
    assert result.decision_need != "temperature"
    assert result.reason_args.get("continue_cooling") is not True




def test_real_temperature_session_keeps_lower_running_gradient_without_making_it_a_start_rule():
    """0.5 K outdoor help is a continuation band only for temperature sessions."""
    running = evaluate_room(
        base(
            indoor_temp=21.2,
            target_temp=21.8,
            outdoor_temp=21.75,  # +0.55 K: enough to continue, below +0.7 K start help
            indoor_humidity=50.0,
            outdoor_humidity=50.0,
            co2=700.0,
            window_open=True,
            open_minutes=8.0,
            previous_mode="weiter_lueften",
            previous_need="temperature",
        )
    )
    assert running.mode == "weiter_lueften"
    assert running.decision_need == "temperature"
    assert running.reason_args["continue_warming"] is True

    unrelated_context = evaluate_room(
        base(
            indoor_temp=21.2,
            target_temp=21.8,
            outdoor_temp=21.75,
            indoor_humidity=50.0,
            outdoor_humidity=50.0,
            co2=700.0,
            window_open=True,
            open_minutes=8.0,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
        )
    )
    assert unrelated_context.mode == "lueftung_fertig"
    assert unrelated_context.decision_need != "temperature"


def test_open_window_co2_session_memory_does_not_create_a_fresh_need_below_900():
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
    # Below the 900-ppm continuation band, session memory no longer injects a
    # synthetic co2_elevated need. Current outdoor conditions may therefore
    # finish or discourage the airing exactly as a fresh evaluation would.
    assert transition.mode == "lueftung_fertig"
    assert transition.color == "yellow"
    assert waiting_at_target.mode == "aussen_zu_kalt"
    assert waiting_at_target.color == "orange"
    assert released.mode == "aussen_zu_kalt"

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
    # v0.8.1 keeps a mild level-1 deviation green in the action-oriented room
    # view. The remembered need still exists internally; it simply no longer
    # makes the front card look as if the user must act.
    assert kept.room_status_color == "green"
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
            previous_need="temperature",
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


def test_co2_session_transitions_green_to_yellow_without_masking_outdoor_disadvantage():
    # With still-good current outdoor conditions, the fixed session target
    # transitions normally from keep-open green to the near-target yellow band.
    green = evaluate_room(
        base(
            co2=930,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
        )
    )
    yellow = evaluate_room(
        base(
            co2=880,
            window_open=True,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
        )
    )
    # Once the current outside situation itself argues against opening, session
    # memory must not force it back to green.
    orange = evaluate_room(
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


def test_room_view_mild_co2_stays_green_even_when_airing_would_be_easy():
    result = evaluate_room(base(co2=1100, outdoor_temp=20, outdoor_humidity=50))
    assert result.color == "green"
    assert result.room_status_color == "green"
    assert result.room_recommendation_key == "room_good"


def test_room_view_meaningful_co2_need_jumps_to_orange_when_outside_is_good():
    result = evaluate_room(base(co2=1500, outdoor_temp=20, outdoor_humidity=50))
    assert result.color == "green"
    assert result.room_status_color == "orange"
    assert result.room_recommendation_key == "room_need"


def test_room_view_routine_fallback_stays_visible_as_yellow():
    result = evaluate_room(base(co2=None, hours_since_airing=25))
    assert result.primary_need == "routine"
    assert result.room_status_color == "yellow"
    assert result.room_recommendation_key == "room_watch"


def test_short_term_thunderstorm_can_turn_current_co2_airing_into_tradeoff():
    result = evaluate_room(
        base(
            co2=1500,
            short_term_weather_change="worsening",
            short_term_weather_kind="thunderstorm",
            short_term_weather_minutes=10,
        )
    )
    assert result.color == "yellow"
    assert result.mode == "co2_abwaegung"
    assert result.reason_args["caution"] == "weather_forecast"


def test_short_term_weather_is_ignored_when_short_airing_finishes_well_before_it():
    result = evaluate_room(
        base(
            co2=1500,
            short_term_weather_change="worsening",
            short_term_weather_kind="thunderstorm",
            short_term_weather_minutes=50,
        )
    )
    assert result.color == "green"
    assert result.mode == "co2_lueften"


def test_short_term_thunderstorm_warns_even_when_room_has_no_airing_need():
    result = evaluate_room(
        base(
            co2=700,
            short_term_weather_change="worsening",
            short_term_weather_kind="thunderstorm",
            short_term_weather_minutes=10,
        )
    )
    assert result.color == "orange"
    assert result.mode == "wetter_vorsicht"
    assert result.reason_key == "weather_forecast_worsening"
    assert result.room_status_color == "green"


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


def test_post_airing_rearm_threshold_suppresses_lower_co2_band_only():
    # A completed 1400-band session may not instantly become a fresh 1000-band
    # recommendation merely because the weather improved after closing.
    blocked = evaluate_room(
        base(
            co2=1200,
            co2_rearm_threshold=1400,
            outdoor_temp=20,
            outdoor_humidity=45,
        )
    )
    assert not blocked.primary_need.startswith("co2_")

    released = evaluate_room(
        base(
            co2=1400,
            co2_rearm_threshold=1400,
            outdoor_temp=20,
            outdoor_humidity=45,
        )
    )
    assert released.primary_need == "co2_high"


def test_crossing_co2_elevated_threshold_never_weakens_temperature_airing():
    before = evaluate_room(
        base(
            indoor_temp=16,
            indoor_humidity=45,
            outdoor_temp=18,
            outdoor_humidity=60,
            target_temp=21,
            co2=999,
        )
    )
    after = evaluate_room(
        base(
            indoor_temp=16,
            indoor_humidity=45,
            outdoor_temp=18,
            outdoor_humidity=60,
            target_temp=21,
            co2=1000,
        )
    )
    assert before.color == "green"
    assert after.color == "green"


def test_crossing_co2_high_threshold_never_weakens_humidity_airing():
    common = dict(
        indoor_temp=16,
        indoor_humidity=60,
        outdoor_temp=-10,
        outdoor_humidity=20,
        target_temp=21,
    )
    before = evaluate_room(base(**common, co2=1399))
    after = evaluate_room(base(**common, co2=1400))
    assert before.color == "green"
    assert after.color == "green"
    assert after.mode == "co2_lueften_mit_nachteil"
    assert after.primary_need == "co2_high"


def test_critical_co2_never_weakens_independent_green_humidity_need():
    common = dict(
        indoor_temp=16,
        indoor_humidity=60,
        outdoor_temp=-10,
        outdoor_humidity=20,
        target_temp=21,
    )
    before = evaluate_room(base(**common, co2=1999))
    after = evaluate_room(base(**common, co2=2001))
    assert before.color == "green"
    assert after.color == "green"
    assert after.mode == "co2_lueften_mit_nachteil"
    assert after.primary_need == "co2_critical"


def test_hard_warning_still_wins_over_independent_green_need():
    result = evaluate_room(
        base(
            indoor_temp=16,
            indoor_humidity=70,
            outdoor_temp=-10,
            outdoor_humidity=20,
            co2=2200,
            nina_status="danger",
        )
    )
    assert result.safety_lock is True
    assert result.mode == "nina_aussenluftgefahr"


def test_regression_more_humidity_does_not_hide_1800ppm_co2():
    common = dict(
        indoor_temp=21,
        outdoor_temp=21,
        outdoor_humidity=90,
        target_temp=21,
        co2=1800,
    )
    below = evaluate_room(base(**common, indoor_humidity=64.9))
    at = evaluate_room(base(**common, indoor_humidity=65.0))
    assert below.color == "yellow"
    assert at.color == "yellow"
    assert below.mode == at.mode == "co2_abwaegung"
    # At 65 % RH the strongest indoor signal may legitimately become humidity;
    # the important invariant is that the still-active CO₂ need remains in the
    # combined decision/session instead of disappearing.
    assert below.co2_session_need == at.co2_session_need == "co2_high"


def test_regression_humidity_threshold_does_not_hide_independent_cooling():
    common = dict(
        indoor_temp=28,
        target_temp=21,
        outdoor_temp=20,
        outdoor_humidity=50,
    )
    below = evaluate_room(base(**common, indoor_humidity=59.9))
    at = evaluate_room(base(**common, indoor_humidity=60.0))
    assert below.color == "green"
    assert at.color == "green"


def test_regression_1399_to_1400_with_rain_never_weakens_recommendation():
    common = dict(
        indoor_temp=16,
        target_temp=21,
        outdoor_temp=18,
        indoor_humidity=40,
        outdoor_humidity=50,
        rain_now=True,
    )
    before = evaluate_room(base(**common, co2=1399))
    after = evaluate_room(base(**common, co2=1400))
    rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    assert rank[after.color] >= rank[before.color]
    assert before.color == after.color == "yellow"


def test_critical_co2_with_moderate_air_quality_keeps_green_session_target():
    result = evaluate_room(base(co2=2000.1, air_quality="moderate"))
    assert result.mode == "co2_kritisch"
    assert result.color == "green"
    assert result.co2_session_target == 850


def test_outdoor_co2_is_general_tradeoff_for_cooling_too():
    result = evaluate_room(
        base(
            indoor_temp=27,
            target_temp=21,
            outdoor_temp=20,
            co2=800,
            outdoor_co2=1500,
        )
    )
    assert result.primary_need == "temperature"
    assert result.mode == "komfort_abwaegung"
    assert result.color == "yellow"
    assert result.reason_args["caution"] == "outdoor_co2"


def test_invariant_increasing_co2_never_weakens_recommendation():
    """More indoor CO2 must not weaken the action with outside fixed."""
    from itertools import product

    rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    levels = [700, 999, 1000, 1100, 1399, 1400, 1500, 1699, 1700, 2000, 2000.1, 2400]
    scenarios = product(
        [16.0, 22.0, 28.0, 31.0],
        [38.0, 59.9, 60.0, 65.0, 72.0],
        [-5.0, 18.0, 24.0, 32.0],
        [30.0, 55.0, 85.0],
        [None, 900.0, 1200.0, 1550.0],
        [False, True],
        ["good", "moderate", "poor"],
    )
    for ti, hi, ta, ho, outdoor_co2, rain_now, air_quality in scenarios:
        previous_rank = None
        previous = None
        for co2 in levels:
            result = evaluate_room(
                base(
                    indoor_temp=ti,
                    indoor_humidity=hi,
                    outdoor_temp=ta,
                    outdoor_humidity=ho,
                    target_temp=21.0,
                    co2=co2,
                    outdoor_co2=outdoor_co2,
                    rain_now=rain_now,
                    air_quality=air_quality,
                )
            )
            current_rank = rank[result.color]
            if previous_rank is not None:
                assert current_rank >= previous_rank, (
                    f"CO2 increase weakened recommendation: {previous} -> "
                    f"{(co2, result.color, result.mode)}; "
                    f"scenario={(ti, hi, ta, ho, outdoor_co2, rain_now, air_quality)}"
                )
            previous_rank = current_rank
            previous = (co2, result.color, result.mode)


def test_worse_outdoor_co2_is_visible_even_without_current_airing_need():
    result = evaluate_room(base(co2=900, outdoor_co2=1500))
    assert result.mode == "aussen_co2_hoeher"
    assert result.color == "orange"
    assert result.reason_key == "outdoor_co2_worse"


def test_co2_session_target_never_demands_below_measured_outdoor_co2():
    result = evaluate_room(base(co2=2200, outdoor_co2=1900))
    assert result.co2_session_need == "co2_critical"
    assert result.co2_session_target == 1950


def test_neutral_secondary_need_cannot_relax_poor_outdoor_air():
    common = dict(
        indoor_temp=22,
        outdoor_temp=20,
        outdoor_humidity=65,
        air_quality="poor",
    )
    below = evaluate_room(base(**common, indoor_humidity=59.9))
    at = evaluate_room(base(**common, indoor_humidity=60.0))

    assert below.color == "orange"
    assert at.color == "orange"
    assert below.mode == at.mode == "luftqualitaet_schlecht"


def test_additional_caution_never_relaxes_existing_co2_wait_state():
    common = dict(co2=1500, outdoor_co2=1800)
    baseline = evaluate_room(base(**common))
    nina = evaluate_room(base(**common, nina_status="caution"))
    weather = evaluate_room(base(**common, weather_caution=True))

    assert baseline.color == "orange"
    assert baseline.mode == "co2_warten"
    assert nina.color == weather.color == "orange"
    assert nina.mode == weather.mode == "co2_warten"


def test_additional_caution_never_relaxes_strong_outside_keep_closed_state():
    common = dict(
        indoor_temp=21,
        target_temp=21,
        outdoor_temp=40,
        indoor_humidity=50,
        outdoor_humidity=50,
    )
    baseline = evaluate_room(base(**common))
    nina = evaluate_room(base(**common, nina_status="caution"))
    weather = evaluate_room(base(**common, weather_caution=True))

    assert baseline.color == "red"
    assert baseline.mode == "aussen_stark_unpassend"
    assert nina.color == weather.color == "red"
    assert nina.mode == weather.mode == "aussen_stark_unpassend"


def test_temperature_hysteresis_uses_actual_decision_need_not_ui_primary_need():
    first = evaluate_room(
        base(
            indoor_temp=22.1,
            target_temp=21,
            indoor_humidity=65,
            outdoor_temp=20,
            outdoor_humidity=74,
        )
    )
    assert first.primary_need == "humidity_urgent"
    assert first.decision_need == "temperature"
    assert first.mode == "kuehlen"

    follow_up = evaluate_room(
        base(
            indoor_temp=21.8,
            target_temp=21,
            indoor_humidity=65,
            outdoor_temp=20,
            outdoor_humidity=74,
            previous_mode=first.mode,
            previous_need=first.decision_need,
        )
    )
    assert follow_up.primary_need == "humidity_urgent"
    assert follow_up.decision_need == "temperature"
    assert follow_up.mode == "kuehlen"
    assert follow_up.color == "green"


def test_routine_airing_stays_active_until_five_real_open_minutes():
    initial = evaluate_room(
        base(
            indoor_temp=22,
            outdoor_temp=22,
            hours_since_airing=25,
        )
    )
    assert initial.mode == "routine_lueften"
    assert initial.decision_need == "routine"

    just_opened = evaluate_room(
        base(
            indoor_temp=22,
            outdoor_temp=22,
            hours_since_airing=25,
            window_open=True,
            open_minutes=0.1,
            previous_mode=initial.mode,
            previous_need=initial.decision_need,
        )
    )
    assert just_opened.mode == "weiter_lueften"
    assert just_opened.reason_args["continue_routine"] is True

    after_minimum = evaluate_room(
        base(
            indoor_temp=22,
            outdoor_temp=22,
            hours_since_airing=25,
            window_open=True,
            open_minutes=5.1,
            previous_mode=just_opened.mode,
            previous_need=just_opened.decision_need,
        )
    )
    assert after_minimum.mode == "lueftung_fertig"


def test_invariant_added_soft_warning_never_improves_opening_rank():
    """NINA/weather caution may keep or reduce, but never improve, opening advice."""
    from itertools import product

    opening_rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    scenarios = product(
        [16.0, 21.0, 28.0, 31.0],
        [40.0, 59.9, 60.0, 65.0],
        [-5.0, 20.0, 32.0, 40.0],
        [35.0, 65.0, 85.0],
        [None, 900.0, 1500.0, 2200.0],
        [None, 900.0, 1800.0],
        ["good", "moderate", "poor"],
    )
    for ti, hi, ta, ho, co2, outdoor_co2, air_quality in scenarios:
        common = dict(
            indoor_temp=ti,
            indoor_humidity=hi,
            outdoor_temp=ta,
            outdoor_humidity=ho,
            target_temp=21.0,
            co2=co2,
            outdoor_co2=outdoor_co2,
            air_quality=air_quality,
        )
        baseline = evaluate_room(base(**common))
        for warning in (
            {"nina_status": "caution"},
            {"weather_caution": True},
        ):
            warned = evaluate_room(base(**common, **warning))
            assert opening_rank[warned.color] <= opening_rank[baseline.color], (
                f"Warning improved opening advice: "
                f"{(baseline.color, baseline.mode)} -> {(warned.color, warned.mode)}; "
                f"scenario={common}, warning={warning}"
            )


def test_invariant_worse_air_quality_never_improves_opening_rank():
    """A worse UBA air-quality class must never make opening more attractive."""
    from itertools import product

    opening_rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    scenarios = product(
        [16.0, 22.0, 28.0, 31.0],
        [40.0, 60.0, 65.0],
        [-5.0, 20.0, 32.0],
        [35.0, 65.0, 85.0],
        [None, 1100.0, 1500.0, 2200.0],
        [None, 900.0, 1800.0],
    )
    levels = ["good", "moderate", "poor", "very_poor"]
    for ti, hi, ta, ho, co2, outdoor_co2 in scenarios:
        previous_rank = None
        previous = None
        for air_quality in levels:
            result = evaluate_room(
                base(
                    indoor_temp=ti,
                    indoor_humidity=hi,
                    outdoor_temp=ta,
                    outdoor_humidity=ho,
                    target_temp=21.0,
                    co2=co2,
                    outdoor_co2=outdoor_co2,
                    air_quality=air_quality,
                )
            )
            current_rank = opening_rank[result.color]
            if previous_rank is not None:
                assert current_rank <= previous_rank, (
                    f"Worse air quality improved opening advice: "
                    f"{previous} -> {(air_quality, result.color, result.mode)}; "
                    f"scenario={(ti, hi, ta, ho, co2, outdoor_co2)}"
                )
            previous_rank = current_rank
            previous = (air_quality, result.color, result.mode)


def test_very_poor_air_quality_keeps_severity_with_temperature_need():
    """An indoor temperature need must not relabel very-poor AQ as moderate."""
    result = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=22.0,
            outdoor_temp=20.0,
            indoor_humidity=50.0,
            outdoor_humidity=50.0,
            air_quality="very_poor",
            air_quality_typical=False,
            air_quality_unusual=True,
            air_quality_trend="rising",
        )
    )
    assert result.mode == "luftqualitaet_sehr_schlecht"
    assert result.color == "red"
    assert result.reason_key == "air_quality_very_poor"


def test_more_urgent_harmful_mold_reason_beats_low_priority_cooling_benefit():
    """Persistent mold risk must not be hidden by a weaker comfort benefit."""
    result = evaluate_room(
        base(
            indoor_temp=22.0,
            target_temp=21.0,
            indoor_humidity=45.0,
            outdoor_temp=18.0,
            outdoor_humidity=80.0,
            surface_temp=10.0,
            mold_persistent=True,
        )
    )
    assert result.primary_need == "mold_persistent"
    assert result.decision_need == "mold_persistent"
    assert result.mode == "schimmel_warten"
    assert result.color == "orange"


def test_warming_start_and_open_continuation_use_same_overshoot_guard():
    """Unchanged values must never make a just-started warming session finish."""
    # Outdoor air more than target + 4 K is intentionally not offered for a
    # small warming need, because the running-session rule would reject it too.
    overshoot = evaluate_room(
        base(
            indoor_temp=20.0,
            target_temp=21.0,
            outdoor_temp=30.0,
            indoor_humidity=50.0,
            outdoor_humidity=50.0,
        )
    )
    assert overshoot.mode != "erwaermen"
    assert overshoot.color != "green"

    initial = evaluate_room(
        base(
            indoor_temp=20.0,
            target_temp=21.0,
            outdoor_temp=24.0,
            indoor_humidity=50.0,
            outdoor_humidity=50.0,
        )
    )
    assert initial.mode == "erwaermen"
    assert initial.color == "green"
    assert initial.decision_need == "temperature"

    opened = evaluate_room(
        base(
            indoor_temp=20.0,
            target_temp=21.0,
            outdoor_temp=24.0,
            indoor_humidity=50.0,
            outdoor_humidity=50.0,
            window_open=True,
            previous_mode=initial.mode,
            previous_need=initial.decision_need,
        )
    )
    assert opened.mode == "weiter_lueften"
    assert opened.color == "green"
    assert opened.reason_args["continue_warming"] is True


def test_three_way_merge_soft_warning_cannot_relax_existing_harmful_mold():
    """A third warning/caution must not make an existing orange conflict yellower."""
    common = dict(
        indoor_temp=22.0,
        target_temp=20.0,
        indoor_humidity=40.0,
        outdoor_temp=16.0,
        outdoor_humidity=70.0,
        surface_temp=5.0,
        co2=1500.0,
        outdoor_co2=1450.0,
        air_quality="good",
    )
    baseline = evaluate_room(base(**common))
    assert baseline.mode == "schimmel_warten"
    assert baseline.color == "orange"
    assert baseline.decision_need == "mold"

    for warning in (
        {"nina_status": "caution"},
        {"weather_caution": True},
        {"air_quality": "moderate"},
    ):
        warned_input = dict(common)
        warned_input.update(warning)
        warned = evaluate_room(base(**warned_input))
        assert warned.mode == "schimmel_warten"
        assert warned.color == "orange"
        assert warned.decision_need == "mold"


def test_blocked_air_quality_beats_harmful_co2_when_outdoor_co2_worsens():
    """A red AQ protection state must never be downgraded by orange CO2 harm."""
    common = dict(
        indoor_temp=18.0,
        target_temp=21.0,
        outdoor_temp=20.0,
        indoor_humidity=35.0,
        outdoor_humidity=35.0,
        co2=1500.0,
        air_quality="very_poor",
        air_quality_typical=False,
        air_quality_unusual=True,
        air_quality_trend="rising",
    )

    baseline = evaluate_room(base(**common, outdoor_co2=900.0))
    worsened = evaluate_room(base(**common, outdoor_co2=1800.0))

    assert baseline.mode == "luftqualitaet_sehr_schlecht"
    assert baseline.color == "red"
    assert worsened.mode == "luftqualitaet_sehr_schlecht"
    assert worsened.color == "red"


def test_critical_co2_tradeoff_is_stable_when_weak_routine_need_appears():
    """A weak 24 h routine reason must not turn critical-CO2 tradeoff yellow -> red."""
    common = dict(
        indoor_temp=22.0,
        target_temp=22.0,
        indoor_humidity=45.0,
        outdoor_temp=20.0,
        outdoor_humidity=45.0,
        co2=2500.0,
        outdoor_co2=500.0,
        air_quality="very_poor",
        air_quality_typical=False,
        air_quality_unusual=True,
        air_quality_trend="rising",
    )

    before_routine = evaluate_room(base(**common, hours_since_airing=23.9))
    with_routine = evaluate_room(base(**common, hours_since_airing=24.0))

    assert before_routine.mode == "co2_kritisch_vorsicht"
    assert before_routine.color == "yellow"
    assert before_routine.decision_need == "co2_critical"
    assert before_routine.safety_lock is False

    assert with_routine.mode == "co2_kritisch_vorsicht"
    assert with_routine.color == "yellow"
    assert with_routine.decision_need == "co2_critical"
    assert with_routine.safety_lock is False

    # The same invariant must hold when a weak humidity need appears exactly at
    # its threshold instead of the routine timer becoming active.
    below_rh = evaluate_room(
        base(**{**common, "indoor_humidity": 59.9}, hours_since_airing=23.9)
    )
    at_rh = evaluate_room(
        base(**{**common, "indoor_humidity": 60.0}, hours_since_airing=23.9)
    )
    assert below_rh.color == at_rh.color == "yellow"
    assert below_rh.mode == at_rh.mode == "co2_kritisch_vorsicht"


def test_opening_candidates_use_same_urgency_merge_with_or_without_harmful_candidate():
    """Adding weak routine harm must not change how beneficial/tradeoff are ranked."""
    common = dict(
        indoor_temp=21.9,
        target_temp=21.0,
        indoor_humidity=66.0,
        outdoor_temp=19.0,
        outdoor_humidity=70.0,
        co2=1200.0,
        air_quality="moderate",
    )

    before_routine = evaluate_room(base(**common, hours_since_airing=23.9))
    with_routine = evaluate_room(base(**common, hours_since_airing=24.0))

    # The routine remains a fallback, so the 24 h transition must not change
    # whichever concrete sensor reasons are already active.
    assert before_routine.primary_need == "humidity_urgent"
    assert before_routine.decision_need == "humidity_urgent"
    assert before_routine.mode == "feuchte_lueften"
    assert before_routine.color == "green"

    assert with_routine.primary_need == "humidity_urgent"
    assert with_routine.decision_need == "humidity_urgent"
    assert with_routine.mode == "feuchte_lueften"
    assert with_routine.color == "green"


def test_24h_routine_to_1000ppm_never_weakens_green_airing():
    """The first CO2 band must not erase an already-due useful routine airing."""
    common = dict(
        indoor_temp=21.0,
        target_temp=22.0,
        indoor_humidity=50.0,
        outdoor_temp=21.0,
        outdoor_humidity=50.0,
        outdoor_co2=950.0,
        hours_since_airing=24.0,
    )

    before = evaluate_room(base(**common, co2=999.0))
    after = evaluate_room(base(**common, co2=1000.0))

    assert before.mode == "routine_lueften"
    assert before.color == "green"
    assert after.color == "green"
    assert after.mode == "co2_lueften_mit_nachteil"
    assert after.primary_need == "co2_elevated"
    assert after.decision_need == "co2_elevated"


def test_humidity_threshold_with_drying_air_and_moderate_aq_never_weakens_green_co2():
    """Useful humidity airing must not make 59.9 -> 60.0 % RH green -> yellow."""
    common = dict(
        indoor_temp=22.0,
        target_temp=22.0,
        outdoor_temp=20.0,
        outdoor_humidity=50.0,
        co2=1100.0,
        outdoor_co2=900.0,
        air_quality="moderate",
    )

    below = evaluate_room(base(**common, indoor_humidity=59.9))
    at = evaluate_room(base(**common, indoor_humidity=60.0))

    assert below.mode == "co2_lueften"
    assert below.color == "green"
    assert at.absolute_humidity_difference > 0.5
    assert at.color == "green"
    assert at.mode == "feuchte_lueften"
    assert at.primary_need == "humidity"
    assert at.decision_need == "humidity"


def test_co2_closing_exception_does_not_let_weaker_tradeoff_skip_priority_merge():
    """Outdoor-CO2 harm must not inherit indoor-band urgency and bypass the merge."""
    common = dict(
        indoor_humidity=50.0,
        target_temp=22.0,
        outdoor_temp=20.0,
        outdoor_humidity=50.0,
        co2=1500.0,
        outdoor_co2=1700.0,
    )

    before = evaluate_room(base(**common, indoor_temp=22.9))
    at_temp_need = evaluate_room(base(**common, indoor_temp=23.0))

    assert before.mode == "co2_warten"
    assert before.color == "orange"
    assert at_temp_need.primary_need == "co2_high"
    # The new temperature reason is a genuine yellow trade-off. The unchanged
    # outdoor-CO2 disadvantage no longer becomes artificially "more urgent"
    # merely because indoor CO2 is in the high band.
    assert at_temp_need.decision_need == "temperature"
    assert at_temp_need.mode == "komfort_abwaegung"
    assert at_temp_need.color == "yellow"


def test_active_co2_session_after_minimum_keeps_current_hot_outdoor_tradeoff():
    """Session memory must not turn unchanged hot outdoor conditions yellow -> green."""
    result = evaluate_room(
        base(
            indoor_temp=22.0,
            target_temp=22.0,
            indoor_humidity=50.0,
            outdoor_temp=38.0,
            outdoor_humidity=50.0,
            co2=1500.0,
            window_open=True,
            open_minutes=6.0,
            previous_mode="co2_mindestlueftung_vorsicht",
            previous_need="co2_high",
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
        )
    )

    assert result.color == "yellow"
    assert result.mode == "co2_abwaegung"
    assert result.mode != "weiter_lueften"


def test_active_co2_session_after_minimum_does_not_override_new_rain():
    """Rain after minute five must remain visible instead of being forced green."""
    result = evaluate_room(
        base(
            co2=1500.0,
            window_open=True,
            open_minutes=6.0,
            rain_now=True,
            previous_mode="co2_mindestlueftung",
            previous_need="co2_high",
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
        )
    )

    assert result.color == "yellow"
    assert result.mode == "co2_abwaegung"
    assert result.mode != "weiter_lueften"


def test_active_co2_session_after_minimum_does_not_override_new_forecast_warning():
    """An imminent weather deterioration remains a tradeoff after minimum airing."""
    result = evaluate_room(
        base(
            co2=1500.0,
            window_open=True,
            open_minutes=6.0,
            short_term_weather_change="worsening",
            short_term_weather_kind="thunderstorm",
            short_term_weather_minutes=10.0,
            previous_mode="co2_mindestlueftung",
            previous_need="co2_high",
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
        )
    )

    assert result.color == "yellow"
    assert result.mode == "co2_abwaegung"
    assert result.mode != "weiter_lueften"


def test_post_minimum_co2_session_never_relaxes_fresh_current_evaluation():
    common = dict(
        co2=880.0,
        window_open=True,
        open_minutes=6.0,
        previous_mode="co2_mindestlueftung",
        previous_need="co2_elevated",
        indoor_temp=20.0,
        target_temp=22.0,
        outdoor_temp=18.0,
        outdoor_humidity=50.0,
    )
    fresh = evaluate_room(base(**common, co2_airing_active=False))
    active = evaluate_room(
        base(
            **common,
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
        )
    )
    rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    assert rank[active.color] <= rank[fresh.color]
    assert active.mode == fresh.mode


def test_imminent_rain_aq_change_cannot_turn_mold_tradeoff_green():
    common = dict(
        indoor_temp=22.0,
        indoor_humidity=65.0,
        target_temp=22.0,
        outdoor_temp=20.0,
        outdoor_humidity=50.0,
        co2=2500.0,
        surface_temp=5.0,
        mold_persistent=True,
        rain_soon=True,
    )
    good = evaluate_room(base(**common, air_quality="good"))
    moderate = evaluate_room(base(**common, air_quality="moderate"))
    assert good.color == "yellow"
    assert moderate.color == "yellow"


def test_imminent_rain_never_weakens_2000_to_2000_point_1_co2_step():
    common = dict(
        indoor_temp=22.0,
        indoor_humidity=65.0,
        outdoor_temp=-8.0,
        outdoor_humidity=50.0,
        rain_soon=True,
        rain_minutes_until=13.5,
    )
    at = evaluate_room(base(**common, co2=2000.0))
    above = evaluate_room(base(**common, co2=2000.1))
    rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    assert rank[above.color] >= rank[at.color]


def test_imminent_rain_does_not_reintroduce_humidity_threshold_regression():
    common = dict(
        indoor_temp=22.0,
        target_temp=22.0,
        outdoor_temp=20.0,
        outdoor_humidity=50.0,
        co2=1100.0,
        outdoor_co2=900.0,
        air_quality="moderate",
        rain_soon=True,
        rain_minutes_until=8.0,
    )
    below = evaluate_room(base(**common, indoor_humidity=59.9))
    at = evaluate_room(base(**common, indoor_humidity=60.0))
    rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    assert rank[at.color] >= rank[below.color]


def test_24h_routine_bridge_keeps_co2_monotonic_with_rain_and_outdoor_co2():
    """1050 -> 1100 ppm must not weaken advice in the 24 h rain bridge."""
    common = dict(
        indoor_temp=21.0,
        target_temp=21.0,
        indoor_humidity=50.0,
        outdoor_temp=20.0,
        outdoor_humidity=50.0,
        outdoor_co2=950.0,
        hours_since_airing=25.0,
        rain_now=True,
    )
    rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    values = [999.0, 1000.0, 1050.0, 1100.0, 1399.0, 1400.0, 2000.1]
    results = [evaluate_room(base(**common, co2=value)) for value in values]
    for earlier, later in zip(results, results[1:]):
        assert rank[later.color] >= rank[earlier.color], (
            earlier.mode, earlier.color, later.mode, later.color
        )


def test_24h_routine_bridge_does_not_override_existing_temperature_conflict():
    """The routine compatibility bridge applies only when routine was the sole prior need."""
    common = dict(
        indoor_temp=26.13,
        indoor_humidity=51.67,
        outdoor_temp=-1.04,
        outdoor_humidity=46.57,
        target_temp=21.05,
        outdoor_co2=950.0,
        hours_since_airing=25.0,
        rain_minutes_until=15.0,
    )
    rank = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    results = [evaluate_room(base(**common, co2=value)) for value in (999.0, 1000.0, 1050.0, 1100.0)]
    assert all(rank[later.color] >= rank[earlier.color] for earlier, later in zip(results, results[1:]))


def test_room_view_uses_strongest_display_need_during_multi_need_airing():
    """A mild CO2 hysteresis tie must not hide a much larger temperature need.

    This reproduces the ugly room-card transition where the open-window card
    could say green / "can close" while the actual ventilation decision was
    still keeping the window open for a large temperature deviation.  Once CO2
    left its hysteresis band, the temperature reason became visible and the
    card jumped to orange.  The room perspective now considers all active
    indoor needs and therefore stays consistent throughout the sequence.
    """
    common = dict(
        indoor_temp=16.88,
        target_temp=24.73,
        outdoor_temp=24.31,
        indoor_humidity=28.75,
        outdoor_humidity=25.34,
        hours_since_airing=2,
    )

    closed = evaluate_room(base(**common, co2=1200, window_open=False))
    assert closed.mode == "erwaermen"
    assert closed.decision_need == "temperature"
    assert closed.primary_need == "temperature"
    assert closed.room_status_color == "orange"
    assert closed.room_reason_args["need"] == "temperature"

    opened = evaluate_room(
        base(
            **common,
            co2=1200,
            window_open=True,
            open_minutes=1,
            previous_mode=closed.mode,
            previous_need=closed.decision_need,
        )
    )
    assert opened.mode == "weiter_lueften"
    assert opened.room_status_color == "orange"
    assert opened.room_recommendation_key == "keep_open"

    co2_dropped = evaluate_room(
        base(
            **common,
            co2=984,
            window_open=True,
            open_minutes=8,
            previous_mode=opened.mode,
            previous_need=opened.decision_need,
        )
    )
    assert co2_dropped.mode == "weiter_lueften"
    assert co2_dropped.room_status_color == "orange"
    assert co2_dropped.room_recommendation_key == "keep_open"


def test_temperature_airing_with_unreachable_target_ends_when_outdoor_help_is_exhausted():
    """24 -> 18 °C with 23 °C outdoors must not promise reaching 18 °C.

    Ventilation can only move the room toward outdoor temperature.  The running
    session should continue while there is a useful >=0.5 K gradient and finish
    before pretending that the configured 18 °C target itself can be reached.
    """
    running = evaluate_room(
        base(
            indoor_temp=24.0,
            target_temp=18.0,
            outdoor_temp=23.0,
            indoor_humidity=52.8,
            outdoor_humidity=49.0,
            co2=648,
            window_open=True,
            open_minutes=1,
            previous_mode="weiter_lueften",
            previous_need="temperature",
        )
    )
    assert running.mode == "weiter_lueften"
    assert running.reason_args["continue_cooling"] is True
    assert running.duration_key == "while_temperature_helps"

    finished = evaluate_room(
        base(
            indoor_temp=23.49,
            target_temp=18.0,
            outdoor_temp=23.0,
            indoor_humidity=52.8,
            outdoor_humidity=49.0,
            co2=648,
            window_open=True,
            open_minutes=10,
            previous_mode="weiter_lueften",
            previous_need="temperature",
        )
    )
    assert finished.mode == "lueftung_fertig"
    assert finished.room_recommendation_key == "can_close"

    closed = evaluate_room(
        base(
            indoor_temp=23.49,
            target_temp=18.0,
            outdoor_temp=23.0,
            indoor_humidity=52.8,
            outdoor_humidity=49.0,
            co2=648,
            window_open=False,
            previous_mode=finished.mode,
            previous_need=finished.decision_need,
        )
    )
    assert closed.recommendation_key != "open_now"
    assert closed.room_status_color == "green"
    assert closed.room_recommendation_key == "room_good"


def test_can_close_then_same_measurements_never_escalate_on_close_across_boundaries():
    """Closing after a real can-close state must not immediately ask to reopen.

    Exercise the exact boundaries most likely to flicker: temperature start /
    stop and useful-gradient bands, humidity 58/60/65 %, CO2 900/1000/1400/
    2000 ppm and the five-minute airing boundary.  This is deliberately a grid
    rather than a single hand-picked regression example.
    """
    checked = 0
    temperature_deltas = (0.19, 0.21, 0.59, 0.61, 0.99, 1.01, 2.99, 3.01)
    helpful_gradients = (0.49, 0.51, 0.69, 0.71)
    humidities = (57.9, 58.0, 59.9, 60.0, 64.9, 65.0)
    co2_values = (849, 850, 899, 900, 999, 1000, 1399, 1400, 2000, 2001)

    for sign in (-1, 1):
        for delta in temperature_deltas:
            target = 21.0
            ti = target + sign * delta
            for gradient in helpful_gradients:
                ta = ti - sign * gradient
                for humidity in humidities:
                    for co2 in co2_values:
                        opened = evaluate_room(
                            base(
                                indoor_temp=ti,
                                target_temp=target,
                                outdoor_temp=ta,
                                indoor_humidity=humidity,
                                outdoor_humidity=50.0,
                                co2=co2,
                                window_open=True,
                                open_minutes=5.01,
                                previous_mode="weiter_lueften",
                                previous_need="temperature",
                            )
                        )
                        if opened.room_recommendation_key != "can_close":
                            continue
                        checked += 1
                        closed = evaluate_room(
                            base(
                                indoor_temp=ti,
                                target_temp=target,
                                outdoor_temp=ta,
                                indoor_humidity=humidity,
                                outdoor_humidity=50.0,
                                co2=co2,
                                window_open=False,
                                previous_mode=opened.mode,
                                previous_need=opened.decision_need,
                            )
                        )
                        # The room-air perspective may deliberately allow a
                        # mild underlying ventilation opportunity (for example
                        # slightly elevated CO2) while still saying the room is
                        # fine.  What must never happen is the user-visible
                        # green "can close" state jumping to orange/red solely
                        # because the contact changed to closed.
                        assert closed.room_status_color not in {"orange", "red"}
                        if opened.recommendation_key == "can_close":
                            assert closed.recommendation_key != "open_now"

    assert checked > 100


def test_running_co2_session_controls_room_card_until_finish_ready():
    """Regression: 1440 -> 1399 must not make room view say can_close.

    This reproduces the real default-room-card case with 61.7 % RH. The normal
    engine already kept the explicit CO2 session alive; the inverted room view
    must now surface that same session instead of letting the mild humidity band
    render green / can_close.
    """
    common = dict(
        indoor_temp=22.0,
        target_temp=22.0,
        indoor_humidity=61.7,
        outdoor_temp=20.0,
        outdoor_humidity=50.0,
        co2_finish_target=850.0,
        co2_near_target=900.0,
    )

    started = evaluate_room(base(**common, co2=1440.0, window_open=False))
    assert started.room_status_color == "orange"
    assert started.room_recommendation_key == "room_need"

    minimum = evaluate_room(
        base(
            **common,
            co2=1399.0,
            window_open=True,
            open_minutes=1.0,
            previous_mode="co2_lueften",
            previous_need="co2_high",
            co2_airing_active=True,
            co2_minimum_airing_active=True,
        )
    )
    assert minimum.mode == "co2_mindestlueftung"
    assert minimum.recommendation_key == "keep_open"
    assert minimum.room_status_color == "orange"
    assert minimum.room_recommendation_key == "keep_open"
    assert minimum.room_reason_key == "co2_minimum_airing"
    assert minimum.primary_need == "co2_session"

    after_minimum = evaluate_room(
        base(
            **common,
            co2=1399.0,
            window_open=True,
            open_minutes=6.0,
            previous_mode="co2_mindestlueftung",
            previous_need="co2_high",
            co2_airing_active=True,
        )
    )
    assert after_minimum.mode == "weiter_lueften"
    assert after_minimum.recommendation_key == "keep_open"
    assert after_minimum.room_status_color == "orange"
    assert after_minimum.room_recommendation_key == "keep_open"
    assert after_minimum.room_reason_key == "continue_airing"


def test_running_co2_session_room_card_is_yellow_near_target_then_green_only_when_ready():
    common = dict(
        indoor_temp=22.0,
        target_temp=22.0,
        indoor_humidity=45.0,
        # Keep the outdoor situation genuinely neutral/helpful here. The
        # near-target CO2 session must not be ended merely because there is no
        # fresh indoor need, but a real outdoor drawback remains authoritative.
        outdoor_temp=22.0,
        outdoor_humidity=45.0,
        window_open=True,
        open_minutes=8.0,
        previous_mode="weiter_lueften",
        previous_need="co2_elevated",
        co2_airing_active=True,
        co2_finish_target=850.0,
        co2_near_target=900.0,
    )

    for ppm in (899.0, 880.0, 850.0, 840.0):
        near = evaluate_room(base(**common, co2=ppm, co2_finish_ready=False))
        assert near.mode == "co2_abwaegung"
        assert near.recommendation_key == "short_observation"
        assert near.room_status_color == "yellow"
        assert near.room_recommendation_key == "room_keep_brief"
        assert near.room_reason_key == "co2_tradeoff"
        assert near.primary_need == "co2_session"

    finished = evaluate_room(base(**common, co2=840.0, co2_finish_ready=True))
    assert finished.mode == "lueftung_fertig"
    assert finished.recommendation_key == "can_close"
    assert finished.room_status_color == "green"
    assert finished.room_recommendation_key == "can_close"
    assert finished.room_reason_key == "airing_finished"
    assert finished.primary_need == "co2_session"


def test_running_co2_session_room_card_fix_does_not_depend_on_humidity():
    for humidity in (45.0, 61.7, 63.0):
        result = evaluate_room(
            base(
                indoor_temp=22.0,
                target_temp=22.0,
                indoor_humidity=humidity,
                outdoor_temp=20.0,
                outdoor_humidity=50.0,
                co2=1100.0,
                window_open=True,
                open_minutes=7.0,
                previous_mode="co2_mindestlueftung",
                previous_need="co2_high",
                co2_airing_active=True,
                co2_finish_target=850.0,
                co2_near_target=900.0,
            )
        )
        assert result.mode == "weiter_lueften"
        assert result.recommendation_key == "keep_open"
        assert result.room_status_color == "orange"
        assert result.room_recommendation_key == "keep_open"
        assert result.room_reason_key == "continue_airing"


def test_running_co2_session_room_view_never_contradicts_keep_open():
    """Cross-view invariant: room card may not close while engine says keep open."""
    checked = 0
    for humidity in (35.0, 45.0, 55.0, 61.7, 63.0, 70.0):
        for outdoor_temp in (5.0, 15.0, 20.0, 22.0, 26.0, 35.0):
            for outdoor_humidity in (20.0, 40.0, 60.0, 90.0):
                for ppm in (840.0, 880.0, 899.0, 920.0, 999.0, 1100.0, 1250.0, 1399.0, 1600.0):
                    result = evaluate_room(
                        base(
                            indoor_temp=22.0,
                            target_temp=22.0,
                            indoor_humidity=humidity,
                            outdoor_temp=outdoor_temp,
                            outdoor_humidity=outdoor_humidity,
                            co2=ppm,
                            window_open=True,
                            open_minutes=7.0,
                            previous_mode="weiter_lueften",
                            previous_need="co2_elevated",
                            co2_airing_active=True,
                            co2_finish_target=850.0,
                            co2_near_target=900.0,
                            co2_finish_ready=False,
                        )
                    )
                    if result.recommendation_key == "keep_open":
                        checked += 1
                        assert result.room_recommendation_key != "can_close"
                        assert result.room_status_color != "green"

    assert checked > 100


def test_co2_finish_ready_never_overrides_independent_temperature_keep_open():
    """Finishing CO2 only removes CO2; an active cooling reason still wins."""
    result = evaluate_room(
        base(
            indoor_temp=26.0,
            target_temp=22.0,
            indoor_humidity=45.0,
            outdoor_temp=18.0,
            outdoor_humidity=45.0,
            co2=840.0,
            window_open=True,
            open_minutes=9.0,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
            co2_finish_ready=True,
        )
    )
    assert result.recommendation_key == "keep_open"
    assert result.mode != "lueftung_fertig"
    assert result.room_recommendation_key != "can_close"
    assert result.room_status_color != "green"


def test_co2_near_target_never_weakens_independent_humidity_keep_open():
    """Near-target CO2 may not downgrade a still useful humidity airing."""
    result = evaluate_room(
        base(
            indoor_temp=22.0,
            target_temp=22.0,
            indoor_humidity=70.0,
            outdoor_temp=20.0,
            outdoor_humidity=40.0,
            co2=899.0,
            window_open=True,
            open_minutes=9.0,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
            co2_finish_ready=False,
        )
    )
    assert result.recommendation_key == "keep_open"
    assert result.mode not in {"co2_abwaegung", "lueftung_fertig"}
    assert result.room_recommendation_key != "can_close"


def test_running_co2_session_without_current_measurement_is_never_finished():
    """Unavailable CO2 after the minimum phase is unknown, never target reached."""
    result = evaluate_room(
        base(
            indoor_temp=22.0,
            target_temp=22.0,
            indoor_humidity=45.0,
            outdoor_temp=22.0,
            outdoor_humidity=45.0,
            co2=None,
            window_open=True,
            open_minutes=8.0,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
            co2_finish_ready=False,
            co2_minimum_airing_active=False,
        )
    )
    assert result.mode == "co2_abwaegung"
    assert result.recommendation_key == "short_observation"
    assert result.reason_key == "co2_tradeoff"
    assert result.reason_args["caution"] == "measurement_unknown"
    assert result.room_status_color == "yellow"
    assert result.room_recommendation_key == "room_keep_brief"


def test_running_co2_session_missing_measurement_does_not_weaken_other_keep_open_reason():
    """If another reason still needs airing, missing CO2 leaves it authoritative."""
    result = evaluate_room(
        base(
            indoor_temp=26.0,
            target_temp=22.0,
            indoor_humidity=45.0,
            outdoor_temp=18.0,
            outdoor_humidity=45.0,
            co2=None,
            window_open=True,
            open_minutes=8.0,
            previous_mode="weiter_lueften",
            previous_need="co2_elevated",
            co2_airing_active=True,
            co2_finish_target=850.0,
            co2_near_target=900.0,
            co2_finish_ready=False,
        )
    )
    assert result.recommendation_key == "keep_open"
    assert result.mode != "lueftung_fertig"
    assert result.room_recommendation_key != "can_close"


def test_co2_finish_ready_with_1250_target_does_not_hide_same_urgency_temperature_need():
    """Even if CO2 still wins the merge, another green need must survive finish."""
    result = evaluate_room(
        base(
            indoor_temp=23.0,
            target_temp=22.0,
            indoor_humidity=45.0,
            outdoor_temp=18.0,
            outdoor_humidity=45.0,
            co2=1240.0,
            window_open=True,
            open_minutes=10.0,
            previous_mode="weiter_lueften",
            previous_need="co2_high",
            co2_airing_active=True,
            co2_finish_target=1250.0,
            co2_near_target=1300.0,
            co2_finish_ready=True,
        )
    )
    assert result.decision_need == "co2_elevated"
    assert result.mode != "lueftung_fertig"
    assert result.recommendation_key == "keep_open"
    assert result.room_recommendation_key != "can_close"

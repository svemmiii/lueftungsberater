"""Room-air actions keep their colour semantics after every decision overlay."""

from dataclasses import replace
from itertools import product

import pytest

from custom_components.lueftungsberater.engine import evaluate_room
from custom_components.lueftungsberater.models import RoomInput
from custom_components.lueftungsberater.localization import reason_text


def open_room(**changes):
    values = dict(
        indoor_temp=22.0,
        indoor_humidity=50.0,
        outdoor_temp=20.0,
        outdoor_humidity=50.0,
        target_temp=22.0,
        window_open=True,
        window_data_status="current",
        open_minutes=10.0,
    )
    return RoomInput(**(values | changes))


def reported_room(**changes):
    return open_room(**(dict(
        indoor_temp=22.8,
        indoor_humidity=66.7,
        outdoor_temp=11.5,
        outdoor_humidity=85.0,
        target_temp=23.0,
        co2=891.0,
        outdoor_co2=445.0,
        open_minutes=36.0,
        current_airing_qualified=True,
        hours_since_airing=12.48,
        surface_temp=23.0,
        humidity_disarmed=True,
        rain_minutes_until=12.329914666666667,
        air_quality="good",
    ) | changes))


def test_reported_quiet_humidity_can_close_without_claiming_good_measurements():
    result = evaluate_room(reported_room())

    assert result.decision_need == "none"
    assert result.active_reasons == ()
    assert result.primary_need == "humidity_observe"
    assert result.color == "orange"
    assert result.mode == "aussen_zu_kalt"
    assert result.recommendation_key == "better_close"
    assert result.reason_key == "outside_too_cold"
    # Green means close the window, NOT that the measured humidity is good.
    assert result.room_status_color == "green"
    assert result.room_recommendation_key == "better_close"
    assert result.room_reason_key == "humidity_observe_close"
    assert result.room_reason_args["closing_reason_key"] == result.reason_key
    assert result.room_reason_args["closing_reason_args"] == result.reason_args
    for language, needle in (("de", "Raumfeuchte"), ("en", "humidity"), ("tr", "nem")):
        explanation = reason_text(result.room_reason_key, result.room_reason_args, language)
        assert needle in explanation
        assert "66" in explanation or "66,7" in explanation
    assert result.duration_key == "not_needed"


@pytest.mark.parametrize(
    "changes,action,reason,native_color,room_color",
    [
        pytest.param(dict(indoor_humidity=70, outdoor_temp=22, outdoor_humidity=80),
                     "better_close", "humidity_wait", "orange", "green", id="wetter-outside"),
        pytest.param(dict(indoor_humidity=70, outdoor_temp=11, humidity_disarmed=True),
                     "better_close", "outside_too_cold", "orange", "green", id="cold-outside"),
        pytest.param(dict(indoor_humidity=70, outdoor_temp=30, humidity_disarmed=True),
                     "better_close", "outside_more_humid", "orange", "green", id="hot-humid-outside"),
        *[
            pytest.param(dict(indoor_humidity=70, humidity_disarmed=True, air_quality=quality),
                         action, reason, color, "green", id=f"outside-air-{quality}")
            for quality, action, reason, color in (
                ("moderate", "better_close", "air_quality_moderate", "orange"),
                ("poor", "better_close", "air_quality_poor", "orange"),
                ("very_poor", "close_now", "air_quality_very_poor", "red"),
            )
        ],
        pytest.param(dict(indoor_humidity=70, humidity_disarmed=True, weather_caution=True),
                     "better_close", "weather_caution", "orange", "green", id="weather-caution"),
        pytest.param(dict(indoor_humidity=70, humidity_disarmed=True, weather_danger=True),
                     "close_now", "weather_danger", "red", "green", id="unlocked-severe-weather"),
    ],
)
def test_closing_actions_use_green_but_keep_indoor_need_diagnostics(
    changes, action, reason, native_color, room_color,
):
    result = evaluate_room(open_room(**changes))

    assert result.safety_lock is False
    assert result.color == native_color
    assert result.recommendation_key == action
    assert result.room_recommendation_key == action
    assert result.reason_key == reason
    if result.primary_need == "humidity_observe":
        assert result.room_reason_key == "humidity_observe_close"
        assert result.room_reason_args["closing_reason_key"] == reason
        assert "70" in reason_text(result.room_reason_key, result.room_reason_args, "de")
    else:
        assert result.room_reason_key == reason
    # Closing is the visible action. The diagnostic/native suitability remains
    # independent and its explanation retains the actual outside hazard.
    assert result.room_status_color == room_color == "green"
    assert result.color == native_color


def test_ineffective_humidity_can_close_without_claiming_humidity_recovered():
    result = evaluate_room(open_room(
        indoor_humidity=70, outdoor_temp=21, outdoor_humidity=40,
        previous_mode="weiter_lueften", previous_need="humidity",
        humidity_session_exhausted=True, humidity_disarmed=True,
    ))
    assert result.recommendation_key == "can_close"
    assert result.reason_key == "humidity_exhausted"
    assert result.room_recommendation_key == "can_close"
    assert result.room_reason_key == "humidity_stalled"
    assert result.room_status_color == "green"  # no more window action
    assert result.active_reasons == ()
    assert result.room_reason_args["humidity"] == 70
    assert result.room_reason_key == "humidity_stalled"


def test_current_humidity_need_is_not_marked_finished():
    result = evaluate_room(reported_room(humidity_disarmed=False))

    assert "humidity_urgent" in result.active_reasons
    assert result.room_status_color == "yellow"
    assert result.room_recommendation_key == "room_keep_brief"


def test_closed_window_stays_green_with_high_humidity_diagnostic():
    result = evaluate_room(reported_room(window_open=False, open_minutes=None))

    assert result.room_status_color == "green"
    assert result.room_recommendation_key == "caution_keep_closed"
    assert result.reason_key == "outside_too_cold"
    assert result.room_reason_key == "humidity_observe_close"
    assert result.room_reason_args["closing_reason_key"] == "outside_too_cold"
    assert result.primary_need == "humidity_observe"


@pytest.mark.parametrize("co2,color,action", [
    (1300, "orange", "keep_open"),
    (880, "yellow", "room_keep_brief"),
    (800, "green", "can_close"),
])
def test_running_co2_session_preserves_continuation_and_finish(co2, color, action):
    result = evaluate_room(open_room(
        co2=co2, outdoor_temp=21, co2_airing_active=True,
        co2_session_strong_origin=True, co2_finish_ready=co2 == 800,
        co2_finish_target=850, co2_near_target=900,
        previous_need="co2_high", previous_mode="weiter_lueften",
    ))

    assert result.room_status_color == color
    assert result.room_recommendation_key == action


def test_missing_co2_does_not_become_a_successful_finished_measurement():
    result = evaluate_room(open_room(
        co2=None, co2_airing_active=True, co2_finish_target=850,
        co2_near_target=900, previous_need="co2_elevated", previous_mode="weiter_lueften",
    ))

    assert result.room_status_color == "green"
    assert result.room_recommendation_key == "better_close"
    assert result.room_reason_key == "co2_measurement_unknown_close"
    assert result.reason_key == "co2_measurement_unknown_close"


def test_missing_optional_window_contact_does_not_override_room_needs():
    normal = evaluate_room(reported_room(window_data_status="current"))
    missing = evaluate_room(reported_room(window_data_status="unavailable"))
    assert missing.room_status_color == normal.room_status_color
    assert missing.room_recommendation_key == normal.room_recommendation_key
    assert missing.room_reason_key == normal.room_reason_key
    assert missing.active_reasons == normal.active_reasons


@pytest.mark.parametrize("window_open,co2,humidity", product([False, True], [800, 2600], [50, 70]))
@pytest.mark.parametrize("danger", ["nina", "weather"])
def test_safety_lock_still_uses_native_red_even_with_quiet_session_memory(
    window_open, co2, humidity, danger,
):
    data = reported_room(window_open=window_open, co2=co2, indoor_humidity=humidity)
    if danger == "nina":
        data = replace(data, nina_status="danger", nina_reason_key="air_smoke_danger")
    else:
        data = replace(data, weather_danger=True, weather_hard_lock=True)
    result = evaluate_room(data)

    assert result.safety_lock is True
    # Both sensor views deliberately use the native decision during a hard lock.
    assert result.color == "red"
    assert result.recommendation_key == ("close_now" if window_open else "keep_closed")

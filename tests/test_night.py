from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.lueftungsberater.night import evaluate_night_ventilation

TZ = ZoneInfo("Europe/Berlin")
NOW = datetime(2026, 8, 24, 22, 0, tzinfo=TZ)


def forecast(*, temps, humidity=55, rain=False, wind=10, gust=20, start=NOW):
    rows = []
    for index, temp in enumerate(temps, start=1):
        rows.append(
            {
                "datetime": start + timedelta(hours=index),
                "temperature": temp,
                "humidity": humidity,
                "condition": "rainy" if rain and index == 3 else "clear-night",
                "precipitation_probability": 80 if rain and index == 3 else 0,
                "wind_speed": wind,
                "wind_gust_speed": gust,
            }
        )
    return rows


def test_night_airing_is_shown_when_room_is_above_personal_target_and_night_cools():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=21,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[20, 19, 18, 17, 17, 18, 19]),
    )
    assert result.status == "now"
    assert result.reason_key == "night_now"


def test_night_airing_line_is_hidden_when_there_is_no_meaningful_benefit():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=22.3,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(temps=[18, 17, 16, 16, 17, 18]),
    )
    assert result.status == "unavailable"
    assert result.reason_key is None


def test_night_airing_becomes_conditional_when_rain_is_forecast():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(temps=[20, 19, 18, 18, 19, 20], rain=True),
    )
    assert result.status == "conditional"
    assert result.reason_args["rain_risk"] is True


def test_night_airing_is_blocked_for_unsafe_forecast_wind():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(
            temps=[20, 19, 18, 18, 19, 20], wind=80, gust=110
        ),
    )
    assert result.status == "blocked"
    assert result.reason_key == "night_blocked"


def test_night_advice_is_hidden_before_the_configured_display_time():
    earlier = NOW.replace(hour=20)
    result = evaluate_night_ventilation(
        now=earlier,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        start_hour=22,
        hourly_forecast=forecast(temps=[20, 19, 18, 18], start=earlier),
    )
    assert result.status == "unavailable"


def test_night_display_time_is_configurable():
    earlier = NOW.replace(hour=20)
    result = evaluate_night_ventilation(
        now=earlier,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=21,
        outdoor_humidity=50,
        start_hour=20,
        hourly_forecast=forecast(temps=[20, 19, 18, 18], start=earlier),
    )
    assert result.status == "now"


def test_night_advice_can_recommend_waiting_until_later():
    # At 22:00 the coming hours are still too warm; from around 01:00 onward
    # there is a sustained cooling window.
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(temps=[27, 26, 20, 19, 18, 18, 19]),
    )
    assert result.status == "later"
    assert result.reason_key == "night_later"
    assert result.reason_args["start_time"].startswith("2026-08-25T01:00")


def test_night_advice_does_not_say_now_when_current_outdoor_air_is_still_too_warm():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=27,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[27, 26, 20, 19, 18, 18, 19]),
    )
    assert result.status == "later"
    assert result.reason_key == "night_later"
    assert result.reason_args["start_time"].startswith("2026-08-25T01:00")


def test_high_co2_alone_does_not_create_an_all_night_instruction():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=22,
        indoor_humidity=50,
        target_temp=22,
        indoor_co2=2500,
        hourly_forecast=forecast(temps=[20, 19, 18, 18, 19]),
    )
    # The normal main advice handles the current CO2 problem; night planning
    # must not pretend it can predict occupancy for the whole night.
    assert result.status == "unavailable"


def test_unusually_very_poor_air_blocks_long_night_opening_but_typical_pollution_is_context():
    episode = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        air_quality="very_poor",
        air_quality_unusual=True,
        air_quality_trend="rising",
        hourly_forecast=forecast(temps=[20, 19, 18, 18, 19]),
    )
    typical = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        air_quality="very_poor",
        air_quality_typical=True,
        air_quality_unusual=False,
        air_quality_trend="stable",
        hourly_forecast=forecast(temps=[20, 19, 18, 18, 19]),
    )
    assert episode.status == "blocked"
    assert typical.status == "conditional"

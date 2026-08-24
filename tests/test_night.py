from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.lueftungsberater.night import evaluate_night_ventilation

TZ = ZoneInfo("Europe/Berlin")
NOW = datetime(2026, 8, 24, 22, 0, tzinfo=TZ)


def forecast(*, temps, humidity=55, rain=False, wind=10, gust=20):
    rows = []
    for index, temp in enumerate(temps, start=1):
        rows.append(
            {
                "datetime": NOW + timedelta(hours=index),
                "temperature": temp,
                "humidity": humidity,
                "condition": "rainy" if rain and index == 3 else "clear-night",
                "precipitation_probability": 80 if rain and index == 3 else 0,
                "wind_speed": wind,
                "wind_gust_speed": gust,
            }
        )
    return rows


def test_night_airing_recommended_when_room_is_above_personal_target_and_night_cools():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(temps=[20, 19, 18, 17, 17, 18, 19]),
    )
    assert result.status == "recommended"
    assert result.reason_key == "night_recommended"


def test_night_airing_not_needed_when_personal_target_is_already_reached():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=22.3,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(temps=[18, 17, 16, 16, 17, 18]),
    )
    assert result.status == "not_recommended"
    assert result.reason_key == "night_target_already_ok"


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


def test_night_airing_rejects_strong_forecast_wind():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(
            temps=[20, 19, 18, 18, 19, 20], wind=50, gust=70
        ),
    )
    assert result.status == "not_recommended"
    assert result.reason_key == "night_strong_wind"


def test_night_advice_is_hidden_outside_evening_window():
    midday = NOW.replace(hour=14)
    result = evaluate_night_ventilation(
        now=midday,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        hourly_forecast=forecast(temps=[20, 19, 18, 18]),
    )
    assert result.status == "unavailable"

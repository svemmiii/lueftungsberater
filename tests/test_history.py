"""Tests for the bounded per-room history."""
from types import SimpleNamespace

from custom_components.lueftungsberater.history import _sample


def test_history_sample_keeps_room_measurements_but_not_rendered_text():
    snapshot = SimpleNamespace(
        result=SimpleNamespace(
            recommendation_key="open_now",
            mode="co2_lueften",
            safety_lock=False,
            color="green",
            room_status_color="yellow",
            primary_need="co2",
            indoor_absolute_humidity=10.5,
            outdoor_absolute_humidity=8.2,
            surface_relative_humidity=67.0,
            mold_risk=False,
            mold_persistent=False,
            mold_current_critical_minutes=0,
            mold_critical_minutes_24h=0,
        ),
        values={
            "temperature_inside": 23.0,
            "target_temperature": 21.0,
            "humidity_inside": 55.0,
            "co2_ppm": 1200,
            "outdoor_co2_ppm": None,
            "co2_data_status": "current",
            "surface_temperature": 20.0,
            "window_open": False,
            "open_minutes": None,
            "hours_since_last_airing": 4.0,
            "air_quality_baseline_value": None,
            "air_quality_typical": None,
            "air_quality_unusual": False,
            "air_quality_trend": "unknown",
            "night_ventilation_status": "unavailable",
        },
        weather=SimpleNamespace(
            temperature=15.0,
            humidity=60.0,
            air_quality_index="good",
            air_quality_pollutant="pm25",
            air_quality_value=4.0,
            air_quality_values={"pm25": 4.0},
            wind_speed_kmh=7.0,
            wind_gust_kmh=12.0,
            rain_minutes_until=None,
        ),
        warnings=SimpleNamespace(
            official_close_instruction=False,
            warning_notice_kind=None,
        ),
    )
    from datetime import UTC, datetime

    item = _sample(snapshot, datetime(2026, 8, 26, tzinfo=UTC))
    assert item["co2_ppm"] == 1200
    assert item["temperature_inside"] == 23.0
    assert item["air_quality_values"] == {"pm25": 4.0}
    assert item["recommendation"] == "open_now"
    assert "reason" not in item
    assert "localized_texts" not in item

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from custom_components.lueftungsberater.night import (
    NightAdvice,
    evaluate_night_ventilation,
    stabilize_night_advice,
    display_interval,
)

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


def test_night_advice_stops_at_configured_end_time():
    after_end = NOW.replace(hour=8)
    result = evaluate_night_ventilation(
        now=after_end,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=18,
        outdoor_humidity=50,
        start_hour=22,
        end_minute=7 * 60,
        hourly_forecast=forecast(temps=[18, 17, 16, 16], start=after_end),
    )
    assert result.status == "unavailable"


def test_night_advice_is_hidden_exactly_at_configured_end_time():
    exact_end = NOW.replace(hour=7) + timedelta(days=1)
    result = evaluate_night_ventilation(
        now=exact_end,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=18,
        outdoor_humidity=50,
        start_hour=22,
        end_minute=7 * 60,
        hourly_forecast=forecast(temps=[18, 17, 16, 16], start=exact_end),
    )
    assert result.status == "unavailable"


def test_night_window_can_use_shift_worker_hours():
    morning = NOW.replace(hour=8)
    result = evaluate_night_ventilation(
        now=morning,
        indoor_temp=26,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=18,
        outdoor_humidity=50,
        start_hour=2,
        end_minute=10 * 60,
        hourly_forecast=forecast(temps=[18, 17, 16, 16], start=morning),
    )
    assert result.status == "now"


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


def test_night_hint_becomes_short_only_when_temperature_delta_exceeds_nine_kelvin():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=15,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[15, 15, 15, 15]),
    )
    assert result.status == "short_only"
    assert result.reason_key == "night_short_only"
    assert result.reason_args["temperature_limit_direction"] == "cold"


def test_currently_good_cooling_but_forecast_turns_too_cold_shows_short_only():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=23.7,
        indoor_humidity=57.4,
        target_temp=22,
        outdoor_temp=15.5,
        outdoor_humidity=68,
        hourly_forecast=forecast(temps=[15.0, 14.0, 13.5, 13.0]),
    )
    assert result.status == "short_only"
    assert result.reason_key == "night_short_only"
    assert result.reason_args["temperature_limit_direction"] == "cold"
    assert result.reason_args["limit_time"].startswith("2026-08-25T00:00")


def test_warm_night_without_cooling_window_is_explicitly_not_recommended():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=25.2,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[25.0, 24.8, 24.7, 24.6]),
    )
    assert result.status == "not_recommended"
    assert result.reason_key == "night_not_recommended"
    assert result.reason_args["thermal_need"] is True
    assert result.reason_args["has_helpful_forecast"] is False


def test_humidity_only_can_be_short_only_when_dry_air_is_too_warm_for_long_opening():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=20,
        indoor_humidity=65,
        target_temp=21,
        outdoor_temp=30,
        outdoor_humidity=20,
        hourly_forecast=forecast(temps=[30, 30, 29.5, 29], humidity=20),
    )
    assert result.status == "short_only"
    assert result.reason_key == "night_short_only"
    assert result.reason_args["temperature_limit_direction"] == "warm"


def test_no_room_need_still_hides_night_card_even_with_extreme_forecast():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=22.2,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=10,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[10, 9, 8, 8]),
    )
    assert result.status == "unavailable"
    assert result.reason_key is None


def test_night_hint_accepts_exactly_nine_kelvin_delta():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=16,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[16, 16, 16, 16]),
    )
    assert result.status == "now"


def test_night_forecast_uses_one_hour_internal_buffer_without_extending_display_end():
    now = datetime(2026, 8, 25, 4, 50, tzinfo=TZ)
    rows = [
        {
            "datetime": datetime(2026, 8, 25, hour, 0, tzinfo=TZ),
            "temperature": 20,
            "humidity": 50,
            "condition": "clear-night",
            "wind_speed": 10,
            "wind_gust_speed": 20,
        }
        for hour in (5, 6, 7)
    ]
    result = evaluate_night_ventilation(
        now=now,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=20,
        outdoor_humidity=50,
        start_minute=22 * 60,
        end_minute=6 * 60,
        hourly_forecast=rows,
    )
    assert result.status == "now"
    assert result.reason_args["end_time"].startswith("2026-08-25T06:00")


def test_internal_buffer_weather_after_display_end_does_not_block_visible_window():
    now = datetime(2026, 8, 25, 4, 30, tzinfo=TZ)
    rows = [
        {
            "datetime": datetime(2026, 8, 25, 5, 0, tzinfo=TZ),
            "temperature": 18,
            "humidity": 50,
            "condition": "clear-night",
            "wind_speed": 10,
            "wind_gust_speed": 20,
        },
        {
            "datetime": datetime(2026, 8, 25, 6, 0, tzinfo=TZ),
            "temperature": 18,
            "humidity": 50,
            "condition": "clear-night",
            "wind_speed": 10,
            "wind_gust_speed": 20,
        },
        {
            "datetime": datetime(2026, 8, 25, 7, 0, tzinfo=TZ),
            "temperature": 18,
            "humidity": 95,
            "condition": "rainy",
            "precipitation_probability": 100,
            "wind_speed": 80,
            "wind_gust_speed": 110,
        },
    ]
    result = evaluate_night_ventilation(
        now=now,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=19,
        outdoor_humidity=50,
        start_minute=22 * 60,
        end_minute=6 * 60,
        hourly_forecast=rows,
    )
    assert result.status == "now"
    assert result.reason_args["end_time"].startswith("2026-08-25T06:00")
    assert result.reason_args["forecast_max_wind_level"] == 0
    assert result.reason_args["forecast_rain_risk"] is False


def test_buffer_only_help_after_display_end_is_not_reported_as_visible_forecast_help():
    now = datetime(2026, 8, 25, 4, 30, tzinfo=TZ)
    rows = [
        {
            "datetime": datetime(2026, 8, 25, 5, 0, tzinfo=TZ),
            "temperature": 26,
            "humidity": 50,
            "condition": "clear-night",
            "wind_speed": 10,
            "wind_gust_speed": 20,
        },
        {
            "datetime": datetime(2026, 8, 25, 6, 0, tzinfo=TZ),
            "temperature": 18,
            "humidity": 50,
            "condition": "clear-night",
            "wind_speed": 10,
            "wind_gust_speed": 20,
        },
        {
            "datetime": datetime(2026, 8, 25, 7, 0, tzinfo=TZ),
            "temperature": 18,
            "humidity": 50,
            "condition": "rainy",
            "precipitation_probability": 100,
            "wind_speed": 80,
            "wind_gust_speed": 110,
        },
    ]
    result = evaluate_night_ventilation(
        now=now,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=26,
        outdoor_humidity=50,
        start_minute=22 * 60,
        end_minute=6 * 60,
        hourly_forecast=rows,
    )
    assert result.status == "not_recommended"
    assert result.reason_args["has_helpful_forecast"] is False
    assert result.reason_args["forecast_max_wind_level"] == 0
    assert result.reason_args["forecast_rain_risk"] is False


def test_final_hour_holds_last_reliable_night_advice_when_forecast_thins_out():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice(
        "now",
        "night_now",
        {"start_time": datetime(2026, 8, 24, 23, 0, tzinfo=TZ).isoformat()},
    )
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=NightAdvice(),
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "now"
    assert remembered is previous


def test_final_hour_hard_safety_overrides_but_does_not_replace_base_plan():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice("now", "night_now", {"start_time": NOW.isoformat()})
    safety = NightAdvice("blocked", "night_blocked", {}, safety_block=True)
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=safety,
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "blocked"
    assert remembered is previous

    # A late all-clear with no trustworthy new forecast falls back to the old
    # plan instead of inventing a brand-new decision.
    chosen_after_clear, remembered_after_clear = stabilize_night_advice(
        now=now + timedelta(minutes=10),
        interval_end=end,
        raw=NightAdvice(),
        previous=remembered,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen_after_clear.status == "now"
    assert remembered_after_clear is previous


def test_current_hard_wind_block_does_not_replace_final_hour_base_plan():
    now = datetime(2026, 8, 25, 5, 10, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice(
        "now",
        "night_now",
        {"end_time": end.isoformat()},
    )
    raw = evaluate_night_ventilation(
        now=now,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=19,
        outdoor_humidity=50,
        wind_speed_kmh=80,
        wind_gust_kmh=110,
        start_minute=22 * 60,
        end_minute=6 * 60,
        hourly_forecast=[
            {"datetime": datetime(2026, 8, 25, 5, 30, tzinfo=TZ), "temperature": 18, "humidity": 50, "wind_speed": 10},
            {"datetime": datetime(2026, 8, 25, 6, 0, tzinfo=TZ), "temperature": 18, "humidity": 50, "wind_speed": 10},
            {"datetime": datetime(2026, 8, 25, 7, 0, tzinfo=TZ), "temperature": 18, "humidity": 50, "wind_speed": 10},
        ],
    )
    assert raw.status == "blocked"
    assert raw.safety_block is True

    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=raw,
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "blocked"
    assert remembered is previous


def test_current_unusual_very_poor_air_does_not_replace_final_hour_base_plan():
    now = datetime(2026, 8, 25, 5, 10, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice("now", "night_now", {"end_time": end.isoformat()})
    raw = evaluate_night_ventilation(
        now=now,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=19,
        outdoor_humidity=50,
        air_quality="very_poor",
        air_quality_unusual=True,
        start_minute=22 * 60,
        end_minute=6 * 60,
        hourly_forecast=[
            {"datetime": datetime(2026, 8, 25, 5, 30, tzinfo=TZ), "temperature": 18, "humidity": 50},
            {"datetime": datetime(2026, 8, 25, 6, 0, tzinfo=TZ), "temperature": 18, "humidity": 50},
            {"datetime": datetime(2026, 8, 25, 7, 0, tzinfo=TZ), "temperature": 18, "humidity": 50},
        ],
    )
    assert raw.status == "blocked"
    assert raw.reason_key == "night_air_too_bad"
    assert raw.safety_block is True

    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=raw,
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "blocked"
    assert remembered is previous


def test_final_hour_does_not_create_a_new_night_plan_from_scratch():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=NightAdvice("now", "night_now", {}),
        previous=None,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "unavailable"
    assert remembered is None


def test_final_hour_may_become_more_cautious():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice("now", "night_now", {})
    raw = NightAdvice("conditional", "night_now_conditional", {"rain_risk": True})
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=raw,
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "conditional"
    assert remembered is not None and remembered.status == "conditional"


def test_worse_outdoor_co2_makes_long_night_opening_conditional():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=21,
        outdoor_humidity=50,
        indoor_co2=800,
        outdoor_co2=1200,
        hourly_forecast=forecast(temps=[20, 19, 18, 18, 19, 20]),
    )
    assert result.status == "conditional"
    assert result.reason_args["outdoor_co2_disadvantage"] is True


def test_spring_dst_nonexistent_0230_start_normalizes_forward():
    now = datetime(2026, 3, 29, 3, 45, tzinfo=TZ)
    interval = display_interval(now, 2 * 60 + 30, 4 * 60 + 30)
    assert interval is not None
    start, end = interval
    assert (start.hour, start.minute) == (3, 30)
    assert (end.hour, end.minute) == (4, 30)


def test_autumn_dst_ambiguous_bound_uses_first_start_and_second_end():
    first_0240 = datetime(2026, 10, 25, 2, 40, tzinfo=TZ, fold=0)
    interval = display_interval(first_0240, 2 * 60 + 30, 2 * 60 + 45)
    assert interval is not None
    start, end = interval
    assert start.fold == 0
    assert end.fold == 1


def test_autumn_dst_interval_remains_active_across_repeated_hour():
    """02:30 fold=0 -> 02:45 fold=1 must include the whole repeated-hour span."""
    first_0250 = datetime(2026, 10, 25, 2, 50, tzinfo=TZ, fold=0)
    interval = display_interval(first_0250, 2 * 60 + 30, 2 * 60 + 45)
    assert interval is not None
    start, end = interval
    assert start.fold == 0
    assert end.fold == 1
    assert start.astimezone(timezone.utc) < first_0250.astimezone(timezone.utc) < end.astimezone(timezone.utc)


def test_temperature_short_only_never_overrides_hard_weather_danger():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=15,
        outdoor_humidity=50,
        weather_danger=True,
        hourly_forecast=forecast(temps=[15, 15, 15, 15]),
    )
    assert result.status == "blocked"
    assert result.reason_key == "night_blocked"
    assert result.safety_block is True


def test_final_hour_may_downgrade_now_to_short_only():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice("now", "night_now", {})
    raw = NightAdvice("short_only", "night_short_only", {"thermal_need": True})
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=raw,
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "short_only"
    assert remembered is not None and remembered.status == "short_only"


def test_final_hour_may_downgrade_short_only_to_not_recommended():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice("short_only", "night_short_only", {})
    raw = NightAdvice(
        "not_recommended",
        "night_not_recommended",
        {"thermal_need": True},
    )
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=raw,
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "not_recommended"
    assert remembered is not None and remembered.status == "not_recommended"


def test_night_cooling_requires_about_point_seven_kelvin_advantage():
    enough = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=24.3,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[24.3, 24.3, 24.3, 24.3], humidity=50),
    )
    not_enough = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=24.31,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[24.31, 24.31, 24.31, 24.31], humidity=50),
    )
    assert enough.status == "now"
    assert not_enough.status == "not_recommended"


def test_humidity_only_long_opening_uses_target_guard_before_nine_kelvin_limit():
    at_limit = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=20,
        indoor_humidity=70,
        target_temp=21,
        outdoor_temp=29,
        outdoor_humidity=15,
        hourly_forecast=forecast(temps=[29, 29, 29, 29], humidity=15),
    )
    over_limit = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=20,
        indoor_humidity=70,
        target_temp=21,
        outdoor_temp=29.01,
        outdoor_humidity=15,
        hourly_forecast=forecast(temps=[29.01, 29.01, 29.01, 29.01], humidity=15),
    )
    assert at_limit.status == "short_only"
    assert over_limit.status == "short_only"


def test_final_hour_does_not_resurrect_plan_whose_own_end_time_passed():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    interval_end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice(
        "later",
        "night_later",
        {
            "start_time": datetime(2026, 8, 24, 23, 0, tzinfo=TZ).isoformat(),
            "end_time": datetime(2026, 8, 25, 1, 0, tzinfo=TZ).isoformat(),
        },
    )
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=interval_end,
        raw=NightAdvice(),
        previous=previous,
        planning_need=True,
        current_delta_ok=True,
    )
    assert chosen.status == "unavailable"
    assert remembered is None


def test_current_wetter_air_does_not_become_night_now_just_because_future_is_dry():
    rows = forecast(temps=[20, 20, 20, 20], humidity=40)
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=65,
        target_temp=22,
        outdoor_temp=20,
        outdoor_humidity=100,
        hourly_forecast=rows,
        live_recommendation_key="better_close",
        live_mode="feuchte_warten",
    )
    assert result.status in {"later", "conditional"}
    assert result.status != "now"
    assert result.reason_args["current_humidity_disadvantage"] is True
    assert result.reason_args["forecast_humidity_advantage"] is True


def test_night_now_never_bridges_over_known_bad_forecast_point():
    now = datetime(2026, 8, 24, 22, 31, tzinfo=TZ)
    rows = [
        {"datetime": datetime(2026, 8, 24, 23, 0, tzinfo=TZ), "temperature": 26, "humidity": 50},
        {"datetime": datetime(2026, 8, 25, 0, 0, tzinfo=TZ), "temperature": 20, "humidity": 50},
        {"datetime": datetime(2026, 8, 25, 1, 0, tzinfo=TZ), "temperature": 19, "humidity": 50},
        {"datetime": datetime(2026, 8, 25, 2, 0, tzinfo=TZ), "temperature": 19, "humidity": 50},
    ]
    result = evaluate_night_ventilation(
        now=now,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=20,
        outdoor_humidity=50,
        hourly_forecast=rows,
        live_recommendation_key="open_now",
    )
    assert result.status == "later"
    assert result.reason_args["start_time"].startswith("2026-08-25T00:00")


def test_later_night_plan_does_not_tell_user_to_ignore_current_critical_co2_opening():
    rows = forecast(temps=[26, 26, 20, 19, 19])
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        indoor_co2=2500,
        outdoor_co2=400,
        outdoor_temp=26,
        outdoor_humidity=50,
        hourly_forecast=rows,
        live_recommendation_key="open_now",
        live_mode="co2_kritisch",
    )
    assert result.status == "later"
    assert result.reason_args["live_open_now"] is True


def test_short_only_keeps_soft_drawbacks_in_reason_args():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        indoor_co2=800,
        outdoor_co2=1200,
        outdoor_temp=15,
        outdoor_humidity=50,
        rain_now=True,
        wind_speed_kmh=55,
        air_quality="poor",
        weather_caution=True,
        hourly_forecast=forecast(temps=[15, 15, 15, 15], wind=55),
    )
    assert result.status == "short_only"
    assert result.reason_args["rain_risk"] is True
    assert result.reason_args["current_wind_level"] == 1
    assert result.reason_args["outdoor_co2_disadvantage"] is True
    assert result.reason_args["air_quality"] == "poor"


def test_alternating_temperature_and_humidity_benefits_do_not_form_one_long_segment():
    rows = [
        {"datetime": NOW + timedelta(hours=1), "temperature": 20, "humidity": 95},
        {"datetime": NOW + timedelta(hours=2), "temperature": 25, "humidity": 30},
        {"datetime": NOW + timedelta(hours=3), "temperature": 20, "humidity": 95},
        {"datetime": NOW + timedelta(hours=4), "temperature": 25, "humidity": 30},
    ]
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=65,
        target_temp=22,
        outdoor_temp=25,
        outdoor_humidity=65,
        hourly_forecast=rows,
    )
    assert result.status == "not_recommended"
    assert result.reason_args["no_contiguous_window"] is True


def test_single_wet_hour_cannot_be_hidden_by_dry_forecast_median():
    rows = [
        {"datetime": NOW + timedelta(hours=1), "temperature": 20, "humidity": 40},
        {"datetime": NOW + timedelta(hours=2), "temperature": 20, "humidity": 95},
        {"datetime": NOW + timedelta(hours=3), "temperature": 20, "humidity": 40},
    ]
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=65,
        target_temp=22,
        outdoor_temp=20,
        outdoor_humidity=40,
        hourly_forecast=rows,
    )
    assert result.status != "now"
    assert result.reason_args.get("no_contiguous_window") is True


def test_final_hour_can_keep_short_only_even_when_delta_exceeds_long_opening_guard():
    now = datetime(2026, 8, 25, 5, 20, tzinfo=TZ)
    end = datetime(2026, 8, 25, 6, 0, tzinfo=TZ)
    previous = NightAdvice(
        "now",
        "night_now",
        {"end_time": datetime(2026, 8, 25, 5, 55, tzinfo=TZ).isoformat()},
    )
    raw = NightAdvice(
        "short_only",
        "night_short_only",
        {"thermal_need": True, "end_time": end.isoformat()},
    )
    chosen, remembered = stabilize_night_advice(
        now=now,
        interval_end=end,
        raw=raw,
        previous=previous,
        planning_need=True,
        current_delta_ok=False,
    )
    assert chosen.status == "short_only"
    assert remembered is not None and remembered.status == "short_only"


def test_tiny_cooling_need_does_not_justify_many_hours_of_very_cold_air():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=24.4,
        outdoor_temp=16,
        outdoor_humidity=50,
        hourly_forecast=forecast(temps=[16, 16, 16, 16]),
    )
    assert result.status == "short_only"


def test_long_night_segment_must_remain_at_least_one_hour_after_end_clipping():
    now = datetime(2026, 8, 25, 4, 50, tzinfo=TZ)
    rows = [
        {"datetime": datetime(2026, 8, 25, 5, 50, tzinfo=TZ), "temperature": 20, "humidity": 50},
        {"datetime": datetime(2026, 8, 25, 6, 50, tzinfo=TZ), "temperature": 20, "humidity": 50},
    ]
    result = evaluate_night_ventilation(
        now=now,
        indoor_temp=25,
        indoor_humidity=50,
        target_temp=22,
        outdoor_temp=20,
        outdoor_humidity=50,
        start_minute=22 * 60,
        end_minute=6 * 60,
        hourly_forecast=rows,
    )
    assert result.status == "short_only"


def test_dry_but_much_hotter_air_does_not_override_active_cooling_need():
    result = evaluate_night_ventilation(
        now=NOW,
        indoor_temp=25,
        indoor_humidity=65,
        target_temp=22,
        outdoor_temp=35,
        outdoor_humidity=15,
        hourly_forecast=forecast(temps=[35, 35, 35, 35], humidity=15),
        live_recommendation_key="better_close",
    )
    assert result.status == "not_recommended"
    assert result.reason_args["current_thermal_disadvantage"] is True

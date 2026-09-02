from datetime import datetime, timedelta, timezone

from custom_components.lueftungsberater.co2_hysteresis import (
    CO2_AIRING_FINISH_STABLE,
    CO2_RECOMMEND_RELEASE_STABLE,
    Co2HysteresisState,
)

UTC = timezone.utc


def test_pending_recommendation_releases_only_after_three_stable_minutes_below_900():
    state = Co2HysteresisState()
    start = datetime(2026, 8, 26, 20, 0, tzinfo=UTC)
    first = state.evaluate(
        now=start, co2=890, window_open=False,
        previous_mode="co2_lueften", previous_need="co2_elevated",
    )
    almost = state.evaluate(
        now=start + CO2_RECOMMEND_RELEASE_STABLE - timedelta(seconds=1),
        co2=880, window_open=False,
        previous_mode="co2_lueften", previous_need="co2_elevated",
    )
    released = state.evaluate(
        now=start + CO2_RECOMMEND_RELEASE_STABLE,
        co2=880, window_open=False,
        previous_mode="co2_lueften", previous_need="co2_elevated",
    )
    assert first.pending_hold is True
    assert almost.pending_hold is True
    assert released.pending_hold is False


def test_pending_release_timer_resets_if_co2_returns_to_900():
    state = Co2HysteresisState()
    start = datetime(2026, 8, 26, 20, 0, tzinfo=UTC)
    state.evaluate(
        now=start, co2=880, window_open=False,
        previous_mode="co2_lueften", previous_need="co2_elevated",
    )
    reset = state.evaluate(
        now=start + timedelta(minutes=2), co2=905, window_open=False,
        previous_mode="co2_lueften", previous_need="co2_elevated",
    )
    restarted = state.evaluate(
        now=start + timedelta(minutes=2, seconds=1), co2=880, window_open=False,
        previous_mode="co2_lueften", previous_need="co2_elevated",
    )
    assert reset.pending_hold is False
    assert restarted.pending_hold is True
    assert restarted.next_check_seconds is not None
    assert restarted.next_check_seconds > 170


def test_open_co2_session_finishes_only_after_two_stable_minutes_at_850_or_less():
    state = Co2HysteresisState()
    start = datetime(2026, 8, 26, 20, 0, tzinfo=UTC)
    assert state.start_airing_session(target_ppm=850)
    first = state.evaluate(
        now=start, co2=850, window_open=True,
        previous_mode="weiter_lueften", previous_need="co2_elevated",
    )
    almost = state.evaluate(
        now=start + CO2_AIRING_FINISH_STABLE - timedelta(seconds=1),
        co2=845, window_open=True,
        previous_mode="co2_abwaegung", previous_need="co2_elevated",
    )
    ready = state.evaluate(
        now=start + CO2_AIRING_FINISH_STABLE,
        co2=845, window_open=True,
        previous_mode="co2_abwaegung", previous_need="co2_elevated",
    )
    assert first.airing_active and not first.finish_ready
    assert almost.airing_active and not almost.finish_ready
    assert ready.airing_active and ready.finish_ready


def test_finish_timer_resets_if_co2_rises_above_850():
    state = Co2HysteresisState()
    start = datetime(2026, 8, 26, 20, 0, tzinfo=UTC)
    assert state.start_airing_session(target_ppm=850)
    state.evaluate(
        now=start, co2=845, window_open=True,
        previous_mode="weiter_lueften", previous_need="co2_elevated",
    )
    reset = state.evaluate(
        now=start + timedelta(minutes=1), co2=860, window_open=True,
        previous_mode="co2_abwaegung", previous_need="co2_elevated",
    )
    restarted = state.evaluate(
        now=start + timedelta(minutes=1, seconds=1), co2=845, window_open=True,
        previous_mode="co2_abwaegung", previous_need="co2_elevated",
    )
    assert reset.airing_active and not reset.finish_ready
    assert restarted.airing_active and not restarted.finish_ready
    assert restarted.next_check_seconds is not None
    assert restarted.next_check_seconds > 110


def test_open_window_never_auto_starts_a_session_from_previous_mode():
    """Only the coordinator may start an explicit session from an engine target."""
    state = Co2HysteresisState()
    start = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)

    decision = state.evaluate(
        now=start,
        co2=2500,
        window_open=True,
        previous_mode="co2_kritisch",
        previous_need="co2_critical",
    )

    assert decision.airing_active is False
    assert state.session_active is False
    assert state.session_target_ppm is None


def test_hysteresis_timestamps_roundtrip_for_restart_memory():
    start = datetime(2026, 8, 27, 1, 2, 3, tzinfo=UTC)
    original = Co2HysteresisState(
        pending_below_since=start,
        finish_below_since=start + timedelta(minutes=1),
    )
    payload = original.as_dict()

    restored = Co2HysteresisState()
    restored.restore(
        pending_below_since=datetime.fromisoformat(payload["pending_below_since"]),
        finish_below_since=datetime.fromisoformat(payload["finish_below_since"]),
    )

    assert restored.pending_below_since == original.pending_below_since
    assert restored.finish_below_since == original.finish_below_since


def test_minimum_co2_airing_runs_five_minutes_and_then_releases():
    from custom_components.lueftungsberater.co2_hysteresis import (
        CO2_MINIMUM_AIRING,
        Co2MinimumAiringState,
    )

    start = datetime(2026, 8, 27, 18, 0, tzinfo=UTC)
    context = {
        "temperature": 1,
        "outdoor_temp": 28.0,
        "temperature_direction": "hot",
        "humidity": 2,
        "outdoor_absolute_humidity": 14.0,
        "air_quality": 0,
        "outdoor_co2": 0,
        "nina_caution": False,
        "weather_caution": False,
        "rain": False,
    }
    state = Co2MinimumAiringState()
    assert state.start(started_at=start, cautious=False, baseline_context=context)

    active = state.evaluate(
        now=start + timedelta(minutes=2),
        window_open=True,
        current_context=context,
        safety_lock=False,
    )
    released = state.evaluate(
        now=start + CO2_MINIMUM_AIRING,
        window_open=True,
        current_context=context,
        safety_lock=False,
    )

    assert active.active is True
    assert 170 <= active.next_check_seconds <= 190
    assert released.active is False
    assert state.completed_for_open_window is True


def test_minimum_co2_airing_keeps_already_known_bad_outdoor_conditions():
    from custom_components.lueftungsberater.co2_hysteresis import Co2MinimumAiringState

    start = datetime(2026, 8, 27, 18, 0, tzinfo=UTC)
    context = {
        "temperature": 2,
        "outdoor_temp": 33.0,
        "temperature_direction": "hot",
        "humidity": 3,
        "outdoor_absolute_humidity": 16.0,
        "air_quality": 0,
        "outdoor_co2": 0,
        "nina_caution": False,
        "weather_caution": False,
        "rain": False,
    }
    state = Co2MinimumAiringState()
    state.start(started_at=start, cautious=True, baseline_context=context)
    decision = state.evaluate(
        now=start + timedelta(minutes=2),
        window_open=True,
        current_context=dict(context),
        safety_lock=False,
    )
    assert decision.active is True
    assert decision.cautious is True


def test_minimum_co2_airing_aborts_for_new_outdoor_warning():
    from custom_components.lueftungsberater.co2_hysteresis import Co2MinimumAiringState

    start = datetime(2026, 8, 27, 18, 0, tzinfo=UTC)
    context = {
        "temperature": 0,
        "outdoor_temp": 21.0,
        "temperature_direction": "neutral",
        "humidity": 0,
        "outdoor_absolute_humidity": 10.0,
        "air_quality": 0,
        "outdoor_co2": 0,
        "nina_caution": False,
        "weather_caution": False,
        "rain": False,
    }
    state = Co2MinimumAiringState()
    state.start(started_at=start, cautious=False, baseline_context=context)
    worsened = dict(context, weather_caution=True)
    decision = state.evaluate(
        now=start + timedelta(minutes=1),
        window_open=True,
        current_context=worsened,
        safety_lock=False,
    )
    assert decision.active is False
    assert decision.aborted_for_outdoor_worsening is True


def test_minimum_co2_airing_aborts_when_a_new_imminent_weather_forecast_appears():
    from custom_components.lueftungsberater.co2_hysteresis import Co2MinimumAiringState

    start = datetime(2026, 8, 31, 16, 0, tzinfo=UTC)
    context = {
        "temperature": 0,
        "outdoor_temp": 21.0,
        "temperature_direction": "neutral",
        "humidity": 0,
        "outdoor_absolute_humidity": 10.0,
        "air_quality": 0,
        "outdoor_co2": 0,
        "nina_caution": False,
        "weather_caution": False,
        "weather_forecast": False,
        "rain": False,
    }
    state = Co2MinimumAiringState()
    state.start(started_at=start, cautious=False, baseline_context=context)
    decision = state.evaluate(
        now=start + timedelta(minutes=1),
        window_open=True,
        current_context=dict(context, weather_forecast=True),
        safety_lock=False,
    )
    assert decision.active is False
    assert decision.aborted_for_outdoor_worsening is True


def test_minimum_co2_airing_hard_safety_lock_always_wins():
    from custom_components.lueftungsberater.co2_hysteresis import Co2MinimumAiringState

    start = datetime(2026, 8, 27, 18, 0, tzinfo=UTC)
    context = {
        "temperature": 0,
        "outdoor_temp": 21.0,
        "temperature_direction": "neutral",
        "humidity": 0,
        "outdoor_absolute_humidity": 10.0,
        "air_quality": 0,
        "outdoor_co2": 0,
        "nina_caution": False,
        "weather_caution": False,
        "rain": False,
    }
    state = Co2MinimumAiringState()
    state.start(started_at=start, cautious=False, baseline_context=context)
    decision = state.evaluate(
        now=start + timedelta(seconds=30),
        window_open=True,
        current_context=context,
        safety_lock=True,
    )
    assert decision.active is False


def test_minimum_co2_airing_does_not_restart_until_window_was_closed():
    from custom_components.lueftungsberater.co2_hysteresis import (
        CO2_MINIMUM_AIRING,
        Co2MinimumAiringState,
    )

    start = datetime(2026, 8, 27, 18, 0, tzinfo=UTC)
    context = {
        "temperature": 0,
        "outdoor_temp": 21.0,
        "temperature_direction": "neutral",
        "humidity": 0,
        "outdoor_absolute_humidity": 10.0,
        "air_quality": 0,
        "outdoor_co2": 0,
        "nina_caution": False,
        "weather_caution": False,
        "rain": False,
    }
    state = Co2MinimumAiringState()
    state.start(started_at=start, cautious=False, baseline_context=context)
    state.evaluate(
        now=start + CO2_MINIMUM_AIRING,
        window_open=True,
        current_context=context,
        safety_lock=False,
    )
    assert state.start(started_at=start + timedelta(minutes=6), cautious=False, baseline_context=context) is False
    state.evaluate(
        now=start + timedelta(minutes=6),
        window_open=False,
        current_context=context,
        safety_lock=False,
    )
    assert state.start(started_at=start + timedelta(minutes=7), cautious=False, baseline_context=context) is True


def test_dynamic_co2_session_targets_follow_the_decision_band():
    from custom_components.lueftungsberater.co2_hysteresis import co2_session_target

    assert co2_session_target(
        co2=1180, primary_need="co2_elevated", mode="co2_lueften"
    ) == 850
    assert co2_session_target(
        co2=1450, primary_need="co2_high", mode="co2_abwaegung"
    ) == 1250
    assert co2_session_target(
        co2=1800, primary_need="co2_high", mode="co2_lueften_mit_nachteil"
    ) == 1550
    assert co2_session_target(
        co2=2200, primary_need="co2_critical", mode="co2_kritisch_vorsicht"
    ) == 1850


def test_explicit_co2_session_survives_mode_change_until_dynamic_target_is_stable():
    state = Co2HysteresisState()
    start = datetime(2026, 8, 27, 20, 0, tzinfo=UTC)
    assert state.start_airing_session(target_ppm=1250)

    # Regression for the real 1400 -> 1399 ppm case: the card must not forget
    # the open CO2 session just because the displayed need/mode changed.
    still_open = state.evaluate(
        now=start,
        co2=1390,
        window_open=True,
        previous_mode="co2_mindestlueftung",
        previous_need="humidity",
    )
    assert still_open.airing_active is True
    assert still_open.finish_ready is False
    assert still_open.finish_target_ppm == 1250
    assert still_open.near_target_ppm == 1300

    first_below = state.evaluate(
        now=start + timedelta(minutes=1),
        co2=1240,
        window_open=True,
        previous_mode="co2_abwaegung",
        previous_need="co2_elevated",
    )
    almost = state.evaluate(
        now=start + timedelta(minutes=2, seconds=59),
        co2=1235,
        window_open=True,
        previous_mode="co2_abwaegung",
        previous_need="co2_elevated",
    )
    ready = state.evaluate(
        now=start + timedelta(minutes=3),
        co2=1235,
        window_open=True,
        previous_mode="co2_abwaegung",
        previous_need="co2_elevated",
    )
    assert first_below.airing_active and not first_below.finish_ready
    assert almost.airing_active and not almost.finish_ready
    assert ready.airing_active and ready.finish_ready


def test_explicit_co2_session_target_roundtrips_for_restart_memory():
    start = datetime(2026, 8, 27, 20, 0, tzinfo=UTC)
    original = Co2HysteresisState(
        finish_below_since=start,
        session_active=True,
        session_target_ppm=1250,
    )
    payload = original.as_dict()
    restored = Co2HysteresisState()
    restored.restore(
        pending_below_since=None,
        finish_below_since=datetime.fromisoformat(payload["finish_below_since"]),
        session_active=payload["session_active"],
        session_target_ppm=payload["session_target_ppm"],
        completed_for_open_window=payload["completed_for_open_window"],
    )
    assert restored.session_active is True
    assert restored.session_target_ppm == 1250
    assert restored.finish_below_since == start


def test_completed_1400_session_blocks_retrigger_until_1400_after_close():
    state = Co2HysteresisState()
    start = datetime(2026, 8, 28, 8, 0, tzinfo=UTC)
    assert state.start_airing_session(target_ppm=1250)

    state.evaluate(
        now=start,
        co2=1240,
        window_open=True,
        previous_mode="weiter_lueften",
        previous_need="co2_high",
    )
    ready = state.evaluate(
        now=start + CO2_AIRING_FINISH_STABLE,
        co2=1240,
        window_open=True,
        previous_mode="co2_abwaegung",
        previous_need="co2_high",
    )
    assert ready.finish_ready is True
    assert ready.rearm_threshold_ppm is None

    closed = state.evaluate(
        now=start + CO2_AIRING_FINISH_STABLE + timedelta(seconds=1),
        co2=1240,
        window_open=False,
        previous_mode="lueftung_fertig",
        previous_need="co2_elevated",
    )
    assert closed.rearm_threshold_ppm == 1400
    assert state.session_active is False


def test_rearm_deadband_ignores_999_to_1000_flicker_after_1400_session():
    state = Co2HysteresisState(rearm_threshold_ppm=1400)
    start = datetime(2026, 8, 28, 9, 0, tzinfo=UTC)

    first = state.evaluate(
        now=start,
        co2=999,
        window_open=False,
        previous_mode="normal",
        previous_need="none",
    )
    second = state.evaluate(
        now=start + timedelta(minutes=1),
        co2=1000,
        window_open=False,
        previous_mode="normal",
        previous_need="none",
    )
    assert first.rearm_threshold_ppm == 1400
    assert second.rearm_threshold_ppm == 1400
    assert state.rearm_below_since is None


def test_rearm_moves_from_1400_to_1000_only_after_two_minutes_at_950_or_less():
    from custom_components.lueftungsberater.co2_hysteresis import CO2_REARM_STABLE

    state = Co2HysteresisState(rearm_threshold_ppm=1400)
    start = datetime(2026, 8, 28, 10, 0, tzinfo=UTC)

    first = state.evaluate(
        now=start,
        co2=945,
        window_open=False,
        previous_mode="normal",
        previous_need="none",
    )
    almost = state.evaluate(
        now=start + CO2_REARM_STABLE - timedelta(seconds=1),
        co2=950,
        window_open=False,
        previous_mode="normal",
        previous_need="none",
    )
    ready = state.evaluate(
        now=start + CO2_REARM_STABLE,
        co2=948,
        window_open=False,
        previous_mode="normal",
        previous_need="none",
    )

    assert first.rearm_threshold_ppm == 1400
    assert almost.rearm_threshold_ppm == 1400
    assert ready.rearm_threshold_ppm == 1000


def test_rearm_can_drop_directly_to_lowest_proven_band():
    from custom_components.lueftungsberater.co2_hysteresis import CO2_REARM_STABLE

    state = Co2HysteresisState(rearm_threshold_ppm=1700)
    start = datetime(2026, 8, 28, 10, 30, tzinfo=UTC)
    state.evaluate(
        now=start,
        co2=930,
        window_open=False,
        previous_mode="normal",
        previous_need="none",
    )
    ready = state.evaluate(
        now=start + CO2_REARM_STABLE,
        co2=940,
        window_open=False,
        previous_mode="normal",
        previous_need="none",
    )
    assert ready.rearm_threshold_ppm == 1000


def test_rearm_state_roundtrips_for_restart_memory():
    start = datetime(2026, 8, 28, 11, 0, tzinfo=UTC)
    original = Co2HysteresisState(
        rearm_threshold_ppm=1400,
        rearm_below_since=start,
        rearm_candidate_ppm=1000,
    )
    payload = original.as_dict()
    restored = Co2HysteresisState()
    restored.restore(
        pending_below_since=None,
        finish_below_since=None,
        rearm_threshold_ppm=payload["rearm_threshold_ppm"],
        rearm_below_since=datetime.fromisoformat(payload["rearm_below_since"]),
        rearm_candidate_ppm=payload["rearm_candidate_ppm"],
    )
    assert restored.rearm_threshold_ppm == 1400
    assert restored.rearm_candidate_ppm == 1000
    assert restored.rearm_below_since == start


def test_new_successful_lower_target_can_replace_an_older_higher_rearm_lock():
    state = Co2HysteresisState(rearm_threshold_ppm=1400)
    start = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)
    assert state.start_airing_session(target_ppm=850)
    state.evaluate(
        now=start,
        co2=840,
        window_open=True,
        previous_mode="weiter_lueften",
        previous_need="co2_high",
    )
    state.evaluate(
        now=start + CO2_AIRING_FINISH_STABLE,
        co2=840,
        window_open=True,
        previous_mode="co2_abwaegung",
        previous_need="co2_elevated",
    )
    closed = state.evaluate(
        now=start + CO2_AIRING_FINISH_STABLE + timedelta(seconds=1),
        co2=840,
        window_open=False,
        previous_mode="lueftung_fertig",
        previous_need="co2_elevated",
    )
    assert closed.rearm_threshold_ppm == 1000

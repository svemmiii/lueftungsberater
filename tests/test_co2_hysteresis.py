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

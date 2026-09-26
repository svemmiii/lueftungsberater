from datetime import datetime, timedelta, timezone

from custom_components.lueftungsberater.reason_sessions import (
    HUMIDITY_MIN_REST,
    HUMIDITY_PROGRESS_WINDOW,
    HUMIDITY_REARM_STABLE,
    HumiditySessionState,
)

UTC = timezone.utc


def _evaluate(
    state: HumiditySessionState,
    *,
    now: datetime,
    rh: float = 60.0,
    indoor_ah: float = 11.6,
    outdoor_ah: float = 8.0,
    window_open: bool = True,
    actionable: bool = True,
    still_needed: bool = True,
):
    return state.evaluate(
        now=now,
        indoor_temp=22.0,
        indoor_rh=rh,
        indoor_ah=indoor_ah,
        outdoor_ah=outdoor_ah,
        window_open=window_open,
        humidity_actionable=actionable,
        humidity_still_needed=still_needed,
        safety_lock=False,
        mold_risk=False,
    )


def test_humidity_session_exhausts_when_absolute_humidity_stops_improving():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)

    first = _evaluate(state, now=start)
    plateau = _evaluate(
        state,
        now=start + HUMIDITY_PROGRESS_WINDOW,
        rh=59.8,
        indoor_ah=11.45,  # only 0.15 g/m3 better: below the 0.25 dead-band
    )

    assert first.session_active is True
    assert plateau.session_active is False
    assert plateau.exhausted is True
    assert plateau.disarmed is True


def test_exhausted_humidity_session_does_not_restart_after_one_hour_if_nothing_changed():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    _evaluate(state, now=start)
    _evaluate(
        state,
        now=start + HUMIDITY_PROGRESS_WINDOW,
        rh=60.0,
        indoor_ah=11.5,
    )

    later = _evaluate(
        state,
        now=start + HUMIDITY_PROGRESS_WINDOW + timedelta(hours=2),
        rh=60.1,
        indoor_ah=11.52,
        window_open=False,
        actionable=False,
        still_needed=False,
    )

    assert later.disarmed is True
    assert state.session_active is False


def test_materially_better_outdoor_drying_is_only_an_optional_opportunity():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    _evaluate(state, now=start, indoor_ah=11.6, outdoor_ah=9.0)
    _evaluate(
        state,
        now=start + HUMIDITY_PROGRESS_WINDOW,
        indoor_ah=11.5,
        outdoor_ah=9.0,
    )

    after_rest = start + HUMIDITY_PROGRESS_WINDOW + HUMIDITY_MIN_REST
    _evaluate(
        state,
        now=after_rest,
        rh=60.0,
        indoor_ah=11.5,
        outdoor_ah=7.8,  # >1 g/m3 extra drying potential versus reference
        window_open=False,
        actionable=False,
        still_needed=False,
    )
    stable = _evaluate(
        state,
        now=after_rest + HUMIDITY_REARM_STABLE,
        rh=60.0,
        indoor_ah=11.5,
        outdoor_ah=7.8,
        window_open=False,
        actionable=False,
        still_needed=False,
    )

    assert stable.optional_opportunity is True
    assert stable.disarmed is True  # not a renewed obligation


def test_humidity_rearms_only_after_sustained_real_worsening():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    _evaluate(state, now=start)
    _evaluate(
        state,
        now=start + HUMIDITY_PROGRESS_WINDOW,
        rh=60.0,
        indoor_ah=11.5,
    )

    after_rest = start + HUMIDITY_PROGRESS_WINDOW + HUMIDITY_MIN_REST
    first_rise = _evaluate(
        state,
        now=after_rest,
        rh=63.1,
        indoor_ah=12.1,
        window_open=False,
        actionable=False,
        still_needed=False,
    )
    rearmed = _evaluate(
        state,
        now=after_rest + HUMIDITY_REARM_STABLE,
        rh=63.2,
        indoor_ah=12.1,
        window_open=False,
        actionable=False,
        still_needed=False,
    )

    assert first_rise.disarmed is True
    assert rearmed.disarmed is False


def test_rapid_humidity_peak_breaks_comfort_quiet_state_immediately():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    # Seed a completed/quiet attempt directly; peak detection is independent of
    # the way the prior session finished.
    state.disarmed = True
    state.exhausted = True
    state.exhausted_at = start - timedelta(minutes=10)
    state.reference_rh = 60.0
    state.reference_ah = 11.5
    state.reference_drying_potential = 2.0

    _evaluate(
        state,
        now=start,
        rh=60.0,
        indoor_ah=11.5,
        window_open=False,
        actionable=False,
        still_needed=False,
    )
    peak = _evaluate(
        state,
        now=start + timedelta(minutes=5),
        rh=67.0,
        indoor_ah=13.0,
        window_open=False,
        actionable=False,
        still_needed=False,
    )

    assert peak.disarmed is False
    assert state.peak_active is True


def test_peak_recovery_without_airing_gets_a_reference_and_can_rearm_later():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)

    _evaluate(
        state,
        now=start,
        rh=60.0,
        indoor_ah=11.5,
        window_open=False,
        actionable=False,
        still_needed=False,
    )
    _evaluate(
        state,
        now=start + timedelta(minutes=5),
        rh=68.0,
        indoor_ah=13.2,
        window_open=False,
        actionable=False,
        still_needed=True,
    )
    recovered = _evaluate(
        state,
        now=start + timedelta(minutes=10),
        rh=64.0,
        indoor_ah=12.3,
        window_open=False,
        actionable=False,
        still_needed=True,
    )

    assert recovered.disarmed is True
    assert state.reference_rh == 64.0

    after_rest = start + timedelta(minutes=10) + HUMIDITY_MIN_REST
    _evaluate(
        state,
        now=after_rest,
        rh=67.2,
        indoor_ah=13.0,
        window_open=False,
        actionable=False,
        still_needed=True,
    )
    rearmed = _evaluate(
        state,
        now=after_rest + HUMIDITY_REARM_STABLE,
        rh=67.2,
        indoor_ah=13.0,
        window_open=False,
        actionable=False,
        still_needed=True,
    )
    assert rearmed.disarmed is False


def test_peak_is_not_declared_recovered_while_room_is_still_very_humid():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    _evaluate(
        state,
        now=start,
        rh=60.0,
        indoor_ah=11.5,
        window_open=False,
        actionable=False,
        still_needed=False,
    )
    _evaluate(
        state,
        now=start + timedelta(minutes=5),
        rh=80.0,
        indoor_ah=15.5,
        window_open=False,
        actionable=False,
        still_needed=True,
    )
    still_high = _evaluate(
        state,
        now=start + timedelta(minutes=10),
        rh=72.0,
        indoor_ah=14.0,
        window_open=False,
        actionable=False,
        still_needed=True,
    )
    assert still_high.peak_recovery is False
    assert still_high.disarmed is False


def test_manual_window_close_finishes_humidity_attempt_into_quiet_state():
    """Closing a running comfort airing must not immediately ask to reopen."""
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    started = _evaluate(state, now=start, rh=60.4, indoor_ah=11.7, outdoor_ah=8.4)
    assert started.session_active is True

    closed = _evaluate(
        state,
        now=start + timedelta(minutes=5),
        rh=60.4,
        indoor_ah=11.7,
        outdoor_ah=8.4,
        window_open=False,
        actionable=True,
        still_needed=True,
    )
    assert closed.session_active is False
    assert closed.disarmed is True
    assert state.reference_rh == 60.4


def test_indoor_air_aftercare_only_suppresses_lingering_moderate_state():
    from custom_components.lueftungsberater.reason_sessions import IndoorAirSessionState

    state = IndoorAirSessionState()
    start = datetime(2026, 9, 26, 11, 0, tzinfo=UTC)
    running = state.evaluate(
        now=start,
        window_open=True,
        quality="moderate",
        trend="stable",
    )
    assert running.session_active is True

    closed = state.evaluate(
        now=start + timedelta(minutes=5),
        window_open=False,
        quality="moderate",
        trend="stable",
    )
    assert closed.disarmed is True

    urgent = state.evaluate(
        now=start + timedelta(minutes=6),
        window_open=False,
        quality="poor",
        trend="rising",
    )
    assert urgent.disarmed is False


def test_rearm_timer_keeps_remaining_minimum_rest_after_stability_is_met():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    state.disarmed = True
    state.exhausted = True
    state.exhausted_at = start
    state.reference_rh = 60.0
    state.reference_ah = 11.5
    state.reference_drying_potential = 2.0

    _evaluate(
        state,
        now=start + timedelta(minutes=10),
        rh=63.2,
        indoor_ah=12.2,
        outdoor_ah=9.5,
        window_open=False,
        actionable=False,
        still_needed=True,
    )
    stable_before_rest = _evaluate(
        state,
        now=start + timedelta(minutes=25),
        rh=63.2,
        indoor_ah=12.2,
        outdoor_ah=9.5,
        window_open=False,
        actionable=False,
        still_needed=True,
    )

    assert stable_before_rest.disarmed is True
    assert stable_before_rest.next_check_seconds == 35 * 60


def test_better_outdoor_timer_keeps_remaining_minimum_rest_after_stability_is_met():
    state = HumiditySessionState()
    start = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    state.disarmed = True
    state.exhausted = True
    state.exhausted_at = start
    state.reference_rh = 60.0
    state.reference_ah = 11.5
    state.reference_drying_potential = 2.0

    _evaluate(
        state,
        now=start + timedelta(minutes=10),
        rh=60.0,
        indoor_ah=11.5,
        outdoor_ah=8.0,
        window_open=False,
        actionable=False,
        still_needed=True,
    )
    stable_before_rest = _evaluate(
        state,
        now=start + timedelta(minutes=25),
        rh=60.0,
        indoor_ah=11.5,
        outdoor_ah=8.0,
        window_open=False,
        actionable=False,
        still_needed=True,
    )

    assert stable_before_rest.optional_opportunity is False
    assert stable_before_rest.next_check_seconds == 35 * 60

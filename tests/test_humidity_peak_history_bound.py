"""Peak history remains bounded without hiding short humidity events."""
from datetime import datetime, timedelta, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

# This module is pure Python; test it independently of the optional HA runtime.
# The normal integration suite still imports it through the HA package.
_source = Path(__file__).resolve().parents[1] / "custom_components/lueftungsberater/reason_sessions.py"
_spec = spec_from_file_location("humidity_peak_under_test", _source)
_module = module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
HUMIDITY_PEAK_MAX_SAMPLES = _module.HUMIDITY_PEAK_MAX_SAMPLES
HUMIDITY_PEAK_WINDOW = _module.HUMIDITY_PEAK_WINDOW
HumiditySessionState = _module.HumiditySessionState

UTC = timezone.utc


def test_one_hundred_millisecond_updates_keep_memory_bounded_and_extrema():
    state = HumiditySessionState()
    start = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
    # 10,000 samples in 16m40s, including two events just 100ms apart.
    for index in range(10_000):
        rh = 48.0 if index == 4_200 else 75.0 if index == 4_201 else 60.0
        now = start + timedelta(milliseconds=100 * index)
        state._observe_peak(now=now, rh=rh, ah=11.0)
        assert len(state.samples) <= HUMIDITY_PEAK_MAX_SAMPLES

    # Extrema from within the 15-minute window survive resampling.
    assert any(sample[1] == 48.0 for sample in state.samples)
    assert any(sample[1] == 75.0 for sample in state.samples)
    assert all(sample[0] >= now - HUMIDITY_PEAK_WINDOW for sample in state.samples)


def test_condensed_low_still_triggers_real_rapid_rise():
    state = HumiditySessionState()
    start = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
    for index in range(400):
        rh = 51.0 if index == 250 else 54.0
        state._observe_peak(
            now=start + timedelta(milliseconds=100 * index), rh=rh, ah=10.0
        )
    assert any(sample[1] == 51.0 for sample in state.samples)
    peak = state._observe_peak(now=start + timedelta(seconds=40), rh=58.0, ah=10.5)
    assert peak is True
    assert state.peak_baseline_rh == 51.0


def test_expired_extrema_do_not_false_trigger_new_peak():
    state = HumiditySessionState()
    start = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
    state._observe_peak(now=start, rh=48.0, ah=9.0)
    for index in range(1, 350):
        state._observe_peak(
            now=start + timedelta(milliseconds=index * 100), rh=60.0, ah=11.0
        )
    now = start + HUMIDITY_PEAK_WINDOW + timedelta(seconds=1)
    assert state._observe_peak(now=now, rh=55.0, ah=10.0) is False
    assert not any(sample[1] == 48.0 for sample in state.samples)
    assert len(state.samples) <= HUMIDITY_PEAK_MAX_SAMPLES


def test_sparse_samples_are_not_unnecessarily_condensed():
    state = HumiditySessionState()
    start = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
    for minute, rh in enumerate((50.0, 53.0, 51.0, 58.0, 56.0)):
        state._observe_peak(
            now=start + timedelta(minutes=minute), rh=rh, ah=10.0
        )
    assert [sample[1] for sample in state.samples] == [50., 53., 51., 58., 56.]


def test_clock_rollback_does_not_keep_future_dated_samples():
    state = HumiditySessionState()
    start = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
    state._observe_peak(now=start + timedelta(minutes=4), rh=41., ah=8.)
    assert not state._observe_peak(now=start, rh=50., ah=9.)
    assert [sample[1] for sample in state.samples] == [50.]

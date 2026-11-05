"""Regression cases for humidity peaks at the edge of the 15-minute window.

Use the pure state implementation so these checks run without Home Assistant.
"""
from datetime import datetime, timedelta, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

source = Path(__file__).resolve().parents[1] / 'custom_components/lueftungsberater/reason_sessions.py'
spec = spec_from_file_location('humidity_peak_edge_under_test', source)
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
HumiditySessionState = module.HumiditySessionState
WINDOW = module.HUMIDITY_PEAK_WINDOW
LIMIT = module.HUMIDITY_PEAK_MAX_SAMPLES

START = datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc)


def observe(state, seconds, rh):
    return state._observe_peak(now=START + timedelta(seconds=seconds), rh=float(rh), ah=10.0)


def test_expiring_bucket_minimum_keeps_later_valid_minimum():
    """49% is expired, but 50% must not disappear with it."""
    state = HumiditySessionState()
    observe(state, 0, 49)
    observe(state, 1, 50)
    observe(state, 2, 54)
    for sec in range(3, 900):
        observe(state, sec, 52)
        assert len(state.samples) <= LIMIT

    now = START + WINDOW + timedelta(milliseconds=500)
    valid = [rh for timestamp, rh, _ in state.samples if timestamp >= now - WINDOW]
    assert min(valid) == 50
    assert observe(state, 900.5, 57) is True
    assert state.peak_baseline_rh == 50
    assert len(state.samples) <= LIMIT


def test_successive_minima_take_over_as_older_values_expire():
    state = HumiditySessionState()
    for seconds, rh in ((0, 49), (1, 50), (2, 51), (3, 54)):
        observe(state, seconds, rh)
    for sec in range(4, 900):
        observe(state, sec, 52)

    for seconds, correct_minimum in ((900.5, 50), (901.5, 51), (902.5, 52)):
        observe(state, seconds, 55)
        assert min(sample[1] for sample in state.samples) == correct_minimum
        assert len(state.samples) <= LIMIT


def test_extremes_and_latest_sample_remain_when_first_two_expire():
    state = HumiditySessionState()
    for sec, rh in ((0, 49), (1, 54), (2, 52)):
        observe(state, sec, rh)
    for i in range(200):
        observe(state, 3 + i * 0.05, 53)
    assert len(state.samples) <= LIMIT

    # The first two extrema are now expired, but the last sample in their
    # original bucket is still a valid baseline.
    observe(state, 901.5, 57)
    assert min(point[1] for point in state.samples) == 52
    assert len(state.samples) <= LIMIT


def test_rapid_updates_always_respect_hard_sample_limit():
    state = HumiditySessionState()
    for i in range(50_000):
        # Both smooth changes and short outliers, with 100ms timestamps.
        rh = 40 + ((i * 37) % 250) / 10
        observe(state, i / 10, rh)
        assert len(state.samples) <= LIMIT
    assert all(sample[0] >= START + timedelta(seconds=4999.9) - WINDOW
               for sample in state.samples)

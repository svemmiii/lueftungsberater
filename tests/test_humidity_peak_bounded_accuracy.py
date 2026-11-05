"""Numerical error and work-budget regressions for peak-history compression.

The reference stream uses a lossless monotone queue for its rolling minimum.
This deliberately exercises more histories than ordinary room sensors produce.
"""
from collections import deque
from datetime import datetime, timedelta, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import random
import sys

import pytest

_SOURCE = Path(__file__).resolve().parents[1] / "custom_components/lueftungsberater/reason_sessions.py"
_SPEC = spec_from_file_location("humidity_peak_accuracy_under_test", _SOURCE)
_MOD = module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MOD
_SPEC.loader.exec_module(_MOD)
HumiditySessionState = _MOD.HumiditySessionState
MAX_SAMPLES = _MOD.HUMIDITY_PEAK_MAX_SAMPLES
RH_ERROR = _MOD.HUMIDITY_PEAK_VALUE_BIN_RH
WINDOW = _MOD.HUMIDITY_PEAK_WINDOW
START = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def _check_against_exact_minimum(values, *, interval_ms):
    """Stored minimum must never be older than the window or too high."""
    state = HumiditySessionState()
    exact_min = deque()
    largest_error = 0.0
    for i, value in enumerate(values):
        now = START + timedelta(milliseconds=i * interval_ms)
        cutoff = now - WINDOW
        while exact_min and exact_min[0][0] < cutoff:
            exact_min.popleft()
        while exact_min and exact_min[-1][1] >= value:
            exact_min.pop()
        exact_min.append((now, value))

        state._observe_peak(now=now, rh=value, ah=10.0)
        assert len(state.samples) <= MAX_SAMPLES
        assert state.samples[0][0] >= cutoff
        assert state.samples[-1][0] <= now
        retained_min = min(sample[1] for sample in state.samples)
        error = retained_min - exact_min[0][1]
        # Only original readings can survive; compression cannot invent a
        # smaller humidity than actually present in the sliding window.
        assert error >= -1e-10
        assert error < RH_ERROR + 1e-10
        largest_error = max(largest_error, error)
    return state, largest_error


def test_boundary_successor_in_same_rh_interval():
    """The latest representative survives even after the exact oldest low."""
    state = HumiditySessionState()
    for offset, rh in ((0, 49.0), (1, 49.3), (2, 54.0)):
        state._observe_peak(now=START + timedelta(seconds=offset), rh=rh, ah=10.0)
    for offset in range(3, 900):
        state._observe_peak(now=START + timedelta(seconds=offset), rh=52.0, ah=10.0)
    at = START + timedelta(seconds=900.5)
    assert state._observe_peak(now=at, rh=55.4, ah=10.0) is True
    assert state.peak_baseline_rh == pytest.approx(49.3)
    assert len(state.samples) <= MAX_SAMPLES


def test_continuous_strong_oscillations_have_bounded_peak_error():
    random_gen = random.Random(20261105)
    values = [
        # Large alternating peaks, rare troughs and many distinct RH values.
        round((40 + random_gen.random() * 47) if i % 3
              else (46 + ((i * 23) % 300) / 10), 3)
        for i in range(12_000)
    ]
    state, largest_error = _check_against_exact_minimum(values, interval_ms=100)
    assert largest_error < RH_ERROR
    assert any(sample[1] >= 80 for sample in state.samples)


def test_full_physical_humidity_range_respects_error_and_budget():
    # Forces more occupied RH intervals than a normal sensor ever would.
    values = [float((i * 7919) % 10001) / 100.0 for i in range(10_000)]
    state, largest_error = _check_against_exact_minimum(values, interval_ms=100)
    assert largest_error < RH_ERROR
    assert len(state.samples) <= MAX_SAMPLES


def test_out_of_range_sensor_values_still_obey_memory_budget():
    # The physical-range error guarantee is intentionally not claimed here.
    state = HumiditySessionState()
    for i in range(1000):
        state._observe_peak(
            now=START + timedelta(seconds=i),
            rh=float(((i * 29) % 2400) - 1200),
            ah=10.0,
        )
        assert len(state.samples) <= MAX_SAMPLES


def test_long_smooth_rise_preserves_nearby_baselines():
    values = [40.0 + 60.0 * i / 19_999 for i in range(20_000)]
    _, error = _check_against_exact_minimum(values, interval_ms=100)
    assert error < RH_ERROR


def test_repeat_early_low_stays_valid_until_own_expiry():
    """The oldest true minimum isn't allowed to linger after its time ends."""
    state = HumiditySessionState()
    for offset, value in ((0, 49), (1, 50), (2, 54)):
        state._observe_peak(now=START + timedelta(seconds=offset), rh=value, ah=10.0)
    for offset in range(3, 900):
        state._observe_peak(now=START + timedelta(seconds=offset), rh=52, ah=10.0)
    now = START + timedelta(seconds=900.5)
    assert state._observe_peak(now=now, rh=57, ah=10.0) is True
    assert state.peak_baseline_rh == 50


def test_invalid_rh_cannot_crash_history_compaction():
    state = HumiditySessionState()
    for i in range(230):
        state._observe_peak(now=START + timedelta(seconds=i), rh=48 + i / 1000, ah=10.0)
    before = list(state.samples)
    assert state._observe_peak(now=START + timedelta(seconds=231), rh=float('nan'), ah=10.0) is False
    assert state._observe_peak(now=START + timedelta(seconds=232), rh=float('inf'), ah=10.0) is False
    assert state.samples == before

"""v0.11.4 COMPLETE(13): fail-closed weather sensor clearing and truthful provenance."""
from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import pytest

from test_v0114_complete12_weather_records_pure import _parts, _setup, A


@pytest.mark.parametrize("state_value", [
    "not-a-number", "nan", "inf", "-inf", "-1", "500", "", "none",
])
def test_invalid_gust_reading_does_not_clear_saved_window_lock(state_value):
    clock, disk, memory, states, run, report = _setup()
    active = report(sources=(A,))
    active.source_gust = A
    active.wind_gust_kmh = 110
    run(active)
    previous_deadline = _parts(disk)[A]["valid_until"]
    clock[0] += timedelta(minutes=5)
    states[A] = SimpleNamespace(state=state_value, attributes={"unit_of_measurement": "km/h"})
    memory.clear()
    result = report()
    run(result)
    assert result.weather_hard_lock is True
    assert set(_parts(disk)) == {A}
    assert _parts(disk)[A]["valid_until"] == previous_deadline


def test_no_unit_and_stale_wind_are_not_confirmed_clear():
    clock, disk, memory, states, run, report = _setup()
    active = report(sources=(A,))
    active.source_wind = A
    active.wind_speed_kmh = 95
    run(active)
    previous_deadline = _parts(disk)[A]["valid_until"]
    clock[0] += timedelta(minutes=5)
    states[A] = SimpleNamespace(state="20", attributes={"unit_of_measurement": ""})
    run(report())
    assert _parts(disk)[A]["valid_until"] == previous_deadline
    states[A] = SimpleNamespace(
        state="20", attributes={"unit_of_measurement": "km/h"},
        last_updated=clock[0] - timedelta(minutes=40),
    )
    memory.clear()
    run(report())
    assert _parts(disk)[A]["valid_until"] == previous_deadline
    states[A].last_updated = clock[0] - timedelta(minutes=2)
    memory.clear()
    run(report())
    assert "weather" not in disk.get("channels", {})


def test_safe_valid_mph_reading_resolves_original_wind_hazard():
    clock, disk, memory, states, run, report = _setup()
    active = report(sources=(A,))
    active.source_wind = A
    active.wind_speed_kmh = 105
    run(active)
    clock[0] += timedelta(minutes=5)
    states[A] = SimpleNamespace(state="15", attributes={"unit_of_measurement": "mph"})
    run(report())
    assert "weather" not in disk["channels"]


def test_hail_retains_hail_reason_with_nonhard_wind_and_gust():
    clock, disk, memory, states, run, report = _setup()
    source = "weather.home"
    states[source] = SimpleNamespace(
        state="hail", attributes={"wind_speed": 18, "wind_gust_speed": 30,
                                  "wind_speed_unit": "km/h"})
    active = report(sources=(source,))
    active.weather_reason_key = "weather_hail_danger"
    active.weather_reason_args = {}
    active.source_wind = source
    active.source_gust = source
    active.wind_speed_kmh = 18
    active.wind_gust_kmh = 30
    run(active)
    assert _parts(disk)[source]["reason_key"] == "weather_hail_danger"
    assert _parts(disk)[source]["hazard_measurement"] == "condition"
    states[source].state = "unavailable"
    clock[0] += timedelta(minutes=5)
    memory.clear()
    fallback = report()
    run(fallback)
    assert fallback.weather_reason_key == "weather_hail_danger"
    assert fallback.weather_hard_lock is True


def test_wind_not_lower_gust_is_stored_when_only_wind_exceeds_hard_threshold():
    clock, disk, memory, states, run, report = _setup()
    source = "weather.home"
    states[source] = SimpleNamespace(
        state="windy", attributes={"wind_speed": 95, "wind_gust_speed": 60,
                                   "wind_speed_unit": "km/h"})
    active = report(sources=(source,))
    active.weather_reason_key = "weather_wind_danger"
    active.source_wind = source
    active.source_gust = source
    active.wind_speed_kmh = 95
    active.wind_gust_kmh = 60
    run(active)
    saved = _parts(disk)[source]
    assert saved["reason_key"] == "weather_wind_danger"
    assert saved["reason_args"] == {"speed_kmh": 95}
    assert saved["hazard_measurement"] == "wind"
    clock[0] += timedelta(minutes=5)
    # Weather is reachable but original wind measurement is corrupt:
    # valid weather condition must not clear a wind-originated lock.
    states[source].attributes["wind_speed"] = float("nan")
    memory.clear()
    run(report())
    assert source in _parts(disk)
    # Confirmed safe wind reading does release it.
    states[source].attributes["wind_speed"] = 15
    memory.clear()
    run(report())
    assert "weather" not in disk["channels"]


def test_hail_condition_and_separate_hard_wind_keep_their_own_reasons():
    clock, disk, memory, states, run, report = _setup()
    condition_source = "weather.home"
    states[condition_source] = SimpleNamespace(
        state="hail", attributes={"wind_speed": 18, "wind_gust_speed": 30,
                                  "wind_speed_unit": "km/h"})
    states[A] = SimpleNamespace(state="95", attributes={"unit_of_measurement": "km/h"})
    active = report(sources=(condition_source, A))
    active.weather_reason_key = "weather_hail_danger"
    active.source_wind = A
    active.wind_speed_kmh = 95
    run(active)
    records = _parts(disk)
    assert records[condition_source]["reason_key"] == "weather_hail_danger"
    assert records[A]["reason_key"] == "weather_wind_danger"
    assert records[A]["reason_args"] == {"speed_kmh": 95}
    clock[0] += timedelta(minutes=5)
    states[condition_source].state = "sunny"
    states[A].state = "unavailable"
    memory.clear()
    fallback = report()
    run(fallback)
    assert set(_parts(disk)) == {A}
    assert fallback.weather_reason_key == "weather_wind_danger"
    assert fallback.weather_reason_args["speed_kmh"] == 95

"""Independent persistent hard-weather source evidence and fallback TTLs."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import math
from types import SimpleNamespace

from test_v0114_complete2_pure import _extract
from test_v0114_complete4_safety_pure import _persistence_environment

A = "sensor.gust_a"
B = "sensor.wind_b"
AUTO = "auto_weather:50.7000:7.1000"


def _setup(*, automatic=False):
    clock = [datetime(2026, 10, 12, 15, tzinfo=timezone.utc)]
    apply, disk, memory = _persistence_environment(clock_ref=clock)
    extra = _extract("safety_state.py", {
        "_weather_provider_availability", "_record_from_weather", "_apply_weather_record",
    }, {
        "CONF_WEATHER": "weather",
        "_state_unknown": lambda state: state is None or state.state in
        ("unknown", "unavailable", "none", ""),
        "_json_reason_args": lambda value: dict(value) if isinstance(value, dict) else {},
        "SAFETY_FALLBACK_MAX_AGE": timedelta(hours=1), "timedelta": timedelta,
    })
    apply.__globals__.update(extra)
    reading = _extract("air_sensors.py", {
        "AirReading", "_finite", "state_is_fresh", "state_number", "SENSOR_MAX_AGE",
    }, {"dt_util": SimpleNamespace(utcnow=lambda: clock[0], UTC=timezone.utc),
        "timedelta": timedelta, "math": math})
    def normalize_speed(value, unit):
        if unit not in ("km/h", "kmh", "m/s", "mph"):
            return None
        try:
            v = float(value)
        except (ValueError, TypeError):
            return None
        if not math.isfinite(v):
            return None
        return v * {"km/h": 1, "kmh": 1, "m/s": 3.6, "mph": 1.609344}[unit]
    source_check = _extract("safety_state.py", {"_weather_source_reliably_readable", "_weather_source_confirmed_safe"}, {
        "state_is_fresh": reading["state_is_fresh"],
        "state_number": reading["state_number"],
        "_wind_to_kmh": normalize_speed,
    })
    source_check["_weather_source_confirmed_safe"].__globals__.update(source_check)
    source_check["_weather_source_confirmed_safe"].__globals__.update({
        "GUST_HARD_LOCK_KMH": 105.0, "WIND_HARD_LOCK_KMH": 89.0,
    })
    apply.__globals__.update(source_check)
    apply.__globals__.update({
        "GUST_HARD_LOCK_KMH": 105.0, "WIND_HARD_LOCK_KMH": 89.0,
    })
    entry = SimpleNamespace(entry_id="weather-independent", data={"weather": "weather.home"})
    states = {A: SimpleNamespace(state="110"), B: SimpleNamespace(state="110")}
    def local_state(source):
        state = states.get(source)
        if state is not None and not hasattr(state, "attributes"):
            # Simulate HA's physical unit metadata for numeric fixture states.
            state.attributes = {"unit_of_measurement": "km/h"}
        return state
    hass = SimpleNamespace(states=SimpleNamespace(get=local_state))

    def weather(*, sources=(), provider_ready=None, key=None, hard=None):
        source_set = set(sources)
        is_hard = bool(source_set) if hard is None else hard
        return SimpleNamespace(
            safety_source_key=(AUTO if automatic else "") if key is None else key,
            provider_available=provider_ready,
            weather_hard_lock=is_hard, weather_danger=is_hard,
            weather_danger_sources=source_set, weather_reason_key="weather_wind_danger",
            weather_reason_args={"speed_kmh": 110}, weather_caution=False,
            weather_original_reason=None, provider_domain="dwd_station",
        )

    def run(report):
        asyncio.run(apply(hass, entry, report, SimpleNamespace()))
        return disk.get("channels", {}).get("weather", {})

    return clock, disk, memory, states, run, weather


def _parts(disk):
    return {p["hazard_source"]: p for p in disk["channels"]["weather"]["weather_records"]}


def test_second_local_danger_preserves_first_unavailable_with_independent_ttls():
    clock, disk, memory, states, run, report = _setup()
    run(report(sources=(A,)))
    old_deadline = _parts(disk)[A]["valid_until"]
    clock[0] += timedelta(minutes=5)
    states[A] = SimpleNamespace(state="unavailable")
    run(report(sources=(B,)))
    assert set(_parts(disk)) == {A, B}
    assert _parts(disk)[A]["valid_until"] == old_deadline
    assert _parts(disk)[B]["valid_until"] == (clock[0] + timedelta(hours=1)).isoformat()

    memory.clear()  # Simulate HA restart using only JSON on disk.
    clock[0] += timedelta(minutes=2)
    states[B] = SimpleNamespace(state="80")
    no_longer_windy = report()
    run(no_longer_windy)
    assert set(_parts(disk)) == {A}
    assert no_longer_windy.weather_hard_lock is True
    assert no_longer_windy.weather_danger_sources == {A}
    assert _parts(disk)[A]["valid_until"] == old_deadline

    clock[0] += timedelta(minutes=54)  # 16:01, older A expires.
    memory.clear()
    recovered = report()
    run(recovered)
    assert recovered.weather_hard_lock is False
    assert "weather" not in disk["channels"]


def test_resolving_a_does_not_end_unresolved_b():
    clock, disk, memory, states, run, report = _setup()
    run(report(sources=(A, B)))
    states[A] = SimpleNamespace(state="80")
    states[B] = SimpleNamespace(state="unavailable")
    clock[0] += timedelta(minutes=4)
    memory.clear()
    result = report()
    run(result)
    assert set(_parts(disk)) == {B}
    assert result.weather_hard_lock is True
    states[B] = SimpleNamespace(state="80")
    memory.clear()
    run(report())
    assert "weather" not in disk["channels"]


def test_auto_provider_success_never_clears_unavailable_local_source():
    clock, disk, memory, states, run, report = _setup(automatic=True)
    run(report(sources=(A, AUTO), provider_ready=True))
    states[A] = SimpleNamespace(state="unavailable")
    clock[0] += timedelta(minutes=7)
    memory.clear()
    fresh_auto_clear = report(provider_ready=True)
    run(fresh_auto_clear)
    assert set(_parts(disk)) == {A}
    assert fresh_auto_clear.weather_hard_lock is True
    assert _parts(disk)[A]["valid_until"] == (clock[0] - timedelta(minutes=7) + timedelta(hours=1)).isoformat()


def test_failed_auto_fetch_does_not_renew_old_auto_or_local_record():
    clock, disk, memory, states, run, report = _setup(automatic=True)
    run(report(sources=(A, AUTO), provider_ready=True))
    original = {source: p["valid_until"] for source, p in _parts(disk).items()}
    states[A] = SimpleNamespace(state="unavailable")
    clock[0] += timedelta(minutes=20)
    memory.clear()
    run(report(sources=(AUTO,), provider_ready=False, hard=True))
    assert {source: p["valid_until"] for source, p in _parts(disk).items()} == original


def test_legacy_two_source_guard_migrates_without_resetting_deadline():
    clock, disk, memory, states, run, report = _setup()
    run(report(sources=(A, B)))
    old_weather = disk["channels"]["weather"]
    deadline = old_weather["valid_until"]
    old_weather.pop("weather_records")
    memory.clear()
    states[A] = SimpleNamespace(state="unavailable")
    states[B] = SimpleNamespace(state="80")
    clock[0] += timedelta(minutes=5)
    run(report())
    assert set(_parts(disk)) == {A}
    assert _parts(disk)[A]["valid_until"] == deadline


def test_independent_local_source_refresh_does_not_extend_failed_other():
    clock, disk, memory, states, run, report = _setup()
    run(report(sources=(A, B)))
    old_expiry = _parts(disk)[A]["valid_until"]
    states[A] = SimpleNamespace(state="unavailable")
    clock[0] += timedelta(minutes=55)
    run(report(sources=(B,)))
    assert _parts(disk)[A]["valid_until"] == old_expiry
    assert _parts(disk)[B]["valid_until"] == (clock[0] + timedelta(hours=1)).isoformat()
    clock[0] += timedelta(minutes=6)
    memory.clear()
    run(report(sources=(B,)))
    assert set(_parts(disk)) == {B}


def test_hard_provenance_excludes_simultaneously_nonhard_wind_and_gust():
    """A merely dangerous gust must not inherit a different hail hard lock."""
    apply_live = _extract("providers.py", {"_apply_live_weather_safety"}, {
        "WEATHER_DANGER_CONDITIONS": {"hail", "lightning", "exceptional"},
        "WIND_HARD_LOCK_KMH": 89.0, "GUST_HARD_LOCK_KMH": 105.0,
        "WIND_DANGER_KMH": 75.0, "GUST_DANGER_KMH": 90.0,
        "WIND_CAUTION_KMH": 50.0, "GUST_CAUTION_KMH": 65.0,
    })["_apply_live_weather_safety"]
    x = SimpleNamespace(
        wind_speed_kmh=80, wind_gust_kmh=95, source_wind=A, source_gust=B,
        weather_danger=False, weather_hard_lock=False, weather_caution=False,
        weather_reason_key=None, weather_reason_args={}, weather_danger_sources=set(),
    )
    apply_live(x, "hail", condition_source=AUTO)
    assert x.weather_hard_lock is True
    assert x.weather_danger_sources == {AUTO}

    x.weather_danger_sources.clear()
    x.weather_hard_lock = False
    x.weather_danger = False
    x.wind_speed_kmh = 90
    apply_live(x, "sunny", condition_source=None)
    assert x.weather_hard_lock is True
    assert x.weather_danger_sources == {A}

    x.weather_danger_sources.clear()
    x.weather_hard_lock = False
    x.weather_danger = False
    x.wind_speed_kmh = 80
    x.wind_gust_kmh = 106
    apply_live(x, "sunny", condition_source=None)
    assert x.weather_hard_lock is True
    assert x.weather_danger_sources == {B}


def test_all_three_and_four_sensor_combinations_resolve_independently():
    from itertools import product
    for count in (3, 4):
        sources = [f"sensor.test_weather_{i}" for i in range(count)]
        for assignment in product(("danger", "safe", "unavailable"), repeat=count):
            clock, disk, memory, states, run, report = _setup()
            for source in sources:
                states[source] = SimpleNamespace(state="110")
            run(report(sources=sources))
            assert set(_parts(disk)) == set(sources)
            clock[0] += timedelta(minutes=3)
            memory.clear()
            for source, condition in zip(sources, assignment):
                states[source] = SimpleNamespace(state=(
                    "unavailable" if condition == "unavailable" else
                    "80" if condition == "safe" else "110"
                ))
            danger = [src for src, condition in zip(sources, assignment) if condition == "danger"]
            run(report(sources=danger))
            expected = {
                src for src, condition in zip(sources, assignment)
                if condition != "safe"
            }
            actual = set(_parts(disk)) if "weather" in disk["channels"] else set()
            assert actual == expected, (count, assignment, actual, expected)
            for part in _parts(disk).values() if actual else []:
                assert part["valid_until"] == (clock[0] + timedelta(minutes=57)).isoformat()


def test_repeated_independent_weather_transitions_and_restarts():
    import random
    rng = random.Random(2114)
    clock, disk, memory, states, run, report = _setup()
    sources = [f"sensor.repeated_{i}" for i in range(4)]
    expiry = {}
    for source in sources:
        states[source] = SimpleNamespace(state="110")
    run(report(sources=sources))
    expiry.update({src: clock[0] + timedelta(hours=1) for src in sources})
    for step in range(250):
        clock[0] += timedelta(minutes=6)
        if step % 3 == 0:
            memory.clear()  # JSON-only restore during a changing weather situation.
        danger = []
        for source in sources:
            state = rng.choice(("danger", "danger", "safe", "unavailable"))
            states[source] = SimpleNamespace(state={
                "danger": "110", "safe": "80", "unavailable": "unavailable",
            }[state])
            if state == "danger":
                danger.append(source)
                expiry[source] = clock[0] + timedelta(hours=1)
            elif state == "safe":
                expiry.pop(source, None)
            elif source in expiry and expiry[source] <= clock[0]:
                expiry.pop(source, None)
        run(report(sources=danger))
        actual = set(_parts(disk)) if "weather" in disk["channels"] else set()
        assert actual == set(expiry), (step, actual, expiry)
        if actual:
            assert {src: part["valid_until"] for src, part in _parts(disk).items()} == {
                src: deadline.isoformat() for src, deadline in expiry.items()
            }

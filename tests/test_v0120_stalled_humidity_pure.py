"""End-to-end pure-engine checks: ineffective airing != good indoor air.

The temporary module namespace allows these tests to run without Home Assistant;
production ``engine.py``, ``models.py`` and ``reason_sessions.py`` are used.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "lueftungsberater"
PKG = "_isolated_v0120_stalled"
package = ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package
engine = import_module(f"{PKG}.engine")
models = import_module(f"{PKG}.models")
sessions = import_module(f"{PKG}.reason_sessions")
colors = import_module(f"{PKG}.window_colors")


def reading(*, rh=64, open_window=True, exhausted=False, disarmed=False,
            co2=None, hard_lock=False):
    return models.RoomInput(
        indoor_temp=22, indoor_humidity=rh, outdoor_temp=12,
        outdoor_humidity=30, target_temp=22, co2=co2,
        window_open=open_window, open_minutes=16 if open_window else None,
        has_window_contacts=True, window_data_status="current",
        current_airing_qualified=open_window,
        previous_mode="weiter_lueften", previous_need="humidity",
        humidity_session_exhausted=exhausted,
        humidity_disarmed=disarmed,
        weather_hard_lock=hard_lock,
        weather_danger=hard_lock,
    )


def evaluate(state, at, open_window, *, rh=64):
    now = datetime(2026, 11, 4, 12, tzinfo=timezone.utc) + timedelta(minutes=at)
    return state.evaluate(
        now=now, indoor_temp=22, indoor_rh=rh,
        indoor_ah=engine.absolute_humidity(22, rh),
        outdoor_ah=engine.absolute_humidity(12, 30),
        window_open=open_window, humidity_actionable=True,
        humidity_still_needed=rh >= 60, safety_lock=False,
        mold_risk=False, airing_minutes=at if open_window else None,
    )


def snap(result, *, rh=64, open_window=True):
    return SimpleNamespace(result=result, values={
        "window_open": open_window,
        "open_minutes": 16 if open_window else None,
        "has_window_contacts": True,
        "window_data_status": "current",
        "humidity_inside": rh, "co2_ppm": None,
        "temperature_inside": 22, "target_temperature": 22,
        "indoor_air_quality": "good",
    })


def test_ineffective_fifteen_minute_airing_stays_orange_through_refresh_and_close():
    state = sessions.HumiditySessionState()
    started = evaluate(state, 0, True)
    assert started.session_active and not started.disarmed
    assert engine.evaluate_room(reading()).room_status_color == "orange"
    assert evaluate(state, 5, True).session_active
    exhausted = evaluate(state, 16, True)
    assert exhausted.exhausted and exhausted.disarmed and not exhausted.session_active
    guard = colors.ShortAiringColorGuard()
    previous = snap(engine.evaluate_room(reading()))
    current = snap(engine.evaluate_room(reading(exhausted=True, disarmed=True)))
    assert current.result.active_reasons == ()  # do not ask for endless airing
    assert current.result.room_status_color == "green"
    assert current.result.room_recommendation_key == "can_close"
    assert current.result.room_reason_key == "humidity_stalled"
    guard.apply(previous, current, short_close=False, opening=False, closing=False)
    assert current.result.room_status_color == "green"
    closed = snap(engine.evaluate_room(reading(open_window=False, exhausted=True, disarmed=True)), open_window=False)
    guard.apply(current, closed, short_close=False, opening=False, closing=True)
    assert closed.result.room_status_color == "green"
    assert closed.result.room_recommendation_key == "keep_closed"
    assert closed.result.room_reason_key == "humidity_stalled"
    later = evaluate(state, 180, False)
    assert later.disarmed and later.exhausted
    refreshed = engine.evaluate_room(reading(open_window=False, exhausted=later.exhausted,
                                             disarmed=later.disarmed))
    assert refreshed.room_status_color == "green"
    restored = sessions.HumiditySessionState()
    restored.restore(state.as_dict(), parse_dt=lambda x: datetime.fromisoformat(x) if x else None)
    assert engine.evaluate_room(reading(open_window=False, exhausted=restored.exhausted,
                                        disarmed=restored.disarmed)).room_status_color == "green"


@pytest.mark.parametrize("rh, expected", [(64, "green"), (63, "green"),
                                          (62, "green"), (60.1, "green"),
                                          (59, "green"), (56, "green")])
def test_exhausted_humidity_uses_measured_recovery_not_elapsed_time(rh, expected):
    result = engine.evaluate_room(reading(rh=rh, exhausted=True, disarmed=True))
    assert result.room_status_color == expected
    assert result.recommendation_key not in {"keep_open", "open_now"}
    if rh >= 60:
        assert result.room_reason_key == "humidity_stalled"
        assert result.room_recommendation_key == "can_close"
        assert result.room_reason_args["humidity"] == rh
    else:
        assert result.room_reason_key != "humidity_stalled"


def test_exhaustion_does_not_hide_critical_independent_co2():
    result = engine.evaluate_room(reading(exhausted=True, disarmed=True, co2=2100))
    assert "co2_critical" in result.active_reasons
    assert result.room_status_color != "green"
    assert result.room_reason_key != "humidity_stalled"


def test_hard_weather_safety_still_wins():
    result = engine.evaluate_room(reading(exhausted=True, disarmed=True, hard_lock=True))
    assert result.safety_lock
    assert result.room_reason_key != "humidity_stalled"

"""Action lamp v0.12.0 invariants without a Home Assistant installation."""
from __future__ import annotations
from importlib import import_module
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "lueftungsberater"
PKG = "_isolated_v0120_action_lamp"
package = ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package
engine = import_module(f"{PKG}.engine")
models = import_module(f"{PKG}.models")
colors = import_module(f"{PKG}.window_colors")
CLOSING = {"close_now", "better_close", "can_close", "keep_closed", "caution_keep_closed"}
OPENING = {"open_now", "keep_open", "room_need", "room_urgent", "room_keep_brief", "short_observation"}


def reading(**updates):
    params = dict(indoor_temp=22, indoor_humidity=50, outdoor_temp=20,
                  outdoor_humidity=45, target_temp=22, window_open=True,
                  open_minutes=8, window_data_status="current")
    return models.RoomInput(**(params | updates))


@pytest.mark.parametrize("kwargs", [
    {},
    {"window_open": False, "open_minutes": None},
    {"co2": 2100},
    {"co2": 1550, "outdoor_temp": 12},
    {"indoor_humidity": 70, "outdoor_humidity": 80, "outdoor_temp": 22},
    {"indoor_humidity": 70, "outdoor_humidity": 40, "outdoor_temp": 21},
    {"indoor_humidity": 64, "humidity_disarmed": True,
     "humidity_session_exhausted": True, "previous_mode": "weiter_lueften",
     "previous_need": "humidity"},
    {"indoor_humidity": 64, "humidity_disarmed": True,
     "humidity_session_exhausted": True, "previous_mode": "weiter_lueften",
     "previous_need": "humidity", "window_open": False, "open_minutes": None},
    {"weather_danger": True},
    {"air_quality": "very_poor"},
    {"window_data_status": "unavailable"},
    {"nina_status": "danger"},
    {"weather_danger": True, "weather_hard_lock": True},
])
def test_public_room_color_never_contradicts_action(kwargs):
    result = engine.evaluate_room(reading(**kwargs))
    if result.safety_lock:
        assert result.recommendation_key in CLOSING
    elif result.room_recommendation_key in CLOSING:
        assert result.room_status_color == "green"
    elif result.room_recommendation_key in OPENING:
        assert result.room_status_color in {"yellow", "orange", "red"}
    # An unavailable optional contact must not override measured room needs.
    if kwargs.get("window_data_status") == "unavailable":
        ordinary = engine.evaluate_room(reading(**(kwargs | {"window_data_status": "current"})))
        assert (result.room_status_color, result.room_recommendation_key) == (
            ordinary.room_status_color, ordinary.room_recommendation_key
        )


def test_unproductive_humidity_is_green_action_but_not_success():
    r = engine.evaluate_room(reading(
        indoor_humidity=70, humidity_session_exhausted=True,
        humidity_disarmed=True, previous_need="humidity", previous_mode="weiter_lueften",
    ))
    assert r.room_status_color == "green"
    assert r.room_recommendation_key == "can_close"
    assert r.room_reason_key == "humidity_stalled"
    assert r.color != "green"  # native suitability remains visible separately
    assert r.active_reasons == ()


def test_unproductive_humidity_closed_is_green_without_claiming_good_reading():
    r = engine.evaluate_room(reading(
        indoor_humidity=64, humidity_session_exhausted=True, humidity_disarmed=True,
        window_open=False, open_minutes=None,
        previous_need="humidity", previous_mode="weiter_lueften",
    ))
    assert (r.room_status_color, r.room_recommendation_key) == ("green", "keep_closed")
    assert r.room_reason_key == "humidity_stalled"


def test_safety_wins_even_if_lamp_closing_green():
    result = engine.evaluate_room(reading(nina_status="danger", indoor_humidity=70))
    assert result.safety_lock and result.recommendation_key == "close_now"


def snapshot(*, color, action, native_action, window_open, humidity=70, outside_temp=20,
             open_minutes=None, needs=("humidity",), reason="room_perspective"):
    return SimpleNamespace(
        result=SimpleNamespace(room_status_color=color, room_recommendation_key=action,
            recommendation_key=native_action, room_reason_key=reason,
            room_reason_args={"need": "humidity"}, primary_need="humidity",
            active_reasons=needs, mode="feuchte_lueften", mold_risk=False,
            mold_persistent=False, safety_lock=False),
        values=dict(has_window_contacts=True, window_data_status="current",
                    window_open=window_open, open_minutes=open_minutes,
                    humidity_inside=humidity, temperature_outside=outside_temp,
                    co2_ppm=800, temperature_inside=22, target_temperature=22,
                    indoor_air_quality="good"))


def test_window_contact_alone_must_not_create_close_green():
    before = snapshot(color="orange", action="room_need", native_action="open_now", window_open=False)
    after = snapshot(color="green", action="can_close", native_action="can_close", window_open=True, open_minutes=0.1)
    assert colors.protect_room_color(before, after, opening=True, short_close=False)
    assert after.result.room_status_color == "orange"
    assert after.result.room_recommendation_key in OPENING


def test_actual_outside_danger_allows_close_during_minimum_window():
    before = snapshot(color="orange", action="keep_open", native_action="keep_open", window_open=True, open_minutes=2)
    after = snapshot(color="green", action="close_now", native_action="close_now", window_open=True,
                     open_minutes=2.1, outside_temp=10)
    assert not colors.protect_room_color(before, after, opening=False, short_close=False)
    assert after.result.room_status_color == "green"
    assert after.result.room_recommendation_key == "close_now"


def test_outside_improvement_allows_a_new_need_after_previous_close():
    before = snapshot(color="green", action="better_close", native_action="better_close", window_open=True,
                      open_minutes=2, outside_temp=12)
    after = snapshot(color="orange", action="keep_open", native_action="keep_open", window_open=True,
                     open_minutes=2.5, outside_temp=21)
    assert not colors.protect_room_color(before, after, opening=False, short_close=False)
    assert after.result.room_status_color == "orange"

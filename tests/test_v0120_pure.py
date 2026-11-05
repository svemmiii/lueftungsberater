"""Isolated v0.12.0 safety/learning/geo regressions, runnable without HA."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import importlib.util
import json
import lzma
import sqlite3
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "lueftungsberater"


def load(name):
    spec = importlib.util.spec_from_file_location(f"isolated_{name}", ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


colors = load("window_colors")
pattern_module = load("air_exchange")


def snapshot(*, green, open_window, minutes, co2=650, humidity=54,
             temperature=22, target=22, active_reasons=(), locked=False):
    return SimpleNamespace(
        result=SimpleNamespace(
            room_status_color="green" if green else "orange",
            mode="normal" if green else "co2_lueften",
            room_recommendation_key="can_close" if green else "keep_open",
            room_reason_key="room_perspective", room_reason_args={"need": "co2_high"},
            active_reasons=active_reasons, primary_need="co2_high",
            mold_risk=False, mold_persistent=False, safety_lock=locked,
        ),
        values={
            "window_open": open_window, "open_minutes": minutes,
            "has_window_contacts": True, "window_data_status": "available",
            "has_co2": True, "co2_ppm": co2,
            "humidity_inside": humidity, "temperature_inside": temperature,
            "target_temperature": target, "indoor_air_quality": "good",
        },
    )


def test_window_open_not_instantly_green_or_non_green():
    before = snapshot(green=False, open_window=False, minutes=None, active_reasons=("co2_high",))
    now = snapshot(green=True, open_window=True, minutes=0.01)
    assert colors.protect_room_color(before, now, short_close=False, opening=True)
    assert now.result.room_status_color == "orange"
    before = snapshot(green=True, open_window=False, minutes=None)
    now = snapshot(green=False, open_window=True, minutes=0.01)
    assert colors.protect_room_color(before, now, short_close=False, opening=True)
    assert now.result.room_status_color == "green"


def test_below_five_minutes_still_blocks_regular_green():
    before = snapshot(green=False, open_window=True, minutes=1.0)
    current = snapshot(green=True, open_window=True, minutes=4.9)
    assert colors.protect_room_color(before, current, short_close=False, opening=False)
    assert current.result.room_status_color == "orange"
    after_5 = snapshot(green=True, open_window=True, minutes=5.0)
    assert not colors.protect_room_color(before, after_5, short_close=False, opening=False)


def test_short_close_15pct_reserve_and_abort_remains_not_confirmed():
    before = snapshot(green=False, open_window=True, minutes=2.9, co2=1400,
                      active_reasons=("co2_high", "humidity"), humidity=65)
    barely_good = snapshot(green=True, open_window=False, minutes=None, co2=650, humidity=59.9)
    assert colors.protect_room_color(before, barely_good, short_close=True, opening=False, closing=True)
    assert barely_good.result.room_status_color == "orange"
    genuinely_good = snapshot(green=True, open_window=False, minutes=None, co2=650, humidity=54)
    assert colors.exceptional_short_airing_good(before, genuinely_good)
    assert not colors.protect_room_color(before, genuinely_good, short_close=True, opening=False, closing=True)
    assert genuinely_good.result.room_status_color == "green"


def test_short_close_requires_good_entire_range_and_no_other_reason():
    before = snapshot(green=False, open_window=True, minutes=2, active_reasons=("routine",))
    now = snapshot(green=True, open_window=False, minutes=None)
    assert not colors.exceptional_short_airing_good(before, now)
    before = snapshot(green=False, open_window=True, minutes=2, active_reasons=("co2_elevated",))
    for data in (dict(co2=935), dict(humidity=58), dict(humidity=42), dict(temperature=23), dict(co2=None)):
        now = snapshot(green=True, open_window=False, minutes=None)
        now.values.update({"co2_ppm": 650, "humidity_inside": 54, "temperature_inside": 22})
        translate = {"co2": "co2_ppm", "humidity": "humidity_inside", "temperature": "temperature_inside"}
        for k, v in data.items(): now.values[translate[k]] = v
        assert not colors.exceptional_short_airing_good(before, now)


def test_window_close_keeps_green_without_measurement_deterioration():
    before = snapshot(green=True, open_window=True, minutes=8)
    after = snapshot(green=False, open_window=False, minutes=None)
    assert colors.protect_room_color(before, after, short_close=False, opening=False, closing=True)
    assert after.result.room_status_color == "green"


def test_actual_worsening_or_safety_lock_is_not_hidden():
    before = snapshot(green=True, open_window=False, minutes=None)
    after = snapshot(green=False, open_window=True, minutes=0, co2=2200)
    assert not colors.protect_room_color(before, after, short_close=False, opening=True)
    locked = snapshot(green=False, open_window=True, minutes=0, locked=True)
    assert not colors.protect_room_color(before, locked, short_close=False, opening=True)


def test_pattern_bounded_reuses_real_measurement_timestamps_only():
    m = pattern_module.RoomAirPattern()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    for i in range(78):
        now = t0 + timedelta(minutes=20*i)
        assert m.observe(now=now, source_stamp=now, co2=650,
                         humidity=50, temperature=22, window_open=False)
        assert not m.observe(now=now+timedelta(seconds=2), source_stamp=now,
                             co2=650, humidity=50, temperature=22, window_open=False)
    assert len(m.as_dict()['samples']) <= pattern_module.MAX_SAMPLES
    assert m.stable_good(now=t0 + timedelta(minutes=20*77))
    assert not m.stable_good(now=t0 + timedelta(minutes=20*77, hours=1))
    restored = pattern_module.RoomAirPattern()
    restored.restore(m.as_dict(), now=t0+timedelta(minutes=20*77))
    assert restored.stable_good(now=t0+timedelta(minutes=20*77))


def test_passive_is_hint_not_proof_and_suspected_is_not_confirmed():
    m = pattern_module.RoomAirPattern()
    now = datetime(2026, 11, 4, tzinfo=timezone.utc)
    report = m.summary(now=now, contact_open=False, passive_hint=True)
    assert report['passive_ventilation_configured'] is True
    assert not report['proven_window_airing'] and not report['stable_good_air']
    m.observe(now=now, source_stamp=now, co2=1400, humidity=60, temperature=22, window_open=False)
    m.observe(now=now+timedelta(minutes=20), source_stamp=now+timedelta(minutes=20),
              co2=900, humidity=55, temperature=22, window_open=False)
    report = m.summary(now=now+timedelta(minutes=20), contact_open=False, passive_hint=False)
    assert report['status'] in {'air_improved', 'exchange_suspected'}
    assert not report['proven_window_airing']


def test_geodata_pack_counts_and_integrity():
    db = sqlite3.connect(f"file:{ROOT / 'assets' / 'geodata.sqlite'}?mode=ro&immutable=1", uri=True)
    assert db.execute('SELECT COUNT(*) FROM region').fetchone()[0] == 2054
    assert db.execute('SELECT COUNT(*) FROM alias').fetchone()[0] == 758
    assert db.execute('SELECT COUNT(*) FROM country').fetchone()[0] == 254
    samples = db.execute('SELECT geometry FROM region LIMIT 10').fetchall()
    for row in samples:
        payload = json.loads(lzma.decompress(row[0]))
        assert isinstance(payload, dict) and 'coordinates' in payload
    db.close()


def test_known_window_never_leaves_contact_confirmed_after_closing():
    m = pattern_module.RoomAirPattern()
    now = datetime(2026, 11, 4, tzinfo=timezone.utc)
    m.invalidate_for_open_window()
    assert m.summary(now=now, contact_open=True, passive_hint=False)["status"] == "contact_confirmed"
    closed = m.summary(now=now, contact_open=False, passive_hint=False)
    assert closed["status"] == "none"
    assert closed["proven_window_airing"] is False


def test_small_real_change_across_co2_or_humidity_limit_is_not_hidden():
    before = snapshot(green=True, open_window=False, minutes=None, humidity=59.9)
    after = snapshot(green=False, open_window=True, minutes=0.1, humidity=60,
                     active_reasons=("humidity",))
    assert not colors.protect_room_color(before, after, short_close=False, opening=True)
    before = snapshot(green=True, open_window=False, minutes=None, co2=1399)
    after = snapshot(green=False, open_window=True, minutes=0.1, co2=1400,
                     active_reasons=("co2_high",))
    assert not colors.protect_room_color(before, after, short_close=False, opening=True)


def test_report_moderate_quality_on_opening_is_real_worsening():
    before = snapshot(green=True, open_window=False, minutes=None)
    after = snapshot(green=False, open_window=True, minutes=0.01)
    after.values["indoor_air_quality"] = "moderate"
    after.result.active_reasons = ("indoor_air",)
    assert not colors.protect_room_color(before, after, short_close=False, opening=True)
    assert after.result.room_status_color == "orange"


def test_aborted_short_close_guard_holds_after_next_refresh_and_restart():
    guard = colors.ShortAiringColorGuard()
    prior = snapshot(green=False, open_window=True, minutes=2, co2=1400, humidity=62,
                     active_reasons=("humidity", "co2_high"))
    closing = snapshot(green=True, open_window=False, minutes=None, co2=650, humidity=62)
    guard.apply(prior, closing, short_close=True, opening=False, closing=True)
    assert closing.result.room_status_color == "orange"
    assert guard.as_dict() is not None
    followup = snapshot(green=True, open_window=False, minutes=None, co2=650, humidity=62)
    guard.apply(closing, followup, short_close=False, opening=False, closing=False)
    assert followup.result.room_status_color == "orange"
    restored = colors.ShortAiringColorGuard()
    restored.restore(guard.as_dict())
    after_restart = snapshot(green=True, open_window=False, minutes=None, co2=650, humidity=62)
    restored.apply(None, after_restart, short_close=False, opening=False, closing=False)
    assert after_restart.result.room_status_color == "orange"
    # Independently improved room air releases the guard; the short session
    # remains *unconfirmed* regardless of the later good air.
    improved = snapshot(green=True, open_window=False, minutes=None, co2=650, humidity=54)
    restored.apply(after_restart, improved, short_close=False, opening=False, closing=False)
    assert restored.as_dict() is None
    assert improved.result.room_status_color == "green"


def test_short_abort_with_non_numeric_reason_never_promotes_green():
    guard = colors.ShortAiringColorGuard()
    opening = snapshot(green=False, open_window=True, minutes=2, active_reasons=("routine",))
    closing = snapshot(green=True, open_window=False, minutes=None)
    guard.apply(opening, closing, short_close=True, opening=False, closing=True)
    assert closing.result.room_status_color == "orange"
    changed = snapshot(green=True, open_window=False, minutes=None, humidity=53)
    guard.apply(closing, changed, short_close=False, opening=False, closing=False)
    assert changed.result.room_status_color == "orange"


def test_short_airing_reserve_only_requires_sensors_that_exist():
    before = snapshot(green=False, open_window=True, minutes=2,
                      active_reasons=("co2_high",))
    after = snapshot(green=True, open_window=False, minutes=None)
    after.values["humidity_inside"] = None
    after.values["temperature_inside"] = None
    after.values["target_temperature"] = None
    assert colors.exceptional_short_airing_good(before, after)


def test_stable_good_rejects_frequent_large_co2_spikes():
    m = pattern_module.RoomAirPattern()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    for i in range(44):
        now = t0 + timedelta(minutes=20 * i)
        m.observe(now=now, source_stamp=now, co2=400 if i % 2 == 0 else 990,
                  humidity=50, temperature=22, window_open=False)
    assert not m.stable_good(now=t0 + timedelta(minutes=20 * 43))
    assert not m.stable_good(now=t0 + timedelta(minutes=20 * 43), passive_hint=True)


def test_passive_hint_requires_evidence_but_can_suppress_sooner():
    m = pattern_module.RoomAirPattern()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    for i in range(27):
        now = t0 + timedelta(minutes=20 * i)
        m.observe(now=now, source_stamp=now, co2=640,
                  humidity=50, temperature=22, window_open=False)
    assert not m.stable_good(now=t0 + timedelta(minutes=20 * 26))
    assert m.stable_good(now=t0 + timedelta(minutes=20 * 26), passive_hint=True)


def test_no_co2_observes_humidity_and_particles_but_does_not_claim_good_air():
    m = pattern_module.RoomAirPattern()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    assert m.observe(now=t0, source_stamp=t0, co2=None, humidity=57, temperature=22,
                     pollutants={"pm2_5": 15}, window_open=False)
    next_time = t0 + timedelta(minutes=20)
    assert m.observe(now=next_time, source_stamp=next_time, co2=None, humidity=52,
                     temperature=22, pollutants={"pm2_5": 9}, window_open=False)
    report = m.summary(now=next_time, contact_open=False, passive_hint=True)
    assert report["status"] == "air_improved"
    assert not report["stable_good_air"]
    restored = pattern_module.RoomAirPattern()
    restored.restore(m.as_dict(), now=next_time)
    assert len(restored.as_dict()["samples"]) == 2


def load_dataclasses(name):
    # Dataclass annotations need the module registered before exec_module.
    import sys
    spec = importlib.util.spec_from_file_location(f"isolated_{name}_dataclasses", ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_humidity_short_close_preserves_reason_across_refresh_and_restore():
    reason = load_dataclasses("reason_sessions")
    state = reason.HumiditySessionState()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    def step(now, *, is_open, rh=62, actionable=True, needed=True, airing_minutes=None):
        return state.evaluate(
            now=now, indoor_temp=22.0, indoor_rh=rh, indoor_ah=12.2,
            outdoor_ah=8.5, window_open=is_open, humidity_actionable=actionable,
            humidity_still_needed=needed, safety_lock=False, mold_risk=False,
            airing_minutes=airing_minutes,
        )
    started = step(t0, is_open=True, airing_minutes=0)
    assert started.session_active and not started.disarmed
    closed = step(t0 + timedelta(minutes=2), is_open=False, airing_minutes=2)
    assert not closed.session_active and not closed.disarmed
    assert state.short_aborted
    later = step(t0 + timedelta(minutes=7), is_open=False, airing_minutes=None)
    assert not later.disarmed and not later.session_active
    assert state.short_aborted
    saved = state.as_dict()
    restored = reason.HumiditySessionState()
    restored.restore(saved, parse_dt=lambda x: datetime.fromisoformat(x) if x else None)
    assert restored.short_aborted and not restored.disarmed


def test_humidity_uses_contact_duration_not_late_reason_start():
    reason = load_dataclasses("reason_sessions")
    state = reason.HumiditySessionState()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    state.evaluate(now=t0, indoor_temp=22.0, indoor_rh=62, indoor_ah=12,
                   outdoor_ah=8, window_open=True, humidity_actionable=True,
                   humidity_still_needed=True, safety_lock=False, mold_risk=False,
                   airing_minutes=4)
    closed = state.evaluate(now=t0 + timedelta(minutes=2), indoor_temp=22.0,
                            indoor_rh=54, indoor_ah=10.5, outdoor_ah=8, window_open=False,
                            humidity_actionable=True, humidity_still_needed=False,
                            safety_lock=False, mold_risk=False, airing_minutes=6)
    assert closed.disarmed and not closed.session_active and not state.short_aborted


def test_humidity_good_in_first_minutes_not_marked_complete():
    reason = load_dataclasses("reason_sessions")
    state = reason.HumiditySessionState()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    common = dict(indoor_temp=22.0, outdoor_ah=8, humidity_actionable=True,
                  safety_lock=False, mold_risk=False)
    state.evaluate(now=t0, indoor_rh=62, indoor_ah=12, window_open=True,
                   humidity_still_needed=True, airing_minutes=0, **common)
    early_good = state.evaluate(now=t0+timedelta(minutes=2), indoor_rh=54,
                                indoor_ah=10.8, window_open=True,
                                humidity_still_needed=False, airing_minutes=2, **common)
    assert early_good.session_active and not early_good.disarmed
    closed = state.evaluate(now=t0+timedelta(minutes=3), indoor_rh=54,
                            indoor_ah=10.8, window_open=False,
                            humidity_still_needed=False, airing_minutes=3, **common)
    assert not closed.session_active and not closed.disarmed
    assert state.short_aborted is False  # independently good RH clears abort memory


def test_five_minute_humidity_close_without_improvement_keeps_reason_armed():
    reason = load_dataclasses("reason_sessions")
    state = reason.HumiditySessionState()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)

    def step(minutes, *, open_window):
        return state.evaluate(
            now=t0 + timedelta(minutes=minutes),
            indoor_temp=22.0, indoor_rh=62.0, indoor_ah=12.2,
            outdoor_ah=8.5, window_open=open_window,
            humidity_actionable=True, humidity_still_needed=True,
            safety_lock=False, mold_risk=False,
            airing_minutes=minutes if open_window or minutes == 5.1 else None,
        )

    assert step(0, open_window=True).session_active
    assert step(5.0, open_window=True).session_active
    closed = step(5.1, open_window=False)
    assert not closed.session_active
    assert not closed.disarmed and not closed.exhausted
    assert not state.short_aborted  # Duration confirmed, but effect NOT confirmed.
    assert state.unresolved_close
    later = step(5.5, open_window=False)
    assert not later.disarmed and not later.exhausted
    restored = reason.HumiditySessionState()
    restored.restore(state.as_dict(), parse_dt=lambda value: datetime.fromisoformat(value) if value else None)
    assert not restored.disarmed and restored.unresolved_close
    assert not restored.evaluate(
        now=t0 + timedelta(minutes=10), indoor_temp=22, indoor_rh=62,
        indoor_ah=12.2, outdoor_ah=8.5, window_open=False,
        humidity_actionable=True, humidity_still_needed=True,
        safety_lock=False, mold_risk=False,
    ).disarmed


def test_five_minute_unresolved_humidity_color_stays_non_green_after_refresh_restart():
    guard = colors.ShortAiringColorGuard()
    before = snapshot(green=False, open_window=True, minutes=5.1,
                      humidity=62, active_reasons=("humidity",))
    closing = snapshot(green=True, open_window=False, minutes=None, humidity=62,
                       active_reasons=("humidity",))
    assert guard.apply(before, closing, short_close=False, opening=False, closing=True,
                       unresolved_humidity_close=True, unresolved_humidity_active=True)
    assert closing.result.room_status_color == "orange"
    assert guard.as_dict()["humidity_unresolved"]
    for minute in (6, 60, 180):
        unchanged = snapshot(green=True, open_window=False, minutes=None, humidity=62,
                             active_reasons=("humidity",))
        assert guard.apply(closing, unchanged, short_close=False, opening=False, closing=False,
                           unresolved_humidity_active=True)
        assert unchanged.result.room_status_color == "orange"
        closing = unchanged
    restored = colors.ShortAiringColorGuard()
    restored.restore(guard.as_dict())
    after_restart = snapshot(green=True, open_window=False, minutes=None,
                             humidity=62, active_reasons=("humidity",))
    assert restored.apply(None, after_restart, short_close=False, opening=False, closing=False,
                          unresolved_humidity_active=True)
    assert after_restart.result.room_status_color == "orange"
    # After five minutes there is *no additional* 15% gate. Normal recovery
    # ends the reason when humidity has really fallen and evaluation agrees.
    improved = snapshot(green=True, open_window=False, minutes=None,
                        humidity=59, active_reasons=())
    restored.apply(after_restart, improved, short_close=False, opening=False,
                   closing=False, unresolved_humidity_active=False)
    assert restored.as_dict() is None
    assert improved.result.room_status_color == "green"


def test_five_minute_humidity_close_after_real_recovery_is_complete():
    reason = load_dataclasses("reason_sessions")
    state = reason.HumiditySessionState()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    common = dict(indoor_temp=22, outdoor_ah=8.5, humidity_actionable=True,
                  safety_lock=False, mold_risk=False)
    state.evaluate(now=t0, indoor_rh=62, indoor_ah=12.2, window_open=True,
                   humidity_still_needed=True, airing_minutes=0, **common)
    recovered = state.evaluate(now=t0+timedelta(minutes=5), indoor_rh=54,
                               indoor_ah=10.5, window_open=False,
                               humidity_still_needed=False, airing_minutes=5, **common)
    assert recovered.disarmed and not recovered.session_active
    assert not state.unresolved_close


def test_observation_suspicion_expires_but_contact_evidence_is_live():
    pattern = pattern_module.RoomAirPattern()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    assert pattern.observe(now=t0, source_stamp=t0, co2=1400,
                           humidity=50, temperature=22, window_open=False)
    t1 = t0 + timedelta(minutes=20)
    assert pattern.observe(now=t1, source_stamp=t1, co2=600,
                           humidity=49, temperature=22, window_open=False)
    assert pattern.summary(now=t1, contact_open=False, passive_hint=False)["status"] == "exchange_suspected"
    assert pattern.next_observation_check(now=t1) == 3600
    assert pattern.summary(now=t1+timedelta(minutes=59), contact_open=False,
                           passive_hint=False)["status"] == "exchange_suspected"
    assert pattern.summary(now=t1+timedelta(minutes=61), contact_open=False,
                           passive_hint=False)["status"] == "none"
    assert pattern.next_observation_check(now=t1+timedelta(minutes=61)) is None
    assert pattern.summary(now=t1+timedelta(minutes=1480), contact_open=False,
                           passive_hint=False)["status"] == "none"
    assert pattern.summary(now=t1+timedelta(minutes=1480), contact_open=True,
                           passive_hint=False)["status"] == "contact_confirmed"
    # No change to bounded measurement history or the 24-hour routine logic.
    assert len(pattern.as_dict()["samples"]) == 2


def test_air_improved_status_also_expires_without_new_samples():
    pattern = pattern_module.RoomAirPattern()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    pattern.observe(now=t0, source_stamp=t0, co2=820,
                    humidity=58, temperature=22, window_open=False)
    t1 = t0 + timedelta(minutes=20)
    pattern.observe(now=t1, source_stamp=t1, co2=820,
                    humidity=56, temperature=22, window_open=False)
    assert pattern.summary(now=t1, contact_open=False, passive_hint=False)["status"] == "air_improved"
    assert pattern.summary(now=t1+timedelta(minutes=61), contact_open=False,
                           passive_hint=False)["status"] == "none"


def test_sustained_good_but_stale_co2_cannot_suppress_routine():
    m = pattern_module.RoomAirPattern()
    t0 = datetime(2026, 11, 4, tzinfo=timezone.utc)
    for i in range(44):
        now = t0 + timedelta(minutes=20*i)
        m.observe(now=now, source_stamp=now, co2=640, humidity=50,
                  temperature=22, window_open=False)
    now = t0 + timedelta(minutes=20*43)
    assert m.stable_good(now=now)
    assert not m.stable_good(now=now, co2_fresh=False)
    assert not m.summary(now=now, contact_open=False, passive_hint=True,
                         co2_fresh=False)['stable_good_air']


def test_short_guard_does_not_hide_new_mold_reason():
    before = snapshot(green=True, open_window=False, minutes=None)
    current = snapshot(green=False, open_window=True, minutes=0)
    current.result.mold_risk = True
    assert not colors.protect_room_color(before, current, short_close=False, opening=True)

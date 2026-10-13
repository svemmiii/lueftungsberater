"""v0.11.4 COMPLETE(10): independent safety TTLs and mobile weather drift."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _extract
from test_v0114_complete9_active_source_transition_pure import (
    AUTO_ID, MANUAL_WARNING_ID, MANUAL_ENTITY, _live, _setup,
)
from test_v0114_complete4_safety_pure import BASE, MOW


def _persist(apply, hass, entry, assessment):
    asyncio.run(apply(hass, entry, SimpleNamespace(), assessment))


def _records(disk):
    return {part["id"]: part for part in disk["channels"]["warning"]["warning_records"]}


def test_new_manual_hazard_survives_old_automatic_outage_and_has_own_ttl():
    clock, apply, disk, volatile, states, hass, entry = _setup()
    _persist(apply, hass, entry, _live(automatic=True))
    old_until = _records(disk)[AUTO_ID]["valid_until"]
    clock[0] += timedelta(minutes=55)
    states[MANUAL_ENTITY] = SimpleNamespace(state="on", attributes={"id": MANUAL_WARNING_ID})
    fresh = _live(manual=True)
    fresh.provider_availability = {BASE: False, MOW: False}
    _persist(apply, hass, entry, fresh)
    saved = _records(disk)
    assert set(saved) == {AUTO_ID, MANUAL_WARNING_ID}
    assert saved[AUTO_ID]["valid_until"] == old_until
    assert datetime.fromisoformat(saved[MANUAL_WARNING_ID]["valid_until"]) == clock[0] + timedelta(hours=1)
    # Both providers now fail. The new danger must last beyond the old TTL.
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    volatile.clear()
    clock[0] += timedelta(minutes=6)
    unavailable = _live()
    unavailable.provider_availability = {BASE: False, MOW: False}
    _persist(apply, hass, entry, unavailable)
    assert unavailable.nina_status == "danger"
    assert set(_records(disk)) == {MANUAL_WARNING_ID}
    # There is no indefinite extension from a different hazard.
    volatile.clear()
    clock[0] += timedelta(minutes=55)
    final = _live()
    final.provider_availability = {BASE: False, MOW: False}
    _persist(apply, hass, entry, final)
    assert "warning" not in disk["channels"]


def test_new_automatic_hazard_survives_old_manual_outage_and_has_own_ttl():
    clock, apply, disk, volatile, states, hass, entry = _setup()
    states[MANUAL_ENTITY] = SimpleNamespace(state="on", attributes={"id": MANUAL_WARNING_ID})
    _persist(apply, hass, entry, _live(manual=True))
    old_until = _records(disk)[MANUAL_WARNING_ID]["valid_until"]
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    clock[0] += timedelta(minutes=55)
    _persist(apply, hass, entry, _live(automatic=True))
    saved = _records(disk)
    assert set(saved) == {AUTO_ID, MANUAL_WARNING_ID}
    assert saved[MANUAL_WARNING_ID]["valid_until"] == old_until
    volatile.clear()
    clock[0] += timedelta(minutes=6)
    unknown = _live()
    unknown.provider_availability = {BASE: False, MOW: False}
    _persist(apply, hass, entry, unknown)
    assert unknown.nina_status == "danger"
    assert set(_records(disk)) == {AUTO_ID}
    volatile.clear()
    clock[0] += timedelta(minutes=55)
    final = _live()
    final.provider_availability = {BASE: False, MOW: False}
    _persist(apply, hass, entry, final)
    assert "warning" not in disk["channels"]


def test_legacy_storage_migrates_without_resetting_original_deadlines():
    clock, apply, disk, volatile, states, hass, entry = _setup()
    _persist(apply, hass, entry, _live(automatic=True))
    disk["channels"]["warning"].pop("warning_records")
    original_until = disk["channels"]["warning"]["valid_until"]
    volatile.clear()
    clock[0] += timedelta(minutes=50)
    unavailable = _live()
    unavailable.provider_availability = {BASE: False, MOW: False}
    _persist(apply, hass, entry, unavailable)
    assert _records(disk)[AUTO_ID]["valid_until"] == original_until


def test_routine_gps_drift_and_failed_weather_fetch_cannot_release_guard():
    scope = _extract("safety_state.py", {"_weather_provider_availability"}, {
        "CONF_WEATHER": "weather", "_state_unknown": lambda value: value is None,
    })
    evaluate = scope["_weather_provider_availability"]
    previous_key = "auto_weather:50.7000:7.1000"
    changed = "auto_weather:50.7001:7.1000"
    old = {"source_key": previous_key, "last_confirmed_at": "2026-10-12T15:00:00+00:00"}
    weather = SimpleNamespace(safety_source_key=changed, provider_available=False,
                              weather_hard_lock=False)
    assert evaluate(SimpleNamespace(), SimpleNamespace(data={}), weather, old) == ("unknown", previous_key)
    weather.provider_available = None
    assert evaluate(SimpleNamespace(), SimpleNamespace(data={}), weather, old) == ("unknown", previous_key)
    weather.provider_available = True
    assert evaluate(SimpleNamespace(), SimpleNamespace(data={}), weather, old)[0] == "clear"


def test_one_live_auto_alert_cannot_extend_second_failed_auto_feed():
    """Multiple automatic NINA alerts keep their own clocks, not the strongest's."""
    from test_v0114_complete2_pure import _provider
    from test_v0114_complete4_safety_pure import _persistence_environment
    clock = [datetime(2026, 10, 12, 15, tzinfo=timezone.utc)]
    apply, disk, volatile = _persistence_environment(clock_ref=clock)
    entry = SimpleNamespace(entry_id="several-nina-providers", data={})
    hass = SimpleNamespace()
    A = _provider()["WarningAssessment"]
    def report(*, smoke: bool, chemicals: bool, police_ready: bool):
        ids = ({"mow.smoke"} if smoke else set()) | ({"pol.chem"} if chemicals else set())
        return A(
            nina_status="danger" if ids else "none",
            official_close_instruction=bool(ids),
            nina_reason_key="nina_air_danger", safety_source_key=MOW if ids else BASE,
            provider_domain="nina_auto", warning_ids=ids,
            warning_origins={ident: f"auto:{BASE}" for ident in ids},
            provider_availability={BASE: False, MOW: True,
                                   f"{BASE}:nina_auto_police": police_ready},
        )
    _persist(apply, hass, entry, report(smoke=True, chemicals=True, police_ready=True))
    original = _records(disk)["pol.chem"]["valid_until"]
    clock[0] += timedelta(minutes=50)
    volatile.clear()
    _persist(apply, hass, entry, report(smoke=True, chemicals=False, police_ready=False))
    records = _records(disk)
    assert records["pol.chem"]["valid_until"] == original
    assert records["mow.smoke"]["valid_until"] == (clock[0] + timedelta(hours=1)).isoformat()
    clock[0] += timedelta(minutes=11)
    volatile.clear()
    _persist(apply, hass, entry, report(smoke=True, chemicals=False, police_ready=False))
    assert set(_records(disk)) == {"mow.smoke"}

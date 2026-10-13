"""COMPLETE(9): an active new warning always replaces a cleared old source."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _provider, _safety
from test_v0114_complete4_safety_pure import BASE, MOW, _persistence_environment

MANUAL_ID = "nina-manual-entry"
MANUAL_ENTITY = "binary_sensor.manual_nina_warning"
AUTO_ID = "mow.old-smoke"
MANUAL_WARNING_ID = "pol.new-chemical"


def _live(*, automatic=False, manual=False):
    scope = _provider()
    assess = scope["WarningAssessment"]
    auto = assess(
        nina_status="danger" if automatic else "none",
        official_close_instruction=automatic,
        nina_reason_key="nina_air_danger",
        safety_source_key=MOW if automatic else BASE,
        provider_domain="nina_auto",
        warning_ids={AUTO_ID} if automatic else set(),
        warning_origins={AUTO_ID: f"auto:{BASE}"} if automatic else {},
        provider_availability={BASE: True, MOW: True, f"{BASE}:nina_auto_dashboard": True},
    )
    other = assess(
        nina_status="danger" if manual else "none",
        official_close_instruction=manual,
        nina_reason_key="nina_air_danger",
        safety_source_key=MANUAL_ID,
        provider_domain="nina",
        source_nina_entity=MANUAL_ENTITY if manual else None,
        warning_ids={MANUAL_WARNING_ID} if manual else set(),
        warning_origins={MANUAL_WARNING_ID: f"manual:{MANUAL_ID}"} if manual else {},
    )
    return scope["_merge_warning_assessments"](auto, other)


def _setup():
    clock = [datetime(2026, 10, 12, 15, tzinfo=timezone.utc)]
    apply, disk, volatile = _persistence_environment(
        clock_ref=clock, manual_entity_ids=[MANUAL_ENTITY]
    )
    states = {MANUAL_ENTITY: SimpleNamespace(state="off", attributes={})}
    hass = SimpleNamespace(
        states=SimpleNamespace(get=states.get),
        config_entries=SimpleNamespace(async_get_entry=lambda ident: (
            SimpleNamespace(entry_id=MANUAL_ID, domain="nina")
            if ident == MANUAL_ID else None
        )),
    )
    entry = SimpleNamespace(entry_id="mixed-source-swap", data={"warning_source": MANUAL_ID})
    return clock, apply, disk, volatile, states, hass, entry


def test_auto_clears_same_cycle_as_manual_danger_then_manual_fails_after_restart():
    clock, apply, disk, volatile, states, hass, entry = _setup()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _live(automatic=True)))
    assert disk["channels"]["warning"]["warning_ids"] == [AUTO_ID]
    assert disk["channels"]["warning"]["source_key"] == MOW

    # The old MoWaS danger is conclusively gone. At the very same refresh,
    # the configured manual NINA reports a fresh hard-close instruction.
    clock[0] += timedelta(minutes=1)
    states[MANUAL_ENTITY] = SimpleNamespace(
        state="on", attributes={"id": MANUAL_WARNING_ID}
    )
    manual = _live(manual=True)
    asyncio.run(apply(hass, entry, SimpleNamespace(), manual))
    assert manual.nina_status == "danger"
    assert disk["channels"]["warning"]["source_key"] == MANUAL_ID
    assert disk["channels"]["warning"]["warning_ids"] == [MANUAL_WARNING_ID]
    assert disk["channels"]["warning"]["warning_components"] == [
        {"id": MANUAL_WARNING_ID, "origin": f"manual:{MANUAL_ID}", "cap": ""}
    ]
    confirmed = disk["channels"]["warning"]["last_confirmed_at"]

    # Restore from disk with the manual source unavailable. The previous
    # verified manual warning must still close windows, with its ORIGINAL TTL.
    volatile.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    clock[0] += timedelta(minutes=2)
    unavailable = _live()
    asyncio.run(apply(hass, entry, SimpleNamespace(), unavailable))
    assert unavailable.nina_status == "danger"
    assert unavailable.official_close_instruction is True
    assert disk["channels"]["warning"]["source_key"] == MANUAL_ID
    assert disk["channels"]["warning"]["last_confirmed_at"] == confirmed

    # A recovered source that now definitively reports OFF may retire it.
    volatile.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="off", attributes={})
    asyncio.run(apply(hass, entry, SimpleNamespace(), _live()))
    assert "warning" not in disk["channels"]


def test_new_manual_warning_fallback_expires_not_perpetually_renewed():
    clock, apply, disk, volatile, states, hass, entry = _setup()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _live(automatic=True)))
    clock[0] += timedelta(minutes=1)
    states[MANUAL_ENTITY] = SimpleNamespace(state="on", attributes={"id": MANUAL_WARNING_ID})
    asyncio.run(apply(hass, entry, SimpleNamespace(), _live(manual=True)))
    confirmed = disk["channels"]["warning"]["last_confirmed_at"]
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    for minutes in (10, 40, 59):
        clock[0] = datetime.fromisoformat(confirmed) + timedelta(minutes=minutes)
        volatile.clear()
        asyncio.run(apply(hass, entry, SimpleNamespace(), _live()))
        assert disk["channels"]["warning"]["last_confirmed_at"] == confirmed
    clock[0] = datetime.fromisoformat(confirmed) + timedelta(minutes=61)
    volatile.clear()
    old = _live()
    asyncio.run(apply(hass, entry, SimpleNamespace(), old))
    assert old.nina_status == "none"
    assert "warning" not in disk["channels"]


def test_bare_manual_key_or_info_is_not_taken_as_a_confirmed_new_danger():
    checker = _safety()["_warning_provider_availability"]
    clock, apply, disk, volatile, states, hass, entry = _setup()
    _ = (clock, apply, disk, volatile, states)
    previous = {"source_key": MOW, "warning_ids": [AUTO_ID]}
    no_danger = _live()
    no_danger.safety_source_key = MANUAL_ID
    assert checker(hass, entry, no_danger, previous)[0] == "clear"
    from_missing_source = _live(manual=True)
    missing_hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_get_entry=lambda _: None)
    )
    assert checker(missing_hass, entry, from_missing_source, previous)[0] != "active"

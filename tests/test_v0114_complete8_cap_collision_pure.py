"""COMPLETE(8): duplicate CAP identifiers across auto and manual cannot drop protection."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _provider
from test_v0114_complete4_safety_pure import BASE, MOW, _persistence_environment

MANUAL_ID = "manual-nina-entry"
MANUAL_ENTITY = "binary_sensor.manual_warning"
COLLISION_ID = "mow.same-id"
ISSUED_A = "authority-a|2026-10-11T17:00:00+00:00"
ISSUED_B = "authority-b|2026-10-11T18:00:00+00:00"


def _build(*, automatic=True, manual=True):
    scope = _provider()
    A = scope["WarningAssessment"]
    auto = A(
        nina_status="danger" if automatic else "none",
        official_close_instruction=automatic, nina_reason_key="nina_air_danger",
        safety_source_key=MOW, provider_domain="nina_auto",
        warning_ids={COLLISION_ID} if automatic else set(),
        warning_origins={COLLISION_ID: f"auto:{BASE}"} if automatic else {},
        warning_cap_identities={COLLISION_ID: {ISSUED_A}} if automatic else {},
        provider_availability={BASE: True, MOW: True},
    )
    other = A(
        nina_status="danger" if manual else "none",
        official_close_instruction=manual, nina_reason_key="nina_air_danger",
        safety_source_key=MANUAL_ID, provider_domain="nina",
        source_nina_entity=MANUAL_ENTITY,
        warning_ids={COLLISION_ID} if manual else set(),
        warning_origins={COLLISION_ID: f"manual:{MANUAL_ID}"} if manual else {},
        warning_cap_identities={COLLISION_ID: {ISSUED_B}} if manual else {},
    )
    if (automatic and manual) or (not automatic and not manual):
        return scope["_merge_warning_assessments"](auto, other)
    return auto if automatic else other


def _scenario():
    clock = [datetime(2026, 10, 11, 18, tzinfo=timezone.utc)]
    apply, disk, memory = _persistence_environment(
        clock_ref=clock, manual_entity_ids=[MANUAL_ENTITY]
    )
    states = {MANUAL_ENTITY: SimpleNamespace(state="on", attributes={"id": COLLISION_ID})}
    hass = SimpleNamespace(
        states=SimpleNamespace(get=states.get),
        config_entries=SimpleNamespace(async_get_entry=lambda ident: (
            SimpleNamespace(entry_id=MANUAL_ID, domain="nina")
            if ident == MANUAL_ID else None
        )),
    )
    entry = SimpleNamespace(entry_id="two-cap-authorities", data={"warning_source": MANUAL_ID})
    return clock, apply, disk, memory, states, hass, entry


def test_collision_survives_manual_outage_and_restart_then_both_resolve():
    clock, apply, disk, memory, states, hass, entry = _scenario()
    together = _build()
    assert together.warning_ids == {COLLISION_ID}
    assert len(together.warning_components) == 2
    assert {row["cap"] for row in together.warning_components} == {ISSUED_A, ISSUED_B}
    asyncio.run(apply(hass, entry, SimpleNamespace(), together))
    record = disk["channels"]["warning"]
    assert len(record["warning_components"]) == 2
    assert {item["origin"] for item in record["warning_components"]} == {
        f"auto:{BASE}", f"manual:{MANUAL_ID}"
    }
    initial_confirmation = record["last_confirmed_at"]

    # One path goes unavailable, but the other continues reporting a live
    # warning with *the same short ID*. Formerly this removed the manual one.
    memory.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    clock[0] += timedelta(minutes=2)
    asyncio.run(apply(hass, entry, SimpleNamespace(), _build(manual=False)))
    assert len(disk["channels"]["warning"]["warning_components"]) == 2
    assert disk["channels"]["warning"]["last_confirmed_at"] == initial_confirmation

    # Active auto danger ceases; the lost manual CAP danger must still protect
    # the room until its independently bounded fallback ends or gets checked.
    memory.clear()
    clock[0] += timedelta(minutes=2)
    unknown = _build(automatic=False, manual=False)
    asyncio.run(apply(hass, entry, SimpleNamespace(), unknown))
    assert unknown.nina_status == "danger"
    # The successfully rechecked automatic warning has ended. Only the
    # separately unavailable manual CAP warning remains in the fallback.
    assert len(disk["channels"]["warning"]["warning_components"]) == 1
    assert disk["channels"]["warning"]["warning_components"][0]["cap"] == ISSUED_B

    # A trustworthy manual OFF + complete automatic clear can retire both.
    states[MANUAL_ENTITY] = SimpleNamespace(state="off", attributes={})
    memory.clear()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _build(automatic=False, manual=False)))
    assert "warning" not in disk["channels"]


def test_collision_outage_expires_without_unrelated_auto_extending_it():
    clock, apply, disk, memory, states, hass, entry = _scenario()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _build()))
    initial = disk["channels"]["warning"]["last_confirmed_at"]
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    for minutes in (20, 40, 59):
        memory.clear()
        clock[0] = datetime(2026, 10, 11, 18, tzinfo=timezone.utc) + timedelta(minutes=minutes)
        asyncio.run(apply(hass, entry, SimpleNamespace(), _build(manual=False)))
        assert disk["channels"]["warning"]["last_confirmed_at"] == initial
    memory.clear()
    clock[0] += timedelta(minutes=2)
    live = _build(manual=False)
    asyncio.run(apply(hass, entry, SimpleNamespace(), live))
    assert len(disk["channels"]["warning"]["warning_components"]) == 1
    assert disk["channels"]["warning"]["warning_components"][0]["cap"] == ISSUED_A


def test_old_storage_format_without_components_remains_readable():
    clock, apply, disk, memory, states, hass, entry = _scenario()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _build()))
    disk["channels"]["warning"].pop("warning_components")
    memory.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    asyncio.run(apply(hass, entry, SimpleNamespace(), _build(manual=False)))
    assert "warning" in disk["channels"]

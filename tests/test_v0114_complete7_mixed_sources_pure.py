"""COMPLETE(7): mixed NINA sources retain unknown hazards with bounded TTL."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _provider
from test_v0114_complete4_safety_pure import BASE, MOW, _persistence_environment

MANUAL_ID = "manual-nina-entry"
MANUAL_ENTITY = "binary_sensor.manual_nina_warning"
MANUAL_WARNING = "pol.manual-smoke"
AUTO_WARNING = "mow.auto-chemical"


def _warnings(manual=True, *, strongest_manual=True):
    scope = _provider()
    cls = scope["WarningAssessment"]
    auto = cls(
        nina_status="danger", official_close_instruction=True,
        nina_reason_key="nina_air_danger", safety_source_key=MOW,
        provider_domain="nina_auto",
        warning_ids={AUTO_WARNING},
        warning_origins={AUTO_WARNING: f"auto:{BASE}"},
        provider_availability={BASE: True, MOW: True},
    )
    if not manual:
        return auto
    other = cls(
        nina_status="danger", official_close_instruction=True,
        nina_reason_key="nina_air_danger", safety_source_key=MANUAL_ID,
        provider_domain="nina", source_nina_entity=MANUAL_ENTITY,
        warning_ids={MANUAL_WARNING},
        warning_origins={MANUAL_WARNING: f"manual:{MANUAL_ID}"},
    )
    if not strongest_manual:
        # Test a persisted *automatic* primary even while manual hazards exist.
        original_merge = scope["_merge_warning_assessments"](auto, other)
        original_merge.safety_source_key = MOW
        return original_merge
    return scope["_merge_warning_assessments"](auto, other)


def _setup(*, strongest_manual=True):
    clock = [datetime(2026, 10, 11, 18, tzinfo=timezone.utc)]
    apply, disk, volatile = _persistence_environment(
        clock_ref=clock, manual_entity_ids=[MANUAL_ENTITY]
    )
    states = {MANUAL_ENTITY: SimpleNamespace(state="on", attributes={"id": MANUAL_WARNING})}
    hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda entity: states.get(entity)),
        config_entries=SimpleNamespace(async_get_entry=lambda ident: (
            SimpleNamespace(entry_id=MANUAL_ID, domain="nina") if ident == MANUAL_ID else None
        )),
    )
    entry = SimpleNamespace(entry_id="mixed-sources", data={"warning_source": MANUAL_ID})
    both = _warnings(strongest_manual=strongest_manual)
    asyncio.run(apply(hass, entry, SimpleNamespace(), both))
    assert set(disk["channels"]["warning"]["warning_ids"]) == {MANUAL_WARNING, AUTO_WARNING}
    assert disk["channels"]["warning"]["warning_origins"] == {
        MANUAL_WARNING: f"manual:{MANUAL_ID}", AUTO_WARNING: f"auto:{BASE}"
    }
    return apply, disk, volatile, states, hass, entry, clock


def test_mixed_source_manual_outage_does_not_erase_persisted_hazard_after_restart():
    apply, disk, volatile, states, hass, entry, clock = _setup()
    volatile.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    still_auto = _warnings(manual=False)
    asyncio.run(apply(hass, entry, SimpleNamespace(), still_auto))
    assert set(disk["channels"]["warning"]["warning_ids"]) == {MANUAL_WARNING, AUTO_WARNING}
    initial_confirmation = disk["channels"]["warning"]["last_confirmed_at"]
    clock[0] += timedelta(minutes=50)
    volatile.clear()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _warnings(manual=False)))
    assert disk["channels"]["warning"]["last_confirmed_at"] == initial_confirmation
    assert set(disk["channels"]["warning"]["warning_ids"]) == {MANUAL_WARNING, AUTO_WARNING}


def test_mixed_source_old_primary_auto_also_keeps_offline_manual_hazard():
    apply, disk, volatile, states, hass, entry, _ = _setup(strongest_manual=False)
    volatile.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="unknown", attributes={})
    asyncio.run(apply(hass, entry, SimpleNamespace(), _warnings(manual=False)))
    assert set(disk["channels"]["warning"]["warning_ids"]) == {MANUAL_WARNING, AUTO_WARNING}


def test_known_manual_recovery_can_narrow_persisted_hazards():
    apply, disk, volatile, states, hass, entry, _ = _setup()
    volatile.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="off", attributes={})
    asyncio.run(apply(hass, entry, SimpleNamespace(), _warnings(manual=False)))
    assert disk["channels"]["warning"]["warning_ids"] == [AUTO_WARNING]


def test_unresolved_manual_hazard_expires_without_other_feed_refreshing_it():
    apply, disk, volatile, states, hass, entry, clock = _setup()
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    volatile.clear()
    clock[0] += timedelta(minutes=61)
    still_auto = _warnings(manual=False)
    asyncio.run(apply(hass, entry, SimpleNamespace(), still_auto))
    assert still_auto.official_close_instruction  # A *new live* hazard still locks.
    assert disk["channels"]["warning"]["warning_ids"] == [AUTO_WARNING]


def test_legacy_mixed_record_without_warning_origins_keeps_unknown_manual():
    apply, disk, volatile, states, hass, entry, _ = _setup()
    disk["channels"]["warning"].pop("warning_origins")
    states[MANUAL_ENTITY] = SimpleNamespace(state="unavailable", attributes={})
    volatile.clear()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _warnings(manual=False)))
    assert set(disk["channels"]["warning"]["warning_ids"]) == {MANUAL_WARNING, AUTO_WARNING}


def test_manual_slot_still_on_without_details_remains_unresolved():
    apply, disk, volatile, states, hass, entry, _ = _setup()
    volatile.clear()
    # Valid ON state, but the detailed official closure text failed to load.
    states[MANUAL_ENTITY] = SimpleNamespace(state="on", attributes={"id": MANUAL_WARNING})
    asyncio.run(apply(hass, entry, SimpleNamespace(), _warnings(manual=False)))
    assert set(disk["channels"]["warning"]["warning_ids"]) == {MANUAL_WARNING, AUTO_WARNING}


def test_manual_slot_on_with_unidentified_alert_is_not_an_all_clear():
    apply, disk, volatile, states, hass, entry, _ = _setup()
    volatile.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="on", attributes={})
    asyncio.run(apply(hass, entry, SimpleNamespace(), _warnings(manual=False)))
    assert set(disk["channels"]["warning"]["warning_ids"]) == {MANUAL_WARNING, AUTO_WARNING}


def test_manual_clears_but_unavailable_auto_remains_independently_protected():
    apply, disk, volatile, states, hass, entry, _ = _setup()
    volatile.clear()
    states[MANUAL_ENTITY] = SimpleNamespace(state="off", attributes={})
    none = _provider()["WarningAssessment"](
        safety_source_key=BASE, provider_domain="nina_auto+nina",
        provider_availability={BASE: False, MOW: False},
    )
    asyncio.run(apply(hass, entry, SimpleNamespace(), none))
    assert none.nina_status == "danger"
    # The manual sensor is explicitly OFF: its warning must be retired without
    # also releasing the unrelated and still-unverifiable automatic hazard.
    assert set(disk["channels"]["warning"]["warning_ids"]) == {AUTO_WARNING}
    volatile.clear()
    confirmed = _provider()["WarningAssessment"](
        safety_source_key=BASE, provider_domain="nina_auto+nina",
        provider_availability={BASE: True, MOW: True},
    )
    asyncio.run(apply(hass, entry, SimpleNamespace(), confirmed))
    assert "warning" not in disk["channels"]


def test_provider_adapters_preserve_per_warning_origin_before_merge():
    scope = _provider()
    now = datetime(2026, 10, 11, 18, tzinfo=timezone.utc)
    warning = SimpleNamespace(
        expires=None, effective=None, event="Rauch", description="Rauch in Umgebung",
        headline="Rauch", instruction="Fenster und Türen schließen", msg_type="Alert",
        references="", warning_id=AUTO_WARNING, provider_domain="nina_auto_mowas",
        category="civil", severity="Severe", sender="amt-a@example.org",
        issued_at=now, evidence_at=now,
    )
    data = SimpleNamespace(
        safety_source_key=BASE, provider_domain="nina_auto", coverage="civil_and_weather",
        error=None, region_ars="053820000000", active_sources=["nina_auto_mowas"],
        source_availability={"nina_auto_mowas": True}, available=True, warnings=[warning],
    )
    scope["auto_warning_data"] = lambda *args: data
    automatic = scope["_automatic_warning_assessment"](SimpleNamespace(), SimpleNamespace(data={}))
    assert automatic.warning_origins == {AUTO_WARNING: f"auto:{BASE}"}

    state = SimpleNamespace(state="on", attributes={
        "id": MANUAL_WARNING, "headline": "Rauch", "description": "Rauch in Umgebung",
        "recommended_actions": "Fenster und Türen schließen",
    })
    scope["_config_entry_entities"] = lambda *args: [MANUAL_ENTITY]
    scope["_nina_slot_sensor_values"] = lambda *args: {}
    scope["_cached_nina_record"] = lambda *args: {}
    scope["_text"] = lambda obj, key: str(obj.attributes.get(key) or "")
    hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda entity: state),
        config_entries=SimpleNamespace(async_get_entry=lambda _: SimpleNamespace(
            entry_id=MANUAL_ID, domain="nina"
        )),
    )
    manual = scope["_manual_warning_assessment"](
        hass, SimpleNamespace(data={"warning_source": MANUAL_ID})
    )
    assert manual.warning_origins == {MANUAL_WARNING: f"manual:{MANUAL_ID}"}
    merged = scope["_merge_warning_assessments"](automatic, manual)
    assert merged.warning_origins == {
        AUTO_WARNING: f"auto:{BASE}", MANUAL_WARNING: f"manual:{MANUAL_ID}"
    }

"""COMPLETE(11): actual manual NINA slots, weather source, independent resolution."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _extract, _provider
from test_v0114_complete4_safety_pure import BASE, MOW, _persistence_environment

MANUAL = "manual-nina-entry"
SLOT_A = "binary_sensor.nina_warning_1"
SLOT_B = "binary_sensor.nina_warning_2"
ID_A = "mow.smoke-a"
ID_B = "mow.chemical-b"


def _setup_manual():
    clock = [datetime(2026, 10, 12, 15, tzinfo=timezone.utc)]
    apply, disk, volatile = _persistence_environment(clock_ref=clock, manual_entity_ids=[SLOT_A, SLOT_B])
    statuses = {
        SLOT_A: SimpleNamespace(state="on", attributes={
            "id": ID_A, "headline": "Rauch", "description": "Rauchentwicklung",
            "recommended_actions": "Schließen Sie Fenster und Türen.",
            "sender": "a@example.org", "sent": "2026-10-12T12:00:00Z",
        }),
        SLOT_B: SimpleNamespace(state="on", attributes={
            "id": ID_B, "headline": "Chemikalien", "description": "Chemikalien in der Luft",
            "recommended_actions": "Schließen Sie Fenster und Türen.",
            "sender": "b@example.org", "sent": "2026-10-12T12:15:00Z",
        }),
    }
    hass = SimpleNamespace(
        states=SimpleNamespace(get=statuses.get),
        config_entries=SimpleNamespace(async_get_entry=lambda ident: (
            SimpleNamespace(entry_id=MANUAL, domain="nina") if ident == MANUAL else None
        )),
    )
    entry = SimpleNamespace(entry_id="two-manual-slots", data={"warning_source": MANUAL})
    scope = _provider()
    scope["_nina_slot_sensor_values"] = lambda *_: {}
    scope["_cached_nina_record"] = lambda *_: {}
    scope["_text"] = lambda state, key: str(state.attributes.get(key) or "")

    def evaluate():
        assessed = scope["_evaluate_nina_like_entities"](
            hass, SimpleNamespace(data={}), [SLOT_A, SLOT_B]
        )
        assessed.warning_components = [
            {**item, "origin": f"manual:{MANUAL}"}
            for item in assessed.warning_components
        ]
        assessed.warning_observations = [
            {**item, "origin": f"manual:{MANUAL}",
             "confirmed_at": clock[0].isoformat()}
            for item in assessed.warning_observations
        ]
        assessed.warning_origins = {
            ident: f"manual:{MANUAL}" for ident in assessed.warning_ids
        }
        assessed.provider_domain = "nina"
        assessed.safety_source_key = MANUAL
        return assessed
    return clock, apply, disk, volatile, statuses, hass, entry, evaluate


def _apply(apply, hass, entry, warning):
    asyncio.run(apply(hass, entry, SimpleNamespace(), warning))


def _parts(disk):
    return {part["id"]: part for part in disk["channels"]["warning"]["warning_records"]}


def test_nina_provider_provides_distinct_ha_entity_for_each_active_warning():
    _clock, apply, disk, memory, states, hass, entry, evaluate = _setup_manual()
    assessed = evaluate()
    assert assessed.source_nina_entity == SLOT_A  # strongest/first only
    assert {item["id"]: item["entity"] for item in assessed.warning_components} == {
        ID_A: SLOT_A, ID_B: SLOT_B,
    }
    assert {item["id"]: item["entity"] for item in assessed.warning_observations} == {
        ID_A: SLOT_A, ID_B: SLOT_B,
    }
    _apply(apply, hass, entry, assessed)
    assert {id_: p["source_entity"] for id_, p in _parts(disk).items()} == {
        ID_A: SLOT_A, ID_B: SLOT_B,
    }
    memory.clear()
    states[SLOT_A] = SimpleNamespace(state="off", attributes={})
    states[SLOT_B] = SimpleNamespace(state="unavailable", attributes={})
    after = evaluate()
    _apply(apply, hass, entry, after)
    assert set(_parts(disk)) == {ID_B}
    assert after.nina_status == "danger"
    assert _parts(disk)[ID_B]["source_entity"] == SLOT_B


def test_three_and_four_manual_nina_slots_each_retains_own_fallback():
    for count in (3, 4):
        clock, apply, disk, memory, states, hass, entry, evaluate = _setup_manual()
        entity_ids = [SLOT_A, SLOT_B]
        for i in range(3, count + 1):
            entity = f"binary_sensor.nina_warning_{i}"
            ident = f"mow.warning-{i}"
            states[entity] = SimpleNamespace(state="on", attributes={
                "id": ident, "headline": "Rauch", "description": "Gefahr",
                "recommended_actions": "Schließen Sie Fenster und Türen.",
            })
            entity_ids.append(entity)
        # Use the same source extraction, but include the additional slots.
        scope = _provider()
        scope["_nina_slot_sensor_values"] = lambda *_: {}
        scope["_cached_nina_record"] = lambda *_: {}
        scope["_text"] = lambda state, field: str(state.attributes.get(field) or "")
        def report():
            report = scope["_evaluate_nina_like_entities"](hass, SimpleNamespace(data={}), entity_ids)
            report.warning_components = [{**c, "origin": f"manual:{MANUAL}"} for c in report.warning_components]
            report.warning_observations = [
                {**c, "origin": f"manual:{MANUAL}", "confirmed_at": clock[0].isoformat()}
                for c in report.warning_observations
            ]
            report.warning_origins = {i: f"manual:{MANUAL}" for i in report.warning_ids}
            report.safety_source_key = MANUAL
            report.provider_domain = "nina"
            return report
        _apply(apply, hass, entry, report())
        for unknown_slot in entity_ids[1:]:
            # Each variant must hold *only* the unavailable slot after all
            # other specific slots independently verify their OFF state.
            memory.clear()
            for eid in entity_ids:
                states[eid] = SimpleNamespace(
                    state="unavailable" if eid == unknown_slot else "off", attributes={}
                )
            fresh = report()
            _apply(apply, hass, entry, fresh)
            remaining = list(_parts(disk).values())
            assert len(remaining) == 1, (count, unknown_slot, remaining)
            assert remaining[0]["source_entity"] == unknown_slot
            # Reset active slots, re-confirm only when old one is no longer
            # available and has not timed out; proof timestamps are bounded.
            for eid in entity_ids:
                states[eid] = SimpleNamespace(state="on", attributes={
                    "id": ID_A if eid == SLOT_A else ID_B if eid == SLOT_B else
                    f"mow.warning-{eid.split('_')[-1]}",
                    "headline": "Rauch", "description": "Gefahr",
                    "recommended_actions": "Schließen Sie Fenster und Türen.",
                })
            clock[0] += timedelta(minutes=6)
            _apply(apply, hass, entry, report())


def test_just_cleared_automatic_danger_is_removed_while_manual_remains_unknown():
    clock, apply, disk, volatile, states, hass, entry, evaluate = _setup_manual()
    manual = evaluate()
    manual.warning_components = [c for c in manual.warning_components if c["id"] == ID_A]
    manual.warning_observations = [c for c in manual.warning_observations if c["id"] == ID_A]
    manual.warning_ids = {ID_A}
    manual.warning_origins = {ID_A: f"manual:{MANUAL}"}
    auto = _provider()["WarningAssessment"](
        nina_status="danger", official_close_instruction=True,
        nina_reason_key="nina_air_danger", safety_source_key=MOW,
        warning_ids={"mow.auto-smoke"},
        warning_origins={"mow.auto-smoke": f"auto:{BASE}"},
        provider_availability={BASE: True, MOW: True},
    )
    merge = _provider()["_merge_warning_assessments"]
    _apply(apply, hass, entry, merge(auto, manual))
    assert set(_parts(disk)) == {"mow.auto-smoke", ID_A}
    states[SLOT_A] = SimpleNamespace(state="unavailable", attributes={})
    volatile.clear()
    clock[0] += timedelta(minutes=5)
    empty = _provider()["WarningAssessment"](
        safety_source_key=BASE, provider_availability={BASE: True, MOW: True},
    )
    _apply(apply, hass, entry, empty)
    assert set(_parts(disk)) == {ID_A}
    assert empty.nina_status == "danger"
    assert _parts(disk)[ID_A]["valid_until"] == (clock[0] + timedelta(minutes=55)).isoformat()


def test_auto_weather_success_cannot_clear_unavailable_original_gust_sensor():
    scope = _extract("safety_state.py", {"_weather_provider_availability"}, {
        "CONF_WEATHER": "weather_entity",
        "_state_unknown": lambda state: state is None or state.state in ("unknown", "unavailable"),
    })
    evaluate = scope["_weather_provider_availability"]
    old = {
        "source_key": "auto_weather:50.7000:7.1000",
        "source_entities": ["sensor.outdoor_gust", "auto_weather:50.7000:7.1000"],
    }
    states = {"sensor.outdoor_gust": SimpleNamespace(state="unavailable")}
    hass = SimpleNamespace(states=SimpleNamespace(get=states.get))
    entry = SimpleNamespace(data={})
    for gps in ("50.7000:7.1000", "50.7001:7.1000"):
        status = SimpleNamespace(safety_source_key=f"auto_weather:{gps}",
                                 provider_available=True, weather_hard_lock=False)
        assert evaluate(hass, entry, status, old)[0] == "unknown"
    states["sensor.outdoor_gust"] = SimpleNamespace(state="8")
    same = SimpleNamespace(safety_source_key=old["source_key"],
                           provider_available=True, weather_hard_lock=False)
    assert evaluate(hass, entry, same, old)[0] == "clear"
    states["sensor.outdoor_gust"] = SimpleNamespace(state="unknown")
    assert evaluate(hass, entry, same, old)[0] == "unknown"


def test_all_3_slot_manual_off_unavailable_combinations_independently_reconcile():
    """27 combinations: no lost unknown hazard and no retained verified OFF."""
    from itertools import product
    for next_states in product(("off", "unavailable", "on"), repeat=3):
        clock, apply, disk, volatile, states, hass, entry, _ = _setup_manual()
        third = "binary_sensor.nina_warning_3"
        third_id = "mow.third"
        states[third] = SimpleNamespace(state="on", attributes={
            "id": third_id, "headline": "Rauch", "description": "Rauch",
            "recommended_actions": "Schließen Sie Fenster und Türen.",
        })
        scope = _provider()
        scope["_nina_slot_sensor_values"] = lambda *_: {}
        scope["_cached_nina_record"] = lambda *_: {}
        scope["_text"] = lambda state, field: str(state.attributes.get(field) or "")
        sources = (SLOT_A, SLOT_B, third)
        ids = (ID_A, ID_B, third_id)
        def report():
            report = scope["_evaluate_nina_like_entities"](hass, SimpleNamespace(data={}), list(sources))
            report.warning_components = [{**p, "origin": f"manual:{MANUAL}"} for p in report.warning_components]
            report.warning_observations = [
                {**p, "origin": f"manual:{MANUAL}", "confirmed_at": clock[0].isoformat()}
                for p in report.warning_observations
            ]
            report.warning_origins = {item: f"manual:{MANUAL}" for item in report.warning_ids}
            report.safety_source_key = MANUAL
            report.provider_domain = "nina"
            return report
        _apply(apply, hass, entry, report())
        volatile.clear()  # Check the disk representation after restart.
        for source, state in zip(sources, next_states):
            if state == "on":
                continue
            states[source] = SimpleNamespace(state=state, attributes={})
        current = report()
        _apply(apply, hass, entry, current)
        expected = {ident for ident, state in zip(ids, next_states) if state != "off"}
        actual = set(disk.get("channels", {}).get("warning", {}).get("warning_ids", []))
        assert actual == expected, (next_states, actual, expected)
        assert (current.nina_status == "danger") == bool(expected)


def test_upgrade_from_shared_manual_slot_does_not_cancel_second_offline_warning():
    """An old common-source-entity record must not clear two manual alerts."""
    clock, apply, disk, volatile, states, hass, entry, evaluate = _setup_manual()
    _apply(apply, hass, entry, evaluate())
    stored = disk["channels"]["warning"]
    # Simulate COMPLETE(10): both warning records referred to strongest slot
    # and had no per-warning 'entity' metadata.
    for component in stored["warning_records"]:
        component.pop("entity", None)
        component["source_entity"] = SLOT_A
    stored["warning_components"] = [
        {k: v for k, v in item.items() if k != "entity"}
        for item in stored["warning_components"]
    ]
    volatile.clear()
    states[SLOT_A] = SimpleNamespace(state="off", attributes={})
    states[SLOT_B] = SimpleNamespace(state="unavailable", attributes={})
    uncertain = evaluate()
    _apply(apply, hass, entry, uncertain)
    assert uncertain.nina_status == "danger"
    assert ID_B in _parts(disk)
    assert all(not part.get("source_entity") for part in _parts(disk).values())
    volatile.clear()
    states[SLOT_B] = SimpleNamespace(state="off", attributes={})
    resolved = evaluate()
    _apply(apply, hass, entry, resolved)
    assert "warning" not in disk["channels"]

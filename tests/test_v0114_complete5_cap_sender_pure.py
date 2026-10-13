"""v0.11.4 COMPLETE(5): CAP issuer + sent identity regressions, no HA runtime."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _provider, _safety
from test_v0114_complete4_safety_pure import (
    BASE, MOW, _case, _decision, _persistence_environment,
)

SENT = "2026-10-11T17:00:00+00:00"


def _active(sender="amt-a@example.org", sent=SENT):
    w = _case(BASE)
    w.safety_source_key = MOW
    w.official_close_instruction = True
    w.nina_status = "danger"
    w.nina_reason_key = "nina_air_danger"
    w.hard_safety_evidence_at = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    w.warning_ids = {"mow.shared-id"}
    w.warning_cap_identities = {
        "mow.shared-id": {_provider()["_cap_identity_signature"](sender, sent)}
    } if sender else {}
    return w


def _clear(sender="amt-b@example.org", sent=SENT):
    w = _case(BASE, ready=True, notice="all_clear", warning_ids={"mow.shared-id"})
    w.provider_availability[MOW] = True
    ref = f"{sender},shared-id,{sent}"
    w.warning_cap_identities = _provider()["_sourced_cap_reference_identities"](
        ref, message_id="mow.cancel-id",
    )
    return w


def test_same_nina_feed_same_id_other_cap_sender_is_not_a_match():
    prev = {"source_key": MOW, "warning_ids": ["mow.shared-id"],
            "warning_cap_identities": {"mow.shared-id": list(_active().warning_cap_identities["mow.shared-id"])}}
    assert _decision(_clear(), prev) == ("unknown", MOW)
    assert _decision(_clear("amt-a@example.org"), prev) == ("clear", MOW)


def test_cap_reference_wrong_original_sent_is_not_a_match():
    prev = {"source_key": MOW, "warning_ids": ["mow.shared-id"],
            "warning_cap_identities": {"mow.shared-id": list(_active().warning_cap_identities["mow.shared-id"])}}
    assert _decision(_clear("amt-a@example.org", "2026-10-11T17:01:00+00:00"), prev) == ("unknown", MOW)
    # Same moment in a different timezone *is* the same CAP sent timestamp.
    assert _decision(_clear("amt-a@example.org", "2026-10-11T19:00:00+02:00"), prev) == ("clear", MOW)


def test_older_persisted_warning_without_cap_metadata_is_not_cancelled_by_new_cap_reference():
    legacy = {"source_key": MOW, "warning_ids": ["mow.shared-id"]}
    assert _decision(_clear("amt-a@example.org"), legacy) == ("unknown", MOW)
    assert _decision(_clear("amt-b@example.org"), legacy) == ("unknown", MOW)
    # Legacy ID-only providers still retain their previous behavior.
    assert _safety()["_matching_warning_ids"](legacy, {"mow.shared-id"})


def test_full_cap_reference_parser_keeps_sender_sent_and_known_provider():
    parse = _provider()["_sourced_cap_reference_identities"]
    stamp_a = "2026-10-11T17:00:00Z"
    stamp_b = "2026-10-11T17:00:00+00:00"
    got = parse(
        f"amt-a@example.org,shared-id,{stamp_a} amt-b@example.org,shared-id,{stamp_b}",
        message_id="mow.cancel-id",
    )
    assert got["mow.shared-id"] == {
        _provider()["_cap_identity_signature"]("amt-a@example.org", stamp_a),
        _provider()["_cap_identity_signature"]("amt-b@example.org", stamp_b),
    }
    assert parse("amt-a@example.org,pol.shared-id,2026-10-11T17:00:00Z",
                 message_id="mow.cancel-id") == {}
    assert parse("amt-a@example.org,shared-id,not-a-date",
                 message_id="mow.cancel-id") == {}


def test_automatic_and_manual_pipelines_keep_cap_original_sender():
    scope = _provider()
    now = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    active = SimpleNamespace(
        expires=None, effective=None, event="Smoke", description="Rauch",
        headline="Rauch", instruction="Fenster und Türen schließen",
        msg_type="Alert", references="", warning_id="mow.shared-id",
        provider_domain="nina_auto_mowas", category="civil", severity="Severe",
        sender="amt-a@example.org", issued_at=datetime(2026, 10, 11, 17, tzinfo=timezone.utc),
        evidence_at=now,
    )
    data = SimpleNamespace(
        provider_domain="nina_auto", safety_source_key=BASE,
        coverage="civil_and_weather", error=None, region_ars="053820000000",
        active_sources=["nina_auto_mowas"], source_availability={"nina_auto_mowas": True},
        available=True, warnings=[active],
    )
    scope["auto_warning_data"] = lambda *_: data
    auto = scope["_automatic_warning_assessment"](SimpleNamespace(), SimpleNamespace(data={}))
    assert auto.nina_status == "danger"
    assert auto.warning_cap_identities["mow.shared-id"] == _active().warning_cap_identities["mow.shared-id"]

    state = SimpleNamespace(state="on", attributes={
        "id": "mow.shared-id", "headline": "Rauch", "description": "Rauch",
        "recommended_actions": "Fenster und Türen schließen",
        "sender": "amt-a@example.org", "sent": SENT,
    })
    scope["_nina_slot_sensor_values"] = lambda *_: {}
    scope["_cached_nina_record"] = lambda *_: {}
    scope["_text"] = lambda state, key: str(state.attributes.get(key) or "")
    manual = scope["_evaluate_nina_like_entities"](
        SimpleNamespace(states=SimpleNamespace(get=lambda _: state)),
        SimpleNamespace(data={}), ["binary_sensor.nina_warnung_1"],
    )
    assert manual.warning_cap_identities == auto.warning_cap_identities


def test_persisted_warning_survives_wrong_issuer_after_restart_then_correct_cancel_clears():
    apply, disk, volatile = _persistence_environment()
    entry = SimpleNamespace(entry_id="wohnmobil-cap-sender", data={})
    hass = SimpleNamespace()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _active()))
    original = disk["channels"]["warning"]
    assert original["warning_ids"] == ["mow.shared-id"]
    assert len(original["warning_cap_identities"]["mow.shared-id"]) == 1

    volatile.clear()  # Restart: load from JSON-backed Store
    wrong = _clear("amt-b@example.org")
    asyncio.run(apply(hass, entry, SimpleNamespace(), wrong))
    assert wrong.nina_status == "danger"
    assert wrong.official_close_instruction is True
    assert disk["channels"]["warning"]["warning_cap_identities"] == original["warning_cap_identities"]

    volatile.clear()
    wrong_sent = _clear("amt-a@example.org", "2026-10-11T16:59:59Z")
    asyncio.run(apply(hass, entry, SimpleNamespace(), wrong_sent))
    assert wrong_sent.nina_status == "danger"
    assert "warning" in disk["channels"]

    volatile.clear()
    correct = _clear("amt-a@example.org")
    asyncio.run(apply(hass, entry, SimpleNamespace(), correct))
    assert correct.nina_status == "clear"
    assert "warning" not in disk["channels"]


def test_legacy_persisted_entry_with_no_sender_does_not_unlock_by_cap_reference():
    apply, disk, volatile = _persistence_environment()
    entry = SimpleNamespace(entry_id="wohnmobil-cap-legacy", data={})
    hass = SimpleNamespace()
    asyncio.run(apply(hass, entry, SimpleNamespace(), _active(sender="")))
    # Simulate actual older Store, which didn't have the new field.
    disk["channels"]["warning"].pop("warning_cap_identities", None)
    volatile.clear()
    candidate = _clear("amt-b@example.org")
    asyncio.run(apply(hass, entry, SimpleNamespace(), candidate))
    assert candidate.nina_status == "danger"
    assert "warning" in disk["channels"]


def test_original_nina_cap_sender_is_read_from_detail_not_from_feed_name():
    from test_v0114_complete3_safety_pure import _ast_functions
    scope = _ast_functions("auto_providers.py", {"AutoWarningRecord", "_nina_record"}, {
        "_pick_info": lambda detail: detail["info"][0],
        "_parse_dt": lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None,
        "_nina_parameter_text": lambda *_: "",
        "dt_util": SimpleNamespace(utcnow=lambda: datetime(2026, 10, 11, 18, tzinfo=timezone.utc)),
    })
    rec = scope["_nina_record"]("mow.shared-id", {
        "sender": "amt-a@example.org", "sent": SENT, "msgType": "Alert",
        "info": [{"headline": "Rauch", "instruction": "Fenster und Türen schließen"}],
    }, source="mowas")
    assert rec.sender == "amt-a@example.org"
    assert rec.issued_at == datetime(2026, 10, 11, 17, tzinfo=timezone.utc)
    assert rec.provider_domain == "nina_auto_mowas"


def test_two_simultaneous_messages_same_id_different_senders_need_both_cancellations():
    signatures = {
        "mow.shared-id": {
            _provider()["_cap_identity_signature"]("amt-a@example.org", SENT),
            _provider()["_cap_identity_signature"]("amt-b@example.org", SENT),
        }
    }
    previous = {"source_key": MOW, "warning_ids": ["mow.shared-id"],
                "warning_cap_identities": {key: list(items) for key, items in signatures.items()}}
    assert _decision(_clear("amt-a@example.org"), previous) == ("unknown", MOW)
    both = _clear("amt-a@example.org")
    both.warning_cap_identities["mow.shared-id"].add(
        _provider()["_cap_identity_signature"]("amt-b@example.org", SENT)
    )
    assert _decision(both, previous) == ("clear", MOW)


def test_really_configured_manual_warning_source_preserves_cap_identities():
    scope = _provider()
    state = SimpleNamespace(state="on", attributes={
        "id": "mow.shared-id", "headline": "Rauch", "description": "Rauch",
        "recommended_actions": "Fenster und Türen schließen",
        "sender": "amt-a@example.org", "sent": SENT,
    })
    scope["_config_entry_entities"] = lambda *_: ["binary_sensor.nina_1"]
    scope["_nina_slot_sensor_values"] = lambda *_: {}
    scope["_cached_nina_record"] = lambda *_: {}
    scope["_text"] = lambda state, key: str(state.attributes.get(key) or "")
    hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda _: state),
        config_entries=SimpleNamespace(async_get_entry=lambda _: SimpleNamespace(
            entry_id="nina-entry", domain="nina")),
    )
    manual = scope["_manual_warning_assessment"](
        hass, SimpleNamespace(data={"warning_source": "nina-entry"})
    )
    assert manual.warning_cap_identities == _active().warning_cap_identities
    assert manual.nina_status == "danger"

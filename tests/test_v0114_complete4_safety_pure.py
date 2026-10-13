"""COMPLETE(4) regressions for mobile GPS drift and source-bound CAP cancellations."""
from __future__ import annotations

import asyncio
import copy
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _extract, _provider, _safety
from test_v0114_complete3_safety_pure import BASE, MOW


DRIFT = "auto_warning:50.7001:7.1000"
FAR = "auto_warning:52.1000:13.2000"


def _case(position: str = BASE, *, ready: bool = False, dashboard: bool = False,
          notice: str | None = None, warning_ids: set[str] | None = None):
    inventory = {position: ready}
    if dashboard:
        inventory[f"{position}:nina_auto_dashboard"] = True
    return SimpleNamespace(
        safety_source_key=position, provider_availability=inventory,
        official_close_instruction=False, weather_hard_lock=False,
        nina_status="clear" if notice == "all_clear" else "none",
        warning_notice_kind=notice, warning_notice_text="Info", warning_ambiguous_clear=False,
        warning_ids=set(warning_ids or set()), provider_domain="nina_auto",
        nina_reason_args={}, nina_reason_key=None, source_nina_entity=None,
    )


def _decision(w, previous=None):
    previous = previous or {"source_key": MOW, "warning_ids": ["mow.smoke-id"]}
    return _safety()["_warning_provider_availability"](
        SimpleNamespace(), SimpleNamespace(data={}), w, previous,
    )


def test_gps_jitter_and_failed_dashboard_cannot_clear_old_smoke_lock():
    w = _case(DRIFT)
    assert _decision(w) == ("unknown", MOW)
    w.provider_availability[DRIFT] = True
    assert _decision(w) == ("unknown", MOW)  # no authoritative regional inventory
    w.provider_availability[f"{DRIFT}:nina_auto_dashboard"] = True
    w.provider_availability[DRIFT] = False
    assert _decision(w) == ("unknown", MOW)  # partial detail failure
    w.provider_availability[DRIFT] = True
    assert _decision(w) == ("clear", MOW)  # authoritative nearby assessment


def test_unrelated_or_ambiguous_clear_not_fresh_release_after_gps_move():
    w = _case(DRIFT, ready=True, dashboard=True, notice="all_clear", warning_ids={"mow.water-id"})
    assert _decision(w) == ("unknown", MOW)
    w.warning_notice_kind = None
    w.warning_ambiguous_clear = True
    assert _decision(w) == ("unknown", MOW)


def test_distant_real_move_requires_successful_new_provider():
    w = _case(FAR)
    assert _decision(w) == ("unknown", MOW)
    w.provider_availability[FAR] = True
    assert _decision(w) == ("clear", MOW)
    # Malformed/unresolved coords never make an old lock disappear.
    w.safety_source_key = "auto_warning:bad:coords"
    w.provider_availability = {w.safety_source_key: True}
    assert _decision(w) == ("unknown", MOW)


def test_dateline_short_crossing_is_not_mistaken_for_intercontinental_move():
    d = _safety()["_safety_location_distance_km"](
        "auto_warning:50.0000:179.9999", "auto_warning:50.0000:-179.9999"
    )
    assert d is not None and d < 0.1


def test_different_nina_sources_cannot_cancel_single_saved_warning():
    matching = _safety()["_matching_warning_ids"]
    original = {"warning_ids": ["pol.shared-id"]}
    assert not matching(original, {"mow.shared-id"})
    assert not matching(original, {"kat.shared-id"})
    assert not matching(original, {"shared-id"})
    assert matching(original, {"pol.shared-id"})
    assert matching({"warning_ids": ["katwarn.shared-id"]}, {"kat.shared-id"})
    # Do not mistake one cancellation for all alerts from two NINA providers.
    assert not matching({"warning_ids": ["mow.shared-id", "pol.shared-id"]}, {"mow.shared-id"})


def test_bare_cap_reference_is_namespaced_from_verified_nina_source():
    source = _provider()["_sourced_warning_reference_ids"]
    ref = "official.sender@example.org,shared-id,2026-10-11T18:00:00+02:00"
    assert source(ref, message_id="mow.cancel-new") == {"mow.shared-id"}
    assert source(ref, message_id="kat.cancel-new") == {"kat.shared-id"}
    assert source(ref, message_id="pol.cancel-new") == {"pol.shared-id"}
    assert source(ref, message_id="cancel-new", provider_domain="nina_auto_police") == {"pol.shared-id"}
    assert source(ref, message_id="cancel-new") == {"shared-id"}
    assert source(ref, message_id="mow.cancel-new") != source(ref, message_id="pol.cancel-new")


def test_verified_source_cap_reference_releases_only_correct_hazard():
    source = _provider()["_sourced_warning_reference_ids"]
    ref = "sender@example.org,shared-id,2026-10-11T18:00:00+02:00"
    for origin, should_clear in (("mow.clear-id", False), ("kat.clear-id", False),
                                 ("pol.clear-id", True), ("clear-id", False)):
        w = _case(BASE, ready=True, notice="all_clear")
        w.provider_availability[MOW] = True
        # Here old known lock is a police alert, regardless of provider cache key.
        w.warning_ids = source(ref, message_id=origin)
        actual = _decision(w, {"source_key": MOW, "warning_ids": ["pol.shared-id"]})[0]
        assert (actual == "clear") == should_clear, origin


def _persistence_environment(*, clock_ref=None, manual_entity_ids=None):
    """Run the real state-application method with an isolated JSON-backed Store."""
    scope = _safety()
    clock = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    if clock_ref is None:
        clock_ref = [clock]
    if manual_entity_ids is not None:
        scope["_entry_entity_ids"] = lambda hass, source: list(manual_entity_ids)
    file_store: dict[str, object] = {}
    volatile: dict[str, object] = {}

    async def load_state(hass, entry):
        if entry.entry_id not in volatile:
            volatile[entry.entry_id] = copy.deepcopy(file_store)
        return volatile[entry.entry_id]

    async def save_state(hass, entry, state):
        file_store.clear()
        file_store.update(json.loads(json.dumps(state)))
        volatile[entry.entry_id] = state

    more = _extract("safety_state.py", {
        "async_apply_persistent_safety_state", "_record_from_warning", "_record_is_valid",
        "_apply_warning_record", "_parse_datetime", "_json_reason_args",
        "_same_safety_payload", "_should_refresh_confirmation",
    }, {
        **scope, "_async_state": load_state, "_async_save_state": save_state,
        "_weather_provider_availability": lambda *a: ("clear", "weather"),
        "dt_util": SimpleNamespace(utcnow=lambda: clock_ref[0], UTC=timezone.utc),
        "SAFETY_FALLBACK_MAX_AGE": timedelta(hours=1), "timedelta": timedelta,
        "_CONFIRM_WRITE_INTERVAL": timedelta(minutes=5),
        "_WARNING_CHANNEL": "warning", "_WEATHER_CHANNEL": "weather",
        "CONF_SHOW_GENERAL_WARNINGS": "show_general_warnings",
    })
    return more["async_apply_persistent_safety_state"], file_store, volatile


def test_real_save_restore_after_restart_and_drift_keeps_lock_and_foreign_cap_cannot_release():
    apply, disk, volatile = _persistence_environment()
    entry = SimpleNamespace(entry_id="wohnmobil", data={})
    hass = SimpleNamespace()
    active = _case(BASE)
    active.safety_source_key = MOW
    active.official_close_instruction = True
    active.nina_status = "danger"
    active.nina_reason_key = "nina_air_danger"
    active.hard_safety_evidence_at = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    active.warning_ids = {"pol.shared-id"}
    asyncio.run(apply(hass, entry, SimpleNamespace(), active))
    assert disk["channels"]["warning"]["warning_ids"] == ["pol.shared-id"]

    # Simulated restart: no memory and only the serialized Store.
    volatile.clear()
    drifting = _case(DRIFT)
    asyncio.run(apply(hass, entry, SimpleNamespace(), drifting))
    assert drifting.nina_status == "danger"
    assert drifting.official_close_instruction is True
    assert disk["channels"]["warning"]["warning_ids"] == ["pol.shared-id"]

    # Wrong-provider cancellation must not change persisted ID.
    volatile.clear()
    wrong = _case(BASE, notice="all_clear", warning_ids={"mow.shared-id"})
    wrong.provider_availability[MOW] = True
    asyncio.run(apply(hass, entry, SimpleNamespace(), wrong))
    assert wrong.nina_status == "danger"
    assert disk["channels"]["warning"]["warning_ids"] == ["pol.shared-id"]

    # A source-matched CAP cancellation can genuinely end that exact lock.
    volatile.clear()
    correct = _case(BASE, notice="all_clear", warning_ids={"pol.shared-id"})
    correct.provider_availability[MOW] = True
    asyncio.run(apply(hass, entry, SimpleNamespace(), correct))
    assert "warning" not in disk["channels"]


def test_conflicting_explicit_reference_namespace_is_not_trusted():
    source = _provider()["_sourced_warning_reference_ids"]
    ref = "sender@example.org,pol.shared-id,2026-10-11T18:00:00+02:00"
    assert source(ref, message_id="mow.clear-id") == set()
    assert source(ref, message_id="pol.clear-id") == {"pol.shared-id"}


def test_automatic_and_manual_cap_paths_agree_on_source_scoped_references():
    scope = _provider()
    reference = "sender@example.org,shared-id,2026-10-11T18:00:00+02:00"
    record = SimpleNamespace(
        expires=None, effective=None, event="Rauch", description="Gefahr vorüber",
        headline="Entwarnung", instruction="", msg_type="Cancel",
        references=reference, warning_id="pol.cancel-new", provider_domain="nina_auto_police",
        category="civil", severity="Minor", issued_at=None, evidence_at=None,
    )
    data = SimpleNamespace(
        provider_domain="nina_auto", safety_source_key=BASE,
        coverage="civil_and_weather", error=None, region_ars="053820000000",
        active_sources=[], source_availability={"nina_auto_police": True},
        available=True, warnings=[record],
    )
    scope["auto_warning_data"] = lambda *_: data
    auto = scope["_automatic_warning_assessment"](SimpleNamespace(), SimpleNamespace(data={}))
    assert auto.warning_ids == {"pol.shared-id"}
    assert auto.warning_notice_kind == "all_clear"

    state = SimpleNamespace(state="on", attributes={
        "id": "pol.cancel-new", "headline": "Entwarnung", "description": "Gefahr vorüber",
        "msg_type": "Cancel", "references": reference,
    })
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: state))
    scope["_nina_slot_sensor_values"] = lambda *_: {}
    scope["_cached_nina_record"] = lambda *_: {}
    scope["_text"] = lambda state, attr: str(state.attributes.get(attr) or "")
    manual = scope["_evaluate_nina_like_entities"](
        hass, SimpleNamespace(data={}), ["binary_sensor.nina_warning_1"]
    )
    assert manual.warning_notice_kind == "all_clear"
    assert manual.warning_ids == auto.warning_ids

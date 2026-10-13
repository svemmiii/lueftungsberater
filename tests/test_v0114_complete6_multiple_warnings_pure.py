"""COMPLETE(6): provider-by-provider NINA clearance of persisted hard locks."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from test_v0114_complete2_pure import _safety
from test_v0114_complete4_safety_pure import BASE, MOW, _case, _persistence_environment

POL = f"{BASE}:nina_auto_police"
KAT = f"{BASE}:nina_auto_katwarn"


def _previous(*ids):
    return {"source_key": MOW, "warning_ids": list(ids)}


def _status(*, mow=True, police=None, katwarn=None, base=False, dashboard=False):
    w = _case(BASE, ready=base, dashboard=dashboard)
    w.provider_availability[MOW] = mow
    if police is not None:
        w.provider_availability[POL] = police
    if katwarn is not None:
        w.provider_availability[KAT] = katwarn
    return w


def _availability(w, previous):
    return _safety()["_warning_provider_availability"](
        SimpleNamespace(), SimpleNamespace(data={}), w, previous,
    )[0]


def test_main_source_success_does_not_clear_unavailable_secondary_source():
    previous = _previous("mow.smoke-id", "pol.chemical-id")
    assert _availability(_status(mow=True, police=False), previous) == "unknown"
    assert _availability(_status(mow=True), previous) == "unknown"
    assert _availability(_status(mow=True, police=True), previous) == "clear"
    assert _availability(_status(mow=False, police=True), previous) == "unknown"


def test_regional_dashboard_only_clears_if_entire_current_inventory_is_valid():
    previous = _previous("mow.smoke-id", "pol.chemical-id")
    # The missing police key means no current candidate for that feed; a
    # fully successful regional inventory can prove its absence.
    assert _availability(_status(mow=True, base=True, dashboard=True), previous) == "clear"
    # A partial polygon/detail fetch is not proof, even with a live dashboard.
    assert _availability(_status(mow=True, police=False, base=False, dashboard=True), previous) == "unknown"
    assert _availability(_status(mow=True, police=False, base=True, dashboard=True), previous) == "unknown"
    assert _availability(_status(mow=True, base=False, dashboard=True), previous) == "unknown"


def test_three_simultaneous_hazards_each_need_evidence():
    previous = _previous("mow.smoke-id", "pol.chemical-id", "kat.warning-id")
    assert _availability(_status(mow=True, police=True, katwarn=False), previous) == "unknown"
    assert _availability(_status(mow=True, police=False, katwarn=True), previous) == "unknown"
    assert _availability(_status(mow=True, police=True, katwarn=True), previous) == "clear"


def test_partial_or_unrelated_cap_clear_never_releases_other_providers():
    previous = _previous("mow.smoke-id", "pol.chemical-id")
    w = _status(mow=True, police=False)
    w.warning_notice_kind = "all_clear"
    w.warning_ids = {"mow.smoke-id"}
    assert _availability(w, previous) == "unknown"
    w.warning_ids = {"mow.smoke-id", "pol.chemical-id"}
    # Even matched cancel IDs are not enough if the responsible provider's
    # *current* fetch explicitly failed in this cycle.
    assert _availability(w, previous) == "unknown"
    w.provider_availability[POL] = True
    assert _availability(w, previous) == "clear"


def test_persistent_store_survives_restart_and_secondary_provider_outage():
    apply, disk, volatile = _persistence_environment()
    entry = SimpleNamespace(entry_id="wohnmobil-two-nina-feeds", data={})
    hass = SimpleNamespace()
    active = _status(mow=True, police=True, base=True)
    active.safety_source_key = MOW
    active.nina_status = "danger"
    active.official_close_instruction = True
    active.nina_reason_key = "nina_air_danger"
    active.hard_safety_evidence_at = datetime(2026, 10, 11, 18, tzinfo=timezone.utc)
    active.warning_ids = {"mow.smoke-id", "pol.chemical-id"}
    active.warning_cap_identities = {}
    asyncio.run(apply(hass, entry, SimpleNamespace(), active))
    assert set(disk["channels"]["warning"]["warning_ids"]) == active.warning_ids

    volatile.clear()  # Simulate Home Assistant restart, using persisted JSON.
    partially_unavailable = _status(mow=True, police=False, base=False)
    asyncio.run(apply(hass, entry, SimpleNamespace(), partially_unavailable))
    assert partially_unavailable.official_close_instruction is True
    assert partially_unavailable.nina_status == "danger"
    # This MoWaS feed replied successfully; its old absent alert can be
    # retired independently. The failed police feed must remain protected.
    assert set(disk["channels"]["warning"]["warning_ids"]) == {"pol.chemical-id"}

    volatile.clear()
    recovered = _status(mow=True, police=True, base=True)
    asyncio.run(apply(hass, entry, SimpleNamespace(), recovered))
    assert "warning" not in disk["channels"]
    assert recovered.official_close_instruction is False


def test_live_hazard_from_one_feed_does_not_erase_unknown_second_feed_on_disk():
    apply, disk, volatile = _persistence_environment()
    entry = SimpleNamespace(entry_id="wohnmobil-multifeed-refresh", data={})
    hass = SimpleNamespace()
    active = _status(mow=True, police=True, base=True)
    active.safety_source_key = MOW
    active.nina_status = "danger"
    active.official_close_instruction = True
    active.nina_reason_key = "nina_air_danger"
    active.hard_safety_evidence_at = datetime(2026, 10, 11, 18, tzinfo=timezone.utc)
    active.warning_ids = {"mow.smoke-id", "pol.chemical-id"}
    active.warning_cap_identities = {}
    asyncio.run(apply(hass, entry, SimpleNamespace(), active))

    volatile.clear()
    still_smoke = _status(mow=True, police=False, base=False)
    still_smoke.safety_source_key = MOW
    still_smoke.official_close_instruction = True
    still_smoke.nina_status = "danger"
    still_smoke.nina_reason_key = "nina_air_danger"
    still_smoke.hard_safety_evidence_at = active.hard_safety_evidence_at
    still_smoke.warning_ids = {"mow.smoke-id"}
    still_smoke.warning_cap_identities = {}
    asyncio.run(apply(hass, entry, SimpleNamespace(), still_smoke))
    assert still_smoke.official_close_instruction
    assert set(disk["channels"]["warning"]["warning_ids"]) == active.warning_ids

    # Once police is reliably checked, the stored warning can be narrowed to
    # the smoke warning that remains genuinely active.
    volatile.clear()
    still_smoke.provider_availability[POL] = True
    still_smoke.provider_availability[BASE] = True
    asyncio.run(apply(hass, entry, SimpleNamespace(), still_smoke))
    assert disk["channels"]["warning"]["warning_ids"] == ["mow.smoke-id"]


def test_non_nina_international_auto_warning_sources_keep_old_clear_semantics():
    other_location = "auto_warning:40.7000:-74.0000"
    older = {
        "source_key": other_location,
        "provider_domain": "nws_auto",
        "warning_ids": ["NWS-EXAMPLE-IDENTIFIER"],
    }
    warning = _case(other_location, ready=True)
    assert _availability(warning, older) == "clear"
    warning.provider_availability[other_location] = False
    assert _availability(warning, older) == "unknown"

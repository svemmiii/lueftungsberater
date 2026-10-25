"""COMPLETE(3): source identity + fresh-evidence safety regressions without HA."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from test_v0114_complete2_pure import _safety

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "lueftungsberater"
BASE = "auto_warning:50.7000:7.1000"
MOW = f"{BASE}:nina_auto_mowas"


def _warnings(**extra: Any) -> SimpleNamespace:
    return SimpleNamespace(
        safety_source_key=BASE,
        provider_availability={BASE: True, f"{BASE}:nina_auto_dashboard": True,
                               f"{BASE}:nina_auto_lhp": True},
        official_close_instruction=False, weather_hard_lock=False,
        warning_notice_kind=None, warning_ambiguous_clear=False,
        warning_ids=set(), **extra,
    )


def _decision(warnings: Any, *, key: str = MOW) -> str:
    previous = {"source_key": key, "warning_ids": ["mow.smoke-id"]}
    return _safety()["_warning_provider_availability"](
        SimpleNamespace(), SimpleNamespace(data={}), warnings, previous,
    )[0]


def test_source_change_at_same_location_with_foreign_clear_must_not_release():
    w = _warnings()
    w.warning_notice_kind = "all_clear"
    w.warning_ids = {"drinking-water-id"}
    assert _decision(w) == "unknown"
    w.warning_ambiguous_clear = True
    assert _decision(w) == "unknown"


def test_other_source_alone_does_not_prove_old_warning_ended():
    w = _warnings()
    w.provider_availability = {BASE: True, f"{BASE}:nina_auto_lhp": True}
    assert _decision(w) == "unknown"
    w.provider_availability = {BASE: False, f"{BASE}:nina_auto_dashboard": True,
                               f"{BASE}:nina_auto_lhp": True}
    assert _decision(w) == "unknown"


def test_fully_available_regional_dashboard_can_confirm_warning_absence():
    # A full fresh regional inventory with no conflicting cancellation is an
    # independent reason to release an alert no longer listed by MoWaS.
    assert _decision(_warnings()) == "clear"


def test_actual_accepted_location_change_drops_old_location_guard():
    w = _warnings()
    next_base = "auto_warning:52.1000:13.2000"
    w.safety_source_key = next_base
    w.provider_availability = {next_base: True}
    assert _decision(w) == "clear"


def test_same_source_partial_clear_with_missing_ids_stays_unknown():
    w = _warnings()
    w.provider_availability[MOW] = True
    w.warning_notice_kind = "all_clear"
    w.warning_ids = {"drinking-water-id"}
    assert _decision(w) == "unknown"
    w.warning_ids = {"mow.smoke-id"}
    assert _decision(w) == "clear"


def test_known_nina_prefixes_match_bare_cap_references():
    scope = _safety()
    compare = scope["_matching_warning_ids"]
    for prefix in ("mow", "dwd", "lhp", "kat", "biw", "pol", "katwarn", "biwapp"):
        assert compare({"warning_ids": [f"{prefix}.smoke-id"]}, {f"{prefix}.smoke-id"}), prefix
        assert not compare({"warning_ids": [f"{prefix}.smoke-id"]}, {"smoke-id"}), prefix
    assert not compare({"warning_ids": ["pol.smoke-id"]}, {"drinking-water-id"})


def test_same_bare_cap_identifier_from_two_sources_cannot_unlock_both():
    compare = _safety()["_matching_warning_ids"]
    prior = {"warning_ids": ["mow.shared-id", "pol.shared-id"]}
    assert not compare(prior, {"shared-id"})
    assert not compare(prior, {"mow.shared-id"})
    assert compare(prior, {"mow.shared-id", "pol.shared-id"})


def _ast_functions(filename: str, names: set[str], extra: dict[str, Any]) -> dict[str, Any]:
    if filename == "auto_providers.py":
        # The adapter now delegates CAP normalization to the same pure package
        # used in production. Keep every historical assertion unchanged.
        from test_v0119_warning_scopes_pure import policy
        cap = policy._warnings
        import xml.etree.ElementTree as ET
        names = names | {"_cap_pairs", "_as_float", "_local_name", "_warning_times"}
        extra = {"field": __import__("dataclasses").field, "math": __import__("math"), "_cap_time": _dt,
                 "_cap_json_infos": cap.json_infos, "_cap_xml_infos": cap.xml_infos,
                 "_attach_cap_infos": cap.attach_infos, "_cap_with_area": cap.with_area,
                 "_cap_info_area_element": cap.info_area_element, "ET": ET, **extra}
        extra.setdefault("_cap_geographic_signature", cap.geographic_signature)
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    body = [node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name in names]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                              *body], type_ignores=[])
    env: dict[str, Any] = {"datetime": datetime, "timedelta": timedelta, "dataclass": dataclass,
                           "Any": Any, **extra}
    exec(compile(ast.fix_missing_locations(module), filename, "exec"), env)
    return env


def _dt(value: str | None):
    return datetime.fromisoformat(value) if value else None


def test_nina_sent_time_is_not_evidence_time():
    now = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    sent = "2026-10-11T15:00:00+00:00"
    env = _ast_functions("auto_providers.py", {"AutoWarningRecord", "_nina_record"}, {
        "_pick_info": lambda details: details["info"][0],
        "_parse_dt": _dt,
        "_nina_parameter_text": lambda *_: "",
        "dt_util": SimpleNamespace(utcnow=lambda: now),
    })
    record = env["_nina_record"]("mow.smoke-id", {
        "sent": sent, "msgType": "Alert", "info": [{"headline": "Rauch", "instruction": "Fenster schließen"}],
    }, observed_at=now)
    assert record.issued_at == datetime.fromisoformat(sent)
    assert record.evidence_at == now
    assert record.evidence_at != record.issued_at


def test_fallback_expires_one_hour_after_last_fresh_observation_not_cap_sent():
    now = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    safety = _ast_functions("safety_state.py", {"_parse_datetime", "_record_from_warning", "_record_is_valid", "_warning_components"}, {
        "dt_util": SimpleNamespace(UTC=timezone.utc),
        "SAFETY_FALLBACK_MAX_AGE": timedelta(hours=1),
        "_json_reason_args": lambda args: args,
    })
    w = SimpleNamespace(nina_status="danger", nina_reason_key="nina_air_danger",
                        nina_reason_args={}, source_nina_entity=None, provider_domain="nina_auto_mowas",
                        hard_safety_evidence_at=now, warning_ids={"mow.smoke-id"},
                        official_close_instruction=True)
    rec = safety["_record_from_warning"](w, MOW, now)
    assert rec["last_confirmed_at"] == now.isoformat()
    assert safety["_record_is_valid"](rec, MOW, now + timedelta(minutes=59))
    assert not safety["_record_is_valid"](rec, MOW, now + timedelta(hours=1, seconds=1))
    # Failed or stale polling never creates a new active record: availability
    # must be unknown and the original bound expires unchanged.
    failure = _warnings()
    failure.provider_availability = {MOW: False, BASE: False}
    assert _decision(failure) == "unknown"


def test_nws_and_meteoalarm_sent_dates_not_treated_as_freshness():
    now = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    env = _ast_functions("auto_providers.py", {"AutoWarningRecord", "_nws_record", "_cap_element_record"}, {
        "dt_util": SimpleNamespace(utcnow=lambda: now),
        "_parse_dt": _dt,
        "_first_text": lambda el, *names: next((el.get(n) for n in names if el.get(n)), ""),
        "_cap_preferred_info": lambda el: el,
        "_cap_area_matches": lambda *_: True,
    })
    old = "2026-10-11T15:00:00+00:00"
    nws = env["_nws_record"]({"properties": {"id": "x", "sent": old, "headline": "Rauch"}})
    assert (nws.issued_at, nws.evidence_at) == (datetime.fromisoformat(old), now)
    import xml.etree.ElementTree as ET
    cap = env["_cap_element_record"](ET.Element("alert", {"identifier": "y", "sent": old, "headline": "Smoke"}),
                                      provider="meteoalarm_auto", lat=51.0, lon=7.0)
    assert (cap.issued_at, cap.evidence_at) == (datetime.fromisoformat(old), now)


def test_fresh_nina_dashboard_confirms_cached_detail_without_faking_new_cap_sent():
    import asyncio
    from dataclasses import field

    first = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
    clock = {"now": first}
    sent = "2026-10-11T15:00:00+00:00"
    calls = []
    details = {"sent": sent, "status": "Actual", "info": [{
        "headline": "Rauch", "instruction": "Fenster und Türen schließen",
    }]}
    geometry = {"type": "Polygon", "coordinates": []}

    async def regional(_session, _location, _state):
        return "053820000000", {"mow.smoke-id": ("mowas", "1", {})}

    async def get_json(_session, url):
        calls.append(url)
        return details if url.endswith(".json") else geometry

    env = _ast_functions("auto_providers.py", {
        "AutoWarningRecord", "AutoWarningData", "_nina_record", "_fetch_nina_warnings",
    }, {
        "field": field, "asyncio": asyncio, "timedelta": timedelta,
        "_NINA_BASE": "https://example.invalid",
        "_LOGGER": SimpleNamespace(debug=lambda *args, **kwargs: None),
        "dt_util": SimpleNamespace(utcnow=lambda: clock["now"]),
        "_pick_info": lambda detail: detail["info"][0],
        "_parse_dt": _dt, "_nina_parameter_text": lambda *_: "",
        "_nina_regional_candidates": regional,
        "_get_json": get_json,
        "_fresh": lambda ts, max_age, now: 0 <= (now - ts).total_seconds() < max_age.total_seconds(),
        "_geojson_contains_point": lambda *_: True,
        "_safety_location_key": lambda kind, loc: BASE,
    })
    state = SimpleNamespace(nina_cache={})
    location = SimpleNamespace(latitude=50.7, longitude=7.1)
    first_data = asyncio.run(env["_fetch_nina_warnings"](None, location, state))
    assert first_data.available
    assert len(calls) == 2  # Fresh detail + geometry
    assert first_data.warnings[0].evidence_at == first
    assert first_data.warnings[0].issued_at == datetime.fromisoformat(sent)

    clock["now"] = first + timedelta(minutes=10)
    second_data = asyncio.run(env["_fetch_nina_warnings"](None, location, state))
    assert second_data.available
    assert len(calls) == 2  # No extra detail requests; active dashboard refetched
    assert second_data.warnings[0].evidence_at == clock["now"]
    assert second_data.warnings[0].issued_at == first_data.warnings[0].issued_at

    # If the regional overview and nationwide fallback both fail, a cached
    # detail alone cannot prove the alert is still active: no new data result.
    async def regional_failure(*_args):
        raise RuntimeError("dashboard offline")

    async def nationwide_failure(*_args):
        raise RuntimeError("map-data offline")

    env["_nina_regional_candidates"] = regional_failure
    env["_nina_nationwide_candidates"] = nationwide_failure
    clock["now"] = first + timedelta(minutes=20)
    try:
        asyncio.run(env["_fetch_nina_warnings"](None, location, state))
    except RuntimeError:
        pass
    else:
        raise AssertionError("Failed providers must not confirm cached alerts")
    assert second_data.warnings[0].evidence_at == first + timedelta(minutes=10)

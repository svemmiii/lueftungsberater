"""COMPLETE(2): CAP identity, partial clears and dryness ordering without HA."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "lueftungsberater"


def _extract(module: str, names: set[str], variables: dict | None = None) -> dict:
    tree = ast.parse((ROOT / module).read_text())
    body = [
        node for node in tree.body
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in names)
        or (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names)
    ]
    mod = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *body], type_ignores=[])
    scope = dict(re=re, Any=Any, datetime=datetime, timezone=timezone, dataclass=dataclass, field=field)
    if variables:
        scope.update(variables)
    exec(compile(ast.fix_missing_locations(mod), module, "exec"), scope)
    return scope


def _provider():
    spec = importlib.util.spec_from_file_location("lb_complete2_languages", ROOT / "warning_language.py")
    language = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = language
    spec.loader.exec_module(language)
    names = {
        "WarningAssessment", "_warning_reference_ids", "_sourced_warning_reference_ids", "_sourced_cap_reference_identities", "_cap_identity_signature", "_NINA_CAP_PREFIXES", "_is_clear_warning",
        "_is_strong_clear_warning", "_evaluate_air_warning", "_contains_any",
        "_matches_close_instruction", "_has_official_close_instruction",
        "STRONG_CLEAR_WORDS", "CLEAR_NEGATIONS", "CLEAR_QUALIFIERS",
        "CLOSE_RELEASE_PATTERNS", "OFFICIAL_CLOSE_ACTIONS", "OFFICIAL_CLOSE_PATTERNS",
        "_assessment_warning_components", "_copy_warning_assessment", "_merge_warning_assessments",
        "_evaluate_nina_like_entities", "_manual_warning_assessment",
        "_automatic_warning_assessment", "_is_ambiguous_clear_update",
    }
    policy_spec = importlib.util.spec_from_file_location("lb_official_policy", ROOT / "warning_policy.py")
    policy = importlib.util.module_from_spec(policy_spec)
    policy_spec.loader.exec_module(policy)
    names.add("_apply_manual_official_notice")
    return _extract("providers.py", names, {
        "assess_official_warning": policy.assess_official_warning,
        "aware": policy.aware,
        "timedelta": __import__("datetime").timedelta,
        "AutoWarningRecord": SimpleNamespace,
        "effective_location": lambda hass, entry: SimpleNamespace(elevation=None),
        "foreign_all_clear": language.foreign_all_clear,
        "has_foreign_close_order": language.has_foreign_close_order,
        "_cap_action_context": policy._warnings.action_context,
        "_cap_json_infos": policy._warnings.json_infos,
        "dt_util": SimpleNamespace(utcnow=lambda: datetime.now(timezone.utc)),
        "CONF_SHOW_GENERAL_WARNINGS": "show_general_warnings",
        "CONF_WARNING_SOURCE": "warning_source",
        "WARNING_SOURCE_NONE": "none",
    })


def _safety():
    return _extract("safety_state.py", {
        "_canonical_warning_id", "_matching_warning_ids", "_warning_provider_availability",
        "_WARNING_SOURCE_ALIASES", "_AUTO_WARNING_ID_SOURCES",
        "_all_previous_auto_warning_sources_resolved", "_safety_location_distance_km",
        "_manual_warning_source_unresolved", "_missing_previous_warning_unresolved", "_warning_components",
        "_state_unknown", "_UNKNOWN_STATES"
    }, {
        "CONF_WARNING_SOURCE": "warning_source",
        "WARNING_SOURCE_NONE": "none",
        "_entry_entity_ids": lambda hass, source: [],
        "cos": __import__("math").cos, "hypot": __import__("math").hypot,
        "radians": __import__("math").radians,
    })


def test_future_conditional_cancel_keeps_active_window_order():
    check = _provider()["_evaluate_air_warning"]
    actions = "Schließen Sie Fenster und Türen."
    for text in (
        "Die Warnung wird aufgehoben, sobald der Einsatz beendet ist.",
        "Die Warnung wird aufgehoben, wenn die Luft wieder sauber ist.",
        "Die Warnung soll später aufgehoben werden.",
        "Wir informieren Sie nach der Entwarnung.",
    ):
        assert check("Rauchentwicklung", text, actions) == "danger", text
    assert check("Rauchentwicklung", "Die Warnung wird aufgehoben.", actions) == "clear"
    assert check("Entwarnung: Rauchentwicklung", "Gefahr vorüber", actions) == "clear"
    assert check("Rauchentwicklung", "Die Warnung wird aufgehoben, sobald alles sicher ist.", actions, "Cancel") == "clear"


def test_cap_references_only_return_old_identifiers():
    f = _provider()["_warning_reference_ids"]
    stamp = "2026-10-11T16:00:00+00:00"
    assert f(f"sender@example.org,smoke-id,{stamp} sender@example.org,chemical-id,{stamp}") == {"smoke-id", "chemical-id"}
    assert f([{"identifier": "smoke-id"}, {"identifier": "chemical-id"}]) == {"smoke-id", "chemical-id"}
    assert f("Entwarnung wird später gegeben") == set()


def test_auto_clear_requires_all_prior_cap_warning_identities():
    f = _safety()["_warning_provider_availability"]
    key = "auto_warning:50.7:7.1:nina_auto_mowas"
    previous = {"source_key": key, "warning_ids": ["mow.smoke-id", "mow.chemical-id"]}
    hass = SimpleNamespace()
    entry = SimpleNamespace(data={})
    warning = SimpleNamespace(
        safety_source_key="auto_warning:50.7:7.1", provider_availability={key: True},
        nina_status="clear", official_close_instruction=False,
        weather_hard_lock=False, warning_notice_kind="all_clear", warning_ids={"mow.smoke-id"},
    )
    assert f(hass, entry, warning, previous) == ("unknown", key)
    warning.warning_ids = {"mow.smoke-id", "mow.chemical-id"}
    assert f(hass, entry, warning, previous) == ("clear", key)
    warning.warning_ids = {"unrelated-id"}
    assert f(hass, entry, warning, previous) == ("unknown", key)
    warning.warning_ids = {"mow.smoke-id", "mow.chemical-id"}
    warning.provider_availability = {key: False}
    assert f(hass, entry, warning, previous) == ("unknown", key)


def test_manual_cancel_with_new_id_and_cap_reference():
    f = _safety()["_warning_provider_availability"]
    prior = {"source_key": "nina-entry", "warning_ids": ["mow.smoke-id"]}
    warning = SimpleNamespace(
        warning_notice_kind="all_clear", warning_ids={"mow.smoke-id"},
        nina_status="clear", official_close_instruction=False,
        weather_hard_lock=False, provider_availability={},
    )
    hass = SimpleNamespace(config_entries=SimpleNamespace(
        async_get_entry=lambda k: SimpleNamespace(domain="nina", entry_id=k)))
    entry = SimpleNamespace(data={"warning_source": "nina-entry"})
    assert f(hass, entry, warning, prior) == ("clear", "nina-entry")
    warning.warning_ids = {"new-cancel-message-id"}
    assert f(hass, entry, warning, prior) == ("unknown", "nina-entry")


def test_merge_does_not_store_cancellation_ids_as_active_hazards():
    scope = _provider()
    A = scope["WarningAssessment"]
    auto = A(nina_status="danger", official_close_instruction=True,
             safety_source_key="auto_warning:1:2:nina_auto_mowas", warning_ids={"mow.smoke-id"})
    manual = A(nina_status="clear", warning_notice_kind="all_clear",
               warning_ids={"unrelated-drinking-water-id"})
    merged = scope["_merge_warning_assessments"](auto, manual)
    assert merged.nina_status == "danger"
    assert merged.warning_ids == {"mow.smoke-id"}
    assert merged.warning_notice_kind is None


def test_temperature_must_win_over_dryness_and_dry_airing_stays_brief():
    from test_v0114_pure import NEW, Input
    r = NEW.evaluate_room(Input(
        indoor_temp=16.88, target_temp=24.73, outdoor_temp=24.31,
        indoor_humidity=28.75, outdoor_humidity=25.34,
        co2=1200, hours_since_airing=2, window_open=False,
    ))
    assert (r.mode, r.decision_need, r.primary_need) == ("erwaermen", "temperature", "temperature")
    assert r.room_status_color == "orange"
    dry = NEW.evaluate_room(Input(
        indoor_temp=22, target_temp=22, outdoor_temp=24,
        indoor_humidity=35, outdoor_humidity=65, hours_since_airing=1,
    ))
    assert dry.mode == "feuchte_befeuchten"
    assert dry.duration_key == "5_8"


def test_partial_or_future_clear_is_ambiguous_not_authoritative():
    classifiers = _provider()
    partial = classifiers["_is_ambiguous_clear_update"]
    assert partial("Teilentwarnung: Der Rauch zieht langsam ab")
    assert partial("Die Warnung wird aufgehoben, sobald der Einsatz beendet ist")
    assert not partial("Warnung ist aufgehoben", "Cancel")
    assert not partial("Trinkwasser abkochen bis zur ausdrücklichen Entwarnung")
    f = _safety()["_warning_provider_availability"]
    key = "auto_warning:50.7:7.1:nina_auto_mowas"
    warning = SimpleNamespace(
        safety_source_key="auto_warning:50.7:7.1", provider_availability={key: True},
        nina_status="none", official_close_instruction=False, weather_hard_lock=False,
        warning_notice_kind=None, warning_ids=set(), warning_ambiguous_clear=True,
    )
    previous = {"source_key": key, "warning_ids": ["smoke-id", "chemical-id"]}
    assert f(SimpleNamespace(), SimpleNamespace(data={}), warning, previous) == ("unknown", key)


def test_bare_entwarnung_cannot_override_continued_close_instruction():
    """A generic headline is weaker than an explicit current protective order."""
    evaluate = _provider()["_evaluate_air_warning"]
    assert evaluate(
        "Entwarnung", "Die Lage hat sich verbessert.",
        "Fenster und Türen weiterhin geschlossen halten.", "Minor",
    ) == "danger"
    # Only authenticated CAP Cancel or a definite full withdrawal may beat
    # potentially stale close instructions.
    assert evaluate(
        "Entwarnung", "Die Warnung wurde aufgehoben.",
        "Fenster und Türen weiterhin geschlossen halten.", "Cancel",
    ) == "clear"


def test_cap_cancel_preserves_reference_without_reporting_active_clear():
    """A CAP cancellation must remain reconcilable with an old saved hard lock."""
    scope = _provider()
    warning = SimpleNamespace(
        warning_id="cancel-123", provider_domain="nina_auto", category="weather",
        headline="Entwarnung: Gefahr ist vorüber", event="",
        description="Die Warnung wurde aufgehoben.",
        instruction="Fenster und Türen geschlossen halten.",
        severity="Extreme", msg_type="Cancel", expires=None, effective=None,
        references="mow@example.org,smoke-123,2026-10-02T09:00:00Z",
        evidence_at=None, issued_at=None, sender="",
    )
    data = SimpleNamespace(
        provider_domain="nina_auto", safety_source_key="auto_warning:50.7:7.1",
        coverage=None, error=None, region_ars=None, active_sources=[],
        available=True, source_availability={}, warnings=[warning],
    )
    scope["auto_warning_data"] = lambda *_args: data
    assessed = scope["_automatic_warning_assessment"](
        SimpleNamespace(), SimpleNamespace(data={})
    )
    assert assessed.nina_status == "none"
    assert assessed.official_close_instruction is False
    assert assessed.weather_danger is False
    assert assessed.warning_notice_kind == "all_clear"
    assert assessed.warning_ids

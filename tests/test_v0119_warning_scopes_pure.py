"""Scoped source conflicts and geographic/temporal gust applicability, without HA."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lb_scoped_warning_policy", ROOT / "custom_components/lueftungsberater/warning_policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
NOW = datetime(2026, 10, 24, 12, 30, tzinfo=timezone.utc)


def warning(**changes):
    return SimpleNamespace(**{
        "warning_id": "scoped", "provider_domain": "nina_auto_dwd", "headline": "Windböen",
        "description": "", "parameters": {}, "effective": NOW - timedelta(hours=2),
        "onset": NOW - timedelta(minutes=30), "expires": NOW + timedelta(hours=9),
        "instruction": "", "event": "", "category": "weather", "severity": "Moderate",
        "msg_type": "Alert", "references": "", "sender": "DWD", "issued_at": NOW - timedelta(hours=2),
        "evidence_at": NOW, **changes})


def assess(description="", parameters=None, *, now=NOW, elevation=60, **changes):
    return policy.assess_official_warning(warning(description=description, parameters=parameters or {}, **changes),
                                          now, elevation=elevation)


@pytest.mark.parametrize("description,parameters", [
    ("Böen 110 km/h.", {"gusts": "70 km/h"}),
    ("Böen 70 km/h.", {"gusts": "110 km/h"}),
    ("Böen 110 km/h, Schäden sind nicht auszuschließen.", {"gusts": "70 km/h"}),
])
def test_disjoint_general_values_keep_both_sources_and_protect_against_high_gusts(description, parameters):
    result = assess(description, parameters)
    assert result["hard_lock"] and result["gust_conflict"]
    assert result["gust_max_kmh"] == result["gust_min_kmh"] == 110
    assert {e["source"] for e in result["gust_evidence"]} == {"description", "parameter"}
    assert {e["max"] for e in result["gust_evidence"]} == {70, 110}
    json.dumps(result, allow_nan=False)


def test_6400_conflict_and_location_combinations():
    count = 0
    for high in range(90, 130):
        for low in range(20, 60):
            for description_speed, parameter_speed in [(high, low), (low, high)]:
                result = assess(f"Böen {description_speed} km/h.", {"gusts": f"{parameter_speed} km/h"})
                assert result["hard_lock"] and result["gust_conflict"], result
                assert result["gust_max_kmh"] == high
                count += 1
    qualifiers = ["nur in höheren Lagen", "ausschließlich in den Bergen", "nur im Norden",
                  "in höheren Lagen", "in tieferen Lagen", "only in the mountains",
                  "only in higher areas", "nur in der Region Eifel"]
    for qualifier in qualifiers:
        for speed in range(90, 110):
            for elevation in [None, 60, 800, 1800]:
                for separator in [" ", ", ", " und ", " (", ", jedoch "]:
                    result = assess(f"Böen {speed} km/h{separator}{qualifier}.",
                                    {"gusts": f"{speed} km/h"}, elevation=elevation)
                    assert not result["hard_lock"] and result["gust_max_kmh"] is None, result
                    assert result["gust_scope_uncertain"]
                    count += 1
    assert count == 6400


@pytest.mark.parametrize("description,parameters,expected,conflict", [
    ("Böen 70 km/h, in höheren Lagen 110 km/h.", {"gusts": "110 km/h"}, 70, False),
    ("In den Bergen Böen 110 km/h, allgemein 70 km/h.", {"gusts": "110 km/h"}, 70, False),
    ("Böen 110 km/h, in höheren Lagen 140 km/h.", {"gusts": "70 km/h"}, 110, False),
    ("Böen 70 km/h, in höheren Lagen 140 km/h.", {"gusts": "110 km/h"}, 70, False),
    ("Böen 70 km/h.", {"exposed gusts": "110 km/h"}, 70, False),
    ("Böen 110 km/h auch in höheren Lagen.", {"gusts": "70 km/h"}, 110, True),
])
def test_conflict_comparison_respects_each_values_scope(description, parameters, expected, conflict):
    result = assess(description, parameters)
    assert result["gust_max_kmh"] == expected
    assert result["hard_lock"] is (expected >= 90)
    assert result["gust_conflict"] is conflict


@pytest.mark.parametrize("elevation,locked", [(60, False), (1000, False), (1001, True), (None, False)])
def test_numeric_height_is_verified_instead_of_discarded(elevation, locked):
    result = assess("Böen 110 km/h nur oberhalb 1000 m.", {"gusts": "70 km/h"}, elevation=elevation)
    assert result["hard_lock"] is locked


def test_scoped_parameter_is_independent_of_other_unverified_description_claims():
    result = assess("Böen 70 km/h in tieferen Lagen.", {"gusts above 1000 m": "110 km/h"}, elevation=1200)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110
    assert result["gust_scope_uncertain"]


@pytest.mark.parametrize("description,parameters", [
    ("Böen 110 km/h ab 18 Uhr UTC.", {"gusts": "110 km/h"}),
    ("Böen 70 km/h bis 18 Uhr UTC, Böen 110 km/h ab 18 Uhr UTC.", {"gusts": "110 km/h"}),
    ("Böen 70 km/h bis 18 Uhr UTC.", {"gusts": "110 km/h ab 18 Uhr UTC"}),
    ("Böen 110 km/h ab 2026-10-24T18:00:00Z.", {"gusts": "110 km/h"}),
])
def test_later_high_gusts_use_their_own_thirty_minute_lead(description, parameters):
    early = assess(description, parameters)
    assert not early["hard_lock"] and not early["gust_conflict"]
    assert early["lock_from"] == "2026-10-24T17:30:00+00:00"
    assert early["next_transition"] == early["lock_from"]
    before = NOW.replace(hour=17, minute=29, second=59)
    assert not assess(description, parameters, now=before)["hard_lock"]
    at_start = assess(description, parameters, now=before + timedelta(seconds=1))
    assert at_start["hard_lock"] and at_start["phase"] == "prelock"
    assert assess(description, parameters, now=NOW.replace(hour=18, minute=0))["phase"] == "active"


@pytest.mark.parametrize("qualifier", ["morgen", "später", "in der Nacht", "ab 99 Uhr UTC", "ab 18 Uhr"])
def test_unresolvable_time_does_not_become_a_current_parameter_forecast(qualifier):
    result = assess(f"Böen 110 km/h {qualifier}.", {"gusts": "110 km/h"})
    assert not result["hard_lock"] and result["gust_time_uncertain"]
    assert result["phase"] == "time_uncertain"


def test_scoped_gust_expiry_releases_before_the_warning_expiry():
    description = "Böen 110 km/h bis 14 Uhr UTC, Böen 70 km/h ab 14 Uhr UTC."
    first = assess(description, {"gusts": "110 km/h"})
    assert first["hard_lock"] and first["lock_ends"] == "2026-10-24T14:00:00+00:00"
    after = assess(description, {"gusts": "110 km/h"}, now=NOW.replace(hour=14, minute=0))
    assert not after["hard_lock"] and after["gust_max_kmh"] == 70
    assert first["next_transition"] == "2026-10-24T14:00:00+00:00"


def test_cross_day_or_offset_ambiguous_clock_time_is_not_guessed():
    result = assess("Böen 110 km/h ab 18 Uhr UTC.", {"gusts": "110 km/h"},
                    expires=NOW + timedelta(days=1))
    assert not result["hard_lock"] and result["gust_time_uncertain"]


def test_real_negation_and_negated_damage_keep_opposite_meanings():
    assert not assess("Böen über 90 km/h sind ausgeschlossen.", {"gusts": "110 km/h"})["hard_lock"]
    assert assess("Böen 110 km/h, Schäden sind nicht auszuschließen.", {"gusts": "70 km/h"})["hard_lock"]


def _provider_case(record):
    from test_v0114_complete2_pure import _provider
    scope = _provider()
    scope["dt_util"] = SimpleNamespace(utcnow=lambda: NOW)
    scope["effective_location"] = lambda *args: SimpleNamespace(elevation=60)
    scope["auto_warning_data"] = lambda *args: SimpleNamespace(
        provider_domain="nina_auto", safety_source_key="auto_warning:50.7:7.1",
        coverage="civil_and_weather", error=None, region_ars="", active_sources=[],
        source_availability={}, available=True, warnings=[record], fetched_at=NOW)
    entry = SimpleNamespace(data={}, entry_id="scope-test")
    return scope, entry


def test_actual_provider_retains_conflicts_in_notice_and_safety_observation():
    scope, entry = _provider_case(warning(description="Böen 110 km/h.", parameters={"gusts": "70 km/h"}))
    result = scope["_automatic_warning_assessment"](SimpleNamespace(), entry)
    assert result.weather_hard_lock
    assert result.warning_notices[0]["gust_conflict"]
    assert result.warning_observations[0]["notice"]["gust_conflict"]
    assert result.weather_reason_args["gust_kmh"] == 110


def test_actual_provider_caps_persistence_at_gust_end_instead_of_cap_expiry():
    record = warning(description="Böen 110 km/h bis 14 Uhr UTC.", parameters={"gusts": "110 km/h"})
    scope, entry = _provider_case(record)
    result = scope["_automatic_warning_assessment"](SimpleNamespace(), entry)
    assert result.weather_hard_lock
    assert result.hard_safety_expires_at == NOW.replace(hour=14, minute=0)
    assert result.warning_observations[0]["expires"] == "2026-10-24T14:00:00+00:00"
    manual = scope["WarningAssessment"]()
    scope["_apply_manual_official_notice"](manual, record, elevation=60)
    assert manual.hard_safety_expires_at == result.hard_safety_expires_at
    assert manual.warning_observations[0]["expires"] == result.warning_observations[0]["expires"]


def test_explicit_clock_zone_is_converted_without_inventing_local_timezone():
    result = assess("Böen 110 km/h ab 18:00 Uhr MESZ.", {"gusts": "110 km/h"})
    assert not result["hard_lock"]
    assert result["lock_from"] == "2026-10-24T15:30:00+00:00"


def test_additive_location_at_the_start_does_not_claim_a_general_forecast():
    assert not assess("Auch in höheren Lagen Böen 110 km/h.", {"gusts": "110 km/h"})["hard_lock"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h ab 18 Uhr UTC werden nicht erwartet.",
    "Böen 110 km/h oberhalb 1000 m werden nicht erwartet.",
])
def test_scoped_negation_still_belongs_to_the_wind_forecast(description):
    result = assess(description, {"gusts": "110 km/h"}, now=NOW.replace(hour=18), elevation=1500)
    assert not result["hard_lock"]


def test_another_subjects_clock_time_does_not_postpone_the_wind_forecast():
    result = assess("Böen 110 km/h, Schäden ab 18 Uhr UTC möglich.", {"gusts": "70 km/h"})
    assert result["hard_lock"] and result["gust_conflict"]
    assert result["gust_onset"] == warning().onset.isoformat()


def test_equivalent_numeric_height_scopes_are_compared_across_languages_and_units():
    result = assess("Böen 110 km/h oberhalb 914.4 m.", {"gusts above 3000 ft": "70 km/h"}, elevation=1200)
    assert result["hard_lock"] and result["gust_conflict"]


def test_cached_notice_uses_the_gust_onset_instead_of_the_overall_event_onset():
    from test_v0114_complete2_pure import _extract
    now = NOW.replace(hour=17, minute=45)
    notice = assess("Böen 110 km/h ab 18 Uhr UTC.", {"gusts": "70 km/h"}, now=now)
    assert notice["phase"] == "prelock"
    scope = _extract("safety_state.py", {"_apply_warning_record"}, {
        "_parse_datetime": policy.aware, "dt_util": SimpleNamespace(utcnow=lambda: now)})
    warnings = SimpleNamespace(weather_hard_lock=False, source_weather_entity=None,
                               official_close_instruction=False, warning_notices=[], next_transition_at=None)
    scope["_apply_warning_record"](warnings, {"warning_records": [{
        "kind": "warning_weather_danger", "reason_key": "official_wind_prelock", "notice": notice,
        "valid_until": "2026-10-24T18:30:00+00:00"}]}, restore_identity=False)
    assert warnings.warning_notices[0]["phase"] == "prelock"
    assert warnings.next_transition_at == NOW.replace(hour=18, minute=0)


@pytest.mark.parametrize("field", ["effective", "onset", "expires", "event_end"])
def test_malformed_cap_period_is_visible_but_cannot_create_a_lock(field):
    result = assess("Böen 110 km/h.", {"gusts": "70 km/h"}, **{field: "bad-time"})
    assert not result["hard_lock"] and result["phase"] == "time_uncertain"


def test_scoped_negative_headline_does_not_become_a_positive_flat_parameter():
    result = assess(parameters={"gusts": "110 km/h"}, now=NOW.replace(hour=18),
                    headline="Böen 110 km/h ab 18 Uhr UTC werden nicht erwartet.")
    assert not result["hard_lock"]


def test_conflicting_headline_and_description_periods_do_not_form_an_empty_lock_interval():
    result = assess("Böen 110 km/h bis 18 Uhr UTC.", {"gusts": "110 km/h"},
                    headline="Böen ab 18 Uhr UTC", now=NOW.replace(hour=17, minute=45))
    assert not result["hard_lock"] and result["gust_time_uncertain"]

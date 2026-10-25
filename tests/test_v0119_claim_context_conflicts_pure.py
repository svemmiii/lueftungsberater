"""Independent claim, context and conflict regression tests for official gusts."""
from datetime import datetime, timedelta
import json
import math
import operator

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


# Preserve the independent audit's original 22 regression expectations.
@pytest.mark.parametrize('desc', [
    'Böen 110 km/h bei gefrierendem Regen.',
    'Böen 110 km/h bei Gewitterlagen.',
    'Böen 110 km/h bei Sturmregen.',
    'Böen 110 km/h bei Temperaturen unter null Grad.',
    'Böen 110 km/h bei aufziehendem Nebel.',
])
def test_weather_conditions_are_not_places(desc):
    r=assess(desc)
    assert r['hard_lock'] and not r['gust_scope_uncertain']

@pytest.mark.parametrize('desc', [
    'Böen 110 km/h im gesamten amtlichen Warnbereich.',
    'Böen 110 km/h über das gesamte Warngebiet verteilt.',
    'Böen 110 km/h im gesamten Gebiet der Warnung.',
    'Böen 110 km/h im gesamten Bereich der Warnung.',
])
def test_complete_matched_cap_area_applies(desc):
    r=assess(desc)
    assert r['hard_lock'] and not r['gust_scope_uncertain']

@pytest.mark.parametrize('height_text', [
    'in einer Höhe von mehr als 1200 m',
    'auf Höhen über 1200 m',
    'in Lagen höher als 1200 m',
])
def test_height_comparisons_apply_at_1500m(height_text):
    r=assess(f'Böen 110 km/h {height_text}.', elevation=1500)
    assert r['hard_lock'] and not r['gust_scope_uncertain']

def test_negation_with_attribution():
    assert not assess('Böen 110 km/h bleiben nach Angaben des DWD aus.')['hard_lock']

def test_geographical_from_to_corridor():
    r=assess('Böen 110 km/h von Köln nach Bonn.')
    assert not r['hard_lock'] and r['gust_scope_uncertain']

@pytest.mark.parametrize('text', [
    'Böen 110 km/h sind ausgeschlossen; Böen 110 km/h werden erwartet.',
    'Böen 110 km/h werden erwartet; Böen 110 km/h sind ausgeschlossen.',
])
def test_contradictory_claims_within_same_description_are_flagged(text):
    r=assess(text)
    assert r['gust_polarity_conflict'] and r['gust_conflict']

def test_earlier_positive_forecast_cannot_be_silently_overridden_by_late_headline():
    r=assess('Böen 110 km/h ab 14 Uhr UTC.',
             headline='Böen 110 km/h ab 18 Uhr UTC.', now=NOW.replace(hour=15,minute=0))
    assert r['hard_lock'] or r['gust_conflict'], r

@pytest.mark.parametrize('desc,locked', [
    ('Böen 110 km/h bei Starkregen.',True),
    ('Böen 110 km/h ab einer Höhe von 1200 m.',False),
    ('Böen 110 km/h nur im Harz.',False),
    ('Böen 110 km/h werden nicht erwartet.',False),
    ('Böen 110 km/h überall im Warngebiet.',True),
])
def test_existing_safe_controls(desc,locked):
    assert assess(desc,elevation=60)['hard_lock'] is locked


# Preserve all 95 original inputs/expectations; the two audit suites overlap.
AUDIT_CASES = [
    ('Es kommt zu Böen von 110 km/h.', True, {}),
    ('Es ist mit Böen von 110 km/h zu rechnen.', True, {}),
    ('Windböen können 110 km/h erreichen.', True, {}),
    ('Böen bis 110 km/h werden gemeldet.', True, {}),
    ('Der Wind bringt Böen mit 110 km/h.', True, {}),
    ('Es sind Windböen mit 110 km/h möglich.', True, {}),
    ('Schwere Windböen mit Spitzen von 110 km/h.', True, {}),
    ('Sturmböen erreichen 110 km/h.', True, {}),
    ('Die stärksten Böen liegen bei 110 km/h.', True, {}),
    ('Mit Windböen bis 110 km/h ist zu rechnen.', True, {}),
    ('110 km/h in Böen sind möglich.', True, {}),
    ('Gusts up to 110 km/h are forecast.', True, {}),
    ('Rafales de vent jusqu’à 110 km/h.', True, {}),
    ('Rachas de viento de hasta 110 km/h.', True, {}),
    ('Raffiche di vento fino a 110 km/h.', True, {}),
    ('Böen bis 110 km/h sind nicht möglich.', False, {}),
    ('Es sind keine Böen bis 110 km/h zu erwarten.', False, {}),
    ('Böen von 110 km/h bleiben aus.', False, {}),
    ('Mit Böen von 110 km/h ist nicht zu rechnen.', False, {}),
    ('Böen 110 km/h sind nicht zu befürchten.', False, {}),
    ('Böen 110 km/h treten in keinem Fall auf.', False, {}),
    ('Böen von 110 km/h lassen sich ausschließen.', False, {}),
    ('Böen 110 km/h sind nicht angekündigt.', False, {}),
    ('Böen 110 km/h bleiben nach Angaben des DWD aus.', False, {}),
    ('Windböen 110 km/h nicht zu erwarten.', False, {}),
    ('Wind gusts of 110 km/h will not occur.', False, {}),
    ('Wind gusts of 110 km/h are ruled out.', False, {}),
    ('Il n’y aura pas de rafales de 110 km/h.', False, {}),
    ('No se esperan rachas de 110 km/h.', False, {}),
    ('Non sono previste raffiche di vento fino a 110 km/h.', False, {}),
    ('Böen 110 km/h, keine Überschwemmungen erwartet.', True, {}),
    ('Böen 110 km/h; Gewitter treten nicht auf.', True, {}),
    ('Böen 110 km/h und keine Glätte.', True, {}),
    ('Böen 110 km/h, Sturmfluten sind ausgeschlossen.', True, {}),
    ('Windböen 110 km/h, aber keine Niederschläge.', True, {}),
    ('Windböen 110 km/h. Schäden können nicht ausgeschlossen werden.', True, {}),
    ('Wind gusts of 110 km/h but no hail is expected.', True, {}),
    ('Windböen 110 km/h, Regen bleibt definitiv aus.', True, {}),
    ('Böen 110 km/h im Westerwald.', False, {}),
    ('Böen 110 km/h am Rhein.', False, {}),
    ('Böen 110 km/h im Norden Nordrhein-Westfalens.', False, {}),
    ('Böen 110 km/h entlang des Rheins.', False, {}),
    ('Böen 110 km/h im südlichen Teil des Warngebietes.', False, {}),
    ('Böen 110 km/h auf Inseln.', False, {}),
    ('Böen 110 km/h in Bergtälern.', False, {}),
    ('Böen 110 km/h an der Landesgrenze.', False, {}),
    ('Böen 110 km/h in der Nähe von Köln.', False, {}),
    ('Böen 110 km/h westlich von Essen.', False, {}),
    ('Böen 110 km/h von Köln nach Bonn.', False, {}),
    ('Böen 110 km/h im Raum Köln.', False, {}),
    ('Böen 110 km/h im kompletten Warngebiet.', True, {}),
    ('Böen 110 km/h in sämtlichen Teilen des Warngebiets.', True, {}),
    ('Böen 110 km/h im ganzen Warngebiet.', True, {}),
    ('Böen 110 km/h im gesamten amtlichen Warnbereich.', True, {}),
    ('Böen 110 km/h über das gesamte Warngebiet verteilt.', True, {}),
    ('Böen 110 km/h im gesamten Gebiet der Warnung.', True, {}),
    ('Böen 110 km/h im gesamten Bereich der Warnung.', True, {}),
    ('Böen 110 km/h bei gefrierendem Regen.', True, {}),
    ('Böen 110 km/h bei heftigem Starkregen.', True, {}),
    ('Böen 110 km/h während der Gewitter.', True, {}),
    ('Böen 110 km/h bei Gewitterlagen.', True, {}),
    ('Böen 110 km/h während Schneefalls.', True, {}),
    ('Böen 110 km/h bei Sturmregen.', True, {}),
    ('Böen 110 km/h bei Regenschauern.', True, {}),
    ('Böen 110 km/h im Zusammenhang mit Gewittern.', True, {}),
    ('Böen 110 km/h mit heftigem Regen.', True, {}),
    ('Böen 110 km/h bei Hagelschlag.', True, {}),
    ('Böen 110 km/h bei Temperaturen unter null Grad.', True, {}),
    ('Böen 110 km/h bei aufziehendem Nebel.', True, {}),
    ('Böen 110 km/h in Höhen oberhalb von 1200 m.', False, {'elevation': 60}),
    ('Böen 110 km/h in Höhen oberhalb von 1200 m.', True, {'elevation': 1500}),
    ('Böen 110 km/h in einer Höhe von mehr als 1200 m.', False, {'elevation': 60}),
    ('Böen 110 km/h in einer Höhe von mehr als 1200 m.', True, {'elevation': 1500}),
    ('Böen 110 km/h ab 1200 m Höhe.', False, {'elevation': 60}),
    ('Böen 110 km/h ab 1200 m Höhe.', True, {'elevation': 1500}),
    ('Böen 110 km/h auf Höhen über 1200 m.', False, {'elevation': 60}),
    ('Böen 110 km/h auf Höhen über 1200 m.', True, {'elevation': 1500}),
    ('Böen 110 km/h in Lagen höher als 1200 m.', False, {'elevation': 60}),
    ('Böen 110 km/h in Lagen höher als 1200 m.', True, {'elevation': 1500}),
    ('Böen 110 km/h auf über 1200 m.', False, {'elevation': 60}),
    ('Böen 110 km/h auf über 1200 m.', True, {'elevation': 1500}),
    ('Böen 110 km/h bis zu 1200 m Höhe.', True, {'elevation': 60}),
    ('Böen 110 km/h bis zu 1200 m Höhe.', False, {'elevation': 1500}),
    ('Böen 110 km/h unter 1200 m Höhe.', True, {'elevation': 60}),
    ('Böen 110 km/h unter 1200 m Höhe.', False, {'elevation': 1500}),
    ('Böen 110 km/h ab morgen.', False, {}),
    ('Böen 110 km/h ab Montag.', False, {}),
    ('Böen 110 km/h ab dem Abend.', False, {}),
    ('Böen 110 km/h ab 2026-10-24T18:00:00Z.', False, {}),
    ('Böen 110 km/h ab 18 Uhr UTC.', False, {}),
    ('Böen 110 km/h ab 18:00 UTC.', False, {}),
    ('Böen 110 km/h ab 18.00 Uhr UTC.', False, {}),
    ('Böen 70 km/h, ab 18 Uhr UTC Böen 110 km/h.', False, {'now': '2026-10-24 16:00:00+00:00'}),
    ('Böen 110 km/h nur bis 14 Uhr UTC.', False, {'now': '2026-10-24 16:00:00+00:00'}),
    ('Böen 110 km/h von 18 Uhr UTC bis 20 Uhr UTC.', False, {'now': '2026-10-24 16:00:00+00:00'}),

]


@pytest.mark.parametrize("description,locked,options", AUDIT_CASES)
def test_independent_95_case_audit(description, locked, options):
    fields = dict(options)
    if isinstance(fields.get("now"), str):
        fields["now"] = datetime.fromisoformat(fields["now"])
    assert assess(description, **fields)["hard_lock"] is locked


@pytest.mark.parametrize("condition", ["gefrierendem Regen", "aufziehendem Nebel", "Gewitterlagen",
                                       "Sturmregen", "Temperaturen unter null Grad", "Temperaturen unter -5 Grad Celsius"])
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h bei {condition}.", True),
    ("Bei {condition} sind Böen 110 km/h möglich.", True),
    ("Böen 110 km/h sind bei {condition} nicht ausgeschlossen.", True),
    ("Böen 110 km/h sind bei {condition} nicht zu erwarten.", False),
])
def test_full_weather_condition_groups_retain_their_own_predicate(condition, frame, locked):
    result = assess(frame.format(condition=condition))
    assert result["hard_lock"] is locked and not result["gust_scope_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h bei aufziehendem Nebel im Harz.",
    "Böen 110 km/h bei Temperaturen unter null Grad im Harz.",
    "Bei gefrierendem Regen im Harz Böen 110 km/h.",
    "Böen 110 km/h bei Gefrierendhausen.", "Böen 110 km/h bei Gewitterlagenstadt.",
    "Böen 110 km/h bei Sturmregenheim.", "Böen 110 km/h bei aufziehendem Nebelhausen.",
])
def test_real_or_unknown_places_survive_weather_parsing(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("phrase", ["im gesamten amtlichen Warnbereich", "über das gesamte Warngebiet verteilt",
                                    "im gesamten Gebiet der Warnung", "im gesamten Bereich der Warnung"])
@pytest.mark.parametrize("unknown", [False, True])
def test_whole_area_noun_groups_only_use_verified_cap_coverage(phrase, unknown):
    result = assess(f"Böen 110 km/h {phrase}.", area_restriction_unknown=unknown)
    assert result["hard_lock"] is (not unknown)


@pytest.mark.parametrize("phrase", ["fast über das gesamte Warngebiet verteilt", "im gesamten Gebiet der Warnung im Harz",
                                    "im gesamten amtlichen Warnbereich des Harzes", "in Teilen des Gebietes der Warnung"])
def test_partial_or_separately_named_areas_do_not_become_universal(phrase):
    result = assess(f"Böen 110 km/h {phrase}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


HEIGHTS = [("in einer Höhe von mehr als", operator.gt), ("auf Höhen über", operator.gt),
           ("in Lagen höher als", operator.gt), ("in einer Höhe von weniger als", operator.lt),
           ("in Lagen niedriger als", operator.lt), ("auf Höhen unter", operator.lt),
           ("in Höhen mindestens", operator.ge), ("in Höhen höchstens", operator.le)]


@pytest.mark.parametrize("phrase,compare", HEIGHTS)
@pytest.mark.parametrize("height", [60, 1199.99, 1200, 1200.01, 1500])
@pytest.mark.parametrize("unit", ["m", "Metern"])
def test_height_quantity_operators_have_strict_or_inclusive_boundaries(phrase, compare, height, unit):
    result = assess(f"Böen 110 km/h {phrase} 1200 {unit}.", elevation=height)
    assert result["hard_lock"] is compare(height, 1200)
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("height", [None, True, math.inf, math.nan])
def test_quantity_syntax_does_not_verify_an_unknown_window_height(height):
    result = assess("Böen 110 km/h in einer Höhe von mehr als 1200 m.", elevation=height)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("source", ["nach Angaben des DWD", "nach Angaben der Meteorologen",
                                    "laut Wetterdienst", "according to Weather Agency"])
@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h bleiben {source} aus.", False),
    ("Böen 110 km/h bleiben, {source}, aus.", False),
    ("Böen 110 km/h sind {source} nicht zu erwarten.", False),
    ("Böen 110 km/h sind {source} nicht ausgeschlossen.", True),
    ("Böen 110 km/h, Schäden bleiben {source} aus.", True),
])
def test_source_attribution_is_a_bounded_adjunct_of_its_own_predicate(source, frame, locked):
    result = assess(frame.format(source=source))
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("phrase", ["von Köln nach Bonn", "von Neustadt nach Altdorf", "von Bad Godesberg nach Köln"])
@pytest.mark.parametrize("frame", ["Böen 110 km/h {place}.", "{place} Böen 110 km/h.", "Böen 110 km/h, {place}."])
def test_from_to_place_grammar_does_not_require_known_city_names(phrase, frame):
    result = assess(frame.format(place=phrase))
    assert not result["hard_lock"] and result["gust_scope_uncertain"]
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("negative", ["Böen 110 km/h sind ausgeschlossen", "Keine Böen über 90 km/h erwartet"])
@pytest.mark.parametrize("separator", ["; ", ". ", ", aber ", " und "])
@pytest.mark.parametrize("reverse", [False, True])
def test_conflict_is_between_claims_in_a_field_not_between_field_names(negative, separator, reverse):
    parts = [negative, "Böen 110 km/h werden erwartet"]
    if reverse:
        parts.reverse()
    result = assess(separator.join(parts) + ".")
    assert result["gust_conflict"] and result["gust_polarity_conflict"] and not result["hard_lock"]
    assert {item["source"] for item in result["gust_evidence"]} == {"description"}
    assert len({item["assertion_id"] for item in result["gust_evidence"]}) >= 2
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("field", ["headline", "event", "parameter"])
def test_multiple_claims_in_other_single_fields_are_also_compared(field):
    parts = ["Böen 110 km/h sind ausgeschlossen", "Böen 110 km/h werden erwartet"]
    changes = {field: "; ".join(parts)} if field != "parameter" else {}
    parameters = {"gusts": parts} if field == "parameter" else {}
    result = assess("", parameters, **changes)
    assert result["gust_polarity_conflict"] and not result["hard_lock"]


@pytest.mark.parametrize("hour,locked", [(12, True), (17, True), (18, False), (19, False)])
def test_a_denial_in_the_same_field_only_removes_its_overlapping_period(hour, locked):
    result = assess("Böen 110 km/h werden erwartet; Böen 110 km/h ab 18 Uhr UTC sind ausgeschlossen.",
                    now=NOW.replace(hour=hour), onset=NOW.replace(hour=0), expires=NOW.replace(hour=23))
    assert result["gust_polarity_conflict"] and result["hard_lock"] is locked


@pytest.mark.parametrize("description", [
    "Böen 110 km/h werden erwartet; Böen 110 km/h im Harz sind ausgeschlossen.",
    "Böen 110 km/h bis 14 Uhr UTC; Böen 110 km/h ab 18 Uhr UTC sind ausgeschlossen.",
    "Böen 110 km/h werden erwartet; Böen 70 km/h sind ausgeschlossen.",
])
def test_distinct_regions_periods_and_speed_sets_do_not_form_polarity_conflicts(description):
    result = assess(description)
    assert result["hard_lock"] and not result["gust_polarity_conflict"]


def test_disjoint_positive_values_in_one_field_remain_visible_and_protect_the_high_value():
    result = assess("Böen 70 km/h werden erwartet; Böen 110 km/h werden erwartet.")
    assert result["gust_conflict"] and not result["gust_polarity_conflict"]
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("offset,locked", [(-1801, False), (-1800, True), (0, True), (3600, True), (14400, True)])
def test_different_explicit_begin_times_keep_earliest_claim_and_mark_the_difference(reverse, field, offset, locked):
    early = "Böen 110 km/h ab 14 Uhr UTC."
    late = "Böen 110 km/h ab 18 Uhr UTC."
    body, heading = (late, early) if reverse else (early, late)
    start = NOW.replace(hour=14, minute=0, second=0)
    result = assess(body, now=start + timedelta(seconds=offset), **{field: heading})
    assert result["hard_lock"] is locked
    assert result["gust_conflict"] and result["gust_time_conflict"]
    assert not result["gust_polarity_conflict"] and not result["gust_time_uncertain"]
    assert result["lock_from"] == (start - timedelta(minutes=30)).isoformat()
    assert {item["declared_period"]["onset"] for item in result["gust_evidence"]} == {
        start.isoformat(), start.replace(hour=18).isoformat()}
    assert {item["onset"] for item in result["gust_evidence"]} == {
        start.isoformat(), start.replace(hour=18).isoformat()}


@pytest.mark.parametrize("reverse", [False, True])
def test_explicit_begin_conflicts_in_one_field_also_keep_both_claims(reverse):
    claims = ["Böen 110 km/h ab 14 Uhr UTC", "Böen 110 km/h ab 18 Uhr UTC"]
    if reverse:
        claims.reverse()
    result = assess("; ".join(claims), now=NOW.replace(hour=15, minute=0))
    assert result["hard_lock"] and result["gust_time_conflict"]
    assert result["lock_from"] == NOW.replace(hour=13, minute=30).isoformat()


def test_explicit_times_in_parameters_are_not_overwritten_by_the_headline():
    result = assess(parameters={"gusts": "110 km/h ab 14 Uhr UTC"},
                    headline="Böen 110 km/h ab 18 Uhr UTC", now=NOW.replace(hour=15, minute=0))
    assert result["hard_lock"] and result["gust_time_conflict"]
    assert result["lock_from"] == NOW.replace(hour=13, minute=30).isoformat()


def test_flat_parameter_time_inheritance_preserves_the_independent_description():
    result = assess("Böen 110 km/h ab 14 Uhr UTC", {"gusts": "110 km/h"},
                    headline="Böen 110 km/h ab 18 Uhr UTC", now=NOW.replace(hour=15, minute=0))
    assert result["hard_lock"] and result["gust_time_conflict"]
    parameter = next(item for item in result["gust_evidence"] if item["source"] == "parameter")
    assert parameter["time_source"] == "description" and parameter["time_bounds"] == ["onset"]
    assert parameter["declared_period"] == {}
    assert parameter["onset"] == NOW.replace(hour=14, minute=0).isoformat()


def test_untimed_matching_value_can_inherit_a_single_positive_headline_time():
    result = assess("Böen 110 km/h", {"gusts": "110 km/h"}, headline="Böen 110 km/h ab 18 Uhr UTC")
    assert not result["hard_lock"] and not result["gust_time_conflict"]
    assert result["lock_from"] == NOW.replace(hour=17, minute=30).isoformat()
    assert {item["onset"] for item in result["gust_evidence"]} == {NOW.replace(hour=18, minute=0).isoformat()}


def test_header_value_time_does_not_qualify_a_different_independent_value():
    result = assess("Böen 100 km/h werden erwartet", headline="Böen 110 km/h ab 18 Uhr UTC")
    assert result["hard_lock"] and result["gust_max_kmh"] == 100
    assert not result["gust_time_conflict"]


def test_nonoverlapping_positive_episodes_are_not_reported_as_different_start_estimates():
    result = assess("Böen 110 km/h von 14 Uhr UTC bis 16 Uhr UTC; Böen 110 km/h von 18 Uhr UTC bis 20 Uhr UTC.",
                    now=NOW.replace(hour=15, minute=0))
    assert result["hard_lock"] and not result["gust_time_conflict"] and not result["gust_conflict"]
    assert result["lock_ends"] == NOW.replace(hour=16, minute=0).isoformat()


def test_end_time_difference_is_visible_and_the_later_valid_claim_survives():
    result = assess("Böen 110 km/h bis 14 Uhr UTC.", headline="Böen 110 km/h bis 18 Uhr UTC.",
                    now=NOW.replace(hour=15, minute=0))
    assert result["hard_lock"] and result["gust_time_conflict"]
    assert result["lock_ends"] == NOW.replace(hour=18, minute=0).isoformat()


def test_equal_peak_and_onset_choose_the_longer_claim_without_mixing_bounds():
    result = assess("Böen 110 km/h bis 18 Uhr UTC.", headline="Böen 110 km/h bis 14 Uhr UTC.")
    assert result["hard_lock"] and result["gust_time_conflict"]
    assert result["lock_ends"] == NOW.replace(hour=18, minute=0).isoformat()
    assert result["gust_source"] == "description"


def test_different_zone_spellings_of_the_same_instant_are_not_a_conflict():
    result = assess("Böen 110 km/h ab 16 Uhr UTC.", headline="Böen 110 km/h ab 18 Uhr CEST.",
                    now=NOW.replace(hour=16, minute=0), expires=NOW.replace(hour=20, minute=0))
    assert result["hard_lock"] and not result["gust_time_conflict"] and not result["gust_conflict"]
    assert result["lock_from"] == NOW.replace(hour=15, minute=30).isoformat()


def test_unresolved_headline_clock_does_not_erase_a_separately_zoned_claim():
    result = assess("Böen 110 km/h ab 14 Uhr UTC.", headline="Böen 110 km/h ab 18 Uhr.",
                    now=NOW.replace(hour=15, minute=0))
    assert result["hard_lock"] and result["gust_time_uncertain"]
    assert result["lock_from"] == NOW.replace(hour=13, minute=30).isoformat()


def test_original_prose_bound_is_retained_even_when_cap_limits_the_effective_interval():
    result = assess("Böen 110 km/h ab 14 Uhr UTC.", onset=NOW.replace(hour=18, minute=0))
    item = result["gust_evidence"][0]
    assert item["declared_period"]["onset"] == NOW.replace(hour=14, minute=0).isoformat()
    assert item["onset"] == NOW.replace(hour=18, minute=0).isoformat()
    assert item["time_constraints"][0]["text"] == "ab 14 Uhr UTC"
    json.dumps(result, allow_nan=False)

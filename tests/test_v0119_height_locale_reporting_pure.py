"""Locale-aware height quantities, reporting grammar and combined conflicts."""
from datetime import timedelta
import json
import math
import operator

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


def _independent_825_cases():
    # Preserve every family and expectation of the independent (1)(9) audit.
    speeds = [20, 65, 89, 90, 91, 105, 110, 130]
    conditions = ["bei eisigen Temperaturen", "bei winterlichen Temperaturen", "bei arktischen Temperaturen",
                  "bei gefrierendem Nieselregen", "bei kräftigen Schauern", "bei heftigen Niederschlägen",
                  "bei Orkanregen", "bei Temperaturen unter -5 Grad Celsius", "bei Blitzschlag",
                  "bei starkem Gewitter", "bei Starkregen"]
    for speed in speeds:
        for condition in conditions:
            for description in [f"Böen {speed} km/h {condition}.",
                                f"{condition[0].upper() + condition[1:]} sind Böen {speed} km/h möglich."]:
                yield description, speed >= 90, {}, False
    areas = ["im gesamten Warngebiet", "im kompletten Warngebiet", "innerhalb des gesamten Warngebiets",
             "im ganzen offiziellen Warngebiet", "im gesamten betroffenen Warngebiet", "im ganzen amtlichen Warnbereich",
             "über das gesamte Warngebiet verteilt", "im gesamten Gebiet der Warnung"]
    for speed in speeds:
        for area in areas:
            yield f"Böen {speed} km/h {area}.", speed >= 90, {}, False
    negatives = ["sind nach neuesten Erkenntnissen nicht zu erwarten", "kann der DWD ausschließen",
                 "kann der Wetterdienst ausschließen", "sind laut amtlicher Einschätzung nicht zu erwarten",
                 "sind keinesfalls zu erwarten", "sind nicht zu erwarten", "werden nach Angaben des DWD nicht auftreten",
                 "werden definitiv nicht eintreten"]
    for speed in speeds:
        for predicate in negatives:
            yield f"Böen {speed} km/h {predicate}.", False, {}, False
    heights = ["oberhalb 1.200 m", "über 1.200 m", "unterhalb 1.200 m", "in Höhen über 1.200 m",
               "in Lagen oberhalb 1.200 Metern", "oberhalb 1200 m", "über 1200 m", "unterhalb 1200 m"]
    for speed in speeds:
        for height in heights:
            for elevation in [60, 1100, 1200, 1300, 1500]:
                above = any(word in height for word in ["oberhalb", "über", "Höhen über"])
                expected = speed >= 90 and (elevation > 1200 if above else elevation < 1200)
                yield f"Böen {speed} km/h {height}.", expected, {"elevation": elevation}, False
    for mean in [30, 50, 70, 89, 90, 110, 130]:
        for gust in [30, 65, 89, 90, 110]:
            for description in [f"Böen {gust} km/h, Wind {mean} km/h.", f"Wind {mean} km/h und Böen {gust} km/h.",
                                f"Böen {gust} km/h, durchschnittlicher Wind {mean} km/h."]:
                yield description, gust >= 90, {}, False
    for early in [13, 14, 15, 16]:
        for late in [17, 18, 19, 20]:
            for swap in [False, True]:
                a, b = (early, late) if not swap else (late, early)
                for hour in [early - 1, early, late]:
                    # early - 1 at :30 is exactly the 30-minute prelock boundary.
                    options = {"headline": f"Böen 110 km/h ab {a} Uhr UTC.", "now": NOW.replace(hour=hour, minute=30)}
                    yield f"Böen 110 km/h ab {b} Uhr UTC.", True, options, True


AUDIT_CASES = list(_independent_825_cases())
assert len(AUDIT_CASES) == 825


@pytest.mark.parametrize("description,locked,options,time_conflict", AUDIT_CASES)
def test_independent_825_case_audit(description, locked, options, time_conflict):
    result = assess(description, **options)
    assert result["hard_lock"] is locked
    if time_conflict:
        assert result["gust_conflict"] and result["gust_time_conflict"]


HEIGHT_NUMBERS = [
    ("oberhalb", "1.200", 1200, operator.gt), ("unterhalb", "1.200", 1200, operator.lt),
    ("above", "1,200", 1200, operator.gt), ("below", "1,200", 1200, operator.lt),
    ("above", "1.200", 1.2, operator.gt), ("below", "1.200", 1.2, operator.lt),
    ("oberhalb", "1,200", 1.2, operator.gt), ("unterhalb", "1,200", 1.2, operator.lt),
    ("ab", "1.200,5", 1200.5, operator.ge), ("bis", "1.200,5", 1200.5, operator.le),
    ("at least", "1,200.5", 1200.5, operator.ge), ("up to", "1,200.5", 1200.5, operator.le),
    ("oberhalb", "1.2", 1.2, operator.gt), ("oberhalb", "0.125", 0.125, operator.gt),
    ("oberhalb", "1.2345", 1.2345, operator.gt), ("above", ".5", 0.5, operator.gt),
    ("unterhalb", ",5", 0.5, operator.lt), ("oberhalb", "1 200", 1200, operator.gt),
    ("oberhalb", "1\u00a0200", 1200, operator.gt), ("above", "1\u202f200", 1200, operator.gt),
    ("above", "1 200.5", 1200.5, operator.gt), ("oberhalb", "1 200,5", 1200.5, operator.gt),
    ("oberhalb", "1'200", 1200, operator.gt), ("above", "1’200", 1200, operator.gt),
    ("oberhalb", "1.200.000", 1200000, operator.gt), ("above", "1,200,000", 1200000, operator.gt),
    ("oberhalb", "-1.200", -1200, operator.gt), ("below", "−1,200", -1200, operator.lt),
    ("au-dessus de", "1,200", 1.2, operator.gt),
    ("oberhalb", "1.20.0", None, None), ("below", "1,20,0", None, None),
    ("above", "1 20", None, None), ("oberhalb", "01.200", None, None),
    ("above", "01,200", None, None), ("au-dessus de", "1.200", None, None),
    ("above", "1e3", None, None), ("oberhalb", "1.200e0", None, None),
]


@pytest.mark.parametrize("relation,number,height,compare", HEIGHT_NUMBERS)
@pytest.mark.parametrize("point", ["low", "below", "equal", "above", "high"])
def test_complete_height_number_notation_has_locale_and_boundary_semantics(relation, number, height, compare, point):
    choices = {"low": 0, "below": (height or 1200) - 0.0001, "equal": height or 1200,
               "above": (height or 1200) + 0.0001, "high": 1500}
    elevation = choices[point]
    result = assess(f"Böen 110 km/h {relation} {number} m.", elevation=elevation)
    if height is None:
        assert not result["hard_lock"] and result["gust_scope_uncertain"]
    else:
        assert result["hard_lock"] is compare(elevation, height)
    assert not result["gust_time_uncertain"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("unit,number", [("ft", "3,000"), ("feet", "3 000"), ("m", "914.4")])
def test_exact_foot_conversion_keeps_equivalent_scopes_comparable(unit, number):
    result = assess("Böen 110 km/h oberhalb 914,4 m.",
                    {"gusts": f"70 km/h above {number} {unit}"}, elevation=1200)
    assert result["hard_lock"] and result["gust_value_conflict"]
    assert len({item["scope"] for item in result["gust_evidence"]}) == 1


@pytest.mark.parametrize("height,locked", [(914.399999, True), (914.4, False), (914.400001, False)])
def test_foot_conversion_does_not_move_a_strict_upper_height_boundary(height, locked):
    result = assess("Gusts 110 km/h below 3,000 ft.", elevation=height)
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("elevation", [None, True, math.inf, math.nan])
def test_grouped_height_is_not_verified_without_a_valid_window_elevation(elevation):
    result = assess("Böen 110 km/h oberhalb 1.200 m.", elevation=elevation)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("height,offset,locked", [(60, 0, False), (1500, -1801, False),
                                               (1500, -1800, True), (1500, 0, True)])
def test_height_grouping_does_not_rewrite_a_dot_clock_time(height, offset, locked):
    start = NOW.replace(hour=18, minute=0, second=0)
    result = assess("Böen 110 km/h oberhalb 1.200 m ab 18.00 Uhr UTC.",
                    elevation=height, now=start + timedelta(seconds=offset))
    assert result["hard_lock"] is locked and not result["gust_time_uncertain"]


@pytest.mark.parametrize("field", ["headline", "event", "description", "parameter"])
@pytest.mark.parametrize("height,locked", [(60, False), (1200, False), (1500, True)])
def test_each_source_uses_the_same_dimensional_number_parser(field, height, locked):
    text = "Böen 110 km/h oberhalb 1.200 m."
    changes = {field: text} if field in {"headline", "event"} else {}
    parameters = {"gusts": text} if field == "parameter" else {}
    result = assess(text if field == "description" else "", parameters, elevation=height, **changes)
    assert result["hard_lock"] is locked


@pytest.mark.parametrize("description", [
    "Böen 110 km/h bei außergewöhnlichen Temperaturen im Harz.",
    "Böen 110 km/h bei Eisigen Temperaturenhausen.", "Böen 110 km/h bei Orkanregenstadt.",
    "Böen 110 km/h bei Blitzschlaghausen.", "Böen 110 km/h bei Winterlichen Temperaturenbergen.",
])
def test_adjective_weather_grammar_does_not_consume_unknown_places(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("phrase", ["bei äußerst eisigen Temperaturen", "bei tropischen Temperaturen",
                                    "bei außergewöhnlichen Temperaturen", "bei unerwartetem Regen"])
@pytest.mark.parametrize("denied", [False, True])
def test_inflected_adjective_phrases_take_the_role_of_their_meteorological_head(phrase, denied):
    result = assess(f"Böen 110 km/h sind {phrase} {'nicht zu erwarten' if denied else 'möglich'}.")
    assert result["hard_lock"] is (not denied) and not result["gust_scope_uncertain"]


@pytest.mark.parametrize("phrase", ["innerhalb des gesamten Warngebiets", "im ganzen offiziellen Warngebiet",
                                    "im gesamten betroffenen Warngebiet"])
@pytest.mark.parametrize("cap_unknown", [False, True])
def test_universal_area_modifiers_do_not_supply_missing_cap_membership(phrase, cap_unknown):
    result = assess(f"Böen 110 km/h {phrase}.", area_restriction_unknown=cap_unknown)
    assert result["hard_lock"] is (not cap_unknown)


@pytest.mark.parametrize("phrase", ["innerhalb des nördlichen Warngebiets", "innerhalb des gesamten Warngebiets im Harz",
                                    "im gesamten höheren Warngebiet", "im gesamten offiziellen Warngebiet des Harzes",
                                    "fast innerhalb des gesamten Warngebiets", "in Teilen des betroffenen Warngebiets"])
def test_named_partial_and_qualified_regions_do_not_become_general(phrase):
    result = assess(f"Böen 110 km/h {phrase}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("frame,locked", [
    ("Böen 110 km/h sind nach neuesten Erkenntnissen nicht zu erwarten.", False),
    ("Böen 110 km/h sind nach aktuellen Erkenntnissen des DWD nicht zu erwarten.", False),
    ("Böen 110 km/h sind, nach neuesten Erkenntnissen, nicht zu erwarten.", False),
    ("Böen 110 km/h sind nach neuesten Erkenntnissen nicht ausgeschlossen.", True),
    ("Böen 110 km/h, Schäden sind nach neuesten Erkenntnissen nicht zu erwarten.", True),
    ("Böen 110 km/h kann der DWD ausschließen.", False),
    ("Böen 110 km/h kann der Wetterdienst ausschließen.", False),
    ("Böen 110 km/h kann der britische Wetterdienst ausschließen.", False),
    ("Böen 110 km/h kann der MetOffice ausschließen.", False),
    ("Böen 110 km/h kann der DWD nicht ausschließen.", True),
    ("Böen 110 km/h kann der DWD mit Sicherheit nicht ausschließen.", True),
    ("Böen 110 km/h können Schäden nicht ausschließen.", True),
    ("Böen 110 km/h können die Fenster beschädigen.", True),
    ("Böen 110 km/h, der DWD kann Schäden ausschließen.", True),
])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_reporting_actor_or_evidential_inset_belongs_to_its_own_predicate(frame, locked, parameters):
    result = assess(frame, parameters)
    assert result["hard_lock"] is locked


def test_combined_value_and_time_conflicts_have_independent_summary_flags():
    result = assess("Böen 110 km/h ab 18 Uhr UTC.", {"gusts": "70 km/h"},
                    headline="Böen 110 km/h ab 14 Uhr UTC.", now=NOW.replace(hour=15, minute=0))
    assert result["hard_lock"] and result["gust_conflict"]
    assert result["gust_value_conflict"] and result["gust_time_conflict"]
    assert not result["gust_polarity_conflict"]
    assert result["lock_from"] == NOW.replace(hour=13, minute=30).isoformat()
    json.dumps(result, allow_nan=False)

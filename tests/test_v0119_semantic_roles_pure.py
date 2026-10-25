"""Keep forecast polarity, weather conditions, height and CAP area roles apart."""
from datetime import timedelta
import json
import math
import random

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


NEGATIVE = [
    "Böen 110 km/h sind keinesfalls zu erwarten.",
    "Windböen 110 km/h werden keinesfalls auftreten.",
    "Böen 110 km/h wird es nicht geben.", "Böen 110 km/h kommen nicht vor.",
    "Böen 110 km/h sind keineswegs zu erwarten.", "Böen 110 km/h werden niemals erwartet.",
    "Böen 110 km/h werden auf keinen Fall auftreten.",
    "Böen 110 km/h werden in keinem Fall eintreten.",
    "Es werden keinesfalls Böen 110 km/h erwartet.",
    "Böen 110 km/h kommen definitiv nicht vor.", "Böen 110 km/h werden nicht vorkommen.",
]
POSITIVE = [
    "Böen 110 km/h wird es geben.", "Böen 110 km/h kommen vor.",
    "Böen 110 km/h werden definitiv vorkommen.",
    "Böen 110 km/h sind keinesfalls ausgeschlossen.",
    "Böen 110 km/h sind auf keinen Fall auszuschließen.",
    "Böen 110 km/h sind keineswegs unmöglich.",
    "Böen 110 km/h, Schäden sind keinesfalls zu erwarten.",
    "Böen 110 km/h, Hagel wird es nicht geben.",
    "Böen 110 km/h, Schäden kommen nicht vor.",
]


@pytest.mark.parametrize("description", NEGATIVE)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_negative_adverbs_and_existence_predicates_deny_their_own_gust_event(description, parameters):
    result = assess(description, parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("description", POSITIVE)
def test_negated_exclusion_or_negated_consequence_keeps_the_possible_wind(description):
    result = assess(description)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


@pytest.mark.parametrize("field", ["headline", "event"])
def test_an_emphatically_negative_header_is_kept_as_a_conflicting_assertion(field):
    result = assess("Böen 110 km/h werden erwartet.", **{field: NEGATIVE[0]})
    assert result["gust_polarity_conflict"] and not result["hard_lock"]
    assert {item["source"] for item in result["gust_evidence"]} == {field, "description"}


CONDITIONS = ["Starkregen", "Dauerregen", "Platzregen", "Sprühregen", "Nieselregen",
              "Starkschneefall", "Dauerschneefall", "starkem Regen", "heftigem Starkregen",
              "leichtem Regen", "anhaltendem Dauerregen"]


@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize("frame", ["Böen 110 km/h bei {condition}.",
                                   "Bei {condition} sind Böen 110 km/h möglich."])
def test_precipitation_compounds_are_weather_conditions(condition, frame):
    result = assess(frame.format(condition=condition))
    assert result["hard_lock"] and not result["gust_scope_uncertain"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h bei Starkregen im Harz.", "Bei Starkregen im Harz Böen 110 km/h.",
    "Böen 110 km/h bei Starkregenhausen.", "Böen 110 km/h bei Dauerschneefalltal.",
    "Böen 110 km/h bei leichtem Regenstauf.",
    "Böen 110 km/h bei Starkregengebieten.",
])
def test_real_or_unresolved_place_phrases_are_not_removed_as_weather(description):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("relation,comparison", [("oberhalb von", lambda height: height > 1200),
                                               ("unterhalb von", lambda height: height < 1200),
                                               ("ab", lambda height: height >= 1200),
                                               ("bis", lambda height: height <= 1200)])
@pytest.mark.parametrize("height", [0, 1199.99, 1200, 1200.01, 1500])
@pytest.mark.parametrize("unit,value", [("m", "1200"), ("Metern", "1200")])
def test_height_relations_use_their_exact_boundary_and_never_become_clock_times(relation, comparison, height, unit, value):
    result = assess(f"Böen 110 km/h {relation} {value} {unit}.", elevation=height)
    assert result["hard_lock"] is comparison(height)
    assert not result["gust_time_uncertain"]


def test_foot_height_uses_the_same_typed_relation_and_metre_elevation():
    for height, locked in [(1200, False), (1219.2, False), (1220, True), (1500, True)]:
        result = assess("Böen 110 km/h oberhalb von 4000 ft.", elevation=height)
        assert result["hard_lock"] is locked and not result["gust_time_uncertain"]


@pytest.mark.parametrize("height", [None, True, math.nan, math.inf])
def test_an_unusable_window_height_cannot_confirm_the_height_scope(height):
    result = assess("Böen 110 km/h oberhalb von 1200 m.", elevation=height)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]
    assert not result["gust_time_uncertain"]


@pytest.mark.parametrize("height,offset,locked", [(1500, -1801, False), (1500, -1800, True),
                                               (1500, 3600, True), (1200, 3600, False)])
def test_combined_height_and_clock_keep_separate_roles(height, offset, locked):
    onset = NOW.replace(hour=18, minute=0, second=0)
    result = assess("Böen 110 km/h oberhalb von 1200 m ab 18.00 Uhr UTC.",
                    elevation=height, now=onset + timedelta(seconds=offset),
                    onset=NOW.replace(hour=0, minute=0), expires=NOW.replace(hour=23, minute=59))
    assert result["hard_lock"] is locked and not result["gust_time_uncertain"]


def test_an_unzoned_clock_stays_uncertain_even_with_a_verified_height():
    result = assess("Böen 110 km/h oberhalb von 1200 m ab 18 Uhr.", elevation=1500)
    assert not result["hard_lock"] and result["gust_time_uncertain"]


WHOLE_AREAS = [
    "in allen Regionen des Warngebietes", "in sämtlichen Regionen des Warngebiets",
    "in allen Teilen des Warngebietes", "in allen Teilregionen des Warnbereichs",
    "in jedem Teil des Warngebietes", "in jeder Region des Warngebiets",
    "in allen Bereichen der Warnregion", "in der gesamten Warnregion", "im gesamten Warngebiet",
    "across all parts of the warning area", "in every region of the warning area",
]


@pytest.mark.parametrize("area", WHOLE_AREAS)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "70 km/h"}])
def test_universal_coverage_of_the_matched_warning_area_is_not_an_unknown_subregion(area, parameters):
    result = assess(f"Böen 110 km/h {area}.", parameters)
    assert result["hard_lock"] and not result["gust_scope_uncertain"]
    assert result["gust_max_kmh"] == 110


@pytest.mark.parametrize("area", ["in Teilen des Warngebietes", "in einigen Regionen des Warngebietes",
                                   "in den meisten Regionen des Warngebietes", "in allen höheren Lagen des Warngebietes",
                                   "auf allen Gipfeln des Warngebietes", "in allen Regionen des Harzes",
                                   "in allen Regionen des Warngebietes im Harz"])
def test_partly_covered_terrain_or_named_areas_are_not_the_entire_matched_warning_area(area):
    result = assess(f"Böen 110 km/h {area}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


def test_whole_area_text_cannot_verify_unresolved_cap_coverage():
    result = assess(f"Böen 110 km/h {WHOLE_AREAS[0]}.", area_restriction_unknown=True)
    assert not result["hard_lock"] and not result["area_verified"]


@pytest.mark.parametrize("height,locked,conflict", [(60, True, False), (1200, True, False), (1500, False, True)])
def test_negative_height_forecast_only_conflicts_where_the_window_belongs(height, locked, conflict):
    result = assess("Böen 110 km/h im gesamten Warngebiet.", elevation=height,
                    headline="Böen 110 km/h oberhalb von 1200 m sind ausgeschlossen.")
    assert result["hard_lock"] is locked and result["gust_polarity_conflict"] is conflict
    json.dumps(result, allow_nan=False)


def test_external_3348_case_matrix_remains_a_permanent_regression():
    # Preserve the independent audit's seed, sentence families and expectations.
    rng = random.Random(20261024)
    checks = 0

    def verify(text, expected, **fields):
        nonlocal checks
        result = assess(text, **fields)
        assert bool(result and result["hard_lock"]) is expected, (text, fields, result)
        checks += 1

    low = [30, 50, 64.99, 65, 70, 85, 89, 89.9, 89.99]
    high = [90, 90.01, 91, 95, 100, 105, 110, 120, 125, 140]
    negative = [
        "Böen {s} km/h sind keinesfalls zu erwarten.", "Windböen {s} km/h werden keinesfalls auftreten.",
        "Böen {s} km/h wird es nicht geben.", "Böen {s} km/h kommen nicht vor.",
        "Böen {s} km/h werden definitiv nicht eintreten.", "Böen {s} km/h sind absolut ausgeschlossen.",
        "Böen {s} km/h treten mit Sicherheit nicht auf.", "Böen {s} km/h werden nicht erwartet.",
        "Windböen {s} km/h sind ausgeschlossen.", "Keine Böen mit {s} km/h werden erwartet.",
    ]
    conditions = [
        "Böen {s} km/h bei Starkregen.", "Böen {s} km/h bei starkem Regen.",
        "Böen {s} km/h bei Niederschlag.", "Böen {s} km/h bei Schneefall.",
        "Böen {s} km/h bei Gewittern.", "Böen {s} km/h bei kräftigen Niederschlägen.",
        "Böen {s} km/h während des Regens.", "Böen {s} km/h, dabei starker Regen.",
        "Böen {s} km/h und starker Regen.", "Böen {s} km/h ohne Niederschlag.",
    ]
    neutral = ["Böen {s} km/h werden erwartet.", "Windspitzen von {s} km/h sind möglich.",
               "Es drohen Böen von {s} km/h."]
    for speed in high:
        for frame in negative:
            verify(frame.format(s=speed), False)
        for frame in conditions + neutral:
            verify(frame.format(s=speed), True)
    for speed in low:
        for frame in neutral:
            verify(frame.format(s=speed), False)
    for elevation in [1001, 1200, 1500, 2500, 5000]:
        for limit in [800, 900, 1000]:
            for suffix in ["oberhalb von {h} m", "oberhalb {h} m", "über {h} m", "ab {h} m", "nur oberhalb {h} m"]:
                verify("Böen 110 km/h " + suffix.format(h=limit) + ".", True, elevation=elevation)
    for speed in [90, 100, 110, 120]:
        for area in ["in der gesamten Warnregion", "im gesamten Warngebiet", WHOLE_AREAS[0], "im ganzen Warngebiet"]:
            verify(f"Böen {speed} km/h {area}.", True)
    for _ in range(2500):
        speed = rng.choice(low + high)
        onset = NOW + timedelta(minutes=rng.randint(-120, 120))
        current = onset + timedelta(minutes=rng.randint(-60, 240))
        verify(f"Böen {speed} km/h.", speed >= 90 and onset - timedelta(minutes=30) <= current < onset + timedelta(hours=6),
               now=current, onset=onset, effective=onset - timedelta(hours=4), expires=onset + timedelta(hours=6))
    for _ in range(500):
        speed = rng.choice(high)
        cutoff = rng.randint(30, int(speed) - 1)
        result = assess(f"Böen {speed} km/h werden erwartet.", headline=f"Keine Böen über {cutoff} km/h erwartet.")
        assert result["gust_polarity_conflict"] and result["gust_conflict"] and not result["hard_lock"]
        checks += 1
    assert checks == 3348

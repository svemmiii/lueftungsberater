"""Adversarial wind grammar, mathematical speed sets and weather conditions."""
from datetime import timedelta
import json
import operator

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


DENIALS = [
    "Böen 110 km/h werden definitiv nicht eintreten.",
    "Böen 110 km/h werden ganz sicher nicht auftreten.",
    "Sturmböen 110 km/h sind mit Sicherheit ausgeschlossen.",
    "Böen bis 110 km/h sind absolut ausgeschlossen.",
    "Es wird kein Wind mit Böen von 110 km/h auftreten.",
    "Es wird kein Wind mit Böen 110 km/h geben.",
    "Windböen von 110 km/h sind praktisch ausgeschlossen.",
    "Böen 110 km/h treten definitiv nicht auf.",
    "Böen 110 km/h bleiben mit Sicherheit aus.",
    "Wind gusts 110 km/h are definitely not expected.",
    "Wind gusts 110 km/h are with certainty excluded.",
    "No wind with gusts 110 km/h is expected.",
    "Die Wahrscheinlichkeit für Böen 110 km/h besteht definitiv nicht.",
]
POSSIBLE = [
    "Böen 110 km/h werden definitiv erwartet.",
    "Böen 110 km/h werden nicht definitiv erwartet.",
    "Böen 110 km/h werden nicht ganz sicher eintreten.",
    "Böen 110 km/h werden nicht mit Sicherheit eintreten.",
    "Böen 110 km/h sind mit Sicherheit nicht ausgeschlossen.",
    "Böen 110 km/h sind nicht mit Sicherheit ausgeschlossen.",
    "Wind gusts 110 km/h are not definitely expected.",
    "Wind gusts 110 km/h are certainly not excluded.",
    "Wind with gusts 110 km/h is expected.",
    "Böen 110 km/h, Schäden werden definitiv nicht eintreten.",
    "Böen 110 km/h, Schäden sind mit Sicherheit ausgeschlossen.",
    "Es wird kein Regen mit Böen 110 km/h erwartet.",
    "Böen 110 km/h, aber kein Hagel.",
    "Die Wahrscheinlichkeit für Böen 110 km/h besteht nicht definitiv.",
]


@pytest.mark.parametrize("description", DENIALS)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_assertion_modifiers_preserve_a_direct_denial(description, parameters):
    result = assess(description, parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("description", POSSIBLE)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "70 km/h"}])
def test_negated_certainty_and_other_subjects_do_not_become_absent_gusts(description, parameters):
    result = assess(description, parameters)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


COMPARISONS = [
    ("über", operator.gt), ("mehr als", operator.gt), (">", operator.gt),
    ("mindestens", operator.ge), ("ab", operator.ge), (">=", operator.ge),
    ("unter", operator.lt), ("weniger als", operator.lt), ("<", operator.lt),
    ("bis", operator.le), ("höchstens", operator.le), ("<=", operator.le),
    ("nicht mehr als", operator.le), ("nicht unter", operator.ge),
]


@pytest.mark.parametrize("comparison,contains", COMPARISONS)
@pytest.mark.parametrize("threshold", [0, 70, 90, 110])
@pytest.mark.parametrize("speed", [0, 69, 70, 89, 90, 91, 109, 110, 111, 140])
def test_polarity_conflict_uses_the_speed_set_including_its_exact_endpoints(comparison, contains, threshold, speed):
    result = assess(f"Böen {speed} km/h werden erwartet.",
                    headline=f"Keine Böen {comparison} {threshold} km/h erwartet.")
    conflict = contains(speed, threshold)
    assert result["gust_polarity_conflict"] is conflict
    assert result["gust_conflict"] is conflict
    assert result["hard_lock"] is (speed >= 90 and not conflict)
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("comparison,contains", [COMPARISONS[0], COMPARISONS[3], COMPARISONS[6], COMPARISONS[9]])
@pytest.mark.parametrize("speed", [70, 89, 90, 91, 110])
def test_a_negated_description_does_not_erase_a_compatible_flat_parameter(comparison, contains, speed):
    result = assess(f"Keine Böen {comparison} 90 km/h erwartet.", {"gusts": f"{speed} km/h"})
    conflict = contains(speed, 90)
    assert result["gust_polarity_conflict"] is conflict
    assert result["hard_lock"] is (speed >= 90 and not conflict)
    assert result["gust_max_kmh"] == (None if conflict else speed)


@pytest.mark.parametrize("headline,description,conflict", [
    ("Keine Böen über 25 m/s erwartet", "Böen 90 km/h erwartet.", False),
    ("Keine Böen mindestens 25 m/s erwartet", "Böen 90 km/h erwartet.", True),
    ("Keine Böen unter 25 m/s erwartet", "Böen 90 km/h erwartet.", False),
    ("Keine Böen bis 25 m/s erwartet", "Böen 90 km/h erwartet.", True),
    ("Keine Böen 90-110 km/h erwartet", "Böen 89 km/h erwartet.", False),
    ("Keine Böen 90-110 km/h erwartet", "Böen 90 km/h erwartet.", True),
    ("Keine Böen 90-110 km/h erwartet", "Böen 110 km/h erwartet.", True),
    ("Keine Böen 90-110 km/h erwartet", "Böen 111 km/h erwartet.", False),
    ("Keine Böen über 90 km/h erwartet", "Böen 70-110 km/h erwartet.", True),
    ("Keine Böen über 90 km/h erwartet", "Böen 70-90 km/h erwartet.", False),
])
def test_intervals_survive_unit_conversion_and_finite_range_intersection(headline, description, conflict):
    result = assess(description, headline=headline)
    assert result["gust_polarity_conflict"] is conflict


def test_a_mathematical_open_bound_does_not_invent_an_unbounded_forecast_peak():
    result = assess("Böen über 90 km/h werden erwartet.")
    claim = result["gust_evidence"][0]
    assert claim["speed_interval"] == {"lower_kmh": 90, "upper_kmh": None,
                                      "lower_inclusive": False, "upper_inclusive": True}
    assert result["gust_max_kmh"] == 90 and result["hard_lock"]
    assert result["gust_original_text"] == "über 90 km/h"
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("description,locked", [
    ("Böen nicht unter 90 km/h.", True),
    ("Böen unter 90 km/h.", False),
    ("Böen nicht mehr als 89 km/h.", False),
    ("Böen nicht mehr als 90 km/h.", True),
])
def test_negated_comparatives_keep_their_positive_forecast_boundary(description, locked):
    assert assess(description)["hard_lock"] is locked


@pytest.mark.parametrize("left,right,conflict", [
    ("Böen 70-110 km/h.", "100-140 km/h", False),
    ("Böen bis 110 km/h.", "70 km/h", False),
    ("Böen über 90 km/h.", "110 km/h", False),
    ("Böen 110 km/h.", "70 km/h", True),
])
def test_numeric_source_disagreement_distinguishes_overlapping_ranges_from_disjoint_values(left, right, conflict):
    result = assess(left, {"gusts": right})
    assert result["gust_conflict"] is conflict and not result["gust_polarity_conflict"]


@pytest.mark.parametrize("suffix,now,locked,conflict", [
    ("", NOW, False, True),
    (" ab 18:00 UTC", NOW, True, True),
    (" ab 18:00 UTC", NOW.replace(hour=19), False, True),
    (" nur im Harz", NOW, True, False),
])
def test_speed_set_conflicts_keep_their_actual_geographic_and_temporal_context(suffix, now, locked, conflict):
    result = assess("Böen 110 km/h werden erwartet.",
                    headline=f"Keine Böen über 90 km/h{suffix} erwartet.", now=now,
                    onset=NOW.replace(hour=0, minute=0), expires=NOW.replace(hour=23, minute=59))
    assert result["hard_lock"] is locked and result["gust_polarity_conflict"] is conflict


@pytest.mark.parametrize("condition", ["Niederschlag", "Niederschläge", "Niederschlägen",
                                       "kräftigen Niederschlägen", "starken Regenfällen",
                                       "Schneeschauern", "Gewitterschauern", "Hagelschlag"])
@pytest.mark.parametrize("frame", ["Windböen 110 km/h bei {condition}.",
                                  "Bei {condition} sind Windböen 110 km/h möglich."])
def test_inflected_weather_conditions_are_not_unverified_places(condition, frame):
    result = assess(frame.format(condition=condition))
    assert result["hard_lock"] and not result["gust_scope_uncertain"]


@pytest.mark.parametrize("place", ["Regenstauf", "Schneeverdingen", "Hagelstadt", "Niederschlaghausen"])
def test_weather_like_prefixes_in_place_names_are_not_condition_words(place):
    result = assess(f"Böen 110 km/h bei {place}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


def test_a_real_location_after_a_weather_condition_remains_unverified():
    result = assess("Böen 110 km/h bei Niederschlägen im Harz.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("speed", [30, 70, 89, 90, 110, 140])
@pytest.mark.parametrize("term", ["Windspitze", "Windspitzen"])
@pytest.mark.parametrize("denied", [False, True])
def test_explicit_wind_peak_tokens_keep_the_speed_threshold_and_polarity(speed, term, denied):
    predicate = "werden definitiv nicht erwartet" if denied else "werden erwartet"
    result = assess(f"{term} bis {speed} km/h {predicate}.")
    assert result["hard_lock"] is (speed >= 90 and not denied)
    assert result["gust_max_kmh"] == (None if denied else speed)


@pytest.mark.parametrize("description", ["Mittelwind 110 km/h.", "Windmittel 110 km/h.",
                                         "Windspitzenmessung 110 km/h.", "Windspitzenhausen 110 km/h."])
def test_mean_wind_and_other_compound_words_are_not_promoted_to_peak_forecasts(description):
    result = assess(description, headline="Amtliche Meldung", event="Unwetter")
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("clock", ["18.00 Uhr UTC", "18.00 UTC", "18:00 UTC"])
@pytest.mark.parametrize("seconds,locked", [(-1801, False), (-1800, True), (-1, True), (0, True), (3600, True)])
def test_dotted_and_colon_clocks_share_the_exact_30_minute_lead(clock, seconds, locked):
    onset = NOW.replace(hour=18, minute=0, second=0)
    result = assess(f"Böen 110 km/h ab {clock}.", now=onset + timedelta(seconds=seconds),
                    onset=NOW.replace(hour=0, minute=0), expires=NOW.replace(hour=23, minute=59))
    assert result["hard_lock"] is locked and not result["gust_time_uncertain"]
    assert result["lock_from"] == (onset - timedelta(minutes=30)).isoformat()


@pytest.mark.parametrize("time", ["18.00", "18.00 Uhr", "18.70 UTC", "25.00 UTC", "18.00 UTC+02:00", "18.00.2026"])
def test_dotted_clocks_still_require_a_valid_zone_and_calendar_binding(time):
    result = assess(f"Böen 110 km/h ab {time}.", onset=NOW.replace(hour=0, minute=0),
                    expires=NOW.replace(hour=23, minute=59))
    assert not result["hard_lock"] and result["gust_time_uncertain"]

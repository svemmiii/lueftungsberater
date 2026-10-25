"""Wind event predicates, value-to-gust links and unresolved calendar times."""
from datetime import timedelta

import pytest

from test_v0119_warning_scopes_pure import NOW, assess, policy, warning


POSITIVE = [
    "Der Wind frischt auf, mit Geschwindigkeiten bis zu 110 km/h in Böen.",
    "Maximale Geschwindigkeiten bis 110 km/h, insbesondere in Böen.",
    "Wind speeds up to 110 km/h in gusts.", "Winds up to 110 km/h in gusts.",
    "Der Wind erreicht böig Geschwindigkeiten bis zu 110 km/h.",
    "Dabei werden Windgeschwindigkeiten bis 110 km/h in Böen erreicht.",
    "Böen 110 km/h treten auf.", "Böen 110 km/h bleiben nicht aus.",
    "Wind gusts 110 km/h cannot be excluded.", "Wind gusts 110 km/h won't be ruled out.",
    "Wind gusts 110 km/h cannot damage buildings.",
    "Böen 110 km/h, Schäden treten nicht auf.",
    "Böen 110 km/h, Stromausfälle bleiben aus.",
    "Wind gusts 110 km/h, lightning will not be observed.",
    "Wind speeds up to 110 km/h in gusts, without rain.",
]
NEGATIVE = [
    "Böen 110 km/h treten nicht auf.", "Sturmböen 110 km/h treten nicht auf.",
    "Böen 110 km/h bleiben aus.", "Wind gusts of 110 km/h cannot occur.",
    "Wind gusts of 110 km/h can't occur.", "Wind gusts 110 km/h won't occur.",
    "Wind gusts 110 km/h will not be observed.", "Wind gusts 110 km/h will be absent.",
    "Wind gusts 110 km/h are not occurring.",
    "Wind speeds up to 110 km/h in gusts are not expected.",
    "Wind speeds up to 110 km/h in gusts cannot occur.",
    "Der Wind frischt auf, mit Geschwindigkeiten bis zu 110 km/h in Böen, die nicht erwartet werden.",
]


@pytest.mark.parametrize("description", POSITIVE)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "70 km/h"}])
def test_explicit_general_gust_constructions_keep_their_protective_value(description, parameters):
    result = assess(description, parameters)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


@pytest.mark.parametrize("description", NEGATIVE)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_negative_event_predicates_do_not_become_hard_wind_evidence(description, parameters):
    result = assess(description, parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("text", ["Böen 110 km/h treten nicht auf.", "Wind gusts cannot occur."])
def test_header_predicates_have_the_same_polarity_rules(field, text):
    assert not assess(parameters={"gusts": "110 km/h"}, **{field: text})["hard_lock"]


@pytest.mark.parametrize("description,speed", [
    ("Wind speed 110 km/h, gusts up to 70 km/h.", 70),
    ("Wind speed 110 km/h in gusts up to 70 km/h.", 70),
    ("Mittlerer Wind 110 km/h, Böen bis 70 km/h.", 70),
    ("Mittlerer Wind 110 km/h, teilweise böig.", None),
    ("Regen mit Geschwindigkeiten bis 110 km/h in Böen.", None),
])
def test_suffix_reading_does_not_promote_a_separate_mean_wind_or_other_subject(description, speed):
    result = assess(description)
    assert not result["hard_lock"] and result["gust_max_kmh"] == speed


@pytest.mark.parametrize("suffix", ["im Harz", "auf See", "oberhalb 1000 m"])
def test_suffix_gusts_keep_their_geographic_scope(suffix):
    result = assess(f"Wind speeds up to 110 km/h in gusts {suffix}.")
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


CALENDAR = [
    "ab Montag", "ab Dienstag", "erst am Montag", "am Dienstagabend", "erst am Wochenende",
    "ab kommender Woche", "erst später in der Woche", "gegen Abend", "erst am 26.10.2026",
    "from Monday", "next Tuesday", "on Friday", "beginning next week", "this evening",
    "ab November", "in May", "next January", "in 2 Stunden", "nach drei Stunden", "within 2h",
    "bald", "morgenfrüh", "heuteabend",
]


@pytest.mark.parametrize("calendar", CALENDAR)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
@pytest.mark.parametrize("separator", [" ", ", "])
def test_unresolved_calendar_beginning_does_not_inherit_a_conflicting_cap_onset(calendar, parameters, separator):
    result = assess(f"Böen 110 km/h{separator}{calendar}.", parameters,
                    onset=NOW + timedelta(minutes=20), expires=NOW + timedelta(days=6))
    assert not result["hard_lock"] and result["gust_time_uncertain"]
    assert not result["gust_scope_uncertain"]  # A weekday is not a place.
    assert result["phase"] == "time_uncertain" and result["lock_from"] is None


@pytest.mark.parametrize("field", ["headline", "event"])
def test_calendar_in_header_is_not_a_verified_current_forecast(field):
    result = assess(parameters={"gusts": "110 km/h"}, **{field: "Windböen ab Montag"})
    assert not result["hard_lock"] and result["gust_time_uncertain"]


def test_calendar_in_a_parameter_is_not_broadened_to_the_cap_period():
    result = assess(parameters={"gusts from Monday": "110 km/h"})
    assert not result["hard_lock"] and result["gust_time_uncertain"]


def test_another_subjects_calendar_does_not_postpone_general_gusts():
    result = assess("Böen 110 km/h, Stromausfälle ab Montag nicht erwartet.")
    assert result["hard_lock"] and not result["gust_time_uncertain"]


def test_current_instant_and_numeric_altitude_do_not_become_unknown_dates():
    assert assess("Böen 110 km/h jetzt.")["hard_lock"]
    assert assess("Böen 110 km/h ab 1000 m.", elevation=1200)["hard_lock"]
    assert assess("Böen 110 km/h in der Region Montagberg.")["gust_scope_uncertain"]
    assert assess("Wind gusts 110 km/h may occur.")["hard_lock"]


def test_explicit_utc_beginning_keeps_the_exact_thirty_minute_lead_for_suffix_gusts():
    description = "Wind speeds up to 110 km/h in gusts ab 18 Uhr UTC."
    before = NOW.replace(hour=17, minute=29, second=59)
    assert not assess(description, now=before)["hard_lock"]
    result = assess(description, now=before + timedelta(seconds=1))
    assert result["hard_lock"] and result["phase"] == "prelock"


def test_real_explicit_close_instruction_is_independent_of_uncertain_wind_time():
    result = policy.assess_official_warning(warning(description="Böen 110 km/h ab Montag."),
                                            NOW, explicit_close=True, elevation=60)
    assert result["hard_lock"] and result["explicit_close"]

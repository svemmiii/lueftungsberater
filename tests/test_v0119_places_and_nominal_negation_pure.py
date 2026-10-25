"""Unverified place phrases and negation of nominal wind events, without HA."""
import itertools
import json
import random

import pytest

from test_v0119_warning_scopes_pure import NOW, _provider_case, assess, policy, warning
from types import SimpleNamespace


PLACES = [
    "im Harz", "in der Eifel", "an der Nordseeküste", "auf der Ostsee", "am Alpenrand",
    "im Erzgebirge", "im westlichen Teil des Kreises", "über offenem Wasser", "auf Inseln",
    "auf See", "in Gipfelnähe", "in Bad Homburg", "in der Nähe von Bad Homburg",
    "im gesamten Harz", "im gesamten Gebiet des Harzes", "in Gustavsburg",
]


@pytest.mark.parametrize("place", PLACES)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}, {"gusts": "70 km/h"}])
@pytest.mark.parametrize("pattern", ["Böen 110 km/h {place}.", "{place} Böen 110 km/h.",
                                     "Böen 110 km/h, {place}."])
def test_named_place_needs_its_own_verified_assignment(place, parameters, pattern):
    result = assess(pattern.format(place=place), parameters, elevation=1800, area_altitude=0)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None
    assert result["gust_scope_uncertain"]
    assert any(not item["location_verified"] for item in result["gust_evidence"])
    json.dumps(result, allow_nan=False)


def test_unknown_geographic_names_are_handled_without_a_name_dictionary():
    rng = random.Random(20261024)
    for prefix, suffix in itertools.product(["Albra", "Beren", "Calt", "Dorn", "Elben", "Gustav"],
                                             ["aue", "tal", "mark", "see", "insel", "burg"]):
        name = prefix + suffix
        speed = rng.choice([90, 95, 110, 120, 140])
        for qualifier in [f"im {name}", f"in der Region {name}", f"nur im {name}"]:
            for case in [str, str.lower, str.upper]:
                result = assess(case(f"Böen {speed} km/h {qualifier}."), {"gusts": f"{speed} km/h"})
                assert not result["hard_lock"] and result["gust_scope_uncertain"], result


@pytest.mark.parametrize("description", [
    "Böen 110 km/h, im Harz und in der Eifel.",
    "Im Harz und in der Eifel Böen 110 km/h.",
    "Wind gusts 110 km/h in Scotland.", "Wind gusts 110 km/h at sea.",
    "Rafales 110 km/h en Bretagne.", "Rafales 110 km/h dans les Alpes.",
    "Rachas 110 km/h en Cantabria.", "Raffiche 110 km/h nelle Alpi.",
    "Windstoten 110 km/h op zee.",
    "Böen 110 km/h, im Randgebiet der großen östlichen Bergregion mit Ausnahme der Täler.",
])
def test_coordinated_and_foreign_place_phrases_do_not_become_general(description):
    result = assess(description, {"gusts": "110 km/h"})
    assert not result["hard_lock"] and result["gust_scope_uncertain"]


@pytest.mark.parametrize("field", ["headline", "event"])
def test_place_in_a_header_cannot_be_overridden_by_general_metadata(field):
    result = assess(parameters={"gusts": "110 km/h"}, area_altitude=0,
                    **{field: "Windböen im Harz"})
    assert not result["hard_lock"] and result["area_verified"] is False


@pytest.mark.parametrize("name,value", [("gusts im Harz", "110 km/h"),
                                      ("gusts", "110 km/h auf See")])
def test_parameter_names_and_values_have_the_same_place_rules(name, value):
    assert not assess(parameters={name: value})["hard_lock"]


@pytest.mark.parametrize("description", [
    "Böen 70 km/h, im Harz 110 km/h.",
    "Böen 70 km/h, im Harz Böen 110 km/h.",
    "Böen 110 km/h im Harz, allgemein 70 km/h.",
    "Im Harz Böen 110 km/h, allgemein Böen 70 km/h.",
])
def test_unverified_regional_peak_does_not_replace_separate_general_gusts(description):
    result = assess(description, {"gusts": "110 km/h"})
    assert not result["hard_lock"] and result["gust_max_kmh"] == 70
    assert result["gust_scope_uncertain"] and not result["gust_conflict"]


@pytest.mark.parametrize("description", [
    "Böen 110 km/h im gesamten Warngebiet.", "In der gesamten Region Böen 110 km/h.",
    "Wind gusts 110 km/h across the entire warning area.",
    "Böen 110 km/h in Verbindung mit Gewittern.", "Böen 110 km/h in Kombination mit Regen.",
    "Böen 110 km/h im Zusammenhang mit Gewittern.", "Böen 110 km/h in der Spitze.",
    "Böen im Bereich von 90 bis 110 km/h.", "Wind gusts 110 km/h at times.",
    "Böen 110 km/h aus westlicher Richtung.", "Böen 110 km/h auch im Harz.",
    "Bei starkem Wind Böen 110 km/h.", "Bei angekündigten Gewittern Böen 110 km/h.",
    "Wind gusts 110 km/h under the threshold of 120 km/h.",
    "Böen 110 km/h, stärkere Werte nur im Harz.",
    "Böen 110 km/h, Schäden im Harz sind nicht auszuschließen.",
    "Böen 110 km/h, im Harz sind Schäden nicht auszuschließen.",
    "Böen 110 km/h ohne Schäden im Harz.", "Keine Schäden im Harz bei Böen 110 km/h.",
])
def test_general_wind_is_not_cancelled_by_other_roles_of_prepositional_phrases(description):
    result = assess(description)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110
    assert not result["gust_scope_uncertain"]


@pytest.mark.parametrize("description", [
    "Kein Auftreten von Böen 110 km/h zu erwarten.",
    "Kein weiteres Auftreten von Böen 110 km/h ist zu erwarten.",
    "Ohne Auftreten von Böen 110 km/h.",
    "Kein Eintreten von Böen 110 km/h zu erwarten.",
    "Das Auftreten von Böen 110 km/h ist ausgeschlossen.",
    "Das Ausbleiben von Böen 110 km/h wird erwartet.",
    "No occurrence of wind gusts 110 km/h is expected.",
])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_nominal_negation_is_part_of_the_wind_forecast(description, parameters):
    result = assess(description, parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None
    assert any(item["denied"] for item in result["gust_evidence"])


@pytest.mark.parametrize("description", [
    "Das Auftreten von Böen 110 km/h ist nicht ausgeschlossen.",
    "Das Auftreten von Böen 110 km/h ist zu erwarten.",
    "Kein Ausbleiben von Böen 110 km/h zu erwarten.",
    "Das Ausbleiben von Böen 110 km/h ist ausgeschlossen.",
    "Kein Auftreten von Schäden bei Böen 110 km/h zu erwarten.",
    "Kein Auftreten von Hagel bei Böen 110 km/h zu erwarten.",
    "No occurrence of damage with wind gusts 110 km/h is expected.",
])
def test_nominal_negation_does_not_cancel_another_subjects_wind(description):
    assert assess(description)["hard_lock"]


@pytest.mark.parametrize("field", ["headline", "event"])
def test_nominal_negation_in_header_is_also_respected(field):
    result = assess(parameters={"gusts": "110 km/h"},
                    **{field: "Kein Auftreten von Böen 110 km/h zu erwarten."})
    assert not result["hard_lock"]


def test_denied_and_positive_wind_assertions_are_kept_separate():
    result = assess("Kein Auftreten von Böen 110 km/h zu erwarten, aber Böen 70 km/h.",
                    {"gusts": "110 km/h"})
    assert not result["hard_lock"] and result["gust_max_kmh"] == 70


@pytest.mark.parametrize("description", ["Böen 110 km/h im Harz.",
                                         "Kein Auftreten von Böen 110 km/h zu erwarten."])
def test_actual_automatic_and_manual_adapters_do_not_reintroduce_a_hard_lock(description):
    record = warning(description=description, parameters={"gusts": "110 km/h"})
    scope, entry = _provider_case(record)
    automatic = scope["_automatic_warning_assessment"](SimpleNamespace(), entry)
    manual = scope["WarningAssessment"]()
    scope["_apply_manual_official_notice"](manual, record, elevation=60)
    for result in [automatic, manual]:
        assert not result.weather_hard_lock
        assert not result.warning_observations
        assert len(result.warning_notices) == 1


def test_whole_warning_area_still_needs_a_valid_cap_area():
    assert not assess("Böen 110 km/h im gesamten Warngebiet.", area_restriction_unknown=True)["hard_lock"]


@pytest.mark.parametrize("description,speed,locked", [
    ("Wind gusts 70 km/h under the threshold of 110 km/h.", 70, False),
    ("Böen 70 km/h, Schäden ab 110 km/h möglich.", 70, False),
    ("Böen 90 km/h bis 110 km/h.", 110, True),
])
def test_an_independent_numeric_limit_is_not_a_second_wind_forecast(description, speed, locked):
    result = assess(description)
    assert result["gust_max_kmh"] == speed and result["hard_lock"] is locked


def test_independent_explicit_close_instruction_keeps_its_protection():
    result = policy.assess_official_warning(warning(description="Böen 110 km/h im Harz."),
                                            NOW, elevation=60, explicit_close=True)
    assert result["hard_lock"] and result["explicit_close"]

"""Expectation polarity, regional relations and lexical wind terms without HA."""
import itertools

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


DENIED = [
    "Es ist nicht mit Böen von 110 km/h zu rechnen.",
    "Mit Böen von 110 km/h ist nicht zu rechnen.",
    "Es ist mit Böen von 110 km/h nicht zu rechnen.",
    "Es ist nicht mit schweren Sturmböen von 110 km/h zu rechnen.",
    "Mit Orkanböen von 110 km/h ist ausdrücklich nicht zu rechnen.",
    "Böen von 110 km/h werden nicht eintreten.",
    "Böen von 110 km/h treten nicht ein.",
    "Böen von 110 km/h werden ausbleiben.",
    "Eine Wahrscheinlichkeit für Böen 110 km/h besteht nicht.",
    "Die Wahrscheinlichkeit für Böen 110 km/h besteht weiterhin nicht.",
    "Keine Wahrscheinlichkeit für Böen 110 km/h besteht.",
    "Es besteht keine Wahrscheinlichkeit für Böen 110 km/h.",
    "Eine Möglichkeit für Böen 110 km/h existiert nicht.",
    "Die Wahrscheinlichkeit für Böen 110 km/h ist ausgeschlossen.",
    "Böen 110 km/h wurden nicht gemeldet.",
    "Böen 110 km/h, die nicht eintreten werden.",
    "Mit Böen 110 km/h, ist nicht zu rechnen.",
]
POSSIBLE = [
    "Es ist mit Böen von 110 km/h zu rechnen.",
    "Mit Böen von 110 km/h ist zu rechnen.",
    "Böen 110 km/h werden eintreten.", "Böen 110 km/h treten ein.",
    "Böen 110 km/h werden nicht ausbleiben.",
    "Eine Wahrscheinlichkeit für Böen 110 km/h besteht.",
    "Die Wahrscheinlichkeit für Böen 110 km/h ist nicht ausgeschlossen.",
    "Eine Möglichkeit für Böen 110 km/h existiert.",
    "Es ist nicht mit Schäden bei Böen 110 km/h zu rechnen.",
    "Mit Schäden bei Böen 110 km/h ist nicht zu rechnen.",
    "Keine Wahrscheinlichkeit für Schäden bei Böen 110 km/h besteht.",
    "Eine Wahrscheinlichkeit für Schäden bei Böen 110 km/h besteht nicht.",
    "Böen 110 km/h, Schäden werden nicht eintreten.",
    "Böen 110 km/h, mit Schäden ist nicht zu rechnen.",
    "Böen 110 km/h, die Wahrscheinlichkeit für Schäden besteht nicht.",
    "Böen 110 km/h, Schäden sind nicht auszuschließen.",
    "Böen 110 km/h, Regen bleibt aus.",
]


@pytest.mark.parametrize("description", DENIED)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_negated_prediction_follows_its_gust_complement(description, parameters):
    result = assess(description, parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None
    assert any(item["denied"] for item in result["gust_evidence"])


@pytest.mark.parametrize("description", POSSIBLE)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "70 km/h"}])
def test_positive_prediction_and_negated_consequence_remain_distinct(description, parameters):
    result = assess(description, parameters)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("description", DENIED[:6] + [DENIED[8]])
def test_negated_header_cannot_be_overridden_by_a_flat_gust_parameter(field, description):
    assert not assess(parameters={"gusts": "110 km/h"}, **{field: description})["hard_lock"]


RELATIONS = [
    "zwischen Köln und Bonn", "rund um Köln", "nördlich von Köln", "südlich der Eifel",
    "östlich von Bonn", "westlich des Harzes", "nordöstlich von Albratal",
    "südwestlich der Berenmark", "rings um Caltinsel", "um Dornburg",
    "between Edinburgh and Glasgow", "around Inverness", "north of Bristol",
    "southwest of London", "east of York",
]


@pytest.mark.parametrize("relation", RELATIONS)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}, {"gusts": "70 km/h"}])
@pytest.mark.parametrize("pattern", ["Böen 110 km/h {relation}.",
                                     "{relation} Böen 110 km/h.", "Böen 110 km/h, {relation}."])
def test_regional_relation_requires_geographic_assignment(relation, parameters, pattern):
    result = assess(pattern.format(relation=relation), parameters, elevation=1800, area_altitude=0)
    assert not result["hard_lock"] and result["gust_scope_uncertain"]
    assert result["gust_max_kmh"] is None


@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("relation", RELATIONS[:5])
def test_regional_header_qualifies_the_warning(field, relation):
    result = assess(parameters={"gusts": "110 km/h"}, **{field: f"Windböen {relation}"})
    assert not result["hard_lock"] and not result["area_verified"]


@pytest.mark.parametrize("name,value", [("gusts zwischen Köln und Bonn", "110 km/h"),
                                      ("gusts", "110 km/h nördlich von Köln")])
def test_regional_parameter_does_not_get_a_general_scope(name, value):
    assert not assess(parameters={name: value})["hard_lock"]


@pytest.mark.parametrize("description,speed,hard", [
    ("Böen 70 km/h, zwischen Köln und Bonn Böen 110 km/h.", 70, False),
    ("Böen 110 km/h zwischen Köln und Bonn, allgemein Böen 70 km/h.", 70, False),
    ("Böen 110 km/h, rund um Köln Böen 145 km/h.", 110, True),
    ("Böen 110 km/h im gesamten Warngebiet, nördlich von Köln 145 km/h.", 110, True),
    ("Böen 110 km/h auch zwischen Köln und Bonn.", 110, True),
    ("Böen 110 km/h rund um die Uhr.", 110, True),
    ("Wind gusts 110 km/h around the clock.", 110, True),
    ("Böen 110 km/h aus nördlicher Richtung.", 110, True),
    ("Böen 110 km/h, Schäden zwischen Köln und Bonn sind nicht auszuschließen.", 110, True),
    ("Böen 110 km/h, nördlich von Köln sind Schäden nicht auszuschließen.", 110, True),
    ("Böen 110 km/h ohne Schäden rund um Köln.", 110, True),
    ("Keine Schäden zwischen Köln und Bonn bei Böen 110 km/h.", 110, True),
    ("Böen 110 km/h ab 18 Uhr UTC.", 110, False),
])
def test_local_peaks_other_subjects_and_time_relations_keep_their_own_scope(description, speed, hard):
    result = assess(description)
    assert result["hard_lock"] is hard and result["gust_max_kmh"] == speed


NON_WIND = [
    "Hitzewarnung im August.", "Hochwasser am 12. August.",
    "Rauchentwicklung in Gustavsburg.", "Starkregen und Hochwasser im August.",
    "Hitze im August, 110 km/h.", "Hinweis von Gustav.",
    "Disgusting smoke in August.", "Rauch in Böendorf.",
]


@pytest.mark.parametrize("description", NON_WIND)
@pytest.mark.parametrize("case", [str, str.upper, str.lower])
def test_non_wind_words_do_not_create_a_wind_notice_or_gust_evidence(description, case):
    result = assess(case(description), headline="Amtliche Meldung", event="Unwetter")
    assert not result["wind"] and not result["hard_lock"] and not result["gust_evidence"]


@pytest.mark.parametrize("field", ["headline", "event"])
def test_non_wind_header_words_do_not_classify_a_message_as_wind(field):
    changes = {"headline": "Amtliche Meldung", "event": "Unwetter", field: "Hinweis im August"}
    result = assess("Hitze", **changes)
    assert not result["wind"] and not result["hard_lock"]


def test_unrelated_parameter_names_supply_no_official_gust_value():
    result = assess(parameters={"August": "110 km/h", "Gustavsburg": "140 km/h"},
                    headline="Amtliche Meldung", event="Unwetter")
    assert not result["wind"] and not result["hard_lock"] and not result["gust_evidence"]


@pytest.mark.parametrize("word", ["Böen", "Windböen", "Sturmböen", "Orkanböen", "Sturm-Böen",
                                  "Boeen", "Böenspitzen", "Windböenspitzen", "Gust", "Gusts",
                                  "Gusting", "Rafales", "Rachas", "Raffiche", "Windstoten",
                                  "Rüzgâr hamleleri"])
def test_complete_wind_words_and_supported_compounds_still_lock(word):
    result = assess(f"{word} 110 km/h.", headline="Amtliche Meldung", event="Unwetter")
    assert result["wind"] and result["hard_lock"] and result["gust_max_kmh"] == 110


def test_gust_substrings_inside_unknown_words_are_not_word_tokens():
    for prefix, suffix in itertools.product(["Al", "Be", "Cal", "Dorn"], ["au", "burg", "tal"]):
        result = assess(f"Hinweis in {prefix}gust{suffix}, 110 km/h.",
                        headline="Amtliche Meldung", event="Unwetter")
        assert not result["wind"] and not result["hard_lock"]


def test_explicit_close_instruction_remains_protective_without_a_wind_word():
    from test_v0119_warning_scopes_pure import policy, warning

    result = policy.assess_official_warning(warning(headline="Rauch im August", event="Brand"),
                                            NOW, explicit_close=True)
    assert not result["wind"] and result["relevant"] and result["hard_lock"]

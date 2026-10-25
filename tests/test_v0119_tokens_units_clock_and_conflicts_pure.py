"""Regression coverage for the seven findings in the COMPLETE (1)(4) audit."""
from datetime import timedelta
import json

import pytest

from test_v0119_warning_scopes_pure import NOW, assess


@pytest.mark.parametrize("word", ["Windstöße", "Windstösse", "Windstoesse", "Windstoß", "Spitzenböen"])
@pytest.mark.parametrize("speed", [30, 70, 89, 90, 110, 140])
@pytest.mark.parametrize("denied", [False, True])
def test_gust_synonyms_keep_the_threshold_and_forecast_polarity(word, speed, denied):
    predicate = "werden nicht erwartet" if denied else "werden erwartet"
    result = assess(f"{word} bis {speed} km/h {predicate}.")
    assert result["hard_lock"] is (speed >= 90 and not denied)
    assert result["gust_max_kmh"] == (None if denied else speed)


@pytest.mark.parametrize("unit", ["km/u", "Kilometer pro Stunde", "Kilometer je Stunde",
                                  "kilometres per hour", "kilometers per hour", "kilometer per uur"])
@pytest.mark.parametrize("speed", [30, 70, 89, 90, 110, 140])
def test_speed_units_are_normalized_before_threshold_comparison(unit, speed):
    result = assess(f"Windstoten van {speed} {unit}.")
    assert result["gust_max_kmh"] == speed and result["hard_lock"] is (speed >= 90)
    assert unit in result["gust_original_text"]


@pytest.mark.parametrize("description", [
    "Spitzenböen unter 90 Kilometer pro Stunde.", "Windstoten minder dan 90 km/u.",
    "Windstöße 110 Kilometer pro Stunde werden nicht erwartet.",
    "No hay rachas de 110 Kilometer pro Stunde previstas.",
])
def test_extended_words_and_units_preserve_strict_bounds_and_negations(description):
    assert not assess(description)["hard_lock"]


@pytest.mark.parametrize("description", [
    "Hinweis in Windstößeberg, 110 km/h.", "Hinweis in Spitzenböendorf, 110 km/h.",
    "Windstöße 110 Kilometer.", "Spitzenböen 110 Liter pro Stunde.",
    "Windstoten 110 km.", "Hinweis 110 Kilometer pro Stunde.",
])
def test_unknown_words_units_and_unrelated_values_supply_no_gust(description):
    result = assess(description, headline="Amtliche Meldung", event="Unwetter")
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("clock", ["18:00 UTC", "18:00 Uhr UTC", "18 UTC", "18:00 GMT",
                                   "19:00 CET", "20:00 CEST", "19:00 MEZ", "20:00 MESZ"])
@pytest.mark.parametrize("offset,locked", [(-1801, False), (-1800, True), (-1, True), (0, True), (3600, True)])
def test_explicit_clock_zone_without_uhr_uses_the_same_exact_lead(clock, offset, locked):
    start = NOW.replace(hour=18, minute=0, second=0)
    result = assess(f"Böen 110 km/h ab {clock}.", now=start + timedelta(seconds=offset),
                    effective=NOW.replace(hour=0, minute=0), onset=NOW.replace(hour=0, minute=0),
                    expires=NOW.replace(hour=21, minute=59))
    assert result["hard_lock"] is locked and not result["gust_time_uncertain"]
    assert result["gust_onset"] == start.isoformat()


@pytest.mark.parametrize("clock", ["18:00", "18:00 Uhr", "25:00 UTC", "18:70 UTC", "18:00 UTC+02:00"])
def test_a_missing_zone_or_invalid_clock_remains_unresolved(clock):
    result = assess(f"Böen 110 km/h ab {clock}.", now=NOW.replace(hour=19),
                    onset=NOW.replace(hour=0, minute=0), expires=NOW.replace(hour=23, minute=59))
    assert not result["hard_lock"] and result["gust_time_uncertain"]


def test_clock_zone_still_needs_a_unique_cap_calendar_day():
    result = assess("Böen 110 km/h ab 18:00 UTC.", onset=NOW.replace(hour=0),
                    expires=NOW + timedelta(days=1))
    assert not result["hard_lock"] and result["gust_time_uncertain"]


def test_explicit_clock_end_without_uhr_expires_the_gusts():
    for hour, locked in [(17, True), (18, False), (19, False)]:
        result = assess("Böen 110 km/h bis 18:00 UTC.", now=NOW.replace(hour=hour),
                        onset=NOW.replace(hour=0), expires=NOW.replace(hour=23, minute=59))
        assert result["hard_lock"] is locked


INTERNATIONAL_DENIALS = [
    "No hay rachas de 110 km/h previstas.", "No hay rachas de 110 km/h.",
    "No se esperan rachas de 110 km/h.", "Des rafales de 110 km/h ne sont pas prévues.",
    "110 km/h rüzgâr hamleleri beklenmiyor.", "Rüzgâr hamleleri 110 km/h beklenmiyor.",
    "110 km/h rüzgar hamleleri beklenmemektedir.", "110 km/h rüzgâr hamleleri beklenmez.",
    "110 km/h rüzgâr hamleleri beklenmeyecektir.",
    "110 km/h rüzgâr hamlesi beklenmiyor.",
]


@pytest.mark.parametrize("description", INTERNATIONAL_DENIALS)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_international_denials_apply_to_their_gust_assertion(description, parameters):
    result = assess(description, parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None
    assert any(item["denied"] for item in result["gust_evidence"])


@pytest.mark.parametrize("description", [
    "Hay rachas de 110 km/h previstas.", "Se esperan rachas de 110 km/h.",
    "No hay daños con rachas de 110 km/h previstas.",
    "110 km/h rüzgâr hamleleri bekleniyor.", "110 km/h rüzgâr hamleleri beklenmektedir.",
    "110 km/h rüzgâr hamleleri beklenir.", "110 km/h rüzgâr hamleleri bekleniyor, hasar beklenmiyor.",
])
def test_international_positive_forecasts_and_negated_damage_do_not_deny_gusts(description):
    result = assess(description)
    assert result["hard_lock"] and result["gust_max_kmh"] == 110


@pytest.mark.parametrize("probability", ["ist null", "beträgt 0 Prozent", "liegt bei 0 %", "ist exakt 0,0 Prozent", "besteht nicht"])
@pytest.mark.parametrize("gust", ["von 110 km/h Böen", "für Böen 110 km/h"])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_explicit_zero_probability_is_not_a_positive_wind_forecast(probability, gust, parameters):
    result = assess(f"Die Wahrscheinlichkeit {gust} {probability}.", parameters)
    assert not result["hard_lock"] and result["gust_max_kmh"] is None


@pytest.mark.parametrize("description", [
    "Die Wahrscheinlichkeit von 110 km/h Böen ist nicht null.",
    "Die Wahrscheinlichkeit für Böen 110 km/h ist gering.",
    "Böen 110 km/h sind unwahrscheinlich.",
    "Böen 110 km/h, die Wahrscheinlichkeit von Schäden ist null.",
    "Die Wahrscheinlichkeit von Schäden bei Böen 110 km/h ist null.",
])
def test_small_probability_and_zero_probability_of_damage_do_not_exclude_gusts(description):
    assert assess(description)["hard_lock"]


@pytest.mark.parametrize("field", ["headline", "event"])
@pytest.mark.parametrize("title", ["Keine Böen von 110 km/h erwartet", "Böen 110 km/h sind ausgeschlossen",
                                   "Böen 110 km/h nicht erwartet", "Keine Sturmböen"])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_contradictory_header_and_description_keep_each_official_assertion(field, title, parameters):
    result = assess("Böen 110 km/h werden erwartet.", parameters, **{field: title})
    assert not result["hard_lock"] and result["gust_polarity_conflict"] and result["gust_conflict"]
    assert result["wind"] and result["relevant"]
    assert any(item["source"] == field and item["denied"] for item in result["gust_evidence"])
    assert any(item["source"] == "description" and not item["denied"] and item["max"] == 110
               for item in result["gust_evidence"])
    json.dumps(result, allow_nan=False)


def test_positive_header_and_denied_description_conflict_in_the_other_direction():
    result = assess("Böen 110 km/h sind ausgeschlossen.", headline="Böen 110 km/h werden erwartet.")
    assert result["gust_polarity_conflict"] and not result["hard_lock"]
    assert {item["source"] for item in result["gust_evidence"]} == {"headline", "description"}


def test_numeric_header_is_an_official_value_and_numeric_disagreement_keeps_existing_protection():
    result = assess("Böen 70 km/h.", headline="Böen 110 km/h werden erwartet.")
    assert result["hard_lock"] and result["gust_max_kmh"] == 110 and result["gust_conflict"]
    assert not result["gust_polarity_conflict"]


def test_negated_header_retains_the_flat_parameters_original_polarity():
    result = assess(parameters={"gusts": "110 km/h"}, headline="Keine Böen 110 km/h erwartet")
    assert not result["hard_lock"] and result["gust_polarity_conflict"]
    assert any(item["source"] == "parameter" and not item["denied"] for item in result["gust_evidence"])


@pytest.mark.parametrize("description,title,locked", [
    ("Böen 70 km/h werden erwartet.", "Böen 110 km/h sind ausgeschlossen", False),
    ("Böen 110 km/h nur im Harz.", "Böen 110 km/h sind ausgeschlossen", False),
    ("Böen 110 km/h bis 14:00 UTC.", "Böen 110 km/h ab 18:00 UTC sind ausgeschlossen", True),
])
def test_different_values_places_and_disjoint_periods_are_not_declared_the_same_conflict(description, title, locked):
    result = assess(description, headline=title, onset=NOW.replace(hour=0), expires=NOW.replace(hour=23, minute=59))
    assert not result["gust_polarity_conflict"] and result["hard_lock"] is locked


@pytest.mark.parametrize("hour,locked", [(12, True), (17, True), (18, False), (19, False)])
def test_a_later_denial_does_not_erase_the_earlier_uncontested_gust_period(hour, locked):
    result = assess("Böen 110 km/h werden erwartet.", now=NOW.replace(hour=hour),
                    headline="Böen 110 km/h ab 18:00 UTC sind ausgeschlossen",
                    onset=NOW.replace(hour=0, minute=0), expires=NOW.replace(hour=23, minute=59))
    assert result["hard_lock"] is locked and result["gust_polarity_conflict"]
    assert any(item["source"] == "description" and not item["denied"] for item in result["gust_evidence"])


def test_a_subregional_denial_does_not_restrict_an_independent_general_forecast():
    result = assess("Böen 110 km/h im gesamten Warngebiet.", headline="Böen 110 km/h im Harz sind ausgeschlossen")
    assert result["hard_lock"] and result["gust_max_kmh"] == 110
    assert not result["gust_polarity_conflict"]


def test_explicit_close_instruction_remains_independent_of_a_wind_polarity_conflict():
    from test_v0119_warning_scopes_pure import policy, warning

    result = policy.assess_official_warning(warning(headline="Keine Böen 110 km/h erwartet",
        description="Böen 110 km/h werden erwartet."), NOW, explicit_close=True)
    assert result["hard_lock"] and result["gust_polarity_conflict"] and result["explicit_close"]


@pytest.mark.parametrize("manual", [False, True])
def test_warning_adapters_keep_the_conflict_notice_without_creating_a_verified_wind_lock(manual):
    from types import SimpleNamespace
    from test_v0119_warning_scopes_pure import _provider_case, warning

    record = warning(headline="Keine Böen von 110 km/h erwartet",
                     description="Böen 110 km/h werden erwartet.")
    scope, entry = _provider_case(record)
    if manual:
        result = scope["WarningAssessment"]()
        scope["_apply_manual_official_notice"](result, record, elevation=60)
    else:
        result = scope["_automatic_warning_assessment"](SimpleNamespace(), entry)
    assert not result.weather_hard_lock
    notice = result.warning_notices[0]
    assert notice["gust_conflict"] and notice["gust_polarity_conflict"]
    assert {item["source"] for item in notice["gust_evidence"]} == {"headline", "description"}
    json.dumps(notice, allow_nan=False)

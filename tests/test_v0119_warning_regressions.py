"""Regression cases from the independent v0.11.9 audit, plus source conflicts."""
import asyncio
from datetime import datetime, timedelta, timezone
import random
from types import SimpleNamespace

import pytest

from custom_components.lueftungsberater.polling import RequestPacer
from custom_components.lueftungsberater.warning_policy import assess_official_warning, plain_text

NOW = datetime(2026, 10, 23, 12, 30, tzinfo=timezone.utc)


def warning(**changes):
    return SimpleNamespace(**{
        "warning_id": "audit.wind", "provider_domain": "meteoalarm_auto",
        "headline": "Wind gusts", "description": "", "parameters": {},
        "effective": NOW - timedelta(hours=1), "onset": NOW + timedelta(minutes=30),
        "expires": NOW + timedelta(hours=3), **changes})


UPPER_LIMITS = [
    "Böen unter 90 km/h werden erwartet.",
    "Böen von weniger als 90 km/h sind angekündigt.",
    "Wind gusts less than 90 km/h.", "Gusts below 90 km/h.",
    "Rafales inférieures à 90 km/h.", "Rachas inferiores a 90 km/h.",
    "Raffiche inferiori a 90 km/h.", "Windstoten minder dan 90 km/h.",
    "Gusts under 25 m/s.", "Böen <90 [km/h].",
]
EXPOSED = [
    "Böen bis {n} km/h in exponierten Lagen.",
    "Böen bis {n} km/h auf Gipfeln.",
    "Wind gusts reaching {n} km/h above 1000 m.",
    "Rafales {n} km/h au-dessus de 1000 m.",
    "Gusts up to {n} km/h at summit elevations.",
    "In exponierten Lagen Böen bis {n} km/h.",
    "Rafales de {n} km/h sur les crêtes.",
    "Rachas de {n} km/h en zonas expuestas.",
    "Raffiche fino a {n} km/h sulle cime.",
]


@pytest.mark.parametrize("description", UPPER_LIMITS)
@pytest.mark.parametrize("parameters", [{}, {"gusts": "90 km/h"}])
def test_natural_strict_upper_bounds_keep_comparison_and_do_not_lock(description, parameters):
    notice = assess_official_warning(warning(description=description, parameters=parameters), NOW)
    assert notice["relevant"] and not notice["hard_lock"]
    assert notice["gust_max_kmh"] < 90
    assert notice["gust_min_kmh"] is None
    assert notice["description"] == description
    assert notice["gust_original_text"] != "90 km/h"


@pytest.mark.parametrize("description", [pattern.format(n=120) for pattern in EXPOSED])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "120 km/h"}])
def test_exposed_or_unmatched_height_after_speed_does_not_become_general_gust(description, parameters):
    notice = assess_official_warning(warning(description=description, parameters=parameters), NOW, elevation=60)
    assert notice["relevant"] and not notice["hard_lock"]
    assert notice["gust_max_kmh"] is None
    assert notice["description"] == description


@pytest.mark.parametrize("description", [
    "Es werden keine Böen über 90 km/h erwartet.",
    "Böen von 120 km/h werden nicht erreicht.",
    "No wind gusts above 90 km/h are expected.",
    "Wind gusts of 120 km/h are not expected.",
    "Aucune rafale de 120 km/h n'est attendue.",
    "Rafales de 120 km/h ne sont pas attendues.",
    "Non sono previste raffiche di 120 km/h.",
    "No se esperan rachas de 120 km/h.",
])
def test_negated_speed_is_not_positive_warning_evidence(description):
    notice = assess_official_warning(warning(description=description,
        parameters={"gusts": "120 km/h"}), NOW)
    assert notice["relevant"] and not notice["hard_lock"]
    assert notice["gust_max_kmh"] is None


@pytest.mark.parametrize("name,value", [
    ("gusts", "less than 90 km/h"), ("gusts under", "90 km/h"),
    ("gusts", "120 km/h in exposed places"), ("exposed gusts", "120 km/h"),
    ("gusts", "90 km/h above 1000 m"), ("gusts above 1000 m", "120 km/h"),
    ("gusts", "no gusts above 90 km/h"), ("gusts", {"untrusted": "120 km/h"}),
])
def test_parameter_names_and_values_are_both_subject_to_qualifications(name, value):
    notice = assess_official_warning(warning(parameters={name: value}), NOW, elevation=60)
    assert not notice["hard_lock"]


def test_comparison_in_parameter_name_is_retained_for_display():
    notice = assess_official_warning(warning(parameters={"gusts less than": "25 m/s"}), NOW)
    assert notice["gust_max_kmh"] < 90
    assert notice["gust_min_kmh"] is None
    assert notice["gust_original_text"] == "less than 25 m/s"


@pytest.mark.parametrize("description,elevation,locked", [
    ("Böen 100 km/h oberhalb 1000 m.", 1000, False),
    ("Böen 100 km/h oberhalb 1000 m.", 1001, True),
    ("Böen 100 km/h ab 1000 m.", 1000, True),
    ("Gusts 100 km/h above 3000 ft.", 1000, True),
    ("Rafales 100 km/h au-dessus de 1000 m.", 1200, True),
    ("Gusts 100 km/h below 1000 m.", 1000, False),
    ("Gusts 100 km/h below 1000 m.", 60, True),
    ("Böen 100 km/h in exponierten Lagen oberhalb 1000 m.", 1200, False),
    ("Böen 100 km/h oberhalb 1000 m.", None, False),
    ("Böen 100 km/h oberhalb 1000 m.", float("nan"), False),
    ("Böen 100 km/h oberhalb 1000 m.", float("inf"), False),
    ("Böen 100 km/h oberhalb 1000 m.", True, False),
])
def test_only_verified_explicit_height_can_apply_to_numeric_gust(description, elevation, locked):
    notice = assess_official_warning(warning(description=description), NOW, elevation=elevation)
    assert notice["hard_lock"] is locked


@pytest.mark.parametrize("headline", ["Böen auf Gipfeln", "Wind gusts above 1000 m", "Keine Sturmböen"])
def test_title_qualifiers_cannot_be_overridden_by_flat_parameters_or_cap_height(headline):
    notice = assess_official_warning(warning(headline=headline,
        parameters={"gusts": "120 km/h"}, area_altitude=0), NOW, elevation=60)
    assert not notice["hard_lock"]


@pytest.mark.parametrize("separator", ["; ", ". ", "\n", "<br>", "</p><p>"])
def test_separate_general_gust_is_retained_beside_exposed_maximum(separator):
    description = f"Böen 75 km/h{separator}In exponierten Lagen Böen 120 km/h."
    notice = assess_official_warning(warning(description=description,
        parameters={"gusts": "120 km/h"}), NOW, elevation=60)
    assert notice["gust_max_kmh"] == 75
    assert notice["level"] == "strong" and not notice["hard_lock"]


def test_late_qualifier_is_not_cut_off_at_arbitrary_character_count():
    description = "Böen bis 120 km/h " + "mit besonderer örtlicher Ausprägung " * 5 + "in exponierten Lagen."
    assert not assess_official_warning(warning(description=description), NOW)["hard_lock"]
    assert plain_text("<b>Böen</b> <90 km/h; exponiert >120 km/h") == "Böen <90 km/h; exponiert >120 km/h"


@pytest.mark.parametrize("gusts,locked", [("30 km/h", False), ("89.999 km/h", False),
    ("90 km/h", True), ("90-100 km/h", True), ("25 m/s", True),
    ("49 knots", True), ("58 mph", True), ("<=90 km/h", True)])
def test_valid_general_official_gust_threshold_and_lead_time_are_preserved(gusts, locked):
    record = warning(parameters={"gusts": gusts})
    assert not assess_official_warning(record, NOW - timedelta(seconds=1))["hard_lock"]
    assert assess_official_warning(record, NOW)["hard_lock"] is locked
    assert assess_official_warning(record, record.expires) is None


def test_original_four_thousand_adversarial_cases():
    # The seed and first six/five patterns reproduce the attached audit exactly.
    rng = random.Random(20261023)
    for patterns, speeds in [(UPPER_LIMITS[:6], [90]), (EXPOSED[:5], [90, 100, 110, 120])]:
        for _ in range(2000):
            description = rng.choice(patterns).format(n=rng.choice(speeds))
            notice = assess_official_warning(warning(description=description), NOW)
            assert notice["relevant"] and not notice["hard_lock"], description


@pytest.mark.parametrize("description,speed", [
    ("Böen von 110 km/h, jedoch kein Starkregen.", 110),
    ("Böen von 120 km/h, aber kein Hagel.", 120),
    ("Sturmböen bis 100 km/h, stellenweise kein Regen.", 100),
    ("Böen 110 km/h, ohne Gewitter.", 110),
    ("Böen 110 km/h ohne Gewitter.", 110),
    ("Kein Hagel, aber Böen 110 km/h.", 110),
    ("Wind gusts 120 km/h but no rain.", 120),
    ("Wind gusts 110 km/h without thunderstorms.", 110),
    ("No rain, but wind gusts of 110 km/h.", 110),
    ("Rafales de 110 km/h, mais pas de pluie.", 110),
    ("Rachas de 110 km/h, pero sin lluvia.", 110),
    ("Raffiche di 110 km/h, ma senza grandine.", 110),
    ("Windstoten 110 km/h, maar geen regen.", 110),
    ("Böen 110 km/h, aber keine Glätte.", 110),
    ("Keine Glätte, aber Böen 110 km/h.", 110),
    ("Wind gusts 110 km/h but no icing.", 110),
    ("Wind gusts 110 km/h but no icing is expected.", 110),
    ("Böen 110 km/h, aber keine Glätte prognostiziert.", 110),
    ("Rafales 110 km/h, mais aucun risque d'inondation.", 110),
    ("Wind gusts 110 km/h could damage concrete structures.", 110),
])
@pytest.mark.parametrize("structured", [False, True])
def test_other_weather_negation_does_not_cancel_actual_gusts(description, speed, structured):
    notice = assess_official_warning(warning(description=description,
        parameters={"gusts": f"{speed} km/h"} if structured else {}), NOW)
    assert notice["hard_lock"]
    assert notice["gust_max_kmh"] == speed


@pytest.mark.parametrize("description,speed", [
    ("Böen 110 km/h, in exponierten Lagen 140 km/h.", 110),
    # Qualitative lower terrain is not a verified altitude range either.
    ("Böen 110 km/h in tieferen Lagen und 140 km/h auf Gipfeln.", None),
    ("Böen 110 km/h und in exponierten Lagen 150 km/h.", 110),
    ("Böen 110 km/h, in exponierten Lagen Böen 140 km/h.", 110),
    ("Böen 75 km/h, in exponierten Lagen 140 km/h.", 75),
    ("Böen unter 90 km/h, in exponierten Lagen 140 km/h.", 89.99999999999999),
    ("In exponierten Lagen Böen 140 km/h, allgemein 110 km/h.", 110),
    ("Böen 110 km/h, in exponierten Lagen, bis 140 km/h.", 110),
    ("Wind gusts 110 km/h and 140 km/h on summits.", 110),
    ("Rafales de 110 km/h, et de 140 km/h sur les crêtes.", 110),
    ("Rachas de 110 km/h y de 140 km/h en zonas expuestas.", 110),
    ("Raffiche di 110 km/h e 140 km/h sulle cime.", 110),
    ("Böen 110 km/h (auf Gipfeln 140 km/h).", 110),
    ("Böen 75 km/h (auf Gipfeln 140 km/h).", 75),
])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "140 km/h"}])
def test_only_the_qualified_value_is_excluded_from_general_gusts(description, speed, parameters):
    notice = assess_official_warning(warning(description=description, parameters=parameters), NOW, elevation=60)
    assert notice["gust_max_kmh"] == speed
    assert notice["hard_lock"] is (speed is not None and speed >= 90)


@pytest.mark.parametrize("description", [
    "Böen 110 km/h, auf Gipfeln.",
    "Böen 110 km/h, jedoch nur in exponierten Lagen.",
    "Wind gusts 110 km/h, but only above 1000 m.",
    "Böen 110 km/h, die nicht erreicht werden.",
    "Keine Böen über 90 km/h, aber Hagel.",
    "No wind gusts above 90 km/h, but heavy rain.",
    "Böen 30 km/h, Regen mit 110 km/h.",
    "Böen 30 km/h, Wind 110 km/h.",
    "Böen 110 km/h (nur auf Gipfeln).",
    "Gusts: 110 km/h above 1000 m.",
    "Wind gusts 110 km/h, but no longer expected.",
])
def test_splitting_cannot_detach_a_modifier_or_turn_another_measurement_into_gusts(description):
    notice = assess_official_warning(warning(description=description), NOW, elevation=60)
    assert not notice["hard_lock"]


@pytest.mark.parametrize("headline,locked", [
    ("Sturmböen, jedoch kein Hagel", True),
    ("Sturmböen ohne Gewitter", True),
    ("Wind gusts but no rain", True),
    ("Sturmböen auf Gipfeln", False),
    ("Keine Sturmböen", False),
    ("Gusts: 110 km/h above 1000 m", False),
])
def test_headline_qualifications_are_scoped_to_their_own_subject(headline, locked):
    notice = assess_official_warning(warning(headline=headline, parameters={"gusts": "110 km/h"}), NOW)
    assert notice["hard_lock"] is locked


@pytest.mark.parametrize("value,speed", [
    ("110 km/h, aber kein Hagel", 110),
    ("110 km/h, in exponierten Lagen 140 km/h", 110),
    ("75 km/h, in exponierten Lagen 140 km/h", 75),
    ("110 km/h, nur auf Gipfeln", None),
])
def test_structured_value_contains_independent_gust_assertions(value, speed):
    notice = assess_official_warning(warning(parameters={"gusts": value}), NOW)
    assert notice["gust_max_kmh"] == speed
    assert notice["hard_lock"] is (speed is not None and speed >= 90)


def test_ten_thousand_followup_examples_include_positive_and_negative_wind():
    rng = random.Random(20261023)
    positives = ["Böen von {n} km/h, aber kein Hagel.",
        "Böen bis {n} km/h, jedoch kein Starkregen.",
        "Wind gusts {n} km/h but no rainfall.",
        "Böen von {n} km/h und in exponierten Lagen 150 km/h.",
        "Böen {n} km/h in tieferen Lagen und 145 km/h auf Gipfeln."]
    negatives = ["Böen unter 90 km/h.", "Wind gusts less than 90 km/h.",
        "Böen bis 120 km/h auf Gipfeln.", "Gusts 110 km/h above 1000 m."]
    for index in range(10000):
        expected = index % 2 == 0
        description = rng.choice(positives).format(n=rng.choice([90, 95, 100, 110, 120, 130])) if expected else rng.choice(negatives)
        # Keep the original generated texts; correct the old assumption that
        # any elevation of 60 m proves membership of unspecified lower terrain.
        expected = expected and "in tieferen Lagen" not in description
        notice = assess_official_warning(warning(description=description), NOW, elevation=60)
        assert notice["hard_lock"] is expected, description


PREDICATE_POSITIVES = [
    "Bei Böen bis {n} km/h sind keine Fenster offen zu lassen.",
    "Böen bis {n} km/h können keine Schäden ausgeschlossen werden.",
    "Windböen von {n} km/h, Schäden sind nicht auszuschließen.",
    "Sturmböen bis {n} km/h ohne nennenswerte Niederschläge.",
    "Windböen von {n} km/h ohne weitere Gewitter.",
    "Böen bis {n} km/h mit keiner nennenswerten Regenmenge.",
    "Wind gusts {n} km/h and lightning is not expected.",
    "Wind gusts {n} km/h not accompanied by rain.",
    "Rafales à {n} km/h sans fortes précipitations.",
    "Böen bis {n} km/h, aber kein Hagel.",
    "Böen {n} km/h in tieferen Lagen und 145 km/h auf Gipfeln.",
    "Wind gusts {n} km/h but no rainfall.",
]
PREDICATE_NEGATIVES = [
    "Böen über {n} km/h sind ausgeschlossen.",
    "Böen {n} km/h nur in Hochlagen.",
    "Böen {n} km/h nur auf Gipfeln.",
    "Böen {n} km/h ausschließlich in exponierten Lagen.",
    "Böen unter 90 km/h, auf Gipfeln bis {n} km/h.",
    "Böen 85 km/h, in freien Lagen {n} km/h.",
    "Wind gusts less than 90 km/h, up to {n} km/h at summits.",
]


def test_complete3_independent_nine_thousand_five_hundred_counterexamples():
    # Same patterns, seed and speed selection as independent_adversarial.py.
    rng = random.Random(20261023)
    for patterns, locked in [(PREDICATE_POSITIVES, True), (PREDICATE_NEGATIVES, False)]:
        for pattern in patterns:
            for _ in range(500):
                speed = rng.choice([90, 95, 100, 105, 110, 120, 140, 160])
                description = pattern.format(n=speed)
                notice = assess_official_warning(warning(description=description), NOW, elevation=60)
                expected = locked and "in tieferen Lagen" not in description
                assert notice["hard_lock"] is expected, description


@pytest.mark.parametrize("description", [pattern.format(n=110) for pattern in PREDICATE_POSITIVES] + [
    "Böen 110 km/h sind nicht auszuschließen.",
    "Böen 110 km/h können nicht ausgeschlossen werden.",
    "Böen 110 km/h sind nicht unmöglich.",
    "Wind gusts 110 km/h cannot be ruled out.",
    "Wind gusts 110 km/h are not excluded.",
    "Rafales 110 km/h ne sont pas exclues.",
    "Böen 110 km/h, Schäden ausgeschlossen.",
    "Böen 110 km/h, Folgeschäden sind nicht ausgeschlossen.",
    "Böen 110 km/h, Stromausfälle werden nicht erwartet.",
    "Böen 110 km/h, Schäden auf Gipfeln sind ausgeschlossen.",
    "Böen 110 km/h, an der Küste keine Schäden erwartet.",
    "Wind gusts 110 km/h, no wind damage is expected.",
    "Wind gusts 110 km/h are not expected to cause damage.",
    "Wind gusts 110 km/h are not expected to produce flooding.",
    "Wind gusts 110 km/h are not expected to threaten buildings.",
    "Es ist nicht ausgeschlossen, dass Böen 110 km/h erreichen.",
    "It is not excluded that wind gusts reach 110 km/h.",
    "Böen 110 km/h, die Schäden verursachen können, sind nicht ausgeschlossen.",
    "Böen 110 km/h sind nicht ausgeschlossen, Schäden aber schon.",
    "Keine Schäden bei Böen 110 km/h.",
    "No damage is expected with wind gusts 110 km/h.",
])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_possible_gust_or_negated_consequence_keeps_the_numeric_forecast(description, parameters):
    notice = assess_official_warning(warning(description=description, parameters=parameters), NOW, elevation=60)
    expected = "in tieferen Lagen" not in description
    assert notice["hard_lock"] is expected
    assert notice["gust_max_kmh"] == (110 if expected else None)
    assert notice["description"] == description


@pytest.mark.parametrize("description", [
    "Böen 110 km/h sind ausgeschlossen.",
    "Böen 110 km/h sind unmöglich.",
    "Böen 110 km/h sind nicht möglich.",
    "Böen 110 km/h können nicht auftreten.",
    "Böen 110 km/h werden ausdrücklich nicht erwartet.",
    "Böen 110 km/h sind nicht zu erwarten.",
    "Böen 110 km/h, die nicht erreicht werden.",
    "Wind gusts 110 km/h are excluded.",
    "Wind gusts 110 km/h are ruled out.",
    "Wind gusts 110 km/h are not expected to occur.",
    "Wind gusts 110 km/h are not expected to be observed.",
    "Wind gusts 110 km/h are not anticipated.",
    "Wind gusts 110 km/h are no longer expected.",
    "Wind gusts are not expected to reach 110 km/h.",
    "Wind gusts are not expected to exceed 110 km/h.",
    "Es ist ausgeschlossen, dass Böen 110 km/h erreichen.",
    "It is excluded that wind gusts reach 110 km/h.",
    "Nicht zu erwarten sind Böen 110 km/h.",
    "Böen 110 km/h sind nicht ausgeschlossen, werden aber nicht erwartet.",
    "Böen 110 km/h, die Schäden verursachen können, sind ausgeschlossen.",
    "Böen 110 km/h sind ausgeschlossen, Schäden aber nicht.",
    "Rafales 110 km/h sont exclues.",
    "Rafales 110 km/h ne sont pas attendues.",
    "Ohne Böen über 90 km/h.",
    "Without wind gusts above 90 km/h.",
    "Keine Böen.", "No wind gusts are expected.",
])
@pytest.mark.parametrize("parameters", [{}, {"gusts": "110 km/h"}])
def test_denial_of_gust_event_prevents_flat_parameter_from_creating_a_lock(description, parameters):
    notice = assess_official_warning(warning(description=description, parameters=parameters), NOW)
    assert not notice["hard_lock"]
    assert notice["gust_max_kmh"] is None
    assert notice["description"] == description


@pytest.mark.parametrize("description", [
    "Böen 110 km/h nur an der Küste.",
    "Böen 110 km/h außerhalb des Stadtgebiets.",
    "Gusts 110 km/h only at the coast.",
    "Rafales 110 km/h seulement sur le littoral.",
    "Böen 110 km/h in freien Lagen.",
    "Böen 110 km/h in Berglagen.",
])
def test_unverified_regional_qualification_cannot_become_a_general_speed(description):
    notice = assess_official_warning(warning(description=description,
        parameters={"gusts": "110 km/h"}), NOW, elevation=60)
    assert not notice["hard_lock"]
    assert notice["gust_max_kmh"] is None


@pytest.mark.parametrize("description", [
    "Böen 75 km/h, Böen 110 km/h sind ausgeschlossen.",
    "Böen 75 km/h, Schäden ab 110 km/h.",
    "Wind gusts 75 km/h, damage at 110 km/h is not excluded.",
])
def test_another_negated_claim_or_consequence_threshold_does_not_replace_general_gust(description):
    notice = assess_official_warning(warning(description=description), NOW)
    assert notice["gust_max_kmh"] == 75
    assert not notice["hard_lock"]


@pytest.mark.parametrize("headline,locked", [
    ("Wind gusts 110 km/h are excluded", False),
    ("Böen 110 km/h sind ausgeschlossen", False),
    ("Böen 110 km/h sind nicht ausgeschlossen", True),
    ("Wind gusts, damage is not expected", True),
])
def test_forecast_polarity_is_also_read_from_the_headline(headline, locked):
    notice = assess_official_warning(warning(headline=headline,
        parameters={"gusts": "110 km/h"}), NOW)
    assert notice["hard_lock"] is locked


@pytest.mark.parametrize("headline,event,locked", [
    ("Keine Sturmböen", "Wind", False),
    ("Böen 110 km/h sind ausgeschlossen", "Wind", False),
    ("Sturmböen auf Gipfeln", "Wind", False),
    ("Wind gusts", "Wind above 1000 m", False),
    ("Wind gusts", "Böen 110 km/h sind ausgeschlossen", False),
    ("Böen 110 km/h sind nicht ausgeschlossen", "Wind", True),
    ("Wind gusts, damage is not expected", "Wind", True),
])
def test_generic_event_label_cannot_change_headline_meaning(headline, event, locked):
    notice = assess_official_warning(warning(headline=headline, event=event,
        parameters={"gusts": "110 km/h"}), NOW, elevation=60)
    assert notice["hard_lock"] is locked


async def test_warning_wins_equal_deadline_and_other_requests_keep_fifo(monkeypatch):
    pacer = RequestPacer(None)
    monkeypatch.setattr(RequestPacer, "gap", property(lambda self: 0))
    order = []
    async def operation(name):
        order.append(name)
    deadline = pacer.clock() + 1000
    await asyncio.gather(*(pacer.submit(lambda name=name: operation(name), deadline=deadline,
        bootstrap=False, urgent=urgent) for name, urgent in [
            ("station1", False), ("warning1", True), ("station2", False), ("warning2", True)]))
    assert order == ["warning1", "warning2", "station1", "station2"]
    await pacer.close()


async def test_warning_priority_keeps_earlier_freshness_deadline(monkeypatch):
    pacer = RequestPacer(None)
    monkeypatch.setattr(RequestPacer, "gap", property(lambda self: 0))
    order = []
    async def operation(name):
        order.append(name)
    deadline = pacer.clock() + 1000
    await asyncio.gather(
        pacer.submit(lambda: operation("expiring_station"), deadline=deadline,
                     bootstrap=False, urgent=False),
        pacer.submit(lambda: operation("warning"), deadline=deadline + 1,
                     bootstrap=False, urgent=True))
    assert order == ["expiring_station", "warning"]
    await pacer.close()


async def test_warning_reorders_waiting_queue_without_cancelling_running_transport(monkeypatch):
    clock = SimpleNamespace(now=0.)
    pacer = RequestPacer(None, clock=lambda: clock.now)
    monkeypatch.setattr(RequestPacer, "gap", property(lambda self: 0))
    running, release, warned = asyncio.Event(), asyncio.Event(), asyncio.Event()
    order = []
    async def slow_station():
        order.append(("running_station", clock.now))
        running.set()
        await release.wait()
        clock.now += 20  # Simulated actual HTTP timeout budget; no real sleep.
        return "complete"
    async def operation(name):
        order.append((name, clock.now))
        if name == "warning":
            warned.set()
    first = asyncio.create_task(pacer.submit(slow_station, deadline=100,
        bootstrap=False, urgent=False))
    await running.wait()
    station = asyncio.create_task(pacer.submit(lambda: operation("waiting_station"),
        deadline=100, bootstrap=False, urgent=False))
    alert = asyncio.create_task(pacer.submit(lambda: operation("warning"),
        deadline=100, bootstrap=False, urgent=True))
    await asyncio.wait_for(warned.wait(), 1)
    assert not first.done()  # Priority also works while the station is blocked.
    release.set()
    assert await first == "complete"
    await asyncio.gather(station, alert)
    assert order == [("running_station", 0), ("warning", 0), ("waiting_station", 0)]
    await pacer.close()

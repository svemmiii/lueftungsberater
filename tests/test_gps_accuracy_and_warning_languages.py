"""Mobile accuracy and official FR/NL/IT protective-action regressions."""
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.lueftungsberater import auto_providers as ap
from custom_components.lueftungsberater.const import CONF_LOCATION_TRACKER
from custom_components.lueftungsberater.location import effective_location
from custom_components.lueftungsberater.outside import LueftungsberaterOutsideCoordinator
from custom_components.lueftungsberater.providers import _evaluate_air_warning
from custom_components.lueftungsberater.warning_regions import coordinate_country
from test_provider_location_regressions import NOW, TRACKER, mobile_hass, tracker_state


@pytest.mark.parametrize('accuracy,valid', [(0,True),(12.5,True),(250,True),(250.01,False),(3000,False),(-1,False),('nan',False),('inf',False),('bad',False),(None,False),(True,False)])
def test_accuracy_in_metres(accuracy,valid):
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        loc=effective_location(mobile_hass(tracker_state(gps_accuracy=accuracy)),SimpleNamespace(data={CONF_LOCATION_TRACKER:TRACKER}))
    assert loc.available is valid
    assert loc.position_valid is valid


def test_missing_accuracy_remains_compatible():
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        loc=effective_location(mobile_hass(tracker_state()),SimpleNamespace(data={CONF_LOCATION_TRACKER:TRACKER}))
    assert loc.available and loc.accuracy_m is None


def coordinator():
    instance=object.__new__(LueftungsberaterOutsideCoordinator)
    instance.entry=SimpleNamespace(data={CONF_LOCATION_TRACKER:TRACKER})
    instance._last_valid_mobile_location=None
    return instance


def test_poor_border_fix_never_switches_country_or_extends_hold():
    instance=coordinator()
    # Eupen (BE) and Aachen (DE): a poor fix must not move the accepted source.
    state=tracker_state(latitude=50.63,longitude=6.03,gps_accuracy=20)
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        instance.hass=mobile_hass(state); accepted=instance._candidate_location()
        assert coordinate_country(accepted.latitude,accepted.longitude)=='BE'
    for minutes in (1,10,29,31):
        time=NOW+timedelta(minutes=minutes)
        state=tracker_state(latitude=50.77,longitude=6.09,gps_accuracy=3000)
        state.last_reported=time
        with patch.object(ap.dt_util,'utcnow',return_value=time):
            instance.hass=mobile_hass(state); held=instance._candidate_location()
        assert held.latitude==accepted.latitude and held.longitude==accepted.longitude
        assert held.updated_at==NOW
        assert held.available is (minutes<=30)
    state.attributes['gps_accuracy']=15
    with patch.object(ap.dt_util,'utcnow',return_value=time):
        recovered=instance._candidate_location()
    assert recovered.available and coordinate_country(recovered.latitude,recovered.longitude)=='DE'


def test_restart_with_only_poor_fix_has_no_accepted_location():
    instance=coordinator()
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        instance.hass=mobile_hass(tracker_state(age=1,gps_accuracy=3000))
        assert not instance._candidate_location().available
        assert instance._last_valid_mobile_location is None


@pytest.mark.parametrize('text', [
    'Sluit ramen en deuren.', 'Zet ventilatie uit.', 'Schakel mechanische ventilatie uit.',
    'Houd ramen en deuren gesloten.',
    'Fermez les portes, les fenêtres et coupez la ventilation.',
    'Gardez les fenêtres fermées.', 'Arrêtez la ventilation.',
    'Ne quittez pas votre abri et fermez les fenêtres.',
    'Chiudi porte e finestre.', 'Spegni gli impianti di ventilazione.',
    'Tenete le finestre chiuse.',
])
def test_official_foreign_orders_lock(text):
    assert _evaluate_air_warning('',text,'')=='danger'


@pytest.mark.parametrize('text', [
    'Ne fermez pas les fenêtres.', 'Ne coupez plus la ventilation.',
    'Sluit ramen niet.', 'Zet ventilatie niet uit.',
    'Non chiudere le finestre.', 'Non spegnere la ventilazione.',
    'U kunt ramen en deuren weer openen en ventilatie aanzetten.',
    'Vous pouvez ouvrir les fenêtres.', 'Potete aprire le finestre.',
    'Incendie industriel. Risque élevé.', 'Brand met rook.', 'Incendio grave.',
])
def test_negations_releases_and_severity_do_not_lock(text):
    assert _evaluate_air_warning('',text,'')!='danger'


@pytest.mark.parametrize('text', ["L’alerte est levée.",'NL-Alert voor brand is ingetrokken.','Het gevaar is geweken.','Cessato allarme.','Allarme revocato.'])
def test_full_foreign_clear_beats_copied_old_action(text):
    assert _evaluate_air_warning(text,'','Sluit ramen en deuren.')=='clear'


@pytest.mark.parametrize('text', ["L’alerte est partiellement levée.","L’alerte n’est pas levée.",'De waarschuwing is niet ingetrokken.','NL-Alert is gedeeltelijk ingetrokken.','Allarme non revocato.','Allarme parzialmente revocato.'])
def test_partial_or_negated_clear_keeps_explicit_lock(text):
    assert _evaluate_air_warning(text,'','Sluit ramen en deuren.')=='danger'


def test_cap_cancel_is_authoritative_without_translated_clear_text():
    assert _evaluate_air_warning('','','Fermez les fenêtres.','Cancel')=='clear'

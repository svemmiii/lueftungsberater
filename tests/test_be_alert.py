"""Official BE-Alert current-feed structure and CAP follow-up tests."""
from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.lueftungsberater import auto_providers as ap
from custom_components.lueftungsberater.be_alert import _candidate_ids, _record, fetch_be_warnings
from custom_components.lueftungsberater.national_warnings import combine_warning_sources
from custom_components.lueftungsberater.providers import _evaluate_air_warning
from test_provider_location_regressions import LOCATION, NOW, cap

GUID='6abe94610ffd731d6843d6fc'
BE_LOCATION=replace(LOCATION, country='BE')


def feed(*,items=None,pubdate=None,description='activeOnly: true'):
    return {'items':[] if items is None else items,'pubDate':pubdate or NOW.isoformat(),'description':description}


def row(**changes):
    value={'guid':GUID,'title':'Rookontwikkeling','description':'Hou best ramen en deuren gesloten.',
           'expirationDate':(NOW+timedelta(hours=1)).isoformat(),
           'area':[{'type':'Polygon','coordinates':[{'type':'LineString','coordinates':[
               {'x':6,'y':50},{'x':7,'y':50},{'x':7,'y':51},{'x':6,'y':51},{'x':6,'y':50}
           ]}]}]}
    value.update(changes)
    return value


def test_current_feed_filters_point_and_historical_expiry():
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        assert _candidate_ids(feed(items=[row()]),BE_LOCATION)==([GUID],0)
        assert _candidate_ids(feed(items=[row()]),replace(BE_LOCATION,latitude=49))==([],0)
        assert _candidate_ids(feed(items=[row(expirationDate=(NOW-timedelta(minutes=1)).isoformat())]),BE_LOCATION)==([],0)


@pytest.mark.parametrize('payload',[None,{'items':None},feed(description='activeOnly: false'),feed(pubdate=(NOW-timedelta(hours=1)).isoformat())])
def test_invalid_or_stale_feed_is_unknown(payload):
    with patch.object(ap.dt_util,'utcnow',return_value=NOW),pytest.raises(ValueError):
        _candidate_ids(payload,BE_LOCATION)


@pytest.mark.parametrize('changes',[{'area':[]},{'guid':'bad'},{'expirationDate':None}])
def test_unresolved_current_alert_prevents_entwarnung(changes):
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        assert _candidate_ids(feed(items=[row(**changes)]),BE_LOCATION)==([],1)


@pytest.mark.parametrize('title,description',[('Test BE-Alert','Fermez les fenêtres.'),('Alarm','Ceci est un test. Fermez les fenêtres.'),('Feuerwehrübung','Fenster schließen')])
def test_probes_published_with_actual_cap_status_are_excluded(title,description):
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        assert _candidate_ids(feed(items=[row(title=title,description=description)]),BE_LOCATION)==([],0)


def test_actual_warning_saying_not_a_test_is_retained():
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        assert _candidate_ids(feed(items=[row(description='Dit is geen test. Sluit ramen en deuren.')]),BE_LOCATION)==([GUID],0)


def test_belgian_flemish_instruction_is_hard():
    assert _evaluate_air_warning('','Hou best ramen en deuren gesloten.','')=='danger'


def test_cap_is_reclassified_civil_and_probe_is_ignored():
    document=cap(polygon='50,6 50,7 51,7 51,6 50,6')
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        record=_record(document,BE_LOCATION)
        assert record.provider_domain=='be_alert_auto' and record.category=='civil'
        assert _record(document.replace('Storm','Test LB-SMS'),BE_LOCATION) is None


@pytest.mark.asyncio
async def test_matching_cap_details_and_failed_retry(hass):
    document=cap(polygon='50,6 50,7 51,7 51,6 50,6')
    with patch.object(ap.dt_util,'utcnow',return_value=NOW),patch('custom_components.lueftungsberater.be_alert._get_json',AsyncMock(return_value=feed(items=[row()]))),patch('custom_components.lueftungsberater.be_alert._get_text',AsyncMock(side_effect=[RuntimeError('offline'),document])) as get:
        failed=await fetch_be_warnings(hass,object(),BE_LOCATION)
        success=await fetch_be_warnings(hass,object(),BE_LOCATION)
    assert not failed.available and failed.error=='be_alert_incomplete'
    assert success.available and len(success.warnings)==1
    assert get.await_args.args[1]==f'https://publicalerts.be/CapGateway/alert/{GUID}'


@pytest.mark.asyncio
async def test_be_source_failure_cannot_be_cleared_by_meteoalarm(hass):
    weather=ap.AutoWarningData('meteoalarm_auto',NOW,True,'BE')
    with patch('custom_components.lueftungsberater.national_warnings.fetch_civil_warnings',AsyncMock(side_effect=RuntimeError('offline'))):
        result=await combine_warning_sources(hass,object(),BE_LOCATION,'BE',AsyncMock(return_value=weather)())
    assert not result.available
    assert result.source_availability=={'meteoalarm_auto':True,'be_alert_auto':False}


@pytest.mark.asyncio
async def test_belgium_automatically_selects_both_sources(hass):
    state=ap.AutoProviderState()
    expected=ap.AutoWarningData('combined',NOW,True,'BE')
    with patch.object(ap,'_fetch_meteoalarm_warnings',AsyncMock(return_value=expected)),patch('custom_components.lueftungsberater.national_warnings.combine_warning_sources',AsyncMock(return_value=expected)) as combine:
        assert await ap._fetch_auto_warning(hass,object(),BE_LOCATION,'BE',state) is expected
        weather_call=combine.await_args.args[-1]
        await weather_call
    assert combine.await_args.args[3]=='BE'

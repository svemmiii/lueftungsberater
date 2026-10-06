"""Provider regressions using real catalog formats and public feed schemas."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from custom_components.lueftungsberater import auto_providers as ap
from custom_components.lueftungsberater.const import CONF_LOCATION_TRACKER, CONF_WARNING_SOURCE_MODE, CONF_WEATHER_SOURCE_MODE, WEATHER_SOURCE_AUTO, WARNING_SOURCE_AUTO
from custom_components.lueftungsberater.location import EffectiveLocation, effective_location
from custom_components.lueftungsberater.national_warnings import _at_record, _swiss_record, _parse_rows, combine_warning_sources, fetch_civil_warnings
from custom_components.lueftungsberater.outside import LueftungsberaterOutsideCoordinator
from custom_components.lueftungsberater.providers import _automatic_warning_assessment

NOW = datetime(2026, 10, 2, 18, 0, tzinfo=timezone.utc)
TRACKER = 'device_tracker.wohnmobil'
LOCATION = EffectiveLocation(50.8, 6.03, None, 'DE', 'home', NOW)
SQUARE = {'type':'Polygon','coordinates':[[[6,50],[7,50],[7,51],[6,51],[6,50]]]}

@pytest.mark.parametrize('raw,limit,expected', [('50.48',90,50.8),('6.02',180,6+2/60),('-8.40',180,-8-40/60),('-0.30',180,-.5),('90.00',90,90),('180.00',180,180)])
def test_real_dwd_degrees_and_minutes(raw,limit,expected):
    assert ap._dwd_catalog_coordinate(raw,limit)==pytest.approx(expected)

@pytest.mark.parametrize('raw,limit',[('50.60',90),('50.798',90),('91.00',90),('180.01',180),('nan',90)])
def test_dwd_rejects_invalid_coordinates(raw,limit):
    with pytest.raises(ValueError): ap._dwd_catalog_coordinate(raw,limit)

def test_real_catalog_positions_and_nearest_station():
    catalog='''10505 ---- AACHEN-ORSBACH        50.48    6.02   231
10513 EDDK KOELN/BONN            50.52    7.10    91
01001 ENJA JAN MAYEN             70.56   -8.40    10'''
    ids=['10505','10513','01001']
    stations=ap._parse_dwd_station_index(catalog,''.join(f'<a href="{i}-BEOB.csv">x</a>' for i in ids),''.join(f'<a href="{i}/">x</a>' for i in ids))
    assert len(stations)==3
    assert stations[0].latitude==pytest.approx(50.8)
    assert stations[1].longitude==pytest.approx(7+10/60)
    assert stations[2].longitude==pytest.approx(-8-40/60)
    assert min(stations,key=lambda s:ap._distance_km(50.85,7.12,s.latitude,s.longitude)).station_id=='10513'

def cap(code='BE001',scheme='EMMA_ID',*,status='Actual',polygon='',expires=''):
    return f'''<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2"><identifier>id-1</identifier><status>{status}</status><scope>Public</scope><msgType>Alert</msgType><info><language>en-GB</language><event>Storm</event><severity>Severe</severity><instruction>Keep windows closed.</instruction>{f'<expires>{expires}</expires>' if expires else ''}<area><geocode><valueName>{scheme}</valueName><value>{code}</value></geocode>{f'<polygon>{polygon}</polygon>' if polygon else ''}</area></info></alert>'''

@pytest.mark.parametrize('code,scheme,lat,lon',[('BE001','EMMA_ID',50,5.5),('BE34','NUTS2',50,5.5),('NL015','EMMA_ID',52.1,5.1)])
def test_real_region_geometry_and_nuts_alias(code,scheme,lat,lon):
    assert ap._parse_cap_document(cap(code,scheme),lat,lon) is not None
    assert ap._parse_cap_document(cap(code,scheme),40,-10) is None

def test_unknown_region_is_unknown():
    with pytest.raises(ap.UnresolvedWarningArea): ap._parse_cap_document(cap('NEW999'),50,6)

def test_explicit_polygon_overrides_broader_region():
    doc=cap(polygon='50,6 50,7 51,7 51,6 50,6')
    assert ap._parse_cap_document(doc,50.5,6.5) is not None
    assert ap._parse_cap_document(doc,50,5.5) is None

@pytest.mark.parametrize('status',['Test','Exercise','Draft'])
def test_cap_probes_do_not_lock(status):
    assert ap._parse_cap_document(cap(status=status),50,5.5) is None

def test_expired_cap_is_not_active():
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        assert ap._parse_cap_document(cap(expires='2026-10-01T00:00:00Z'),50,5.5) is None

@pytest.mark.asyncio
async def test_failed_cap_is_unknown_and_retried(hass):
    feed='''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2"><entry><id>x</id><cap:geocode><cap:valueName>EMMA_ID</cap:valueName><cap:value>BE001</cap:value></cap:geocode><link type="application/cap+xml" href="https://feeds.meteoalarm.org/one.cap"/></entry></feed>'''
    state=ap.AutoProviderState(); loc=replace(LOCATION,latitude=50,longitude=5.5,country='BE')
    with patch.object(ap,'_get_text',AsyncMock(side_effect=[feed,RuntimeError('offline'),feed,cap()])) as get:
        one=await ap._fetch_meteoalarm_warnings(hass,object(),loc,'BE',state)
        two=await ap._fetch_meteoalarm_warnings(hass,object(),loc,'BE',state)
    assert not one.available
    assert two.available and len(two.warnings)==1
    assert get.await_count==4

@pytest.mark.asyncio
async def test_all_cap_links_are_processed_beyond_forty(hass):
    feed='<feed xmlns="http://www.w3.org/2005/Atom">'+''.join(f'<entry><id>x{i}</id><link type="application/cap+xml" href="https://feeds.meteoalarm.org/{i}.cap"/></entry>' for i in range(45))+'</feed>'
    docs=[cap(polygon='50,6 50,7 51,7 51,6 50,6').replace('id-1',f'id-{i}') for i in range(45)]
    with patch.object(ap,'_get_text',AsyncMock(side_effect=[feed]+docs)):
        result=await ap._fetch_meteoalarm_warnings(hass,object(),LOCATION,'BE',ap.AutoProviderState())
    assert result.available and len(result.warnings)==45

def swiss(**overrides):
    row={'identifier':'ch-1','nationWide':False,'testAlert':False,'technicalTestAlert':False,'title':{'title':'Rauch'},'description':{'description':'Rauchentwicklung'},'instructions':[{'text':'Fenster und Türen geschlossen halten.'}],'allClear':False,'areas':[{'polygons':[{'coordinates':[[50,6],[50,7],[51,7],[51,6],[50,6]],'excludes':[]}],'circles':[]}]}
    row.update(overrides);return row

def test_alertswiss_polygons_holes_circles_and_clear():
    assert _swiss_record(swiss(),LOCATION).category=='civil'
    assert _swiss_record(swiss(),replace(LOCATION,latitude=49)) is None
    row=swiss();row['areas'][0]['polygons'][0]['excludes']=[{'coordinates':[[50.7,6.02],[50.7,6.04],[50.9,6.04],[50.9,6.02],[50.7,6.02]]}]
    assert _swiss_record(row,LOCATION) is None
    circle=swiss(areas=[{'polygons':[],'circles':[{'centerPosition':[50.8,6.03],'radius':2}]}])
    assert _swiss_record(circle,replace(LOCATION,latitude=50.81)) is not None
    assert _swiss_record(circle,replace(LOCATION,latitude=51.8)) is None
    assert _swiss_record(swiss(nationWide=True,areas=[]),LOCATION) is not None
    assert _swiss_record(swiss(allClear=True),LOCATION).msg_type=='Cancel'

@pytest.mark.parametrize('key',['testAlert','technicalTestAlert'])
def test_swiss_probes_are_excluded(key):
    assert _swiss_record(swiss(**{key:True}),LOCATION) is None

def at(**overrides):
    row={'consolidation_identifier':'at-1','alert_level':'Emergency','title':'Rauch','info_description':'Fenster und Türen geschlossen halten.','geometries':[SQUARE],'begin_date':'2026-10-02T17:00:00Z','end_date':'2026-10-02T19:00:00Z'}
    row.update(overrides);return row

@pytest.mark.parametrize('geometries',[[SQUARE],str([SQUARE])])
def test_at_alert_shapes_and_active_period(geometries):
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        assert _at_record(at(geometries=geometries),LOCATION).category=='civil'
        assert _at_record(at(geometries=geometries),replace(LOCATION,latitude=49)) is None
        assert _at_record(at(end_date='2026-10-02T17:00:00Z'),LOCATION) is None
        assert _at_record(at(begin_date='2026-10-02T19:00:00Z'),LOCATION) is None

@pytest.mark.parametrize('level',['Test','MonthlyTest','Exercise'])
def test_at_probes_are_excluded(level):
    assert _at_record(at(alert_level=level),LOCATION) is None

def test_malformed_national_areas_are_unknown():
    records,failures=_parse_rows([swiss(areas=[])],LOCATION,'CH')
    assert records==[] and failures==1
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        records,failures=_parse_rows([at(geometries="__import__('os').system('false')")],LOCATION,'AT')
    assert records==[] and failures==1

@pytest.mark.asyncio
async def test_stale_swiss_heartbeat_is_unavailable(hass):
    with patch('custom_components.lueftungsberater.national_warnings._get_json',AsyncMock(return_value={'heartbeatAgeInMillis':400_000,'alerts':[]})):
        with pytest.raises(ValueError): await fetch_civil_warnings(hass,object(),LOCATION,'CH')

@pytest.mark.asyncio
async def test_civil_warning_survives_weather_provider_outage(hass):
    warning=ap.AutoWarningRecord('ch','alertswiss_auto','civil',instruction='Fenster schließen.',evidence_at=NOW)
    civil=ap.AutoWarningData('alertswiss_auto',NOW,True,'CH',warnings=[warning])
    async def weather():raise RuntimeError('weather offline')
    with patch('custom_components.lueftungsberater.national_warnings.fetch_civil_warnings',AsyncMock(return_value=civil)):
        result=await combine_warning_sources(hass,object(),LOCATION,'CH',weather())
    assert not result.available and result.warnings==[warning]
    with patch('custom_components.lueftungsberater.providers.auto_warning_data',return_value=result),patch.object(ap.dt_util,'utcnow',return_value=NOW):
        assessment=_automatic_warning_assessment(hass,SimpleNamespace())
    assert assessment.official_close_instruction
    assert assessment.safety_source_key.endswith(':alertswiss_auto')
    assert assessment.provider_availability[assessment.safety_source_key]

def tracker_state(age=0,**attrs):
    return SimpleNamespace(state='not_home',attributes={'latitude':50.8,'longitude':6.03,**attrs},last_reported=NOW-timedelta(minutes=age),last_updated=NOW-timedelta(days=1))

def mobile_hass(state):
    return SimpleNamespace(states=SimpleNamespace(get=lambda _id:state),config=SimpleNamespace(latitude=1,longitude=2,country='DE'))

@pytest.mark.parametrize('age,available',[(0,True),(5,True),(6,False),(40,False),(-1,False)])
def test_gps_last_report_counts_identical_stationary_positions(age,available):
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        loc=effective_location(mobile_hass(tracker_state(age)),SimpleNamespace(data={CONF_LOCATION_TRACKER:TRACKER}))
    assert loc.available==available
    assert loc.updated_at==NOW-timedelta(minutes=age)
    assert loc.source==TRACKER and loc.country is None

def test_explicit_fix_time_prevents_republished_old_gps_becoming_fresh():
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        loc=effective_location(mobile_hass(tracker_state(gps_timestamp='2026-10-01T00:00:00Z')),SimpleNamespace(data={CONF_LOCATION_TRACKER:TRACKER}))
    assert not loc.available

def test_hold_expires_from_actual_fix_and_never_jumps_home():
    coordinator=object.__new__(LueftungsberaterOutsideCoordinator)
    coordinator.entry=SimpleNamespace(data={CONF_LOCATION_TRACKER:TRACKER});coordinator._last_valid_mobile_location=None
    with patch.object(ap.dt_util,'utcnow',return_value=NOW):
        coordinator.hass=mobile_hass(tracker_state(10));first=coordinator._candidate_location()
        assert first.available and first.latitude==50.8
        coordinator.hass=mobile_hass(tracker_state(31));expired=coordinator._candidate_location()
        assert not expired.available and expired.source==TRACKER
        coordinator.hass=mobile_hass(None)
        assert not coordinator._candidate_location().available

@pytest.mark.asyncio
async def test_lost_location_does_not_start_network_requests(hass):
    entry=SimpleNamespace(data={CONF_WARNING_SOURCE_MODE:WARNING_SOURCE_AUTO,CONF_WEATHER_SOURCE_MODE:WEATHER_SOURCE_AUTO},entry_id='gps')
    with patch.object(ap,'async_get_clientsession') as session:
        await ap.async_refresh_auto_providers(hass,entry,replace(LOCATION,available=False))
    session.assert_not_called()
    assert ap.auto_warning_data(hass,entry).error=='location_stale'
    assert not ap.auto_weather_available(hass,entry)

@pytest.mark.asyncio
async def test_germany_neighbor_germany_resets_provider_caches(hass):
    entry=SimpleNamespace(data={CONF_WARNING_SOURCE_MODE:WARNING_SOURCE_AUTO,CONF_WEATHER_SOURCE_MODE:WEATHER_SOURCE_AUTO},entry_id='borders',title='Camper')
    seen=[]
    async def warning(_hass,_session,loc,country,state):
        seen.append(country)
        assert not state.meteoalarm_cache
        # NINA detail/GeoJSON cache is warning-revision keyed and intentionally
        # survives movement; only location-dependent regional resolution changes.
        if len(seen) > 1:
            assert state.nina_cache
        return ap.AutoWarningData('nina_auto' if country=='DE' else 'meteoalarm_auto',NOW,True,country,safety_source_key=ap._safety_location_key('warning',loc))
    async def weather(_session,loc,country,state):return ap.AutoWeatherData('test',NOW,country=country)
    with patch.object(ap,'async_get_clientsession',return_value=object()),patch.object(ap,'_fetch_auto_weather',side_effect=weather),patch.object(ap,'_fetch_auto_warning',side_effect=warning):
        for country,lat,lon in [('DE',50.8,6.03),('BE',50,5.5),('DE',50.8,6.03)]:
            await ap.async_refresh_auto_providers(hass,entry,replace(LOCATION,latitude=lat,longitude=lon,country=country))
            state=ap._state(hass,entry);state.nina_cache['old']=(NOW,{},{});state.meteoalarm_cache['old']=(NOW,'old')
    assert seen==['DE','BE','DE']

@pytest.mark.parametrize('lat,lon,expected',[(50.8,6.03,'DE'),(50,5.5,'BE'),(47.37,8.54,'CH'),(48.21,16.37,'AT'),(52.1,5.1,'NL'),(40.75,-73.99,'US'),(49.28,-123.12,'CA'),(45.81,15.98,'HR'),(46.05,14.5,'SI'),(43.7384,7.4246,'MC'),(0,-30,None)])
def test_coordinate_country_uses_boundaries_not_timezones(lat,lon,expected):
    from custom_components.lueftungsberater.warning_regions import coordinate_country
    assert coordinate_country(lat,lon)==expected

@pytest.mark.parametrize("polygon", ["", "nan,6 50,7 51,7 nan,6", "50,6 50,7 51,7"])
def test_malformed_explicit_footprint_is_unknown(polygon):
    document = cap(polygon="50,6 50,7 51,7 50,6").replace("50,6 50,7 51,7 50,6", polygon)
    with pytest.raises(ap.UnresolvedWarningArea):
        ap._parse_cap_document(document, 50, 5.5)

@pytest.mark.asyncio
async def test_nina_partial_outage_keeps_known_civil_source():
    responses = [[], [], RuntimeError("offline"), [], [], []]
    with patch.object(ap, "_get_json", AsyncMock(side_effect=responses)):
        data = await ap._fetch_nina_warnings(object(), LOCATION, ap.AutoProviderState())
    assert not data.available
    assert data.error == "nina_partial_failure"
    assert data.source_availability["nina_auto_mowas"]
    assert not data.source_availability["nina_auto_biwapp"]


def test_zone_can_be_used_as_effective_location_without_gps_freshness():
    zone = SimpleNamespace(
        state="0",
        attributes={"latitude": 50.75, "longitude": 7.05, "altitude": 70},
        last_reported=NOW - timedelta(days=5),
        last_updated=NOW - timedelta(days=5),
    )
    hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda entity_id: zone if entity_id == "zone.home" else None),
        config=SimpleNamespace(latitude=1, longitude=2, country="DE"),
    )
    with patch.object(ap.dt_util, "utcnow", return_value=NOW):
        loc = effective_location(hass, SimpleNamespace(data={CONF_LOCATION_TRACKER: "zone.home"}))
    assert loc.available and loc.position_valid
    assert loc.source == "zone.home"
    assert loc.latitude == 50.75 and loc.longitude == 7.05

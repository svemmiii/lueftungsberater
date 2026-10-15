"""COMPLETE(15): recorder data correctness, retries, and read-only history lookup."""
from __future__ import annotations
import asyncio
import time
import ast
from types import SimpleNamespace as NS
import math
import pytest
from test_v0114_complete2_pure import _extract, ROOT


async def _mock_confirm_history_save(hass, store, payload):
    await store.async_save(payload)

def support():
    tree=ast.parse((ROOT/'history_support.py').read_text())
    metric_node=next(n for n in tree.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=='HISTORY_METRICS')
    metrics=ast.literal_eval(metric_node.value)
    spec=_extract('history_support.py', {
        'finite_value','preferred_air_quality_variant','_air_quality_sample','current_unit','current_value','history_data','history_sensor_unique_id','async_enable_history',
        'allowed_metric','HISTORY_METRICS',
    }, {'math':math, 'time':time, 'DOMAIN':'lueftungsberater','SUBENTRY_TYPE_ROOM':'room', 'HISTORY_METRICS':metrics,
        'async_save_history_confirmed':_mock_confirm_history_save})
    return spec


def test_surface_humidity_is_derived_not_temperature_source():
    h=support()
    assert h['HISTORY_METRICS']['surface_humidity'][3] is None
    s=NS(values={'surface_relative_humidity':78.5, 'surface_temperature':17.8},result=None)
    assert h['current_value'](s,'surface_humidity')==78.5
    attrs={'source_surface_temperature':'sensor.surface_temp','surface_relative_humidity':78.5}
    assert h['allowed_metric'](attrs,'surface_humidity')
    attrs.pop('surface_relative_humidity')
    assert not h['allowed_metric'](attrs,'surface_humidity')
    attrs.update(source_humidity_inside='sensor.rh',source_temperature_inside='sensor.airtemp')
    assert h['allowed_metric'](attrs,'surface_humidity')  # temporary outage must not hide configuration


def test_failed_history_store_save_can_retry_and_register():
    h=support()
    calls=[]
    class Store:
        attempts=0
        async def async_save(self, value):
            self.attempts+=1
            if self.attempts==1:
                raise OSError('temporary recorder storage error')
            calls.append(dict(value))
    store=Store()
    hass=NS(data={'lueftungsberater':{
        'history_stores':{'one':store},
        'history_adders':{'one':lambda room,keys:calls.append((room,keys))},
    }})
    sub=NS(subentry_id='r',subentry_type='room')
    entry=NS(entry_id='one',subentries={'r':sub})
    fn=h['async_enable_history']
    with pytest.raises(OSError):asyncio.run(fn(hass,entry,'r',['surface_humidity']))
    assert h['history_data'](hass,'one')=={}
    assert asyncio.run(fn(hass,entry,'r',['surface_humidity']))==['surface_humidity']
    assert store.attempts==2
    assert ('r',['surface_humidity']) in calls


def test_read_only_room_lookup_uses_registry_without_admin_permission():
    # Extract callback body without HA's websocket decorators, which cannot
    # run in this isolated environment. Test its actual room/entity lookup.
    tree=ast.parse((ROOT/'api.py').read_text())
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='websocket_history_room_info')
    node.decorator_list=[]
    resolver=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_resolve_history_room')
    mod=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),resolver,node],type_ignores=[])
    lookup={('sensor','lueftungsberater','r_history_surface_humidity_v2'):'sensor.history_surface_humidity'}
    lookup[('sensor','lueftungsberater','r_advisor')]='sensor.advisor'
    deliberately_disabled = {'value': False}
    registry=NS(async_get=lambda entity:(
                    NS(unique_id='r_advisor',platform='lueftungsberater',config_entry_id='one')
                    if entity=='sensor.advisor' else
                    NS(disabled_by='user') if entity=='sensor.history_surface_humidity' and deliberately_disabled['value'] else None),
                async_get_entity_id=lambda *args:lookup.get(args))
    # Neither the advisor nor the enabled helper currently has a HA state;
    # the registry and Recorder history must remain independently resolvable.
    states={}
    room=NS(subentry_id='r',subentry_type='room',title='Room')
    entry=NS(entry_id='one',subentries={'r':room})
    hass=NS(states=NS(get=states.get),data={},config_entries=NS(async_entries=lambda domain:[entry]))
    result=[]
    conn=NS(send_result=lambda id,value:result.append(value),send_error=lambda *args:pytest.fail('unexpected error'))
    scope={
        'DOMAIN':'lueftungsberater','ENTRY_KIND_LOCAL':'local','SUBENTRY_TYPE_ROOM':'room',
        'entry_kind':lambda entry:'local',
        'er':NS(async_get=lambda hass:registry),
        'history_data':lambda h,id:{'r':['surface_humidity','decision']},
        'history_sensor_unique_id':lambda room,metric:f'{room}_history_{metric}_v2' if metric=='surface_humidity' else f'{room}_history_{metric}',
    }
    # Local import in callback is replaced for an isolated test namespace.
    # Actual function code is retained, including the entity resolution logic.
    node.body=[item for item in node.body if not (isinstance(item,ast.ImportFrom) and item.module=='history_support')]
    exec(compile(ast.fix_missing_locations(mod),'api.py','exec'),scope)
    scope['websocket_history_room_info'](hass,conn,{'id':42,'entity':'sensor.advisor'})
    assert result==[{'room':'r','room_name':'Room','enabled':['surface_humidity','decision'],
                     'helpers':{'surface_humidity':'sensor.history_surface_humidity'}, 'disabled':[],
                     'failed':[], 'failure_reason':None, 'history_store_readonly':False}]
    deliberately_disabled['value'] = True
    scope['websocket_history_room_info'](hass,conn,{'id':43,'entity':'sensor.advisor'})
    assert result[-1]['disabled'] == ['surface_humidity']
    hass.data={'lueftungsberater':{'history_repair_failed':{'one':{'rooms':{'r':['decision']},'reason':'helpers_missing'}}}}
    scope['websocket_history_room_info'](hass,conn,{'id':44,'entity':'sensor.advisor'})
    assert result[-1]['failed']==['decision']
    assert result[-1]['failure_reason']=='helpers_missing'
    lookup[('sensor','lueftungsberater','r_history_decision')] = 'sensor.history_decision'
    states['sensor.history_decision'] = NS(state='open_now', attributes={})
    scope['websocket_history_room_info'](hass,conn,{'id':45,'entity':'sensor.advisor'})
    assert result[-1]['failed'] == []
    assert result[-1]['failure_reason'] is None
    assert 'one' not in hass.data['lueftungsberater']['history_repair_failed']


def test_history_source_resolution_prefers_config_over_stale_advisor_and_keeps_co2():
    """Exercise the actual room resolver without a Home Assistant runtime."""
    tree = ast.parse((ROOT/'api.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == '_history_room_attributes')
    node.decorator_list = []
    node.body = [n for n in node.body if not isinstance(n, ast.ImportFrom)]
    namespace = {
        'DOMAIN': 'lueftungsberater',
        'history_data': lambda h, eid: {'r': ['decision']},
        'er': NS(async_get=lambda _: NS(async_get_entity_id=lambda *args: None)),
        'station_for_room': lambda entry, room: None,
        'station_is_direct': lambda station: False,
        'direct_station_entities': lambda hass, station: None,
        'uses_auto_weather': lambda entry: False,
        'get_outside_coordinator': lambda hass, entry: None,
        'HISTORY_METRICS': support()['HISTORY_METRICS'],
        'finite_value': support()['finite_value'],
        'preferred_air_quality_variant': support()['preferred_air_quality_variant'],
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'api.py', 'exec'), namespace)
    old = NS(state='unavailable', attributes={
        'has_co2': False,
        'source_co2': 'sensor.old_co2',
        'source_temperature_inside': 'sensor.old_temp',
    })
    states = NS(get=lambda _: old)
    room = NS(subentry_id='r', data={'co2_entity': 'sensor.new_co2',
                                   'indoor_temperature': 'sensor.new_temp'})
    entry = NS(entry_id='e', data={}, subentries={})
    attrs = namespace['_history_room_attributes'](NS(states=states), entry,
                                                   room, 'sensor.advisor')
    assert attrs['has_co2'] is True
    assert attrs['source_co2'] == 'sensor.new_co2'
    assert attrs['source_temperature_inside'] == 'sensor.new_temp'

    # Removing the configured CO2 source must not resurrect a stale one.
    room.data = {}
    attrs = namespace['_history_room_attributes'](NS(states=states), entry,
                                                   room, 'sensor.advisor')
    assert attrs['has_co2'] is False
    assert 'source_co2' not in attrs
    namespace['history_data'] = lambda h, eid: {'r': ['co2_in']}
    attrs = namespace['_history_room_attributes'](NS(states=states), entry,
                                                   room, 'sensor.advisor')
    assert attrs['has_co2'] is True  # Previously activated helper is retained.


def test_auto_weather_history_keeps_recording_option_without_advisor_or_fake_source():
    tree = ast.parse((ROOT/'api.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == '_history_room_attributes')
    node.decorator_list = []
    node.body = [n for n in node.body if not isinstance(n, ast.ImportFrom)]
    namespace = {
        'DOMAIN': 'lueftungsberater',
        'history_data': lambda h, eid: {},
        'er': NS(async_get=lambda _: NS(async_get_entity_id=lambda *args: None)),
        'station_for_room': lambda entry, room: None,
        'station_is_direct': lambda station: False,
        'direct_station_entities': lambda hass, station: None,
        'uses_auto_weather': lambda entry: True,
        'HISTORY_METRICS': support()['HISTORY_METRICS'],
        'finite_value': support()['finite_value'],
        'preferred_air_quality_variant': support()['preferred_air_quality_variant'],
        'get_outside_coordinator': lambda hass, entry: NS(data=NS(weather=NS(
            source_temperature='dwd:station_123', source_humidity='sensor.outdoor_rh',
            source_wind='auto_weather:coord', source_gust=None,
            wind_speed_kmh=None, wind_gust_kmh=None,
        ))),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'api.py', 'exec'), namespace)
    hass = NS(states=NS(get=lambda _: None))
    entry = NS(entry_id='e', data={}, subentries={})
    room = NS(subentry_id='r', data={})
    attrs = namespace['_history_room_attributes'](hass, entry, room, 'sensor.advisor')
    assert attrs['_history_auto_available'] == {'temp_out', 'humidity_out'}
    assert attrs.get('source_temperature_outside') is None  # DWD marker is not a HA entity.
    assert attrs.get('source_humidity_outside') == 'sensor.outdoor_rh'  # Effective HA source supports Recorder.
    h = support()
    assert h['allowed_metric'](attrs, 'temp_out')
    assert h['allowed_metric'](attrs, 'humidity_out')
    assert not h['allowed_metric'](attrs, 'wind_out')


def test_removed_outdoor_sources_and_stale_live_co2_do_not_reappear():
    """Old advisor scalars/source IDs are not authoritative after a config edit."""
    tree = ast.parse((ROOT/'api.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == '_history_room_attributes')
    node.decorator_list = []
    node.body = [n for n in node.body if not isinstance(n, ast.ImportFrom)]
    ns = {
        'DOMAIN': 'lueftungsberater',
        'history_data': lambda h, eid: {},
        'HISTORY_METRICS': support()['HISTORY_METRICS'],
        'finite_value': support()['finite_value'],
        'preferred_air_quality_variant': support()['preferred_air_quality_variant'],
        'er': NS(async_get=lambda _: NS(async_get_entity_id=lambda *args: None)),
        'station_for_room': lambda entry, room: None,
        'station_is_direct': lambda station: False,
        'direct_station_entities': lambda hass, station: None,
        'uses_auto_weather': lambda entry: True,
        'get_outside_coordinator': lambda hass, entry: NS(data=NS(weather=NS(
            source_temperature='dwd:former', source_humidity='auto_weather:coord',
            source_wind='auto_weather:wind', source_gust=None,
            outdoor_co2_source=None, air_quality_sources={},
            air_quality_values={}, wind_speed_kmh=None, wind_gust_kmh=None,
        ))),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'api.py', 'exec'), ns)
    old = NS(state='open_now', attributes={
        'has_co2': True, 'co2_ppm': 1800,
        'source_co2': 'sensor.old_co2',
        'source_temperature_outside': 'sensor.removed_outside',
        'source_humidity_outside': 'sensor.removed_humidity',
        'source_outdoor_co2': 'sensor.removed_co2',
        'source_wind_outside': 'sensor.removed_wind',
        'outdoor_co2_ppm': 550,
    })
    room = NS(subentry_id='room', data={})
    entry = NS(entry_id='instance', data={'weather_source_mode': 'auto'}, subentries={})
    attrs = ns['_history_room_attributes'](NS(states=NS(get=lambda _: old)), entry,
                                          room, 'sensor.advisor')
    for source in ('source_temperature_outside', 'source_humidity_outside',
                   'source_outdoor_co2', 'source_wind_outside', 'source_co2'):
        assert source not in attrs, source
    assert attrs['has_co2'] is False
    assert not support()['allowed_metric'](attrs, 'co2_out')
    assert not support()['allowed_metric'](attrs, 'co2_in')
    assert not support()['allowed_metric'](attrs, 'wind_out')
    assert support()['allowed_metric'](attrs, 'temp_out')  # auto helper may be enabled


def test_history_helper_records_coordinator_value_not_old_advisor_sensor():
    """A room sensor change must never append the previous sensor's value."""
    tree = ast.parse((ROOT/'sensor.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'HistoryRoomSensor')
    native = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'native_value')
    unit = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                and n.name == 'native_unit_of_measurement')
    for node in (native, unit):
        node.decorator_list = []
    ns = {'current_value': support()['current_value'],
          'current_unit': support()['current_unit'],
          'HISTORY_METRICS': support()['HISTORY_METRICS']}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[native,unit], type_ignores=[])),
                 'sensor.py', 'exec'), ns)
    snapshot = NS(values={'co2_ppm': 700, 'temperature_inside': 20}, result=None)
    old_advisor = {'source_co2': 'sensor.old_co2'}
    fake_hass = NS(states=NS(get=lambda id: NS(state='1800') if id=='sensor.old_co2' else None))
    helper = NS(metric='co2_in', snapshot=snapshot, hass=fake_hass,
                advisor_attrs=old_advisor)
    assert ns['native_value'](helper) == 700
    assert ns['native_unit_of_measurement'](helper) == 'ppm'
    helper.snapshot = None
    assert ns['native_value'](helper) is None


def test_air_quality_history_preserves_actual_variant_and_unit():
    h = support()
    snapshot = NS(
        values={
            'indoor_air_quality_values': {'voc_index': 151, 'no2_parts': 35},
            'indoor_air_quality_units': {'voc_index': '', 'no2_parts': 'ppb'},
        },
        weather=NS(local_station_values={'voc_index': 80, 'no2_parts': 12},
                   air_quality_values={}),
        result=None,
    )
    assert h['current_value'](snapshot, 'voc_in') == 151
    assert h['current_unit'](snapshot, 'voc_in') == 'Index'
    assert h['current_value'](snapshot, 'no2_in') == 35
    assert h['current_unit'](snapshot, 'no2_in') == 'ppb'
    assert h['current_value'](snapshot, 'voc_out') == 80
    assert h['current_unit'](snapshot, 'voc_out') == 'Index'
    assert h['current_value'](snapshot, 'no2_out') == 12
    assert h['current_unit'](snapshot, 'no2_out') == 'ppb'
    snapshot.values['indoor_air_quality_values'] = {'voc': 23}
    assert h['current_value'](snapshot, 'voc_in') == 23
    assert h['current_unit'](snapshot, 'voc_in') == 'µg/m³'


def test_removed_indoor_quality_source_cannot_resurface_from_old_value():
    h = support()
    attrs = {
        '_history_inactive_metrics': {'pm25_in', 'voc_in', 'no2_in'},
        'indoor_air_quality_values': {'pm2_5': 80, 'voc': 150, 'no2': 24},
    }
    for metric in ('pm25_in', 'voc_in', 'no2_in'):
        assert not h['allowed_metric'](attrs, metric)
    attrs['_history_enabled'] = {'voc_in'}
    assert h['allowed_metric'](attrs, 'voc_in')  # Existing Recorder helper preserved.


def test_history_prefers_local_air_variant_before_regional_mass_and_keeps_unit():
    """The same local measurement and scale must reach opt-in Recorder sensors."""
    h = support()
    weather = NS(
        local_station_values={'voc_index': 160, 'no2_parts': 42, 'o3_parts': 60},
        air_quality_values={'voc': 15, 'no2': 20, 'o3': 55},
        air_quality_sources={
            'voc': 'sensor.regional_voc', 'voc_index': 'sensor.local_voc',
            'no2': 'sensor.regional_no2', 'no2_parts': 'sensor.local_no2',
            'o3': 'sensor.regional_o3', 'o3_parts': 'sensor.local_o3',
        },
    )
    snapshot = NS(weather=weather, values={}, result=None)
    assert (h['current_value'](snapshot,'voc_out'),h['current_unit'](snapshot,'voc_out')) == (160, 'Index')
    assert (h['current_value'](snapshot,'no2_out'),h['current_unit'](snapshot,'no2_out')) == (42, 'ppb')
    assert (h['current_value'](snapshot,'o3_out'),h['current_unit'](snapshot,'o3_out')) == (60, 'ppb')
    # An explicit sensor outage preserves the last established physical scale.
    tree=ast.parse((ROOT/'sensor.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='HistoryRoomSensor')
    unit=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='native_unit_of_measurement')
    unit.decorator_list=[]
    scope={'current_unit': h['current_unit']}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[unit],type_ignores=[])),'sensor.py','exec'),scope)
    helper=NS(metric='voc_out',snapshot=snapshot,_history_last_unit=None)
    assert scope['native_unit_of_measurement'](helper)=='Index'
    helper.snapshot=None
    assert scope['native_unit_of_measurement'](helper)=='Index'
    offline=NS(metric='no2_out',snapshot=None,_history_last_unit=None)
    assert scope['native_unit_of_measurement'](offline) is None  # never invent µg/m³


def test_history_metadata_uses_actual_helper_units_and_matching_bands():
    from test_v0114_history_pure import defs
    d=defs()
    d['configured_metrics'].__globals__['HISTORY_METRICS']=support()['HISTORY_METRICS']
    attrs={'_history_auto_available':{'voc_out','no2_out','o3_out'},
           '_history_metric_units':{'voc_out':'Index','no2_out':'ppb','o3_out':'ppb'}}
    metadata={metric['key']:metric for metric in d['configured_metrics'](attrs,{})}
    assert metadata['voc_out']['unit']=='Index'
    assert metadata['voc_out']['high'] is None
    assert metadata['no2_out']['unit']=='ppb'
    assert metadata['no2_out']['high']==16.0
    assert metadata['o3_out']['unit']=='ppb'
    assert metadata['o3_out']['high']==36.0
    # Without a live source or helper scale the backend must not guess mass.
    attrs['_history_metric_units']={}
    unknown={m['key']:m for m in d['configured_metrics'](attrs,{})}
    for key in ('voc_out','no2_out','o3_out'):
        assert unknown[key]['unit']==''
        assert unknown[key]['high'] is None


def test_auto_history_source_is_the_local_variant_not_regional_provider():
    tree=ast.parse((ROOT/'api.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
              and n.name=='_history_room_attributes')
    node.decorator_list=[]
    node.body=[n for n in node.body if not isinstance(n,ast.ImportFrom)]
    weather=NS(
        air_quality_values={'voc':15,'no2':20,'o3':55},
        local_station_values={'voc_index':160,'no2_parts':42,'o3_parts':60},
        air_quality_sources={
            'voc':'sensor.provider_voc','voc_index':'sensor.local_voc',
            'no2':'sensor.provider_no2','no2_parts':'sensor.local_no2',
            'o3':'sensor.provider_o3','o3_parts':'sensor.local_o3',
        },source_temperature=None,source_humidity=None,source_wind=None,
        source_gust=None,outdoor_co2_source=None,wind_speed_kmh=None,wind_gust_kmh=None,
    )
    ns={
        'DOMAIN':'lueftungsberater',
        'history_data':lambda hass,entry_id:{},
        'HISTORY_METRICS':support()['HISTORY_METRICS'],
        'finite_value':support()['finite_value'],
        'preferred_air_quality_variant': support()['preferred_air_quality_variant'],
        'er':NS(async_get=lambda _:NS(async_get_entity_id=lambda *args:None)),
        'station_for_room':lambda entry,room:None,
        'station_is_direct':lambda station:False,
        'direct_station_entities':lambda hass,station:None,
        'uses_auto_weather':lambda entry:True,
        'get_outside_coordinator':lambda hass,entry:NS(data=NS(weather=weather)),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
                 'api.py','exec'),ns)
    entry=NS(entry_id='e',data={},subentries={})
    room=NS(subentry_id='r',data={})
    attrs=ns['_history_room_attributes'](NS(states=NS(get=lambda _:None)),entry,room,'sensor.advisor')
    assert attrs['source_voc_outside']=='sensor.local_voc'
    assert attrs['source_no2_outside']=='sensor.local_no2'
    assert attrs['source_o3_outside']=='sensor.local_o3'


def test_websocket_history_metrics_passes_real_snapshot_scale_to_chart():
    """Coordinator -> WebSocket -> plotted metadata, not a default µg/m³."""
    from test_v0114_history_pure import defs
    d=defs()
    d['configured_metrics'].__globals__['HISTORY_METRICS']=support()['HISTORY_METRICS']
    tree=ast.parse((ROOT/'api.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
              and n.name=='websocket_history_metrics')
    node.decorator_list=[]
    node.body=[n for n in node.body if not isinstance(n,ast.ImportFrom)]
    weather=NS(local_station_values={'voc_index':151,'no2_parts':35},
               air_quality_values={'voc':15,'no2':20})
    snapshot=NS(weather=weather,values={},result=None)
    room=NS(subentry_id='r')
    entry=NS(entry_id='e')
    attrs={'_history_auto_available':{'voc_out','no2_out'}}
    registry=NS(async_get_entity_id=lambda *args:None)
    scope={
        '_resolve_history_room':lambda hass,entity:(entry,room),
        '_history_room_attributes':lambda *args:dict(attrs),
        'get_room_coordinator':lambda *args:NS(data=snapshot),
        'current_unit':support()['current_unit'],
        'history_sensor_unique_id':lambda r,m:f'{r}_history_{m}',
        'history_data':lambda *args:{},
        'configured_metrics':d['configured_metrics'],
        'er':NS(async_get=lambda hass:registry),
        'DOMAIN':'lueftungsberater',
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
                 'api.py','exec'),scope)
    responses=[]
    connection=NS(send_result=lambda id,data:responses.append(data))
    hass=NS(states=NS(get=lambda _:None))
    scope['websocket_history_metrics'](hass,connection,{'id':2,'entity':'sensor.wohnzimmer'})
    result={m['key']:m for m in responses[-1]}
    assert result['voc_out']['unit']=='Index' and result['voc_out']['high'] is None
    assert result['no2_out']['unit']=='ppb' and result['no2_out']['high']==16
    # After an outage, use the last registered helper's persisted unit.
    snapshot=None
    attrs={'_history_enabled':{'voc_out'}}
    scope['history_data']=lambda *args:{'r':['voc_out']}
    registry.async_get_entity_id=lambda *args:'sensor.voc_history'
    hass.states.get=lambda _:NS(attributes={'unit_of_measurement':'Index'})
    scope['websocket_history_metrics'](hass,connection,{'id':3,'entity':'sensor.wohnzimmer'})
    assert next(m for m in responses[-1] if m['key']=='voc_out')['unit']=='Index'


def test_provider_real_local_gas_payload_reaches_history_with_source_and_unit():
    """Use the real provider functions: local ppb gases live in air_quality_values."""
    from dataclasses import dataclass
    from test_v0114_complete2_pure import _extract

    states = {
        'sensor.local_no2': NS(state='42', attributes={'unit_of_measurement':'ppb'}),
        'sensor.local_o3': NS(state='60', attributes={'unit_of_measurement':'ppb'}),
        'sensor.local_voc': NS(state='35', attributes={'unit_of_measurement':'ppb'}),
    }
    hass=NS(states=NS(get=states.get))
    settings={'outdoor_no2':'sensor.local_no2','outdoor_o3':'sensor.local_o3',
              'outdoor_voc':'sensor.local_voc'}
    entry=NS(data={'manual_outdoor':settings})
    raw=_extract('air_sensors.py',
                 {'AirReading','_normalized_unit','_device_class','pollutant_reading'},
                 {'dataclass':dataclass,'PHYSICAL_MASS_UNITS':{'µg/m3','ug/m3','mg/m3'},
                  'PHYSICAL_PART_UNITS':{'ppm','ppb'},'RAW_DEVICE_CLASSES':
                  {'volatile_organic_compounds','volatile_organic_compounds_parts','nitrogen_dioxide','ozone'},
                  'state_number':lambda ha,id,**kwargs:NS(value=float(ha.states.get(id).state),
                       unit=ha.states.get(id).attributes.get('unit_of_measurement'))})
    consts={f'CONF_OUTDOOR_{name}':f'outdoor_{slug}' for name,slug in
            [('PM25','pm25'),('PM10','pm10'),('VOC','voc'),('NO2','no2'),('O3','o3')]}
    cfg=lambda entry,key:entry.data.get('manual_outdoor',{}).get(key)
    provider=_extract('providers.py',{'_local_station_air_quality','_apply_local_air_quality'},
                      {**consts,'_manual_override':cfg,
                       'pollutant_reading':raw['pollutant_reading'],
                       'concentration_ugm3':lambda ha,id:NS(value=None),
                       'classify_absolute':lambda kind,val:'moderate',
                       'worst_quality':lambda classes:('moderate','no2_parts',42),
                       '_air_quality_class':lambda kind,val:'moderate',
                       'AIR_QUALITY_RANK':{'unknown':-1,'moderate':2}})
    assessment=NS(source_entities=set(),air_quality_sources={
        'no2':'sensor.regional_no2','o3':'sensor.regional_o3','voc':'sensor.regional_voc'},
        air_quality_values={'no2':20,'o3':55,'voc':15},
        local_station_values={},local_air_quality_keys=set(),air_quality_variant_units={},
        air_quality_index='moderate',air_quality_pollutant='no2',air_quality_value=20,
        air_quality_unit='µg/m³',air_quality_measurement_type='mass')
    local_payload=provider['_local_station_air_quality'](hass,entry)
    assert local_payload[3]=={'no2_parts':42,'o3_parts':60}
    assert local_payload[4]=={'voc_parts':35}
    provider['_apply_local_air_quality'](hass,entry,assessment)
    assert {'no2_parts','o3_parts','voc_parts'} <= assessment.local_air_quality_keys
    assert all(assessment.air_quality_variant_units[k]=='ppb' for k in ('no2_parts','o3_parts','voc_parts'))
    for pollutant, raw_value in [('no2',42),('o3',60),('voc',35)]:
        snapshot=NS(weather=assessment,values={},result=None)
        assert (support()['current_value'](snapshot,pollutant+'_out'),
                support()['current_unit'](snapshot,pollutant+'_out'))==(raw_value,'ppb')
    # The room-history WebSocket resolver must choose those same physical
    # local sensors, not nearby/regional mass sensors with a different scale.
    node=next(n for n in ast.parse((ROOT/'api.py').read_text()).body
              if isinstance(n,ast.FunctionDef) and n.name=='_history_room_attributes')
    node.decorator_list=[]
    node.body=[n for n in node.body if not isinstance(n,ast.ImportFrom)]
    h=support()
    env={
        'DOMAIN':'lueftungsberater','history_data':lambda *args:{},
        'HISTORY_METRICS':h['HISTORY_METRICS'],'finite_value':h['finite_value'],
        'preferred_air_quality_variant':h['preferred_air_quality_variant'],
        'er':NS(async_get=lambda _:NS(async_get_entity_id=lambda *args:None)),
        'station_for_room':lambda *args:None,
        'station_is_direct':lambda *args:False,
        'direct_station_entities':lambda *args:None,
        'uses_auto_weather':lambda entry:True,
        'get_outside_coordinator':lambda *args:NS(data=NS(weather=assessment)),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
                 'api.py','exec'),env)
    attrs=env['_history_room_attributes'](NS(states=NS(get=lambda _:None)),
        NS(entry_id='e',data={'manual_outdoor':settings},subentries={}),
        NS(subentry_id='r',data={}), 'sensor.room')
    assert attrs['source_no2_outside']=='sensor.local_no2'
    assert attrs['source_o3_outside']=='sensor.local_o3'
    assert attrs['source_voc_outside']=='sensor.local_voc'


def test_voc_parts_unit_does_not_depend_on_currently_worst_pollutant():
    h=support()
    weather=NS(air_quality_values={'voc_parts':35,'no2_parts':70},
               local_station_values={},local_air_quality_keys={'voc_parts','no2_parts'},
               air_quality_variant_units={'voc_parts':'ppb','no2_parts':'ppb'},
               air_quality_pollutant='no2_parts',air_quality_unit='ppb')
    snapshot=NS(weather=weather,values={},result=None)
    assert h['current_value'](snapshot,'voc_out')==35
    assert h['current_unit'](snapshot,'voc_out')=='ppb'
    assert h['current_value'](snapshot,'no2_out')==70

@pytest.mark.asyncio
async def test_complete34_history_admin_retry_and_readonly_store_protocol():
    """Exercise actual admin websocket function, not a frontend-only stub."""
    tree = ast.parse((ROOT / 'api.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                and n.name == 'websocket_history_enable')
    node.decorator_list = []
    node.body = [n for n in node.body if not isinstance(n, ast.ImportFrom)]
    module = ast.Module(body=[node], type_ignores=[])
    room = NS(subentry_id='r')
    entry = NS(entry_id='one')
    invoked = []
    async def enable(*args):
        invoked.append(('enable', args[-1]))
        return ['decision']
    data = {'lueftungsberater': {'history_retry_adders': {'one': lambda: invoked.append(('retry',))}}}
    scope = {
        'DOMAIN': 'lueftungsberater', '_resolve_history_room': lambda h, entity: (entry, room),
        '_history_room_attributes': lambda *a: {}, 'HISTORY_METRICS': {},
        'allowed_metric': lambda *a: False, 'async_enable_history': enable,
        '_LOGGER': NS(exception=lambda *args: None),
    }
    exec(compile(ast.fix_missing_locations(module), 'api.py', 'exec'), scope)
    results = []
    conn = NS(send_error=lambda *args: results.append(('error', args)),
              send_result=lambda *args: results.append(('result', args)))
    hass = NS(data=data)
    await scope['websocket_history_enable'](hass, conn, {'id': 1, 'entity': 'sensor.r',
                                                   'metrics': ['decision'], 'retry': True})
    assert invoked == [('enable', ['decision']), ('retry',)]
    assert results[-1][0] == 'result'
    data['lueftungsberater']['history_load_errors'] = {'one': True}
    await scope['websocket_history_enable'](hass, conn, {'id': 2, 'entity': 'sensor.r',
                                                   'metrics': ['decision'], 'retry': True})
    assert results[-1] == ('error', (2, 'history_store_readonly',
                                    'History preferences are damaged or unreadable'))
    assert len(invoked) == 2


@pytest.mark.asyncio
async def test_complete34_optional_recorder_index_read_failure_keeps_original():
    """An unreadable optional index cannot unload already created room entities."""
    tree = ast.parse((ROOT / 'recorder_maintenance.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                and n.name == 'async_refresh_recorder_entity_index')
    node.decorator_list = []
    fake = NS(async_get=lambda _: NS(), async_entries_for_config_entry=lambda *_: [])
    events = []
    class Store:
        async def async_load(self):
            raise OSError('broken index')
        async def async_save(self, _):
            events.append('written')
    scope = {'er': fake, '_selected_entries': lambda x: x, '_index_store': lambda *a: Store(),
             '_LOGGER': NS(warning=lambda *args, **kwargs: events.append('warning'))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'recorder_maintenance.py', 'exec'), scope)
    await scope['async_refresh_recorder_entity_index'](NS(), NS(entry_id='one'))
    assert events == ['warning']


@pytest.mark.asyncio
async def test_complete34_optional_air_quality_cleanup_read_failure_preserves_store():
    """Orphaned room cleanup still completes despite an unreadable AQ Store."""
    tree = ast.parse((ROOT / 'storage_cleanup.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                and n.name == 'async_cleanup_orphaned_room_stores')
    node.decorator_list = []
    events = []
    class Store:
        def __init__(self, hass, version, key): self.key=key
        async def async_load(self): raise OSError('broken air quality store')
        async def async_remove(self): events.append(('removed', self.key))
        async def async_save(self, data): events.append(('saved', self.key))
    async def names(_): return ['lueftungsberater.air_quality.one', 'lueftungsberater.co2.one.old']
    scope = {
        'Store': Store, '_storage_names': names, 'STORAGE_VERSION': 1,
        'DOMAIN': 'lueftungsberater', 'SUBENTRY_TYPE_ROOM': 'room',
        '_ROOM_STORE_KINDS': ('airing', 'co2', 'decision', 'mold'),
        '_room_store_prefix': lambda entry, kind: f'lueftungsberater.{kind}.{entry}.',
        '_entry_store_key': lambda entry, kind: f'lueftungsberater.{kind}.{entry}',
        '_LOGGER': NS(warning=lambda *args, **kwargs: events.append(('warning', args[0]))),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'storage_cleanup.py', 'exec'), scope)
    result = await scope['async_cleanup_orphaned_room_stores'](
        NS(), NS(entry_id='one', subentries={}))
    assert result == {'lueftungsberater.co2.one.old'}
    assert any(kind == 'warning' for kind, _ in events)
    assert not any(kind == 'saved' for kind, _ in events)


@pytest.mark.asyncio
async def test_complete34_esphome_topology_task_cancelled_on_unload():
    """A running topology push may not outlive its old config entry."""
    tree = ast.parse((ROOT / 'hardware_provisioning.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == 'async_watch_master_participant_service')
    node.decorator_list = []
    import asyncio
    started = asyncio.Event()
    callbacks = []
    cancelled = []
    tasks = []
    async def sync(h, e):
        started.set()
        await asyncio.Event().wait()
    class Entry:
        def async_on_unload(self, fn): callbacks.append(fn)
        def async_create_background_task(self, hass, coro, name):
            task = asyncio.create_task(coro)
            tasks.append(task)
            return task
    class Bus:
        def async_listen(self, name, handler):
            self.handler = handler
            return lambda: cancelled.append('unsub')
    bus = Bus()
    scope = {'async_sync_master_participant_lists': sync, 'callback': lambda f: f,
             'ATTR_DOMAIN': 'domain', 'ATTR_SERVICE': 'service',
             'EVENT_SERVICE_REGISTERED': 'service_registered',
             'SERVICE_APPLY_PARTICIPANTS': 'apply_participants', 'DOMAIN': 'lueftungsberater',
             'asyncio': asyncio}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'hardware_provisioning.py', 'exec'), scope)
    entry = Entry()
    scope['async_watch_master_participant_service'](NS(bus=bus), entry)
    bus.handler(NS(data={'domain': 'esphome', 'service': 'room_apply_participants'}))
    await started.wait()
    assert len(tasks) == 1 and not tasks[0].done()
    callbacks[0]()
    await asyncio.sleep(0)
    assert cancelled == ['unsub'] and tasks[0].cancelled()
    bus.handler(NS(data={'domain': 'esphome', 'service': 'room_apply_participants'}))
    assert len(tasks) == 1


@pytest.fixture(autouse=True)
def _isolate_home_assistant_registry(monkeypatch):
    """Pure SimpleNamespace fixtures must never reach a real HA registry."""
    try:
        from homeassistant.helpers import entity_registry as entity_registry
    except ImportError:
        return
    registry = NS(
        async_get_entity_id=lambda *args: None,
        async_get=lambda entity_id: None,
    )
    monkeypatch.setattr(entity_registry, "async_get", lambda _hass: registry)


def test_complete35_air_quality_optional_store_corruption_and_shutdown():
    """A bad optional store must not fail setup, erase original data or unload."""
    from datetime import datetime, timezone
    from statistics import median
    import logging
    class FakeStore:
        payload = None
        fail_save = False
        saved = []
        def __init__(self, *args): pass
        async def async_load(self):
            if isinstance(self.payload, Exception):
                raise self.payload
            return self.payload
        async def async_save(self, value):
            if self.fail_save:
                raise OSError('write denied')
            self.saved.append(value)
        def async_delay_save(self, *args):
            self.saved.append('delayed')
    src=ast.parse((ROOT/'air_quality.py').read_text())
    cls=next(x for x in src.body if isinstance(x, ast.ClassDef) and x.name=='OutdoorAirQualityTracker')
    scope={'Store':FakeStore,'logging':logging,'_LOGGER':logging.getLogger('test35'),
           'DOMAIN':'lueftungsberater','STORAGE_VERSION':1,'dt_util':NS(utcnow=lambda:datetime.now(timezone.utc)),
           'median':median,'_finite':lambda x:float(x) if x is not None else None,
           '_parse_dt':lambda _:None,'clamp_not_future':lambda _,val:val,
           'AIR_QUALITY_RECENT_SAMPLES':15,'AIR_QUALITY_MAX_LOCATIONS':10,
           'DATA_AIR_QUALITY_TRACKERS':'trackers', 'math':math,
           'AIR_QUALITY_SAMPLE_MIN_INTERVAL':1,'AIR_QUALITY_BASELINE_ALPHA':0.1,
           'AIR_QUALITY_HISTORY_MIN_SAMPLES':2}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),
                 'air_quality.py','exec'),scope)
    Tracker=scope['OutdoorAirQualityTracker']
    entry=NS(entry_id='test',data={});hass=NS()
    async def run():
        for payload in (OSError('cannot read'), [1],
                        {'buckets':{'x':{'no2':{'baseline':12,'count':'broken'}}}}):
            FakeStore.payload=payload
            tracker=Tracker(hass,entry)
            await tracker.async_initialize()
            assert tracker._store_readonly
            assert not tracker._buckets
            before=len(FakeStore.saved)
            tracker._schedule_save()
            await tracker.async_shutdown()
            assert len(FakeStore.saved)==before
        FakeStore.payload={}
        tracker=Tracker(hass,entry)
        await tracker.async_initialize()
        assert not tracker._store_readonly
        FakeStore.fail_save=True
        await tracker.async_shutdown()  # must not fail an otherwise successful HA unload
    asyncio.run(run())


def test_complete35_legacy_cleanup_errors_are_optional():
    """A failed v0.7.2 purge is retried without blocking room setup."""
    import logging
    from pathlib import Path
    from tempfile import TemporaryDirectory
    class Store:
        async def async_remove(self): raise OSError('cannot remove old store')
        def __init__(self, *args): pass
    defs=_extract('history.py', {'_legacy_history_keys','async_cleanup_legacy_room_history'},
                  {'DOMAIN':'lueftungsberater','_LEGACY_PREFIX':'lueftungsberater.history.',
                   '_CLEANUP_FLAG':'cleaned','Store':Store,'STORAGE_VERSION':1,
                   '_LOGGER':logging.getLogger('test35'),'Path':Path})
    async def run():
        with TemporaryDirectory() as tmp:
            storage=Path(tmp)/'.storage';storage.mkdir()
            (storage/'lueftungsberater.history.old').write_text('old')
            hass=NS(data={},config=NS(path=lambda name:str(storage)),
                    config_entries=NS(async_entries=lambda _:[]),
                    async_add_executor_job=lambda fn:asyncio.to_thread(fn))
            await defs['async_cleanup_legacy_room_history'](hass)
            assert 'cleaned' not in hass.data['lueftungsberater']
            assert (storage/'lueftungsberater.history.old').exists()
    asyncio.run(run())


def test_complete35_periodic_esphome_tasks_stop_at_unload():
    """Both retry timers must cancel in-flight work before a fast reload."""
    from datetime import datetime, timezone, timedelta
    class Entry:
        def __init__(self, station):
            self.subentries={'id':station}
            self.unloads=[]
        def async_on_unload(self, callback):self.unloads.append(callback)
        def async_create_background_task(self,hass,coro,title):return asyncio.create_task(coro)
    async def run(name):
        started=asyncio.Event(); release=asyncio.Event(); committed=[]
        station=NS(subentry_id='id',subentry_type='station',title='Master',data={'pending':True})
        entry=Entry(station);timer=[]
        async def deferred(*args, **kwargs):
            started.set()
            await release.wait()
            committed.append('finished')
            return True
        scope={'ENTRY_KIND_LOCAL':'local','entry_kind':lambda entry:'local',
               '_has_master_stations':lambda entry:True,
               '_has_pending_stations':lambda entry:True,
               'station_subentries':lambda entry:[station],
               'station_role':lambda station:'master','HARDWARE_ROLE_MASTER':'master',
               'SUBENTRY_TYPE_STATION':'station',
               'CONF_HARDWARE_PROVISION_PENDING':'pending',
               'async_sync_master_participants':deferred,
               'async_provision_station':deferred,
               '_mark_station_provisioned':lambda *args:committed.append('marked'),
               'RETRY_BACKOFF_MINUTES':(1,2,5,10),'timedelta':timedelta,
               'async_track_time_interval':lambda hass,cb,period:timer.append(cb) or (lambda:timer.clear()),
               'dt_util':NS(utcnow=lambda:datetime.now(timezone.utc)),
               'DOMAIN':'lueftungsberater','asyncio':asyncio,
               'callback':lambda fn:fn,'_LOGGER':NS(warning=lambda *a,**k:None,debug=lambda *a,**k:None)}
        d=_extract('hardware_provisioning.py',{name},scope)
        d[name](NS(),entry)
        assert len(timer)==1
        timer[0](None)
        await asyncio.wait_for(started.wait(),1)
        for unload in entry.unloads:unload()
        assert not timer
        release.set()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert not committed
    async def main():
        await run('async_start_master_participant_retry')
        await run('async_start_pending_provision_retry')
    asyncio.run(main())


def test_complete35_metrics_require_helper_for_purged_internal_raw_entities():
    """Use actual websocket metadata selection rather than test-only booleans."""
    tree=ast.parse((ROOT/'api.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='websocket_history_metrics')
    node.decorator_list=[]
    node.body=[n for n in node.body if not isinstance(n,ast.ImportFrom)]
    entities={
        'sensor.internal_wind': NS(platform='lueftungsberater',unique_id='room_wind'),
        'sensor.internal_absolute': NS(platform='lueftungsberater',unique_id='room_absolute_humidity'),
        'sensor.external_co2': NS(platform='other',unique_id='co2'),
    }
    registry=NS(async_get=lambda entity_id:entities.get(entity_id),async_get_entity_id=lambda *args:None)
    def metrics(attrs,states):
        return [{'key':'wind_out','source':'sensor.internal_wind'},
                {'key':'absolute_in','source':'sensor.internal_absolute'},
                {'key':'co2_in','source':'sensor.external_co2'},
                {'key':'absolute_out','source':None}]
    scope={
        '_resolve_history_room':lambda *_:(NS(entry_id='entry'),NS(subentry_id='room')),
        '_history_room_attributes':lambda *args:{},'get_room_coordinator':lambda *a:NS(data=None),
        'current_unit':lambda *a:None,'history_sensor_unique_id':lambda r,k:f'{r}_history_{k}',
        'history_data':lambda *a:{},'configured_metrics':metrics,
        'er':NS(async_get=lambda h:registry),'DOMAIN':'lueftungsberater',
        '_RETAINED_HISTORY_SUFFIXES':('_advisor','_absolute_humidity','_last_airing','_critical_danger'),
        'RECORDER_RETENTION_DAYS':20,'HISTORY_RECORDER_RETENTION_DAYS':30,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
                 'api.py','exec'),scope)
    answers=[]
    scope['websocket_history_metrics'](NS(states=NS(get=lambda _:None)),
        NS(send_result=lambda _,data:answers.append(data)),{'id':1,'entity':'sensor.room'})
    values={item['key']:item['helper_required'] for item in answers[-1]}
    assert values=={'wind_out':True,'absolute_in':False,'co2_in':False,'absolute_out':True}
    assert {m['key']:m.get('raw_retention_days') for m in answers[-1]}['absolute_in']==20
    assert {m['key']:m.get('raw_retention_days') for m in answers[-1]}['co2_in'] is None

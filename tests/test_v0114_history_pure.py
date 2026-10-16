"""History-card activation, evaluation bands and retention, without a HA process."""
from __future__ import annotations
from types import SimpleNamespace
import math
import asyncio
import pytest
import time
from test_v0114_complete2_pure import _extract

PM = {"pm2_5": (5.,15.,30.,50.),"pm10": (9.,27.,54.,90.),"no2": (10.,30.,60.,100.),"o3": (24.,72.,144.,240.),"no2_parts": (5.,16.,32.,53.),"o3_parts": (12.,36.,72.,120.)}
SPEC = {"co2_in":("CO2", "ppm", "co2_ppm", "source_co2"),"co2_out":("CO2 out", "ppm", "outdoor_co2_ppm", "source_outdoor_co2"),"humidity_in":("Humidity", "%", "humidity_inside", "source_humidity_inside"),"pm25_out":("PM2.5", "µg/m³", "air_quality_values.pm2_5", "source_pm25_outside"),"no2_in":("NO2", "µg/m³", "indoor_air_quality_values.no2", "source_no2_inside"),"voc_in":("VOC", "µg/m³", "indoor_air_quality_values.voc", "source_voc_inside"),"temp_in":("Temp", "°C", "temperature_inside", "source_temperature_inside"),"o3_out":("O3", "µg/m³", "air_quality_values.o3", "source_o3_outside")}

async def _mock_confirm_history_save(hass, store, payload):
    """Pure tests supply in-memory Stores; durable confirmation is tested below."""
    await store.async_save(payload)


def defs():
    return _extract("history_support.py", {"finite_value","good_limits","allowed_metric","configured_metrics","history_data","history_sensor_unique_id","async_enable_history"}, {
        "time":time,"HISTORY_METRICS":SPEC,"PM_LIMITS":PM,"AIR_QUALITY_LIMITS":PM,
        "VOC_MASS_LIMITS":(300.,950.,3000.,10000.),"HCHO_LIMITS":(.03,.05,.1,.2),
        "DOMAIN":"lueftungsberater", "SUBENTRY_TYPE_ROOM":"room", "math":math,
        "async_save_history_confirmed":_mock_confirm_history_save,
        "CO2_GOOD_UPPER_PPM":1000.0,"RH_GOOD_LOWER":40.0,"RH_GOOD_UPPER":60.0,
        "temperature_need_limits":lambda *,has_window_contacts:(1.0,0.6) if has_window_contacts else (4.0,3.0),
    })

def test_evaluation_good_ranges_come_from_python_rules():
    d=defs(); good=d['good_limits']
    assert good('co2_in')['high'] == 1000
    assert good('humidity_in') == {'low':40,'high':60}
    assert good('pm25_out')['high'] == PM['pm2_5'][1]
    assert good('voc_in')['high'] == 950
    assert good('temp_in',target=23,has_windows=True) == {'low':22,'high':24}
    assert good('temp_in',target=23,has_windows=False) == {'low':19,'high':27}

def test_configured_sources_only_and_actual_units():
    d=defs()
    attrs={'source_co2':'sensor.co2','co2_ppm':1140,'has_co2':True,
           'source_pm25_outside':'sensor.pm','air_quality_values':{'pm2_5':20},
           'source_no2_inside':'sensor.no2','indoor_air_quality_values':{'no2':12},
           'source_voc_inside':'sensor.voc','source_humidity_inside':'sensor.rh',
           'source_temperature_inside':'sensor.temperature','target_temperature':23,
           'has_window_contacts':True}
    states={k:SimpleNamespace(attributes={'unit_of_measurement':v}) for k,v in {
        'sensor.pm':'mg/m³','sensor.no2':'ppb','sensor.voc':'VOC Index',
        'sensor.rh':'%','sensor.temperature':'°F'}.items()}
    data={x['key']:x for x in d['configured_metrics'](attrs,states)}
    assert data['pm25_out']['high'] == .015
    assert data['no2_in']['high'] == 16
    assert data['voc_in']['high'] is None
    assert data['temp_in']['low'] == 71.6
    assert 'co2_out' not in data
    assert d['allowed_metric'](attrs, 'whatever') is False

def test_opt_in_is_persistent_and_deduplicated():
    d=defs()
    saves=[]; calls=[]
    class Store:
        async def async_save(self,value):saves.append(dict(value))
    room=SimpleNamespace(subentry_id='room1',subentry_type='room')
    entry=SimpleNamespace(entry_id='e1',subentries={'room1':room})
    hass=SimpleNamespace(data={'lueftungsberater':{'history_stores':{'e1':Store()},'history_adders':{'e1':lambda r,keys:calls.append((r,keys))}}})
    fn=d['async_enable_history']
    assert asyncio.run(fn(hass,entry,'room1',['co2_out','decision'])) == ['co2_out','decision']
    assert asyncio.run(fn(hass,entry,'room1',['co2_out'])) == ['co2_out','decision']
    assert len(calls)==1 and len(saves)==1


def test_failed_sensor_add_retries_without_resaving_activation():
    """Durable preference alone must not make a failed sensor creation permanent."""
    d = defs()
    saves = []
    additions = []
    class Store:
        async def async_save(self, value):
            saves.append({key: list(vals) for key, vals in value.items()})
    def add(room, keys):
        additions.append((room, list(keys)))
        if len(additions) == 1:
            raise RuntimeError('temporarily failed to create sensor')
        return list(keys)
    entry = SimpleNamespace(entry_id='one', subentries={
        'r': SimpleNamespace(subentry_id='r', subentry_type='room')
    })
    hass = SimpleNamespace(data={'lueftungsberater': {
        'history_stores': {'one': Store()}, 'history_adders': {'one': add}
    }})
    async def run():
        try:
            await d['async_enable_history'](hass, entry, 'r', ['co2_in'])
        except RuntimeError:
            pass
        else:
            assert False, 'failed platform registration should be reported'
        assert d['history_data'](hass, 'one')['r'] == ['co2_in']
        assert len(saves) == 1
        assert await d['async_enable_history'](hass, entry, 'r', ['co2_in']) == ['co2_in']
        # Already submitted successfully: another card must not submit it again.
        assert await d['async_enable_history'](hass, entry, 'r', ['co2_in']) == ['co2_in']
    asyncio.run(run())
    assert additions == [('r', ['co2_in']), ('r', ['co2_in'])]
    assert len(saves) == 1


def test_concurrent_history_opt_ins_preserve_rooms_and_only_register_once():
    """Two cards racing across rooms and metrics must not lose disk writes."""
    d = defs()
    saved = []
    additions = []
    class Store:
        async def async_save(self, value):
            # Deliberately yield inside the write; without a lock all calls
            # would capture the same pre-save dictionary and overwrite it.
            await asyncio.sleep(0)
            saved.append({key: list(vals) for key, vals in value.items()})
    def add(room, keys):
        additions.append((room, tuple(keys)))
        return keys
    entry = SimpleNamespace(entry_id='one', subentries={
        'a': SimpleNamespace(subentry_id='a', subentry_type='room'),
        'b': SimpleNamespace(subentry_id='b', subentry_type='room'),
    })
    hass = SimpleNamespace(data={'lueftungsberater': {
        'history_stores': {'one': Store()}, 'history_adders': {'one': add}
    }})
    async def run():
        await asyncio.gather(
            d['async_enable_history'](hass, entry, 'a', ['co2_in']),
            d['async_enable_history'](hass, entry, 'b', ['decision']),
            d['async_enable_history'](hass, entry, 'a', ['co2_in']),
            d['async_enable_history'](hass, entry, 'a', ['temp_in']),
        )
        assert await d['async_enable_history'](hass, entry, 'a', ['co2_in', 'temp_in']) == ['co2_in','temp_in']
    asyncio.run(run())
    assert saved[-1] == {'a': ['co2_in', 'temp_in'], 'b': ['decision']}
    assert d['history_data'](hass, 'one') == saved[-1]
    assert sorted(additions) == [('a', ('co2_in',)), ('a', ('temp_in',)), ('b', ('decision',))]
    assert len(saved) == 3


def test_deferred_history_registration_can_be_retried_after_adder_exists():
    """Setup race: durable opt-in precedes platform availability."""
    d = defs()
    events = []
    class Store:
        async def async_save(self, value):
            events.append(('save', value.copy()))
    entry = SimpleNamespace(entry_id='one', subentries={
        'a': SimpleNamespace(subentry_id='a', subentry_type='room')
    })
    hass = SimpleNamespace(data={'lueftungsberater': {'history_stores': {'one': Store()}}})
    async def run():
        await d['async_enable_history'](hass, entry, 'a', ['decision'])
        hass.data['lueftungsberater']['history_adders'] = {
            'one': lambda room, keys: events.append(('add', room, tuple(keys))) or keys
        }
        await d['async_enable_history'](hass, entry, 'a', ['decision'])
        await d['async_enable_history'](hass, entry, 'a', ['decision'])
    asyncio.run(run())
    assert [item for item in events if item[0] == 'add'] == [('add', 'a', ('decision',))]


def test_sensor_platform_initial_registration_and_retry_share_one_identity():
    """Run real sensor.async_setup_entry body with a failing HA entity adder."""
    from test_v0114_complete2_pure import _extract
    callbacks = []
    calls = []
    failures = {'co2_in': 1}
    def entity(*args):
        return SimpleNamespace(metric=None)
    def history_sensor(entry, room, coordinator, key):
        return SimpleNamespace(metric=key)
    def add_entities(items, *, config_subentry_id):
        keys = [item.metric for item in items if item.metric is not None]
        calls.append((config_subentry_id, keys))
        if 'co2_in' in keys and failures['co2_in']:
            failures['co2_in'] -= 1
            raise RuntimeError('temporary HA entity platform error')
    async def coordinator(hass, entry, room):
        return 'coordinator'
    d = defs()
    scope = _extract('sensor.py', {'async_setup_entry'}, {
        'DOMAIN': 'lueftungsberater', 'SUBENTRY_TYPE_STATION':'station',
        'SUBENTRY_TYPE_ROOM':'room', 'CONF_CO2':'co2', 'CONF_WINDOWS':'windows',
        'station_uses_hardware_hub': lambda sub: False,
        'station_for_room':lambda *args:None,
        'async_get_or_create_room_coordinator':coordinator,
        'history_data':d['history_data'], 'callback':lambda fn:fn, 'time':time,
        'async_call_later':lambda hass, seconds, callback:(lambda:None),
        'async_enable_history':d['async_enable_history'],
        'er':SimpleNamespace(async_get=lambda hass:SimpleNamespace(async_get_entity_id=lambda *args:None)),
        'RoomAbsoluteHumiditySensor':entity,
        'RoomOutdoorAbsoluteHumiditySensor':entity,
        'RoomAbsoluteHumidityDifferenceSensor':entity,
        'RoomAdvisorSensor':entity,
        'RoomCo2StatusSensor':entity,
        'HistoryRoomSensor':history_sensor,
    })
    room = SimpleNamespace(subentry_id='r', subentry_type='room', data={})
    entry = SimpleNamespace(entry_id='one', subentries={'r':room},
                            async_on_unload=callbacks.append)
    class Store:
        async def async_save(self, value):
            pass
    hass = SimpleNamespace(data={'lueftungsberater':{
        'history_enabled':{'one':{'r':['decision']}},
        'history_stores':{'one':Store()},
        'coordinators':{('one','r'):'coordinator'},
    }})
    async def run():
        await scope['async_setup_entry'](hass,entry,add_entities)
        assert calls == [('r',['decision'])]
        await d['async_enable_history'](hass,entry,'r',['decision'])
        assert len(calls) == 1, 'already loaded on platform must never be re-added'
        try:
            await d['async_enable_history'](hass,entry,'r',['co2_in'])
        except RuntimeError:
            pass
        else:
            assert False
        await d['async_enable_history'](hass,entry,'r',['co2_in'])
        await d['async_enable_history'](hass,entry,'r',['co2_in'])
    asyncio.run(run())
    assert calls == [('r',['decision']),('r',['co2_in']),('r',['co2_in'])]
    assert d['history_data'](hass,'one')['r'] == ['co2_in','decision']
    assert len(callbacks) == 1
    callbacks[0]()
    assert hass.data['lueftungsberater']['history_adders'] == {}


def test_submitted_history_entity_is_retried_if_registry_stays_missing(monkeypatch):
    """HA may accept async_add_entities, yet fail during subsequent registration."""
    import sys
    import types
    d = defs()
    d['history_sensor_unique_id'] = lambda room, metric: f'{room}_history_{metric}'
    clock = {'at': 100.0}
    d['time'] = SimpleNamespace(monotonic=lambda: clock['at'])
    registry_entries = set()
    live = {'yes': False, 'disabled': False}
    registry = SimpleNamespace(async_get_entity_id=lambda domain, platform, unique_id:
                               f'sensor.{unique_id}' if unique_id in registry_entries else None,
                               async_get=lambda id: SimpleNamespace(disabled_by='user' if live['disabled'] else None))
    fake_hass = types.ModuleType('homeassistant')
    fake_helpers = types.ModuleType('homeassistant.helpers')
    fake_registry = types.ModuleType('homeassistant.helpers.entity_registry')
    fake_registry.async_get = lambda h: registry
    fake_helpers.entity_registry = fake_registry
    fake_hass.helpers = fake_helpers
    for name, obj in [('homeassistant', fake_hass),
                      ('homeassistant.helpers', fake_helpers),
                      ('homeassistant.helpers.entity_registry', fake_registry)]:
        monkeypatch.setitem(sys.modules, name, obj)

    adds = []
    class Store:
        async def async_save(self, payload):
            pass
    entry = SimpleNamespace(entry_id='e',subentries={
        'r': SimpleNamespace(subentry_id='r',subentry_type='room')})
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: '700' if entity_id=='sensor.r_history_decision' and live['yes'] else None),data={'lueftungsberater':{
        'history_stores':{'e':Store()},
        'history_adders':{'e':lambda room,keys: adds.append(tuple(keys)) or keys}}})
    async def check():
        await d['async_enable_history'](hass,entry,'r',['decision'])
        assert adds==[('decision',)]
        registry_entries.add('r_history_decision')  # Registry row, but no live HA entity yet.
        clock['at']+=60
        await d['async_enable_history'](hass,entry,'r',['decision'])
        assert len(adds)==1  # HA is still registering; no duplicate.
        clock['at']+=31
        await d['async_enable_history'](hass,entry,'r',['decision'])
        assert adds==[('decision',),('decision',)]
        live['yes'] = True
        clock['at']+=200
        await d['async_enable_history'](hass,entry,'r',['decision'])
        assert len(adds)==2  # Once registered, never add again.
    asyncio.run(check())


def test_unreadable_history_store_cannot_block_setup_or_be_overwritten():
    """Optional history failure leaves the rooms functional and disk intact."""
    import logging
    from test_v0114_complete16_history_storage_pure import _functions
    class Store:
        fail = True
        saved = []
        def __init__(self, hass, version, key):
            self.key=key
        async def async_load(self):
            if Store.fail: raise OSError('history store read error')
            return {'r':['decision']}
        async def async_save(self, payload):
            Store.saved.append(payload)
    env = _functions('history_support.py', ('history_data','async_load_history'), {
        'async_save_history_confirmed':_mock_confirm_history_save,
        'Store':Store,'DOMAIN':'lueftungsberater','SUBENTRY_TYPE_ROOM':'room',
        'HISTORY_METRICS':SPEC,'_LOGGER':logging.getLogger('test.history'),
    })
    d = defs()
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id='e', subentries={
        'r':SimpleNamespace(subentry_id='r',subentry_type='room')})
    assert asyncio.run(env['async_load_history'](hass,entry))=={}
    assert 'e' in hass.data['lueftungsberater']['history_load_errors']
    try:
        asyncio.run(d['async_enable_history'](hass,entry,'r',['decision']))
    except RuntimeError as exc:
        assert 'unreadable' in str(exc)
    else:
        assert False, 'unsafe overwrite of unreadable Store'
    assert Store.saved==[]
    Store.fail=False
    assert asyncio.run(env['async_load_history'](hass,entry)) == {'r':['decision']}
    assert not hass.data['lueftungsberater']['history_load_errors']


def test_uninstall_cleans_only_own_history_store():
    """Uninstall removes opt-ins, not Recorder or another integration entry."""
    from test_v0114_complete16_history_storage_pure import _functions
    removed=[]
    names=['lueftungsberater.history_enabled.one','lueftungsberater.history_enabled.two',
           'lueftungsberater.air_quality.one','lueftungsberater.co2.one.r',
           'lueftungsberater.history_enabled.one.extra']
    class Store:
        def __init__(self,hass,version,name):self.name=name
        async def async_remove(self):removed.append(self.name)
    d=_functions('storage_cleanup.py',('_entry_store_key','_room_store_prefix','async_remove_entry_stores'),{
        'DOMAIN':'lueftungsberater','Store':Store,'STORAGE_VERSION':1,
        '_ENTRY_STORE_KINDS':('air_quality','history_enabled'),
        '_ROOM_STORE_KINDS':('airing','co2','decision','mold'),
        '_storage_names':lambda hass: asyncio.sleep(0,result=names),
    })
    result=asyncio.run(d['async_remove_entry_stores'](None,'one'))
    assert result==set(removed)=={'lueftungsberater.history_enabled.one',
                                 'lueftungsberater.air_quality.one',
                                 'lueftungsberater.co2.one.r'}


def test_history_store_with_invalid_json_root_is_protected_and_room_setup_continues():
    """A structurally corrupt Store must not be silently replaced by opt-ins."""
    from test_v0114_complete16_history_storage_pure import _functions
    saved = []
    class Store:
        def __init__(self, *args):
            pass
        async def async_load(self):
            return ['bad but readable']
        async def async_save(self, payload):
            saved.append(payload)
    errors = []
    env = _functions('history_support.py', ('history_data','async_load_history','history_sensor_unique_id','async_enable_history'), {
        'async_save_history_confirmed':_mock_confirm_history_save,
        'DOMAIN':'lueftungsberater','Store':Store,'SUBENTRY_TYPE_ROOM':'room',
        'HISTORY_METRICS':{'co2_in':()},'_LOGGER':SimpleNamespace(error=lambda *args: errors.append(args)),
    })
    hass=SimpleNamespace(data={})
    room=SimpleNamespace(subentry_id='r',subentry_type='room')
    entry=SimpleNamespace(entry_id='e',subentries={'r':room})
    async def run():
        assert await env['async_load_history'](hass,entry)=={}
        assert hass.data['lueftungsberater']['history_load_errors']['e']
        try:
            await env['async_enable_history'](hass,entry,'r',['co2_in'])
        except RuntimeError as err:
            assert 'unreadable' in str(err)
        else:
            assert False, 'Invalid JSON root must make opt-ins read only'
    asyncio.run(run())
    assert not saved and errors


def test_background_repair_after_delayed_registration_failure_without_card(monkeypatch):
    """Real sensor setup + timer + registry check, no websocket/card involved."""
    import sys
    from types import ModuleType
    from test_v0114_complete2_pure import _extract
    d=defs()
    now={'n':100.0}
    scheduled=[]; canceled=[]; created=[]; adds=[]; callbacks=[]
    entry=SimpleNamespace(entry_id='e',subentries={},async_on_unload=callbacks.append)
    room=SimpleNamespace(subentry_id='r',subentry_type='room',data={})
    entry.subentries['r']=room
    hass=SimpleNamespace(data={'lueftungsberater':{
        'history_enabled':{'e':{'r':['decision']}},'history_stores':{'e':SimpleNamespace()},
        'coordinators':{('e','r'):object()}}})
    class States:
        value = None
        def get(self, eid): return self.value
    hass.states=States()
    async def coordinator(*args): return object()
    def entity(*args): return SimpleNamespace(metric=None)
    def sensor(*args): return SimpleNamespace(metric=args[-1])
    def add_entities(items,*,config_subentry_id):
        adds.extend(x.metric for x in items if x.metric is not None)
    def timer(hass,delay,callback):
        assert delay>=90
        scheduled.append(callback)
        return lambda: canceled.append(callback)
    async def spawn(coro):
        await coro
    entry.async_create_background_task=lambda h,coro,name: (created.append(asyncio.create_task(coro)) or created[-1])
    registry_entries=set()
    registry=SimpleNamespace(
        async_get_entity_id=lambda domain, platform, uid: f'sensor.{uid}' if uid in registry_entries else None,
        async_get=lambda entity_id: SimpleNamespace(disabled_by=None),
    )
    module=ModuleType('homeassistant'); helpers=ModuleType('homeassistant.helpers')
    reg=ModuleType('homeassistant.helpers.entity_registry');reg.async_get=lambda h:registry
    helpers.entity_registry=reg;module.helpers=helpers
    for name,obj in [('homeassistant',module),('homeassistant.helpers',helpers),
                     ('homeassistant.helpers.entity_registry',reg)]:
        monkeypatch.setitem(sys.modules,name,obj)
    d['time']=SimpleNamespace(monotonic=lambda:now['n'])
    d['history_sensor_unique_id']=lambda room,key:f'{room}_history_{key}'
    scope = _extract('sensor.py',{'async_setup_entry'}, {
        'DOMAIN':'lueftungsberater','SUBENTRY_TYPE_STATION':'station','SUBENTRY_TYPE_ROOM':'room',
        'CONF_CO2':'co2','CONF_WINDOWS':'windows','station_uses_hardware_hub':lambda sub:False,
        'station_for_room':lambda *args:None,'async_get_or_create_room_coordinator':coordinator,
        'history_data':d['history_data'],'callback':lambda f:f,'time':d['time'],
        'RoomAbsoluteHumiditySensor':entity,'RoomOutdoorAbsoluteHumiditySensor':entity,
        'RoomAbsoluteHumidityDifferenceSensor':entity,'RoomAdvisorSensor':entity,
        'RoomCo2StatusSensor':entity,'HistoryRoomSensor':sensor,
        'async_call_later':timer,'async_enable_history':d['async_enable_history'],
        'er':SimpleNamespace(async_get=lambda h:registry),
        '_LOGGER':SimpleNamespace(exception=lambda *args:None),
        'history_sensor_unique_id':lambda room,key:f'{room}_history_{key}',
    })
    async def run():
        await scope['async_setup_entry'](hass,entry,add_entities)
        assert adds==['decision']
        assert len(scheduled)==1
        now['n']+=95
        scheduled.pop(0)(None)  # no frontend; HA one-shot timer fires
        await asyncio.gather(*created); created.clear()
        assert adds==['decision','decision'], adds
        assert len(scheduled)==1
        registry_entries.add('r_history_decision')
        hass.states.value='open_now'
        now['n']+=95
        scheduled.pop(0)(None)
        await asyncio.gather(*created); created.clear()
        assert len(adds)==2 and not scheduled, 'stop when helper exists'
        assert len(callbacks)==1
        callbacks[0]()
        assert hass.data['lueftungsberater']['history_adders']=={}
    asyncio.run(run())


def test_partly_damaged_history_store_remains_read_only_without_losing_good_rooms():
    """A JSON object with one broken room must never be overwritten on opt-in."""
    import logging
    from test_v0114_complete16_history_storage_pure import _functions
    original={'r_bad': {'damaged': ['decision']}, 'r_good': ['decision']}
    saves=[]
    class Store:
        async def async_load(self):
            return original
        async def async_save(self, payload):
            saves.append(payload)
        def __init__(self,*args): pass
    env=_functions('history_support.py', ('history_data','async_load_history','history_sensor_unique_id','async_enable_history'), {
        'async_save_history_confirmed':_mock_confirm_history_save,
        'DOMAIN':'lueftungsberater', 'Store':Store, 'SUBENTRY_TYPE_ROOM':'room',
        'HISTORY_METRICS':SPEC, 'time':time, '_LOGGER':logging.getLogger('history.storage.regression'),
    })
    entry=SimpleNamespace(entry_id='e',subentries={
        r:SimpleNamespace(subentry_id=r,subentry_type='room') for r in ('r_bad','r_good')})
    hass=SimpleNamespace(data={})
    async def run():
        assert await env['async_load_history'](hass,entry)=={'r_good':['decision']}
        assert hass.data['lueftungsberater']['history_load_errors']['e']
        try:
            await env['async_enable_history'](hass,entry,'r_good',['co2_in'])
        except RuntimeError as err:
            assert 'unreadable' in str(err)
        else:
            assert False, 'must not overwrite partly damaged Store'
        assert not saves
        assert original['r_bad']=={'damaged':['decision']}
        # A manually repaired Store should allow normal opt-ins after reload.
        original['r_bad']=['decision']
        assert await env['async_load_history'](hass,entry)=={'r_bad':['decision'],'r_good':['decision']}
        assert 'e' not in hass.data['lueftungsberater']['history_load_errors']
        assert await env['async_enable_history'](hass,entry,'r_good',['co2_in'])==['co2_in','decision']
    asyncio.run(run())
    assert saves and saves[-1]['r_bad']==['decision']


def test_history_background_registry_failures_retry_and_report_exhaustion(monkeypatch):
    """Two failed registry reads cannot kill a bounded repair sequence."""
    import sys
    import logging
    from types import ModuleType
    d=defs()
    scheduled=[]; created=[]; added=[]; callbacks=[]
    now={'n':500.}
    room=SimpleNamespace(subentry_id='r',subentry_type='room',data={})
    entry=SimpleNamespace(entry_id='e',subentries={'r':room},async_on_unload=callbacks.append)
    def add_task(hass,coro,name):
        task=asyncio.create_task(coro)
        created.append(task)
        return task
    entry.async_create_background_task=add_task
    hass=SimpleNamespace(data={'lueftungsberater':{
        'history_enabled':{'e':{'r':['decision']}},
        'history_stores':{'e':SimpleNamespace()},
        'coordinators':{('e','r'):object()},
    }},states=SimpleNamespace(get=lambda entity_id:None))
    errors={'remaining':2, 'count':0}
    def lookup(domain,platform,unique_id):
        errors['count']+=1
        if errors['remaining']:
            errors['remaining']-=1
            raise OSError('temporary registry failure')
        return None
    registry=SimpleNamespace(async_get_entity_id=lookup, async_get=lambda eid:None)
    home=ModuleType('homeassistant')
    helpers=ModuleType('homeassistant.helpers')
    reg=ModuleType('homeassistant.helpers.entity_registry')
    reg.async_get=lambda h:registry
    helpers.entity_registry=reg; home.helpers=helpers
    for name,obj in [('homeassistant',home),('homeassistant.helpers',helpers),
                     ('homeassistant.helpers.entity_registry',reg)]:
        monkeypatch.setitem(sys.modules,name,obj)
    d['time']=SimpleNamespace(monotonic=lambda:now['n'])
    d['history_sensor_unique_id']=lambda room,key:f'{room}_history_{key}'
    def timer(hass,delay,cb):
        assert delay>=90
        scheduled.append(cb)
        return lambda:None
    def sensor(*args): return SimpleNamespace(metric=args[-1])
    scope=_extract('sensor.py',{'async_setup_entry'}, {
        'DOMAIN':'lueftungsberater','SUBENTRY_TYPE_ROOM':'room',
        'SUBENTRY_TYPE_STATION':'station','CONF_CO2':'co2','CONF_WINDOWS':'windows',
        'station_uses_hardware_hub':lambda _:False, 'station_for_room':lambda *args:None,
        'async_get_or_create_room_coordinator':lambda *args:asyncio.sleep(0,result=object()),
        'history_data':d['history_data'],'callback':lambda f:f,'time':d['time'],
        'RoomAbsoluteHumiditySensor':lambda *args:SimpleNamespace(metric=None),
        'RoomOutdoorAbsoluteHumiditySensor':lambda *args:SimpleNamespace(metric=None),
        'RoomAbsoluteHumidityDifferenceSensor':lambda *args:SimpleNamespace(metric=None),
        'RoomAdvisorSensor':lambda *args:SimpleNamespace(metric=None),
        'RoomCo2StatusSensor':lambda *args:SimpleNamespace(metric=None),
        'HistoryRoomSensor':sensor,'async_call_later':timer,
        'async_enable_history':d['async_enable_history'],
        'er':SimpleNamespace(async_get=lambda h:registry),
        'history_sensor_unique_id':lambda room,key:f'{room}_history_{key}',
        '_LOGGER':logging.getLogger('history.repair.test'),
    })
    def add_entities(items,*,config_subentry_id):
        added.extend(x.metric for x in items if x.metric is not None)
    async def run():
        await scope['async_setup_entry'](hass,entry,add_entities)
        assert added==['decision']
        for round_number in range(3):
            assert len(scheduled)==1, (round_number,errors)
            now['n']+=95
            scheduled.pop(0)(None)
            await asyncio.gather(*created)
            created.clear()
        assert errors['remaining']==0 and errors['count']>=3
        assert added==['decision','decision']
        assert not scheduled
        status=hass.data['lueftungsberater']['history_repair_failed']['e']
        assert status['reason']=='helpers_missing' and status['rooms']=={'r':['decision']}
        assert len(callbacks)==1
        callbacks[0]()
        assert 'e' not in hass.data['lueftungsberater']['history_repair_failed']
    asyncio.run(run())


def test_history_repair_task_is_cancelled_on_unload_during_reconcile():
    """A running old entry must not continue registering helpers after reload."""
    import logging
    callbacks=[]; timers=[]; tasks=[]; gate=asyncio.Event(); started=asyncio.Event(); cancelled=asyncio.Event()
    room=SimpleNamespace(subentry_id='r',subentry_type='room',data={})
    entry=SimpleNamespace(entry_id='e',subentries={'r':room},async_on_unload=callbacks.append)
    def create_background_task(hass,coro,name):
        task=asyncio.create_task(coro)
        tasks.append(task)
        return task
    entry.async_create_background_task=create_background_task
    registry=SimpleNamespace(async_get_entity_id=lambda *args:None,async_get=lambda eid:None)
    hass=SimpleNamespace(data={'lueftungsberater':{
        'history_enabled':{'e':{'r':['decision']}}, 'coordinators':{('e','r'):object()},
    }}, states=SimpleNamespace(get=lambda eid:None))
    async def slow_enable(hass,entry,room,keys):
        started.set()
        try:
            await gate.wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise
    def timer(hass,delay,callback):
        timers.append(callback)
        return lambda:None
    scope=_extract('sensor.py',{'async_setup_entry'}, {
        'DOMAIN':'lueftungsberater','SUBENTRY_TYPE_ROOM':'room',
        'SUBENTRY_TYPE_STATION':'station','CONF_CO2':'co2','CONF_WINDOWS':'windows',
        'station_uses_hardware_hub':lambda _:False,'station_for_room':lambda *args:None,
        'async_get_or_create_room_coordinator':lambda *args:asyncio.sleep(0,result=object()),
        'history_data':lambda h,eid:h.data['lueftungsberater']['history_enabled'][eid],
        'callback':lambda f:f, 'time':time,
        'RoomAbsoluteHumiditySensor':lambda *args:SimpleNamespace(),
        'RoomOutdoorAbsoluteHumiditySensor':lambda *args:SimpleNamespace(),
        'RoomAbsoluteHumidityDifferenceSensor':lambda *args:SimpleNamespace(),
        'RoomAdvisorSensor':lambda *args:SimpleNamespace(),
        'RoomCo2StatusSensor':lambda *args:SimpleNamespace(),
        'HistoryRoomSensor':lambda *args:SimpleNamespace(),
        'async_call_later':timer,'async_enable_history':slow_enable,
        'er':SimpleNamespace(async_get=lambda h:registry),
        'history_sensor_unique_id':lambda room,key:f'{room}_history_{key}',
        '_LOGGER':logging.getLogger('history.repair.cancel.test'),
    })
    async def run():
        await scope['async_setup_entry'](hass,entry,lambda entities,config_subentry_id:None)
        assert len(timers)==1
        timers.pop(0)(None)
        await asyncio.wait_for(started.wait(),1)
        callbacks[0]()
        results=await asyncio.gather(*tasks,return_exceptions=True)
        assert cancelled.is_set()
        assert isinstance(results[0],asyncio.CancelledError)
        assert not timers and 'e' not in hass.data['lueftungsberater']['history_repair_failed']
        assert not hass.data['lueftungsberater']['history_adders']
    asyncio.run(run())


@pytest.fixture(autouse=True)
def _isolate_home_assistant_registry(monkeypatch):
    """Pure SimpleNamespace fixtures must never reach a real HA registry."""
    try:
        from homeassistant.helpers import entity_registry as entity_registry
    except ImportError:
        return
    registry = SimpleNamespace(
        async_get_entity_id=lambda *args: None,
        async_get=lambda entity_id: None,
    )
    monkeypatch.setattr(entity_registry, "async_get", lambda _hass: registry)


def test_v0116_outdoor_temperature_humidity_and_co2_do_not_inherit_indoor_good_limits():
    """No room-comfort limits on outdoor relative weather/model values."""
    good = defs()['good_limits']
    for key in ('temp_out', 'humidity_out', 'co2_out'):
        assert good(key, target=23, has_windows=True) == {'low': None, 'high': None}
        assert good(key, target=23, has_windows=False) == {'low': None, 'high': None}
    # The INDOOR limits are unchanged; no ventilation engine edit.
    assert good('temp_in', target=23, has_windows=True) == {'low': 22, 'high': 24}
    assert good('humidity_in') == {'low': 40, 'high': 60}
    assert good('co2_in') == {'low': None, 'high': 1000}

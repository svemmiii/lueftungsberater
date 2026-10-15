"""Persistent history across two restarts and multiple HA integration entries."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

from test_v0114_complete2_pure import ROOT

DOMAIN = "lueftungsberater"


async def _mock_confirm_history_save(hass, store, payload):
    await store.async_save(payload)

def _functions(filename, wanted, env):
    if filename == 'history_support.py':
        env.setdefault('async_save_history_confirmed', _mock_confirm_history_save)
    tree = ast.parse((ROOT / filename).read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted]
    assert {n.name for n in nodes} == set(wanted)
    mod = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod), filename, "exec"), env)
    return env


def test_two_restarts_preserve_opt_ins_for_two_entries(tmp_path):
    storage = tmp_path / ".storage"
    storage.mkdir()
    disk = {
        f"{DOMAIN}.history.first": {"r1": ["co2_out", "decision"]},
        f"{DOMAIN}.history.second": {"r2": ["surface_humidity", "decision"]},
        f"{DOMAIN}.history.orphan": {"unused": ["decision"]},
    }
    for key in disk:
        (storage / key).touch()

    class Store:
        def __init__(self, hass, version, key):
            self.key = key
        async def async_load(self):
            return disk.get(self.key)
        async def async_save(self, data):
            disk[self.key] = data
            (storage / self.key).touch()
        async def async_remove(self):
            disk.pop(self.key, None)
            (storage / self.key).unlink(missing_ok=True)

    env = _functions("history_support.py", ("history_data", "async_load_history"), {
        "Store": Store, "DOMAIN": DOMAIN, "SUBENTRY_TYPE_ROOM": "room", "HISTORY_METRICS": {"co2_out": (), "surface_humidity": ()},
    })
    cleaner = _functions("history.py", ("_legacy_history_keys", "async_cleanup_legacy_room_history"), {
        "Path": Path, "Store": Store, "DOMAIN": DOMAIN, "STORAGE_VERSION": 1,
        "_LEGACY_PREFIX": f"{DOMAIN}.history.", "_CLEANUP_FLAG": "legacy_room_history_cleaned",
    })
    entries = [NS(entry_id="first", subentries={"r1": NS(subentry_id="r1", subentry_type="room")}),
               NS(entry_id="second", subentries={"r2": NS(subentry_id="r2", subentry_type="room")})]
    for restart in range(3):
        hass = NS(data={}, config=NS(path=lambda key: str(storage)),
                  config_entries=NS(async_entries=lambda domain: entries),
                  async_add_executor_job=lambda func: asyncio.to_thread(func))
        async def load(entry):
            return await env["async_load_history"](hass, entry)
        assert asyncio.run(load(entries[0])) == {"r1": ["co2_out", "decision"]}
        asyncio.run(cleaner["async_cleanup_legacy_room_history"](hass))
        # While entry two is still unloaded, its old opt-in may not be purged.
        if restart == 0:
            assert f"{DOMAIN}.history.second" in disk
        assert asyncio.run(load(entries[1])) == {"r2": ["surface_humidity", "decision"]}
        assert f"{DOMAIN}.history_enabled.first" in disk
        assert f"{DOMAIN}.history_enabled.second" in disk
        assert f"{DOMAIN}.history.orphan" not in disk
        assert f"{DOMAIN}.history.first" not in disk
        assert f"{DOMAIN}.history.second" not in disk


def test_new_store_key_is_not_legacy_cleanup_target():
    env = _functions("history.py", ("_legacy_history_keys",), {"_LEGACY_PREFIX": f"{DOMAIN}.history."})
    assert env["_legacy_history_keys"]([f"{DOMAIN}.history_enabled.x",f"{DOMAIN}.history.x"], ["x"]) == []
    assert env["_legacy_history_keys"]([f"{DOMAIN}.history_enabled.x",f"{DOMAIN}.history.orphan"], ["x"]) == [f"{DOMAIN}.history.orphan"]


def test_history_helpers_get_thirty_day_target_without_changing_other_retention():
    import asyncio
    registry_rows=[NS(entity_id='sensor.room_advisor',unique_id='room_advisor',platform=DOMAIN),
                   NS(entity_id='sensor.room_history_co2_out',unique_id='room_history_co2_out',platform=DOMAIN),
                   NS(entity_id='sensor.room_other',unique_id='room_status',platform=DOMAIN)]
    calls=[]
    env=_functions('recorder_maintenance.py', ('async_purge_recorder_history',), {
        'DOMAIN':DOMAIN,
        '_RECORDER_DOMAIN':'recorder','_PURGE_SERVICE':'purge_entities',
        'DATA_RECORDER_RETENTION':'retention',
        'RECORDER_RETENTION_DAYS':20,'HISTORY_RECORDER_RETENTION_DAYS':30,
        'async_retry_orphaned_recorder_indexes':lambda h: asyncio.sleep(0),
        'er':NS(async_get=lambda h:'registry',async_entries_for_config_entry=lambda registry,id:registry_rows),
        '_partition_history':lambda rows:(['sensor.room_advisor','sensor.room_history_co2_out'],['sensor.room_other']),
        '_selected_entries':lambda rows:rows,
        '_async_purge_ids':lambda h,ids,*,keep_days: record(ids,keep_days),
    })
    async def record(ids,keep_days):
        calls.append((tuple(sorted(ids)),keep_days))
    hass=NS(services=NS(has_service=lambda domain,name:True),data={DOMAIN:{'retention':{'entry_ids':{'one'}}}})
    asyncio.run(env['async_purge_recorder_history'](hass))
    assert (('sensor.room_advisor',),20) in calls
    assert (('sensor.room_history_co2_out',),30) in calls
    assert (('sensor.room_other',),0) in calls


def test_reload_replaces_previous_opt_ins_and_ignores_unhashable_values():
    """Malformed opt-ins must not block the other rooms' first evaluation."""
    class Store:
        payload = {'room': ['decision', {'invalid': True}, 'co2_in', [], 'co2_in'],
                   'removed_room': ['decision']}
        def __init__(self, *args):
            pass
        async def async_load(self):
            return self.payload
    warnings=[]
    env = _functions('history_support.py', ('history_data', 'async_load_history'), {
        'Store': Store, 'DOMAIN': DOMAIN, 'SUBENTRY_TYPE_ROOM': 'room',
        'HISTORY_METRICS': {'co2_in': ()},
        '_LOGGER': NS(warning=lambda *args: warnings.append(args), error=lambda *args: warnings.append(args)),
    })
    hass = NS(data={})
    entry = NS(entry_id='e', subentries={'room': NS(subentry_id='room', subentry_type='room')})
    saved = asyncio.run(env['async_load_history'](hass,entry))
    assert saved == {'room': ['decision','co2_in']}
    assert warnings
    assert hass.data[DOMAIN]['history_load_errors']['e'] is True
    enabled = env['history_data'](hass,'e')
    enabled['room'].append('not_persisted')
    enabled['old_room'] = ['decision']
    Store.payload = {'room': ['decision']}
    saved = asyncio.run(env['async_load_history'](hass,entry))
    assert enabled == saved == {'room': ['decision']}
    assert 'e' not in hass.data[DOMAIN]['history_load_errors']
    Store.payload = {}
    assert asyncio.run(env['async_load_history'](hass,entry)) == {}
    assert enabled == {}


def _room_method(module, class_name, method_name, values):
    """Exercise production persistence methods without importing HA at test time."""
    tree = ast.parse((ROOT / module).read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == method_name)
    scope = dict(values)
    code = ast.Module(body=[ast.ImportFrom(module='__future__',
                          names=[ast.alias(name='annotations')], level=0), method], type_ignores=[])
    exec(compile(ast.fix_missing_locations(code), module, 'exec'), scope)
    return scope[method_name]


def test_complete37_optional_co2_store_corruption_never_blocks_live_readings_or_overwrites():
    from datetime import datetime, timezone
    class Store:
        def __init__(self, mode): self.mode, self.writes = mode, 0
        async def async_load(self):
            if self.mode == 'read_error': raise OSError('unreadable CO2 store')
            return [1]
        async def async_save(self, value): self.writes += 1
    now = datetime.now(timezone.utc)
    env = {'_LOGGER':NS(warning=lambda *args,**kwargs:None), 'dt_util': NS(utcnow=lambda:now),
           '_state_to_float':lambda state:float(state.state),
           'async_track_state_change_event':lambda *args:lambda:None}
    method = _room_method('co2.py','RoomCo2Tracker','async_initialize',env)
    for mode in ('invalid_root','read_error'):
        store=Store(mode)
        obj=NS(entity_id='sensor.co2', _store=store, _store_readonly=False,
               hass=NS(states=NS(get=lambda entity:NS(state='900'))),
               last_valid_value=None, last_valid_at=None, unavailable_since=None,
               _parse_dt=lambda value:None, _payload=lambda:{'state':'would_replace_original'},
               _async_state_changed=lambda *_args:None)
        asyncio.run(method(obj))
        assert obj._store_readonly is True
        assert obj.last_valid_value == 900  # live sensor, no fabricated history
        assert store.writes == 0


def test_complete37_optional_mold_storage_does_not_block_room_or_overwrite_bad_root():
    from datetime import datetime, timezone
    class Store:
        def __init__(self, broken):self.broken=broken;self.writes=0
        async def async_load(self):
            if self.broken == 'error': raise OSError('unreadable mold')
            return [1]
        async def async_save(self, data):self.writes+=1
    now=datetime.now(timezone.utc)
    env={'_LOGGER':NS(warning=lambda *args,**kwargs:None),'dt_util':NS(utcnow=lambda:now),'clamp_not_future':lambda n,v:v,
         '_parse_dt':lambda value:None}
    init=_room_method('mold.py','RoomMoldTracker','async_initialize',env)
    shutdown=_room_method('mold.py','RoomMoldTracker','async_shutdown',env)
    for mode in ('list','error'):
        store=Store(mode)
        obj=NS(_store=store,_store_readonly=False,critical_since=None,
               last_valid_at=None,intervals=[],_prune=lambda now:None)
        asyncio.run(init(obj))
        asyncio.run(shutdown(obj))
        assert obj._store_readonly and store.writes==0


def test_complete37_airing_restore_rejects_unreadable_context_and_keeps_original():
    from datetime import datetime, timezone
    from types import MethodType
    now=datetime.now(timezone.utc)
    class Store:
        writes=0
        async def async_load(self): return [1]
        async def async_save(self, value): self.writes+=1
    env={'_LOGGER':NS(warning=lambda *a,**kw:None),'dt_util':NS(utcnow=lambda:now),
         'clamp_not_future':lambda n,v:v,'_parse_dt':lambda value:None,
         'async_dispatcher_send':lambda *a:None,'tracker_signal':lambda a,b:'unused'}
    init=_room_method('airing.py','RoomAiringTracker','async_initialize',env)
    save=_room_method('airing.py','RoomAiringTracker','_async_save',env)
    stop=_room_method('airing.py','RoomAiringTracker','async_stop',env)
    tracker=NS(_store=Store(), _store_readonly=False, windows=(),entry=NS(entry_id='e'),
               subentry=NS(subentry_id='r'),hass=NS(), last_confirmed_airing=None,
               last_qualified_airing_seen_at=None,tracking_started_at=None,open_since=None,
               minimum_reached_at=None,_unknown_since=None,
               _unsub_state=None,_unsub_registry=None,
               _restore_window_identities=lambda stored:None,
               _restore_window_aliases=lambda stored:None,
               _repair_missing_windows_from_registry=lambda:None,
               _contact_state=lambda:(False,True), _sync_timers=lambda:None,
               _cancel_tick=lambda:None,_cancel_fallback=lambda:None,
               _cancel_minimum=lambda:None,_cancel_unknown_grace=lambda:None)
    async def drain():pass
    tracker._drain_save_tasks=drain
    tracker._async_save=MethodType(save,tracker)
    asyncio.run(init(tracker))
    assert tracker._active is True and tracker._store_readonly is True
    asyncio.run(stop(tracker))
    assert tracker._store.writes==0 and tracker._active is False


def test_complete37_decision_restore_rejects_corrupt_context_without_resurrecting_old_mode():
    from datetime import datetime, timezone
    now=datetime.now(timezone.utc)
    class Store:
        def __init__(self,value):self.value=value
        async def async_load(self):
            if self.value == 'error': raise OSError('unreadable decision context')
            return self.value
    env={'_LOGGER':NS(warning=lambda *a,**kw:None),'dt_util':NS(utcnow=lambda:now),
         '_parse_dt':lambda value:None}
    restore=_room_method('coordinator.py','LueftungsberaterRoomCoordinator','_restore_memory',env)
    for damaged in ([1],'error'):
        tracker=NS(_memory_store=Store(damaged),_memory_store_readonly=False,
                   _previous_mode=None,_previous_decision_need=None)
        asyncio.run(restore(tracker))
        assert tracker._memory_store_readonly is True
        assert tracker._previous_mode is None


def test_complete39_presentation_duration_keeps_room_good_consistent_without_engine_changes():
    """The HA advisor state remains actionable, but the room view has no duration."""
    functions = _functions('sensor.py', ('_display_duration_key',), {
        'DISPLAY_MODE_ROOM_AIR': 'room_air',
    })
    display_key = functions['_display_duration_key']
    assert display_key('room_air', 'room_good', '8_12') == 'not_needed'
    assert display_key('room_air', 'room_good', 'while_temperature_helps') == 'not_needed'
    # A room duration must describe a *visible* open/continue-ventilating
    # instruction, never closing, watching or waiting.  The original action
    # engine duration remains available separately for integrations.
    for recommendation in (
        'can_close', 'room_watch', 'room_good', 'close_now', 'better_close',
        'keep_closed', 'short_observation', 'wait', 'window_state_unknown',
        'unknown',
    ):
        assert display_key('room_air', recommendation, 'until_targets') == 'not_needed'
        assert display_key('room_air', recommendation, 'brief_observation') == 'not_needed'
    for recommendation in ('open_now', 'room_need', 'room_urgent', 'keep_open', 'room_keep_brief'):
        assert display_key('room_air', recommendation, '8_12') == '8_12'
        assert display_key('room_air', recommendation, 'brief_observation') == 'brief_observation'
    # Technical ventilation perspective is deliberately unchanged.
    assert display_key('ventilation', 'short_observation', 'brief_observation') == 'brief_observation'
    assert display_key('ventilation', 'keep_open', 'until_targets') == 'until_targets'
    assert display_key('ventilation', 'open_now', '8_12') == '8_12'
    assert display_key('room_air', 'keep_closed', 'not_needed') == 'not_needed'
    assert display_key('room_air', 'short_observation', '5_8') == 'not_needed'


def _mock_ha_registry_if_available():
    """Pure SimpleNamespace tests must not access the real HA entity registry."""
    from contextlib import nullcontext
    from unittest.mock import patch
    try:
        from homeassistant.helpers import entity_registry as registry
    except ImportError:
        return nullcontext()
    registry_dummy = NS(async_get_entity_id=lambda *_args: None)
    return patch.object(registry, 'async_get', return_value=registry_dummy)


def test_complete38_legacy_history_is_not_removed_after_silently_failed_write():
    """The real HA Store may swallow WriteError yet return from async_save."""
    from copy import deepcopy
    disk = {f'{DOMAIN}.history.one': {'room': ['co2_in', 'decision']}}
    failed = {f'{DOMAIN}.history_enabled.one'}
    removals = []

    class Store:
        def __init__(self, hass, version, key):
            self.key = key
            self._pending = None
        async def async_save(self, payload):
            self._pending = deepcopy(payload)
            if self.key not in failed:
                disk[self.key] = deepcopy(payload)
            # Deliberately swallow the failed write just as HA Store does.
        async def async_load(self):
            # A same-instance load could falsely return unsaved _pending!
            return deepcopy(self._pending if self._pending is not None else disk.get(self.key))
        async def async_remove(self):
            removals.append(self.key)
            disk.pop(self.key, None)

    import logging
    env = _functions('history_support.py',
        ('history_data', 'async_save_history_confirmed', 'async_load_history'), {
            'Store': Store, 'DOMAIN': DOMAIN, 'SUBENTRY_TYPE_ROOM': 'room',
            'HISTORY_METRICS': {'co2_in': ()}, '_LOGGER': logging.getLogger('complete38-test'),
            'time':__import__('time'),
        })
    # _functions default mock is overwritten by the extracted production helper.
    entry = NS(entry_id='one', subentries={'room': NS(subentry_id='room', subentry_type='room')})
    hass = NS(data={})
    assert asyncio.run(env['async_load_history'](hass, entry)) == {}
    assert disk[f'{DOMAIN}.history.one'] == {'room': ['co2_in', 'decision']}
    assert f'{DOMAIN}.history_enabled.one' not in disk
    assert removals == []
    assert hass.data[DOMAIN]['history_load_errors']['one'] is True

    # Fixing the underlying disk fault lets an ordinary reload retry migration.
    failed.clear()
    hass = NS(data={})
    assert asyncio.run(env['async_load_history'](hass, entry)) == {'room': ['co2_in', 'decision']}
    assert disk[f'{DOMAIN}.history_enabled.one'] == {'room': ['co2_in', 'decision']}
    assert f'{DOMAIN}.history.one' not in disk
    assert removals == [f'{DOMAIN}.history.one']
    assert 'one' not in hass.data[DOMAIN]['history_load_errors']


def test_complete38_uncommitted_history_opt_in_is_not_published_or_registered():
    """A swallowed WriteError must not acknowledge a WebSocket opt-in."""
    from copy import deepcopy
    import logging
    disk = {}
    failed = {f'{DOMAIN}.history_enabled.one'}
    registered = []

    class Store:
        def __init__(self, hass, version, key):
            self.key = key
            self._pending = None
        async def async_load(self):
            return deepcopy(self._pending if self._pending is not None else disk.get(self.key))
        async def async_save(self, payload):
            self._pending = deepcopy(payload)
            if self.key not in failed:
                disk[self.key] = deepcopy(payload)
        async def async_remove(self):
            disk.pop(self.key, None)

    env = _functions('history_support.py', ('history_data',
        'async_save_history_confirmed', 'async_load_history',
        'async_enable_history', 'history_sensor_unique_id'), {
            'Store': Store, 'DOMAIN': DOMAIN, 'SUBENTRY_TYPE_ROOM': 'room',
            'HISTORY_METRICS': {'co2_in': ()}, '_LOGGER': logging.getLogger('complete38-test'),
            'time':__import__('time'),
        })
    entry = NS(entry_id='one', subentries={'room': NS(subentry_id='room', subentry_type='room')})
    hass = NS(data={})

    async def run():
        assert await env['async_load_history'](hass, entry) == {}
        hass.data[DOMAIN].setdefault('history_adders', {})['one'] = (
            lambda room, keys: registered.append((room, tuple(keys))) or keys
        )
        import pytest
        with pytest.raises(RuntimeError, match='not durably saved'):
            await env['async_enable_history'](hass, entry, 'room', ['co2_in'])
        assert env['history_data'](hass, 'one') == {}
        assert registered == []
        assert f'{DOMAIN}.history_enabled.one' not in disk

        # After the transient fault, the same request must persist and publish.
        failed.clear()
        assert await env['async_enable_history'](hass, entry, 'room', ['co2_in']) == ['co2_in']
        assert registered == [('room', ('co2_in',))]
        assert disk[f'{DOMAIN}.history_enabled.one'] == {'room': ['co2_in']}

    with _mock_ha_registry_if_available():
        asyncio.run(run())
    new_hass = NS(data={})
    assert asyncio.run(env['async_load_history'](new_hass, entry)) == {'room': ['co2_in']}


def test_complete38_confirmed_parallel_history_opt_ins_preserve_disk():
    """The per-entry lock spans both save and read-after-write verification."""
    from copy import deepcopy
    import logging
    disk = {}
    class Store:
        def __init__(self, hass, version, key):
            self.key = key
            self._pending = None
        async def async_load(self):
            await asyncio.sleep(0)
            return deepcopy(self._pending if self._pending is not None else disk.get(self.key))
        async def async_save(self, payload):
            self._pending = deepcopy(payload)
            await asyncio.sleep(0)
            disk[self.key] = deepcopy(payload)
    env = _functions('history_support.py', ('history_data',
        'async_save_history_confirmed', 'async_enable_history', 'history_sensor_unique_id'), {
            'Store': Store, 'DOMAIN': DOMAIN, 'SUBENTRY_TYPE_ROOM': 'room',
            'HISTORY_METRICS': {'co2_in': (), 'temp_in': ()},
            'time':__import__('time'), '_LOGGER': logging.getLogger('complete38-test'),
        })
    entry = NS(entry_id='one', subentries={
        x: NS(subentry_id=x, subentry_type='room') for x in ('a', 'b')
    })
    hass = NS(data={DOMAIN: {'history_stores': {'one': Store(None, 1, f'{DOMAIN}.history_enabled.one')}}})
    async def run():
        await asyncio.gather(
            env['async_enable_history'](hass, entry, 'a', ['co2_in']),
            env['async_enable_history'](hass, entry, 'b', ['decision']),
            env['async_enable_history'](hass, entry, 'a', ['temp_in']),
        )
    with _mock_ha_registry_if_available():
        asyncio.run(run())
    assert disk[f'{DOMAIN}.history_enabled.one'] == {
        'a': ['co2_in', 'temp_in'], 'b': ['decision']
    }

"""Persistent history across two restarts and multiple HA integration entries."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

from test_v0114_complete2_pure import ROOT

DOMAIN = "lueftungsberater"


def _functions(filename, wanted, env):
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

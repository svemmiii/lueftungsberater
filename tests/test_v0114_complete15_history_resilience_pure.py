"""COMPLETE(15): recorder data correctness, retries, and read-only history lookup."""
from __future__ import annotations
import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import math
import pytest
from test_v0114_complete2_pure import _extract, ROOT


def support():
    tree=ast.parse((ROOT/'history_support.py').read_text())
    metric_node=next(n for n in tree.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=='HISTORY_METRICS')
    metrics=ast.literal_eval(metric_node.value)
    spec=_extract('history_support.py', {
        'finite_value','current_value','history_data','async_enable_history',
        'allowed_metric','HISTORY_METRICS',
    }, {'math':math, 'DOMAIN':'lueftungsberater','SUBENTRY_TYPE_ROOM':'room', 'HISTORY_METRICS':metrics})
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
    mod=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),node],type_ignores=[])
    lookup={('sensor','lueftungsberater','r_history_surface_humidity_v2'):'sensor.history_surface_humidity'}
    registry=NS(async_get=lambda entity:NS(unique_id='r_advisor',platform='lueftungsberater'),
                async_get_entity_id=lambda *args:lookup.get(args))
    states={'sensor.advisor':NS(attributes={'instance_id':'one'}),
            'sensor.history_surface_humidity':NS(attributes={})}
    room=NS(subentry_id='r',subentry_type='room')
    entry=NS(entry_id='one',subentries={'r':room})
    hass=NS(states=NS(get=states.get),config_entries=NS(async_get=lambda id:entry if id=='one' else None))
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
    assert result==[{'room':'r','enabled':['surface_humidity','decision'],
                     'helpers':{'surface_humidity':'sensor.history_surface_humidity'}}]

"""Standalone UI selector regression coverage for COMPLETE(4)."""
from __future__ import annotations
import ast
import math
import re
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).resolve().parents[1]/'custom_components'/'lueftungsberater'/'config_flow.py'

class FakeClass:
    PM25='pm25'; PM10='pm10'; VOLATILE_ORGANIC_COMPOUNDS='voc'; VOLATILE_ORGANIC_COMPOUNDS_PARTS='voc_parts'; NITROGEN_DIOXIDE='no2'; OZONE='o3'

class Config:
    def __init__(self, **kw): self.kwargs=kw

class Selector:
    def __init__(self, config): self.kwargs=config.kwargs

class State:
    def __init__(self, entity_id, state, device_class=None, unit=None, friendly_name=None):
        self.entity_id=entity_id
        self.state=state
        self.attributes={'device_class':device_class,'unit_of_measurement':unit,'friendly_name':friendly_name or entity_id}


def selector_functions():
    tree=ast.parse(SRC.read_text())
    items=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in {'_is_numeric_sensor_state','_air_sensor_selector'}]
    namespace={'HomeAssistant':object,'EntitySelector':Selector,'EntitySelectorConfig':Config,'SensorDeviceClass':FakeClass,'Any':object,'re':re,'math':math}
    exec(compile(ast.fix_missing_locations(ast.Module(body=items,type_ignores=[])),str(SRC),'exec'),namespace)
    return namespace


def test_numeric_state_requires_finite_value():
    valid=selector_functions()['_is_numeric_sensor_state']
    for value in ('1.5','-25','0',4,0.0):
        assert valid(value), value
    for value in ('nan','NaN','inf','-inf','Infinity',float('inf'),float('-inf'),'unavailable','unknown','garbage',None):
        assert not valid(value), value


def test_only_explicitly_named_finite_unitless_indexes():
    s=[State('sensor.voc_index','85'),State('sensor.sen55_voc_index','unknown'),State('sensor.voc_baseline','45'),
       State('sensor.voc_calibration','55'),State('sensor.voc_index_bad','inf'),State('sensor.voc_index_bad2','-inf'),
       State('sensor.no2_index','85'),State('sensor.no2_calibration','55'),State('sensor.no2_baseline','20'),
       State('sensor.no2_index_bad','inf'),State('sensor.no2_indeks','34'),
       State('sensor.voc_concentration','5',unit='ppb'),State('sensor.unrelated','10',device_class='voc')]
    fake_hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda domain:s))
    ns=selector_functions()
    voc=ns['_air_sensor_selector']('voc',fake_hass).kwargs['include_entities']
    no2=ns['_air_sensor_selector']('no2',fake_hass).kwargs['include_entities']
    for name in ('sensor.voc_index','sensor.sen55_voc_index','sensor.voc_concentration','sensor.unrelated'):
        assert name in voc,name
    for name in ('sensor.voc_baseline','sensor.voc_calibration','sensor.voc_index_bad','sensor.voc_index_bad2'):
        assert name not in voc,name
    for name in ('sensor.no2_index','sensor.no2_indeks'):
        assert name in no2,name
    for name in ('sensor.no2_calibration','sensor.no2_baseline','sensor.no2_index_bad'):
        assert name not in no2,name


def test_existing_filter_path_remains_for_non_index_pollutants():
    namespace=selector_functions()
    selector=namespace['_air_sensor_selector']('pm25')
    assert selector.kwargs['filter'][0]['device_class']==['pm25']
    assert selector.kwargs['filter'][1]['unit_of_measurement']==['µg/m³','ug/m3']

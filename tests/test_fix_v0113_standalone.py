"""Targeted fixed-bug regressions; no Home Assistant dependency."""
from __future__ import annotations
import ast
import math
import re
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).resolve().parents[1] / 'custom_components' / 'lueftungsberater'
spec = spec_from_file_location('test_fix_localization', SRC/'localization.py')
module = module_from_spec(spec); spec.loader.exec_module(module)


def test_dst_night_end_fallback():
    args = dict(start_time='2026-10-25T00:00:00+02:00',
                end_time='2026-10-25T05:00:00+01:00',
                requested_night_end='06:00', local_timezone='Europe/Berlin')
    assert not module._night_covers_requested_end(args)
    assert '05:00' not in module.night_advice_text('night_now', args, 'de')


def test_dst_night_end_spring():
    args = dict(start_time='2026-03-28T23:00:00+01:00',
                end_time='2026-03-29T06:00:00+02:00',
                requested_night_end='06:00', local_timezone='Europe/Berlin')
    assert module._night_covers_requested_end(args)
    assert '06:00' in module.night_advice_text('night_now', args, 'de')


def test_night_confirmed_co2_hint_only_when_allowed():
    args = dict(start_time='2026-10-08T22:00:00+02:00',
                end_time='2026-10-09T03:00:00+02:00',
                requested_night_end='06:00',local_timezone='Europe/Berlin',
                co2_minutes_to_2000=25,live_open_now=True)
    for lang in ('de','en','tr'):
        assert 'CO₂' in module.night_advice_text('night_short_only', args, lang)
        assert 'CO₂' not in module.night_advice_text('night_short_only', {**args,'live_open_now':False}, lang)


def test_index_sensor_filter_has_narrow_fallback():
    tree = ast.parse((SRC/'config_flow.py').read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'_air_sensor_selector','_is_numeric_sensor_state'}]
    source = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    class FakeClass:
        PM25='pm25';PM10='pm10';VOLATILE_ORGANIC_COMPOUNDS='voc';VOLATILE_ORGANIC_COMPOUNDS_PARTS='voc_parts'; NITROGEN_DIOXIDE='no2'; OZONE='o3'
    class FakeConfig:
        def __init__(self, **kwargs): self.kwargs = kwargs
    class FakeSelector:
        def __init__(self, conf): self.kwargs = conf.kwargs
    class State:
        def __init__(self,name,value,unit=None,dc=None):
            self.entity_id='sensor.'+name; self.state=value
            self.attributes={'friendly_name':name,'unit_of_measurement':unit,'device_class':dc}
    states = [State('sen55_voc_index', '128'), State('no2_index', '85'), State('unrelated_illuminance','300','lx'), State('correct_voc','unavailable','index')]
    fake_hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda domain:states))
    ns=dict(HomeAssistant=object,EntitySelector=FakeSelector,EntitySelectorConfig=FakeConfig,SensorDeviceClass=FakeClass, Any=object, re=re, math=math)
    exec(compile(source,'config_flow_subset.py','exec'),ns)
    voc = ns['_air_sensor_selector']('voc',fake_hass).kwargs['include_entities']
    no2 = ns['_air_sensor_selector']('no2',fake_hass).kwargs['include_entities']
    assert 'sensor.sen55_voc_index' in voc
    assert 'sensor.no2_index' in no2
    assert 'sensor.unrelated_illuminance' not in voc + no2


def test_sensor_passes_only_confirmed_short_term_co2_value():
    s=(SRC/'sensor.py').read_text()
    assert 'r.reason_args.get("co2_minutes_to_2000")' in s
    assert 'night_args["co2_minutes_to_2000"] = confirmed_co2_minutes' in s
    assert 'night_args["local_timezone"] = self.hass.config.time_zone' in s

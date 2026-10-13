"""History-card activation, evaluation bands and retention, without a HA process."""
from __future__ import annotations
from types import SimpleNamespace
import math
import asyncio
from test_v0114_complete2_pure import _extract

PM = {"pm2_5": (5.,15.,30.,50.),"pm10": (9.,27.,54.,90.),"no2": (10.,30.,60.,100.),"o3": (24.,72.,144.,240.),"no2_parts": (5.,16.,32.,53.),"o3_parts": (12.,36.,72.,120.)}
SPEC = {"co2_in":("CO2", "ppm", "co2_ppm", "source_co2"),"co2_out":("CO2 out", "ppm", "outdoor_co2_ppm", "source_outdoor_co2"),"humidity_in":("Humidity", "%", "humidity_inside", "source_humidity_inside"),"pm25_out":("PM2.5", "µg/m³", "air_quality_values.pm2_5", "source_pm25_outside"),"no2_in":("NO2", "µg/m³", "indoor_air_quality_values.no2", "source_no2_inside"),"voc_in":("VOC", "µg/m³", "indoor_air_quality_values.voc", "source_voc_inside"),"temp_in":("Temp", "°C", "temperature_inside", "source_temperature_inside"),"o3_out":("O3", "µg/m³", "air_quality_values.o3", "source_o3_outside")}

def defs():
    return _extract("history_support.py", {"finite_value","good_limits","allowed_metric","configured_metrics","history_data","async_enable_history"}, {
        "HISTORY_METRICS":SPEC,"PM_LIMITS":PM,"AIR_QUALITY_LIMITS":PM,
        "VOC_MASS_LIMITS":(300.,950.,3000.,10000.),"HCHO_LIMITS":(.03,.05,.1,.2),
        "DOMAIN":"lueftungsberater", "SUBENTRY_TYPE_ROOM":"room", "math":math,
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

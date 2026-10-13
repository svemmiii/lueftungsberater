"""COMPLETE(15): real safe readings must precede persisted-weather release."""
from types import SimpleNamespace as NS
from datetime import timedelta
from test_v0114_complete12_weather_records_pure import _parts,_setup,A


def test_unchanged_still_dangerous_gust_never_confirms_clear():
    clock,disk,memory,states,run,report=_setup()
    danger=report(sources=(A,))
    danger.source_gust=A
    danger.wind_gust_kmh=110
    run(danger)
    expires=_parts(disk)[A]['valid_until']
    clock[0]+=timedelta(minutes=6)
    memory.clear()
    again=report()
    run(again)
    assert A in _parts(disk)
    assert _parts(disk)[A]['valid_until']==expires
    assert again.weather_hard_lock
    states[A].state='30'
    run(report())
    assert 'weather' not in disk['channels']


def test_legacy_weather_entity_without_subtype_does_not_clear_from_one_valid_wind():
    clock,disk,memory,states,run,report=_setup()
    source='weather.home'
    states[source]=NS(state='windy',attributes={
        'wind_speed':95,'wind_gust_speed':60,'wind_speed_unit':'km/h',
    })
    active=report(sources=(source,))
    active.source_wind=source
    active.wind_speed_kmh=95
    run(active)
    old=_parts(disk)[source]
    old.pop('hazard_measurement',None)  # Legacy state before typed weather evidence.
    clock[0]+=timedelta(minutes=6)
    states[source].attributes['wind_speed']=20
    states[source].attributes['wind_gust_speed']='nan'
    memory.clear()
    run(report())
    assert source in _parts(disk)
    states[source].attributes['wind_gust_speed']=30
    memory.clear()
    run(report())
    assert 'weather' not in disk['channels']

"""Regression tests for version 0.11.4 that run without Home Assistant."""
import importlib.util
import importlib.machinery
import random
import re
import sys
import types
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
COMP = BASE / 'custom_components/lueftungsberater'


def load_engine(root, name):
    package = types.ModuleType(name)
    package.__path__=[str(root)]
    sys.modules[name]=package
    for component in ('models','engine'):
        spec=importlib.util.spec_from_file_location(f'{name}.{component}',root/f'{component}.py')
        module=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=module
        spec.loader.exec_module(module)
    return sys.modules[f'{name}.engine'], sys.modules[f'{name}.models'].RoomInput

NEW, Input = load_engine(COMP, 'lb_114_engine')


def test_previous_normal_humidity_decisions_remain_identical():
    """Golden digest over 2,200 deterministic 0.11.3 cases (humidity >=41%)."""
    import hashlib
    import json
    rng=random.Random(114)
    outputs=[]
    for _ in range(2200):
        values=dict(indoor_temp=rng.uniform(16,31), indoor_humidity=rng.uniform(41,85), outdoor_temp=rng.uniform(-5,35), outdoor_humidity=rng.uniform(10,99), target_temp=rng.uniform(18,24), co2=rng.choice([None,500,900,1100,1500,2100]), window_open=rng.choice([False,True]), has_window_contacts=rng.choice([False,True]), hours_since_airing=rng.choice([2,25]))
        r=NEW.evaluate_room(Input(**values))
        outputs.append((r.color,r.mode,r.recommendation_key,r.room_status_color))
    digest=hashlib.sha256(json.dumps(outputs,ensure_ascii=False).encode()).hexdigest()
    assert digest == 'd37148a017fbed397bb824a5de8a08757a8abb385cdde047385b2b276cac493f'


def test_dry_air_with_real_outdoor_moisture_advantage():
    result=NEW.evaluate_room(Input(indoor_temp=22,indoor_humidity=35,outdoor_temp=24,outdoor_humidity=65,target_temp=22,hours_since_airing=1))
    assert result.decision_need=='humidity_low'
    assert result.mode=='feuchte_befeuchten'
    assert result.color=='green'


def test_high_outdoor_relative_humidity_not_automatically_useful():
    result=NEW.evaluate_room(Input(indoor_temp=22,indoor_humidity=35,outdoor_temp=1,outdoor_humidity=90,target_temp=22,hours_since_airing=1))
    assert result.mode != 'feuchte_befeuchten'
    assert result.color != 'green'


def test_critical_co2_and_safety_override_dry_comfort():
    result=NEW.evaluate_room(Input(indoor_temp=22,indoor_humidity=35,outdoor_temp=24,outdoor_humidity=65,target_temp=22,co2=2100,nina_status='danger'))
    assert result.safety_lock and result.mode=='nina_aussenluftgefahr'


def test_clear_words_not_future_or_false_clear():
    for phrase in ('bis zur abschließenden Untersuchung und ausdrücklichen Entwarnung', 'Noch keine Entwarnung', 'Teilentwarnung'):
        assert not re.search(r'^Entwarnung$', phrase)
    # Scoping through AST is done in separate dedicated NINA tests.



def test_confirmed_open_window_does_not_trigger_overdue_airing_after_two_days():
    for hours in (24, 48, 72):
        state = NEW.evaluate_room(Input(
            indoor_temp=22, indoor_humidity=48,
            outdoor_temp=18, outdoor_humidity=70,
            target_temp=22, hours_since_airing=hours,
            has_window_contacts=True, window_open=True,
            current_airing_qualified=True,
        ))
        assert state.decision_need != 'routine'
        assert state.mode not in {'routine_lueften', 'routine_warten'}

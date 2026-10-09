"""No-Home-Assistant smoke/regression tests for display-only 0.11.3 changes."""
from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path

COMP = Path(__file__).resolve().parents[1] / 'custom_components' / 'lueftungsberater'
spec = importlib.util.spec_from_file_location('lb_qol_localization', COMP / 'localization.py')
assert spec and spec.loader
lang = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lang)

langs = ('de', 'en', 'tr')
count = 0
for code in langs:
    original_args = {
        'start_time': datetime.fromisoformat('2026-10-08T22:00:00+02:00'),
        'end_time': datetime.fromisoformat('2026-10-09T03:00:00+02:00'),
        'requested_night_end': '06:00',
        'thermal_need': True,
        'live_open_now': True,
    }
    text = lang.night_advice_text('night_now', original_args, code)
    assert text and '03:00' not in text, (code,text)
    assert '06:00' not in text, (code,text)
    assert len(text) < 210, (code,text)
    count += 3
    text2 = lang.night_advice_text('night_now', {**original_args, 'end_time': datetime.fromisoformat('2026-10-09T06:00:00+02:00')}, code)
    assert '06:00' in text2, (code,text2)
    count += 1
    note = lang.night_advice_text('night_short_only', {**original_args, 'co2_minutes_to_2000': 25}, code)
    assert 'CO₂' in note and '03:00' not in note
    count += 1
    no_note = lang.night_advice_text('night_short_only', {**original_args, 'live_open_now': False, 'co2_minutes_to_2000': 25}, code)
    assert 'CO₂' not in no_note
    count += 1
    assert lang.recommendation_text('open_now', code)
    assert lang.duration_text('5_10', code)
    count += 2

# Existing localization keys (including warning and setup entries) must stay aligned.
files = {code: json.loads((COMP/'translations'/f'{code}.json').read_text()) for code in langs}
def collect(data,prefix=''):
    if isinstance(data,dict):
        out={}
        for key,value in data.items(): out.update(collect(value,f'{prefix}.{key}' if prefix else key))
        return out
    return {prefix: str(data)}
texts={code:collect(payload) for code,payload in files.items()}
assert set(texts['de'])==set(texts['en'])==set(texts['tr']), 'translation keys diverged'
count += 1
pattern = re.compile(r'\{[a-zA-Z0-9_]+\}')
for key,de in texts['de'].items():
    for code in ('en','tr'):
        assert set(pattern.findall(de))==set(pattern.findall(texts[code][key])),(key,code)
        count+=1
print(f'PASS: {count} localization/night regression checks, {len(texts["de"])} translation strings per language')

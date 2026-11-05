"""One request per distinct station per provider job (no HA import required)."""
import ast
from datetime import datetime, timezone, timedelta
import math
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE = Path(__file__).resolve().parents[1] / 'custom_components/lueftungsberater/auto_providers.py'
TREE = ast.parse(MODULE.read_text(encoding='utf8'))


def load_function(name, namespace):
    node = next(node for node in TREE.body if isinstance(node, ast.AsyncFunctionDef) and node.name == name)
    # Strip type annotations and helper defaults that may reference HA types.
    import copy
    node = copy.deepcopy(node)
    node.decorator_list = []
    node.returns = None
    for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
        arg.annotation = None
    code = compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(MODULE), 'exec')
    exec(code, namespace)
    return namespace[name]


DWD_FIELDS = {'temp': (-90, 60), 'humidity': (0, 100)}


@pytest.mark.asyncio
async def test_dwd_all_failed_stations_are_queried_once_including_duplicate_candidate():
    ids = ['a', 'b', 'a', 'c']
    stations = [(SimpleNamespace(station_id=station), index) for index, station in enumerate(ids)]
    calls = []
    async def index(*_args): return stations
    async def get_bytes(_session, url):
        calls.append(url)
        if url.endswith('b'): raise ConnectionError('offline')
        return b''
    fetch = load_function('_fetch_dwd_observations', {
        '_dwd_station_candidates': index, '_DWD_FIELDS': DWD_FIELDS,
        '_get_bytes': get_bytes, '_DWD_MEASUREMENT_URL': '{station_id}',
        '_valid_dwd_measurement': lambda _raw: {},
    })
    _candidates, observations = await fetch(None, None, None)
    assert calls == ['a', 'b', 'c']
    assert observations == []


@pytest.mark.asyncio
async def test_dwd_partial_fields_progress_and_recovery_on_next_job():
    stations = [(SimpleNamespace(station_id=i), n) for n, i in enumerate('abc')]
    calls = []
    progress = []
    responses = {'a': {}, 'b': {'temp': '17'}, 'c': {'humidity': '54', 'present_weather': 'cloudy'}}
    async def index(*_args): return stations
    async def get_bytes(_session, url): calls.append(url); return url.encode()
    fetch = load_function('_fetch_dwd_observations', {
        '_dwd_station_candidates': index, '_DWD_FIELDS': DWD_FIELDS,
        '_get_bytes': get_bytes, '_DWD_MEASUREMENT_URL': '{station_id}',
        '_valid_dwd_measurement': lambda raw: responses[raw.decode()],
    })
    async def on_progress(value): progress.append(value)
    _, found = await fetch(None, None, None, on_progress=on_progress)
    assert calls == ['a', 'b', 'c']
    assert len(found) == 2 and len(progress) == 2
    responses['a'] = {'temp': '16', 'humidity': '52', 'present_weather': 'sunny'}
    calls.clear()
    _, found = await fetch(None, None, None)
    assert calls == ['a'] and len(found) == 1  # recovery, no persistent blacklist


class TimedValues(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observed_at = {}
        self.fetched_at = {}


@pytest.mark.asyncio
async def test_uba_unavailable_and_stale_candidates_are_not_retried():
    ids = ['one', 'two', 'one', 'three']
    stations = [(SimpleNamespace(code=station, name=station), number) for number, station in enumerate(ids)]
    calls = []
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    async def station_candidates(*_args): return stations
    async def components(*_args): return {'pm': 'pm2_5'}
    class DT:
        @staticmethod
        def utcnow(): return now
        @staticmethod
        async def async_get_time_zone(_name): return timezone.utc
    async def get_json(_session, _url, params):
        calls.append(params['station'])
        if params['station'] == 'two': raise ConnectionError('bad station')
        return {'station': params['station']}
    def parser(_result, _components, _zone): return TimedValues()  # stale/empty
    fetch = load_function('_fetch_uba_air_quality', {
        'asyncio': __import__('asyncio'), 'dt_util': DT,
        'timedelta': timedelta, 'math': math, 'TimedValues': TimedValues,
        '_uba_station_candidates': station_candidates,
        '_uba_component_index': components, '_get_json': get_json,
        '_UBA_AIRQUALITY': 'unused', '_parse_uba_airquality_fresh': parser,
    })
    values, sources = await fetch(None, None, None)
    assert calls == ['one', 'two', 'three']
    assert values == {} and sources == {}


@pytest.mark.asyncio
async def test_uba_partial_pollutants_preserve_sources_and_measurement_time():
    stations = [(SimpleNamespace(code=i, name=f'Station {i}'), n) for n, i in enumerate('abc')]
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    calls = []
    progress = []
    async def station_candidates(*_args): return stations
    async def components(*_args): return {}
    class DT:
        @staticmethod
        def utcnow(): return now
        @staticmethod
        async def async_get_time_zone(_name): return timezone.utc
    async def get_json(_session, _url, params):
        calls.append(params['station'])
        return {'station': params['station']}
    def parser(response, *_args):
        out = TimedValues()
        mapping = {'a': {'pm10': 11}, 'b': {'pm2_5': 8, 'o3': 40}, 'c': {'no2': 20, 'so2': 3}}
        for key, value in mapping[response['station']].items():
            out[key] = value
            out.observed_at[key] = now - timedelta(minutes=20)
        return out
    fetch = load_function('_fetch_uba_air_quality', {
        'asyncio': __import__('asyncio'), 'dt_util': DT,
        'timedelta': timedelta, 'math': math, 'TimedValues': TimedValues,
        '_uba_station_candidates': station_candidates,
        '_uba_component_index': components, '_get_json': get_json,
        '_UBA_AIRQUALITY': 'unused', '_parse_uba_airquality_fresh': parser,
    })
    async def on_progress(value): progress.append(value)
    values, sources = await fetch(None, None, None, on_progress=on_progress)
    assert calls == ['a', 'b', 'c']
    assert set(values) == {'pm10', 'pm2_5', 'o3', 'no2', 'so2'}
    assert len(progress) == 3
    assert all(values.observed_at[k] == now - timedelta(minutes=20) for k in values)
    assert sources['pm10'].startswith('uba_station:a:')
    assert sources['so2'].startswith('uba_station:c:')

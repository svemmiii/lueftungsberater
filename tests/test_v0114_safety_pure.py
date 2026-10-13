"""Isolated safety regressions without an installed Home Assistant runtime."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'lueftungsberater'


def _availability():
    tree = ast.parse((ROOT / 'safety_state.py').read_text())
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and
             node.name in {'_warning_provider_availability', '_matching_warning_ids', '_canonical_warning_id', '_safety_location_distance_km'}]
    aliases = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_WARNING_SOURCE_ALIASES' for t in node.targets)]
    mod = ast.fix_missing_locations(ast.Module(body=[*aliases, *funcs], type_ignores=[]))
    ns = {'Any': object, 'SafetyAvailability': str, 'CONF_WARNING_SOURCE': 'warning_source',
          'WARNING_SOURCE_NONE': 'none', '_entry_entity_ids': lambda hass, entry: [],
          'cos': __import__('math').cos, 'hypot': __import__('math').hypot, 'radians': __import__('math').radians}
    exec(compile(mod, 'safety_state.py', 'exec'), ns)
    return ns['_warning_provider_availability']


def test_unrelated_or_partial_cancellation_must_not_release_window_lock():
    evaluator = _availability()
    prior = {'source_key': 'nina-id', 'warning_ids': ['smoke-id', 'chemical-id']}
    config = SimpleNamespace(data={'warning_source': 'nina-id'})
    nina = SimpleNamespace(domain='nina', entry_id='nina-id')
    hass = SimpleNamespace(config_entries=SimpleNamespace(async_get_entry=lambda key: nina))
    warning = SimpleNamespace(warning_notice_kind='all_clear',
                              warning_ids={'smoke-id'}, nina_status='clear',
                              official_close_instruction=False, provider_availability={})
    assert evaluator(hass, config, warning, prior)[0] == 'unknown'
    warning.warning_ids = {'drinking-water-id'}
    assert evaluator(hass, config, warning, prior)[0] == 'unknown'
    warning.warning_ids = {'smoke-id', 'chemical-id'}
    assert evaluator(hass, config, warning, prior)[0] == 'clear'


def test_warning_opt_in_is_persisted_without_extra_reconfigure_fields():
    src = (ROOT / 'config_flow.py').read_text()
    assert 'CONF_SHOW_GENERAL_WARNINGS: bool(entry.data.get(CONF_SHOW_GENERAL_WARNINGS, False))' in src
    assert 'data.setdefault(CONF_SHOW_GENERAL_WARNINGS, bool(entry.data.get(CONF_SHOW_GENERAL_WARNINGS, False)))' in src
    assert 'vol.Optional(CONF_SHOW_GENERAL_WARNINGS): BooleanSelector()' in src


def test_open_window_duration_has_periodic_maintenance_without_new_completed_airing():
    src = (ROOT / 'coordinator.py').read_text()
    assert 'async_track_time_interval(self.hass, refresh_open_airing, timedelta(minutes=1))' in src
    assert 'if tracker is not None and tracker.is_open:' in src
    assert 'self._handle_tracker_change()' in src
    # Persisted completed sessions continue to be written only by the airing tracker.
    assert 'last_confirmed_airing' not in src[src.index('def refresh_open_airing'):src.index('def refresh_open_airing') + 350]


def test_night_does_not_create_new_mid_sleep_instructions():
    src = (ROOT / 'coordinator.py').read_text()
    assert 'previous is None' in src
    assert 'raw = NightAdvice()' in src
    assert 'night_temperature_already_active=night_thermal_active' in src

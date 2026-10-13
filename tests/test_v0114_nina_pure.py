"""NINA content regression checks independent of the HA test harness."""
from __future__ import annotations
import ast
import importlib.util
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'custom_components'/'lueftungsberater'


def warning_classifier():
    spec=importlib.util.spec_from_file_location('lb_nina_language_114',ROOT/'warning_language.py')
    language=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(language)
    names={
        'OFFICIAL_CLOSE_ACTIONS','CLEAR_WORDS','CLEAR_NEGATIONS','CLEAR_QUALIFIERS',
        'STRONG_CLEAR_WORDS','OFFICIAL_CLOSE_PATTERNS','CLOSE_RELEASE_PATTERNS',
        '_contains_any','_is_clear_warning','_is_strong_clear_warning',
        '_matches_close_instruction','_has_official_close_instruction','_evaluate_air_warning',
    }
    source=ast.parse((ROOT/'providers.py').read_text())
    filtered=[]
    for node in source.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
            filtered.append(node)
        elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in names:
            filtered.append(node)
    scope=dict(re=re, foreign_all_clear=language.foreign_all_clear,has_foreign_close_order=language.has_foreign_close_order)
    exec(compile(ast.fix_missing_locations(ast.Module(body=filtered,type_ignores=[])),str(ROOT/'providers.py'),'exec'),scope)
    return scope['_evaluate_air_warning']


def test_bornheim_drinking_water_is_not_an_all_clear():
    evaluate=warning_classifier()
    headline='Wichtiger Hinweis zur Trinkwassernutzung - Stadt Bornheim'
    description=('Im Wasserwerk wurden E.coli-Bakterien gefunden. Es wird ein Abkochgebot '
                 'für Trinkwasser bis zur abschließenden Untersuchung und ausdrücklichen '
                 'Entwarnung ausgesprochen.')
    assert evaluate(headline,description,'Kochen Sie das Wasser vor dem Trinken ab.') == 'none'
    assert evaluate(headline,description,'',message_type='Alert') == 'none'


def test_real_clear_and_simultaneous_close_instruction():
    evaluate=warning_classifier()
    assert evaluate('Entwarnung: Rauchentwicklung','Die Warnung wurde aufgehoben.',
        'Schließen Sie Fenster und Türen und schalten Sie Lüftungen ab.')=='clear'
    assert evaluate('Giftiger Rauch','Fenster und Türen geschlossen halten.', '')=='danger'
    assert evaluate('Lageupdate','Eine Entwarnung liegt noch nicht vor.',
        'Fenster und Türen weiterhin geschlossen halten.')=='danger'
    assert evaluate('Teilentwarnung','Ein Teilgebiet ist sicher.',
        'Fenster und Türen geschlossen halten.')=='danger'
    assert evaluate('Rauchentwicklung','Eine Entwarnung erfolgt, sobald die Gefahr vorbei ist.', '')=='none'


def test_cancel_status_overrides_stale_actions():
    evaluate=warning_classifier()
    assert evaluate('Rauchentwicklung','Alte Warnbeschreibung',
        'Fenster geschlossen halten',message_type='Cancel')=='clear'


def test_manual_and_auto_pass_the_same_warning_fields():
    src=(ROOT/'providers.py').read_text()
    assert src.count('_evaluate_air_warning(')>=3

"""Small, explicit FR/NL/IT protective orders, without machine translation.

Based on official FR-Alert, NL-Alert and Protezione Civile action wording.
These rules run only on warning text, not on general advice web pages.
"""
from __future__ import annotations

import re
import unicodedata


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(text)).casefold().replace("’", "'").split())


_WINDOWS = r"(?:portes?|fen[eê]tres?|ramen|deuren|porte|finestre)"
_VENT = r"(?:ventilation|climatisation|ventilatie|luchttoevoer|ventilazione|climatizzazione|condizionamento)"
_CLOSE = tuple(re.compile(pattern) for pattern in (
    rf"\b(?:fermez|fermer)\b.{{0,80}}\b{_WINDOWS}\b",
    rf"\b(?:gardez|maintenez)\b.{{0,60}}\b{_WINDOWS}\b.{{0,50}}\bferm[eé]es?\b",
    rf"\b(?:coupez|arr[eê]tez|[eé]teignez)\b.{{0,80}}\b{_VENT}\b",
    r"\bsluit\b.{0,80}\b(?:ramen|deuren)\b",
    r"\b(?:hou|houd)\b.{0,60}\b(?:ramen|deuren)\b.{0,40}\bgesloten\b",
    r"\b(?:zet|schakel)\b.{0,70}\b(?:ventilatie|luchttoevoer)\b.{0,40}\buit\b",
    r"\b(?:chiudi|chiudete|chiudere)\b.{0,80}\b(?:porte|finestre)\b",
    r"\b(?:tieni|tenete|mantieni|mantenete)\b.{0,60}\b(?:porte|finestre)\b.{0,40}\bchiuse\b",
    rf"\b(?:spegni|spegnete|spegnere|disattiva|disattivate)\b.{{0,80}}\b{_VENT}\b",
))
# Negations are tied to the closing/switching verb. An unrelated instruction
# such as "ne quittez pas votre abri" must not hide a valid close order.
_NEGATION = tuple(re.compile(pattern) for pattern in (
    r"\b(?:ne|n')\s*(?:fermez|fermer|coupez|arr[eê]tez|[eé]teignez)\b.{0,55}\b(?:pas|plus)\b",
    r"\b(?:sluit|houd|zet|schakel)\b.{0,65}\bniet\b",
    r"\bnon\s+(?:chiudi|chiudete|chiudere|spegni|spegnete|spegnere|disattiva|disattivate|tenete|tieni)\b",
    r"\b(?:pas|plus)\s+n[eé]cessaire\b.{0,50}\b(?:fermer|couper)\b",
    r"\bniet\s+meer\b.{0,60}\b(?:gesloten|uitschakelen|sluiten)\b",
    r"\bnon\s+[eè]\s+pi[uù]\s+necessario\b.{0,50}\b(?:chiudere|spegnere)\b",
))


def has_foreign_close_order(text: str) -> bool:
    for sentence in re.split(r"[.!?;\n]+", normalized(text)):
        if any(pattern.search(sentence) for pattern in _NEGATION):
            continue
        if any(pattern.search(sentence) for pattern in _CLOSE):
            return True
    return False


def foreign_all_clear(text: str) -> bool:
    """Recognize explicit full withdrawal; ambiguous/partial text stays unknown."""
    low = normalized(text)
    if re.search(r"\b(?:partiel\w*|partiellement|gedeeltelijk\w*|voorwaardelijk\w*|parzial\w*|condizion\w*)\b", low):
        return False
    if re.search(r"\b(?:pas|niet|non)\b.{0,70}\b(?:lev[eé]e?|ingetrokken|geweken|cessato|revocato)\b", low):
        return False
    if re.search(r"\b(?:lev[eé]e?|ingetrokken|geweken|cessato|revocato)\b.{0,40}\b(?:pas|niet|non)\b", low):
        return False
    return bool(re.search(
        r"\balerte\b.{0,90}\b(?:est|a [eé]t[eé])\s+lev[eé]e\b|"
        r"\b(?:nl-alert|waarschuwing)\b.{0,90}\b(?:is\s+)?ingetrokken\b|"
        r"\bgevaar\s+is\s+geweken\b|"
        r"\b(?:allarme\s+(?:[eè]\s+)?(?:cessato|revocato)|cessato\s+allarme)\b",
        low,
    ))


def is_probe_message(*parts: str) -> bool:
    low = normalized(" ".join(parts))
    if re.search(r"\b(?:not a test|geen test|kein test|kein probealarm|non [eè] un test)\b|n'est pas un test", low):
        return False
    return bool(re.search(
        r"^test\b|\b(?:testbericht|alarmeringstest|testalarm|probealarm|feuerwehr[uü]bung|exercice|esercitazione)\b|"
        r"\b(?:this is a test|dit is een test|ceci est un test|questo [eè] un test)\b", low,
    ))

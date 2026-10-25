"""Local warning languages and provider-neutral CAP evidence.

Language packs, CAP normalization, typed claims and source reconciliation share
this existing module to preserve the integration's original file layout. Only
warning_policy.py makes the common safety decision. Parsing remains bounded
local rules, independent of the selected interface language.
"""
from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import lru_cache
from html import unescape
import math
import re
from types import SimpleNamespace
from typing import Any, Literal
import unicodedata
import xml.etree.ElementTree as ET



# Existing protective-action and all-clear language helpers.
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


# Shared UTC normalization, units and policy constants.
LEAD_TIME = timedelta(minutes=30)


HARD_GUST_KMH = 90.0


STRONG_GUST_KMH = 65.0


UTC_MAX = datetime.max.replace(tzinfo=timezone.utc)


def plain_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    # A comparison such as "<90 km/h ... >100 km/h" is not an HTML tag.
    return " ".join(unescape(re.sub(r"</?[a-zA-Z][^>]*>", " ", value)).split()).strip()


def aware(value: Any) -> datetime | None:
    """Normalize provider times without letting a UTC offset cross date limits."""
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime) or value.tzinfo is None:
            return None
        if value.utcoffset() is None:
            return None
        return value.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _lead_start(onset: datetime | None) -> datetime | None:
    """An unrepresentable prelock is unresolved, never an invented onset."""
    if onset is None:
        return None
    try:
        return onset - LEAD_TIME
    except OverflowError:
        return None


# Registered language packs; each pack provides metadata and an extractor.
_WARNING_LANGUAGE_PACKS = {}


class WarningLanguagePack:
    """A bounded text extractor, with separately declared UI capability."""

    CODE = ""
    UI_LANGUAGE = False
    WARNING_TEXT_SUPPORT = "bounded_rules"
    ENABLED = True
    FRAGMENTS = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.CODE:
            _WARNING_LANGUAGE_PACKS[cls.CODE] = cls
            for name in ("_text_grammar", "_header_grammar"):
                cached = globals().get(name)
                if cached is not None:
                    cached.cache_clear()

    @classmethod
    def extract(cls, record, *, elevation=None):
        raise NotImplementedError("Each warning language must declare its extractor")


def installed():
    """Return registered packs; changing the UI locale never changes these."""
    return tuple(_WARNING_LANGUAGE_PACKS[code] for code in sorted(_WARNING_LANGUAGE_PACKS)
                 if _WARNING_LANGUAGE_PACKS[code].ENABLED)


def set_warning_language_enabled(code: str, enabled: bool):
    """Activate text support independently of UI translations and CAP profiles."""
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be a boolean")
    language = base_language(code)
    pack = next((pack for pack in _WARNING_LANGUAGE_PACKS.values()
                 if language in getattr(pack, "LANGUAGES", (pack.CODE,))), None)
    if pack is None:
        raise ValueError(f"No registered warning language: {code}")
    pack.ENABLED = enabled
    _text_grammar.cache_clear()
    _header_grammar.cache_clear()



class CompatibleWarningLanguages(WarningLanguagePack):
    """Shared extractor implementation, not a separately enabled language."""

    @classmethod
    def extract(cls, record, *, elevation=None):
        return _text_grammar(cls).extract_text(record, elevation=elevation)

    UI_LANGUAGE = False
    WARNING_TEXT_SUPPORT = 'bounded_rules'


class FrenchWarningLanguage(CompatibleWarningLanguages):
    CODE = 'fr'
    FRAGMENTS = {'gust': r'rafales?', 'wind': r'tornade|temp[eê]te|vent violent',
                 'relevant': r'orage|gr[eê]le|pluie intense|fum[eé]e|poussi[eè]re',
                 'exposed': r'expos[ée]s?|cr[êe]tes?|littoral|en\s+dehors|au-dessus|au-dessous'}


class SpanishWarningLanguage(CompatibleWarningLanguages):
    CODE = 'es'
    FRAGMENTS = {'gust': r'rachas?', 'wind': r'viento',
                 'relevant': r'tormenta|granizo|lluvia intensa|\bhumo\b',
                 'exposed': r'expuest[oa]s?|altitud|cumbres?|costa'}


class ItalianWarningLanguage(CompatibleWarningLanguages):
    CODE = 'it'
    FRAGMENTS = {'gust': r'raffiche', 'wind': r'vento', 'relevant': r'temporale',
                 'exposed': r'espost[ei]|cime\b|quota\b|fuori'}


class DutchWarningLanguage(CompatibleWarningLanguages):
    CODE = 'nl'
    FRAGMENTS = {'gust': r'windstoten', 'wind': r'(?!)', 'relevant': r'(?!)',
                 'exposed': r'kust'}


class GermanWarningLanguage(WarningLanguagePack):
    @classmethod
    def extract(cls, record, *, elevation=None):
        return _text_grammar(cls).extract_text(record, elevation=elevation)

    CODE = 'de'
    UI_LANGUAGE = True
    WARNING_TEXT_SUPPORT = 'bounded_rules'
    LANGUAGE_HINT = r"\b(?:fenster|t[üu]ren|l[üu]ftungsanlage[n]?)\b"
    FRAGMENTS = {'gust': '(?:(?:wind|sturm|orkan|spitzen)[ -]?)?(?:b[oö]en|boeen)(?:spitzen)?|windst(?:oß|oss|oess|öß|öss)(?:en|e)?|windspitze(?:n)?|b[oö]ig', 'wind': '\\bwind\\b|sturm|orkan', 'relevant': 'gewitter|hagel|starkregen|\\brauch\\b|chemisch|schadstoff|giftig|staub', 'weather_head': 'sicht', 'predicate_time': 'inzwischen|derzeit|gegenwärtig|gegenwaertig|aktuell|momentan|zur\\s+zeit'}


class EnglishWarningLanguage(WarningLanguagePack):
    @classmethod
    def extract(cls, record, *, elevation=None):
        return _text_grammar(cls).extract_text(record, elevation=elevation)

    CODE = 'en'
    UI_LANGUAGE = True
    WARNING_TEXT_SUPPORT = 'bounded_rules'
    LANGUAGE_HINT = r"\b(?:windows?|doors?)\b"
    FRAGMENTS = {'gust': 'gust(?:s|ing)?', 'wind': '\\bwind\\b|hurricane|tornado', 'relevant': 'thunderstorm|\\bhail\\b|heavy rain|\\bsmoke\\b|chemical|toxic|dust', 'predicate_time': 'now|currently|presently|already|still|any\\s+longer'}


class TurkishWarningLanguage(WarningLanguagePack):
    @classmethod
    def extract(cls, record, *, elevation=None):
        return _text_grammar(cls).extract_text(record, elevation=elevation)

    CODE = 'tr'
    UI_LANGUAGE = True
    WARNING_TEXT_SUPPORT = 'bounded_rules'
    LANGUAGE_HINT = r"\b(?:pencereler[iı]?|kap[ıi]lar[ıi]?|havaland[ıi]rma)\b"
    FRAGMENTS = {'gust': 'r[üu]zg[aâ]r\\s+hamle(?:leri|ler|si)?', 'wind': 'fırtına|firtina|r[üu]zg[aâ]r', 'relevant': 'g[öo]k\\s+g[üu]r[üu]lt[üu]l[üu]|dolu|[şs]iddetli\\s+ya[ğg]mur|duman|zehirli', 'exposed': 'da[ğg]lar(?:da)?\\b|da[ğg]l[ıi]k\\s+b[öo]lgelerde\\b|k[ıi]y[ıi](?:larda|da)?\\b|y[üu]ksek\\s+kesimlerde\\b', 'denial': 'beklenmiyor|beklenmemektedir|beklenmez|beklenmeyecek(?:tir)?|beklenmedi|beklenmemiş(?:tir)?|ihtimali\\s+ortadan\\s+kalkt[ıi]', 'speed_unit': 'km\\s*/\\s*sa(?:at)?'}


GermanWarningLanguage.FRAGMENTS["exposed"] = 'exponiert|gipfel|h[öo]henlagen|hochlagen|bergland|berglagen|freien?\\s+lagen|k[üu]ste|kueste|au[ßs]erhalb|oberhalb|unterhalb'

EnglishWarningLanguage.FRAGMENTS["exposed"] = 'exposed|mountain|summit|coast|outside'

def fragments(kind: str) -> str:
    parts = [pack.FRAGMENTS[kind] for pack in installed() if pack.FRAGMENTS.get(kind)]
    return "|".join(f"(?:{part})" for part in parts) or r"(?!)"


def base_language(language: str) -> str:
    return str(language or "").strip().replace("_", "-").split("-", 1)[0].lower()


def select(language: str, text: str):
    """Prefer CAP metadata, checking recognizable subject words for plausibility."""
    base = base_language(language)
    matching = [pack for pack in installed() if base in getattr(pack, "LANGUAGES", (pack.CODE,))]
    detected = [pack for pack in installed() if re.search(
        r"\b(?:" + pack.FRAGMENTS.get("gust", r"(?!)") + r")\b", text, re.I)
        or re.search(getattr(pack, "LANGUAGE_HINT", r"(?!)"), text, re.I)]
    if detected:
        pack = next((pack for pack in detected if pack in matching), detected[0])
        return pack, bool(language and pack not in matching), False
    if matching:
        return matching[0], False, False
    if not language:
        # Older HA adapters have no CAP language metadata. Preserve their
        # established grammar; this is not a claim about arbitrary languages.
        fallback = next((pack for pack in installed() if pack.CODE == "de"), None)
        return fallback, False, fallback is None
    return None, False, True


def capabilities():
    return {language: {"ui": pack.UI_LANGUAGE, "warning_text": pack.WARNING_TEXT_SUPPORT}
            for pack in installed() for language in getattr(pack, "LANGUAGES", (pack.CODE,))}


UI_LANGUAGES = tuple(sorted(pack.CODE for pack in installed() if pack.UI_LANGUAGE))


# Typed assertions and protective actions.
@dataclass(frozen=True, slots=True)
class Quantity:
    minimum: float | None
    maximum: float | None
    unit: Literal["km/h"] = "km/h"


@dataclass(frozen=True, slots=True)
class AreaScope:
    key: str
    verified: bool


@dataclass(frozen=True, slots=True)
class TimeInterval:
    onset: datetime | None
    ends: datetime | None
    verified: bool


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    provider: str
    sender: str
    warning_id: str
    issued_at: str | None
    info_index: int
    language: str
    field: str
    detected_language: str = ""
    language_mismatch: bool = False

    def to_dict(self):
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True)
class WarningAssertion:
    event: Literal["wind_gust"]
    quantity: Quantity
    polarity: Literal["affirmative", "negated", "uncertain"]
    area: AreaScope
    period: TimeInterval
    provenance: tuple[EvidenceSource, ...]
    details: dict[str, Any] = field(compare=False, repr=False)

    @classmethod
    def from_evidence(cls, item, provenance):
        return cls("wind_gust", Quantity(item["min"], item["max"]),
                   "negated" if item["denied"] else "affirmative",
                   AreaScope(item["scope"], item["location_verified"]),
                   TimeInterval(item["onset"], item["ends"], item["time_verified"]),
                   tuple(provenance), dict(item))

    def to_evidence(self):
        return {**self.details, "event_type": self.event,
                "quantity_unit": self.quantity.unit, "polarity": self.polarity,
                "provenance": [source.to_dict() for source in self.provenance]}


@dataclass(frozen=True, slots=True)
class ProtectiveAction:
    action: Literal["keep_closed"]
    period: TimeInterval
    provenance: EvidenceSource
    text: str


@dataclass(frozen=True, slots=True)
class WarningAnalysis:
    assertions: tuple[WarningAssertion, ...]
    wind: bool
    relevant: bool
    area_verified: bool
    outside_area: bool = False
    uncertain: bool = False
    languages: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    close_intervals: tuple[TimeInterval, ...] = ()
    timing_uncertain: bool = False
    close_orders: tuple[ProtectiveAction, ...] = ()
    close_area_verified: bool = True

    def evidence(self):
        return [assertion.to_evidence() for assertion in self.assertions]


# CAP info normalization and per-block action context.
def pairs(rows: Any) -> dict[str, Any]:
    if isinstance(rows, dict):
        if "valueName" not in rows:
            return deepcopy(rows)
        rows = [rows]
    result = {}
    for row in rows if isinstance(rows, (list, tuple)) else ():
        if not isinstance(row, dict) or not row.get("valueName"):
            continue
        key, value = str(row["valueName"]), deepcopy(row.get("value"))
        if key in result:
            result[key] = [*result[key], value] if isinstance(result[key], list) else [result[key], value]
        else:
            result[key] = value
    return result


def number(value):
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError, OverflowError):
        return None


@dataclass(frozen=True, slots=True)
class CAPInfo:
    index: int
    language: str
    data: dict[str, Any]
    area_match: bool | None = True
    altitude: float | None = None
    ceiling: float | None = None
    area_uncertain: bool = False

    def to_record(self, envelope):
        data = self.data
        raw_times = {key: data.get(key) for key in ("effective", "onset", "expires", "event_end")}
        if raw_times["effective"] in (None, ""):
            # CAP 1.2 defaults effective to the envelope's sent time.
            raw_times["effective"] = getattr(envelope, "issued_at", None)
        times = {key: aware(value) for key, value in raw_times.items()}
        instruction = str(data.get("instruction") or "")
        parameters = pairs(data.get("parameter", data.get("parameters")))
        if not instruction:
            instruction = " ".join(str(value) for key in ("instructionText", "recommendedActions", "recommended_actions")
                                   for value in (parameters.get(key) if isinstance(parameters.get(key), list)
                                                 else [parameters.get(key)]) if value)
        # Only envelope identity/transport metadata is shared across info blocks.
        return SimpleNamespace(
            **{key: getattr(envelope, key, None) for key in
               ("warning_id", "provider_domain", "category", "sender", "issued_at", "evidence_at", "msg_type", "references")},
            **{key: str(data.get(key) or "") for key in ("headline", "description", "event")},
            instruction=instruction, severity=str(data.get("severity") or "unknown"),
            parameters=parameters, event_codes=pairs(data.get("eventCode", data.get("event_codes"))),
            language=self.language, info_index=self.index, info_blocks=(),
            area_altitude=self.altitude, area_ceiling=self.ceiling,
            area_restriction_unknown=self.area_uncertain or self.area_match is None,
            area_match=self.area_match,
            timing_uncertain=any(raw_times[key] not in (None, "") and times[key] is None for key in times),
            **times,
        )


def info_block(data, index, *, area_match=True):
    data = deepcopy(data)
    areas = data.get("area", [])
    if isinstance(areas, dict):
        areas = [areas]
    bounds = {(number(area.get("altitude")), number(area.get("ceiling")))
              for area in areas if isinstance(area, dict)}
    lower, upper = next(iter(bounds)) if len(bounds) == 1 else (None, None)
    malformed = any(area.get(key) not in (None, "") and number(area.get(key)) is None
                    for area in areas if isinstance(area, dict) for key in ("altitude", "ceiling"))
    return CAPInfo(index, str(data.get("language") or "en-US"), data, area_match, lower, upper,
                   malformed or len(bounds) > 1 and any(lo is not None or hi is not None for lo, hi in bounds))


def json_infos(payload):
    """Stop at the nearest CAP envelope; never mix sibling warning versions."""
    if not isinstance(payload, dict):
        return ()
    infos = payload.get("info")
    if isinstance(infos, dict):
        infos = [infos]
    if isinstance(infos, list):
        return tuple(info_block(info, index) for index, info in enumerate(infos) if isinstance(info, dict))
    # Documented wrappers may contain exactly one alert, never aggregate alerts.
    if isinstance(payload.get("alert"), dict):
        return json_infos(payload["alert"])
    return ()


def xml_data(element):
    """Keep repeated fields (parameters, areas, event codes) without overwrites."""
    result = {}
    repeated = {"area", "parameter", "eventCode", "category", "polygon", "circle", "geocode", "responseType"}
    for child in element:
        name = str(child.tag).rsplit("}", 1)[-1]
        value = xml_data(child) if len(child) else str(child.text or "").strip()
        if name in repeated:
            result.setdefault(name, []).append(value)
        elif name in result:
            result[name] = [*result[name], value] if isinstance(result[name], list) else [result[name], value]
        else:
            result[name] = value
    return result


def xml_infos(element):
    return tuple(info_block(xml_data(info), index, area_match=None)
                 for index, info in enumerate(element) if str(info.tag).rsplit("}", 1)[-1] == "info")


def attach_infos(record, blocks, *, preferred_language="en", now=None):
    """Keep one display record, with a time envelope spanning all relevant infos."""
    blocks = tuple(blocks)
    if not blocks:
        return record
    record.info_blocks = blocks
    eligible = [block for block in blocks if block.area_match is not False
                and (now is None or aware(block.data.get("expires")) is None
                     or aware(block.data["expires"]) > now)]
    if not eligible:
        return record
    display_candidates = [block for block in eligible if block.area_match is True] or eligible
    preferred = next((block for block in display_candidates if block.language.lower().startswith(preferred_language)),
                     display_candidates[0])
    display = preferred.to_record(record)
    for key in ("language", "headline", "description", "instruction", "event", "severity"):
        setattr(record, key, getattr(display, key))
    variants = [block.to_record(record) for block in eligible]
    # This envelope is only for transport expiry/persistence. Every assertion
    # retains its own info timing for the actual safety decision.
    for key, aggregate in (("effective", min), ("onset", min), ("expires", max), ("event_end", max)):
        values = [getattr(variant, key) for variant in variants]
        setattr(record, key, aggregate(values) if all(value is not None for value in values) else None)
    record.timing_uncertain = any(variant.timing_uncertain for variant in variants)
    return record


def with_area(block, matched, *, bounds=None):
    if bounds is None:
        return replace(block, area_match=matched)
    lower, upper, uncertain = bounds
    return replace(block, area_match=matched, altitude=lower, ceiling=upper,
                   area_uncertain=uncertain)


def variants(record):
    blocks = getattr(record, "info_blocks", ())
    return tuple(block.to_record(record) for block in blocks if block.area_match is not False) if blocks else (record,)


def info_area_element(block):
    """Use the same geography resolver for JSON and XML CAP footprints."""
    root = ET.Element("info")
    areas = block.data.get("area", [])
    if isinstance(areas, dict):
        areas = [areas]
    for data in areas:
        if not isinstance(data, dict):
            continue
        area = ET.SubElement(root, "area")
        for name in ("polygon", "circle", "geocode", "altitude", "ceiling"):
            values = data.get(name, [])
            if not isinstance(values, list):
                values = [values]
            for value in values:
                child = ET.SubElement(area, name)
                if isinstance(value, dict):
                    for key in ("valueName", "value"):
                        ET.SubElement(child, key).text = str(value.get(key) or "")
                else:
                    child.text = str(value)
    return root


def geographic_signature(block):
    """Compare typed footprints across translations, never translated names."""
    areas = block.data.get("area", [])
    if isinstance(areas, dict):
        areas = [areas]
    signatures = []
    for area in areas:
        if not isinstance(area, dict):
            return None
        entries = []
        for key in ("polygon", "circle", "geocode"):
            values = area.get(key, [])
            if not isinstance(values, list):
                values = [values]
            entries.extend((key, str(value.get("valueName", "")), str(value.get("value", "")))
                           if isinstance(value, dict) else (key, "", str(value)) for value in values)
        if not entries:
            return None
        signatures.append(tuple(sorted(entries)))
    return tuple(sorted(signatures))


def action_context(record, evaluate, now, *, elevation=None):
    """Evaluate protective actions per info; an unknown translation is no clear."""
    if str(getattr(record, "msg_type", "")).casefold() == "cancel":
        return "clear", frozenset(), False
    statuses, closes = [], set()
    uncertain = False
    for variant in variants(record):
        effective, ends, valid = _valid_times(variant)
        if ends is not None and ends <= now:
            continue
        status = evaluate(variant.headline, " ".join((variant.event, variant.description)),
                          variant.instruction, variant.msg_type)
        text = " ".join((variant.headline, variant.event, variant.description, variant.instruction))
        language = str(getattr(variant, "language", "") or "")
        pack, mismatch, unsupported = select(language, text)
        if status == "danger":
            # evaluate() has already proved an original protective command.
            # Metadata disagreement is evidence of uncertainty, not a veto.
            uncertain |= mismatch or unsupported
        elif status == "clear" and (pack is None or language and base_language(language) not in capabilities()):
            uncertain = True
            continue
        known, outside = _area_context(variant, elevation, explicit_close=status == "danger")
        if outside:
            continue
        if not known or not valid or getattr(variant, "area_match", True) is None:
            uncertain = True
            continue
        if status == "danger":
            closes.add(getattr(variant, "info_index", 0))
        if effective is not None and effective > now:
            uncertain |= status in {"danger", "clear"}
            continue
        statuses.append(status)
    if "danger" in statuses:
        return "danger", frozenset(closes), uncertain or "clear" in statuses
    if statuses and all(status == "clear" for status in statuses) and not uncertain:
        return "clear", frozenset(), False
    return "none", frozenset(closes), uncertain or "clear" in statuses


# Versioned provider parameter profiles.
PROFILES = {
    # NWS CAP documentation: maxWindGust. Units must be present in the value;
    # neither a bare number nor severity/SAME/II codes imply a wind speed.
    "nws_auto": ("nws-cap-v1", {"maxWindGust": "wind_gust"}),
    "nina_auto_dwd": ("dwd-cap-v2.1.14", {"gusts": "wind_gust"}),
    "meteoalarm_auto": ("meteoalarm-cap-v1", {}),
}


def normalized_record(record):
    """Keep free-text parameters separate from profile-defined CAP quantities."""
    name, typed_parameters = PROFILES.get(str(getattr(record, "provider_domain", "")), ("generic-cap-v1", {}))
    parameters = getattr(record, "parameters", {}) or {}
    if not isinstance(parameters, dict):
        return record, name
    # DWD's historical `gusts` field can ALSO contain free-form, scoped CAP
    # language. Retain its text evidence so that 30-minute timing and local
    # qualifiers are not lost when adding its typed numeric profile.
    normalized = ({key: value for key, value in parameters.items()
                   if not (isinstance(key, str) and any(
                       key.casefold() == name.casefold() for name in typed_parameters))}
                  if not name.startswith("dwd-cap-") else dict(parameters))
    keys = ("warning_id", "provider_domain", "category", "sender", "issued_at", "evidence_at", "msg_type", "references",
            "headline", "description", "instruction", "event", "severity", "effective", "onset", "expires", "event_end",
            "event_codes", "language", "info_index", "area_altitude", "area_ceiling", "area_restriction_unknown", "timing_uncertain")
    return SimpleNamespace(**{key: getattr(record, key, None) for key in keys}, parameters=normalized), name


@dataclass(frozen=True, slots=True)
class StructuredFindings:
    assertions: tuple[WarningAssertion, ...]
    issues: tuple[str, ...] = ()


_CAP_GUST_VALUE = re.compile(
    r"\s*(?P<value>\d{1,3}(?:[.,]\d+)?)\s*(?P<bracket>\[)?\s*"
    r"(?P<unit>km\s*/\s*h|kmh|kph|m\s*/\s*s|mph|knots?|kts?|kn)"
    r"\s*(?(bracket)\])\s*", re.I)


# DWD CAP Profile 2.1.14, section 3.2: gusts are expressed as
# <50, ~50, >120, etc., with the documented unit [km/h]. Parse those
# qualifiers as bounds/estimates; never silently turn them into exact values.
_DWD_GUST_VALUE = re.compile(
    r"\s*(?P<qualifier>[~<>])?\s*(?P<value>\d{1,3}(?:[.,]\d+)?)\s*"
    r"(?P<bracket>\[)?\s*(?P<unit>km\s*/\s*h)\s*(?(bracket)\])\s*", re.I)


def _typed_cap_gust(raw, *, dwd=False):
    """Return bounded km/h data or None for unknown units/invalid syntax."""
    match = (_DWD_GUST_VALUE if dwd else _CAP_GUST_VALUE).fullmatch(raw) if isinstance(raw, str) else None
    if match is None:
        return None
    unit = re.sub(r"\s", "", match["unit"].lower())
    factor = 3.6 if unit == "m/s" else 1.609344 if unit == "mph" else 1.852 if unit.startswith(("kn", "kt")) else 1.0
    speed = float(match["value"].replace(",", ".")) * factor
    if not math.isfinite(speed) or not 0 <= speed <= 500:
        return None
    qualifier = match["qualifier"] if dwd else None
    if qualifier == "<":
        lower, upper, lower_closed, upper_closed = None, speed, True, False
    elif qualifier == ">":
        lower, upper, lower_closed, upper_closed = speed, None, False, True
    else:
        # '~' is a nominal estimate, not a mathematically exact forecast.
        lower, upper, lower_closed, upper_closed = speed, speed, True, True
    return (lower, upper, {"lower_kmh": lower, "upper_kmh": upper,
                           "lower_inclusive": lower_closed, "upper_inclusive": upper_closed},
            "approximately" if qualifier == "~" else
            "less_than" if qualifier == "<" else "greater_than" if qualifier == ">" else "reported")


def _cap_area_context(record, elevation):
    """Resolve only CAP geometry/altitude; never inspect natural language."""
    if getattr(record, "area_match", True) is False:
        return False, True
    known = not getattr(record, "area_restriction_unknown", False) and getattr(record, "area_match", True) is not None
    altitude, ceiling = (getattr(record, key, None) for key in ("area_altitude", "area_ceiling"))
    if altitude is not None or ceiling is not None:
        known = (known and isinstance(elevation, (int, float)) and not isinstance(elevation, bool)
                 and math.isfinite(elevation)
                 and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
                         for value in (altitude, ceiling) if value is not None))
        if known and altitude is not None and ceiling is not None and altitude > ceiling:
            return False, False
        if known and ((altitude is not None and elevation < altitude * 0.3048)
                      or (ceiling is not None and elevation > ceiling * 0.3048)):
            return False, True
    return known, False


def extract_structured_cap(record, *, elevation=None) -> StructuredFindings:
    """Extract profiled quantities without selecting or calling a text parser.

    NWS defines maxWindGust as a quantity applying to its containing CAP info.
    An explicit unit, matching provider profile, own interval and own CAP area
    are mandatory. Unrecognized keys, bare numbers and prose are not quantities.
    """
    profile, names = PROFILES.get(str(getattr(record, "provider_domain", "")), ("generic-cap-v1", {}))
    parameters = getattr(record, "parameters", {}) or {}
    if not isinstance(parameters, dict):
        return StructuredFindings(())
    _, ends, valid = _valid_times(record)
    onset = aware(getattr(record, "onset", None))
    known, _ = _cap_area_context(record, elevation)
    issued = aware(getattr(record, "issued_at", None))
    findings, issues = [], set()
    for key in names:
        # DWD documents the field as 'gusts' (also printed 'Gusts'). Other
        # suppliers cannot gain trust just by reusing the parameter name.
        matching_keys = [name for name in parameters if isinstance(name, str)
                         and name.casefold() == key.casefold()]
        for actual_key in matching_keys:
            raw_values = parameters[actual_key] if isinstance(parameters[actual_key], list) else [parameters[actual_key]]
            for raw in raw_values:
                parsed = _typed_cap_gust(raw, dwd=profile.startswith("dwd-cap-"))
                if parsed is None:
                    issues.add("invalid_structured_gust")
                    continue
                lower, upper, interval, qualifier = parsed
                item = {
                    "source": "parameter", "parameter": actual_key,
                    "statement": f"{actual_key}: {raw}",
                    "min": lower, "max": upper, "text": raw, "denied": False,
                    "speed_interval": interval, "quantity_qualifier": qualifier,
                    "scope": "general", "location_verified": known,
                    "location_explicit": False,
                    "onset": onset, "ends": ends, "time_verified": valid,
                    "time_explicit": False, "time_bounds": [], "time_source": "CAP",
                    "declared_period": {}, "time_period": {}, "time_constraints": [],
                    "location_exclusions": [], "weather_conditions": [],
                    "height_references": [], "explicit_scope": False,
                    "provider_profile": profile, "evidence_kind": "structured_cap",
                    "parameter_original_value": raw,
                    "event_codes": deepcopy(getattr(record, "event_codes", {}) or {}),
                }
                provenance = EvidenceSource(
                    str(getattr(record, "provider_domain", "")),
                    str(getattr(record, "sender", "")), str(getattr(record, "warning_id", "")),
                    issued.isoformat() if issued else None,
                    int(getattr(record, "info_index", 0)),
                    str(getattr(record, "language", "") or ""), f"parameter:{actual_key}")
                findings.append(WarningAssertion.from_evidence(item, (provenance,)))
    return StructuredFindings(tuple(findings), tuple(sorted(issues)))


# Language-independent numeric and source reconciliation.
def _speed_sets_overlap(left: dict, right: dict) -> bool:
    def interval(item):
        value = item.get("speed_interval")
        if value is not None:
            return (value["lower_kmh"], value["upper_kmh"],
                    value["lower_inclusive"], value["upper_inclusive"])
        return item["min"] or 0.0, item["max"], True, True

    a, b = interval(left), interval(right)
    lower = max(a[0] if a[0] is not None else 0.0,
                b[0] if b[0] is not None else 0.0)
    upper = min(a[1] if a[1] is not None else math.inf,
                b[1] if b[1] is not None else math.inf)
    if lower != upper:
        return lower < upper
    return all((lower > low or low_closed) and (high is None or lower < high or high_closed)
               for low, high, low_closed, high_closed in (a, b))


def _same_speed(left: dict, right: dict) -> bool:
    if left["max"] is None or right["max"] is None:
        return False
    return (math.isclose(left["max"], right["max"], rel_tol=0.005, abs_tol=0.5)
            and (left["min"] is None) == (right["min"] is None)
            and (left["min"] is None or math.isclose(left["min"], right["min"], rel_tol=0.005, abs_tol=0.5)))


def _periods_overlap(left: dict, right: dict) -> bool:
    starts = [item["onset"] for item in (left, right) if item["onset"]]
    ends = [item["ends"] for item in (left, right) if item["ends"]]
    return not starts or not ends or max(starts) < min(ends)


def _polarity_locations_overlap(left: dict, right: dict) -> bool:
    if (left.get("info_index") != right.get("info_index")
            and not all(item.get("cap_area_verified", True) and item.get("cap_timing_verified", True)
                        for item in (left, right))):
        return False
    if left["scope"] == right["scope"]:
        return True
    # General, numeric-height and verified exclusion claims can refer to the
    # same window. Unknown named/terrain regions never become verified here.
    return all(item["location_verified"] and (item["scope"] == "general"
               or item["scope"].startswith(("height:", "excluded:"))) for item in (left, right))


def _reconcile_gust_claims(evidence: list[dict]) -> list[dict]:
    """Compare atomic claims, including distinct assertions in the same field."""
    for index, item in enumerate(evidence):
        item["assertion_id"] = f"gust:{index}"
    for index, left in enumerate(evidence):
        for right_index, right in enumerate(evidence[index + 1:], index + 1):
            if not _polarity_locations_overlap(left, right) or not _periods_overlap(left, right):
                continue
            left_denied = left.get("source_denied", left["denied"])
            right_denied = right.get("source_denied", right["denied"])
            if left_denied != right_denied and _speed_sets_overlap(left, right):
                left["polarity_conflict"] = right["polarity_conflict"] = True
                positive, negative_index = (right, index) if left_denied else (left, right_index)
                positive.setdefault("polarity_conflicts", []).append(negative_index)
            if left["denied"] or right["denied"] or not left["time_verified"] or not right["time_verified"]:
                continue
            if _same_speed(left, right) and left["time_explicit"] and right["time_explicit"] and any(
                    key in left["time_period"] and key in right["time_period"]
                    and left["time_period"][key] != right["time_period"][key]
                    for key in ("onset", "ends")):
                left["time_conflict"] = right["time_conflict"] = True
            if (left["location_verified"] and right["location_verified"]
                    and left["scope"] == right["scope"] and left["max"] is not None and right["max"] is not None
                    and not _speed_sets_overlap(left, right)
                    and (left["max"] + 0.5 < (right["min"] or 0) or right["max"] + 0.5 < (left["min"] or 0))):
                left["value_conflict"] = right["value_conflict"] = True
    return evidence


def _uncontested_gust_periods(item: dict, evidence: list[dict]) -> list[dict]:
    """Retain a positive forecast outside the actual contradictory intervals."""
    periods = [(item["onset"], item["ends"])]
    for index in item.get("polarity_conflicts", []):
        denial = evidence[index]
        if not denial["time_verified"]:
            return []  # Do not invent when an unresolved denial starts or ends.
        remaining = []
        for start, end in periods:
            overlap = {"onset": start, "ends": end}
            if not _periods_overlap(overlap, denial):
                remaining.append((start, end))
                continue
            if denial["onset"] and (start is None or start < denial["onset"]):
                remaining.append((start, denial["onset"]))
            if denial["ends"] and (end is None or denial["ends"] < end):
                remaining.append((denial["ends"], end))
        periods = remaining
    return [{**item, "onset": start, "ends": end} for start, end in periods]


# Per-language text parser state. Shared methods interpret syntax, not safety.
@dataclass(frozen=True, slots=True)
class TextFindings:
    headers: tuple[dict, ...]
    descriptions: tuple[dict, ...]
    unbound: tuple[dict, ...]
    titles: dict[str, str]


def _parameter_identifies_quantity(parameter: dict, quantity: dict) -> bool:
    """A flat peak can identify the event type of a matching reported peak.

    Scalar parameters do not reproduce the lower endpoint of a textual range.
    Their matching maximum can still inherit that quantity's own restricted
    scope. The original interval and strict-upper safeguards stay separate.
    """
    return _same_speed(parameter, quantity) or (
        parameter["min"] is not None and parameter["min"] == parameter["max"]
        and quantity["max"] is not None
        and math.isclose(parameter["max"], quantity["max"], rel_tol=0.005, abs_tol=0.5))


class WarningTextGrammar:
    """A reentrant grammar instance configured by one installed language pack.

    Numeric, time and context machinery is shared. Event vocabulary, exposed
    terrain, negative inflections and lexical modifiers belong to the pack.
    No grammar instance receives or returns a window-lock decision.
    """

    def __init__(self, pack):
        self.pack = pack

        self._GUST = re.compile(r"\b(?:" + self.fragment("gust") + r")\b", re.I)

        self._GUST_NOMINAL = re.compile(
            rf"(?:{self._GUST.pattern})(?:\s+(?:of\s+wind|de\s+(?:viento|vent)|di\s+vento)\b)?", re.I)

        self._WIND = re.compile(self.fragment("wind"), re.I)

        self._RELEVANT = re.compile(self.fragment("relevant"), re.I)

        self._SPEED = re.compile(
            r"(?<![\d.,+−-])(?P<lower>\d{1,3}(?:[.,]\d+)?)\s*(?:(?:-|–|—|to|bis|à|a)\s*(?P<upper>\d{1,3}(?:[.,]\d+)?))?\s*\[?\s*"
            rf"(?P<unit>{self.fragment('speed_unit')}|km\s*/\s*[hu]|kmh|kph|stundenkilometer(?:n|s)?|"
            r"kilomet(?:er|re)(?:n|s)?\s+(?:pro|je|per)\s+(?:stunde|hour|uur)|"
            r"m\s*/\s*s|mph|knots?|kts?|kn)\b", re.I)

        self._GUST_AFTER_SPEED = re.compile(
            rf"^\s*(?:,\s*)?(?:(?:insbesondere|vor\s+allem|especially|particularly)\s+)?"
            rf"(?:in|als|as|en|dans)\s+(?:(?:starken?|schweren?|strong|severe)\s+)?"
            rf"(?:(?:wind|sturm|orkan)[ -]?)?(?:{self._GUST_NOMINAL.pattern})\b", re.I)

        self._SPEED_FIELD = re.compile(
            r"\b(?:wind(?:geschwindigkeit(?:en)?|s)?|geschwindigkeit(?:en)?|speeds?|velocity|"
            r"vitesses?|velocidad(?:es)?|velocit[àa]|snelheid|snelheden)\b", re.I)

        self._EXPOSED = re.compile(r"\b(?:" + self.fragment("exposed") + r")", re.I)

        self._SEA_LEVEL_REFERENCE = (
            r"(?:(?:über|ueber)\s+(?:dem\s+)?(?:NN|NHN|normalnull|normalh[öo]hennull|meeresspiegel|meer)|"
            r"ü\.\s*(?:d\.\s*)?(?:NN|NHN|M)|NN|NHN|MSL|AMSL|"
            r"above\s+(?:mean\s+)?sea\s+level)\b")

        self._RELATIVE_HEIGHT_REFERENCE = (
            r"(?:(?:über|ueber)\s+(?:dem\s+)?(?:grund|boden)|AGL|"
            r"above\s+(?:ground|terrain)(?:\s+level)?|WGS\s*84|ellipsoid(?:al)?)\b")

        self._HEIGHT_NOUN = r"(?:meeres)?h(?:ö|oe|o)he(?:n(?:lage(?:n)?)?)?|lagen?"

        self._ALTITUDE = re.compile(
            rf"\b(?:(?:in|auf)\s+(?:(?:einer|der)\s+)?(?:{self._HEIGHT_NOUN})\s+(?:von\s+)?)?"
            r"(?P<relation>above|over|below|under|at\s+least|up\s+to|"
            r"oberhalb|unterhalb|über|ueber|unter|mehr\s+als|weniger\s+als|h[öo]her\s+als|niedriger\s+als|"
            r"mindestens|h[öo]chstens|ab|bis(?:\s+zu)?|"
            r"au-dessus\s+de|au-dessous\s+de|por\s+encima\s+de|por\s+debajo\s+de|"
            r"al\s+di\s+sopra\s+di|al\s+di\s+sotto\s+di|boven|beneden)\s*"
            rf"(?:(?:von\s+)?(?:(?:einer|der)\s+)?(?:{self._HEIGHT_NOUN})\s+von\s+|von\s+)?"
            r"(?P<height>[+−-]?(?:\d(?:[\d.,'’\u00a0\u202f ]{0,28}\d)?|[.,]\d{1,15})(?:[eE][+−-]?\d{0,4})?)\s*"
            r"(?P<unit>metres?|meters?|metern?|m|feet|ft)(?=\b|(?:NN|NHN|MSL|AMSL|AGL)\b)(?!\s*/)"
            rf"(?:\s*(?P<reference>{self._SEA_LEVEL_REFERENCE}|{self._RELATIVE_HEIGHT_REFERENCE}))?", re.I)

        self._LOCAL_AREA = re.compile(
            r"\b(?:in|im|auf|an|at|on|sur|en|sulle|nelle|in\s+the)\s+"
            r"(?:(?:der|den|dem|des|die|the|les|des|le|la|los|las|den|de)\s+)?"
            r"(?:(?:h[öo]her\w*|tiefer\w*|hoch\w*|niedrig\w*|exponiert\w*|frei\w*|"
            r"upper|higher|lower|high|exposed|mountain|coastal)\s+)*"
            r"(?:lagen|h[öo]hen|bergen|berge|bergland|gebirg\w*|gipfel\w*|k[üu]sten?\w*|"
            r"norden|s[üu]den|osten|westen|nordteil|s[üu]dteil|ostteil|westteil|"
            r"mountains?|summits?|highlands?|hills?|elevations?|coast|areas?|regions?|"
            r"montagne|montagnes|monta[ñn]as|monti|cr[êe]tes?|cumbres?|cime)\b", re.I)

        self._ONLY_LOCATION = re.compile(
            r"\b(?:nur|ausschlie[ßs]lich|lediglich|only|solely|seulement|uniquement|solo|solamente|alleen)"
            r"\s+(?:in|im|auf|an|am|at|on|above|below|sur|en|sulle|nelle)\b", re.I)

        self._PLACE_PREPOSITION = (
            r"zwischen|between|von|from|(?:rund|rings)\s+um|around|um|"
            r"(?:n[öo]rd|s[üu]d|[öo]st|west|nord[öo]st|nordwest|s[üu]d[öo]st|s[üu]dwest)lich(?:\s+von)?|"
            r"(?:north|south)(?:east|west)?\s+of|(?:east|west)\s+of|"
            r"in|im|ins|an|am|auf|aufs|bei|beim|über|ueber|unter|vor|hinter|nahe|"
            r"innerhalb|außerhalb|ausserhalb|entlang|at|on|over|off|above|below|under|near|within|outside|"
            r"sur|dans|en|sulle|sul|nel|nella|nei|nelle|aan|op")

        self._PLACE_START = re.compile(rf"\b(?:{self._PLACE_PREPOSITION})\s+", re.I)

        self._PLACE_PHRASE = re.compile(
            rf"\b(?:{self._PLACE_PREPOSITION})\s+"
            r"(?P<body>[^\W\d_][\w'’\-]*(?:\s+[^\W\d_][\w'’\-]*){0,8})", re.I)

        self._PLACE_DETERMINER = re.compile(
            r"der|den|dem|des|die|das|einem|einer|einen|eines|the|a|an|les|le|la|los|las|"
            r"de|het|il|lo|gli|i|un|une|el", re.I)

        self._PLACE_WORD_END = re.compile(
            r"und|oder|aber|jedoch|and|or|but|et|y|e|en|sowie|doch|mais|pero|ma|maar|"
            r"mit|bei|with|without|ohne|durch|during|will|would|are|is|be|"
            r"werden|wird|wurden|wurde|sind|ist|seien|sein|können|kann|könnten|könnte|"
            r"treten|tritt|erwartet|erwarten|auftreten|ausgeschlossen|expected|forecast|possible|"
            r"von|bis|nach|um|up|to|of", re.I)

        self._WIND_NOUN = re.compile(rf"(?:(?:wind|sturm|orkan)[ -]?)?(?:{self._GUST_NOMINAL.pattern})|{self._WIND.pattern}", re.I)

        self._ATMOSPHERIC_STATE = (
            r"(?:(?:boden|luft|dauer|nacht|stark|spät|spaet|früh|frueh)?(?:frost(?:s|es)?|fr[öo]ste(?:n)?))|"
            r"luftfeucht(?:e|igkeit)|luftdruck(?:s|es)?|minusgrad(?:e(?:n)?|s)?|wolke(?:n)?")

        self._WEATHER_SYSTEM = (
            r"(?:kalt|warm|okklusions|gewitter)front(?:en)?|schauerlinie(?:n)?|"
            r"(?:tief|hoch)druck(?:zone(?:n)?|gebiet(?:es|s)?|lage(?:n)?)")

        self._WEATHER_NOUN = re.compile(
            rf"{self.fragment('weather_head')}|gewitter(?:n|s|schauer(?:n|s)?|lage(?:n)?)?|"
            r"(?:(?:stark|dauer|platz|spr[üu]h|niesel|eis|schnee|sturm|orkan|gewitter)?regen|(?:stark|dauer)?schnee)"
            r"(?:s|f[aä]ll(?:e|en|s)?|schauer(?:n|s)?)?|"
            r"niederschl(?:ag(?:s|es)?|[äa]ge(?:n)?)|schauer(?:n|s)?|"
            r"hagel(?:s|schlag(?:s|es)?|schl[äa]ge(?:n)?|schauer(?:n|s)?)?|"
            r"graupel(?:s|schauer(?:n|s)?)?|blitz(?:schlag(?:s|es)?|schl[äa]ge(?:n)?)|"
            r"glatteis(?:es)?|(?:eis|schnee)gl[äa]tte|"
            r"schnee(?:verwehung(?:en)?|matsch(?:es|s)?|griesel(?:s)?|treiben(?:s)?|gest[öo]ber(?:s)?)|"
            r"brise(?:n)?|nebel(?:s)?|temperatur(?:en)?|"
            r"(?:un|schauer|tau|f[öo]hn|fr[üu]hlings|fruehlings|sommer|herbst|winter)?"
            r"wetter(?:s|lage(?:n)?|bedingung(?:en)?|verh[äa]ltnis(?:se|sen)?)?|"
            r"wetter(?:besserung|beruhigung|verschlechterung|umschwung|wechsel|[äa]nderung|aenderung)(?:en|s)?|"
            r"n[äa]sse|b[öo]igkeit|sicht(?:weite(?:n)?|verh[äa]ltnis(?:se|sen))|"
            r"wind(?:bedingung(?:en)?|verh[äa]ltnis(?:se|sen)?)|"
            r"witterung(?:s(?:bedingung(?:en)?|verh[äa]ltnis(?:se|sen)?))?|"
            r"himmel(?:s)?|k[äa]lte|sonne|hitze|gl[äa]tte|"
            r"bew[öo]lkung|trockenheit|wolkendecke|"
            rf"{self._ATMOSPHERIC_STATE}|{self._WEATHER_SYSTEM}|"
            r"thunderstorms?|rain(?:fall|showers?)?|hail|snow(?:fall)?|fog", re.I)

        self._WEATHER_MODIFIER = re.compile(
            r"(?:stark|schwer|kräftig|heftig|anhaltend|ergiebig|leicht|mäßig|maessig|schwach|"
            r"dicht|orkanartig|stürmisch|weiter|angekündigt|prognostiziert|"
            r"(?:gefrier|aufzieh|abzieh|einsetz|zunehm|abnehm)end)(?:e[rmns]?)?|"
            r"strong|severe|heavy|further|forecast|expected", re.I)

        self._THERMAL_CONDITION = (
            r"temperatur(?:en)?\s+(?:unter|über|ueber|von|um|bis(?:\s+zu)?|mehr\s+als|weniger\s+als)\s+"
            r"(?:(?:minus|plus)\s+)?(?:[+−-]?\d{1,3}(?:[.,]\d+)?|null|zero)\s*"
            r"(?:grad(?:\s+(?:celsius|fahrenheit))?\b|°\s*[cf]\b)|"
            r"temperatur(?:en)?\s+um\s+(?:den\s+)?gefrierpunkt(?:\s+herum)?")

        self._CONDITION_MODIFIERS = (
            rf"(?:(?:{self._WEATHER_MODIFIER.pattern}|(?-i:[a-zäöüß]+(?:em|en|er|es|e|ig|isch|lich))|"
            # An adverb can modify a following inflected adjective. The complete
            # meteorological head is still required; an unknown place cannot end it.
            r"(?-i:[a-zäöüß]+)(?=\s+(?-i:[a-zäöüß]+(?:em|en|er|es|e))\b)|"
            r"sehr|äußerst|aeusserst|extrem|ungewöhnlich|teils|teilweise|zeitweise|überwiegend)\s+){0,4}")

        self._WEATHER_INTERVAL = (
            r"(?:sonnig|heiter|bew[öo]lkt|regnerisch|trocken|wechselhaft)(?:e[rmns]?)\s+abschnitt(?:e|en)?")

        self._ENVIRONMENT_STATE = (
            rf"(?:{self._CONDITION_MODIFIERS}(?-i:[a-zäöüß]+(?:em|en|er|es|e))\s+"
            r"(?:(?:witterungs|wetter|straßen|strassen)?bedingungen|verh[äa]ltnis(?:se|sen))|"
            rf"{self._CONDITION_MODIFIERS}(?:feucht|nass|trocken|gefroren|vereist|verschneit|glatt|rutschig)"
            r"(?:e[rmns]?)\s+(?:straßen?|strassen?|boden|böden))")

        self._CONDITION_ATOM = (
            rf"(?:(?:dem|der|den|des|einem|einer|the)\s+)?"
            rf"(?:{self._ENVIRONMENT_STATE}|{self._CONDITION_MODIFIERS}"
            rf"(?:{self._THERMAL_CONDITION}|{self._WEATHER_INTERVAL}|{self._WEATHER_NOUN.pattern}|{self._WIND_NOUN.pattern}))\b")

        self._WEATHER_CONDITION = re.compile(
            rf"\b(?:bei|beim|unter|mit|ohne|durch|während|waehrend|with|without|during)\s+"
            rf"{self._CONDITION_ATOM}(?:\s+(?:und|oder|sowie|and|or)\s+{self._CONDITION_ATOM}){{0,4}}", re.I)

        self._NON_SPATIAL_PLACE = re.compile(
            rf"\b(?:(?:in\s+presenza\s+di|in\s+the\s+presence\s+of)(?=\s+(?:{self._WIND_NOUN.pattern})\b)|"
            r"in\s+(?:verbindung|kombination)\s+mit|im\s+(?:zusammenhang|vergleich|wechsel)\s+mit|"
            r"(?:rund|rings)\s+um\s+die\s+uhr|around\s+the\s+clock|"
            r"auf\s+grund(?:\s+(?:von|des|der))?|unter\s+anderem|"
            r"in\s+(?:(?:der|den)\s+)?spitzen?|im\s+mittel|"
            r"im\s+bereich\s+(?:von\s+)?(?=\d)|in\s+excess\s+of|in\s+combination\s+with|"
            r"at\s+times|in\s+(?:einzelnen|seltenen|manchen)\s+f[äa]llen|"
            r"(?:above|below|over|under)\s+(?:the\s+)?(?:threshold|limit)\s+of(?=\s+\d))\b", re.I)

        self._OTHER_SUBJECT_LINK = re.compile(r"\b(?:mit|ohne|with|without|sans|sin|senza)\s+", re.I)

        self._WIND_ATTRIBUTE = re.compile(
            rf"spitzen?\w*|h[öo]chstwert\w*|maxim\w*|verst[äa]rk\w*|auspr[äa]g\w*|"
            rf"geschwindigkeit\w*|speeds?|peaks?|{self._WIND_NOUN.pattern}", re.I)

        self._WARNING_AREA_MODIFIER = (
            r"(?:(?:(?:amtlich|offiziell)\s+)?(?:betroffen|ausgegeben|herausgegeben|angegeben|festgelegt|definiert)"
            r"(?:e[rmns]?)?|(?:amtlich|offiziell)(?:e[rmns]?)?)")

        self._WARNING_AREA_NOUN = (
            rf"(?:(?:{self._WARNING_AREA_MODIFIER})\s+){{0,3}}"
            r"(?:warngebiet(?:es|s)?|warnbereich(?:es|s)?|warnregion|"
            r"(?:gebiet(?:es|s)?|bereich(?:es|s)?|geltungsbereich(?:es|s)?)\s+der\s+(?:amtlichen\s+)?warnung)")

        self._WHOLE_WARNING_AREA = re.compile(
            rf"\b(?:(?:über|ueber)\s+(?:(?:das|dieses)\s+)?(?:{self._WARNING_AREA_NOUN})\s+"
            r"(?:hinweg\s+)?(?:flächendeckend|flaechendeckend)|"
            r"(?:überall|ueberall|flächendeckend|flaechendeckend)\s+"
            rf"(?:im|in\s+(?:dem|der|diesem|dieser)|innerhalb\s+(?:des|der|dieses|dieser)|"
            rf"(?:über|ueber)\s+(?:das|dieses))\s+(?:{self._WARNING_AREA_NOUN})|"
            r"everywhere\s+(?:in|within|across)\s+(?:the\s+)?warning\s+(?:area|region)|"
            r"(?:im|in|auf|an|über|ueber|innerhalb)\s+(?:(?:der|dem|den|das|des|diesem|dieser|dieses)\s+)?"
            rf"(?:gesamten?|ganzen?|kompletten?)\s+(?:{self._WARNING_AREA_NOUN}|"
            rf"(?:(?:{self._WARNING_AREA_MODIFIER})\s+){{0,3}}(?:region|gebiet(?:es|s)?))(?:\s+verteilt)?|"
            r"(?:in|innerhalb|auf)\s+(?:(?:allen|sämtlichen|saemtlichen)\s+"
            r"(?:teilen|teilregionen|regionen|bereichen|gebieten)|jedem\s+(?:teil|bereich|gebiet)|jeder\s+region)\s+"
            rf"(?:des|der|dieses|dieser)\s+(?:{self._WARNING_AREA_NOUN})|"
            r"(?:in|across|throughout)\s+(?:all\s+(?:parts|regions|areas)|every\s+(?:part|region|area)|"
            r"each\s+(?:part|region|area))\s+of\s+(?:the\s+)?warning\s+(?:area|region)|"
            r"(?:in|across|throughout)\s+(?:the\s+)?(?:whole|entire)\s+(?:warning\s+)?(?:area|region))\b"
            r"(?!\s+(?:des|der|von|of)\b)", re.I)

        self._WEEKDAY = (
            r"montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|"
            r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|"
            r"lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo")

        self._DAY_PART = r"morgen|vormittag|mittag|nachmittag|abend|nacht|fr[üu]h(?:e)?|morning|noon|afternoon|evening|night"

        self._MONTH = (
            r"januar|februar|m[äa]rz|april|mai|juni|juli|august|september|oktober|november|dezember|"
            r"january|february|march|may|june|july|october|december")

        self._CALENDAR_TIME = re.compile(
            rf"\b(?:(?:ab|bis|am|gegen|zum|vom|seit|on|from|until|since|by|beginning|starting|after|before|at|in)\s+)?"
            rf"(?:(?:der|dem|den|die|the)\s+)?"
            rf"(?:(?:kommend(?:e[rmns]?)?|n[äa]chst(?:e[rmns]?)?|next|this|coming|following)\s+)?"
            rf"(?:(?:{self._WEEKDAY}|heute|morgen|[üu]bermorgen|uebermorgen|today|tomorrow)(?:s)?(?:\s*(?:{self._DAY_PART}))?|{self._DAY_PART}|"
            rf"wochenende|woche|monat|jahr|weekend|week|month|year)\b|"
            rf"\b(?:ab|bis|im|am|vom|zum|seit|in|from|until|since|by|next|this|coming)\s+"
            rf"(?:(?:der|dem|den|the)\s+)?(?:(?:kommend(?:e[rmns]?)?|n[äa]chst(?:e[rmns]?)?|next|coming)\s+)?"
            rf"(?:{self._MONTH})\b", re.I)

        self._DATE_TEXT = re.compile(
            r"\b(?:am|ab|bis|vom|zum|on|from|until)\s+\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b", re.I)

        self._RELATIVE_TIME = re.compile(
            r"\b(?:in|nach|innerhalb|after|within)\s+(?:\d+(?:[.,]\d+)?|ein(?:e[rmns]?)?|zwei|drei|vier|f[üu]nf|"
            r"sechs|sieben|acht|neun|zehn|one|two|three|four|five|six|seven|eight|nine|ten)\s*"
            r"(?:minuten?|stunden?|tagen?|wochen?|minutes?|hours?|days?|weeks?|min|h)\b|"
            r"\b(?:bald|demn[äa]chst|zuk[üu]nftig|k[üu]nftig|soon|eventually)\b", re.I)

        self._TIME_HINT = re.compile(
            r"\b(?:gestern|heute|morgen|[üu]bermorgen|sp[äa]ter|zuvor|vorher|anschlie[ßs]end|"
            r"yesterday|today|tomorrow|later|previously|tonight|abends|nachts|nachmittags|"
            r"am\s+(?:abend|morgen|nachmittag)|in\s+der\s+nacht)\b|"
            r"\b(?:ab|bis|von|zwischen|from|until|after|before|between)\s+\d{1,4}(?:[:.-]\d{2})?|"
            rf"\b\d{{1,2}}(?::\d{{2}})?\s*(?:Uhr|UTC|CET|CEST|MEZ|MESZ)\b|"
            rf"{self._CALENDAR_TIME.pattern}|{self._DATE_TEXT.pattern}|{self._RELATIVE_TIME.pattern}", re.I)

        self._ISO_TIME = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})"

        self._TIME_BOUND = re.compile(
            rf"\b(?P<relation>ab|von|bis|from|until|before)\s+(?P<stamp>{self._ISO_TIME})", re.I)

        self._CLOCK_BOUND = re.compile(
            r"\b(?P<relation>ab|von|bis|from|until|before)\s+"
            r"(?P<hour>\d{1,2})(?:[.:](?P<minute>\d{2}))?"
            r"(?=\s*(?:Uhr|h|UTC|GMT|CET|CEST|MEZ|MESZ)\b)"
            r"(?:\s*(?:Uhr|h)\b)?(?:\s*(?P<zone>UTC|GMT|CET|CEST|MEZ|MESZ)\b)?"
            r"(?!\s*[+-]\s*\d)", re.I)

        self._STRICT_UPPER = re.compile(
            r"(?:<(?!=)|\b(?:unter|weniger\s+als|less\s+than|below|under|"
            r"inf[ée]rieur(?:e)?s?\s+[àa]|inferiores?\s+a|meno\s+di|inferiori\s+a|"
            r"minder\s+dan))\s*$", re.I)

        self._SPEED_COMPARISON = re.compile(
            rf"(?P<lt>{self._STRICT_UPPER.pattern})|"
            r"(?P<le><=|≤|\b(?:nicht\s+(?:über|ueber|mehr\s+als)|bis(?:\s+zu)?|höchstens|hoechstens|maximal|at\s+most|up\s+to|"
            r"no\s+more\s+than|au\s+plus|hasta|fino\s+a|tot))\s*$|"
            r"(?P<ge>>=|≥|\b(?:nicht\s+(?:unter|weniger\s+als)|ab|mindestens|at\s+least|au\s+moins|al\s+menos|almeno|ten\s+minste))\s*$|"
            r"(?P<gt>>|\b(?:über|ueber|mehr\s+als|oberhalb|more\s+than|above|over|"
            r"sup[ée]rieur(?:e)?s?\s+[àa]|superiores?\s+a|più\s+di|meer\s+dan))\s*$", re.I)

        self._NEGATIVE_ADVERB = (
            r"nicht|keinesfalls|keineswegs|niemals|nie|auf\s+keinen\s+fall|in\s+keinem\s+fall|"
            r"unter\s+keinen\s+umst[äa]nden|zu\s+keiner\s+zeit|not|never")

        self._NEGATED = re.compile(
            rf"\b(?:{self._NEGATIVE_ADVERB}|kein(?:e[rmns]?)?|ohne|no|without|none|"
            r"cannot|can['’]t|couldn['’]t|won['’]t|wouldn['’]t|don['’]t|doesn['’]t|didn['’]t|isn['’]t|aren['’]t|"
            r"non|nessun\w*|senza|sin|aucun\w*|pas|sans|geen|niet)\b", re.I)

        self._CLAUSE_BREAK = re.compile(r"[;\n]|(?<=[.!?])\s+(?=[^\W\d_])")

        self._PHRASE_BREAK = re.compile(
            r",(?!\d)|[():]|\s+\b(?:und|and|et|y|e|en|sowie|but|aber|jedoch|doch|mais|pero|ma|maar)\b\s+", re.I)

        self._OTHER_WEATHER = re.compile(
            rf"\b(?:{self._WEATHER_NOUN.pattern}|pluie|gr[êe]le|orages?|"
            r"lluvia|granizo|tormentas?|pioggia|grandine|temporali?|onweer|sneeuw|mist)\b", re.I)

        self._WIND_SUBJECT = re.compile(rf"{self._GUST_NOMINAL.pattern}|{self._WIND.pattern}", re.I)

        self._WIND_HEADER_SUBJECT = re.compile(
            rf"\b(?:wind|sturm|orkan|storm)(?:warnung(?:en)?|warnings?|gefahr)\b|{self._WIND_SUBJECT.pattern}", re.I)

        self._NEGATIVE_SUBJECT = re.compile(
            r"\b(?:kein(?:e[rmns]?)?|no|aucun\w*|nessun\w*|geen|pas\s+de|ohne|sin|senza|sans|without)\s+[^\W\d_]", re.I)

        self._WIND_REFERENCE = re.compile(
            r"^\s*(?:die|diese|welche|sie|which|that|these|those|they|elles|celles)\b|\bno\s+longer\b", re.I)

        self._LOCATION_START = re.compile(
            r"^\s*(?:(?:nur|ausschließlich|only|solely|seulement|uniquement|solo|solamente|alleen)\s+)*"
            r"(?:in|im|auf|an|ab|über|ueber|unter|oberhalb|unterhalb|außerhalb|ausserhalb|"
            r"above|over|below|under|at|on|outside|exposed|exponiert\w*|"
            r"au-dessus|au-dessous|sur|en|zonas?|zones?|lugares?|sulle|al|por|boven|beneden|die|which|that)\b", re.I)

        self._VALUE_LINK = re.compile(
            r"^\s*(?:(?:von|bis|zu|mit|spitzen|maximal|max\.?|allgemein|insgesamt|"
            r"up|to|of|generally|de|à|a|di|fino|hasta|tot|örtlich|reaching|reach|erreichen|erreicht|can|may)\s*)*$", re.I)

        self._PREDICATE_MODIFIER = (
            r"(?:(?:ganz|sehr|völlig|voellig|completely|very)\s+)?"
            r"(?:sicher(?:lich)?|definitiv|absolut|praktisch|bestimmt|gewiss|zweifellos|"
            r"offiziell|amtlich|garantiert|definitely|certainly|absolutely|practically)|"
            r"(?:mit|with)\s+(?:(?:großer|grosser|hoher|absoluter|great|absolute)\s+)?"
            r"(?:sicherheit|gewissheit|certainty)|völlig|voellig|ganz|completely|entirely|totally|"
            r"meteorologisch|rechnerisch|statistisch|modellseitig"
        )

        self._PREDICATE_TIME_ADVERB = self.fragment("predicate_time")

        self._OCCURRENCE_STEM = r"treten|tritt|traten|trat"

        self._ARRIVAL_STEM = r"kommen|kommt|kamen|kam"

        self._EXISTENCE_STEM = r"besteht|bestehen|existiert|existieren"

        self._ABSENCE_STEM = r"bleiben|bleibt|blieben|blieb|fallen|fällt|faellt|fielen|fiel"

        self._REPORTING_DETERMINER = (
            r"der|die|das|den|dem|des|ein(?:e[rmns]?)?|unser(?:e[rmns]?)?|"
            r"ihr(?:e[rmns]?)?|dies(?:e[rmns]?)?|all(?:e[rmns]?)?")

        self._REPORTING_NOUN = (
            r"angaben|informationen|auskunft|einschätzung(?:en)?|erkenntnissen|meldungen|stand|"
            r"aussage(?:n)?|ansicht(?:en)?|r[üu]ckmeldung(?:en)?|rueckmeldung(?:en)?|kenntnisstand(?:s|es)?|"
            r"berechnung(?:en)?|analyse(?:n)?|prognose(?:n)?|vorhersage(?:n)?|voraussicht|"
            r"modellrechnung(?:en)?|bericht(?:s|e(?:n)?)?|"
            r"(?:mess|wetter|vorhersage|prognose)?modell(?:s|e(?:n)?)?")

        self._REPORTING_MODIFIER = (
            rf"(?!(?:{self._REPORTING_DETERMINER}|{self._PLACE_WORD_END.pattern}|{self._NEGATED.pattern}|"
            rf"{self._OCCURRENCE_STEM}|{self._ARRIVAL_STEM}|{self._EXISTENCE_STEM}|{self._ABSENCE_STEM})\b)"
            r"[^\W\d_]+(?:em|en|er|es|e)")

        self._REPORTING_ENTITY = (
            rf"(?:{self._REPORTING_MODIFIER}\s+){{0,3}}"
            rf"(?:wetterdienst(?:es|s|e(?:n)?)?|wetterbehörde(?:n)?|wetterbehoerde(?:n)?|"
            rf"meteorologen|meteorologin(?:nen)?|behörde(?:n)?|behoerde(?:n)?|{self._REPORTING_NOUN}|"
            r"(?-i:[A-Z][A-Z0-9-]{1,12}|[A-Z][a-z]+[A-Z][A-Za-z]+))"
        )

        self._REPORTING_AGENT = (
            rf"(?:(?:der|die|das|unser(?:e[rmns]?)?|ihr(?:e[rmns]?)?)\s+|"
            rf"(?:durch|von)\s+(?:(?:{self._REPORTING_DETERMINER})\s+)?|vom\s+){self._REPORTING_ENTITY}"
        )

        self._PREDICATE_LINK = (
            rf"(?:{self._REPORTING_AGENT}|{self._PREDICATE_MODIFIER}|{self._PREDICATE_TIME_ADVERB}|{self._NEGATIVE_ADVERB}|die|diese|welche|sie|which|that|these|those|they|elles|celles|"
            r"es|werden|wird|wurden|wurde|sind|ist|seien|sein|können|kann|könnten|könnte|"
            r"lassen|lässt|laesst|sich|gelten|gilt|galten|galt|als|"
            r"zu|mehr|weiterhin|ausdrücklich|voraussichtlich|auch|wohl|"
            r"will|would|could|may|might|can|cannot|can['’]t|couldn['’]t|won['’]t|wouldn['’]t|"
            r"don['’]t|doesn['’]t|didn['’]t|isn['’]t|aren['’]t|do|does|did|are|is|be|been|being|have|has|longer|"
            r"ne|n['’]|sont|est|seront|serait|être|etre|peuvent|"
            r"sono|saranno|si|possono|potranno|può|puo|essere|son|se|worden|wordt|zijn|zullen|"
            r"kein(?:e[rmns]?)?|no|non|pas|plus|jamais|niet)"
        )

        self._EXCLUSION = (
            r"ausgeschlossen|auszuschlie[ßs]en|ausschlie[ßs]en|unmöglich|unmoeglich|"
            r"excluded|ruled\s+out|impossible|absent|exclu[es]?s?|esclus[oaie]|"
            r"escludono|esclude|escludere|descartad[oa]s?|uitgesloten"
        )

        self._FORECAST = (
            r"erwartet|erwarten|rechnen|befürchten|befuerchten|gemeldet|angekündigt|prognostiziert|vorhergesagt|"
            r"erreicht|erreichen|möglich|moeglich|wahrscheinlich|"
            r"eintreten|einzutreten|auftreten|aufzutreten|geben|gibt|vorkommen|"
            rf"(?:{self._OCCURRENCE_STEM})\s+(?:{self._PREDICATE_LINK}\b\s+){{0,12}}(?:auf|ein)|"
            rf"(?:{self._ARRIVAL_STEM})\s+(?:{self._PREDICATE_LINK}\b\s+){{0,12}}vor|"
            rf"(?:{self._EXISTENCE_STEM})\b(?:\s+{self._PREDICATE_LINK}\b){{0,12}}|"
            r"expected|anticipated|forecast(?:ed)?|predicted|reached|possible|occur(?:ring|red)?|observed|recorded|"
            r"attendu[es]?s?|pr[ée]vu[es]?s?|previs[toaie]+s?|"
            r"prevedono|prevede|prevedevano|prevedeva|prevedere|prevederanno|prevederà|"
            r"attendono|attende|attendere|attes[oaie]|esperan|esperad[oa]s?|verwacht|"
            r"bekleniyor|beklenmektedir|beklenir|beklenecek(?:tir)?|beklendi|beklenmiş(?:tir)?"
        )

        self._PREDICATE = re.compile(
            rf"(?P<links>(?:{self._PREDICATE_LINK}\b\s*){{0,12}})"
            rf"(?:(?P<exclusion>{self._EXCLUSION})|(?P<forecast>{self._FORECAST})|"
            rf"(?P<denial>{self.fragment('denial')})|"
            rf"(?P<absence>ausbleiben|auszubleiben|ausfallen|auszufallen|(?:{self._ABSENCE_STEM})\s+"
            rf"(?:{self._PREDICATE_LINK}\b\s+){{0,12}}aus))\b", re.I)

        self._ABSENCE_FRAME = re.compile(
            rf"\b(?:{self._ABSENCE_STEM})\s+(?:{self._PREDICATE_LINK}\b\s*){{0,12}}$", re.I)

        self._EXPECTATION_FRAME = re.compile(
            rf"\b(?P<links>(?:{self._PREDICATE_LINK}\b\s*){{1,12}})mit\s+"
            r"(?:(?:stark\w*|schwer\w*|weiter\w*)\s+){0,3}"
            r"(?:(?:wind|sturm|orkan)[ -]?)?$", re.I)

        self._ABSENT_WIND = re.compile(
            rf"\b(?:{self._NEGATIVE_ADVERB}|kein(?:e[rmns]?)?|no(?:\s+hay)?|aucun\w*|nessun\w*|geen|pas\s+de|"
            rf"ohne|without|sans|sin|senza|zonder)\s+"
            rf"(?:(?:stark\w*|schwer\w*|weiter\w*|strong|severe|further|fort\w*|violent\w*)\s+){{0,3}}"
            rf"(?:(?:wind|sturm|orkan)[ -]?)?(?:{self._WIND_SUBJECT.pattern})", re.I)

        self._NOMINAL_WIND_EVENT = re.compile(
            r"\b(?:(?P<negation>kein(?:e[rmns]?)?|ohne|no|without)\s+)?"
            r"(?:(?:das|dem|des|ein(?:e[rmns]?)?|the|an?)\s+)?"
            r"(?:(?:weiter\w*|erneut\w*|further|renewed)\s+){0,2}"
            r"(?P<head>auftreten|eintreten|vorkommen|aufkommen|occurrence|appearance|"
            r"ausbleiben|absence|wahrscheinlichkeit|möglichkeit|moeglichkeit|probability|likelihood|chance)\s+"
            r"(?:von|der|dieser|solcher|of|für|fuer|for)\s+"
            r"(?:(?:stark\w*|schwer\w*|weiter\w*|strong|severe|further)\s+){0,3}"
            r"(?:(?:wind|sturm|orkan)[ -]?)?$", re.I)

        self._ZERO_PROBABILITY = re.compile(
            r"^\s*(?:ist|sei|beträgt|betraegt|liegt\s+bei|is|equals)\s+"
            r"(?:(?:genau|exakt|exactly)\s+)?(?:null|zero|0(?:[.,]0+)?(?:\s*(?:%|prozent|percent))?)"
            r"(?=\s|[.!?]|$)", re.I)

        self._ATTRIBUTION = re.compile(
            rf"\b(?P<frame>(?:nach|entgegen|gemäß|gemaess)\s+(?:(?:{self._REPORTING_DETERMINER})\s+)?"
            rf"(?:{self._REPORTING_MODIFIER}\s+){{0,3}}"
            r"(?:[^\W\d_][\w’'\-]*[-–])?"
            rf"(?:{self._REPORTING_NOUN})|laut|according\s+to)\b"
            r"(?:\s+(?P<body>[^\W\d_][\w'’\-]*(?:\s+[^\W\d_][\w'’\-]*){0,7}))?", re.I)

        self._POST_ATTRIBUTION = re.compile(
            rf"\b(?:(?:{self._REPORTING_DETERMINER})\s+)?{self._REPORTING_ENTITY}"
            rf"(?:\s+(?:des|der|von|vom)\s+(?:(?:{self._REPORTING_DETERMINER})\s+)?{self._REPORTING_ENTITY})?"
            r"\s+(?:zufolge|nach)\b", re.I)

        self._REGION_EXCEPTION = re.compile(
            r"\b(?:mit\s+ausnahmen?(?:\s+von)?|außer|ausser|ausgenommen|"
            r"nur\s+nicht|nicht\s+aber|except(?:\s+for)?|excluding|with\s+the\s+exception\s+of)\s+", re.I)

    def fragment(self, kind):
        return self.pack.FRAGMENTS.get(kind, r"(?!)")

    @lru_cache(maxsize=512)
    def _region_exclusions(self, text: str) -> tuple[tuple[int, int, str], ...]:
        """Retain the subtracted region as part of its own gust assertion.

        Exception markers are not wind negation and not independent consequence
        nouns. Meteorological conditions and another subject's exceptions stay with
        that subject. A new gust/value starts a separate assertion.
        """
        result = []
        for marker in self._REGION_EXCEPTION.finditer(text):
            end = len(text)
            if boundary := re.search(r",(?!\d)|[;\n!?]", text[marker.end():]):
                end = marker.end() + boundary.start()
            tail = text[marker.end():end]
            if new_claim := self._GUST.search(tail) or self._SPEED.search(tail):
                boundaries = list(self._PHRASE_BREAK.finditer(tail[:new_claim.start()]))
                end = marker.end() + (boundaries[-1].start() if boundaries else new_claim.start())
            # The following forecast predicate is not part of the region noun
            # group. In particular, an exception cannot swallow a gust denial.
            for word in re.finditer(r"\b[^\W\d_][\w'’\-]*", text[marker.end():end]):
                fragment = text[marker.end() + word.start():end]
                predicate_word = word.group(0)
                if (predicate_word[0].islower()
                        or predicate_word.casefold() in {"sind", "ist", "werden", "wird", "können", "kann", "seien"}
                        or self._NEGATED.fullmatch(predicate_word)) and self._PREDICATE.match(fragment):
                    end = marker.end() + word.start()
                    break
            body = text[marker.end():end].strip(" .,:()")
            if not body or self._PREDICATE.match(body):
                continue
            nominal = re.sub(r"^(?:(?:von|der|den|dem|des|die|das)\s+)+", "", body, flags=re.I)
            if self._WEATHER_CONDITION.fullmatch(body) or self._WEATHER_CONDITION.fullmatch("bei " + nominal):
                continue
            speeds = list(self._SPEED.finditer(text[:marker.start()]))
            if speeds:
                bridge = text[speeds[-1].end():marker.start()]
                if subject := self._OTHER_SUBJECT_LINK.search(bridge):
                    words = re.findall(r"[^\W\d_][\w'’\-]*", bridge[subject.end():])
                    if words and not any(self._WIND_ATTRIBUTE.fullmatch(word) for word in words):
                        continue
            result.append((marker.start(), end, body))
        return tuple(result)

    def _excluded_height_membership(self, body: str, elevation) -> bool | None:
        """Three-valued membership: inside, outside, or unverified subregion.

        A single numeric height restriction can prove a window is outside even if
        the region itself is named. Qualitative terrain has no invented elevation
        threshold; coordinated/alternative regions remain unverified.
        """
        if (not isinstance(elevation, (int, float)) or isinstance(elevation, bool) or not math.isfinite(elevation)
                or re.search(r"\b(?:und|oder|and|or|sowie|mit|bei|with|during)\b", body, re.I)):
            return None
        heights = list(self._ALTITUDE.finditer(body))
        if len(heights) != 1:
            return None
        relation, height = self._height_bound(heights[0])
        if height is None:
            return None
        inside = (elevation > height if relation == "gt" else elevation < height if relation == "lt"
                  else elevation >= height if relation == "ge" else elevation <= height)
        if not inside:
            return False
        remaining = self._ALTITUDE.sub(" ", body)
        remaining = re.sub(rf"\b(?:in|im|auf|an|am|von|der|den|dem|des|die|das|allen|{self._HEIGHT_NOUN})\b",
                           " ", remaining, flags=re.I)
        return True if not remaining.strip(" .,:()") else None

    def _source_attributions(self, text: str) -> list[tuple[int, int]]:
        """Bound a source noun group without consuming its forecast predicate."""
        spans = []
        for match in self._ATTRIBUTION.finditer(text):
            end = match.end("frame")
            content = False
            for word in re.finditer(r"[^\W\d_][\w'’\-]*", match["body"] or ""):
                value = word.group(0)
                if (self._PLACE_WORD_END.fullmatch(value) or self._NEGATED.fullmatch(value)
                        or re.fullmatch(self._PREDICATE_LINK, value, re.I) or self._PREDICATE.match(value)
                        or re.fullmatch(self._ABSENCE_STEM, value, re.I)
                        or self._PLACE_START.match(value + " ")
                        or value.casefold() in {"aus", "auf", "ein", "vor"}):
                    break
                content |= not bool(self._PLACE_DETERMINER.fullmatch(value))
                end = match.start("body") + word.end()
            if not content and not re.match(r"(?:nach|entgegen|gemäß|gemaess)\s", match["frame"], re.I):
                continue
            start = match.start()
            prefix = text[:start].rstrip()
            if prefix.endswith(","):
                start = len(prefix) - 1
            if suffix := re.match(r"\s*,", text[end:]):
                end += suffix.end()
            spans.append((start, end))
        for match in self._POST_ATTRIBUTION.finditer(text):
            start, end = match.span()
            prefix = text[:start].rstrip()
            if prefix.endswith(","):
                start = len(prefix) - 1
            if suffix := re.match(r"\s*,", text[end:]):
                end += suffix.end()
            spans.append((start, end))
        merged = []
        for start, end in sorted(spans):
            if merged and start <= merged[-1][1]:
                merged[-1] = merged[-1][0], max(merged[-1][1], end)
            else:
                merged.append((start, end))
        return merged

    def _predicate_denies(self, match) -> bool:
        polarity = match["links"] + " " + (match["forecast"] or match["absence"] or "")
        if match["forecast"]:
            # "definitely not expected" denies the event; "not definitely
            # expected" only denies certainty. A modifier cannot move negation
            # from its own assertion onto the possible gust occurrence.
            polarity = re.sub(rf"\b(?:nicht|not)\s+(?:{self._PREDICATE_MODIFIER})\b", " ", polarity, flags=re.I)
        negated = bool(self._NEGATED.search(polarity))
        # "not excluded" is a possible event; "not expected" is not a forecast.
        return not negated if match["exclusion"] or match["absence"] or match["denial"] else negated

    def _denied_prediction(self, fragment: str) -> bool:
        """Follow only directly connected forecast predicates of the same subject."""
        fragment = fragment.lstrip(" ,:")
        while predicate := self._PREDICATE.match(fragment):
            tail = fragment[predicate.end():]
            if predicate["forecast"] and re.match(r"\s+to\b", tail, re.I) and not re.match(
                    r"\s+to\s+(?:occur|develop|arise|materiali[sz]e|reach|exceed|persist|continue|"
                    r"be\s+(?:observed|reached|recorded|expected|possible|felt|experienced))\b", tail, re.I):
                # An infinitive describing a consequence/action ("not expected to
                # threaten buildings") does not deny occurrence of the gusts.
                return False
            if self._predicate_denies(predicate):
                return True
            fragment = tail.lstrip(" ,:")
        return False

    def _suffix_gust(self, statement: str, speed):
        """Bind a value to a directly following 'in gusts' speed qualifier.

        A separate mean wind is not promoted: the preceding speed field must have
        a grammatical value link, and the following gust noun must not introduce
        its own, different value ("wind 110, in gusts up to 70").
        """
        suffix = self._GUST_AFTER_SPEED.match(statement[speed.end():])
        if suffix is None:
            return None
        prefix = statement[:speed.start()]
        fields = list(self._SPEED_FIELD.finditer(prefix))
        if not fields or not self._VALUE_LINK.fullmatch(prefix[fields[-1].end():]) or self._OTHER_WEATHER.search(prefix):
            return None
        end = speed.end() + suffix.end()
        tail = statement[end:]
        next_speed = self._SPEED.search(tail)
        if next_speed and self._VALUE_LINK.fullmatch(tail[:next_speed.start()]):
            return None
        return next((gust for gust in self._GUST_NOMINAL.finditer(statement, speed.end(), end) if gust.end() == end), None)

    def _wind_is_condition(self, prefix: str) -> bool:
        """A predicate on 'damage during gusts' does not deny the gust event."""
        condition = re.search(
            r"\b(?:bei|durch|with|during|con|durante|in\s+presenza\s+di)\s+(?:(?:stark\w*|schwer\w*|strong|severe)\s+)*"
            r"(?:(?:wind|sturm|orkan)[ -]?)?$", prefix + " ", re.I)
        if condition is None:
            return False
        head = prefix[:condition.start()]
        if not head.strip() and re.match(r"(?:con|durante|in\s+presenza\s+di)\b", condition.group(0), re.I):
            # A fronted 'con raffiche ...' is a circumstance of another event,
            # not the subject of 'non si prevedono danni' that follows it.
            return True
        for start, end in reversed(self._place_phrases(head)):
            head = head[:start] + " " * (end - start) + head[end:]
        head = self._OTHER_SUBJECT_LINK.sub(" ", head)
        words = re.findall(r"[^\W\d_][\w'’\-]*", head)
        return any(not re.fullmatch(self._PREDICATE_LINK, word, re.I)
                   and not self._PLACE_DETERMINER.fullmatch(word)
                   and not self._WIND_ATTRIBUTE.fullmatch(word)
                   and not self._WEATHER_MODIFIER.fullmatch(word) for word in words)

    def _predicate_text(self, statement: str, *, after: int = 0) -> str:
        """Separate assertion adjuncts from predicates, preserving text offsets.

        The same constituent roles decide whether a comma-separated continuation
        completes a gust claim and which verb negates that claim. Unknown places
        remain separately unverified by the geographic policy.
        """
        for start, end, _ in reversed(self._region_exclusions(statement)):
            statement = statement[:start] + " " * (end - start) + statement[end:]
        statement = self._whole_area_text(statement)
        for start, end in reversed(self._source_attributions(statement)):
            statement = statement[:start] + " " * (end - start) + statement[end:]
        for pattern in (self._TIME_BOUND, self._CLOCK_BOUND):
            statement = pattern.sub(lambda match: " " * len(match.group(0)), statement)
        for height in reversed(list(self._ALTITUDE.finditer(statement))):
            end = height.end()
            if height["reference"] and statement[end:end + 1] == ".":
                end += 1  # Include the terminal datum abbreviation dot, not a verb separator.
            statement = statement[:height.start()] + " " * (end - height.start()) + statement[end:]
        for condition in reversed(list(self._WEATHER_CONDITION.finditer(statement, after))):
            if self._OTHER_SUBJECT_LINK.match(condition.group(0)):
                continue  # "with hail not expected" may deny the hail alone.
            statement = statement[:condition.start()] + " " * len(condition.group(0)) + statement[condition.end():]
        for start, end in reversed(self._place_phrases(self._location_text(statement))):
            if start >= after:
                statement = statement[:start] + " " * (end - start) + statement[end:]
        return statement

    def _weather_adjunct(self, text: str) -> bool:
        """A condition can continue wind, but another named subject cannot."""
        if not self._WEATHER_CONDITION.match(text) or self._OTHER_SUBJECT_LINK.match(text):
            return False
        remaining = self._predicate_text(text).strip(" .,:()")
        return not remaining or bool(self._PREDICATE.fullmatch(remaining))

    def _wind_denied(self, statement: str, speed=None, *, header=False) -> bool:
        """Read polarity on the wind assertion, never on another subject's verb."""
        speed = speed or self._SPEED.search(statement)
        statement = self._predicate_text(statement, after=speed.end() if speed else 0)
        subjects = list((self._WIND_SUBJECT if header else self._GUST_NOMINAL).finditer(statement))
        anchor = next((subject for subject in reversed(subjects)
                       if speed is None or subject.end() <= speed.start()), None)
        if anchor is None and speed is not None:
            anchor = self._suffix_gust(statement, speed)
            if anchor is None:
                # A value can precede its noun: "110 km/h Böen" or Turkish
                # "110 km/h rüzgâr hamleleri". Require a direct adjectival link.
                anchor = next((subject for subject in subjects if subject.start() >= speed.end()
                               and re.fullmatch(r"\s*(?:(?:stark\w*|schwer\w*|strong|severe)\s+)*",
                                                statement[speed.end():subject.start()], re.I)), None)
        nominal_denies = False
        prediction_denied = False
        if anchor:
            for absent in self._ABSENT_WIND.finditer(statement):
                if absent.start() <= anchor.start() and absent.end() >= anchor.end():
                    return True
                if absent.end() <= anchor.start() and re.fullmatch(
                        r"\s+(?:mit|with)\s+(?:(?:stark\w*|schwer\w*|strong|severe)\s+)*",
                        statement[absent.end():anchor.start()], re.I):
                    # In "kein Wind mit Böen", the gust noun is the directly
                    # attached property of the absent wind, not a new forecast.
                    return True
            # E.g. "Non sono previste raffiche": the predicate precedes its subject.
            prefix = statement[:anchor.start()].strip()
            if speed and speed.end() <= anchor.start():
                prefix = (statement[:speed.start()] + statement[speed.end():anchor.start()]).strip()
            if self._wind_is_condition(prefix):
                return False
            nominal = self._NOMINAL_WIND_EVENT.search(prefix + " ")
            if nominal:
                # Negation belongs to the nominal wind event, not any preceding
                # consequence noun: "Kein Auftreten von Schäden bei Böen" does not
                # match this direct grammatical link. A negated absence is possible
                # wind; an excluded occurrence and a not-excluded occurrence differ.
                nominal_denies = bool(nominal["negation"]) != (nominal["head"].casefold() in {"ausbleiben", "absence"})
                prefix = prefix[:nominal.start()].strip()
                if nominal["head"].casefold() in {"wahrscheinlichkeit", "probability", "likelihood", "chance"}:
                    tail = statement[max(speed.end(), anchor.end()) if speed else anchor.end():]
                    prediction_denied = bool(self._ZERO_PROBABILITY.match(tail))
            for predicate in self._PREDICATE.finditer(prefix):
                tail = prefix[predicate.end():].strip()
                if re.fullmatch(
                        rf"(?:{self._PREDICATE_LINK}\b\s*)*(?:(?:dass|that|que|che|dat)\s*)?"
                        r"(?:(?:wind|sturm|orkan)[ -]?)?", tail, re.I) and self._predicate_denies(predicate):
                    prediction_denied = True
            # Inversion can put the gust subject between a separable verb and its
            # particle: 'Nach den Berechnungen bleiben <gust value> aus'. Require
            # both halves and only direct grammatical links to that same subject.
            if absence := self._ABSENCE_FRAME.search(prefix + " "):
                tail = statement[max(speed.end(), anchor.end()) if speed else anchor.end():]
                predicate = self._PREDICATE.match(absence.group(0) + " " + tail.lstrip(" ,:"))
                if predicate and predicate["absence"] and self._predicate_denies(predicate):
                    prediction_denied = True
            # The expectation predicate can surround its gust complement:
            # "Es ist nicht mit <gust value> zu rechnen". Require both halves
            # of that grammatical frame; an unrelated "nicht" cannot deny wind.
            frame = self._EXPECTATION_FRAME.search(prefix + " ")
            tail = statement[max(speed.end(), anchor.end()) if speed else anchor.end():]
            if frame:
                predicate = self._PREDICATE.match(frame["links"] + " " + tail.lstrip(" ,:"))
                if predicate and (predicate["forecast"] or "").casefold() == "rechnen" and self._predicate_denies(predicate):
                    prediction_denied = True
            if speed and anchor.end() <= speed.start() and self._denied_prediction(statement[anchor.end():speed.start()].strip()):
                prediction_denied = True
        end = max(speed.end(), anchor.end() if anchor else 0) if speed else anchor.end() if anchor else 0
        prediction_denied |= self._denied_prediction(statement[end:])
        return nominal_denies != prediction_denied

    def _speed_values(self, match):
        lower = float(match["lower"].replace(",", "."))
        upper = float((match["upper"] or match["lower"]).replace(",", "."))
        unit = re.sub(r"\s", "", match["unit"].lower())
        factor = 3.6 if unit == "m/s" else 1.609344 if unit == "mph" else 1.852 if unit.startswith(("kn", "kt")) else 1.0
        if not 0 <= lower <= upper or not all(math.isfinite(v) for v in (lower, upper)) or upper * factor > 500:
            return None
        # Numeric bounds do not interpret sentence polarity. That belongs to the
        # particular wind assertion, independently of other subjects in the text.
        return lower * factor, upper * factor

    def _bounds(self, value: str, *, context_prefix="", match=None):
        match = match or self._SPEED.search(value)
        bounds = self._speed_values(match) if match else None
        if bounds is None:
            return None
        lower, upper = bounds
        # Apply the open bound AFTER conversion, so "less than 25 m/s" stays below
        # 90 km/h as well. The original comparison is retained for display.
        comparison = self._SPEED_COMPARISON.search(f"{context_prefix} {value[:match.start()]}")
        if comparison and comparison.lastgroup == "lt":
            if upper <= 0:
                return None
            upper = math.nextafter(upper, 0)
            # An upper bound alone supplies no forecast minimum.
            lower = min(lower, upper) if match["upper"] else None
        return lower, upper

    def _speed_interval(self, statement: str, match) -> dict:
        """The mathematical speed set, separate from the reported peak value.

        None is an unbounded upper endpoint, never a fabricated gust forecast.
        Exact endpoints and inclusion flags preserve '<', '<=', '>' and '>=' even
        where the display/compatibility tuple uses a rounded or open upper peak.
        """
        lower, upper = self._speed_values(match)
        comparison = self._SPEED_COMPARISON.search(statement[:match.start()])
        operator = comparison.lastgroup if comparison else "eq"
        if match["upper"] is None:
            if operator in {"lt", "le"}:
                lower = 0.0
            elif operator in {"gt", "ge"}:
                upper = None
        return {"lower_kmh": lower, "upper_kmh": upper,
                "lower_inclusive": operator != "gt", "upper_inclusive": operator != "lt"}

    def _location_applies(self, text: str, elevation) -> bool:
        """Verify explicit height bounds; never infer that a window is exposed."""
        exclusions = self._region_exclusions(text)
        for start, end, body in reversed(exclusions):
            if self._excluded_height_membership(body, elevation) is not False:
                return False
            text = text[:start] + " " * (end - start) + text[end:]
        text = self._location_text(text)
        heights = list(self._ALTITUDE.finditer(text))
        remaining = self._ALTITUDE.sub(" ", text)
        if (self._EXPOSED.search(remaining) or self._LOCAL_AREA.search(remaining)
                or self._ONLY_LOCATION.search(remaining) or self._place_phrases(remaining)):
            return False
        for match in heights:
            if (not isinstance(elevation, (int, float)) or isinstance(elevation, bool)
                    or not math.isfinite(elevation)):
                return False
            relation, height = self._height_bound(match)
            if height is None:
                return False
            if relation == "gt":
                applies = elevation > height
            elif relation == "lt":
                applies = elevation < height
            elif relation == "ge":
                applies = elevation >= height
            else:
                applies = elevation <= height
            if not applies:
                return False
        return True

    def _height_number(self, raw: str, relation: str) -> float | None:
        """Read a complete dimensional number, using its grammatical language.

        Grouping has exactly three digits; decimal punctuation is not globally
        removed. Space/apostrophe groups and mixed grouping/decimal notation are
        explicit. A lone ambiguous separator without a language cue stays unknown.
        This parser is deliberately separate from speeds and clock times.
        """
        raw = " ".join(raw.replace("−", "-").replace("’", "'").split())
        sign = -1 if raw.startswith("-") else 1
        raw = raw.lstrip("+-")
        if raw.startswith((".", ",")):
            raw = "0" + raw
        value = None
        if " " in raw or "'" in raw:
            separator = " " if " " in raw else "'"
            if re.fullmatch(rf"[1-9]\d{{0,2}}(?:{re.escape(separator)}\d{{3}})+(?:[.,]\d+)?", raw):
                value = float(raw.replace(separator, "").replace(",", "."))
        elif "." in raw and "," in raw:
            if re.fullmatch(r"[1-9]\d{0,2}(?:\.\d{3})+,\d+", raw):
                value = float(raw.replace(".", "").replace(",", "."))
            elif re.fullmatch(r"[1-9]\d{0,2}(?:,\d{3})+\.\d+", raw):
                value = float(raw.replace(",", ""))
        elif "." in raw or "," in raw:
            separator = "." if "." in raw else ","
            if raw.count(separator) > 1:
                if re.fullmatch(rf"[1-9]\d{{0,2}}(?:{re.escape(separator)}\d{{3}})+", raw):
                    value = float(raw.replace(separator, ""))
            elif re.fullmatch(r"\d+[.,]\d+", raw):
                whole, fraction = raw.split(separator)
                groupable = len(fraction) == 3 and bool(re.fullmatch(r"[1-9]\d{0,2}", whole))
                if relation in {"above", "over", "below", "under", "at least", "up to"}:
                    decimal, grouping = ".", ","
                elif relation in {"au-dessus de", "au-dessous de"}:
                    decimal, grouping = ",", None
                else:
                    decimal, grouping = ",", "."
                if groupable and separator == grouping:
                    value = float(whole + fraction)
                elif separator == grouping and len(fraction) == 3 and whole.startswith("0") and whole != "0":
                    return None  # Invalid grouping must not become a small height.
                elif not groupable or separator == decimal:
                    value = float(raw.replace(",", "."))
        elif raw.isdigit():
            value = float(raw)
        return sign * value if value is not None and math.isfinite(value) else None

    def _height_bound(self, match):
        relation = " ".join(match["relation"].casefold().split())
        relation = re.sub(r"\s+von$", "", relation)
        height = self._height_number(match["height"], relation)
        if match["reference"] and not re.fullmatch(self._SEA_LEVEL_REFERENCE, match["reference"], re.I):
            height = None  # A relative/ellipsoidal height needs a known conversion.
        if height is not None and match["unit"].casefold() in {"feet", "ft"}:
            # The foot is exactly 0.3048 m. Decimal multiplication avoids making
            # "3000 ft" and "914.4 m" different scopes through binary rounding.
            height = float(Decimal(str(height)) * Decimal("0.3048"))
        if relation in {"above", "over", "oberhalb", "über", "ueber", "mehr als", "höher als", "hoher als", "au-dessus de",
                        "por encima de", "al di sopra di", "boven"}:
            return "gt", height
        if relation in {"below", "under", "unterhalb", "unter", "weniger als", "niedriger als", "au-dessous de",
                        "por debajo de", "al di sotto di", "beneden"}:
            return "lt", height
        return ("ge" if relation in {"ab", "mindestens", "at least"} else "le"), height

    @lru_cache(maxsize=512)
    def _location_text(self, text: str) -> str:
        text = self._NON_SPATIAL_PLACE.sub(lambda match: " " * len(match.group(0)), text)
        text = self._whole_area_text(text)
        for pattern in (self._CALENDAR_TIME, self._DATE_TEXT, self._RELATIVE_TIME):
            text = pattern.sub(lambda match: " " * len(match.group(0)), text)
        # "also in higher areas" adds an example to an otherwise general claim.
        # It does not have the restrictive meaning of "only in higher areas".
        text = re.sub(
            rf"\b(?:auch|ebenfalls|selbst|also|including)\s+(?:{self._LOCAL_AREA.pattern})",
            lambda match: " " if self._SPEED.search(text[:match.start()]) else match.group(0),
            text, flags=re.I)
        for start, end in reversed(self._place_phrases(text)):
            if self._place_on_other_subject(text, start, end):
                text = text[:start] + " " * (end - start) + text[end:]
                continue
            addition = re.search(r"\b(?:auch|ebenfalls|selbst|also|including)\s*$", text[:start], re.I)
            if addition and self._SPEED.search(text[:addition.start()]):
                text = text[:addition.start()] + " " * (end - addition.start()) + text[end:]
        return text

    def _whole_area_text(self, text: str) -> str:
        """Mask universal CAP-area coverage only when its quantifier is intact.

        "Not everywhere" and "almost the entire area" do not confirm the window's
        membership. Named regions and trailing restrictions remain in the text.
        """
        for match in reversed(list(self._WHOLE_WARNING_AREA.finditer(text))):
            if re.search(r"\b(?:nicht|not|fast|beinahe|nahezu|annähernd|almost|nearly)\s*$",
                         text[:match.start()], re.I):
                continue
            text = text[:match.start()] + " " * (match.end() - match.start()) + text[match.end():]
        return text

    def _place_on_other_subject(self, text: str, start: int, end: int) -> bool:
        """Do not transfer the place of a consequence/condition onto the gusts."""
        speeds = list(self._SPEED.finditer(text[:start]))
        if speeds:
            bridge = text[speeds[-1].end():start]
            if subject := self._OTHER_SUBJECT_LINK.search(bridge):
                words = re.findall(r"[^\W\d_][\w'’\-]*", bridge[subject.end():])
                if words and not any(self._WIND_ATTRIBUTE.fullmatch(word) for word in words):
                    return True
        elif self._GUST.search(text[end:]):
            # "Keine Schäden im Harz bei Böen 110" describes where damage is
            # absent. A leading "Im Harz ... Böen 110" has no other subject.
            prefix = text[:start].strip()
            tail = text[end:]
            if prefix and re.search(rf"\b(?:bei|mit|durch|with|during)\s+(?:{self._GUST.pattern})", tail, re.I):
                return not re.fullmatch(rf"(?:{self._PREDICATE_LINK}\b\s*)*", prefix, re.I)
        return False

    @lru_cache(maxsize=512)
    def _place_phrases(self, text: str) -> tuple[tuple[int, int], ...]:
        """Read locative noun phrases, retaining unknown places as unverified.

        Forecast verbs, numeric values and new weather subjects delimit the noun
        phrase. Temporal/manner constructions are excluded by their grammatical
        role rather than by enumerating geographic names.
        """
        masked = text
        for pattern in (self._ALTITUDE, self._TIME_BOUND, self._CLOCK_BOUND, self._TIME_HINT, self._NON_SPATIAL_PLACE, self._WEATHER_CONDITION):
            masked = pattern.sub(lambda match: " " * len(match.group(0)), masked)
        masked = self._whole_area_text(masked)
        result = []
        for preposition in self._PLACE_START.finditer(masked):
            match = self._PLACE_PHRASE.match(masked, preposition.start())
            if match is None:
                continue
            words = list(re.finditer(r"[^\W\d_][\w'’\-]*", match["body"]))
            end = None
            content = False
            modifiers = []
            preposition_word = preposition.group(0).strip().casefold()
            connector = {"zwischen": ("und",), "between": ("and",), "von": ("bis", "nach"),
                         "from": ("to",)}.get(preposition_word, ())
            requires_pair = preposition_word in {"von", "from"}
            paired = False
            for index, word in enumerate(words):
                value = word.group(0)
                if self._WIND_NOUN.fullmatch(value) or self._WEATHER_NOUN.fullmatch(value):
                    if all(self._WEATHER_MODIFIER.fullmatch(modifier) for modifier in modifiers):
                        content = False  # "bei starkem Wind" is a condition, not a place.
                    break
                if (self._PLACE_WORD_END.fullmatch(value) or self._NEGATED.fullmatch(value)) and not (
                        content and value.casefold() in {"von", "of"}):
                    following = words[index + 1].group(0) if index + 1 < len(words) else ""
                    if (connector and content and value.casefold() in connector and following
                            and not (self._PLACE_WORD_END.fullmatch(following) or self._WIND_NOUN.fullmatch(following)
                                     or self._WEATHER_NOUN.fullmatch(following))):
                        end = match.start("body") + word.end()
                        connector = None
                        paired = True
                        continue
                    break
                if not self._PLACE_DETERMINER.fullmatch(value):
                    content = True
                    modifiers.append(value)
                end = match.start("body") + word.end()
            if content and end is not None and (not requires_pair or paired):
                result.append((match.start(), end))
        return tuple(result)

    def _location_adjunct(self, text: str) -> bool:
        """Only a place-only fragment can complete the previous wind assertion."""
        if self._SPEED.search(text):
            return False  # A dimensional value is an assertion, not shared scope.
        exclusions = self._region_exclusions(text)
        if exclusions:
            remaining = text
            for start, end, _ in reversed(exclusions):
                remaining = remaining[:start] + " " * (end - start) + remaining[end:]
            if not remaining.strip(" .,:()"):
                return True
        scope = self._location_text(text)
        spans = self._place_phrases(scope)
        if not spans:
            return self._has_location(text) and bool(self._LOCATION_START.match(text))
        modifiers = r"\b(?:nur|ausschlie[ßs]lich|lediglich|only|solely|seulement|uniquement|solo|solamente|alleen|auch|also|und|oder|and|or|et|y|e)\b"
        prefix = re.sub(modifiers, " ", scope[:spans[0][0]], flags=re.I).strip(" .,:()")
        for start, end in reversed(spans):
            scope = scope[:start] + " " * (end - start) + scope[end:]
        scope = re.sub(modifiers, " ", scope, flags=re.I)
        if not scope.strip(" .,:()"):
            return True
        # A longer/partially understood place phrase stays restrictive. Only a
        # clearly separate assertion may detach it; a noun-phrase length limit must
        # not turn "im ... Randgebiet mit Ausnahme ..." into general wind.
        return not prefix and not (self._PREDICATE.search(scope) or self._NEGATIVE_SUBJECT.search(scope)
                                   or self._OTHER_WEATHER.search(scope) or self._WIND_SUBJECT.search(scope))

    def _has_location(self, text: str) -> bool:
        if self._region_exclusions(text):
            return True
        text = self._location_text(text)
        return bool(self._ALTITUDE.search(text) or self._EXPOSED.search(text)
                    or self._LOCAL_AREA.search(text) or self._ONLY_LOCATION.search(text) or self._place_phrases(text))

    def _location_key(self, text: str) -> str:
        if self._region_exclusions(text):
            return "excluded:" + text.casefold()
        text = self._location_text(text)
        heights = list(self._ALTITUDE.finditer(text))
        remaining = self._ALTITUDE.sub(" ", text)
        if heights and not (self._EXPOSED.search(remaining) or self._LOCAL_AREA.search(remaining)
                            or self._ONLY_LOCATION.search(remaining) or self._place_phrases(remaining)):
            bounds = list(map(self._height_bound, heights))
            if any(height is None for _, height in bounds):
                return "unresolved_height:" + text.casefold()
            return "height:" + "|".join(sorted(f"{relation}:{height:.17g}" for relation, height in bounds))
        if self._has_location(text):
            return "local:" + text.casefold()
        return "general"

    def _time_text(self, text: str) -> str:
        """Resolve measured speed/height roles before looking for temporal numbers.

        A complete height comparison includes its unit and optional preposition.
        Bare or otherwise unresolved numbers remain available to the conservative
        time parser; they do not acquire an assumed clock or elevation.
        """
        return self._ALTITUDE.sub(" ", self._SPEED.sub(" ", text))

    def _has_time(self, text: str) -> bool:
        return bool(self._TIME_HINT.search(self._time_text(text)))

    def _time_adjunct(self, text: str) -> bool:
        """A time-only fragment can qualify wind; another subject's time cannot."""
        if not self._has_time(text):
            return False
        remaining = self._CLOCK_BOUND.sub(" ", self._TIME_BOUND.sub(" ", text))
        remaining = self._CALENDAR_TIME.sub(" ", self._DATE_TEXT.sub(" ", self._RELATIVE_TIME.sub(" ", remaining)))
        remaining = re.sub(
            r"\b(?:nur|erst|auch|only|solely|later|today|tomorrow|yesterday|tonight|"
            r"sp[äa]ter|morgen|heute|gestern|[üu]bermorgen|zuvor|vorher|anschlie[ßs]end|"
            r"abends|nachts|nachmittags|am\s+(?:abend|morgen|nachmittag)|in\s+der\s+nacht)\b",
            " ", remaining, flags=re.I)
        return not remaining.strip(" .,:()")

    def _statement_period(self, text: str, record, *, include_constraints=False):
        """Resolve explicit times, retaining ambiguity rather than guessing a date.

        ISO times carry their own offset. Clock times require an explicit time zone
        and a single calendar day in that zone. CAP UTC metadata alone does not tell
        us which local time zone a human-language clock time refers to.
        The reference never moves with the polling clock.
        """
        start = aware(getattr(record, "onset", None))
        end_values = [aware(getattr(record, key, None)) for key in ("expires", "event_end")]
        end = min(v for v in end_values if v is not None) if any(end_values) else None
        constraints = []

        def result(certain):
            if start is not None and _lead_start(start) is None:
                certain = False
            period = (start, end, certain)
            return (*period, constraints) if include_constraints else period

        remaining = self._time_text(text)
        for match in self._TIME_BOUND.finditer(remaining):
            stamp = aware(match["stamp"])
            if stamp is None:
                return result(False)
            bound = "ends" if match["relation"].casefold() in {"bis", "until", "before"} else "onset"
            constraints.append({"bound": bound, "value": stamp.isoformat(), "text": match.group(0)})
            if match["relation"].casefold() in {"bis", "until", "before"}:
                end = min(end, stamp) if end else stamp
            else:
                start = max(start, stamp) if start else stamp
        remaining = self._TIME_BOUND.sub(" ", remaining)
        clocks = list(self._CLOCK_BOUND.finditer(remaining))
        if clocks:
            for match in clocks:
                if not match["zone"]:
                    return result(False)
                offset = {"utc": 0, "gmt": 0, "cet": 1, "mez": 1, "cest": 2, "mesz": 2}[match["zone"].casefold()]
                zone = timezone(timedelta(hours=offset))
                reference = aware(getattr(record, "onset", None)) or aware(getattr(record, "effective", None))
                try:
                    if reference is None or end is None:
                        return result(False)
                    local_start, local_end = reference.astimezone(zone), end.astimezone(zone)
                    if local_start.date() != local_end.date():
                        return result(False)
                    stamp = local_start.replace(hour=int(match["hour"]), minute=int(match["minute"] or 0),
                                                second=0, microsecond=0).astimezone(timezone.utc)
                except (ValueError, OverflowError):
                    return result(False)
                bound = "ends" if match["relation"].casefold() in {"bis", "until", "before"} else "onset"
                constraints.append({"bound": bound, "value": stamp.isoformat(), "text": match.group(0)})
                if match["relation"].casefold() in {"bis", "until", "before"}:
                    end = min(end, stamp) if end else stamp
                else:
                    start = max(start, stamp) if start else stamp
            remaining = self._CLOCK_BOUND.sub(" ", remaining)
        certain = not self._TIME_HINT.search(remaining) and not (start and end and start >= end)
        return result(certain)

    def _gust_clauses(self, value):
        if not isinstance(value, str):
            return []
        # Preserve paragraph boundaries while removing markup and normalizing text.
        value = re.sub(r"<\s*/?\s*(?:br|p|div)\b[^>]*>", ";", value, flags=re.I)
        value = unescape(re.sub(r"</?[a-zA-Z][^>]*>", " ", value))
        heights = list(self._ALTITUDE.finditer(value))
        parts = []
        start = 0
        for boundary in self._CLAUSE_BREAK.finditer(value):
            if any(height.start() <= boundary.start() < height.end() for height in heights):
                continue  # A datum abbreviation such as "ü. NN" belongs together.
            if any(height["reference"] and height.end() + 1 == boundary.start()
                   and value[height.end():boundary.start()] == "." for height in heights) and (
                    self._TIME_HINT.match(value[boundary.end():]) or self._PREDICATE.match(value[boundary.end():])):
                continue
            parts.append(value[start:boundary.start()])
            start = boundary.end()
        parts.append(value[start:])
        return [plain_text(part) for part in parts if plain_text(part)]

    def _gust_text(self, clause: str, match) -> str:
        comparison = self._SPEED_COMPARISON.search(clause[:match.start()])
        if comparison:
            return clause[comparison.start():match.end()].strip()
        sign = re.search(r"(?:<=|>=|[<>≤≥])\s*$", clause[:match.start()])
        return (sign.group(0).strip() if sign else "") + match.group(0)

    def _wind_statements(self, sentence: str, *, header=False, unbound: list[str] | None = None, subjects=None) -> list[str]:
        """Associate each coordinated value with its own subject and modifiers.

        A new value can inherit the gust subject ("110, exposed 140"). A trailing
        qualification without its own value still belongs to the preceding value
        ("110, only on summits"). Other weather subjects do not negate wind.
        """
        subject = subjects or (self._WIND_SUBJECT if header else self._GUST)
        speeds = list(self._SPEED.finditer(sentence))
        protected = speeds + list(self._TIME_BOUND.finditer(sentence)) + list(self._CLOCK_BOUND.finditer(sentence))
        suffixes = [(speed.start(), gust.end()) for speed in speeds
                    if (gust := self._suffix_gust(sentence, speed)) is not None]
        places = self._place_phrases(self._location_text(sentence))
        attributions = self._source_attributions(sentence)
        conditions = list(self._WEATHER_CONDITION.finditer(sentence))
        exclusions = self._region_exclusions(sentence)
        parts = []
        start = 0
        for boundary in self._PHRASE_BREAK.finditer(sentence):
            if any(condition.start() <= boundary.start() < condition.end() for condition in conditions):
                continue  # A coordinated condition cannot detach the wind predicate.
            if any(start <= boundary.start() < end for start, end, _ in exclusions):
                continue  # Keep the subtraction and its coordinated region intact.
            if any(start <= boundary.start() < end for start, end in attributions):
                continue
            if any(value.start() < boundary.start() < value.end() for value in protected):
                continue  # Do not split a speed range or an offset-aware time.
            if any(start < boundary.start() < end for start, end in suffixes):
                continue  # Keep "110 km/h, insbesondere in Böen" attached.
            if any(start < boundary.end() < end for start, end in places):
                continue  # E.g. Spanish/French "en <place>" is not a conjunction.
            parts.append(sentence[start:boundary.start()].strip())
            start = boundary.end()
        parts.append(sentence[start:].strip())
        statements = []
        inherited = False
        relative_on_wind = False
        pending = ""
        for index, raw in enumerate(parts):
            part = raw
            # A wind-like substring inside an already parsed place name (e.g.
            # Gustavsburg) is not a new gust subject and must not detach its place.
            local_names = self._place_phrases(self._location_text(part))
            anchor = next((candidate for candidate in subject.finditer(part)
                           if not any(start <= candidate.start() < end for start, end in local_names)), None)
            speed = self._SPEED.search(part)
            other = self._OTHER_WEATHER.search(part)
            if not anchor and speed is None and self._weather_adjunct(part):
                # A shared condition and its gust predicate cannot disappear as
                # an independent weather subject merely because of a comma.
                following = next((p for p in parts[index + 1:] if p), "")
                if not statements or self._SPEED.search(following):
                    pending = f"{pending} {part}".strip()
                else:
                    statements[-1] += f" {part}"
                continue
            if not anchor and speed is None and self._region_exclusions(part) and self._location_adjunct(part):
                if statements:
                    statements[-1] += f" {part}"
                else:
                    pending = f"{pending} {part}".strip()
                continue
            if not anchor and other and (speed is None or other.start() < speed.start()):
                relative_on_wind = False
                continue
            if (not anchor and speed is None and self._NEGATIVE_SUBJECT.search(part)
                    and not self._WIND_REFERENCE.search(part)):
                # A separate negated subject ("no icing", "keine Glätte") is an
                # independent statement even when its vocabulary is not listed.
                relative_on_wind = False
                continue
            if not anchor and speed and (self._WIND.search(part) or not inherited):
                # A value with no gust subject cannot be promoted to gusts or
                # carried forward as shared location/time context. Any preceding
                # pending adjunct belongs to that value, not the next gust claim.
                if unbound is not None and not self._WIND.search(part) and (
                        self._VALUE_LINK.fullmatch(part[:speed.start()]) or self._STRICT_UPPER.search(part[:speed.start()])
                        or self._LOCATION_START.match(part) or self._location_adjunct(part[:speed.start()])
                        or self._time_adjunct(part[:speed.start()])):
                    unbound.append(f"{pending} {part}".strip())
                inherited = False
                relative_on_wind = False
                pending = ""
                continue
            if not anchor and speed and not (self._VALUE_LINK.fullmatch(part[:speed.start()])
                    or self._STRICT_UPPER.search(part[:speed.start()])
                    or self._LOCATION_START.match(part) or self._location_adjunct(part[:speed.start()])
                    or self._time_adjunct(part[:speed.start()])):
                # A number with an independently named subject does not inherit
                # "gusts" merely because a previous clause mentioned gusts.
                relative_on_wind = False
                continue
            if anchor or speed and inherited:
                inherited = True
                relative_on_wind = True
                if (not anchor and statements and self._SPEED.search(statements[-1]) is None
                        and not self._has_location(statements[-1]) and not self._has_time(statements[-1])
                        and not self._NEGATED.search(statements[-1])):
                    statements[-1] += f" {pending} {part}"
                else:
                    statements.append(f"{pending} {part}".strip())
                pending = ""
            elif self._location_adjunct(part) or self._time_adjunct(part):
                # A location-only fragment before another speed qualifies that
                # next value; otherwise it is a suffix of the preceding value.
                following = next((p for p in parts[index + 1:] if p), "")
                if self._SPEED.search(following) or not statements:
                    pending = f"{pending} {part}".strip()
                else:
                    statements[-1] += f" {part}"
            elif (statements and inherited and (relative_on_wind or not self._WIND_REFERENCE.match(part))
                  and self._PREDICATE.match(self._predicate_text(part).lstrip(" ,:"))):
                # Only a directly linked forecast predicate completes the claim.
                # "Schäden sind nicht auszuschließen" and "lightning is not
                # expected" have their own subjects and are left independent;
                # a relative clause with its own object also leaves the main
                # forecast predicate available ("gusts, which cause damage, are
                # excluded"). A wind relative such as "which are not expected"
                # matches the same predicate grammar and stays attached.
                statements[-1] += f" {part}"
            elif not inherited:
                # A comma-separated independent subject cannot become a prefix of
                # the next wind event merely because its vocabulary is unknown.
                # Pure adjuncts were handled above; source/predicate prefixes can
                # still precede the gust noun ('not expected: gusts ...').
                bridge = self._predicate_text(part).strip(" .,:()")
                words = re.findall(r"[^\W\d_][\w'’\-]*", bridge)
                if (not bridge or self._PREDICATE.match(bridge) or self._NEGATED.fullmatch(bridge)
                        or self._EXPECTATION_FRAME.search(bridge + " ") or self._NOMINAL_WIND_EVENT.search(bridge + " ")
                        or self._VALUE_LINK.fullmatch(bridge) or self._WEATHER_MODIFIER.fullmatch(bridge)
                        or words and all(re.fullmatch(self._PREDICATE_LINK, word, re.I) for word in words)):
                    pending = f"{pending} {part}".strip()
                else:
                    pending = ""
            elif not self._WIND_REFERENCE.match(part) and self._predicate_text(part).strip(" .,:()"):
                # A newly named noun is the antecedent of its own relative clause.
                # An inserted relative on the gusts ('which cause damage') keeps
                # the gust antecedent; 'damage, which ...' cannot borrow it.
                relative_on_wind = False
        if pending and statements:
            statements[-1] += f" {pending}"
        return statements

    def _header_applies(self, title: str, elevation, *, reject_negated=False) -> bool:
        statements = [statement for sentence in self._gust_clauses(title)
                      for statement in self._wind_statements(sentence, header=True)]
        if not statements:
            return self._location_applies(title, elevation)
        return any(self._location_applies(statement, elevation)
                   and (not reject_negated or not self._wind_denied(statement, header=True)) for statement in statements)

    def _header_has_denial(self, title: str) -> bool:
        """An absence assertion is not a global place/time qualifier of gusts."""
        return any(self._wind_denied(statement, header=True) for sentence in self._gust_clauses(title)
                   for statement in self._wind_statements(sentence, header=True))

    @lru_cache(maxsize=512)
    def _wind_header_context(self, title: str) -> str:
        """Only generic wind statements or pure untyped adjuncts qualify gusts.

        Numeric headlines already have their own evidence and scope. Independently
        named hazards cannot donate context to wind. Whole-word subjects also keep
        a compound such as 'Sturmflut' from becoming a generic storm qualifier.
        """
        wind_statements = []
        for sentence in self._gust_clauses(title):
            for statement in self._wind_statements(sentence, header=True, subjects=self._WIND_HEADER_SUBJECT):
                for subject in self._WIND_HEADER_SUBJECT.finditer(statement):
                    if ((subject.start() and re.match(r"\w", statement[subject.start() - 1]))
                            or subject.end() < len(statement) and re.match(r"\w", statement[subject.end()])
                            or self._wind_is_condition(statement[:subject.start()])):
                        continue
                    wind_statements.append(statement)
                    break
        if wind_statements:
            return "; ".join(statement for statement in wind_statements if not self._SPEED.search(statement))
        return title if self._location_adjunct(title) or self._time_adjunct(title) else ""

    def _assertion_context(self, statement: str, record, elevation, source: str) -> dict:
        """Parse the complete claim before inheriting context or comparing claims.

        Declared temporal bounds stay separate from CAP defaults and later inherited
        context. Source labels identify fields; assertion IDs identify claims.
        """
        start, end, certain, constraints = self._statement_period(statement, record, include_constraints=True)
        exclusions = self._region_exclusions(statement)
        if any(self._TIME_HINT.search(self._time_text(body)) for _, _, body in exclusions):
            certain = False  # A region exception's time is not a proven gust onset.
        directions = sorted({constraint["bound"] for constraint in constraints})
        declared = {key: (max if key == "onset" else min)(constraint["value"] for constraint in constraints
                                                        if constraint["bound"] == key) for key in directions}
        timed = self._has_time(statement)
        located = self._has_location(statement)
        general = [*self._WHOLE_WARNING_AREA.finditer(statement),
                   *re.finditer(r"\b(?:allgemein|generally|overall)\b", statement, re.I)]
        explicit_general = any(not self._place_on_other_subject(statement, match.start(), match.end()) for match in general)
        return {"source": source, "statement": statement,
                "scope": self._location_key(statement), "location_verified": self._location_applies(statement, elevation),
                "location_explicit": located or explicit_general,
                "onset": start, "ends": end, "time_verified": certain,
                "time_explicit": timed, "time_bounds": directions, "time_source": source if timed else "CAP",
                "declared_period": declared, "time_period": dict(declared), "time_constraints": constraints,
                "location_exclusions": [statement[start:end] for start, end, _ in exclusions],
                "weather_conditions": [match.group(0) for match in self._WEATHER_CONDITION.finditer(statement)],
                "height_references": [match["reference"] for match in self._ALTITUDE.finditer(statement) if match["reference"]],
                "explicit_scope": located or timed}

    def _gust_evidence(self, text: str, record, elevation, source: str, *, unbound_contexts: list[dict] | None = None) -> list[dict]:
        evidence = []
        for sentence in self._gust_clauses(text):
            unbound = []
            for statement in self._wind_statements(sentence, unbound=unbound):
                common = self._assertion_context(statement, record, elevation, source)
                gusts = list(self._GUST_NOMINAL.finditer(statement))
                speeds = list(self._SPEED.finditer(statement))
                if not speeds and self._wind_denied(statement):
                    evidence.append({**common, "min": None, "max": None, "text": "", "denied": True})
                for match in speeds:
                    previous = next((gust for gust in reversed(gusts) if gust.end() <= match.start()), None)
                    suffix = self._suffix_gust(statement, match) if previous is None else None
                    earlier_speed = next((speed for speed in reversed(speeds) if speed.end() <= match.start()), None)
                    if earlier_speed and suffix is None and (previous is None or previous.start() < earlier_speed.end()):
                        bridge = statement[earlier_speed.end():match.start()]
                        if not (self._VALUE_LINK.fullmatch(bridge) or self._STRICT_UPPER.search(bridge)):
                            # Another noun's speed/limit is not a second forecast:
                            # "gusts 70 km/h under the threshold of 110 km/h".
                            continue
                    prefix = statement[previous.end():match.start()] if previous else statement[:match.start()]
                    if len(prefix) > 110 or self._OTHER_WEATHER.search(prefix) or suffix is None and self._WIND.search(prefix):
                        continue
                    bounds = self._bounds(statement, match=match)
                    if bounds:
                        evidence.append({**common, "min": bounds[0], "max": bounds[1],
                                         "speed_interval": self._speed_interval(statement, match),
                                         "text": self._gust_text(statement, match),
                                         "denied": self._wind_denied(statement, match)})
            if unbound_contexts is not None:
                # These are quantity contexts, not gust evidence. A flat parameter
                # may identify an exactly matching value as gusts; its description
                # still supplies that value's own place, height, time and polarity.
                for statement in unbound:
                    common = self._assertion_context(statement, record, elevation, source)
                    for match in self._SPEED.finditer(statement):
                        bounds = self._bounds(statement, match=match)
                        if bounds:
                            unbound_contexts.append({**common, "min": bounds[0], "max": bounds[1],
                                                     "speed_interval": self._speed_interval(statement, match),
                                                     "text": self._gust_text(statement, match), "unbound_context": True,
                                                     "denied": self._wind_denied(statement, match)})
        return evidence

    def _header_context(self, evidence: list[dict], headers: list[dict], titles: dict, record, elevation) -> list[dict]:
        """Inherit only missing context of the same event and quantity.

        Numeric headlines are separate claims, not global location filters. A bare
        matching quantity can inherit their missing scope; an independently stated
        general/location/time assertion keeps its own context. Only generic wind
        statements and untyped adjuncts supply broader wind-message context.
        """
        for source, title in titles.items():
            numeric = [claim for claim in headers if claim["source"] == source
                       and not claim["denied"] and claim["max"] is not None]
            resolved = []
            for item in evidence:
                can_inherit = item["source"] not in {"headline", "event"} and not item["location_explicit"]
                matches = [] if not can_inherit else [
                    context for context in numeric if context["location_explicit"]
                    and _parameter_identifies_quantity(item, context)]
                ambiguous = False
                if can_inherit and not matches:
                    # Without an independent location assertion, an unpaired value
                    # must not silently erase a scoped wind heading. Conflicting
                    # possible defaults remain unresolved rather than invented.
                    matches = [context for context in numeric if context["location_explicit"]
                               and context["scope"] != "general"]
                    ambiguous = len({context["scope"] for context in matches}) > 1
                if not matches:
                    resolved.append(item)
                    continue
                for context in matches:
                    linked = dict(item)
                    for key in ("scope", "location_verified", "location_explicit", "location_exclusions", "height_references"):
                        linked[key] = context[key]
                    linked["scope_from_header"] = context["statement"]
                    linked["explicit_scope"] |= context["explicit_scope"]
                    if ambiguous:
                        linked["location_verified"] = False
                        linked["scope"] = "unresolved_header_scope"
                    resolved.append(linked)
            evidence = resolved
            contexts = [claim for claim in numeric if claim["time_explicit"]]
            if contexts:
                resolved = []
                for item in evidence:
                    matches = [] if item["time_explicit"] else [context for context in contexts
                                if _same_speed(item, context) and _polarity_locations_overlap(item, context)]
                    if not matches:
                        resolved.append(item)
                        continue
                    for context in matches:
                        linked = dict(item)
                        for key in ("onset", "ends", "time_verified", "time_explicit", "time_bounds", "time_source",
                                    "time_period", "time_constraints"):
                            linked[key] = context[key]
                        linked["time_verified"] &= item["time_verified"]
                        linked["time_from_header"] = context["statement"]
                        resolved.append(linked)
                evidence = resolved
            title = self._wind_header_context(title)
            if not title or self._header_has_denial(title):
                continue
            if not self._header_applies(title, elevation):
                for item in evidence:
                    item["location_verified"] = False
                    item["scope_from_header"] = title
            if not self._has_time(title):
                continue
            start, end, certain = self._statement_period(title, record)
            context = self._assertion_context(title, record, elevation, source)
            for item in evidence:
                joined_start = max(v for v in (item["onset"], start) if v) if item["onset"] or start else None
                joined_end = min(v for v in (item["ends"], end) if v) if item["ends"] or end else None
                empty = bool(joined_start and joined_end and joined_start >= joined_end)
                overwrites = any(key in item["time_bounds"] and key in context["time_bounds"]
                                 and item[key] != bound and joined != item[key]
                                 for key, bound, joined in (("onset", start, joined_start), ("ends", end, joined_end)))
                if empty or overwrites:
                    item["time_conflict"] = True
                    item["time_verified"] = False
                else:
                    item["onset"], item["ends"] = joined_start, joined_end
                    item["time_verified"] &= certain
                item["time_from_header"] = title
                item["time_explicit"] |= context["time_explicit"]
                item["time_bounds"] = sorted(set(item["time_bounds"]) | set(context["time_bounds"]))
                item["time_period"] = {**context["time_period"], **item["time_period"]}
        return evidence

    def extract_text(self, record, *, elevation=None) -> TextFindings:
        """Return only local-language text assertions and their own contexts."""
        titles = {key: plain_text(getattr(record, key, "")) for key in ("headline", "event")}
        # An event label is separate metadata, not a continuation of the headline's
        # sentence. A generic "Wind" event must not erase a headline qualification.
        headers = []
        for source, title in titles.items():
            claims = self._gust_evidence(title, record, elevation, source)
            if not claims and not self._header_applies(title, elevation, reject_negated=True):
                # A generic negated wind heading may have no numeric value. Keep
                # its assertion as evidence rather than erasing the other fields.
                for sentence in self._gust_clauses(title):
                    for statement in self._wind_statements(sentence, header=True):
                        if self._wind_denied(statement, header=True) and not self._SPEED.search(statement):
                            claims.append({**self._assertion_context(statement, record, elevation, source),
                                           "min": None, "max": None, "text": "", "denied": True})
            headers.extend(claims)
        unbound_contexts = []
        description = self._gust_evidence(getattr(record, "description", ""), record, elevation, "description",
                                     unbound_contexts=unbound_contexts)
        return TextFindings(tuple(headers), tuple(description), tuple(unbound_contexts), titles)

    def parameter_text(self, name, value, record, elevation):
        """Legacy free-form parameter text; never handles profiled quantities."""
        if not isinstance(name, str) or self._SPEED.search(name):
            return []
        if not isinstance(value, str):
            return []
        if not (self._GUST.search(name) or self._GUST.search(value)):
            return []
        return self._gust_evidence(f"{name} {plain_text(value)}", record, elevation, "parameter")


@lru_cache(maxsize=16)
def _text_grammar(pack):
    return WarningTextGrammar(pack)


@lru_cache(maxsize=1)
def _header_grammar():
    # Headers can contain multiple event/language contexts. This instance only
    # resolves those contexts; it never supplies numeric text assertions.
    keys = {key for pack in installed() for key in pack.FRAGMENTS}
    combined = SimpleNamespace(CODE="header_context", FRAGMENTS={key: fragments(key) for key in keys})
    return WarningTextGrammar(combined)


def _distinct_text_claims(claims):
    result = []
    for item in claims:
        duplicate = next((previous for previous in result
                          if all(previous.get(key) == item.get(key) for key in
                                 ("source", "statement", "min", "max", "denied", "scope", "onset", "ends",
                                  "time_verified", "location_verified", "speed_interval"))), None)
        if duplicate is None:
            result.append(item)
    return result


def _extract_warning_text(record, primary, *, elevation=None):
    """Merge text-only findings before inheriting cross-field context.

    A trusted CAP quantity never enters this function. An unprofiled free-form
    parameter is language evidence and may inherit a matching textual scope.
    """
    if primary is None:
        return []
    text = " ".join(plain_text(getattr(record, key, "")) for key in ("headline", "event", "description"))
    packs = [pack for pack in installed() if pack is primary or re.search(
        r"\b(?:" + pack.FRAGMENTS.get("gust", r"(?!)") + r")\b", text, re.I)]
    headings, descriptions, unbound, titles = [], [], [], {}
    for pack in packs:
        findings = pack.extract(record, elevation=elevation)
        for group in (findings.headers, findings.descriptions, findings.unbound):
            for item in group:
                item["text_parser"] = pack.CODE
                item["evidence_kind"] = "warning_text"
        headings.extend(findings.headers)
        descriptions.extend(findings.descriptions)
        unbound.extend(findings.unbound)
        titles.update(findings.titles)
    headings = _distinct_text_claims(headings)
    descriptions = _distinct_text_claims(descriptions)
    unbound = _distinct_text_claims(unbound)
    parameters = getattr(record, "parameters", {}) or {}
    linked_parameters = []
    for name, raw in parameters.items() if isinstance(parameters, dict) else ():
        if not isinstance(name, str) or not _header_grammar()._GUST.search(name) or _header_grammar()._SPEED.search(name):
            continue
        for value in raw if isinstance(raw, list) else [raw]:
            if not isinstance(value, str):
                continue
            claims = []
            value_packs = [pack for pack in installed() if re.search(
                r"\b(?:" + pack.FRAGMENTS.get("gust", r"(?!)") + r")\b", value, re.I)]
            for pack in value_packs or installed():
                items = _text_grammar(pack).parameter_text(name, value, record, elevation)
                for item in items:
                    item["text_parser"] = pack.CODE
                    item["evidence_kind"] = "parameter_text"
                claims.extend(items)
            for item in _distinct_text_claims(claims):
                item["parameter"] = name
                linked_parameters.extend(_bind_parameter_context(item, descriptions, unbound))
    return _header_grammar()._header_context(headings + descriptions + linked_parameters,
                                            headings, titles, record, elevation)


def _bind_parameter_context(item, description, unbound_contexts):
    if not item["explicit_scope"] and (description or unbound_contexts):
        contexts = description + [claim for claim in unbound_contexts if _parameter_identifies_quantity(item, claim)]
        relevant = [claim for claim in contexts if not claim["denied"] or _speed_sets_overlap(item, claim)]
        matches = [claim for claim in relevant if _same_speed(item, claim)
                   or claim.get("unbound_context") and _parameter_identifies_quantity(item, claim)]
        guarded = [claim for claim in relevant if claim["denied"] or claim["explicit_scope"] or claim["min"] is None]
        general = [claim for claim in matches if not claim["denied"] and not claim["explicit_scope"]]
        contexts = general or matches
        if not contexts and guarded:
            contexts = relevant
        if contexts:
            resolved = []
            for context in contexts:
                linked = dict(item)
                for key in ("scope", "location_verified", "location_explicit", "onset", "ends", "time_verified", "denied",
                            "time_explicit", "time_bounds", "time_source", "time_period", "time_constraints",
                            "location_exclusions", "height_references", "weather_conditions"):
                    linked[key] = context[key]
                linked["scope_from_description"] = context["statement"]
                if context.get("unbound_context"):
                    linked["description_subject_from_parameter"] = item["parameter"]
                linked["source_disagrees"] = bool(context["denied"] and not item["denied"])
                linked["source_denied"] = item["denied"]
                if context["min"] is None and context["max"] is not None:
                    linked["min"], linked["max"], linked["text"] = context["min"], context["max"], context["text"]
                    linked["speed_interval"] = context["speed_interval"]
                if not matches and guarded and len({
                        (claim["scope"], claim["onset"], claim["ends"], claim["denied"], claim["time_verified"])
                        for claim in contexts}) > 1:
                    linked["location_verified"] = False
                    linked["scope"] = "unresolved_parameter_scope"
                resolved.append(linked)
            return resolved
    return [item]


# One typed extraction result for the safety policy.
def _area_context(record, elevation, *, explicit_close=False):
    parser = _header_grammar()
    known = not getattr(record, "area_restriction_unknown", False)
    titles = [plain_text(getattr(record, key, "")) for key in ("headline", "event")]
    if not explicit_close:
        titles = [parser._wind_header_context(title) for title in titles]
    if not all(parser._header_applies(title, elevation) for title in titles
               if title and not parser._header_has_denial(title)):
        known = False
    altitude = getattr(record, "area_altitude", None)
    ceiling = getattr(record, "area_ceiling", None)
    if altitude is not None or ceiling is not None:
        known = (known and isinstance(elevation, (int, float)) and not isinstance(elevation, bool)
                 and math.isfinite(elevation)
                 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                         for v in (altitude, ceiling) if v is not None))
        if known and ((altitude is not None and elevation < altitude * 0.3048)
                      or (ceiling is not None and elevation > ceiling * 0.3048)):
            return False, True
    return known, False


def _bind_structured_local_scope(assertions, text_evidence):
    """Bind explicit, unambiguous same-quantity area and time restrictions.

    A regional CAP maximum retains its CAP envelope unless same-info,
    matching-value text proves a more specific location or period. An
    independent general statement, contradictory period, or unknown language
    must not silently reduce a valid structured warning. The underlying CAP
    quantity and its provider provenance are never replaced.
    """
    resolved = []
    for assertion in assertions:
        item = assertion.to_evidence()
        same_value = [claim for claim in text_evidence
                      if claim.get("evidence_kind") == "warning_text"
                      and not claim["denied"] and claim.get("max") is not None
                      and _parameter_identifies_quantity(item, claim)
                      and _periods_overlap(item, claim)
                      and claim["time_verified"] and item["time_verified"]]
        # An explicitly scoped sentence is only authoritative when every
        # textual assertion of this same value shares that scope.
        scoped = [claim for claim in same_value if claim.get("explicit_scope")
                  and claim.get("location_explicit")]
        if scoped and len(scoped) == len(same_value) and len({
                claim["scope"] for claim in scoped}) == 1:
            context = scoped[0]
            item.update({"scope": context["scope"],
                         "location_verified": item["location_verified"] and context["location_verified"],
                         "location_explicit": True, "explicit_scope": True,
                         "location_exclusions": deepcopy(context.get("location_exclusions", [])),
                         "height_references": deepcopy(context.get("height_references", [])),
                         "scope_from_description": context["statement"],
                         "scope_reconciliation": "same_info_matching_quantity"})

        # The same reasoning applies to an explicit onset or end of a *gust*
        # assertion. Never borrow a time associated with damage, hail, or an
        # unrelated speed. An untimed independent same-value assertion prevents
        # narrowing the regional maximum to one of several local forecasts.
        timed = [claim for claim in same_value if claim.get("time_explicit")
                 and claim.get("time_bounds")]
        if timed and len(timed) == len(same_value) and len({
                (claim["onset"], claim["ends"],
                 tuple(sorted(claim.get("time_period", {}).items())))
                for claim in timed}) == 1:
            context = timed[0]
            starts = [v for v in (item["onset"], context["onset"]) if v is not None]
            ends = [v for v in (item["ends"], context["ends"]) if v is not None]
            narrowed_start = max(starts) if starts else None
            narrowed_end = min(ends) if ends else None
            if narrowed_start is None or narrowed_end is None or narrowed_start < narrowed_end:
                item.update({"onset": narrowed_start, "ends": narrowed_end,
                             "time_explicit": True, "time_bounds": list(context["time_bounds"]),
                             "time_source": context["time_source"],
                             "time_period": deepcopy(context["time_period"]),
                             "time_constraints": deepcopy(context.get("time_constraints", [])),
                             "time_from_description": context["statement"],
                             "time_reconciliation": "same_info_matching_quantity"})
        resolved.append(WarningAssertion.from_evidence(item, assertion.provenance))
    return tuple(resolved)


def _single(record, *, elevation=None, explicit_close=False):
    structured = extract_structured_cap(record, elevation=elevation)
    language = str(getattr(record, "language", "") or "")
    text = " ".join(plain_text(getattr(record, key, "")) for key in ("headline", "event", "description"))
    pack, mismatch, unsupported = select(language, text + " " + plain_text(getattr(record, "instruction", "")))
    normalized, profile = normalized_record(record)
    evidence = _extract_warning_text(normalized, pack, elevation=elevation)
    for item in evidence:
        item["provider_profile"] = profile
    issued = aware(getattr(record, "issued_at", None))
    # A DWD scalar may also be an older free-text CAP parameter. Where its
    # original language parser has already contextualized the SAME numeric
    # parameter (place, denial, or event time), keep that contextualized
    # assertion instead of adding an unscoped duplicate. With unsupported
    # languages no such evidence exists: the structured quantity stays active.
    structured_assertions = tuple(assertion for assertion in structured.assertions
        if not (str(getattr(record, "provider_domain", "")) == "nina_auto_dwd"
                and any(item.get("evidence_kind") == "parameter_text"
                        and item.get("parameter", "").casefold() ==
                            assertion.details.get("parameter", "").casefold()
                        and _parameter_identifies_quantity(assertion.details, item)
                        for item in evidence)))
    assertions = _bind_structured_local_scope(structured_assertions, evidence) + tuple(WarningAssertion.from_evidence(item, [EvidenceSource(
        str(getattr(record, "provider_domain", "")), str(getattr(record, "sender", "")),
        str(getattr(record, "warning_id", "")), issued.isoformat() if issued else None,
        int(getattr(record, "info_index", 0)), language or (pack.CODE if pack else "unknown"), item["source"],
        item.get("text_parser", pack.CODE if pack else ""), mismatch,
    )]) for item in evidence)
    known, outside = _area_context(record, elevation, explicit_close=explicit_close)
    close_known = known
    if structured_assertions:
        known, outside = _cap_area_context(record, elevation)
    return WarningAnalysis(assertions, bool(structured.assertions or _header_grammar()._GUST.search(text) or _header_grammar()._WIND.search(text)),
                           bool(_header_grammar()._RELEVANT.search(text)), known, outside, unsupported or mismatch or bool(structured.issues),
                           (language,) if language else (),
                           structured.issues + tuple(issue for issue, active in (("language_mismatch", mismatch),
                                                            ("unsupported_language", unsupported)) if active),
                           close_area_verified=close_known)


def _valid_times(record):
    effective, onset, expires, event_end = (aware(getattr(record, key, None))
                                           for key in ("effective", "onset", "expires", "event_end"))
    ends = min(value for value in (expires, event_end) if value is not None) if expires or event_end else None
    valid = not (getattr(record, "timing_uncertain", False)
                 or any(getattr(record, key, None) is not None and aware(getattr(record, key, None)) is None
                        for key in ("effective", "onset", "expires", "event_end"))
                 or onset and ends and onset >= ends
                 or effective and ends and effective >= ends
                 or onset is not None and _lead_start(onset) is None)
    return effective, ends, bool(valid)


def _merge_equivalent(rows):
    """Merge equal translations while retaining all original source references."""
    merged = []
    keys = ("source", "min", "max", "denied", "scope", "location_verified", "onset", "ends", "time_verified",
            "effective", "speed_interval", "time_explicit", "location_explicit")
    for item, provenance in rows:
        equivalent = next((row for row in merged
                           if row[1][0].info_index != provenance[0].info_index
                           and all(row[0].get(key) == item.get(key) for key in keys)), None)
        if equivalent is None:
            merged.append((item, list(provenance)))
        else:
            equivalent[1].extend(provenance)
    return merged


def analyze(record, *, elevation=None, explicit_close=False, now=None):
    if not getattr(record, "info_blocks", ()):
        result = _single(record, elevation=elevation, explicit_close=bool(explicit_close))
        reconciled = _reconcile_gust_claims(result.evidence())
        return WarningAnalysis(tuple(WarningAssertion.from_evidence(item, assertion.provenance)
                                     for item, assertion in zip(reconciled, result.assertions)),
                               result.wind, result.relevant, result.area_verified, result.outside_area,
                               result.uncertain, result.languages, result.issues,
                               close_area_verified=result.close_area_verified)
    rows, issues, languages, close_intervals, close_orders = [], set(), [], [], []
    wind = relevant = uncertain = timing_uncertain = area_verified = False
    any_inside = False
    for variant in variants(record):
        effective, ends, timing_valid = _valid_times(variant)
        if now is not None and ends is not None and ends <= now:
            continue
        close = (bool(explicit_close) if isinstance(explicit_close, bool)
                 else variant.info_index in explicit_close)
        result = _single(variant, elevation=elevation, explicit_close=close)
        if result.outside_area:
            continue
        any_inside = True
        languages.extend(result.languages)
        issues.update(result.issues)
        wind |= result.wind
        relevant |= result.relevant
        uncertain |= result.uncertain or variant.area_match is None
        timing_uncertain |= not timing_valid
        area_verified |= result.area_verified
        if close and result.close_area_verified and timing_valid:
            period = TimeInterval(effective, ends, True)
            close_intervals.append(period)
            issued = aware(variant.issued_at)
            action_pack, mismatch, _ = select(variant.language, " ".join((variant.headline, variant.description, variant.instruction)))
            close_orders.append(ProtectiveAction("keep_closed", period, EvidenceSource(
                str(variant.provider_domain or ""), str(variant.sender or ""), str(variant.warning_id or ""),
                issued.isoformat() if issued else None, variant.info_index, variant.language, "info",
                action_pack.CODE if action_pack else "", mismatch),
                plain_text(variant.instruction or variant.description or variant.headline)))
        for assertion in result.assertions:
            item = assertion.to_evidence()
            item["location_verified"] &= result.area_verified
            item["time_verified"] &= timing_valid
            item["effective"] = effective.isoformat() if effective else None
            item["info_index"] = variant.info_index
            item["cap_area_verified"] = result.area_verified
            item["cap_timing_verified"] = timing_valid
            rows.append((item, assertion.provenance))
    merged = _merge_equivalent(rows)
    reconciled = _reconcile_gust_claims([item for item, _ in merged])
    assertions = tuple(WarningAssertion.from_evidence(item, provenance)
                       for item, (_, provenance) in zip(reconciled, merged))
    return WarningAnalysis(assertions, wind, relevant, area_verified, not any_inside, uncertain,
                           tuple(dict.fromkeys(languages)), tuple(sorted(issues)),
                           tuple(close_intervals), timing_uncertain, tuple(close_orders))


# Public compatibility names consumed by the common safety policy.
lead_start = _lead_start
uncontested_gust_periods = _uncontested_gust_periods

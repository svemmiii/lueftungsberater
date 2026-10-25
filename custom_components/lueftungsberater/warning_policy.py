"""One language-independent safety policy for normalized official warnings."""
from __future__ import annotations
from datetime import datetime, timedelta
import importlib.util
from pathlib import Path
import sys

if __package__:
    from . import warning_language as _warnings
else:
    # The existing independent tests load this facade directly, without HA.
    # Load the same pure module, without executing the integration __init__.
    _name = "_lueftungsberater_warning_language"
    if _name not in sys.modules:
        _path = Path(__file__).with_name("warning_language.py")
        _spec = importlib.util.spec_from_file_location(_name, _path)
        _module = importlib.util.module_from_spec(_spec)
        sys.modules[_name] = _module
        _spec.loader.exec_module(_module)
    _warnings = sys.modules[_name]

aware = _warnings.aware
plain_text = _warnings.plain_text
LEAD_TIME = _warnings.LEAD_TIME
HARD_GUST_KMH = _warnings.HARD_GUST_KMH
STRONG_GUST_KMH = _warnings.STRONG_GUST_KMH
_UTC_MAX = _warnings.UTC_MAX
_lead_start = _warnings.lead_start
_uncontested_gust_periods = _warnings.uncontested_gust_periods

def _reaches_gust_threshold(item: dict, threshold: float) -> bool:
    """Decide from a speed interval, respecting a strictly excluded ceiling.

    CAP `<90 [km/h]` never reaches 90 km/h. An open lower bound such as
    `>120 [km/h]` proves the threshold without inventing a peak speed.
    """
    interval = item.get("speed_interval")
    if isinstance(interval, dict):
        upper = interval.get("upper_kmh")
        lower = interval.get("lower_kmh")
        if upper is not None:
            return upper > threshold or (upper == threshold and interval.get("upper_inclusive", True))
        return lower is not None and lower >= threshold
    upper, lower = item.get("max"), item.get("min")
    return (upper if upper is not None else lower) is not None and (
        upper if upper is not None else lower) >= threshold


def _select_gusts(evidence: list[dict], now=None):
    candidates = [period for item in evidence if not item["denied"]
                  for period in _uncontested_gust_periods(item, evidence)]
    usable = [item for item in candidates if not item["denied"]
              and item["location_verified"]
              and item["time_verified"] and (item["max"] is not None or item["min"] is not None)
              and (now is None or item["ends"] is None or item["ends"] > now)]
    due = [item for item in usable if _reaches_gust_threshold(item, HARD_GUST_KMH)
           and (now is None or aware(item.get("effective")) is None or now >= aware(item["effective"]))
           and (now is None or item["onset"] is None
                or (lead := _lead_start(item["onset"])) is not None and now >= lead)]
    # UTC datetime/timedelta ordering is independent of platform POSIX epoch
    # limits, including valid year-1 and year-9999 provider dates.
    selected = max(due or usable, key=lambda item: (item["max"] if item["max"] is not None else item["min"],
                   _UTC_MAX - item["onset"] if item["onset"] else timedelta.max,
                   item["ends"] or _UTC_MAX), default=None)
    # Bounds belong to the selected assertion. Combining another area's/time's
    # minimum with this maximum would invent an official range.
    result = (selected["min"], selected["max"], selected["source"], selected["text"]) if selected else (None, None, "unknown", "")
    conflict = any(item.get("source_disagrees") or item.get("polarity_conflict")
                   or item.get("time_conflict") or item.get("value_conflict") for item in evidence)
    return result, selected, usable, conflict


def official_gusts(record, *, elevation=None):
    """Compatibility tuple; the warning assessment also retains scoped evidence."""
    return _select_gusts(_warnings.analyze(record, elevation=elevation).evidence())[0]


def assess_official_warning(record, now: datetime, *, explicit_close=False, elevation=None):
    """Return a serializable notice plus decision metadata, never live weather."""
    now = aware(now)
    effective = aware(getattr(record, "effective", None))
    onset = aware(getattr(record, "onset", None))
    expires = aware(getattr(record, "expires", None))
    event_end = aware(getattr(record, "event_end", None))
    ends = min(v for v in (expires, event_end) if v is not None) if expires or event_end else None
    if now is None:
        return None
    analysis = _warnings.analyze(record, elevation=elevation, explicit_close=explicit_close, now=now)
    evidence = analysis.evidence()
    (lower, upper, speed_source, gust_text), selected, usable, conflict = _select_gusts(evidence, now)
    scope_uncertain = any(not item["location_verified"] for item in evidence if not item["denied"])
    gust_time_uncertain = any(not item["time_verified"] for item in evidence if not item["denied"])
    wind = analysis.wind or upper is not None
    relevant = bool(explicit_close or wind or analysis.relevant)
    cancelled = str(getattr(record, "msg_type", "")).lower() == "cancel"
    if now is None or cancelled or ends is not None and ends <= now:
        return None
    if (getattr(record, "timing_uncertain", False)
            or any(getattr(record, key, None) is not None and aware(getattr(record, key, None)) is None
                   for key in ("effective", "onset", "expires", "event_end"))
            or onset and ends and onset >= ends
            or onset is not None and _lead_start(onset) is None
            or effective and ends and effective >= ends):
        # Contradictory times are visible but cannot drive an automatic lock.
        timing_valid = False
    else:
        timing_valid = True
    multiblock = bool(getattr(record, "info_blocks", ()))
    if multiblock:
        # Each info block already validated its own time and area. An unrelated
        # malformed/future block cannot erase a valid assertion's protection.
        timing_valid = True
    area_known = analysis.area_verified
    if analysis.outside_area:
        return None
    # The numeric value must actually occur in the official message. A color,
    # severity, event name or foreign category alone supplies no km/h value.
    # Open lower bounds (DWD '>120 [km/h]') prove threshold exceedance
    # without pretending that 120 is the unknown peak/maximum.
    severe_wind = bool(wind and selected and _reaches_gust_threshold(selected, HARD_GUST_KMH))
    strong_wind = bool(wind and selected and _reaches_gust_threshold(selected, STRONG_GUST_KMH))
    gust_onset = selected["onset"] if selected else None
    gust_ends = selected["ends"] if selected else None
    start_lock = _lead_start(gust_onset) if gust_onset is not None and severe_wind else gust_onset
    if selected is not None and multiblock:
        effective = aware(selected.get("effective"))
    if effective is not None and (start_lock is None or start_lock < effective):
        start_lock = effective
    valid = effective is None or now >= effective
    active_orders = [order for order in analysis.close_orders
                     if (order.period.onset is None or now >= order.period.onset)
                     and (order.period.ends is None or now < order.period.ends)]
    close_due = bool(active_orders) if multiblock else bool(explicit_close) and valid and analysis.close_area_verified
    close_end = (max(order.period.ends for order in active_orders)
                 if active_orders and all(order.period.ends is not None for order in active_orders) else None)
    if not multiblock and close_due:
        close_end = ends
    hard = bool(timing_valid and area_known and (
        close_due or valid and severe_wind and (start_lock is None or now >= start_lock)))
    phase_onset = gust_onset if selected else onset
    if close_due and multiblock:
        phase = "active"
    elif not timing_valid or gust_time_uncertain and not usable and not explicit_close:
        phase = "time_uncertain"
    elif effective and effective > now or phase_onset and now < phase_onset:
        phase = "prelock" if hard else "announced"
    else:
        phase = "active" if onset is not None else "start_unknown"
    transitions = [v for v in (effective, onset, start_lock, ends) if v is not None and v > now]
    for item in usable:
        transitions.extend(v for v in (item["onset"], item["ends"],
                           _lead_start(item["onset"]) if _reaches_gust_threshold(item, HARD_GUST_KMH) else None)
                           if v is not None and v > now)
        block_effective = aware(item.get("effective"))
        if block_effective is not None and block_effective > now:
            transitions.append(block_effective)
    for period in analysis.close_intervals:
        transitions.extend(v for v in (period.onset, period.ends) if v is not None and v > now)
    return {
        "id": str(getattr(record, "warning_id", "")),
        "provider": str(getattr(record, "provider_domain", "")),
        "sender": plain_text(getattr(record, "sender", "")),
        "issued_at": aware(getattr(record, "issued_at", None)).isoformat() if aware(getattr(record, "issued_at", None)) else None,
        "headline": plain_text(getattr(record, "headline", "")) or plain_text(getattr(record, "event", "")),
        "event": plain_text(getattr(record, "event", "")),
        "description": plain_text(getattr(record, "description", "")),
        "official_instruction": " ".join(dict.fromkeys(order.text for order in active_orders))
                                or plain_text(getattr(record, "instruction", "")),
        "close_ends": close_end.isoformat() if close_end else None,
        "close_evidence": [{"action": order.action, "text": order.text,
                            "effective": order.period.onset.isoformat() if order.period.onset else None,
                            "ends": order.period.ends.isoformat() if order.period.ends else None,
                            "provenance": order.provenance.to_dict()} for order in analysis.close_orders],
        "relevant": relevant, "wind": wind, "hard_lock": hard,
        "level": "lock" if hard else "strong" if strong_wind else "caution",
        "phase": phase, "timing_uncertain": not timing_valid or analysis.timing_uncertain,
        "gust_min_kmh": lower, "gust_max_kmh": upper,
        "gust_source": speed_source,
        "gust_original_text": gust_text,
        "gust_conflict": conflict,
        "interpretation_uncertain": analysis.uncertain or scope_uncertain or gust_time_uncertain or conflict,
        "cap_languages": list(analysis.languages),
        "language_issues": list(analysis.issues),
        "gust_polarity_conflict": any(item.get("polarity_conflict", False) for item in evidence),
        "gust_time_conflict": any(item.get("time_conflict", False) for item in evidence),
        "gust_value_conflict": any(item.get("value_conflict", False) for item in evidence),
        "gust_scope_uncertain": scope_uncertain,
        "gust_time_uncertain": gust_time_uncertain,
        "gust_onset": gust_onset.isoformat() if gust_onset else None,
        "gust_ends": gust_ends.isoformat() if gust_ends else None,
        "gust_evidence": [{**item,
                           "onset": item["onset"].isoformat() if item["onset"] else None,
                           "ends": item["ends"].isoformat() if item["ends"] else None}
                          for item in evidence],
        "effective": effective.isoformat() if effective else None,
        "onset": onset.isoformat() if onset else None,
        "ends": ends.isoformat() if ends else None,
        "lock_from": start_lock.isoformat() if severe_wind and start_lock else None,
        "lock_ends": gust_ends.isoformat() if severe_wind and gust_ends else None,
        "next_transition": min(transitions).isoformat() if transitions else None,
        "explicit_close": close_due, "area_verified": area_known,
    }



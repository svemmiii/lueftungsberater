"""Verified public civil-protection feeds, complementary to MeteoAlarm.

These are the public website endpoints of Alertswiss and RTR's AT-Alert, not
formally versioned APIs. Schema failures therefore mean UNKNOWN, never clear.
"""
from __future__ import annotations

import asyncio
from html import unescape
import logging
import re
from typing import Any

from homeassistant.util import dt as dt_util

from .auto_providers import (
    AutoWarningData, AutoWarningRecord, EffectiveLocation, _as_float,
    _cap_polygon_contains, _get_json, _geojson_contains_point,
    _parse_dt, _point_in_polygon, _safety_location_key, _HTTP_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)
_SWISS_FEED = "https://www.alert.swiss/content/alertswiss-internet/de/home/_jcr_content/polyalert.alertswiss_alerts.actual.json"
_AT_ALERT_FEED = "https://warnungen.at-alert.at/api/rpc/alert/list"
CIVIL_PROVIDERS = {"CH": "alertswiss_auto", "AT": "at_alert_auto", "BE": "be_alert_auto"}


def _text(value: Any) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", str(value or "")).replace("❘", " ")).split())


def _swiss_value(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    return _text(value.get(key) if isinstance(value, dict) else value)


def _swiss_record(item: dict[str, Any], location: EffectiveLocation) -> AutoWarningRecord | None:
    if item.get("testAlert") or item.get("technicalTestAlert"):
        return None
    identifier = item.get("identifier")
    if not identifier:
        raise ValueError("Alertswiss missing identifier")
    matched = item.get("nationWide") is True
    spatial = matched
    for area in item.get("areas", []):
        for polygon in area.get("polygons", []):
            rings = [polygon.get("coordinates", [])] + [hole.get("coordinates", []) for hole in polygon.get("excludes", [])]
            if rings[0]:
                spatial = True
                matched |= _point_in_polygon(location.latitude, location.longitude, rings, geojson=False)
        for circle in area.get("circles", []):
            # Alertswiss's public web representation uses lat/lon and kilometres.
            center = circle.get("centerPosition", [])
            radius = _as_float(circle.get("radius"))
            if len(center) == 2 and radius is not None:
                from .auto_providers import _distance_km
                spatial = True
                matched |= _distance_km(location.latitude, location.longitude, float(center[0]), float(center[1])) <= radius
    if not spatial:
        raise ValueError("Alertswiss unresolved area")
    if not matched:
        return None
    return AutoWarningRecord(
        warning_id=str(identifier), provider_domain="alertswiss_auto", category="civil",
        headline=_swiss_value(item, "title"), description=_swiss_value(item, "description"),
        instruction=" ".join(_text(row.get("text")) for row in item.get("instructions", [])),
        event=_text(item.get("event")), severity=_text(item.get("severity")),
        msg_type="Cancel" if item.get("allClear") is True else "Alert",
        # Successfully reading the current active set confirms this evidence.
        evidence_at=dt_util.utcnow(),
    )


def _at_record(item: dict[str, Any], location: EffectiveLocation) -> AutoWarningRecord | None:
    level = str(item.get("alert_level") or "").lower()
    if "test" in level or "exercise" in level:
        return None
    expires = _parse_dt(item.get("end_date") or item.get("info_expires"))
    effective = _parse_dt(item.get("begin_date") or item.get("sent"))
    now = dt_util.utcnow()
    if expires is not None and expires <= now:
        return None
    if effective is not None and effective > now:
        return None
    identifier = item.get("consolidation_identifier")
    if not identifier:
        raise ValueError("AT-Alert missing identifier")
    geometries = item.get("geometries")
    # The public endpoint currently emits Python-literal text for some shapes.
    # literal_eval parses data only, never code. It runs in the HA executor.
    if isinstance(geometries, str):
        import ast
        geometries = ast.literal_eval(geometries)
    if not isinstance(geometries, list):
        raise ValueError("AT-Alert malformed geometries")
    valid = [shape for shape in geometries if isinstance(shape, dict) and shape.get("type") in {"Polygon", "MultiPolygon"} and shape.get("coordinates")]
    if not valid:
        # Older alerts can still expose only CAP polygon strings.
        polygons = item.get("polygons") or []
        if not polygons:
            raise ValueError("AT-Alert unresolved area")
        matched = any(_cap_polygon_contains(str(row.get("polygon") or ""), location.latitude, location.longitude) for row in polygons)
    else:
        matched = any(_geojson_contains_point(shape, location.latitude, location.longitude) for shape in valid)
    if not matched:
        return None
    return AutoWarningRecord(
        warning_id=str(identifier), provider_domain="at_alert_auto", category="civil",
        headline=_text(item.get("title")),
        description=_text(item.get("info_description") or item.get("description")),
        severity="unknown", msg_type="Cancel" if level in {"clear", "allclear", "cancel"} else "Alert",
        effective=effective, expires=expires, evidence_at=now,
    )


def _parse_rows(rows: list[Any], location: EffectiveLocation, country: str) -> tuple[list[AutoWarningRecord], int]:
    records, failures = [], 0
    parser = _swiss_record if country == "CH" else _at_record
    for row in rows:
        try:
            if not isinstance(row, dict):
                raise ValueError("invalid alert row")
            record = parser(row, location)
            if record is not None:
                records.append(record)
        except (ValueError, TypeError, KeyError, IndexError, SyntaxError, RecursionError):
            failures += 1
    return records, failures


async def fetch_civil_warnings(hass, session, location: EffectiveLocation, country: str) -> AutoWarningData:
    if country == "BE":
        from .be_alert import fetch_be_warnings
        return await fetch_be_warnings(hass, session, location)
    if country == "CH":
        payload = await _get_json(session, _SWISS_FEED)
        if not isinstance(payload, dict) or not isinstance(payload.get("alerts"), list):
            raise ValueError("Alertswiss invalid active-set response")
        heartbeat = _as_float(payload.get("heartbeatAgeInMillis"))
        if heartbeat is None or not 0 <= heartbeat <= 300_000:
            raise ValueError("Alertswiss heartbeat stale")
        rows = payload["alerts"]
    else:
        rows = []
        offset = 0
        while True:
            async with session.post(_AT_ALERT_FEED, json={"json": {"limit": 100, "offset": offset}}, timeout=_HTTP_TIMEOUT) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
            body = payload.get("json") if isinstance(payload, dict) else None
            if not isinstance(body, dict) or not isinstance(body.get("alerts"), list) or not isinstance(body.get("totalCount"), int):
                raise ValueError("AT-Alert invalid active-set response")
            page = body["alerts"]
            rows.extend(page)
            offset += len(page)
            if offset >= body["totalCount"]:
                break
            if not page or offset > 10_000:
                raise ValueError("AT-Alert incomplete pagination")
    records, failures = await hass.async_add_executor_job(_parse_rows, rows, location, country)
    return AutoWarningData(
        provider_domain=CIVIL_PROVIDERS[country], fetched_at=dt_util.utcnow(),
        available=not failures, country=country,
        safety_source_key=_safety_location_key("warning", location), warnings=records,
        error="unresolved_civil_warning_areas" if failures else None, coverage="civil",
    )


async def combine_warning_sources(hass, session, location, country, weather_call) -> AutoWarningData:
    """Keep each provider's availability so another source cannot clear it."""
    domains = ["meteoalarm_auto", CIVIL_PROVIDERS[country]]
    results = await asyncio.gather(weather_call, fetch_civil_warnings(hass, session, location, country), return_exceptions=True)
    records, availability, errors = [], {}, []
    for domain, result in zip(domains, results, strict=True):
        if isinstance(result, Exception):
            availability[domain] = False
            errors.append(f"{domain}:unavailable")
            _LOGGER.debug("Automatic warning source %s failed: %s", domain, result)
            continue
        availability[domain] = result.available
        records.extend(result.warnings)
        if result.error:
            errors.append(f"{domain}:{result.error}")
    unique = {(record.provider_domain, record.warning_id): record for record in records}
    return AutoWarningData(
        provider_domain="+".join(domains), fetched_at=dt_util.utcnow(),
        available=all(availability.values()), country=country,
        safety_source_key=_safety_location_key("warning", location),
        warnings=list(unique.values()), error=";".join(errors) or None,
        coverage="civil_and_weather", source_availability=availability,
    )

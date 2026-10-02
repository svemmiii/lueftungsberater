"""Belgium's official BE-Alert public CAP gateway and current public feed."""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
import re
from typing import Any

from homeassistant.util import dt as dt_util

from .auto_providers import (
    AutoWarningData, AutoWarningRecord, EffectiveLocation, _get_json, _get_text,
    _parse_cap_document, _parse_dt, _safety_location_key, _cap_polygon_contains,
)
from .warning_language import is_probe_message

_BASE = 'https://publicalerts.be/CapGateway'
_FEED = f'{_BASE}/feed?outdated=false'


def _candidate_ids(payload: Any, location: EffectiveLocation) -> tuple[list[str], int]:
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        raise ValueError('BE-Alert invalid public-feed response')
    if 'activeOnly: true' not in str(payload.get('description') or ''):
        raise ValueError('BE-Alert did not confirm active-set filter')
    published = _parse_dt(payload.get('pubDate'))
    if published is None or not -timedelta(minutes=5) <= dt_util.utcnow() - published <= timedelta(minutes=15):
        raise ValueError('BE-Alert feed timestamp stale')
    identifiers, failures = [], 0
    for item in payload['items']:
        try:
            if not isinstance(item, dict):
                raise ValueError('invalid BE-Alert row')
            if is_probe_message(str(item.get('title') or ''), str(item.get('description') or '')):
                continue
            expires = _parse_dt(item.get('expirationDate'))
            if expires is None:
                raise ValueError('BE-Alert expiry missing')
            if expires <= dt_util.utcnow():
                continue
            areas = item.get('area')
            if not isinstance(areas, list) or not areas:
                raise ValueError('BE-Alert area missing')
            matches = False
            for area in areas:
                if not isinstance(area, dict) or area.get('type') != 'Polygon':
                    raise ValueError('BE-Alert unsupported area')
                outlines = area.get('coordinates')
                if not isinstance(outlines, list) or not outlines:
                    raise ValueError('BE-Alert outline missing')
                for outline in outlines:
                    if outline.get('type') != 'LineString':
                        raise ValueError('BE-Alert unsupported outline')
                    polygon = ' '.join(f"{point['y']},{point['x']}" for point in outline['coordinates'])
                    matches |= _cap_polygon_contains(polygon, location.latitude, location.longitude)
            if matches:
                identifier = str(item.get('guid') or '')
                if not re.fullmatch('[0-9a-fA-F]{24}', identifier):
                    raise ValueError('BE-Alert invalid identifier')
                identifiers.append(identifier)
        except (ValueError, TypeError, KeyError, AttributeError):
            failures += 1
    return list(dict.fromkeys(identifiers)), failures


def _record(text: str, location: EffectiveLocation) -> AutoWarningRecord | None:
    record = _parse_cap_document(text, location.latitude, location.longitude)
    if record is None or is_probe_message(record.headline, record.event, record.description):
        return None
    return replace(record, provider_domain='be_alert_auto', category='civil')


async def fetch_be_warnings(hass, session, location: EffectiveLocation) -> AutoWarningData:
    payload = await _get_json(session, _FEED)
    identifiers, failures = await hass.async_add_executor_job(_candidate_ids, payload, location)
    limit = asyncio.Semaphore(4)

    async def resolve(identifier):
        async with limit:
            text = await _get_text(session, f'{_BASE}/alert/{identifier}')
        return await hass.async_add_executor_job(_record, text, location)

    results = await asyncio.gather(*(resolve(identifier) for identifier in identifiers), return_exceptions=True)
    failures += sum(isinstance(result, Exception) for result in results)
    return AutoWarningData(
        provider_domain='be_alert_auto', fetched_at=dt_util.utcnow(), available=not failures,
        country='BE', safety_source_key=_safety_location_key('warning', location),
        warnings=[result for result in results if isinstance(result, AutoWarningRecord)],
        error='be_alert_incomplete' if failures else None, coverage='civil',
    )

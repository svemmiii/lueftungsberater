"""Local official MeteoAlarm region snapshot, loaded in the executor only.

The public CAP feeds remain live. The geometry snapshot avoids requiring an
account for the new authenticated Metadata API. Unknown/new codes must remain
UNKNOWN at the caller; never infer a country-wide warning from an area name.
"""
from __future__ import annotations

from functools import lru_cache
import gzip
import json
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _region_snapshot() -> dict[str, Any]:
    path = Path(__file__).parent / "assets" / "meteoalarm_regions.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def geocode_geometry(scheme: str, code: str) -> dict[str, Any] | None:
    """Resolve exact typed CAP codes including official NUTS aliases."""
    snapshot = _region_snapshot()
    key = f"{scheme.strip().upper()}|{code.strip().upper()}"
    region = snapshot["regions"].get(key)
    if region is None:
        alias = snapshot["aliases"].get(key)
        region = snapshot["regions"].get(f"EMMA_ID|{alias}") if alias else None
    return region.get("geometry") if region else None


@lru_cache(maxsize=1)
def _countries() -> list[dict[str, Any]]:
    path = Path(__file__).parent / "assets" / "countries.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)["countries"]


def coordinate_country(lat: float, lon: float) -> str | None:
    """Resolve land coordinates without mistaking a timezone for a country.

    Call in the executor. Natural Earth is a cartographic boundary snapshot,
    not cadastral border data; unmatched offshore/border points remain unknown.
    """
    from .auto_providers import _geojson_contains_point
    matches = set()
    for item in _countries():
        west, south, east, north = item["bbox"]
        if west <= lon <= east and south <= lat <= north and _geojson_contains_point(item["geometry"], lat, lon):
            matches.add(item["code"])
    return next(iter(matches)) if len(matches) == 1 else None

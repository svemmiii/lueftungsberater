"""Exact on-demand geographic resolution, without materializing the world in RAM.

The packaged SQLite lookup is read-only; individual geometries retain the
original source coordinates and are decoded only when selected. Calls remain
executor-only, as before. Missing EMMA codes stay unknown rather than being
silently assigned to a whole country.
"""
from __future__ import annotations

from functools import lru_cache
import json
import lzma
from pathlib import Path
import sqlite3
from typing import Any

_DATABASE = Path(__file__).parent / "assets" / "geodata.sqlite"


def _connect() -> sqlite3.Connection:
    # A short-lived read-only handle keeps connections out of the event loop,
    # avoids leaked file descriptors and does not retain a multi-MB page cache.
    return sqlite3.connect(f"{_DATABASE.as_uri()}?mode=ro&immutable=1", uri=True)


def _decode(data: bytes) -> dict[str, Any]:
    return json.loads(lzma.decompress(data))


@lru_cache(maxsize=48)
def geocode_geometry(scheme: str, code: str) -> dict[str, Any] | None:
    """Resolve a typed CAP region code or its exact official NUTS alias."""
    key = f"{scheme.strip().upper()}|{code.strip().upper()}"
    with _connect() as db:
        row = db.execute("SELECT geometry FROM region WHERE key=?", (key,)).fetchone()
        if row is None:
            alias = db.execute("SELECT target FROM alias WHERE key=?", (key,)).fetchone()
            if alias:
                row = db.execute("SELECT geometry FROM region WHERE key=?", (alias[0],)).fetchone()
    return _decode(row[0]) if row else None


def coordinate_country(lat: float, lon: float) -> str | None:
    """Return the unique matching country by exact original polygon containment.

    Bounding-box filtering occurs inside SQLite; only nearby candidates are
    inflated. Border/offshore ambiguities correctly remain unknown.
    """
    from .auto_providers import _geojson_contains_point

    with _connect() as db:
        candidates = db.execute(
            "SELECT code, geometry FROM country "
            "WHERE west <= ? AND east >= ? AND south <= ? AND north >= ?",
            (lon, lon, lat, lat),
        ).fetchall()
    matches = {
        code for code, packed in candidates
        if _geojson_contains_point(_decode(packed), lat, lon)
    }
    return next(iter(matches)) if len(matches) == 1 else None

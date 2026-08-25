"""Local outdoor-air-quality context for Lüftungsberater.

The UBA LQI remains the absolute health-oriented classification. This tracker
only adds local context: whether the current concentration is typical for the
configured Home Assistant location and whether it has recently been rising or
falling. A chronically poor location is therefore never relabelled as good.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from statistics import median
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    AIR_QUALITY_HISTORY_MIN_SAMPLES,
    AIR_QUALITY_HISTORY_RETENTION,
    AIR_QUALITY_SAMPLE_MIN_INTERVAL,
    CONF_WEATHER,
    DATA_AIR_QUALITY_TRACKERS,
    DOMAIN,
    STORAGE_VERSION,
)


@dataclass(slots=True)
class AirQualityContext:
    """Local context for one current pollutant value."""

    baseline: float | None = None
    typical: bool | None = None
    unusual: bool = False
    trend: str = "unknown"  # rising | falling | stable | unknown
    samples: int = 0
    location_key: str | None = None


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def location_key(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """Return a coarse key so history does not silently follow a moved home.

    Prefer coordinates exposed by the selected weather entity because a mobile
    Home Assistant (for example a motorhome) may deliberately use a moving
    provider. Fall back to Home Assistant's configured location. Two decimal
    places are roughly kilometre-scale and are only a context bucket, never a
    claim that pollution is spatially uniform inside it.
    """
    lat = lon = None
    weather_id = entry.data.get(CONF_WEATHER)
    if isinstance(weather_id, str):
        state = hass.states.get(weather_id)
        if state is not None:
            lat = _finite(state.attributes.get("latitude"))
            lon = _finite(state.attributes.get("longitude"))
    if lat is None or lon is None:
        lat = _finite(getattr(hass.config, "latitude", None))
        lon = _finite(getattr(hass.config, "longitude", None))
    if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return None
    return f"{lat:.2f},{lon:.2f}"


class OutdoorAirQualityTracker:
    """Keep a compact rolling history for the local advisor location."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._buckets: dict[str, dict[str, list[tuple[datetime, float]]]] = {}
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.air_quality.{entry.entry_id}",
        )

    async def async_initialize(self) -> None:
        stored = await self._store.async_load() or {}
        raw_buckets = stored.get("buckets", {})
        if isinstance(raw_buckets, dict):
            for loc, raw_pollutants in raw_buckets.items():
                if not isinstance(loc, str) or not isinstance(raw_pollutants, dict):
                    continue
                pollutants: dict[str, list[tuple[datetime, float]]] = {}
                for kind, raw_points in raw_pollutants.items():
                    if not isinstance(kind, str) or not isinstance(raw_points, list):
                        continue
                    points: list[tuple[datetime, float]] = []
                    for item in raw_points:
                        if not isinstance(item, (list, tuple)) or len(item) != 2:
                            continue
                        stamp = _parse_dt(item[0])
                        value = _finite(item[1])
                        if stamp is not None and value is not None and value >= 0:
                            points.append((stamp, value))
                    if points:
                        pollutants[kind] = sorted(points, key=lambda item: item[0])
                if pollutants:
                    self._buckets[loc] = pollutants
        self._prune(dt_util.utcnow())

    def _serialize(self) -> dict[str, Any]:
        return {
            "buckets": {
                loc: {
                    kind: [[stamp.isoformat(), value] for stamp, value in points]
                    for kind, points in pollutants.items()
                }
                for loc, pollutants in self._buckets.items()
            }
        }

    def _schedule_save(self) -> None:
        self._store.async_delay_save(self._serialize, 15)

    def _prune(self, now: datetime) -> None:
        cutoff = now - AIR_QUALITY_HISTORY_RETENTION
        for loc in list(self._buckets):
            pollutants = self._buckets[loc]
            for kind in list(pollutants):
                kept = [point for point in pollutants[kind] if point[0] >= cutoff]
                if kept:
                    pollutants[kind] = kept
                else:
                    pollutants.pop(kind, None)
            if not pollutants:
                self._buckets.pop(loc, None)

    def observe(self, values: dict[str, float], *, now: datetime | None = None) -> None:
        """Record valid current provider values at most twice an hour."""
        loc = location_key(self.hass, self.entry)
        if loc is None or not values:
            return
        now = now or dt_util.utcnow()
        self._prune(now)
        pollutants = self._buckets.setdefault(loc, {})
        changed = False
        for kind, raw in values.items():
            value = _finite(raw)
            if value is None or value < 0:
                continue
            points = pollutants.setdefault(kind, [])
            if points and now - points[-1][0] < AIR_QUALITY_SAMPLE_MIN_INTERVAL:
                # Keep the newest reading for the current half-hour slot rather
                # than allowing multiple rooms to duplicate the same sample.
                if abs(points[-1][1] - value) > 1e-9:
                    # Update the value inside the current sampling slot but keep
                    # the slot timestamp. Otherwise a frequently changing sensor
                    # would continuously move the timestamp forward and never
                    # reach the next 30-minute sample.
                    points[-1] = (points[-1][0], value)
                    changed = True
                continue
            points.append((now, value))
            changed = True
        if changed:
            self._schedule_save()

    def context(self, kind: str | None, current_value: float | None) -> AirQualityContext:
        loc = location_key(self.hass, self.entry)
        if loc is None or not kind or current_value is None:
            return AirQualityContext(location_key=loc)
        points = self._buckets.get(loc, {}).get(kind, [])
        if not points:
            return AirQualityContext(location_key=loc)

        values = [value for _stamp, value in points]
        samples = len(values)
        baseline = float(median(values))
        if samples < AIR_QUALITY_HISTORY_MIN_SAMPLES:
            return AirQualityContext(
                baseline=baseline,
                samples=samples,
                location_key=loc,
            )

        ordered = sorted(values)
        p90 = ordered[min(len(ordered) - 1, int((len(ordered) - 1) * 0.9))]
        # Deliberately broad: local history is context, not a second health
        # threshold. A current value must be clearly outside the recent local
        # distribution before it is called unusual.
        unusual_limit = max(p90 * 1.15, baseline + max(2.0, baseline * 0.15))
        unusual = current_value > unusual_limit
        typical = not unusual

        trend = "unknown"
        if samples >= 6:
            recent = median(values[-3:])
            previous = median(values[-6:-3])
            threshold = max(2.0, baseline * 0.10)
            if recent > previous + threshold:
                trend = "rising"
            elif recent < previous - threshold:
                trend = "falling"
            else:
                trend = "stable"

        return AirQualityContext(
            baseline=baseline,
            typical=typical,
            unusual=unusual,
            trend=trend,
            samples=samples,
            location_key=loc,
        )


async def async_get_or_create_air_quality_tracker(
    hass: HomeAssistant, entry: ConfigEntry
) -> OutdoorAirQualityTracker:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_AIR_QUALITY_TRACKERS, {})
    tracker = store.get(entry.entry_id)
    if tracker is None:
        tracker = OutdoorAirQualityTracker(hass, entry)
        store[entry.entry_id] = tracker
        await tracker.async_initialize()
    return tracker


def get_air_quality_tracker(
    hass: HomeAssistant, entry: ConfigEntry
) -> OutdoorAirQualityTracker | None:
    return (
        hass.data.get(DOMAIN, {})
        .get(DATA_AIR_QUALITY_TRACKERS, {})
        .get(entry.entry_id)
    )


def async_stop_air_quality_tracker(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hass.data.get(DOMAIN, {}).get(DATA_AIR_QUALITY_TRACKERS, {}).pop(entry.entry_id, None)

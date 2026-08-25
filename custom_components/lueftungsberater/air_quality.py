"""Compact local outdoor-air-quality context for Lüftungsberater.

The UBA LQI remains the absolute health-oriented classification. This tracker
adds only local context (typical/unusual and a short trend) and deliberately
keeps a fixed-size persistent memory instead of a second raw-history database.
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
    AIR_QUALITY_BASELINE_ALPHA,
    AIR_QUALITY_HISTORY_MIN_SAMPLES,
    AIR_QUALITY_MAX_LOCATIONS,
    AIR_QUALITY_RECENT_SAMPLES,
    AIR_QUALITY_SAMPLE_MIN_INTERVAL,
    CONF_WEATHER,
    DATA_AIR_QUALITY_TRACKERS,
    DOMAIN,
    STORAGE_VERSION,
)


@dataclass(slots=True)
class AirQualityContext:
    baseline: float | None = None
    typical: bool | None = None
    unusual: bool = False
    trend: str = "unknown"
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
    """Return a coarse location bucket; never transfer learned context blindly."""
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
    """Keep a bounded statistical memory per location and pollutant."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._buckets: dict[str, dict[str, dict[str, Any]]] = {}
        self._last_seen: dict[str, datetime] = {}
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.air_quality.{entry.entry_id}"
        )

    async def async_initialize(self) -> None:
        stored = await self._store.async_load() or {}
        raw = stored.get("buckets", {})
        if isinstance(raw, dict):
            for loc, pollutants in raw.items():
                if not isinstance(loc, str) or not isinstance(pollutants, dict):
                    continue
                clean: dict[str, dict[str, Any]] = {}
                newest: datetime | None = None
                for kind, stats in pollutants.items():
                    if not isinstance(kind, str):
                        continue

                    # v0.6.23 stored half-hour raw points. Fold those points into
                    # the new fixed-size statistics once so an update does not
                    # throw away the local context the advisor already learned.
                    if isinstance(stats, list):
                        legacy: list[tuple[datetime, float]] = []
                        for item in stats:
                            if not isinstance(item, (list, tuple)) or len(item) != 2:
                                continue
                            stamp, value = _parse_dt(item[0]), _finite(item[1])
                            if stamp is not None and value is not None and value >= 0:
                                legacy.append((stamp, value))
                        legacy.sort(key=lambda item: item[0])
                        if not legacy:
                            continue
                        values = [value for _stamp, value in legacy]
                        baseline = float(median(values))
                        deviation = float(median(abs(value - baseline) for value in values))
                        count = len(values)
                        last_sample = legacy[-1][0]
                        recent = legacy[-AIR_QUALITY_RECENT_SAMPLES:]
                    elif isinstance(stats, dict):
                        baseline = _finite(stats.get("baseline"))
                        deviation = _finite(stats.get("deviation"))
                        count = int(stats.get("count", 0) or 0)
                        last_sample = _parse_dt(stats.get("last_sample"))
                        recent = []
                    else:
                        continue

                    raw_recent = stats.get("recent", []) if isinstance(stats, dict) else []
                    if isinstance(raw_recent, list):
                        for item in raw_recent[-AIR_QUALITY_RECENT_SAMPLES:]:
                            if not isinstance(item, (list, tuple)) or len(item) != 2:
                                continue
                            stamp, value = _parse_dt(item[0]), _finite(item[1])
                            if stamp is not None and value is not None and value >= 0:
                                recent.append((stamp, value))
                    if baseline is None and recent:
                        baseline = float(median(value for _stamp, value in recent))
                    if baseline is None:
                        continue
                    clean[kind] = {
                        "baseline": baseline,
                        "deviation": max(0.0, deviation or 0.0),
                        "count": max(1, count),
                        "last_sample": last_sample,
                        "recent": recent,
                    }
                    candidate = last_sample or (recent[-1][0] if recent else None)
                    if candidate is not None and (newest is None or candidate > newest):
                        newest = candidate
                if clean:
                    self._buckets[loc] = clean
                    self._last_seen[loc] = newest or dt_util.utcnow()
        self._trim_locations()

    async def async_shutdown(self) -> None:
        """Flush the small bounded memory before unload/reload."""
        await self._store.async_save(self._serialize())

    def _serialize(self) -> dict[str, Any]:
        return {
            "buckets": {
                loc: {
                    kind: {
                        "baseline": stats["baseline"],
                        "deviation": stats["deviation"],
                        "count": stats["count"],
                        "last_sample": stats["last_sample"].isoformat() if stats.get("last_sample") else None,
                        "recent": [[stamp.isoformat(), value] for stamp, value in stats.get("recent", [])],
                    }
                    for kind, stats in pollutants.items()
                }
                for loc, pollutants in self._buckets.items()
            }
        }

    def _schedule_save(self) -> None:
        self._store.async_delay_save(self._serialize, 30)

    def _trim_locations(self) -> None:
        if len(self._buckets) <= AIR_QUALITY_MAX_LOCATIONS:
            return
        ordered = sorted(self._buckets, key=lambda loc: self._last_seen.get(loc, datetime.min.replace(tzinfo=dt_util.UTC)))
        for loc in ordered[: len(self._buckets) - AIR_QUALITY_MAX_LOCATIONS]:
            self._buckets.pop(loc, None)
            self._last_seen.pop(loc, None)

    def observe(self, values: dict[str, float], *, now: datetime | None = None) -> None:
        """Fold one provider sample into a fixed-size local memory."""
        loc = location_key(self.hass, self.entry)
        if loc is None or not values:
            return
        now = now or dt_util.utcnow()
        pollutants = self._buckets.setdefault(loc, {})
        self._last_seen[loc] = now
        changed = False

        for kind, raw in values.items():
            value = _finite(raw)
            if value is None or value < 0:
                continue
            stats = pollutants.get(kind)
            if stats is None:
                pollutants[kind] = {
                    "baseline": value,
                    "deviation": 0.0,
                    "count": 1,
                    "last_sample": now,
                    "recent": [(now, value)],
                }
                changed = True
                continue

            last_sample = stats.get("last_sample")
            if isinstance(last_sample, datetime) and now - last_sample < AIR_QUALITY_SAMPLE_MIN_INTERVAL:
                # Current-slot changes are useful for decisions but not worth a
                # persistent write. The next scheduled sample will fold them in.
                continue

            baseline = float(stats.get("baseline", value))
            count = int(stats.get("count", 0) or 0)
            # Adapt quickly while learning, then slowly. The steady alpha keeps
            # roughly weeks of memory without storing weeks of raw measurements.
            alpha = (1.0 / max(count + 1, 1)) if count < 50 else AIR_QUALITY_BASELINE_ALPHA
            new_baseline = baseline + alpha * (value - baseline)
            deviation = float(stats.get("deviation", 0.0) or 0.0)
            new_deviation = deviation + alpha * (abs(value - new_baseline) - deviation)
            recent = list(stats.get("recent", []))
            recent.append((now, value))
            stats.update(
                baseline=new_baseline,
                deviation=max(0.0, new_deviation),
                count=count + 1,
                last_sample=now,
                recent=recent[-AIR_QUALITY_RECENT_SAMPLES:],
            )
            changed = True

        self._trim_locations()
        if changed:
            self._schedule_save()

    def context(self, kind: str | None, current_value: float | None) -> AirQualityContext:
        loc = location_key(self.hass, self.entry)
        if loc is None or not kind or current_value is None:
            return AirQualityContext(location_key=loc)
        stats = self._buckets.get(loc, {}).get(kind)
        if not stats:
            return AirQualityContext(location_key=loc)

        baseline = float(stats.get("baseline", current_value))
        samples = int(stats.get("count", 0) or 0)
        if samples < AIR_QUALITY_HISTORY_MIN_SAMPLES:
            return AirQualityContext(baseline=baseline, samples=samples, location_key=loc)

        deviation = float(stats.get("deviation", 0.0) or 0.0)
        # Local context must be broad enough not to re-label normal measurement
        # noise as an event. It never changes the absolute UBA class.
        unusual_limit = baseline + max(2.0, baseline * 0.20, deviation * 3.0)
        unusual = current_value > unusual_limit

        recent = [float(value) for _stamp, value in stats.get("recent", [])]
        trend = "unknown"
        if len(recent) >= 6:
            previous = median(recent[-6:-3])
            latest = median(recent[-3:])
            threshold = max(2.0, baseline * 0.10, deviation * 1.5)
            if latest > previous + threshold:
                trend = "rising"
            elif latest < previous - threshold:
                trend = "falling"
            else:
                trend = "stable"

        return AirQualityContext(
            baseline=baseline,
            typical=not unusual,
            unusual=unusual,
            trend=trend,
            samples=samples,
            location_key=loc,
        )


async def async_get_or_create_air_quality_tracker(hass: HomeAssistant, entry: ConfigEntry) -> OutdoorAirQualityTracker:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_AIR_QUALITY_TRACKERS, {})
    tracker = store.get(entry.entry_id)
    if tracker is None:
        tracker = OutdoorAirQualityTracker(hass, entry)
        store[entry.entry_id] = tracker
        await tracker.async_initialize()
    return tracker


def get_air_quality_tracker(hass: HomeAssistant, entry: ConfigEntry) -> OutdoorAirQualityTracker | None:
    return hass.data.get(DOMAIN, {}).get(DATA_AIR_QUALITY_TRACKERS, {}).get(entry.entry_id)


async def async_stop_air_quality_tracker(hass: HomeAssistant, entry: ConfigEntry) -> None:
    tracker = (
        hass.data.get(DOMAIN, {})
        .get(DATA_AIR_QUALITY_TRACKERS, {})
        .pop(entry.entry_id, None)
    )
    if tracker is not None:
        await tracker.async_shutdown()

"""Optional long-term surface-moisture context for Lüftungsberater.

The tracker deliberately stores only the advisor's derived local surface-risk
intervals. It is never created for remote/Tailscale entries and it never tries
to infer a surface temperature when no dedicated sensor is configured.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_SURFACE_TEMP,
    DATA_MOLD_TRACKERS,
    DOMAIN,
    MOLD_HISTORY_RETENTION,
    MOLD_HISTORY_WINDOW,
    MOLD_CURRENT_LONG,
    MOLD_REPEATED_DAY_MIN,
    MOLD_REPEATED_DAYS,
    STORAGE_VERSION,
)


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed


class RoomMoldTracker:
    """Remember how long a measured cold surface stays in a critical RH range."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self.critical_since: datetime | None = None
        self.intervals: list[tuple[datetime, datetime]] = []
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.mold.{entry.entry_id}.{subentry.subentry_id}",
        )

    async def async_initialize(self) -> None:
        """Restore the local rolling exposure context."""
        stored = await self._store.async_load() or {}
        self.critical_since = _parse_dt(stored.get("critical_since"))
        raw_intervals = stored.get("intervals", [])
        if isinstance(raw_intervals, list):
            for item in raw_intervals:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    continue
                start, end = _parse_dt(item[0]), _parse_dt(item[1])
                if start is not None and end is not None and end >= start:
                    self.intervals.append((start, end))
        self._prune(dt_util.utcnow())

    async def async_shutdown(self) -> None:
        """Flush the compact exposure context before unload/reload."""
        await self._store.async_save(self._serialize())

    def _serialize(self) -> dict[str, Any]:
        return {
            "critical_since": (
                self.critical_since.isoformat() if self.critical_since else None
            ),
            "intervals": [
                [start.isoformat(), end.isoformat()]
                for start, end in self.intervals
            ],
        }

    def _schedule_save(self) -> None:
        # Store writes are intentionally delayed/coalesced; sensor updates must
        # never block the decision path.
        self._store.async_delay_save(self._serialize, 10)

    def _prune(self, now: datetime) -> None:
        cutoff = now - MOLD_HISTORY_RETENTION
        self.intervals = [
            (start, end) for start, end in self.intervals if end >= cutoff
        ]

    def observe(self, surface_rh: float | None, now: datetime | None = None) -> None:
        """Observe one derived surface RH value.

        Missing data does not end an active interval: an unavailable optional
        sensor is unknown, not evidence that the surface has dried.
        """
        if surface_rh is None:
            return
        now = now or dt_util.utcnow()
        self._prune(now)
        critical = surface_rh >= 80.0

        if critical and self.critical_since is None:
            self.critical_since = now
            self._schedule_save()
        elif not critical and self.critical_since is not None:
            self.intervals.append((self.critical_since, now))
            self.critical_since = None
            self._prune(now)
            self._schedule_save()

    @property
    def current_critical_minutes(self) -> float:
        if self.critical_since is None:
            return 0.0
        return max(
            0.0,
            (dt_util.utcnow() - self.critical_since).total_seconds() / 60.0,
        )

    @property
    def critical_minutes_24h(self) -> float:
        now = dt_util.utcnow()
        window_start = now - MOLD_HISTORY_WINDOW
        seconds = 0.0

        for start, end in self.intervals:
            overlap_start = max(start, window_start)
            overlap_end = min(end, now)
            if overlap_end > overlap_start:
                seconds += (overlap_end - overlap_start).total_seconds()

        if self.critical_since is not None:
            overlap_start = max(self.critical_since, window_start)
            if now > overlap_start:
                seconds += (now - overlap_start).total_seconds()

        return max(0.0, seconds / 60.0)

    def _critical_minutes_per_day(self) -> dict[str, float]:
        """Return compact daily exposure totals for the retained week."""
        now = dt_util.utcnow()
        cutoff = now - MOLD_HISTORY_RETENTION
        totals: dict[str, float] = {}
        intervals = list(self.intervals)
        if self.critical_since is not None:
            intervals.append((self.critical_since, now))

        for start, end in intervals:
            start = max(start, cutoff)
            end = min(end, now)
            while end > start:
                local_start = dt_util.as_local(start)
                next_day_local = local_start.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                split = min(end, next_day_local.astimezone(start.tzinfo))
                key = local_start.date().isoformat()
                totals[key] = totals.get(key, 0.0) + (split - start).total_seconds() / 60.0
                start = split
        return totals

    @property
    def persistent(self) -> bool:
        """Return a soft product-side persistence hint, never a diagnosis.

        Instead of one fixed 12-of-24-hour threshold, escalation is based on an
        actually measured surface remaining critical for many hours or recurring
        on several days. The numbers are intentionally conservative software
        heuristics and are not presented as medical/DIN limits.
        """
        if self.current_critical_minutes >= MOLD_CURRENT_LONG.total_seconds() / 60.0:
            return True
        day_min = MOLD_REPEATED_DAY_MIN.total_seconds() / 60.0
        active_days = sum(1 for minutes in self._critical_minutes_per_day().values() if minutes >= day_min)
        return active_days >= MOLD_REPEATED_DAYS


def _tracker_key(entry: ConfigEntry, subentry: ConfigSubentry) -> str:
    return f"{entry.entry_id}:{subentry.subentry_id}"


async def async_get_or_create_mold_tracker(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> RoomMoldTracker | None:
    """Create the tracker only when an actual surface sensor is configured."""
    if not subentry.data.get(CONF_SURFACE_TEMP):
        return None
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_MOLD_TRACKERS, {})
    key = _tracker_key(entry, subentry)
    tracker = store.get(key)
    if tracker is None:
        tracker = RoomMoldTracker(hass, entry, subentry)
        store[key] = tracker
        await tracker.async_initialize()
    return tracker


def get_mold_tracker(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> RoomMoldTracker | None:
    return (
        hass.data.get(DOMAIN, {})
        .get(DATA_MOLD_TRACKERS, {})
        .get(_tracker_key(entry, subentry))
    )


async def async_stop_entry_mold_trackers(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    store = hass.data.get(DOMAIN, {}).get(DATA_MOLD_TRACKERS, {})
    prefix = f"{entry.entry_id}:"
    for key in [item for item in store if item.startswith(prefix)]:
        tracker = store.pop(key, None)
        if tracker is not None:
            await tracker.async_shutdown()

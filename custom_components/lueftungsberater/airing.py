"""Internal airing-session tracking for rooms with window contacts."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_WINDOWS,
    DATA_TRACKERS,
    DOMAIN,
    MIN_CONFIRMED_AIRING,
    STORAGE_VERSION,
)


def tracker_signal(entry_id: str, subentry_id: str) -> str:
    """Return dispatcher signal for one room tracker."""
    return f"{DOMAIN}_{entry_id}_{subentry_id}_airing_update"


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed


class RoomAiringTracker:
    """Track real airing sessions from configured window/door contacts."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self.windows = tuple(subentry.data.get(CONF_WINDOWS, []) or [])
        self.open_since: datetime | None = None
        self.last_confirmed_airing: datetime | None = None
        self._unsub_state = None
        self._unsub_tick = None
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.airing.{entry.entry_id}.{subentry.subentry_id}",
        )

    @property
    def is_open(self) -> bool:
        """Return true if at least one configured contact is open."""
        return any(self.hass.states.is_state(entity_id, "on") for entity_id in self.windows)

    @property
    def current_open_minutes(self) -> float | None:
        """Return current airing-session duration."""
        if not self.is_open or self.open_since is None:
            return None
        seconds = (dt_util.utcnow() - self.open_since).total_seconds()
        return max(0.0, seconds / 60.0)

    @property
    def hours_since_last_airing(self) -> float | None:
        """Return hours since last confirmed airing session."""
        if self.last_confirmed_airing is None:
            return None
        seconds = (dt_util.utcnow() - self.last_confirmed_airing).total_seconds()
        return max(0.0, seconds / 3600.0)

    async def async_initialize(self) -> None:
        """Restore state and start tracking."""
        stored = await self._store.async_load() or {}
        self.last_confirmed_airing = _parse_dt(stored.get("last_confirmed_airing"))
        stored_open_since = _parse_dt(stored.get("open_since"))

        if self.is_open:
            # Preserve an already-running session across an HA restart.
            self.open_since = stored_open_since or dt_util.utcnow()
        else:
            # We cannot safely infer a completed airing while HA was offline.
            self.open_since = None

        await self._async_save()

        if self.windows:
            self._unsub_state = async_track_state_change_event(
                self.hass,
                self.windows,
                self._async_window_changed,
            )

        # Update "x hours since" and current open duration without polling entities.
        self._unsub_tick = async_track_time_interval(
            self.hass,
            self._async_tick,
            timedelta(minutes=1),
        )

    async def async_stop(self) -> None:
        """Stop listeners and persist current state."""
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        if self._unsub_tick:
            self._unsub_tick()
            self._unsub_tick = None
        await self._async_save()

    @callback
    def _async_tick(self, _now: datetime) -> None:
        async_dispatcher_send(
            self.hass,
            tracker_signal(self.entry.entry_id, self.subentry.subentry_id),
        )

    @callback
    def _async_window_changed(self, _event: Event) -> None:
        """Handle any configured contact changing state."""
        now = dt_util.utcnow()
        currently_open = self.is_open

        if currently_open and self.open_since is None:
            self.open_since = now
            self.hass.async_create_task(self._async_save())

        elif not currently_open and self.open_since is not None:
            duration = now - self.open_since
            if duration >= MIN_CONFIRMED_AIRING:
                self.last_confirmed_airing = now
            self.open_since = None
            self.hass.async_create_task(self._async_save())

        async_dispatcher_send(
            self.hass,
            tracker_signal(self.entry.entry_id, self.subentry.subentry_id),
        )

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "open_since": self.open_since.isoformat() if self.open_since else None,
                "last_confirmed_airing": (
                    self.last_confirmed_airing.isoformat()
                    if self.last_confirmed_airing
                    else None
                ),
            }
        )


def _tracker_bucket(hass: HomeAssistant, entry_id: str) -> dict[str, RoomAiringTracker]:
    domain_data = hass.data.setdefault(DOMAIN, {})
    entry_data = domain_data.setdefault(entry_id, {})
    return entry_data.setdefault(DATA_TRACKERS, {})


async def async_get_or_create_tracker(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> RoomAiringTracker | None:
    """Return/create a tracker for a room with window contacts."""
    windows = subentry.data.get(CONF_WINDOWS, []) or []
    if not windows:
        return None

    bucket = _tracker_bucket(hass, entry.entry_id)
    tracker = bucket.get(subentry.subentry_id)
    if tracker is not None:
        return tracker

    tracker = RoomAiringTracker(hass, entry, subentry)
    bucket[subentry.subentry_id] = tracker
    await tracker.async_initialize()
    return tracker


def get_tracker(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> RoomAiringTracker | None:
    """Return an initialized room tracker if present."""
    try:
        return hass.data[DOMAIN][entry.entry_id][DATA_TRACKERS].get(
            subentry.subentry_id
        )
    except KeyError:
        return None


async def async_stop_entry_trackers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Stop all trackers belonging to a config entry."""
    try:
        bucket = hass.data[DOMAIN][entry.entry_id].get(DATA_TRACKERS, {})
    except KeyError:
        return

    for tracker in list(bucket.values()):
        await tracker.async_stop()
    bucket.clear()

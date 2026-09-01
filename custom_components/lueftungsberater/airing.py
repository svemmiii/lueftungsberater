"""Internal airing-session tracking for rooms with window contacts."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
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
    WINDOW_UNKNOWN_GRACE,
)

_UNKNOWN = {"unknown", "unavailable", "none", ""}


def tracker_signal(entry_id: str, subentry_id: str) -> str:
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
    """Track real airing sessions while doing no idle minute polling."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self.windows = tuple(subentry.data.get(CONF_WINDOWS, []) or [])
        self.open_since: datetime | None = None
        self.last_confirmed_airing: datetime | None = None
        self._unsub_state = None
        self._unsub_tick = None
        self._unsub_fallback = None
        self._unsub_unknown_grace = None
        self._unknown_since: datetime | None = None
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.airing.{entry.entry_id}.{subentry.subentry_id}"
        )

    def _contact_state(self) -> tuple[bool, bool]:
        """Return (any_open, all_contacts_known)."""
        if not self.windows:
            return False, True
        any_open = False
        all_known = True
        for entity_id in self.windows:
            state = self.hass.states.get(entity_id)
            if state is None or state.state in _UNKNOWN:
                all_known = False
                continue
            if state.state == "on":
                any_open = True
        return any_open, all_known

    @property
    def is_open(self) -> bool:
        return self._contact_state()[0]

    @property
    def current_open_minutes(self) -> float | None:
        if self.open_since is None or not self.is_open:
            return None
        return max(0.0, (dt_util.utcnow() - self.open_since).total_seconds() / 60.0)

    @property
    def hours_since_last_airing(self) -> float | None:
        if self.last_confirmed_airing is None:
            return None
        return max(0.0, (dt_util.utcnow() - self.last_confirmed_airing).total_seconds() / 3600.0)

    async def async_initialize(self) -> None:
        stored = await self._store.async_load() or {}
        self.last_confirmed_airing = _parse_dt(stored.get("last_confirmed_airing"))
        stored_open_since = _parse_dt(stored.get("open_since"))
        stored_unknown_since = _parse_dt(stored.get("unknown_since"))

        any_open, all_known = self._contact_state()
        if any_open:
            self.open_since = stored_open_since or dt_util.utcnow()
            self._unknown_since = None
        elif not all_known:
            # Startup often exposes contacts as unknown for a moment. Preserve a
            # running session briefly, but never let an unknown state count as
            # confirmed airing without a time limit.
            self.open_since = stored_open_since
            self._unknown_since = (
                stored_unknown_since
                if stored_open_since is not None
                else None
            ) or (dt_util.utcnow() if stored_open_since is not None else None)
        else:
            self.open_since = None
            self._unknown_since = None

        if self.windows:
            self._unsub_state = async_track_state_change_event(
                self.hass, self.windows, self._async_window_changed
            )
        self._sync_timers()
        await self._async_save()

    async def async_stop(self) -> None:
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        self._cancel_tick()
        self._cancel_fallback()
        self._cancel_unknown_grace()
        await self._async_save()

    def _cancel_tick(self) -> None:
        if self._unsub_tick:
            self._unsub_tick()
            self._unsub_tick = None

    def _cancel_fallback(self) -> None:
        if self._unsub_fallback:
            self._unsub_fallback()
            self._unsub_fallback = None

    def _cancel_unknown_grace(self) -> None:
        if self._unsub_unknown_grace:
            self._unsub_unknown_grace()
            self._unsub_unknown_grace = None

    def _schedule_unknown_grace(self) -> None:
        self._cancel_unknown_grace()
        if self.open_since is None or self._unknown_since is None:
            return
        deadline = self._unknown_since + WINDOW_UNKNOWN_GRACE
        now = dt_util.utcnow()
        if deadline <= now:
            self._async_unknown_grace_expired(now)
            return
        self._unsub_unknown_grace = async_track_point_in_utc_time(
            self.hass, self._async_unknown_grace_expired, deadline
        )

    def _finish_open_session(self, end: datetime) -> None:
        if self.open_since is None:
            self._unknown_since = None
            return
        duration = max(timedelta(0), end - self.open_since)
        if duration >= MIN_CONFIRMED_AIRING:
            self.last_confirmed_airing = end
        self.open_since = None
        self._unknown_since = None

    @callback
    def _async_unknown_grace_expired(self, now: datetime) -> None:
        self._unsub_unknown_grace = None
        any_open, all_known = self._contact_state()
        if (
            self.open_since is not None
            and not any_open
            and not all_known
            and self._unknown_since is not None
            and now >= self._unknown_since + WINDOW_UNKNOWN_GRACE
        ):
            # We only know that the window was definitely open up to the start
            # of the unknown period.  End there instead of turning unknown time
            # into a successful airing session.
            self._finish_open_session(self._unknown_since)
            self.hass.async_create_task(self._async_save())
        self._sync_timers()
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    def _sync_timers(self) -> None:
        """Run timers only for states that can still change the recommendation."""
        any_open, all_known = self._contact_state()
        if any_open and self.open_since is not None:
            self._cancel_unknown_grace()
            self._unknown_since = None
            self._cancel_fallback()
            if self._unsub_tick is None:
                self._unsub_tick = async_track_time_interval(
                    self.hass, self._async_tick, timedelta(minutes=1)
                )
            return

        self._cancel_tick()
        if not all_known and self.open_since is not None:
            self._cancel_fallback()
            if self._unknown_since is None:
                self._unknown_since = dt_util.utcnow()
            if self._unsub_unknown_grace is None:
                self._schedule_unknown_grace()
            return

        self._cancel_unknown_grace()
        self._cancel_fallback()
        if self.last_confirmed_airing is None:
            return
        target = self.last_confirmed_airing + timedelta(hours=24)
        now = dt_util.utcnow()
        if target > now:
            self._unsub_fallback = async_track_point_in_utc_time(
                self.hass, self._async_fallback_due, target
            )

    @callback
    def _async_tick(self, _now: datetime) -> None:
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    @callback
    def _async_fallback_due(self, _now: datetime) -> None:
        self._unsub_fallback = None
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    @callback
    def _async_window_changed(self, _event: Event) -> None:
        now = dt_util.utcnow()
        any_open, all_known = self._contact_state()
        changed = False

        if any_open:
            if self.open_since is None:
                self.open_since = now
                changed = True
            if self._unknown_since is not None:
                self._unknown_since = None
                changed = True
        elif not all_known and self.open_since is not None:
            if self._unknown_since is None:
                self._unknown_since = now
                changed = True
        elif all_known and self.open_since is not None:
            # If the contact was unknown before becoming definitively closed,
            # use the last definitely-open instant as the conservative end.
            end = self._unknown_since or now
            self._finish_open_session(end)
            changed = True
        elif all_known and self._unknown_since is not None:
            self._unknown_since = None
            changed = True

        if changed:
            self.hass.async_create_task(self._async_save())

        self._sync_timers()
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "open_since": self.open_since.isoformat() if self.open_since else None,
                "unknown_since": self._unknown_since.isoformat() if self._unknown_since else None,
                "last_confirmed_airing": self.last_confirmed_airing.isoformat() if self.last_confirmed_airing else None,
            }
        )


def _tracker_bucket(hass: HomeAssistant, entry_id: str) -> dict[str, RoomAiringTracker]:
    domain_data = hass.data.setdefault(DOMAIN, {})
    entry_data = domain_data.setdefault(entry_id, {})
    return entry_data.setdefault(DATA_TRACKERS, {})


async def async_get_or_create_tracker(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> RoomAiringTracker | None:
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


def get_tracker(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> RoomAiringTracker | None:
    try:
        return hass.data[DOMAIN][entry.entry_id][DATA_TRACKERS].get(subentry.subentry_id)
    except KeyError:
        return None


async def async_stop_entry_trackers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    try:
        bucket = hass.data[DOMAIN][entry.entry_id].get(DATA_TRACKERS, {})
    except KeyError:
        return
    for tracker in list(bucket.values()):
        await tracker.async_stop()
    bucket.clear()

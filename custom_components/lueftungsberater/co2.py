"""Short-term CO2 dropout stabilization for configured room sensors."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util
from homeassistant.helpers.storage import Store

from .const import (
    CO2_GRACE_PERIOD,
    CONF_CO2,
    DATA_CO2_TRACKERS,
    DOMAIN,
    STORAGE_VERSION,
)


def co2_tracker_signal(entry_id: str, subentry_id: str) -> str:
    """Return dispatcher signal for one room CO2 tracker."""
    return f"{DOMAIN}_{entry_id}_{subentry_id}_co2_update"


def _state_to_float(state: Any) -> float | None:
    """Parse a Home Assistant State object to a float."""
    if state is None:
        return None
    raw = getattr(state, "state", None)
    if raw in {None, "", "unknown", "unavailable", "none"}:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


class RoomCo2Tracker:
    """Hold a last valid CO2 value briefly across short dropouts."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self.entity_id: str | None = subentry.data.get(CONF_CO2)
        self.last_valid_value: float | None = None
        self.last_valid_at: datetime | None = None
        self.unavailable_since: datetime | None = None
        self._unsub_state = None
        self._unsub_expiry = None
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.co2.{entry.entry_id}.{subentry.subentry_id}",
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        parsed = dt_util.parse_datetime(value)
        if parsed is None:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt_util.UTC)
        return parsed

    def _payload(self) -> dict[str, Any]:
        return {
            "last_valid_value": self.last_valid_value,
            "last_valid_at": self.last_valid_at.isoformat() if self.last_valid_at else None,
            "unavailable_since": (
                self.unavailable_since.isoformat() if self.unavailable_since else None
            ),
        }

    def _queue_save(self) -> None:
        self._store.async_delay_save(self._payload, 2)

    def _schedule_expiry(self) -> None:
        if self._unsub_expiry:
            self._unsub_expiry()
            self._unsub_expiry = None
        if self.unavailable_since is None:
            return
        remaining = CO2_GRACE_PERIOD - (dt_util.utcnow() - self.unavailable_since)
        if remaining.total_seconds() <= 0:
            return
        self._unsub_expiry = async_call_later(
            self.hass,
            remaining.total_seconds(),
            self._async_grace_expired,
        )

    @property
    def configured(self) -> bool:
        """Return whether this room has a CO2 entity configured."""
        return bool(self.entity_id)

    @property
    def current_value(self) -> float | None:
        """Return current value, brief cached value, or None."""
        if not self.entity_id:
            return None

        current = _state_to_float(self.hass.states.get(self.entity_id))
        if current is not None:
            self.last_valid_value = current
            if self.last_valid_at is None:
                self.last_valid_at = dt_util.utcnow()
            self.unavailable_since = None
            return current

        if (
            self.last_valid_value is not None
            and self.unavailable_since is not None
            and dt_util.utcnow() - self.unavailable_since < CO2_GRACE_PERIOD
        ):
            return self.last_valid_value

        return None

    @property
    def data_status(self) -> str:
        """Return current/grace/unavailable/not_configured."""
        if not self.entity_id:
            return "not_configured"

        current = _state_to_float(self.hass.states.get(self.entity_id))
        if current is not None:
            return "current"

        if (
            self.last_valid_value is not None
            and self.unavailable_since is not None
            and dt_util.utcnow() - self.unavailable_since < CO2_GRACE_PERIOD
        ):
            return "grace"

        return "unavailable"

    async def async_initialize(self) -> None:
        """Initialize cache, restore a still-valid grace period, and listen."""
        if not self.entity_id:
            return

        now = dt_util.utcnow()
        stored = await self._store.async_load() or {}
        stored_value = stored.get("last_valid_value")
        try:
            stored_value = float(stored_value) if stored_value is not None else None
        except (TypeError, ValueError):
            stored_value = None
        stored_valid_at = self._parse_dt(stored.get("last_valid_at"))
        stored_unavailable = self._parse_dt(stored.get("unavailable_since"))

        current = _state_to_float(self.hass.states.get(self.entity_id))
        if current is not None:
            self.last_valid_value = current
            self.last_valid_at = now
            self.unavailable_since = None
            await self._store.async_save(self._payload())
        elif (
            stored_value is not None
            and stored_valid_at is not None
            and now - stored_valid_at < CO2_GRACE_PERIOD
        ):
            self.last_valid_value = stored_value
            self.last_valid_at = stored_valid_at
            self.unavailable_since = stored_unavailable or stored_valid_at
            if now - self.unavailable_since < CO2_GRACE_PERIOD:
                self._schedule_expiry()
            else:
                self.unavailable_since = None

        self._unsub_state = async_track_state_change_event(
            self.hass,
            [self.entity_id],
            self._async_state_changed,
        )

    async def async_stop(self) -> None:
        """Stop listeners/timers while preserving a tiny restart grace state."""
        if self.entity_id:
            current = _state_to_float(self.hass.states.get(self.entity_id))
            if current is not None:
                self.last_valid_value = current
                self.last_valid_at = dt_util.utcnow()
                self.unavailable_since = None
            await self._store.async_save(self._payload())
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        if self._unsub_expiry:
            self._unsub_expiry()
            self._unsub_expiry = None

    @callback
    def _async_state_changed(self, event: Event) -> None:
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        new_value = _state_to_float(new_state)

        now = dt_util.utcnow()
        if new_value is not None:
            self.last_valid_value = new_value
            self.last_valid_at = now
            self.unavailable_since = None
            if self._unsub_expiry:
                self._unsub_expiry()
                self._unsub_expiry = None
        else:
            old_value = _state_to_float(old_state)
            if old_value is not None:
                self.last_valid_value = old_value
                self.last_valid_at = now

            if self.unavailable_since is None:
                self.unavailable_since = now
            self._schedule_expiry()

        self._queue_save()

        async_dispatcher_send(
            self.hass,
            co2_tracker_signal(
                self.entry.entry_id,
                self.subentry.subentry_id,
            ),
        )

    @callback
    def _async_grace_expired(self, _now: datetime) -> None:
        self._unsub_expiry = None
        self._queue_save()
        async_dispatcher_send(
            self.hass,
            co2_tracker_signal(
                self.entry.entry_id,
                self.subentry.subentry_id,
            ),
        )


def _tracker_bucket(
    hass: HomeAssistant,
    entry_id: str,
) -> dict[str, RoomCo2Tracker]:
    """Return/create tracker bucket for one config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    entry_data = domain_data.setdefault(entry_id, {})
    return entry_data.setdefault(DATA_CO2_TRACKERS, {})


async def async_get_or_create_co2_tracker(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> RoomCo2Tracker | None:
    """Return/create tracker when a CO2 entity is configured."""
    if not subentry.data.get(CONF_CO2):
        return None

    bucket = _tracker_bucket(hass, entry.entry_id)
    tracker = bucket.get(subentry.subentry_id)
    if tracker is not None:
        return tracker

    tracker = RoomCo2Tracker(hass, entry, subentry)
    bucket[subentry.subentry_id] = tracker
    await tracker.async_initialize()
    return tracker


def get_co2_tracker(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> RoomCo2Tracker | None:
    """Return an initialized room CO2 tracker if present."""
    try:
        return hass.data[DOMAIN][entry.entry_id][DATA_CO2_TRACKERS].get(
            subentry.subentry_id
        )
    except KeyError:
        return None


async def async_stop_entry_co2_trackers(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Stop all CO2 trackers belonging to a config entry."""
    try:
        bucket = hass.data[DOMAIN][entry.entry_id].get(
            DATA_CO2_TRACKERS,
            {},
        )
    except KeyError:
        return

    for tracker in list(bucket.values()):
        await tracker.async_stop()
    bucket.clear()

"""Shared event-driven room coordinator for Lüftungsberater."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .airing import tracker_signal
from .co2 import co2_tracker_signal
from .const import (
    CONF_CO2,
    CONF_NIGHT_START_HOUR,
    CONF_NIGHT_START_TIME,
    CONF_SURFACE_TEMP,
    CONF_WINDOWS,
    DATA_COORDINATORS,
    DECISION_MEMORY_TTL,
    DEFAULT_NIGHT_START_HOUR,
    DOMAIN,
    MOLD_SAMPLE_INTERVAL,
    STORAGE_VERSION,
)
from .notifications import async_handle_room_notification, clear_room_notification_state
from .outside import async_get_or_create_outside_coordinator, get_outside_coordinator
from .runtime import RoomSnapshot, build_room_snapshot, room_source_entities

_LOGGER = logging.getLogger(__name__)


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed


def _night_clock(subentry: ConfigSubentry) -> tuple[int, int]:
    raw = subentry.data.get(CONF_NIGHT_START_TIME)
    if isinstance(raw, str):
        parts = raw.split(":")
        try:
            return max(0, min(23, int(parts[0]))), max(0, min(59, int(parts[1])))
        except (ValueError, IndexError):
            pass
    try:
        hour = int(subentry.data.get(CONF_NIGHT_START_HOUR, DEFAULT_NIGHT_START_HOUR))
    except (TypeError, ValueError):
        hour = DEFAULT_NIGHT_START_HOUR
    return max(0, min(23, hour)), 0


class LueftungsberaterRoomCoordinator(DataUpdateCoordinator[RoomSnapshot]):
    """Compute one shared room snapshot whenever one of its inputs changes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{subentry.subentry_id}",
            update_interval=None,
            always_update=False,
        )
        self.entry = entry
        self.subentry = subentry
        self._unsubs: list[Callable[[], None]] = []
        self._started = False
        self._previous_mode: str | None = None
        self._previous_need: str | None = None
        self._previous_mode_at: datetime | None = None
        self._memory_store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.decision.{entry.entry_id}.{subentry.subentry_id}",
        )

    async def _restore_memory(self) -> None:
        stored = await self._memory_store.async_load() or {}
        mode = stored.get("mode")
        need = stored.get("primary_need")
        stamp = _parse_dt(stored.get("updated_at"))
        if isinstance(mode, str) and mode and stamp is not None and dt_util.utcnow() - stamp <= DECISION_MEMORY_TTL:
            self._previous_mode = mode
            self._previous_need = need if isinstance(need, str) and need else None
            self._previous_mode_at = stamp

    def _memory_payload(self) -> dict[str, Any]:
        return {
            "mode": self._previous_mode,
            "primary_need": self._previous_need,
            "updated_at": self._previous_mode_at.isoformat() if self._previous_mode_at else None,
        }

    def _remember_snapshot(self, snapshot: RoomSnapshot) -> None:
        if snapshot.result is None:
            return
        mode = snapshot.result.mode
        need = snapshot.result.primary_need
        if mode == self._previous_mode and need == self._previous_need:
            return
        self._previous_mode = mode
        self._previous_need = need
        self._previous_mode_at = dt_util.utcnow()
        self._memory_store.async_delay_save(self._memory_payload, 10)

    def _build_snapshot(self) -> RoomSnapshot:
        outside_coordinator = get_outside_coordinator(self.hass, self.entry)
        weather = outside_coordinator.data.weather if outside_coordinator is not None and outside_coordinator.data is not None else None
        warnings = outside_coordinator.data.warnings if outside_coordinator is not None and outside_coordinator.data is not None else None
        previous_mode = (
            self.data.result.mode
            if self.data is not None and self.data.result is not None
            else self._previous_mode
        )
        previous_need = (
            self.data.result.primary_need
            if self.data is not None and self.data.result is not None
            else self._previous_need
        )
        return build_room_snapshot(
            self.hass,
            self.entry,
            self.subentry,
            previous_mode=previous_mode,
            previous_need=previous_need,
            weather=weather,
            warnings=warnings,
        )

    async def _async_update_data(self) -> RoomSnapshot:
        snapshot = self._build_snapshot()
        self._remember_snapshot(snapshot)
        await async_handle_room_notification(self.hass, self.entry, self.subentry, snapshot)
        return snapshot

    async def async_start(self) -> None:
        if self._started:
            return
        self._started = True
        await self._restore_memory()
        outside = await async_get_or_create_outside_coordinator(self.hass, self.entry)
        await self.async_config_entry_first_refresh()

        entities = room_source_entities(self.hass, self.entry, self.subentry)
        if entities:
            self._unsubs.append(async_track_state_change_event(self.hass, entities, self._handle_source_change))

        self._unsubs.append(outside.async_add_listener(self._handle_tracker_change))

        if self.subentry.data.get(CONF_WINDOWS):
            self._unsubs.append(
                async_dispatcher_connect(
                    self.hass,
                    tracker_signal(self.entry.entry_id, self.subentry.subentry_id),
                    self._handle_tracker_change,
                )
            )

        if self.subentry.data.get(CONF_CO2):
            self._unsubs.append(
                async_dispatcher_connect(
                    self.hass,
                    co2_tracker_signal(self.entry.entry_id, self.subentry.subentry_id),
                    self._handle_tracker_change,
                )
            )

        if self.subentry.data.get(CONF_SURFACE_TEMP):
            self._unsubs.append(
                async_track_time_interval(
                    self.hass,
                    lambda _now: self._handle_tracker_change(),
                    MOLD_SAMPLE_INTERVAL,
                )
            )

        # Re-evaluate exactly when this room's night hint becomes visible. The
        # shared outside coordinator handles the actual forecast refreshes.
        night_hour, night_minute = _night_clock(self.subentry)
        self._unsubs.append(
            async_track_time_change(
                self.hass,
                self._handle_night_start,
                hour=night_hour,
                minute=night_minute,
                second=0,
            )
        )

    def _publish_snapshot(self, snapshot: RoomSnapshot) -> None:
        self._remember_snapshot(snapshot)
        self.async_set_updated_data(snapshot)
        self.hass.async_create_task(
            async_handle_room_notification(self.hass, self.entry, self.subentry, snapshot),
            f"Lüftungsberater notification check {self.subentry.subentry_id}",
        )

    @callback
    def _handle_night_start(self, _now: datetime) -> None:
        """Refresh the shared forecast exactly when this room starts showing it."""
        outside = get_outside_coordinator(self.hass, self.entry)
        if outside is None:
            self._handle_tracker_change()
            return
        self.hass.async_create_task(
            outside.async_request_refresh(),
            f"Lüftungsberater night forecast {self.subentry.subentry_id}",
        )

    @callback
    def _handle_source_change(self, _event: Event) -> None:
        self._publish_snapshot(self._build_snapshot())

    @callback
    def _handle_tracker_change(self) -> None:
        self._publish_snapshot(self._build_snapshot())

    async def async_shutdown(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()
        clear_room_notification_state(self.hass, self.entry.entry_id, self.subentry.subentry_id)
        self._started = False
        # A clean Home Assistant restart should not discard a long-stable
        # hysteresis mode merely because the last mode *change* happened more
        # than DECISION_MEMORY_TTL ago. Refresh the tiny memory timestamp only
        # on clean shutdown; after an unclean stop the existing TTL still keeps
        # stale decisions from being resurrected.
        if self.data is not None and self.data.result is not None:
            self._previous_mode = self.data.result.mode
            self._previous_need = self.data.result.primary_need
            self._previous_mode_at = dt_util.utcnow()
        await self._memory_store.async_save(self._memory_payload())
        await super().async_shutdown()


def _coordinator_key(entry: ConfigEntry, subentry: ConfigSubentry) -> str:
    return f"{entry.entry_id}:{subentry.subentry_id}"


async def async_get_or_create_room_coordinator(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> LueftungsberaterRoomCoordinator:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_COORDINATORS, {})
    key = _coordinator_key(entry, subentry)
    coordinator = store.get(key)
    if coordinator is None:
        coordinator = LueftungsberaterRoomCoordinator(hass, entry, subentry)
        store[key] = coordinator
        await coordinator.async_start()
    return coordinator


def get_room_coordinator(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> LueftungsberaterRoomCoordinator | None:
    return hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {}).get(_coordinator_key(entry, subentry))


async def async_stop_entry_coordinators(hass: HomeAssistant, entry: ConfigEntry) -> None:
    store = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {})
    prefix = f"{entry.entry_id}:"
    for key in [item for item in store if item.startswith(prefix)]:
        coordinator = store.pop(key, None)
        if coordinator is not None:
            await coordinator.async_shutdown()

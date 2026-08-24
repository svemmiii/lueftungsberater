"""Shared event-driven room coordinator for Lüftungsberater."""
from __future__ import annotations

from collections.abc import Callable
import logging

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .airing import tracker_signal
from .co2 import co2_tracker_signal
from .const import (
    CONF_CO2,
    CONF_SURFACE_TEMP,
    CONF_WINDOWS,
    DATA_COORDINATORS,
    DOMAIN,
    MOLD_SAMPLE_INTERVAL,
)
from .runtime import RoomSnapshot, build_room_snapshot, room_source_entities
from .notifications import (
    async_handle_room_notification,
    clear_room_notification_state,
)

_LOGGER = logging.getLogger(__name__)


class LueftungsberaterRoomCoordinator(DataUpdateCoordinator[RoomSnapshot]):
    """Compute one shared room snapshot whenever one of its inputs changes."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
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

    def _build_snapshot(self) -> RoomSnapshot:
        previous_mode = (
            self.data.result.mode
            if self.data is not None and self.data.result is not None
            else None
        )
        return build_room_snapshot(
            self.hass, self.entry, self.subentry, previous_mode=previous_mode
        )

    async def _async_update_data(self) -> RoomSnapshot:
        snapshot = self._build_snapshot()
        await async_handle_room_notification(self.hass, self.entry, self.subentry, snapshot)
        return snapshot

    async def async_start(self) -> None:
        """Start shared listeners and build the initial room snapshot."""
        if self._started:
            return
        self._started = True

        await self.async_config_entry_first_refresh()

        entities = room_source_entities(self.hass, self.entry, self.subentry)
        if entities:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass,
                    entities,
                    self._handle_source_change,
                )
            )

        if self.subentry.data.get(CONF_WINDOWS):
            self._unsubs.append(
                async_dispatcher_connect(
                    self.hass,
                    tracker_signal(
                        self.entry.entry_id,
                        self.subentry.subentry_id,
                    ),
                    self._handle_tracker_change,
                )
            )

        if self.subentry.data.get(CONF_CO2):
            self._unsubs.append(
                async_dispatcher_connect(
                    self.hass,
                    co2_tracker_signal(
                        self.entry.entry_id,
                        self.subentry.subentry_id,
                    ),
                    self._handle_tracker_change,
                )
            )

        if self.subentry.data.get(CONF_SURFACE_TEMP):
            # Surface persistence is time-dependent. Refresh periodically even
            # when the sensor value itself is unchanged so a genuinely long
            # critical period can influence the advice later.
            self._unsubs.append(
                async_track_time_interval(
                    self.hass,
                    lambda _now: self._handle_tracker_change(),
                    MOLD_SAMPLE_INTERVAL,
                )
            )

    @callback
    def _handle_source_change(self, event: Event) -> None:
        snapshot = self._build_snapshot()
        self.async_set_updated_data(snapshot)
        self.hass.async_create_task(
            async_handle_room_notification(self.hass, self.entry, self.subentry, snapshot),
            f"Lüftungsberater notification check {self.subentry.subentry_id}",
        )

    @callback
    def _handle_tracker_change(self) -> None:
        # Tracker callbacks already run in HA's event loop, so we can refresh
        # synchronously and immediately notify every entity of the room.
        snapshot = self._build_snapshot()
        self.async_set_updated_data(snapshot)
        self.hass.async_create_task(
            async_handle_room_notification(self.hass, self.entry, self.subentry, snapshot),
            f"Lüftungsberater notification check {self.subentry.subentry_id}",
        )

    async def async_shutdown(self) -> None:
        """Remove shared listeners and shut down the HA coordinator."""
        while self._unsubs:
            self._unsubs.pop()()
        clear_room_notification_state(
            self.hass, self.entry.entry_id, self.subentry.subentry_id
        )
        self._started = False
        await super().async_shutdown()


def _coordinator_key(entry: ConfigEntry, subentry: ConfigSubentry) -> str:
    return f"{entry.entry_id}:{subentry.subentry_id}"


async def async_get_or_create_room_coordinator(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> LueftungsberaterRoomCoordinator:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_COORDINATORS, {})
    key = _coordinator_key(entry, subentry)
    coordinator = store.get(key)
    if coordinator is None:
        coordinator = LueftungsberaterRoomCoordinator(hass, entry, subentry)
        store[key] = coordinator
        await coordinator.async_start()
    return coordinator


def get_room_coordinator(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
) -> LueftungsberaterRoomCoordinator | None:
    return (
        hass.data.get(DOMAIN, {})
        .get(DATA_COORDINATORS, {})
        .get(_coordinator_key(entry, subentry))
    )


async def async_stop_entry_coordinators(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    store = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {})
    prefix = f"{entry.entry_id}:"
    for key in [item for item in store if item.startswith(prefix)]:
        # DataUpdateCoordinator registered async_shutdown on the config entry.
        # Remove our lookup reference here; HA calls the coordinator shutdown
        # callback as part of the same config-entry unload.
        store.pop(key)

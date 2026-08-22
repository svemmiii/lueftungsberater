"""Base entity shared by Lüftungsberater platforms."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.event import async_track_state_change_event

from .airing import tracker_signal
from .co2 import co2_tracker_signal
from .const import CONF_CO2, CONF_WINDOWS, DOMAIN
from .runtime import room_source_entities


class LueftungsberaterRoomEntity(Entity):
    """Base entity for one configured room."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        self.entry = entry
        self.subentry = subentry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.subentry.subentry_id)},
            name=f"Lüftungsberater {self.subentry.title}",
            manufacturer="Lüftungsberater",
            model="Raum-Lüftungsberater",
            sw_version="0.6.2",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        entities = room_source_entities(self.hass, self.entry, self.subentry)
        if entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    entities,
                    self._handle_source_change,
                )
            )

        if self.subentry.data.get(CONF_WINDOWS):
            self.async_on_remove(
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
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    co2_tracker_signal(
                        self.entry.entry_id,
                        self.subentry.subentry_id,
                    ),
                    self._handle_tracker_change,
                )
            )

    async def _handle_source_change(self, event) -> None:
        self.async_write_ha_state()

    def _handle_tracker_change(self) -> None:
        self.async_write_ha_state()

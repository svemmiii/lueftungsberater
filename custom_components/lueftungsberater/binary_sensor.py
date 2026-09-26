"""Binary sensor platform for Lüftungsberater."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import MATCH_ALL
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CONF_NINA_STATUS,
    CONF_WEATHER,
    CONF_WEATHER_DANGER,
    SUBENTRY_TYPE_ROOM,
    SUBENTRY_TYPE_STATION,
    CONF_HARDWARE_ID,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .coordinator import async_get_or_create_room_coordinator
from .entity import LueftungsberaterRoomEntity
from .hardware_hub import master_device_id, station_is_fresh, station_is_master, station_runtime, station_signal
from .runtime import warning_source_configured
from .localization import reason_text


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up hardware online state and optional room danger entities."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_STATION and station_is_master(subentry):
            async_add_entities(
                [HardwareStationOnlineBinarySensor(entry, subentry)],
                config_subentry_id=subentry.subentry_id,
            )

    has_warning_source = (
        warning_source_configured(entry)
        or bool(entry.data.get(CONF_WEATHER))
        or bool(entry.data.get(CONF_WEATHER_DANGER))
        or bool(entry.data.get(CONF_NINA_STATUS))
    )
    if not has_warning_source:
        return

    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        coordinator = await async_get_or_create_room_coordinator(
            hass, entry, subentry
        )
        async_add_entities(
            [RoomDangerBinarySensor(entry, subentry, coordinator)],
            config_subentry_id=subentry.subentry_id,
        )


class RoomDangerBinarySensor(LueftungsberaterRoomEntity, BinarySensorEntity):
    """Critical ventilation danger for one room."""

    _unrecorded_attributes = frozenset({MATCH_ALL})

    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_translation_key = "critical_danger"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_critical_danger"

    @property
    def is_on(self):
        result = self.snapshot.result if self.snapshot else None
        return result is not None and result.safety_lock

    @property
    def extra_state_attributes(self):
        result = self.snapshot.result if self.snapshot else None
        if not result:
            return {}
        return {
            "reason": reason_text(
                result.reason_key,
                result.reason_args,
                self.hass.config.language,
                str(self.hass.config.units.temperature_unit),
            ),
            "reason_key": result.reason_key,
            "original_warning_text": result.original_reason,
        }


class HardwareStationOnlineBinarySensor(BinarySensorEntity):
    """Connectivity state reported by the physical station/master path."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Verbindung"

    def __init__(self, entry, subentry) -> None:
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = f"{subentry.subentry_id}_online"

    @property
    def is_on(self):
        state = station_runtime(self.hass, self.entry.entry_id, self.subentry.subentry_id)
        return station_is_fresh(state)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"station:{self.subentry.data.get(CONF_HARDWARE_ID)}")},
            name=f"{self.entry.title} · {self.subentry.title}",
            manufacturer="Lüftungsassistent",
            model="ESP32 Lüftungsstation (SCD41 + Display)",
            sw_version=INTEGRATION_VERSION,
            via_device_id=master_device_id(self.hass, self.entry.entry_id),
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                station_signal(self.entry.entry_id, self.subentry.subentry_id),
                self.async_write_ha_state,
            )
        )

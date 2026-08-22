"""Binary sensor platform for Lüftungsberater."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_NINA_STATUS, CONF_WEATHER_DANGER, SUBENTRY_TYPE_ROOM
from .entity import LueftungsberaterRoomEntity
from .runtime import build_result


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up danger entities only when warning sources are configured."""
    has_warning_source = bool(
        entry.data.get(CONF_WEATHER_DANGER) or entry.data.get(CONF_NINA_STATUS)
    )
    if not has_warning_source:
        return

    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        async_add_entities(
            [RoomDangerBinarySensor(entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class RoomDangerBinarySensor(LueftungsberaterRoomEntity, BinarySensorEntity):
    """Critical ventilation danger for one room."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_translation_key = "critical_danger"

    def __init__(self, entry, subentry):
        super().__init__(entry, subentry)
        self._attr_unique_id = f"{subentry.subentry_id}_critical_danger"

    @property
    def is_on(self):
        result = build_result(self.hass, self.entry, self.subentry)
        return result is not None and result.mode in {
            "nina_aussenluftgefahr",
            "wettergefahr",
        }

    @property
    def extra_state_attributes(self):
        result = build_result(self.hass, self.entry, self.subentry)
        return {"reason": result.reason} if result else {}

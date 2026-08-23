"""Base entity shared by Lüftungsberater platforms."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LueftungsberaterRoomCoordinator


class LueftungsberaterRoomEntity(
    CoordinatorEntity[LueftungsberaterRoomCoordinator]
):
    """Base entity for one configured room using its shared coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        coordinator: LueftungsberaterRoomCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.subentry = subentry

    @property
    def snapshot(self):
        """Return the latest shared room snapshot."""
        return self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.subentry.subentry_id)},
            name=f"{self.entry.title} · {self.subentry.title}",
            manufacturer="Lüftungsberater",
            model=(
                "Raum-Lüftungsberater"
                if str(self.hass.config.language).lower().startswith("de")
                else (
                    "Oda havalandırma danışmanı"
                    if str(self.hass.config.language).lower().startswith("tr")
                    else "Room ventilation advisor"
                )
            ),
            sw_version="0.6.14",
        )

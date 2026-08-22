"""Sensor platform for Lüftungsberater."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .airing import get_tracker
from .const import (
    CONF_CLIMATE,
    CONF_CO2,
    CONF_INDOOR_HUMIDITY,
    CONF_INDOOR_TEMP,
    CONF_NINA_STATUS,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMP,
    CONF_WEATHER_DANGER,
    CONF_WEATHER_REASON,
    CONF_WINDOWS,
    DOMAIN,
    SUBENTRY_TYPE_ROOM,
)
from .coordinator import async_get_or_create_room_coordinator
from .entity import LueftungsberaterRoomEntity


RECOMMENDATION_STATES = {
    "Jetzt lüften": "open_now",
    "Weiter lüften": "keep_open",
    "Lüften kann beendet werden": "can_close",
    "Nur kurz unter Beobachtung": "short_observation",
    "Besser schließen": "better_close",
    "Vorsicht – lieber geschlossen lassen": "caution_keep_closed",
    "Geschlossen lassen": "keep_closed",
    "Jetzt schließen": "close_now",
    "Noch nicht nötig / besser warten": "wait",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up room sensors."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue

        coordinator = await async_get_or_create_room_coordinator(
            hass, entry, subentry
        )

        entities: list[SensorEntity] = [
            RoomAdvisorSensor(entry, subentry, coordinator),
            RoomAbsoluteHumiditySensor(entry, subentry, coordinator),
        ]

        if subentry.data.get(CONF_CO2):
            entities.append(RoomCo2StatusSensor(entry, subentry, coordinator))

        if subentry.data.get(CONF_WINDOWS):
            entities.extend(
                [
                    RoomAiringStatusSensor(entry, subentry, coordinator),
                    RoomLastAiringSensor(entry, subentry, coordinator),
                    RoomHoursSinceAiringSensor(entry, subentry, coordinator),
                ]
            )

        async_add_entities(entities, config_subentry_id=subentry.subentry_id)


class RoomAdvisorSensor(LueftungsberaterRoomEntity, SensorEntity):
    """Main recommendation for one room."""

    _attr_translation_key = "advisor"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(RECOMMENDATION_STATES.values())

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_advisor"
        self._attr_name = None

    @property
    def native_value(self):
        result = self.snapshot.result if self.snapshot else None
        if result is None:
            return None
        return RECOMMENDATION_STATES.get(result.recommendation, "wait")

    @property
    def icon(self) -> str:
        result = self.snapshot.result if self.snapshot else None
        if result is None:
            return "mdi:window-closed-variant"
        if result.color == "green":
            return "mdi:window-open-variant"
        if result.color == "red":
            return "mdi:window-closed-variant"
        return "mdi:window-open"

    @property
    def extra_state_attributes(self):
        snapshot = self.snapshot
        r = snapshot.result if snapshot else None
        if not r:
            return {}

        values = snapshot.values
        weather = snapshot.weather
        warnings = snapshot.warnings
        last_airing = values["last_confirmed_airing"]

        registry = er.async_get(self.hass)
        airing_entity = registry.async_get_entity_id(
            "sensor",
            DOMAIN,
            f"{self.subentry.subentry_id}_airing_status",
        )
        last_airing_entity = registry.async_get_entity_id(
            "sensor",
            DOMAIN,
            f"{self.subentry.subentry_id}_last_airing",
        )
        absolute_humidity_entity = registry.async_get_entity_id(
            "sensor",
            DOMAIN,
            f"{self.subentry.subentry_id}_absolute_humidity",
        )

        return {
            "room_name": self.subentry.title,
            "status": r.color,
            "recommendation": r.recommendation,
            "mode": r.mode,
            "reason": r.reason,
            "duration": r.duration,
            "co2_status": r.co2_status,
            "co2_data_status": values.get("co2_data_status", "not_configured"),
            "co2_ppm": (
                round(values["co2_ppm"])
                if values["co2_ppm"] is not None
                else None
            ),
            "temperature_inside": values["temperature_inside"],
            "temperature_outside": values["temperature_outside"],
            "target_temperature": values["target_temperature"],
            "temperature_unit_internal": "°C",
            "temperature_display_unit": str(
                self.hass.config.units.temperature_unit
            ),
            "humidity_inside": values["humidity_inside"],
            "humidity_outside": values["humidity_outside"],
            "absolute_humidity_inside": r.indoor_absolute_humidity,
            "absolute_humidity_outside": r.outdoor_absolute_humidity,
            "absolute_humidity_difference": r.absolute_humidity_difference,
            "has_co2": values["has_co2"],
            "has_window_contacts": values["has_window_contacts"],
            "window_open": values["window_open"],
            "open_minutes": (
                round(values["open_minutes"], 1)
                if values["open_minutes"] is not None
                else None
            ),
            "last_confirmed_airing": (
                last_airing.isoformat()
                if last_airing is not None
                else None
            ),
            "hours_since_last_airing": (
                round(values["hours_since_last_airing"], 2)
                if values["hours_since_last_airing"] is not None
                else None
            ),

            # Source entities for clickable dashboard values.
            # These are UI metadata only and are not used by engine.py.
            "source_temperature_inside": self.subentry.data.get(CONF_INDOOR_TEMP),
            "source_temperature_outside": weather.source_temperature,
            "source_target_temperature": self.subentry.data.get(CONF_CLIMATE),
            "source_humidity_inside": self.subentry.data.get(CONF_INDOOR_HUMIDITY),
            "source_humidity_outside": weather.source_humidity,
            "outdoor_temperature_source": weather.temperature_source_kind,
            "outdoor_humidity_source": weather.humidity_source_kind,
            "source_absolute_humidity_inside": absolute_humidity_entity,
            "source_co2": self.subentry.data.get(CONF_CO2),
            "source_airing": airing_entity,
            "source_last_airing": last_airing_entity,
            "source_window_entities": list(
                self.subentry.data.get(CONF_WINDOWS, []) or []
            ),
            "source_weather_reason": (
                next(iter(warnings.source_entities), None)
                or self.entry.data.get(CONF_WEATHER_REASON)
            ),
            "source_weather_danger": (
                next(iter(warnings.source_entities), None)
                or self.entry.data.get(CONF_WEATHER_DANGER)
            ),
            "source_nina_status": (
                next(iter(warnings.source_entities), None)
                or self.entry.data.get(CONF_NINA_STATUS)
            ),
            "weather_provider": weather.provider_domain,
            "warning_provider": warnings.provider_domain,
            "radar_current_entity": weather.radar_current_entity,
            "radar_next_entity": weather.radar_next_entity,
        }


class RoomAbsoluteHumiditySensor(LueftungsberaterRoomEntity, SensorEntity):
    """Absolute indoor humidity."""

    _attr_icon = "mdi:water-percent"
    _attr_native_unit_of_measurement = "g/m³"
    _attr_suggested_display_precision = 1
    _attr_translation_key = "absolute_humidity"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_absolute_humidity"

    @property
    def native_value(self):
        result = self.snapshot.result if self.snapshot else None
        return result.indoor_absolute_humidity if result else None

    @property
    def extra_state_attributes(self):
        result = self.snapshot.result if self.snapshot else None
        if not result:
            return {}
        return {
            "outside": result.outdoor_absolute_humidity,
            "difference": result.absolute_humidity_difference,
        }


class RoomCo2StatusSensor(LueftungsberaterRoomEntity, SensorEntity):
    """Human-readable CO2 assessment for a configured CO2 sensor."""

    _attr_icon = "mdi:molecule-co2"
    _attr_translation_key = "co2_status"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_co2_status"

    @property
    def native_value(self):
        result = self.snapshot.result if self.snapshot else None
        return result.co2_status if result else None

    @property
    def extra_state_attributes(self):
        values = self.snapshot.values if self.snapshot else {}
        ppm = values.get("co2_ppm")
        return {
            "ppm": round(ppm) if ppm is not None else None,
            "data_status": values.get("co2_data_status", "unavailable"),
        }


class RoomAiringStatusSensor(LueftungsberaterRoomEntity, SensorEntity):
    """Current airing/window state."""

    _attr_translation_key = "airing_status"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_airing_status"

    @property
    def native_value(self):
        tracker = get_tracker(self.hass, self.entry, self.subentry)
        if tracker is None:
            return None
        return "airing" if tracker.is_open else "closed"

    @property
    def icon(self) -> str:
        return (
            "mdi:window-open-variant"
            if self.native_value == "airing"
            else "mdi:window-closed-variant"
        )

    @property
    def extra_state_attributes(self):
        tracker = get_tracker(self.hass, self.entry, self.subentry)
        if tracker is None:
            return {}

        open_windows = [
            entity_id
            for entity_id in tracker.windows
            if self.hass.states.is_state(entity_id, "on")
        ]
        return {
            "open_contacts": open_windows,
            "configured_contacts": len(tracker.windows),
            "open_since": (
                tracker.open_since.isoformat() if tracker.open_since else None
            ),
            "open_minutes": (
                round(tracker.current_open_minutes, 1)
                if tracker.current_open_minutes is not None
                else None
            ),
            "last_confirmed_airing": (
                tracker.last_confirmed_airing.isoformat()
                if tracker.last_confirmed_airing
                else None
            ),
            "hours_since_last_airing": (
                round(tracker.hours_since_last_airing, 2)
                if tracker.hours_since_last_airing is not None
                else None
            ),
            "confirmation_minutes": 5,
        }


class RoomLastAiringSensor(LueftungsberaterRoomEntity, SensorEntity):
    """Timestamp of the last confirmed airing."""

    _attr_translation_key = "last_airing"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:history"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_last_airing"

    @property
    def native_value(self):
        tracker = get_tracker(self.hass, self.entry, self.subentry)
        return tracker.last_confirmed_airing if tracker else None


class RoomHoursSinceAiringSensor(LueftungsberaterRoomEntity, SensorEntity):
    """Hours elapsed since the last confirmed airing."""

    _attr_translation_key = "hours_since_airing"
    _attr_native_unit_of_measurement = "h"
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:timer-sand"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_hours_since_airing"

    @property
    def native_value(self):
        tracker = get_tracker(self.hass, self.entry, self.subentry)
        if tracker is None or tracker.hours_since_last_airing is None:
            return None
        return round(tracker.hours_since_last_airing, 2)

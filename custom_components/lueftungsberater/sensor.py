"""Sensor platform for Lüftungsberater."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import MATCH_ALL
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .airing import get_tracker
from .api import remote_access_info
from .const import (
    CONF_CLIMATE,
    CONF_DISPLAY_MODE,
    CONF_CO2,
    CONF_INDOOR_HUMIDITY,
    CONF_INDOOR_TEMP,
    CONF_MANUAL_OUTDOOR,
    CONF_SURFACE_TEMP,
    CONF_NINA_STATUS,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_CO2,
    CONF_OUTDOOR_TEMP,
    CONF_WEATHER_DANGER,
    CONF_WEATHER_REASON,
    CONF_WINDOWS,
    CONF_REMOTE_ROOM_SHARE,
    DOMAIN,
    DEFAULT_DISPLAY_MODE,
    DISPLAY_MODE_ROOM_AIR,
    SUBENTRY_TYPE_ROOM,
)
from .coordinator import async_get_or_create_room_coordinator
from .entity import LueftungsberaterRoomEntity
from .engine import co2_status
from .localization import (
    duration_text,
    night_advice_text,
    reason_text,
    recommendation_text,
)


RECOMMENDATION_STATES = [
    "open_now",
    "keep_open",
    "can_close",
    "short_observation",
    "optional",
    "better_close",
    "caution_keep_closed",
    "keep_closed",
    "close_now",
    "wait",
]


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

        # Register the derived humidity sensors before the advisor so the advisor
        # can expose their entity IDs as clickable source attributes immediately.
        entities: list[SensorEntity] = [
            RoomAbsoluteHumiditySensor(entry, subentry, coordinator),
            RoomOutdoorAbsoluteHumiditySensor(entry, subentry, coordinator),
            RoomAbsoluteHumidityDifferenceSensor(entry, subentry, coordinator),
            RoomAdvisorSensor(entry, subentry, coordinator),
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
    _attr_options = RECOMMENDATION_STATES
    # The recommendation state itself is worth keeping in Recorder history.
    # The large dynamic attribute bundle exists for the custom card and would
    # otherwise create a recorder row whenever a presentation-only value changes.
    _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_advisor"
        self._attr_name = None
        self._derived_entity_cache: dict[str, str | None] | None = None

    @property
    def native_value(self):
        result = self.snapshot.result if self.snapshot else None
        if result is None:
            return None
        # Keep the entity state as the stable action/automation interface. The
        # selected traffic-light perspective only changes the card attributes
        # (colour, short recommendation and reason), so existing automations do
        # not change semantics when a user switches the visual mode.
        return result.recommendation_key

    @property
    def icon(self) -> str:
        result = self.snapshot.result if self.snapshot else None
        if result is None:
            return "mdi:window-closed-variant"
        if result.safety_lock:
            return "mdi:lock"
        display_mode = self.entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE)
        if display_mode == DISPLAY_MODE_ROOM_AIR:
            return "mdi:air-filter"
        if result.color == "green":
            return "mdi:window-open-variant"
        if result.color in {"orange", "red"}:
            return "mdi:window-closed-variant"
        return "mdi:window-open"


    @property
    def extra_state_attributes(self):
        snapshot = self.snapshot
        if not snapshot:
            return {}

        r = snapshot.result
        values = snapshot.values
        weather = snapshot.weather
        warnings = snapshot.warnings
        last_airing = values["last_confirmed_airing"]

        registry = er.async_get(self.hass)
        unique_ids = {
            "airing": f"{self.subentry.subentry_id}_airing_status",
            "last_airing": f"{self.subentry.subentry_id}_last_airing",
            "absolute_humidity": f"{self.subentry.subentry_id}_absolute_humidity",
            "absolute_humidity_outside": f"{self.subentry.subentry_id}_absolute_humidity_outside",
            "absolute_humidity_difference": f"{self.subentry.subentry_id}_absolute_humidity_difference",
            "co2_status": f"{self.subentry.subentry_id}_co2_status",
        }
        if self._derived_entity_cache is None:
            self._derived_entity_cache = {
                key: registry.async_get_entity_id("sensor", DOMAIN, unique_id)
                for key, unique_id in unique_ids.items()
            }
        else:
            # User renames are rare, but do not keep a stale cached entity id.
            # A first render can also happen before the sibling entities have
            # finished registering, so retry entries which were initially None.
            for key, entity_id in tuple(self._derived_entity_cache.items()):
                if entity_id is None or registry.async_get(entity_id) is None:
                    self._derived_entity_cache[key] = registry.async_get_entity_id(
                        "sensor", DOMAIN, unique_ids[key]
                    )

        airing_entity = self._derived_entity_cache["airing"]
        last_airing_entity = self._derived_entity_cache["last_airing"]
        absolute_humidity_entity = self._derived_entity_cache["absolute_humidity"]
        outdoor_absolute_humidity_entity = self._derived_entity_cache["absolute_humidity_outside"]
        absolute_humidity_difference_entity = self._derived_entity_cache["absolute_humidity_difference"]
        co2_status_entity = self._derived_entity_cache["co2_status"]

        language = self.hass.config.language
        temperature_unit = str(self.hass.config.units.temperature_unit)
        display_mode = self.entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE)

        if r is None:
            recommendation_key = "unknown"
            reason_key = "incomplete_data"
            reason_args: dict = {}
            duration_key = "incomplete_data"
            status = "yellow"
            mode = "incomplete_data"
            original_reason = None
            indoor_absolute_humidity = None
            outdoor_absolute_humidity = None
            absolute_humidity_difference = None
            current_co2_status = co2_status(values.get("co2_ppm"))
        else:
            display_mode = self.entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE)
            room_view = display_mode == DISPLAY_MODE_ROOM_AIR and not r.safety_lock
            recommendation_key = (
                r.room_recommendation_key if room_view else r.recommendation_key
            )
            reason_key = r.room_reason_key if room_view else r.reason_key
            reason_args = dict(r.room_reason_args if room_view else r.reason_args)
            duration_key = r.duration_key
            status = (
                "locked"
                if r.safety_lock
                else (r.room_status_color if room_view else r.color)
            )
            mode = r.mode
            original_reason = r.original_reason
            indoor_absolute_humidity = r.indoor_absolute_humidity
            outdoor_absolute_humidity = r.outdoor_absolute_humidity
            absolute_humidity_difference = r.absolute_humidity_difference
            current_co2_status = r.co2_status

        night_key = values.get("night_ventilation_key")
        night_args = dict(values.get("night_ventilation_args") or {})
        remote_active, remote_clients = remote_access_info(
            self.hass, self.entry.entry_id, self.subentry.subentry_id
        )

        attrs = {
            "instance_id": self.entry.entry_id,
            "instance_name": self.entry.title,
            "room_name": self.subentry.title,
            "remote_shared": bool(self.subentry.data.get(CONF_REMOTE_ROOM_SHARE, True)),
            "status": status,
            "display_mode": display_mode,
            "safety_lock": bool(r.safety_lock) if r is not None else False,
            "ventilation_status": r.color if r is not None else "yellow",
            "room_status": r.room_status_color if r is not None else "yellow",
            "recommendation": recommendation_text(recommendation_key, language),
            "recommendation_key": recommendation_key,
            "mode": mode,
            "reason": reason_text(
                reason_key, reason_args, language, temperature_unit
            ),
            "reason_key": reason_key,
            "reason_args": reason_args,
            "duration": duration_text(duration_key, language),
            "duration_key": duration_key,
            "co2_status": current_co2_status,
            "co2_data_status": values.get("co2_data_status", "not_configured"),
            "co2_ppm": (
                round(values["co2_ppm"])
                if values["co2_ppm"] is not None
                else None
            ),
            "outdoor_co2_ppm": (
                round(values["outdoor_co2_ppm"])
                if values.get("outdoor_co2_ppm") is not None
                else None
            ),
            "co2_difference": (r.co2_difference if r is not None else None),
            "temperature_inside": values["temperature_inside"],
            "temperature_outside": values["temperature_outside"],
            "target_temperature": values["target_temperature"],
            "temperature_display_unit": temperature_unit,
            "humidity_inside": values["humidity_inside"],
            "humidity_outside": values["humidity_outside"],
            "absolute_humidity_inside": indoor_absolute_humidity,
            "absolute_humidity_outside": outdoor_absolute_humidity,
            "absolute_humidity_difference": absolute_humidity_difference,
            "surface_temperature": values.get("surface_temperature"),
            "surface_relative_humidity": (
                r.surface_relative_humidity if r is not None else None
            ),
            "mold_risk": bool(r.mold_risk) if r is not None else False,
            "mold_persistent": bool(r.mold_persistent) if r is not None else False,
            "mold_current_critical_minutes": (
                r.mold_current_critical_minutes if r is not None else None
            ),
            "mold_critical_minutes_24h": (
                r.mold_critical_minutes_24h if r is not None else None
            ),
            "air_quality": r.air_quality if r is not None else weather.air_quality_index,
            "air_quality_pollutant": (
                r.air_quality_pollutant if r is not None else weather.air_quality_pollutant
            ),
            "air_quality_value": (
                r.air_quality_value if r is not None else weather.air_quality_value
            ),
            "air_quality_values": dict(weather.air_quality_values),
            "air_quality_baseline_value": values.get("air_quality_baseline_value"),
            "air_quality_typical": values.get("air_quality_typical"),
            "air_quality_unusual": values.get("air_quality_unusual", False),
            "air_quality_trend": values.get("air_quality_trend", "unknown"),
            "air_quality_history_samples": values.get("air_quality_history_samples", 0),
            "wind_speed_kmh": weather.wind_speed_kmh,
            "wind_gust_kmh": weather.wind_gust_kmh,
            "rain_minutes_until": weather.rain_minutes_until,
            "night_ventilation_status": values.get("night_ventilation_status", "unavailable"),
            "night_ventilation_key": night_key,
            "night_ventilation_args": night_args,
            "night_ventilation": night_advice_text(
                night_key, night_args, language, temperature_unit
            ),
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
            "source_absolute_humidity_outside": outdoor_absolute_humidity_entity,
            "source_absolute_humidity_difference": absolute_humidity_difference_entity,
            "source_co2": self.subentry.data.get(CONF_CO2),
            "source_outdoor_co2": (
                (self.entry.data.get(CONF_MANUAL_OUTDOOR) or {}).get(CONF_OUTDOOR_CO2)
                if isinstance(self.entry.data.get(CONF_MANUAL_OUTDOOR), dict)
                else self.entry.data.get(CONF_OUTDOOR_CO2)
            ),
            "source_surface_temperature": self.subentry.data.get(CONF_SURFACE_TEMP),
            "source_co2_status": co2_status_entity,
            "source_airing": airing_entity,
            "source_last_airing": last_airing_entity,
            "source_window_entities": list(
                self.subentry.data.get(CONF_WINDOWS, []) or []
            ),
            "source_weather_reason": (
                warnings.source_weather_entity
                or self.entry.data.get(CONF_WEATHER_REASON)
            ),
            "source_weather_danger": (
                warnings.source_weather_entity
                or self.entry.data.get(CONF_WEATHER_DANGER)
            ),
            "source_nina_status": (
                warnings.source_nina_entity
                or self.entry.data.get(CONF_NINA_STATUS)
            ),
            "weather_provider": weather.provider_domain,
            "warning_provider": warnings.provider_domain,
            "radar_current_entity": weather.radar_current_entity,
            "radar_next_entity": weather.radar_next_entity,
        }
        # Keep rarely used transient metadata out of the normal attribute list.
        # The custom card treats missing values as false/empty, so nothing visible
        # is lost while the state inspector stays significantly smaller.
        if remote_active:
            attrs["remote_access_active"] = True
            attrs["remote_access_count"] = len(remote_clients)
            attrs["remote_access_clients"] = remote_clients
        if original_reason:
            attrs["original_warning_text"] = original_reason
        if warnings.warning_notice_kind:
            attrs["warning_notice_kind"] = warnings.warning_notice_kind
        if warnings.warning_notice_text:
            attrs["warning_notice_text"] = warnings.warning_notice_text
        if warnings.official_close_instruction:
            attrs["official_close_instruction"] = True
        return attrs


class RoomAbsoluteHumiditySensor(LueftungsberaterRoomEntity, SensorEntity):
    """Absolute indoor humidity."""

    _unrecorded_attributes = frozenset({"outside", "difference"})

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


class RoomOutdoorAbsoluteHumiditySensor(LueftungsberaterRoomEntity, SensorEntity):
    """Absolute outdoor humidity with its own recorder history."""

    _attr_icon = "mdi:water-outline"
    _attr_native_unit_of_measurement = "g/m³"
    _attr_suggested_display_precision = 1
    _attr_translation_key = "absolute_humidity_outside"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_absolute_humidity_outside"

    @property
    def native_value(self):
        result = self.snapshot.result if self.snapshot else None
        return result.outdoor_absolute_humidity if result else None


class RoomAbsoluteHumidityDifferenceSensor(LueftungsberaterRoomEntity, SensorEntity):
    """Absolute humidity difference between indoor and outdoor air."""

    _attr_icon = "mdi:water-sync"
    _attr_native_unit_of_measurement = "g/m³"
    _attr_suggested_display_precision = 1
    _attr_translation_key = "absolute_humidity_difference"

    def __init__(self, entry, subentry, coordinator):
        super().__init__(entry, subentry, coordinator)
        self._attr_unique_id = f"{subentry.subentry_id}_absolute_humidity_difference"

    @property
    def native_value(self):
        result = self.snapshot.result if self.snapshot else None
        return result.absolute_humidity_difference if result else None


class RoomCo2StatusSensor(LueftungsberaterRoomEntity, SensorEntity):
    """Human-readable CO2 assessment for a configured CO2 sensor."""

    _unrecorded_attributes = frozenset({"ppm", "data_status"})

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

    _unrecorded_attributes = frozenset({MATCH_ALL})

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
        # The UI already displays one decimal place. Recording hundredths of an
        # hour would create a new Recorder state roughly every 36 seconds without
        # adding useful historical precision.
        return round(tracker.hours_since_last_airing, 1)

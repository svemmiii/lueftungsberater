"""Shared outside/weather/warning coordinator per local advisor."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .air_quality import get_air_quality_tracker
from .const import (
    CONF_MANUAL_OUTDOOR,
    CONF_OUTDOOR_CO2,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMP,
    CONF_RAIN_NOW,
    CONF_RAIN_SOON,
    CONF_WEATHER_DANGER,
    CONF_WARNING_SOURCE,
    CONF_WEATHER_REASON,
    CONF_NINA_STATUS,
    DATA_OUTSIDE_COORDINATORS,
    DOMAIN,
    FORECAST_REFRESH_INTERVAL,
)
from .providers import (
    NINA_DETAILS_CACHE_MAX_AGE,
    WeatherAssessment,
    WarningAssessment,
    async_refresh_hourly_forecast,
    async_refresh_nina_details,
    weather_assessment,
    warning_assessment,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class OutsideSnapshot:
    weather: WeatherAssessment
    warnings: WarningAssessment


def _uses_home_assistant_nina(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    source = entry.data.get(CONF_WARNING_SOURCE)
    if not isinstance(source, str) or not source:
        return False
    source_entry = hass.config_entries.async_get_entry(source)
    return source_entry is not None and source_entry.domain == "nina"


def _configured_outside_entities(entry: ConfigEntry) -> set[str]:
    entities: set[str] = set()
    manual = entry.data.get(CONF_MANUAL_OUTDOOR)
    if isinstance(manual, dict):
        for key in (CONF_OUTDOOR_TEMP, CONF_OUTDOOR_HUMIDITY, CONF_OUTDOOR_CO2):
            value = manual.get(key)
            if isinstance(value, str) and value:
                entities.add(value)
    for key in (
        CONF_OUTDOOR_TEMP,
        CONF_OUTDOOR_HUMIDITY,
        CONF_OUTDOOR_CO2,
        CONF_WEATHER_DANGER,
        CONF_WEATHER_REASON,
        CONF_NINA_STATUS,
        CONF_RAIN_NOW,
        CONF_RAIN_SOON,
    ):
        value = entry.data.get(key)
        if isinstance(value, str) and value:
            entities.add(value)
    return entities


class LueftungsberaterOutsideCoordinator(DataUpdateCoordinator[OutsideSnapshot]):
    """Normalize outside information once and fan it out to every room."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}_outside",
            update_interval=None,
            always_update=False,
        )
        self.entry = entry
        self._unsubs: list[Callable[[], None]] = []
        self._source_unsub: Callable[[], None] | None = None
        self._source_entities: set[str] = set()
        self._registry_refresh_pending = False
        self._started = False

    async def _async_update_data(self) -> OutsideSnapshot:
        # Keep one small shared hourly-forecast cache warm all day. The normal
        # live card only looks at the next hour, while the night strategy can
        # use the wider forecast later. This stays one provider call per advisor
        # and is cache-limited to avoid per-room polling.
        await async_refresh_hourly_forecast(self.hass, self.entry)
        await async_refresh_nina_details(self.hass, self.entry)
        weather = weather_assessment(self.hass, self.entry)
        warnings = warning_assessment(self.hass, self.entry)
        tracker = get_air_quality_tracker(self.hass, self.entry)
        if tracker is not None and weather.air_quality_values:
            tracker.observe(weather.air_quality_values)
        return OutsideSnapshot(weather=weather, warnings=warnings)

    async def async_start(self) -> None:
        if self._started:
            return
        self._started = True
        await self.async_config_entry_first_refresh()

        self._replace_source_listener()

        # Provider integrations can add/rename/remove entities after this
        # coordinator has started. Re-discover sources on registry changes so a
        # newly created NINA/weather entity becomes event-driven without a
        # Lüftungsberater reload. Registry changes are rare and are collapsed
        # while one refresh is already pending.
        self._unsubs.append(
            self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED,
                self._handle_registry_change,
            )
        )

        # One forecast refresh per advisor instead of one timer per room.
        self._unsubs.append(
            async_track_time_interval(
                self.hass,
                self._handle_forecast_tick,
                FORECAST_REFRESH_INTERVAL,
            )
        )
        # NINA detail fields can change while a slot/id stays stable. Entity
        # events normally refresh us immediately; this sparse fallback makes the
        # five-minute detail TTL effective even when Home Assistant suppresses a
        # same-state update after the legacy long attributes disappear.
        if _uses_home_assistant_nina(self.hass, self.entry):
            self._unsubs.append(
                async_track_time_interval(
                    self.hass,
                    self._handle_nina_detail_tick,
                    NINA_DETAILS_CACHE_MAX_AGE,
                )
            )


    @callback
    def _replace_source_listener(self) -> None:
        """Subscribe to the currently discovered outside/provider entities."""
        sources = _configured_outside_entities(self.entry)
        if self.data is not None:
            sources.update(self.data.weather.source_entities)
            sources.update(self.data.warnings.source_entities)
        sources.discard("")

        if sources == self._source_entities:
            return
        if self._source_unsub is not None:
            self._source_unsub()
            self._source_unsub = None
        self._source_entities = sources
        if sources:
            self._source_unsub = async_track_state_change_event(
                self.hass,
                sources,
                self._handle_source_change,
            )

    async def _async_refresh_after_registry_change(self) -> None:
        try:
            await self.async_request_refresh()
            self._replace_source_listener()
        finally:
            self._registry_refresh_pending = False

    @callback
    def _handle_registry_change(self, event: Event) -> None:
        if self._registry_refresh_pending or not self._started:
            return
        entity_id = str(event.data.get("entity_id") or "")
        registry_entry = er.async_get(self.hass).async_get(entity_id) if entity_id else None
        # Our own room/result entities are not provider sources and are created
        # during setup, so ignore those registry events to avoid a refresh loop.
        if registry_entry is not None and registry_entry.config_entry_id == self.entry.entry_id:
            return
        self._registry_refresh_pending = True
        self.hass.async_create_task(
            self._async_refresh_after_registry_change(),
            f"Lüftungsberater provider discovery {self.entry.entry_id}",
        )

    @callback
    def _handle_forecast_tick(self, _now) -> None:
        """Refresh the shared short-term/night forecast cache."""
        self.hass.async_create_task(
            self.async_request_refresh(),
            f"Lüftungsberater forecast outside refresh {self.entry.entry_id}",
        )

    @callback
    def _handle_nina_detail_tick(self, _now) -> None:
        self.hass.async_create_task(
            self.async_request_refresh(),
            f"Lüftungsberater NINA detail refresh {self.entry.entry_id}",
        )

    @callback
    def _handle_source_change(self, _event: Event) -> None:
        # Warning details and forecasts may require async provider calls, so use
        # the coordinator refresh path instead of recomputing each room inline.
        self.hass.async_create_task(
            self.async_request_refresh(),
            f"Lüftungsberater outside update {self.entry.entry_id}",
        )

    async def async_shutdown(self) -> None:
        if self._source_unsub is not None:
            self._source_unsub()
            self._source_unsub = None
        self._source_entities.clear()
        while self._unsubs:
            self._unsubs.pop()()
        self._registry_refresh_pending = False
        self._started = False
        await super().async_shutdown()


async def async_get_or_create_outside_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> LueftungsberaterOutsideCoordinator:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_OUTSIDE_COORDINATORS, {})
    coordinator = store.get(entry.entry_id)
    if coordinator is None:
        coordinator = LueftungsberaterOutsideCoordinator(hass, entry)
        store[entry.entry_id] = coordinator
        await coordinator.async_start()
    return coordinator


def get_outside_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> LueftungsberaterOutsideCoordinator | None:
    return hass.data.get(DOMAIN, {}).get(DATA_OUTSIDE_COORDINATORS, {}).get(entry.entry_id)


async def async_stop_outside_coordinator(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator = hass.data.get(DOMAIN, {}).get(DATA_OUTSIDE_COORDINATORS, {}).pop(entry.entry_id, None)
    if coordinator is not None:
        await coordinator.async_shutdown()

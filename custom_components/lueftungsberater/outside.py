"""Shared outside/weather/warning coordinator per local advisor."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .air_quality import get_air_quality_tracker
from .const import (
    CONF_MANUAL_OUTDOOR,
    CONF_NIGHT_START_HOUR,
    CONF_NIGHT_START_TIME,
    CONF_NIGHT_END_TIME,
    CONF_OUTDOOR_CO2,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMP,
    CONF_RAIN_NOW,
    CONF_RAIN_SOON,
    CONF_WEATHER_DANGER,
    CONF_WEATHER_REASON,
    CONF_NINA_STATUS,
    DATA_OUTSIDE_COORDINATORS,
    DEFAULT_NIGHT_START_HOUR,
    DEFAULT_NIGHT_END_TIME,
    DOMAIN,
    FORECAST_REFRESH_INTERVAL,
    SUBENTRY_TYPE_ROOM,
)
from .providers import (
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


def _night_start_minutes(subentry) -> int:
    raw = subentry.data.get(CONF_NIGHT_START_TIME)
    if isinstance(raw, str):
        parts = raw.split(":")
        try:
            hour = max(0, min(23, int(parts[0])))
            minute = max(0, min(59, int(parts[1]) if len(parts) > 1 else 0))
            return hour * 60 + minute
        except (TypeError, ValueError):
            pass
    try:
        hour = int(subentry.data.get(CONF_NIGHT_START_HOUR, DEFAULT_NIGHT_START_HOUR))
    except (TypeError, ValueError):
        hour = DEFAULT_NIGHT_START_HOUR
    return max(0, min(23, hour)) * 60


def _night_end_minutes(subentry) -> int:
    raw = subentry.data.get(CONF_NIGHT_END_TIME, DEFAULT_NIGHT_END_TIME)
    if isinstance(raw, str):
        parts = raw.split(":")
        try:
            hour = max(0, min(23, int(parts[0])))
            minute = max(0, min(59, int(parts[1]) if len(parts) > 1 else 0))
            return hour * 60 + minute
        except (TypeError, ValueError):
            pass
    try:
        hour, minute = str(DEFAULT_NIGHT_END_TIME).split(":", 1)
        return int(hour) * 60 + int(minute)
    except (TypeError, ValueError):
        return 7 * 60


def _minute_in_night_window(now_minute: int, start: int, end: int) -> bool:
    """Return whether a minute belongs to the configured daily night window."""
    start = max(0, min(1439, int(start)))
    end = max(0, min(1439, int(end)))
    now_minute = max(0, min(1439, int(now_minute)))
    if start == end:
        return True
    if start < end:
        return start <= now_minute < end
    return now_minute >= start or now_minute < end


def _night_forecast_relevant(entry: ConfigEntry) -> bool:
    """Return whether at least one room may currently show night advice."""
    now = dt_util.now()
    now_minute = now.hour * 60 + now.minute
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        if _minute_in_night_window(
            now_minute,
            _night_start_minutes(subentry),
            _night_end_minutes(subentry),
        ):
            return True
    return False


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
        self._started = False

    async def _async_update_data(self) -> OutsideSnapshot:
        # Hourly forecasts are only needed while at least one room can display
        # the night strategy. Current weather/warnings remain event-driven all
        # day, so idle daytime rooms do not keep fetching forecast data.
        if _night_forecast_relevant(self.entry):
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

        sources = _configured_outside_entities(self.entry)
        if self.data is not None:
            sources.update(self.data.weather.source_entities)
            sources.update(self.data.warnings.source_entities)
        if sources:
            self._unsubs.append(
                async_track_state_change_event(self.hass, sources, self._handle_source_change)
            )

        # One forecast refresh per advisor instead of one timer per room.
        self._unsubs.append(
            async_track_time_interval(
                self.hass,
                self._handle_forecast_tick,
                FORECAST_REFRESH_INTERVAL,
            )
        )


    @callback
    def _handle_forecast_tick(self, _now) -> None:
        """Refresh forecast/provider context only while a night hint can be shown."""
        if not _night_forecast_relevant(self.entry):
            return
        self.hass.async_create_task(
            self.async_request_refresh(),
            f"Lüftungsberater night outside refresh {self.entry.entry_id}",
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
        while self._unsubs:
            self._unsubs.pop()()
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

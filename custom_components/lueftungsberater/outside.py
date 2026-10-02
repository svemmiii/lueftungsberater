"""Shared outside/weather/warning coordinator per local advisor."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .air_quality import get_air_quality_tracker
from .auto_providers import async_refresh_auto_providers, uses_auto_warning
from .const import (
    CONF_MANUAL_OUTDOOR,
    CONF_LOCATION_TRACKER,
    CONF_OUTDOOR_CO2,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMP,
    CONF_OUTDOOR_WIND,
    CONF_OUTDOOR_GUST,
    CONF_OUTDOOR_RAIN,
    CONF_OUTDOOR_PM25,
    CONF_OUTDOOR_PM10,
    CONF_OUTDOOR_VOC,
    CONF_OUTDOOR_NO2,
    CONF_OUTDOOR_O3,
    CONF_RAIN_NOW,
    CONF_RAIN_SOON,
    CONF_WEATHER_DANGER,
    CONF_WARNING_SOURCE,
    CONF_WEATHER_REASON,
    CONF_NINA_STATUS,
    DATA_OUTSIDE_COORDINATORS,
    DOMAIN,
    FORECAST_REFRESH_INTERVAL,
    AUTO_WARNING_REFRESH_INTERVAL,
)
from .location import (
    LOCATION_MOBILE_STALE_HOLD,
    EffectiveLocation,
    effective_location,
    materially_changed,
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
from .safety_state import async_apply_persistent_safety_state

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
        for key in (
            CONF_OUTDOOR_TEMP, CONF_OUTDOOR_HUMIDITY, CONF_OUTDOOR_CO2,
            CONF_OUTDOOR_WIND, CONF_OUTDOOR_GUST, CONF_OUTDOOR_RAIN,
            CONF_OUTDOOR_PM25, CONF_OUTDOOR_PM10, CONF_OUTDOOR_VOC,
            CONF_OUTDOOR_NO2, CONF_OUTDOOR_O3,
        ):
            value = manual.get(key)
            if isinstance(value, str) and value:
                entities.add(value)
    for key in (
        CONF_OUTDOOR_TEMP,
    CONF_OUTDOOR_WIND,
    CONF_OUTDOOR_GUST,
    CONF_OUTDOOR_RAIN,
    CONF_OUTDOOR_PM25,
    CONF_OUTDOOR_PM10,
    CONF_OUTDOOR_VOC,
    CONF_OUTDOOR_NO2,
    CONF_OUTDOOR_O3,
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
    tracker = entry.data.get(CONF_LOCATION_TRACKER)
    if isinstance(tracker, str) and tracker:
        entities.add(tracker)
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
        self._accepted_location: EffectiveLocation | None = None
        self._last_valid_mobile_location: EffectiveLocation | None = None

    def _candidate_location(self) -> EffectiveLocation:
        """Return the throttled source candidate without jumping home on GPS loss."""
        current = effective_location(self.hass, self.entry)
        tracker = str(self.entry.data.get(CONF_LOCATION_TRACKER) or "").strip()
        if not tracker:
            self._last_valid_mobile_location = None
            return current
        if current.source == tracker and current.available and current.position_valid:
            self._last_valid_mobile_location = current
            return current

        # Age the grace period from the actual report, never from polling time.
        # A valid-but-stale point is useful after restart for the bounded hold.
        previous = self._last_valid_mobile_location
        if previous is None and current.position_valid and self.hass.states.get(tracker) is not None:
            state = self.hass.states.get(tracker)
            if state.state not in {"unknown", "unavailable", "none", ""} and current.updated_at < dt_util.utcnow():
                previous = current
        if (
            previous is not None
            and 0 <= (dt_util.utcnow() - previous.updated_at).total_seconds() <= LOCATION_MOBILE_STALE_HOLD.total_seconds()
        ):
            return replace(previous, available=True)
        return replace(previous or current, available=False)

    async def _async_update_data(self) -> OutsideSnapshot:
        candidate_location = self._candidate_location()
        if materially_changed(self._accepted_location, candidate_location):
            self._accepted_location = candidate_location
        # Automatic providers follow the accepted effective coordinate. They do
        # not create/configure foreign Home Assistant integrations and failures
        # are deliberately non-fatal to the ventilation engine.
        await async_refresh_auto_providers(
            self.hass,
            self.entry,
            self._accepted_location or candidate_location,
        )
        # Manual weather overrides keep Home Assistant's native forecast cache.
        # In automatic mode this helper returns immediately.
        await async_refresh_hourly_forecast(self.hass, self.entry)
        await async_refresh_nina_details(self.hass, self.entry)
        weather = weather_assessment(self.hass, self.entry)
        warnings = warning_assessment(self.hass, self.entry)
        # A previously confirmed hard safety lock must survive a temporary
        # provider outage, an integration reload and a Home Assistant restart.
        # Only normalized hard-safety state is persisted; explicit provider
        # clears still win immediately.
        await async_apply_persistent_safety_state(
            self.hass, self.entry, weather, warnings
        )
        tracker = get_air_quality_tracker(self.hass, self.entry)
        if tracker is not None and weather.air_quality_values:
            tracker.observe(weather.air_quality_values)
        return OutsideSnapshot(weather=weather, warnings=warnings)

    async def async_start(self) -> None:
        if self._started:
            return
        self._started = True
        try:
            await self.async_config_entry_first_refresh()
            self._replace_source_listener()
        except Exception:
            # A retry must create/start a fresh runtime, not reuse an object that
            # still claims it started successfully. Any listener installed before
            # the failure is local to this temporary object and can be removed now.
            self._started = False
            if self._source_unsub is not None:
                self._source_unsub()
                self._source_unsub = None
            while self._unsubs:
                self._unsubs.pop()()
            raise

        # Provider integrations can add/rename/remove entities after this
        # coordinator has started. Re-discover sources on registry changes so a
        # newly created NINA/weather entity becomes event-driven without a
        # Lüftungsassistent reload. Registry changes are rare and are collapsed
        # while one refresh is already pending.
        self._unsubs.append(
            self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED,
                self._handle_registry_change,
            )
        )
        # Home location changes are already an HA core event. No polling and no
        # copied coordinates are required for normal house installations.
        self._unsubs.append(
            self.hass.bus.async_listen(
                EVENT_CORE_CONFIG_UPDATE,
                self._handle_home_location_change,
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

        if uses_auto_warning(self.entry):
            self._unsubs.append(
                async_track_time_interval(
                    self.hass,
                    self._handle_auto_warning_tick,
                    AUTO_WARNING_REFRESH_INTERVAL,
                )
            )


    @callback
    def _create_background_task(self, target, name: str):
        # Home Assistant 2026.6+ provides lifecycle-bound task creation on
        # ConfigEntry. The integration's declared minimum already guarantees
        # this API, so do not fall back to hass.async_create_task (which could
        # outlive entry unload).
        return self.entry.async_create_background_task(self.hass, target, name)

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
            # Unload may have happened while the refresh awaited provider I/O.
            # Never recreate listeners after shutdown.
            if self._started:
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
        self._create_background_task(
            self._async_refresh_after_registry_change(),
            f"Lüftungsassistent provider discovery {self.entry.entry_id}",
        )

    @callback
    def _handle_forecast_tick(self, _now) -> None:
        """Refresh the shared short-term/night forecast cache."""
        if not self._started:
            return
        self._create_background_task(
            self.async_request_refresh(),
            f"Lüftungsassistent forecast outside refresh {self.entry.entry_id}",
        )

    @callback
    def _handle_nina_detail_tick(self, _now) -> None:
        if not self._started:
            return
        self._create_background_task(
            self.async_request_refresh(),
            f"Lüftungsassistent NINA detail refresh {self.entry.entry_id}",
        )

    @callback
    def _handle_auto_warning_tick(self, _now) -> None:
        if not self._started:
            return
        self._create_background_task(
            self.async_request_refresh(),
            f"Lüftungsassistent automatic warning refresh {self.entry.entry_id}",
        )

    @callback
    def _handle_source_change(self, event: Event) -> None:
        # Warning details and forecasts may require async provider calls, so use
        # the coordinator refresh path instead of recomputing each room inline.
        if not self._started:
            return
        tracker = str(self.entry.data.get(CONF_LOCATION_TRACKER) or "")
        if tracker and str(event.data.get("entity_id") or "") == tracker:
            current = self._candidate_location()
            if not materially_changed(self._accepted_location, current):
                return
        self._create_background_task(
            self.async_request_refresh(),
            f"Lüftungsassistent outside update {self.entry.entry_id}",
        )

    @callback
    def _handle_home_location_change(self, _event: Event) -> None:
        if not self._started or self.entry.data.get(CONF_LOCATION_TRACKER):
            return
        current = self._candidate_location()
        if not materially_changed(self._accepted_location, current):
            return
        self._create_background_task(
            self.async_request_refresh(),
            f"Lüftungsassistent Home location update {self.entry.entry_id}",
        )

    async def async_shutdown(self) -> None:
        # Prevent already-queued callbacks from scheduling fresh work while the
        # coordinator tears down its listeners.
        self._started = False
        if self._source_unsub is not None:
            self._source_unsub()
            self._source_unsub = None
        self._source_entities.clear()
        while self._unsubs:
            self._unsubs.pop()()
        self._registry_refresh_pending = False
        await super().async_shutdown()


async def async_get_or_create_outside_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> LueftungsberaterOutsideCoordinator:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_OUTSIDE_COORDINATORS, {})
    coordinator = store.get(entry.entry_id)
    if coordinator is not None:
        return coordinator
    coordinator = LueftungsberaterOutsideCoordinator(hass, entry)
    try:
        await coordinator.async_start()
    except Exception:
        try:
            await coordinator.async_shutdown()
        except Exception:  # noqa: BLE001 - preserve the original setup error
            _LOGGER.debug("Unable to clean up failed outside coordinator setup", exc_info=True)
        raise
    store[entry.entry_id] = coordinator
    return coordinator


def get_outside_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> LueftungsberaterOutsideCoordinator | None:
    return hass.data.get(DOMAIN, {}).get(DATA_OUTSIDE_COORDINATORS, {}).get(entry.entry_id)


async def async_stop_outside_coordinator(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator = hass.data.get(DOMAIN, {}).get(DATA_OUTSIDE_COORDINATORS, {}).pop(entry.entry_id, None)
    if coordinator is not None:
        await coordinator.async_shutdown()

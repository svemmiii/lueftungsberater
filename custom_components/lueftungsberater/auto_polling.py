"""Independent automatic-provider jobs and source-specific evidence lifetimes."""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from . import auto_providers as ap
from .const import AUTO_PROVIDER_STALE_MAX_AGE
from .polling import RequestPacer
from .warning_regions import coordinate_country

_LOGGER = logging.getLogger(__name__)
PERIODS = {"observations": 900.0, "forecast": 900.0, "air_model": 900.0,
           "air_stations": 900.0, "warnings": 300.0}


class AutomaticPolling:
    """Run network work outside the local room/coordinator update path."""

    def __init__(self, hass, entry, publish):
        self.hass, self.entry, self.publish = hass, entry, publish
        self.pacer = RequestPacer(async_get_clientsession(hass))
        self.location = None
        self.tasks = {}
        self.stopping = False
        self.ready = False
        self.generation = 0
        self.locks = {name: asyncio.Lock() for name in PERIODS}
        self.start_lock = asyncio.Lock()

    async def start(self, location):
        self.generation += 1
        async with self.start_lock:
            await self._start(location)

    async def _start(self, location):
        generation = self.generation
        await self._cancel_jobs()
        if self.pacer.requests or self.pacer.active or self.pacer.queue:
            await self.pacer.close()
            self.pacer = RequestPacer(async_get_clientsession(self.hass))
        self.ready = False
        self.location = location
        state = ap._state(self.hass, self.entry)
        state.location_key = ap._location_key(location)
        state.weather = None
        state.weather_available = False
        state.warning = None
        state.part_data.clear()
        state.part_updated_at.clear()
        state.part_attempted_at.clear()
        state.part_errors.clear()
        ap._clear_forecast(state)
        country = await self.hass.async_add_executor_job(
            coordinate_country, location.latitude, location.longitude)
        if generation != self.generation:
            return
        self.location = replace(location, country=country)
        if not location.available:
            self.ready = True
            return
        names = []
        if ap.uses_auto_weather(self.entry):
            names.extend(("forecast", "air_model"))
            if country == "DE":
                names.extend(("observations", "air_stations"))
        if ap.uses_auto_warning(self.entry):
            names.insert(0, "warnings")
        # Successful startup is assembled from validated results, not from the
        # fact that one request was sent. Failed jobs get bounded early retries.
        await asyncio.gather(*(self._job(name, bootstrap=True) for name in names))
        if generation != self.generation:
            return
        self.ready = True
        for name in names:
            self.tasks[name] = self.entry.async_create_background_task(
                self.hass, self._loop(name), f"Lüftungsassistent {name} {self.entry.entry_id}")

    async def _cancel_jobs(self):
        tasks = list(self.tasks.values())
        self.tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _loop(self, name):
        period = PERIODS[name]
        deadline = self.pacer.clock() + period
        failures = 0
        forecast_release = None
        if name != "forecast" and name in ap._state(self.hass, self.entry).part_errors:
            await asyncio.sleep(60)
            await self._job(name, deadline=self.pacer.clock() + 30)
            failures = 1
            deadline = self.pacer.clock() + period
        while not self.stopping:
            weight = self.pacer.weights.get(name, (1.0, period))[0]
            # Release early enough to pace the complete job within its existing
            # interval; deadlines are fixed anchors, not completion+interval.
            lead = min(period * 0.9, max(weight * (self.pacer.gap + 20), period * 0.75))
            release = forecast_release if forecast_release is not None else deadline - lead
            await asyncio.sleep(max(0, release - self.pacer.clock()))
            ok = await self._job(name, deadline=deadline)
            if not ok and failures < 3 and name != "forecast":
                failures += 1
                retry_delay = (60, 120, 300)[failures - 1]
                await asyncio.sleep(retry_delay)
                # Recovery must not monopolize the normal refresh slots.
                await self._job(name, deadline=min(deadline, self.pacer.clock() + 30))
            elif ok:
                failures = 0
            deadline += period
            if deadline <= self.pacer.clock():
                deadline = self.pacer.clock() + period
            forecast_release = None
            if name == "forecast" and ok:
                # After the initial phase distribution, the *actual* preceding
                # success sets this single-request job's freshness deadline.
                # A fixed cycle anchor could otherwise allow a busy warning
                # queue to turn an early previous result stale before its turn.
                updated = ap._state(self.hass, self.entry).forecast_updated_at
                if updated is not None:
                    remaining = (updated + timedelta(seconds=period) - dt_util.utcnow()).total_seconds()
                    deadline = self.pacer.clock() + max(0.0, remaining)
                    forecast_release = deadline - 20.0

    async def refresh_warning(self):
        if self.ready and not self.stopping and self.location.available:
            await self._job("warnings", deadline=self.pacer.clock() + 30)

    async def refresh_forecast(self):
        if self.ready and not self.stopping and self.location.available:
            await self._job("forecast", deadline=self.pacer.clock() + 30)

    async def _job(self, name, *, bootstrap=False, deadline=None):
        if self.locks[name].locked():
            return True
        async with self.locks[name]:
            budget = 120.0 if bootstrap else max(20.0, (deadline or self.pacer.clock() + PERIODS[name]) - self.pacer.clock())
            try:
                async with asyncio.timeout(budget):
                    return await self._run_job(name, bootstrap=bootstrap, deadline=deadline)
            except TimeoutError:
                state = ap._state(self.hass, self.entry)
                state.part_errors[name] = "refresh_budget_exhausted"
                if name == "forecast":
                    ap._record_forecast_result(state, [], dt_util.utcnow(), "refresh_budget_exhausted", self.entry.title)
                if name == "warnings" and state.warning is not None:
                    state.warning = replace(state.warning, available=False, error="refresh_budget_exhausted",
                        source_availability={key: False for key in state.warning.source_availability})
                if self.ready and not self.stopping:
                    await self.publish()
                return False

    async def _run_job(self, name, *, bootstrap=False, deadline=None):
        generation = self.generation
        location = self.location
        state = ap._state(self.hass, self.entry)
        started = dt_util.utcnow()
        state.part_attempted_at[name] = started
        session = self.pacer.job(name, PERIODS[name], deadline or self.pacer.clock() + PERIODS[name],
                                 bootstrap=bootstrap, urgent=name == "warnings")
        ok = False
        async def progress(part_result):
            if generation != self.generation:
                return
            state.part_data[name] = part_result
            state.part_updated_at[name] = started
            await self._compose(state)
            if self.ready and not self.stopping:
                await self.publish()
        try:
            if name == "warnings":
                result = await ap._fetch_auto_warning(self.hass, session, location, location.country, state)
                if generation != self.generation:
                    return False
                state.warning_attempted_at = started
                # An incomplete feed is an outage, never an all-clear.
                previous = state.warning
                if not result.available and previous is not None:
                    present = {(w.provider_domain, w.warning_id, w.sender, w.issued_at) for w in result.warnings}
                    for old in previous.warnings:
                        if ((result.source_availability.get(old.provider_domain) is False
                             or not result.source_availability)
                                and (old.provider_domain, old.warning_id, old.sender, old.issued_at) not in present
                                and ap._fresh(old.evidence_at or previous.fetched_at, timedelta(hours=1), dt_util.utcnow())):
                            result.warnings.append(old)
                state.warning = result
                ok = result.available
                if ok:
                    state.part_updated_at[name] = result.fetched_at
            elif name == "observations":
                result = await ap._fetch_dwd_observations(session, location, state, on_progress=progress)
                if not result[1]:
                    raise ValueError("no_valid_station_observations")
            elif name == "air_stations":
                result = await ap._fetch_uba_air_quality(session, location, state, on_progress=progress)
                if not result[0]:
                    raise ValueError("no_valid_air_station_observations")
            elif name == "air_model":
                result = await ap._fetch_coordinate_air_quality(session, location)
                if not result[0] and result[2] is None:
                    raise ValueError("no_valid_air_model_observations")
            else:
                result = await ap._get_json(session,
                    ap._OPEN_METEO_DWD if location.country == "DE" else ap._OPEN_METEO_FORECAST,
                    params={"latitude": location.latitude, "longitude": location.longitude,
                        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m",
                        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_gusts_10m",
                        "forecast_hours": 36, "timezone": "auto", "timeformat": "unixtime",
                        "wind_speed_unit": "kmh",
                        **({"elevation": location.elevation} if location.elevation is not None else {})})
                if not isinstance(result, dict):
                    raise ValueError("invalid_forecast_response")
                zone = await ap._async_forecast_timezone(result.get("timezone"))
                points = ap._normalize_open_meteo_hourly(result, zone=zone)
                if not ap._usable_forecast(points, dt_util.utcnow(), dt_util.utcnow()):
                    raise ValueError("incomplete_forecast_response")
                ap._record_forecast_result(state, points, dt_util.utcnow(), None, self.entry.title)
            if generation != self.generation:
                return False
            if name != "warnings":
                state.part_data[name] = result
                state.part_updated_at[name] = dt_util.utcnow()
                await self._compose(state)
                ok = True
            if ok:
                state.part_errors.pop(name, None)
            else:
                state.part_errors[name] = getattr(result, "error", None) or "provider_unavailable"
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if generation != self.generation:
                return False
            state.part_errors[name] = ap._forecast_error_text(exc)
            _LOGGER.debug("Automatic %s failed for %s: %s", name, self.entry.title, exc)
            if name == "forecast":
                ap._record_forecast_result(state, [], dt_util.utcnow(), str(exc), self.entry.title)
            if name == "warnings":
                previous = state.warning
                state.warning = ap.AutoWarningData(
                    provider_domain=previous.provider_domain if previous else "auto_warning",
                    fetched_at=previous.fetched_at if previous else started,
                    available=False, country=location.country,
                    safety_source_key=ap._safety_location_key("warning", location),
                    warnings=list(previous.warnings) if previous else [], error=str(exc),
                    coverage=previous.coverage if previous else "none",
                    source_availability={domain: False for domain in previous.source_availability} if previous else {})
        finally:
            session.finish()
            if generation == self.generation:
                state.polling_diagnostics = {**self.pacer.diagnostics(), "sources": {
                    key: {"last_attempt": value.isoformat(),
                          "last_success": state.part_updated_at[key].isoformat() if key in state.part_updated_at else None,
                          "error": state.part_errors.get(key)}
                    for key, value in state.part_attempted_at.items()}}
        if self.ready and generation == self.generation and not self.stopping:
            await self.publish()
        return ok

    async def _compose(self, state):
        now = dt_util.utcnow()
        def data(name, empty, age=AUTO_PROVIDER_STALE_MAX_AGE):
            return state.part_data.get(name, empty) if ap._fresh(state.part_updated_at.get(name), age, now) else empty
        candidates, observations = data("observations", ([], []))
        weather = await ap._compose_weather(self.location, state, candidates, observations,
            data("forecast", {}), data("air_model", ({}, {}, None), timedelta(hours=3)),
            data("air_stations", ({}, {}), timedelta(hours=3)))
        for key, source in weather.measurement_sources.items():
            part = "observations" if source.get("provider") == "dwd_station" else "forecast"
            source = dict(source)
            source["fetched_at"] = state.part_updated_at[part].isoformat()
            weather.measurement_sources[key] = source
        weather.fetched_at = max((state.part_updated_at[n] for n in ("observations", "forecast")
                                  if n in state.part_updated_at), default=now)
        # Publish source-specific ages, never the completion time of another job.
        weather.air_quality_updated_at = {
            kind: state.part_updated_at["air_stations" if source.startswith("uba_station:") else "air_model"]
            for kind, source in weather.air_quality_sources.items()}
        for part in ("air_model", "air_stations"):
            result = state.part_data.get(part)
            if result:
                for kind, stamp in getattr(result[0], "fetched_at", {}).items():
                    if kind in weather.air_quality_values:
                        selected_station = weather.air_quality_sources.get(kind, "").startswith("uba_station:")
                        if selected_station == (part == "air_stations"):
                            weather.air_quality_updated_at[kind] = stamp
        weather.outdoor_co2_updated_at = state.part_updated_at.get("air_model")
        previous = state.weather
        if previous is not None:
            # A partial failure can retain only the still-valid individual old
            # fields. Their own proof times survive, including during recovery.
            for key, attribute in {"temperature": "temperature", "humidity": "humidity",
                    "condition": "condition", "precipitation": "precipitation",
                    "wind_speed": "wind_speed_kmh", "wind_gust": "wind_gust_kmh"}.items():
                old_source = previous.measurement_sources.get(key, {})
                old_stamp = ap._parse_dt(old_source.get("fetched_at")) or previous.fetched_at
                if getattr(weather, attribute) is None and ap._fresh(old_stamp, AUTO_PROVIDER_STALE_MAX_AGE, now):
                    setattr(weather, attribute, getattr(previous, attribute))
                    if key in previous.measurement_sources:
                        weather.measurement_sources[key] = dict(old_source)
            for kind, value in previous.air_quality_values.items():
                old_stamp = previous.air_quality_updated_at.get(kind, previous.fetched_at)
                if kind not in weather.air_quality_values and ap._fresh(old_stamp, timedelta(hours=3), now):
                    weather.air_quality_values[kind] = value
                    weather.air_quality_sources[kind] = previous.air_quality_sources.get(kind, "")
                    weather.air_quality_updated_at[kind] = old_stamp
                    if kind in previous.air_quality_observed_at:
                        weather.air_quality_observed_at[kind] = previous.air_quality_observed_at[kind]
            old_co2_stamp = previous.outdoor_co2_updated_at or previous.fetched_at
            if (weather.outdoor_co2_ppm is None and previous.outdoor_co2_ppm is not None
                    and ap._fresh(old_co2_stamp, timedelta(hours=3), now)):
                weather.outdoor_co2_ppm = previous.outdoor_co2_ppm
                weather.outdoor_co2_source = previous.outdoor_co2_source
                weather.outdoor_co2_updated_at = old_co2_stamp
                weather.outdoor_co2_observed_at = previous.outdoor_co2_observed_at
        weather.available = bool(weather.measurement_sources)
        state.weather = weather
        state.weather_available = weather.available

    async def close(self):
        self.stopping = True
        self.generation += 1
        await self._cancel_jobs()
        await self.pacer.close()

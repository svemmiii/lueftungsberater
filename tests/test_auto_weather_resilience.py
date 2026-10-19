"""Real provider/cache transitions with controlled external responses."""

from datetime import datetime, timedelta, timezone
from dataclasses import replace
import asyncio
import aiohttp
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.lueftungsberater import auto_providers as ap
from custom_components.lueftungsberater.const import (
    CONF_WARNING_SOURCE_MODE,
    CONF_WEATHER_SOURCE_MODE,
    WEATHER_SOURCE_AUTO,
)
from custom_components.lueftungsberater.location import EffectiveLocation
from custom_components.lueftungsberater.providers import weather_assessment


NOW = datetime(2026, 10, 17, 10, tzinfo=timezone.utc)
LOCATION = EffectiveLocation(50.7567, 6.9930, 60, "DE", "home", NOW)


def entry():
    return SimpleNamespace(
        entry_id="weather-resilience", title="Meine Wohnung", data={
            CONF_WEATHER_SOURCE_MODE: WEATHER_SOURCE_AUTO,
            CONF_WARNING_SOURCE_MODE: "manual",
        },
    )


def payload(now=NOW, temperature=13.5):
    return {
        "timezone": "Europe/Berlin",
        "current": {"temperature_2m": temperature, "relative_humidity_2m": 77},
        "hourly": {
            "time": [(now + timedelta(hours=i)).isoformat() for i in range(36)],
            "temperature_2m": [temperature] * 36,
            "relative_humidity_2m": [77] * 36,
            "wind_speed_10m": [12] * 36,
            "wind_gusts_10m": [23] * 36,
            "precipitation": [0] * 36,
            "weather_code": [3] * 36,
        },
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [
    TimeoutError("test timeout"), OSError("test connection failure"),
    aiohttp.ClientResponseError(None, (), status=503),
    aiohttp.ClientResponseError(None, (), status=429),
    ValueError("invalid JSON response"), {"hourly": {}},
])
async def test_one_forecast_timeout_keeps_actual_previous_points_and_timestamp(hass, freezer, failure):
    freezer.move_to(NOW)
    config = entry()
    station = ap.DwdStation("H932", "Weilerswist-Lommersum", 50.7, 6.9)
    observation = (
        "date;time;dry_bulb_temperature_at_2_meter_above_ground;relative_humidity\n"
        "unit;unit;C;%\n"
        "desc;desc;temp;humidity\n"
        "20261017;1000;13,5;77\n"
    ).encode()
    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value="DE"),
        patch.object(ap, "_dwd_station_candidates", AsyncMock(return_value=[(station, 15.1)])),
        patch.object(ap, "_get_bytes", AsyncMock(return_value=observation)),
        patch.object(ap, "_fetch_coordinate_air_quality", AsyncMock(return_value=({}, {}, 442))),
        patch.object(ap, "_fetch_uba_air_quality", AsyncMock(return_value=({}, {}))),
        patch.object(ap, "_get_json", AsyncMock(side_effect=[payload(), failure])),
    ):
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        before = weather_assessment(hass, config)
        assert before.forecast_data_status == "fresh"
        freezer.tick(timedelta(minutes=16))
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        after = weather_assessment(hass, config)

    assert after.temperature == 13.5
    assert after.humidity == 77
    assert after.hourly_forecast == before.hourly_forecast
    assert after.hourly_forecast_updated == before.hourly_forecast_updated
    assert after.forecast_data_status == "stale"


def weather(now=NOW, temperature=13.5, *, forecast=True):
    return ap.AutoWeatherData(
        "dwd_station+dwd_icon", now, country="DE", temperature=temperature,
        humidity=77, wind_speed_kmh=12, wind_gust_kmh=23,
        hourly_forecast=ap._normalize_open_meteo_hourly(payload(now), zone=timezone.utc) if forecast else [],
    )


@pytest.mark.parametrize("bad", [
    {}, {"hourly": {}}, {"hourly": {"time": [], "temperature_2m": []}},
    {"hourly": {"time": "broken", "temperature_2m": [13]}},
    {"hourly": {"time": ["broken"], "temperature_2m": [13]}},
    {"hourly": {"time": ["2026-10-17T11:00:00+00:00"], "temperature_2m": [None]}},
    {"hourly": {"time": ["2026-10-17T11:00:00+00:00"], "temperature_2m": [float("nan")]}},
    {"hourly": {"time": ["2026-10-17T11:00:00+00:00"], "temperature_2m": [float("inf")]}},
    {"hourly": {"time": ["2026-10-17T11:00:00+00:00"], "temperature_2m": [False]}},
    {"hourly": {"time": ["2026-10-17T11:00:00+00:00"], "temperature_2m": [True]}},
])
async def test_unusable_replacement_preserves_previous_evidence(hass, freezer, bad):
    freezer.move_to(NOW)
    config = entry()
    state = ap._state(hass, config)
    good = weather()
    ap._record_forecast_result(state, good.hourly_forecast, NOW, None, config.title)
    freezer.tick(timedelta(minutes=16))
    points = ap._normalize_open_meteo_hourly(bad, zone=timezone.utc)
    ap._record_forecast_result(state, points, ap.dt_util.utcnow(), None, config.title)
    result, updated, status = ap.auto_forecast_data(hass, config)
    assert result == good.hourly_forecast
    assert updated == NOW
    assert status == "stale"
    assert state.forecast_error == "empty_or_invalid_forecast"


@pytest.mark.parametrize("field,bad", [
    ("humidity", None), ("humidity", 101), ("humidity", -1),
    ("wind_speed", None), ("wind_speed", -1),
    ("wind_gust_speed", None), ("condition", None), ("condition", "unknown"),
])
def test_incomplete_forecast_does_not_replace_complete_evidence(hass, freezer, field, bad):
    freezer.move_to(NOW)
    config = entry()
    state = ap._state(hass, config)
    old = weather().hourly_forecast
    ap._record_forecast_result(state, old, NOW, None, config.title)
    freezer.tick(timedelta(minutes=16))
    partial = weather(ap.dt_util.utcnow()).hourly_forecast
    # Even a later missing field must not become calm/dry in the night planner.
    partial[5][field] = bad
    ap._record_forecast_result(state, partial, ap.dt_util.utcnow(), None, config.title)
    rows, updated, status = ap.auto_forecast_data(hass, config)
    assert rows == old and updated == NOW and status == "stale"
    assert state.forecast_error == "incomplete_forecast"


@pytest.mark.parametrize("minutes,status", [(0, "fresh"), (14, "fresh"), (15, "stale"), (59, "stale"), (60, "unavailable"), (61, "unavailable"), (180, "unavailable")])
def test_forecast_age_is_independent_of_station_updates(hass, freezer, minutes, status):
    freezer.move_to(NOW)
    config = entry()
    state = ap._state(hass, config)
    good = weather()
    ap._record_forecast_result(state, good.hourly_forecast, NOW, None, config.title)
    freezer.tick(timedelta(minutes=minutes))
    # New station evidence must not renew old forecast evidence.
    state.weather = weather(ap.dt_util.utcnow(), temperature=18, forecast=False)
    rows, updated, actual = ap.auto_forecast_data(hass, config)
    assert actual == status
    assert updated == NOW
    assert bool(rows) is (status != "unavailable")
    assert state.weather.temperature == 18


@pytest.mark.parametrize("offset", [-1, 1, 120])
def test_future_or_naive_fetch_timestamp_never_becomes_fresh(hass, freezer, offset):
    freezer.move_to(NOW)
    config = entry()
    state = ap._state(hass, config)
    state.hourly_forecast = weather().hourly_forecast
    state.forecast_updated_at = NOW + timedelta(minutes=offset) if offset > 0 else NOW.replace(tzinfo=None)
    assert ap.auto_forecast_data(hass, config)[2] == "unavailable"


@pytest.mark.parametrize("points", [[], [{"datetime": NOW, "temperature": 13}], [{"datetime": NOW + timedelta(hours=3), "temperature": 13}]])
def test_missing_nearby_future_coverage_does_not_extrapolate(hass, freezer, points):
    freezer.move_to(NOW)
    config = entry()
    state = ap._state(hass, config)
    state.forecast_updated_at = NOW
    state.hourly_forecast = points
    rows, updated, status = ap.auto_forecast_data(hass, config)
    assert rows == [] and status == "unavailable" and updated == NOW


async def test_forecast_retry_recovers_without_renewing_measurements(hass, freezer):
    freezer.move_to(NOW)
    config = entry()
    current = weather(forecast=False)
    current.forecast_error = "TimeoutError"
    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value="DE"),
        patch.object(ap, "_fetch_auto_weather", AsyncMock(return_value=current)) as station_fetch,
        patch.object(ap, "_get_json", AsyncMock(return_value=payload(NOW + timedelta(minutes=1), 12))) as forecast_fetch,
    ):
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        assert ap.auto_forecast_data(hass, config)[2] == "unavailable"
        freezer.tick(timedelta(seconds=59))
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        forecast_fetch.assert_not_awaited()
        freezer.tick(timedelta(seconds=1))
        await ap.async_refresh_auto_providers(hass, config, LOCATION)

    station_fetch.assert_awaited_once()
    forecast_fetch.assert_awaited_once()
    assert "current" not in forecast_fetch.call_args.kwargs["params"]
    assert forecast_fetch.call_args.kwargs["params"]["timeformat"] == "unixtime"
    state = ap._state(hass, config)
    assert state.weather is current
    assert state.weather.fetched_at == NOW
    assert state.weather.temperature == 13.5
    rows, updated, status = ap.auto_forecast_data(hass, config)
    assert status == "fresh" and updated == NOW + timedelta(minutes=1)
    assert all(row["temperature"] == 12 for row in rows)
    assert state.forecast_error is None and state.forecast_retry_at is None


@pytest.mark.parametrize("country", ["DE", "BE", "US"])
async def test_bounded_retries_and_many_source_updates_do_not_flood(hass, freezer, country, caplog):
    freezer.move_to(NOW)
    config = entry()
    current = weather(forecast=False)
    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value=country),
        patch.object(ap, "_fetch_auto_weather", AsyncMock(return_value=current)) as full,
        patch.object(ap, "_get_json", AsyncMock(side_effect=TimeoutError("offline"))) as retry,
    ):
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        for minute in range(1, 15):
            freezer.move_to(NOW + timedelta(minutes=minute))
            for _ in range(25):
                await ap.async_refresh_auto_providers(hass, config, LOCATION)
            assert retry.await_count == sum(minute >= due for due in (1, 3, 8))
        full.assert_awaited_once()
        assert retry.await_count == 3
        assert ap._state(hass, config).forecast_retry_at is None
        assert "Hourly forecast refresh failed" in caplog.text
        assert sum(
            record.levelname == "WARNING" and "Hourly forecast refresh failed" in record.message
            for record in caplog.records
        ) == 1
        expected = ap._OPEN_METEO_DWD if country == "DE" else ap._OPEN_METEO_FORECAST
        assert {call.args[1] for call in retry.call_args_list} == {expected}
        freezer.move_to(NOW + timedelta(minutes=15))
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        assert full.await_count == 2
        assert retry.await_count == 3


async def test_two_simultaneous_retry_triggers_share_one_request(hass, freezer):
    freezer.move_to(NOW)
    config = entry()
    state = ap._state(hass, config)
    state.location_key = ap._location_key(LOCATION)
    state.weather_attempted_at = NOW
    state.forecast_retry_at = NOW
    state.forecast_failures = 1
    started = asyncio.Event()
    release = asyncio.Event()

    async def get_json(*args, **kwargs):
        started.set()
        await release.wait()
        return payload()

    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value="DE"),
        patch.object(ap, "_get_json", AsyncMock(side_effect=get_json)) as fetch,
    ):
        first = asyncio.create_task(ap.async_refresh_auto_providers(hass, config, LOCATION))
        await started.wait()
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        release.set()
        await first
    fetch.assert_awaited_once()


async def test_full_provider_outage_keeps_forecast_but_not_a_fresh_clear(hass, freezer):
    freezer.move_to(NOW)
    config = entry()
    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value="DE"),
        patch.object(ap, "_fetch_auto_weather", AsyncMock(side_effect=[weather(), OSError("offline")])),
    ):
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        freezer.tick(timedelta(minutes=16))
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
    assessment = weather_assessment(hass, config)
    assert assessment.forecast_data_status == "stale"
    assert assessment.hourly_forecast_updated == NOW
    assert assessment.provider_available is False
    assert "OSError" in assessment.forecast_error


@pytest.mark.parametrize("change", ["move", "lost", "clear"])
async def test_location_change_loss_and_unload_never_reuse_foreign_forecast(hass, freezer, change):
    freezer.move_to(NOW)
    config = entry()
    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value="DE"),
        patch.object(ap, "_fetch_auto_weather", AsyncMock(side_effect=[weather(), OSError("offline")])),
    ):
        await ap.async_refresh_auto_providers(hass, config, LOCATION)
        if change == "move":
            await ap.async_refresh_auto_providers(hass, config, replace(LOCATION, latitude=52))
        elif change == "lost":
            await ap.async_refresh_auto_providers(hass, config, replace(LOCATION, available=False))
        else:
            ap.clear_auto_provider_cache(hass, config)
    rows, updated, status = ap.auto_forecast_data(hass, config)
    assert rows == [] and updated is None and status == "unavailable"


async def test_current_data_keeps_updating_during_long_forecast_outage(hass, freezer):
    freezer.move_to(NOW)
    config = entry()
    records = []
    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value="DE"),
        patch.object(ap, "_fetch_auto_weather", AsyncMock(side_effect=[
            weather(), *[weather(NOW + timedelta(minutes=i), temperature=10 + i / 10, forecast=False)
                         for i in (15, 30, 45, 60, 75)], weather(NOW + timedelta(minutes=90), temperature=20),
        ])),
    ):
        for minute in range(0, 91, 15):
            freezer.move_to(NOW + timedelta(minutes=minute))
            await ap.async_refresh_auto_providers(hass, config, LOCATION)
            result = weather_assessment(hass, config)
            records.append((minute, result.forecast_data_status, result.temperature, result.hourly_forecast_updated))
    assert [r[1] for r in records] == ["fresh", "stale", "stale", "stale", "unavailable", "unavailable", "fresh"]
    assert [r[2] for r in records] == [13.5, 11.5, 13, 14.5, 16, 17.5, 20]
    assert all(r[3] == NOW for r in records[1:6])
    assert records[-1][3] == NOW + timedelta(minutes=90)


def test_unix_forecast_keeps_dst_hours_distinct_and_missing_values_missing():
    stamps = [datetime(2026, 10, 25, hour, tzinfo=timezone.utc).timestamp() for hour in (0, 1, 2)]
    rows = ap._normalize_open_meteo_hourly({
        "timezone": "Europe/Berlin", "hourly": {"time": stamps, "temperature_2m": [13, 12, 11]},
    }, zone=timezone.utc)
    assert [item["datetime"].timestamp() for item in rows] == stamps
    assert [item["temperature"] for item in rows] == [13, 12, 11]
    assert all(set(item) == {"datetime", "temperature"} for item in rows)


@pytest.mark.parametrize("country", ["DE", "BE"])
async def test_missing_current_precipitation_stays_unknown(country):
    with patch.object(ap, "_get_json", AsyncMock(side_effect=[{"current": {}}, {"current": {}}])):
        result = await ap._fetch_auto_weather(object(), LOCATION, country)
    assert result.precipitation is None
    assert result.temperature is None and result.humidity is None
    assert result.available is False


async def test_empty_station_measurements_are_not_converted_into_zero_rain():
    with (
        patch.object(ap, "_dwd_station_candidates", AsyncMock(return_value=[])),
        patch.object(ap, "_get_json", AsyncMock(return_value={"current": {}})),
        patch.object(ap, "_fetch_coordinate_air_quality", AsyncMock(return_value=({}, {}, None))),
        patch.object(ap, "_fetch_uba_air_quality", AsyncMock(return_value=({}, {}))),
    ):
        result = await ap._fetch_dwd_station_weather(object(), LOCATION, ap.AutoProviderState())
    assert result.precipitation is None and result.wind_speed_kmh is None
    assert result.available is False


@pytest.mark.parametrize("condition,wind,gust,point", [
    ("cloudy", 60, 80, {"temperature": 13}),
    ("cloudy", 60, 80, {"temperature": 13, "wind_speed": 12}),
    ("rainy", 12, 23, {"temperature": 13}),
    ("rainy", 12, 23, {"temperature": 13, "condition": "cloudy", "precipitation": 1}),
    ("rainy", 12, 23, {"temperature": 13, "condition": "cloudy", "precipitation_probability": 70}),
])
def test_missing_or_wet_forecast_never_implies_improving_weather(condition, wind, gust, point):
    from custom_components.lueftungsberater.providers import _short_term_forecast_outlook
    result = _short_term_forecast_outlook(
        now=NOW, current_condition=condition, current_wind_kmh=wind,
        current_gust_kmh=gust, rain_now=condition == "rainy",
        hourly_forecast=[{"datetime": NOW + timedelta(minutes=30), **point}],
    )
    assert result[0] != "improving"


async def test_real_shared_coordinator_fires_one_retry_and_cancels_on_shutdown(hass, freezer, enable_custom_integrations):
    from homeassistant.config_entries import ConfigEntryState
    from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
    from custom_components.lueftungsberater.outside import LueftungsberaterOutsideCoordinator
    from custom_components.lueftungsberater.const import DOMAIN
    from custom_components.lueftungsberater.providers import WarningAssessment

    freezer.move_to(NOW)
    config = MockConfigEntry(domain=DOMAIN, title="Meine Wohnung", data=entry().data)
    config.add_to_hass(hass)
    config._async_set_state(hass, ConfigEntryState.SETUP_IN_PROGRESS, None)
    coordinator = LueftungsberaterOutsideCoordinator(hass, config)
    with (
        patch.object(ap, "async_get_clientsession", return_value=object()),
        patch.object(ap, "coordinate_country", return_value="DE"),
        patch.object(ap, "_fetch_auto_weather", AsyncMock(return_value=weather(forecast=False))) as full,
        patch.object(ap, "_get_json", AsyncMock(return_value=payload(NOW + timedelta(minutes=1)))) as retry,
        patch.object(coordinator, "_candidate_location", return_value=LOCATION),
        patch("custom_components.lueftungsberater.outside.warning_assessment", return_value=WarningAssessment()),
        patch("custom_components.lueftungsberater.outside.async_apply_persistent_safety_state", AsyncMock()),
    ):
        try:
            await coordinator.async_start()
            assert coordinator.data.weather.forecast_data_status == "unavailable"
            assert coordinator._forecast_retry_at == NOW + timedelta(minutes=1)
            for _ in range(10):
                coordinator._schedule_forecast_retry()
            freezer.tick(timedelta(seconds=61))
            async_fire_time_changed(hass, ap.dt_util.utcnow())
            await hass.async_block_till_done()
            assert coordinator.data.weather.forecast_data_status == "fresh"
            full.assert_awaited_once()
            retry.assert_awaited_once()
        finally:
            await coordinator.async_shutdown()
        assert coordinator._forecast_retry_unsub is None
        freezer.tick(timedelta(hours=2))
        async_fire_time_changed(hass, ap.dt_util.utcnow())
        await hass.async_block_till_done()
        full.assert_awaited_once()
        retry.assert_awaited_once()


@pytest.mark.parametrize("status", ["fresh", "stale", "unavailable"])
def test_night_final_hour_memory_obeys_forecast_availability(status):
    from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator
    from custom_components.lueftungsberater.night import NightAdvice
    from custom_components.lueftungsberater.providers import WeatherAssessment
    from custom_components.lueftungsberater.runtime import RoomSnapshot

    now = datetime(2026, 10, 18, 5, 45, tzinfo=timezone.utc)
    end = now + timedelta(minutes=45)
    start = now - timedelta(hours=7)
    remembered = NightAdvice("now", "night_now", {
        "start_time": start.isoformat(), "end_time": end.isoformat(), "thermal_need": True,
    })
    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    coordinator.entry = entry()
    coordinator.subentry = SimpleNamespace(data={})
    coordinator._night_memory = remembered
    coordinator._night_memory_start = start
    coordinator._night_memory_end = end
    coordinator._night_interval = lambda _now: (start, end)
    coordinator._queue_memory_save = lambda: None
    snapshot = RoomSnapshot(None, {
        "temperature_inside": 26, "humidity_inside": 65, "target_temperature": 23,
        "night_ventilation_status": "unavailable", "has_window_contacts": True,
    }, WeatherAssessment(forecast_data_status=status), None)
    with patch("custom_components.lueftungsberater.coordinator.dt_util.now", return_value=now):
        result = coordinator._apply_night_memory(snapshot)
    if status == "unavailable":
        assert result.values["night_ventilation_status"] == "unavailable"
        assert coordinator._night_memory is None
    else:
        assert result.values["night_ventilation_status"] == "now"
        assert coordinator._night_memory is remembered


def test_expired_forecast_stops_night_evaluation_even_when_station_values_are_new(hass, freezer):
    from custom_components.lueftungsberater.night import evaluate_night_ventilation
    from zoneinfo import ZoneInfo
    now = datetime(2026, 10, 17, 20, tzinfo=timezone.utc)
    freezer.move_to(now)
    config = entry()
    state = ap._state(hass, config)
    good = weather(now, temperature=21)
    ap._record_forecast_result(state, good.hourly_forecast, now, None, config.title)
    seen = []
    for minutes in (0, 16, 59, 60):
        freezer.move_to(now + timedelta(minutes=minutes))
        if minutes:
            ap._record_forecast_result(state, [], ap.dt_util.utcnow(), "TimeoutError", config.title)
        state.weather = weather(ap.dt_util.utcnow(), temperature=21, forecast=False)
        assessment = weather_assessment(hass, config)
        advice = evaluate_night_ventilation(
            now=ap.dt_util.utcnow().astimezone(ZoneInfo("Europe/Berlin")),
            indoor_temp=26, indoor_humidity=65, target_temp=23, outdoor_temp=21,
            outdoor_humidity=55, hourly_forecast=assessment.hourly_forecast,
            start_minute=22 * 60, end_minute=6 * 60 + 30,
        )
        seen.append((assessment.forecast_data_status, advice.status))
    assert [s[0] for s in seen] == ["fresh", "stale", "stale", "unavailable"]
    assert all(s[1] != "unavailable" for s in seen[:3])
    assert seen[-1][1] == "unavailable"

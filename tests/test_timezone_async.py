"""Uncached timezone I/O, forecast timestamps and untrusted night arguments."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from zoneinfo import ZoneInfo
from zoneinfo import _common as zoneinfo_common

import pytest

from homeassistant.util import dt as dt_util

from custom_components.lueftungsberater import auto_providers as ap
from custom_components.lueftungsberater import localization
from custom_components.lueftungsberater.api import websocket_localize
from custom_components.lueftungsberater.location import EffectiveLocation


@contextmanager
def no_timezone_file_reads_on_loop():
    """Exercise cold ZoneInfo loads and reject disk parsing on this thread."""
    loop_thread = threading.get_ident()
    original = zoneinfo_common.load_data
    blocking_reads = []

    def checked_load(*args, **kwargs):
        if threading.get_ident() == loop_thread:
            blocking_reads.append(True)
            raise AssertionError("timezone file was read on the event-loop thread")
        return original(*args, **kwargs)

    ZoneInfo.clear_cache()
    with patch.object(zoneinfo_common, "load_data", side_effect=checked_load):
        yield
    assert not blocking_reads, "even an internally caught blocking read is a regression"


def forecast_payload(zone, local_time, utc_time, unix):
    start = datetime.fromisoformat(utc_time if unix else local_time)
    times = [start + timedelta(hours=i) for i in range(36)]
    return {
        "timezone": zone,
        "current": {"temperature_2m": 13.5, "relative_humidity_2m": 50},
        "hourly": {
            "time": [value.timestamp() if unix else value.isoformat() for value in times],
            "temperature_2m": [13.5] * 36,
            "relative_humidity_2m": [50] * 36,
            "wind_speed_10m": [5] * 36,
            "wind_gusts_10m": [8] * 36,
            "precipitation": [0] * 36,
            "weather_code": [3] * 36,
        },
    }


@pytest.mark.parametrize("path", ["coordinate", "dwd", "retry"])
@pytest.mark.parametrize("unix", [False, True], ids=["naive-provider-time", "unix-utc"])
@pytest.mark.parametrize("zone,local_time,utc_time", [
    ("Europe/Berlin", "2026-03-29T03:15:00", "2026-03-29T01:15:00+00:00"),
    ("America/New_York", "2026-11-01T01:30:00", "2026-11-01T05:30:00+00:00"),
    ("Asia/Kathmandu", "2026-10-19T12:15:00", "2026-10-19T06:30:00+00:00"),
    ("Pacific/Chatham", "2026-10-19T20:15:00", "2026-10-19T06:30:00+00:00"),
])
async def test_forecast_paths_keep_real_instants_without_blocking(
    freezer, path, unix, zone, local_time, utc_time,
):
    expected = datetime.fromisoformat(utc_time)
    freezer.move_to(expected)
    location = EffectiveLocation(50.7567, 6.993, 60, "DE", "home", expected)
    state = ap.AutoProviderState()
    payload = forecast_payload(zone, local_time, utc_time, unix)
    with (
        patch.object(ap, "_get_json", AsyncMock(return_value=payload)),
        patch.object(ap, "_dwd_station_candidates", AsyncMock(return_value=[])),
        patch.object(ap, "_fetch_coordinate_air_quality", AsyncMock(return_value=({}, {}, 441))),
        patch.object(ap, "_fetch_uba_air_quality", AsyncMock(return_value=({}, {}))),
        no_timezone_file_reads_on_loop(),
    ):
        if path == "coordinate":
            result = await ap._fetch_auto_weather(object(), location, "US")
            points = result.hourly_forecast
        elif path == "dwd":
            result = await ap._fetch_dwd_station_weather(object(), location, state)
            points = result.hourly_forecast
        else:
            await ap._retry_hourly_forecast(object(), location, "DE", state, "Test")
            assert state.forecast_error is None
            points = state.hourly_forecast
    assert len(points) == 36
    assert points[0]["datetime"].astimezone(timezone.utc) == expected
    assert points[0]["temperature"] == 13.5
    assert points[0]["humidity"] == 50


@pytest.mark.parametrize("path", ["stations", "air_quality"])
@pytest.mark.parametrize("now,berlin_date", [
    ("2026-03-28T23:30:00+00:00", "2026-03-29"),
    ("2026-10-24T22:30:00+00:00", "2026-10-25"),
    ("2026-10-25T23:30:00+00:00", "2026-10-26"),
])
async def test_uba_paths_use_berlin_calendar_without_blocking(freezer, path, now, berlin_date):
    instant = datetime.fromisoformat(now)
    freezer.move_to(instant)
    location = EffectiveLocation(50.7, 7.1, 60, "DE", "home", instant)
    state = ap.AutoProviderState()
    station = ap.UbaStation("123", "DENW123", "Teststation", 50.7, 7.1)
    with no_timezone_file_reads_on_loop():
        if path == "stations":
            payload = {"data": {"123": [123, "DENW123", "Teststation", "City", None, None, None, 7.1, 50.7]}}
            with patch.object(ap, "_get_json", AsyncMock(return_value=payload)) as get_json:
                result = await ap._uba_station_candidates(object(), location, state)
            assert result[0][0] == station
        else:
            payload = {"data": {"123": {"2026-10-19 08:00:00": ["2026-10-19 09:00:00", 1, 0, [9, 7.0, 1, "1.0"]]}}}
            with (
                patch.object(ap, "_uba_station_candidates", AsyncMock(return_value=[(station, 1.0)])),
                patch.object(ap, "_uba_component_index", AsyncMock(return_value={9: "pm2_5"})),
                patch.object(ap, "_get_json", AsyncMock(return_value=payload)) as get_json,
            ):
                values, sources = await ap._fetch_uba_air_quality(object(), location, state)
            assert values == {"pm2_5": 7.0}
            assert sources["pm2_5"].startswith("uba_station:DENW123:")
        assert get_json.await_args.kwargs["params"]["date_to"] == berlin_date
        if path == "stations":
            assert get_json.await_args.kwargs["params"]["date_from"] == berlin_date
        else:
            previous_day = (datetime.fromisoformat(berlin_date) - timedelta(days=1)).date()
            assert get_json.await_args.kwargs["params"]["date_from"] == previous_day.isoformat()


@pytest.mark.parametrize("language,expected", [
    ("de", "Nicht über Nacht offen lassen."),
    ("en", "Do not leave the window open overnight."),
    ("tr", "Pencereyi gece boyu açık bırakma."),
])
@pytest.mark.parametrize("client_zone", [
    "Europe/Berlin", "Etc/GMT-3", "UTC", "not-a-valid/zone", "/etc/passwd", None,
])
async def test_localize_websocket_preserves_source_end_not_client_zone_input(
    hass, language, expected, client_zone,
):
    berlin = ZoneInfo("Europe/Berlin")
    connection = SimpleNamespace(send_result=Mock())
    message = {
        "id": 71,
        "language": language,
        "temperature_unit": "°C",
        "recommendation_key": "room_good",
        "reason_key": "room_perspective",
        "reason_args": {},
        "duration_key": "not_needed",
        "night_ventilation_key": "night_now",
        "night_ventilation_args": {
            "start_time": "2026-10-25T00:00:00+02:00",
            "end_time": "2026-10-25T05:00:00+01:00",
            "requested_night_end": "06:00",
            "local_timezone": client_zone,
        },
    }
    # New source sensors export the exact requested instant in their own zone.
    message["night_ventilation_args"] = localization.night_args_with_requested_end(
        message["night_ventilation_args"], zone=berlin
    )
    with (
        patch.object(dt_util, "get_default_time_zone", return_value=berlin) as configured_zone,
        no_timezone_file_reads_on_loop(),
    ):
        websocket_localize(hass, connection, message)
        await hass.async_block_till_done(wait_background_tasks=True)
    configured_zone.assert_not_called()
    call = connection.send_result.call_args
    assert call.args[0] == 71
    assert expected in call.args[1]["night"]


@pytest.mark.parametrize("zone,start,finish,covered", [
    ("Europe/Berlin", "2026-03-28T23:00:00+01:00", "2026-03-29T06:00:00+02:00", True),
    ("Europe/Berlin", "2026-10-25T00:00:00+02:00", "2026-10-25T05:00:00+01:00", False),
    ("America/New_York", "2026-03-07T23:00:00-05:00", "2026-03-08T06:00:00-04:00", True),
    ("America/New_York", "2026-11-01T00:00:00-04:00", "2026-11-01T05:00:00-05:00", False),
])
@pytest.mark.parametrize("client_zone", ["UTC", "Etc/GMT-3", "bad/zone"])
async def test_night_coverage_keeps_local_dst_and_midnight_semantics(
    zone, start, finish, covered, client_zone,
):
    configured = ZoneInfo(zone)
    args = {
        "start_time": start, "end_time": finish, "requested_night_end": "06:00",
        "local_timezone": client_zone,
    }
    with (
        patch.object(dt_util, "get_default_time_zone", return_value=configured),
        no_timezone_file_reads_on_loop(),
    ):
        assert localization._night_covers_requested_end(args) is covered


@pytest.mark.parametrize("zone", [None, "", "not-a-valid/zone", 123])
async def test_missing_or_unknown_provider_zone_keeps_existing_utc_fallback(zone):
    payload = forecast_payload(zone, "2026-10-19T06:30:00", "2026-10-19T06:30:00+00:00", False)
    location = EffectiveLocation(50.7, 7.1, 60, "US", "home", datetime.now(timezone.utc))
    with (
        patch.object(ap, "_get_json", AsyncMock(return_value=payload)),
        patch.object(ap, "_fetch_coordinate_air_quality", AsyncMock(return_value=({}, {}, None))),
        no_timezone_file_reads_on_loop(),
    ):
        result = await ap._fetch_auto_weather(object(), location, "US")
    assert result.hourly_forecast[0]["datetime"] == datetime(2026, 10, 19, 6, 30, tzinfo=timezone.utc)

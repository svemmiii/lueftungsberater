"""Regression coverage for the independent v0.11.8 review findings."""

import json
from types import MappingProxyType, SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.config_entries import ConfigSubentry
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lueftungsberater import binary_sensor
from custom_components.lueftungsberater.api import (
    _export_attributes,
    _remote_instances_for_protocol,
    websocket_localize,
)
from custom_components.lueftungsberater.const import DOMAIN, CONF_NIGHT_END_TIME
from custom_components.lueftungsberater.localization import (
    _night_covers_requested_end,
    async_prepare_night_args,
    night_args_with_requested_end,
)


def local_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Review",
        version=1,
        minor_version=14,
        data={"entry_kind": "local"},
    )
    entry.add_to_hass(hass)
    return entry








NIGHTS = [
    ("Europe/Berlin", "2026-10-19T22:00:00+02:00", "2026-10-20T06:00:00+02:00", True),
    ("Europe/Berlin", "2026-10-19T22:00:00+02:00", "2026-10-20T05:00:00+02:00", False),
    (
        "America/New_York",
        "2026-10-19T22:00:00-04:00",
        "2026-10-20T06:00:00-04:00",
        True,
    ),
    (
        "America/New_York",
        "2026-10-19T22:00:00-04:00",
        "2026-10-20T05:00:00-04:00",
        False,
    ),
    ("Europe/Berlin", "2026-03-28T22:00:00+01:00", "2026-03-29T06:00:00+02:00", True),
    ("Europe/Berlin", "2026-10-24T22:00:00+02:00", "2026-10-25T05:00:00+01:00", False),
    (
        "America/New_York",
        "2026-03-07T22:00:00-05:00",
        "2026-03-08T06:00:00-04:00",
        True,
    ),
    (
        "America/New_York",
        "2026-10-31T22:00:00-04:00",
        "2026-11-01T05:00:00-05:00",
        False,
    ),
    (
        "Australia/Lord_Howe",
        "2026-10-03T22:00:00+10:30",
        "2026-10-04T06:00:00+11:00",
        True,
    ),
    ("Asia/Kolkata", "2026-10-19T22:00:00+05:30", "2026-10-20T06:00:00+05:30", True),
    (
        "Pacific/Kiritimati",
        "2026-10-19T22:00:00+14:00",
        "2026-10-20T06:00:00+14:00",
        True,
    ),
    (
        "Pacific/Honolulu",
        "2026-10-19T22:00:00-10:00",
        "2026-10-20T05:00:00-10:00",
        False,
    ),
]
POSITIVE = {
    "de": "Längeres Nachtlüften",
    "en": "Leaving the window open overnight",
    "tr": "Gece boyunca havalandırma",
}


async def localize(hass, args, language="de", key="night_now"):
    connection = SimpleNamespace(
        send_result=Mock(), send_error=Mock(), async_handle_exception=Mock()
    )
    websocket_localize(
        hass,
        connection,
        {
            "id": 42,
            "language": language,
            "temperature_unit": "°C",
            "recommendation_key": "room_good",
            "reason_key": "room_perspective",
            "reason_args": {},
            "duration_key": "not_needed",
            "night_ventilation_key": key,
            "night_ventilation_args": args,
        },
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    connection.send_error.assert_not_called()
    connection.async_handle_exception.assert_not_called()
    connection.send_result.assert_called_once()
    assert connection.send_result.call_args.args[0] == 42
    return connection.send_result.call_args.args[1]["night"]


@pytest.mark.parametrize("source,start,finish,covered", NIGHTS)
@pytest.mark.parametrize("receiver", ["Europe/Berlin", "America/New_York"])
@pytest.mark.parametrize("language", ["de", "en", "tr"])
@pytest.mark.parametrize("legacy", [True, False])
async def test_remote_night_text_preserves_source_schedule(
    hass, source, start, finish, covered, receiver, language, legacy
):
    source_zone, receiver_zone = ZoneInfo(source), ZoneInfo(receiver)
    args = {
        "start_time": start,
        "end_time": finish,
        "requested_night_end": "06:00",
        "local_timezone": source,
    }
    if not legacy:
        args = night_args_with_requested_end(args, zone=source_zone)
        attrs = _export_attributes(
            {"night_ventilation_args": args, "night_ventilation_key": "night_now"},
            "°C",
            remote_export=True,
        )
        instances = _remote_instances_for_protocol(
            [{"rooms": [{"attributes": attrs}]}], 3
        )
        args = json.loads(json.dumps(instances))[0]["rooms"][0]["attributes"][
            "night_ventilation_args"
        ]
    original = dict(args)
    with patch.object(dt_util, "get_default_time_zone", return_value=receiver_zone):
        text = await localize(hass, args, language)
    assert (POSITIVE[language] in text) is covered
    assert args == original


@pytest.mark.parametrize("source,start,finish,covered", NIGHTS)
async def test_source_semantics_are_receiver_independent_without_sync_zone_loading(
    source, start, finish, covered
):
    args = night_args_with_requested_end(
        {"start_time": start, "end_time": finish, "requested_night_end": "06:00"},
        zone=ZoneInfo(source),
    )
    with patch.object(
        dt_util,
        "get_default_time_zone",
        side_effect=AssertionError("Receiver zone must not be used"),
    ):
        assert _night_covers_requested_end(args) is covered
        assert await async_prepare_night_args(args) is args


@pytest.mark.parametrize("invalid", ["bad/zone", "/etc/passwd", 123, False, {}, []])
async def test_unknown_remote_zone_cannot_produce_an_overnight_recommendation(
    hass, invalid
):
    args = {
        "start_time": "2026-10-19T22:00:00+02:00",
        "end_time": "2026-10-20T06:00:00+02:00",
        "requested_night_end": "06:00",
        "local_timezone": invalid,
    }
    text = await localize(hass, args)
    assert "Nicht über Nacht offen lassen" in text


@pytest.mark.parametrize("invalid", [None, "bad-date", "2026-10-20T06:00:00", 123])
async def test_invalid_absolute_night_end_is_not_replaced_by_receiver_time(
    hass, invalid
):
    args = {
        "start_time": "2026-10-19T22:00:00+02:00",
        "end_time": "2026-10-20T06:00:00+02:00",
        "requested_night_end": "06:00",
        "local_timezone": "Europe/Berlin",
        "requested_night_end_time": invalid,
    }
    text = await localize(hass, args)
    assert "Nicht über Nacht offen lassen" in text


async def test_short_only_key_stays_short_even_when_whole_night_is_covered(hass):
    args = night_args_with_requested_end(
        {
            "start_time": "2026-10-19T22:00:00+02:00",
            "end_time": "2026-10-20T06:00:00+02:00",
            "requested_night_end": "06:00",
        },
        zone=ZoneInfo("Europe/Berlin"),
    )
    assert "Nicht über Nacht offen lassen" in await localize(
        hass, args, key="night_short_only"
    )


async def test_cold_legacy_source_zone_is_loaded_asynchronously(hass):
    from test_timezone_async import no_timezone_file_reads_on_loop

    receiver = ZoneInfo("UTC")
    resolver = AsyncMock(wraps=dt_util.async_get_time_zone)
    args = {
        "start_time": "2026-10-19T22:00:00+13:45",
        "end_time": "2026-10-20T06:00:00+13:45",
        "requested_night_end": "06:00",
        "local_timezone": "Pacific/Chatham",
    }
    with (
        patch.object(dt_util, "get_default_time_zone", return_value=receiver),
        patch.object(dt_util, "async_get_time_zone", resolver),
        no_timezone_file_reads_on_loop(),
    ):
        assert "Längeres Nachtlüften" in await localize(hass, args)
    resolver.assert_awaited_once_with("Pacific/Chatham")


@pytest.mark.parametrize(
    "failure", [OSError("unreadable zone"), ValueError("invalid zone")]
)
async def test_failed_async_zone_lookup_never_falls_back_to_receiver(hass, failure):
    args = {
        "start_time": "2026-10-19T22:00:00+02:00",
        "end_time": "2026-10-20T06:00:00+02:00",
        "requested_night_end": "06:00",
        "local_timezone": "Europe/Berlin",
    }
    with (
        patch.object(dt_util, "get_default_time_zone", return_value=ZoneInfo("UTC")),
        patch.object(dt_util, "async_get_time_zone", AsyncMock(side_effect=failure)),
    ):
        assert "Nicht über Nacht offen lassen" in await localize(hass, args)


async def test_actual_websocket_response_handles_remote_source_zone(
    hass, hass_ws_client
):
    from homeassistant.components import websocket_api

    await hass.config.async_set_time_zone("America/New_York")
    client = await hass_ws_client(hass)
    websocket_api.async_register_command(hass, websocket_localize)
    await client.send_json(
        {
            "id": 1,
            "type": "lueftungsberater/localize",
            "language": "de",
            "temperature_unit": "°C",
            "recommendation_key": "room_good",
            "reason_key": "room_perspective",
            "duration_key": "not_needed",
            "night_ventilation_key": "night_now",
            "night_ventilation_args": {
                "start_time": "2026-10-19T22:00:00+02:00",
                "end_time": "2026-10-20T06:00:00+02:00",
                "requested_night_end": "06:00",
                "local_timezone": "Europe/Berlin",
            },
        }
    )
    response = await client.receive_json()
    assert response["id"] == 1 and response["success"] is True
    assert "Längeres Nachtlüften" in response["result"]["night"]


@pytest.mark.parametrize(
    "data,expected",
    [
        ({}, False),
        ({"warning_source": "none"}, False),
        ({"warning_source_mode": "none"}, False),
        ({"weather_source_mode": "auto", "warning_source_mode": "none"}, False),
        ({"weather_entity": "weather.home"}, True),
        ({"weather_danger_entity": "binary_sensor.storm"}, True),
        ({"nina_status_entity": "sensor.nina"}, True),
        ({"warning_source": "official-provider"}, True),
        ({"warning_source_mode": "auto"}, True),
        ({"warning_source_mode": "auto_plus_manual"}, True),
    ],
)
async def test_danger_sensor_retains_original_warning_source_condition(
    hass, monkeypatch, data, expected
):
    entry = local_entry(hass)
    hass.config_entries.async_update_entry(entry, data=data)
    hass.config_entries.async_add_subentry(
        entry,
        ConfigSubentry(
            subentry_id="room",
            subentry_type="room",
            title="Room",
            unique_id=None,
            data=MappingProxyType({}),
        ),
    )
    coordinator = SimpleNamespace(
        hass=hass, config_entry=entry, data=None, last_update_success=True
    )
    factory = AsyncMock(return_value=coordinator)
    monkeypatch.setattr(binary_sensor, "async_get_or_create_room_coordinator", factory)
    add = Mock()
    await binary_sensor.async_setup_entry(hass, entry, add)
    assert add.call_count == int(expected)
    assert factory.await_count == int(expected)
    if expected:
        sensor = add.call_args.args[0][0]
        assert sensor.unique_id == "room_critical_danger"
        assert add.call_args.kwargs["config_subentry_id"] == "room"


async def test_sensor_exports_source_end_instant_without_changing_planner_or_measurements(
    hass,
):
    from custom_components.lueftungsberater.providers import (
        WeatherAssessment,
        WarningAssessment,
    )
    from custom_components.lueftungsberater.runtime import build_room_snapshot
    from custom_components.lueftungsberater.sensor import RoomAdvisorSensor

    entry = local_entry(hass)
    await hass.config.async_set_time_zone("Europe/Berlin")
    room = ConfigSubentry(
        subentry_id="room",
        subentry_type="room",
        title="Room",
        unique_id=None,
        data=MappingProxyType({CONF_NIGHT_END_TIME: "06:00:00"}),
    )
    hass.config_entries.async_add_subentry(entry, room)
    snapshot = build_room_snapshot(
        hass, entry, room, weather=WeatherAssessment(), warnings=WarningAssessment()
    )
    snapshot.values.update(
        night_ventilation_key="night_now",
        night_ventilation_args={
            "start_time": "2026-10-19T22:00:00+02:00",
            "end_time": "2026-10-20T06:00:00+02:00",
        },
    )
    before = dict(snapshot.values["night_ventilation_args"])
    coordinator = SimpleNamespace(
        hass=hass, config_entry=entry, data=snapshot, last_update_success=True
    )
    sensor = RoomAdvisorSensor(entry, room, coordinator)
    sensor.hass = hass
    with patch.object(
        dt_util, "get_default_time_zone", return_value=ZoneInfo("Europe/Berlin")
    ):
        attrs = sensor.extra_state_attributes
    assert (
        attrs["night_ventilation_args"]["requested_night_end_time"]
        == "2026-10-20T06:00:00+02:00"
    )
    assert snapshot.values["night_ventilation_args"] == before
    assert attrs["co2_ppm"] is None
    with patch.object(
        dt_util, "get_default_time_zone", return_value=ZoneInfo("America/New_York")
    ):
        assert "Längeres Nachtlüften" in await localize(
            hass, attrs["night_ventilation_args"]
        )

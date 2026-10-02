import asyncio
from types import SimpleNamespace

import pytest

from custom_components.lueftungsberater.const import (
    CONF_DISPLAY_MODE,
    CONF_HARDWARE_CONNECTION_TYPE,
    CONF_HARDWARE_DEVICE_ID,
    CONF_HARDWARE_ID,
    CONF_HARDWARE_ROLE,
    CONF_HARDWARE_ROOM_ID,
    DISPLAY_MODE_VENTILATION,
    HARDWARE_CONNECTION_DIRECT,
    HARDWARE_CONNECTION_MASTER,
    HARDWARE_ROLE_MASTER,
    HARDWARE_ROLE_NODE,
    HARDWARE_ROLE_STANDALONE,
    SUBENTRY_TYPE_ROOM,
    SUBENTRY_TYPE_STATION,
)
from custom_components.lueftungsberater.hardware_display import (
    DirectDisplayDispatcher,
    SERVICE_APPLY_DISPLAY_RESULT,
)
from custom_components.lueftungsberater.models import VentilationResult
from custom_components.lueftungsberater.providers import (
    WarningAssessment,
    WeatherAssessment,
)
from custom_components.lueftungsberater.runtime import RoomSnapshot


async def _esphome_device(hass, *, name="station", mac="AA:BB:CC:DD:EE:01"):
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    esphome = MockConfigEntry(
        domain="esphome",
        title=name,
        data={"device_name": name},
        unique_id=mac,
    )
    esphome.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=esphome.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, mac)},
        name=name,
    )
    return device


def _add_direct_sensors(hass, device, *, prefix="local"):
    from homeassistant.components.sensor import SensorDeviceClass
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    result = {}
    for key, device_class, value in (
        ("co2", SensorDeviceClass.CO2.value, "900"),
        ("temperature", SensorDeviceClass.TEMPERATURE.value, "21.5"),
        ("humidity", SensorDeviceClass.HUMIDITY.value, "45"),
    ):
        entity = registry.async_get_or_create(
            "sensor",
            "esphome",
            f"{prefix}-{key}",
            device_id=device.id,
        )
        hass.states.async_set(
            entity.entity_id,
            value,
            {"device_class": device_class},
        )
        result[key] = entity.entity_id
    return result


def _snapshot(
    *,
    status="green",
    recommendation_key="optional",
    safety_lock=False,
):
    result = VentilationResult(
        color=status,
        mode="test",
        recommendation_key=recommendation_key,
        reason_key="test",
        reason_args={},
        duration_key="unknown",
        duration_args={},
        original_reason=None,
        indoor_absolute_humidity=None,
        outdoor_absolute_humidity=None,
        absolute_humidity_difference=None,
        co2_status="ok",
        room_status_color=status,
        room_recommendation_key=recommendation_key,
        safety_lock=safety_lock,
    )
    return RoomSnapshot(
        result=result,
        values={},
        weather=WeatherAssessment(),
        warnings=WarningAssessment(),
    )


def _local_entry(hass, room, station):
    def create_background_task(_hass, target, _name):
        return asyncio.create_task(target)

    return SimpleNamespace(
        entry_id="assistant-entry",
        data={CONF_DISPLAY_MODE: DISPLAY_MODE_VENTILATION},
        subentries={room.subentry_id: room, station.subentry_id: station},
        async_create_background_task=create_background_task,
    )


def _room(room_id="room-1", title="Wohnzimmer"):
    return SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_ROOM,
        subentry_id=room_id,
        title=title,
        data={},
    )


def _station(device, *, role=HARDWARE_ROLE_STANDALONE, room_id="room-1"):
    return SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id=f"{role}-station",
        title="Station",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "DIRECT:AA:BB:CC:DD:EE:01",
            CONF_HARDWARE_CONNECTION_TYPE: (
                HARDWARE_CONNECTION_MASTER
                if role == HARDWARE_ROLE_NODE
                else HARDWARE_CONNECTION_DIRECT
            ),
            CONF_HARDWARE_ROLE: role,
            CONF_HARDWARE_ROOM_ID: room_id,
        },
    )


def _register_display_service(hass, name, calls, *, fail=False):
    async def apply_display(call):
        calls.append(dict(call.data))
        if fail:
            raise RuntimeError("device offline")

    hass.services.async_register(
        "esphome",
        f"{name}_{SERVICE_APPLY_DISPLAY_RESULT}",
        apply_display,
    )


@pytest.mark.asyncio
async def test_standalone_receives_direct_display_payload(hass, enable_custom_integrations):
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "station", calls)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(status="green"))
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0]["station_subentry_id"] == station.subentry_id
    assert calls[0]["room_id"] == room.subentry_id
    assert calls[0]["room_name"] == "Wohnzimmer"
    assert calls[0]["status"] == "green"
    assert calls[0]["recommendation_key"] == "optional"
    assert calls[0]["display_mode"] == DISPLAY_MODE_VENTILATION
    assert calls[0]["safety_lock"] is False


@pytest.mark.asyncio
async def test_master_with_own_room_sensors_receives_direct_display_payload(
    hass, enable_custom_integrations
):
    device = await _esphome_device(hass, name="master")
    _add_direct_sensors(hass, device, prefix="master")
    room = _room()
    station = _station(device, role=HARDWARE_ROLE_MASTER)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "master", calls)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(status="orange"))
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0]["station_subentry_id"] == station.subentry_id
    assert calls[0]["status"] == "orange"


@pytest.mark.asyncio
async def test_gateway_only_master_without_local_sensors_gets_no_direct_display(
    hass, enable_custom_integrations
):
    device = await _esphome_device(hass, name="master")
    room = _room()
    station = _station(device, role=HARDWARE_ROLE_MASTER)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "master", calls)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(status="orange"))
    await hass.async_block_till_done()

    assert calls == []


@pytest.mark.asyncio
async def test_node_never_receives_direct_display_push(hass, enable_custom_integrations):
    device = await _esphome_device(hass, name="node")
    room = _room()
    station = _station(device, role=HARDWARE_ROLE_NODE)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "node", calls)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(status="red"))
    await hass.async_block_till_done()

    assert calls == []


@pytest.mark.asyncio
async def test_identical_display_payload_is_not_resent(hass, enable_custom_integrations):
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "station", calls)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    snapshot = _snapshot(status="green", recommendation_key="optional")
    dispatcher.queue_room(room.subentry_id, snapshot)
    await hass.async_block_till_done()
    dispatcher.queue_room(room.subentry_id, snapshot)
    await hass.async_block_till_done()

    assert len(calls) == 1


@pytest.mark.asyncio
async def test_changed_recommendation_is_resent(hass, enable_custom_integrations):
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "station", calls)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(recommendation_key="optional"))
    await hass.async_block_till_done()
    dispatcher.queue_room(
        room.subentry_id,
        _snapshot(status="orange", recommendation_key="open_now"),
    )
    await hass.async_block_till_done()

    assert len(calls) == 2
    assert calls[-1]["recommendation_key"] == "open_now"
    assert calls[-1]["status"] == "orange"


@pytest.mark.asyncio
async def test_changed_safety_lock_is_pushed_immediately(hass, enable_custom_integrations):
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "station", calls)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(status="green"))
    await hass.async_block_till_done()
    dispatcher.queue_room(
        room.subentry_id,
        _snapshot(status="red", recommendation_key="close_now", safety_lock=True),
    )
    await hass.async_block_till_done()

    assert len(calls) == 2
    assert calls[-1]["status"] == "locked"
    assert calls[-1]["safety_lock"] is True


@pytest.mark.asyncio
async def test_missing_display_action_is_deferred_and_later_registration_flushes(
    hass, enable_custom_integrations
):
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.start()
    dispatcher.queue_room(room.subentry_id, _snapshot(status="yellow"))
    await hass.async_block_till_done()
    assert calls == []
    assert station.subentry_id in dispatcher._desired

    _register_display_service(hass, "station", calls)
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0]["status"] == "yellow"
    dispatcher.stop()


@pytest.mark.asyncio
async def test_offline_display_device_never_breaks_room_result(hass, enable_custom_integrations):
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []
    _register_display_service(hass, "station", calls, fail=True)

    dispatcher = DirectDisplayDispatcher(hass, entry)
    # queue_room is deliberately synchronous/non-blocking from the coordinator's
    # point of view. The transport failure is swallowed by the background task.
    dispatcher.queue_room(room.subentry_id, _snapshot(status="red"))
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert station.subentry_id in dispatcher._desired
    assert station.subentry_id not in dispatcher._sent
    assert station.subentry_id in dispatcher._next_due


@pytest.mark.asyncio
async def test_reconfigure_discards_old_ids_and_only_sends_new_assignment(
    hass, enable_custom_integrations
):
    device = await _esphome_device(hass)
    old_room = _room("room-old", "Alt")
    station = _station(device, room_id=old_room.subentry_id)
    entry = _local_entry(hass, old_room, station)
    dispatcher = DirectDisplayDispatcher(hass, entry)

    # Old firmware/action is missing, so the old payload becomes pending.
    dispatcher.queue_room(old_room.subentry_id, _snapshot(status="green"))
    await hass.async_block_till_done()

    # A station reconfigure reloads the ConfigEntry. The old dispatcher is
    # stopped (and therefore drops its obsolete ids) before the new room state
    # is published.
    dispatcher.stop()
    new_room = _room("room-new", "Neu")
    entry.subentries[new_room.subentry_id] = new_room
    station.data[CONF_HARDWARE_ROOM_ID] = new_room.subentry_id
    dispatcher = DirectDisplayDispatcher(hass, entry)
    calls = []
    _register_display_service(hass, "station", calls)

    dispatcher.queue_room(new_room.subentry_id, _snapshot(status="orange"))
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0]["station_subentry_id"] == station.subentry_id
    assert calls[0]["room_id"] == "room-new"
    assert calls[0]["room_name"] == "Neu"


@pytest.mark.asyncio
async def test_removed_station_never_receives_deferred_display(hass, enable_custom_integrations):
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.start()

    dispatcher.queue_room(room.subentry_id, _snapshot(status="green"))
    await hass.async_block_till_done()
    entry.subentries.pop(station.subentry_id)

    calls = []
    _register_display_service(hass, "station", calls)
    await hass.async_block_till_done()

    assert calls == []
    assert station.subentry_id not in dispatcher._desired
    dispatcher.stop()


def test_node_and_direct_paths_share_one_display_payload_builder():
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater import hardware_display as display_module
    from custom_components.lueftungsberater.display_payload import hardware_display_payload

    assert api_module._hardware_display_payload is hardware_display_payload
    assert display_module.hardware_display_payload is hardware_display_payload


@pytest.mark.asyncio
async def test_offline_display_retry_sends_latest_payload_when_device_recovers(
    hass, enable_custom_integrations
):
    from datetime import timedelta
    from homeassistant.util import dt as dt_util

    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []
    offline = [True]

    async def apply_display(call):
        calls.append(dict(call.data))
        if offline[0]:
            raise RuntimeError("device offline")

    hass.services.async_register(
        "esphome",
        f"station_{SERVICE_APPLY_DISPLAY_RESULT}",
        apply_display,
    )

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(status="yellow"))
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert station.subentry_id in dispatcher._next_due

    offline[0] = False
    dispatcher._next_due[station.subentry_id] = dt_util.utcnow() - timedelta(seconds=1)
    await dispatcher._retry_pending(None)
    await hass.async_block_till_done()

    assert len(calls) == 2
    assert dispatcher._sent[station.subentry_id]["status"] == "yellow"
    assert station.subentry_id not in dispatcher._next_due

@pytest.mark.asyncio
async def test_changed_safety_lock_bypasses_old_payload_backoff(
    hass, enable_custom_integrations
):
    """A new safety state must not wait behind an old offline-display backoff."""
    device = await _esphome_device(hass)
    room = _room()
    station = _station(device)
    entry = _local_entry(hass, room, station)
    calls = []
    offline = [True]

    async def apply_display(call):
        calls.append(dict(call.data))
        if offline[0]:
            raise RuntimeError("device offline")

    hass.services.async_register(
        "esphome",
        f"station_{SERVICE_APPLY_DISPLAY_RESULT}",
        apply_display,
    )

    dispatcher = DirectDisplayDispatcher(hass, entry)
    dispatcher.queue_room(room.subentry_id, _snapshot(status="green"))
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert station.subentry_id in dispatcher._next_due

    offline[0] = False
    dispatcher.queue_room(
        room.subentry_id,
        _snapshot(status="red", recommendation_key="close_now", safety_lock=True),
    )
    await hass.async_block_till_done()

    assert len(calls) == 2
    assert calls[-1]["status"] == "locked"
    assert calls[-1]["safety_lock"] is True
    assert station.subentry_id not in dispatcher._next_due

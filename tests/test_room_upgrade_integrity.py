"""Upgrade integrity for ordinary rooms, remote settings and recorded sources."""

from copy import deepcopy
from types import MappingProxyType

from homeassistant.config_entries import ConfigSubentry
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lueftungsberater import async_migrate_entry
from custom_components.lueftungsberater.const import DOMAIN


def entry(hass, *, rooms=1, minor=14, data=None, remote=False):
    obj = MockConfigEntry(
        domain=DOMAIN,
        title="Test",
        version=1,
        minor_version=minor,
        data=data or {"entry_kind": "remote" if remote else "local"},
    )
    obj.add_to_hass(hass)
    for index in range(rooms):
        add(
            hass,
            obj,
            f"room{index}",
            "room",
            {
                "room_name": f"Room {index}",
                "windows": ["binary_sensor.window"],
                "night_end_time": "06:30:00",
                "remote_room_share": True,
                "room_notify_triggers": [],
                "target_temperature": 23,
            },
        )
    return obj


def add(hass, obj, sid, kind, data):
    child = ConfigSubentry(
        data=MappingProxyType(data),
        subentry_id=sid,
        subentry_type=kind,
        title=sid,
        unique_id=None,
    )
    hass.config_entries.async_add_subentry(obj, child)
    return child


async def test_ordinary_rooms_remote_configuration_and_history_survive(hass):
    local = entry(hass, rooms=12)
    remote = entry(
        hass,
        rooms=3,
        remote=True,
        data={
            "entry_kind": "remote",
            "remote_host": "100.1.2.3",
            "remote_token": "secret",
        },
    )
    registry = er.async_get(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=local.entry_id,
        config_subentry_id="room0",
        identifiers={(DOMAIN, "room0")},
        name="Room",
    )
    history = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "room0_history_co2_in",
        config_entry=local,
        config_subentry_id="room0",
        device_id=device.id,
    )
    hass.data.setdefault(DOMAIN, {})["history"] = {"sentinel": ["co2_in", "temp_in"]}
    before = {
        obj.entry_id: {key: dict(child.data) for key, child in obj.subentries.items()}
        for obj in (local, remote)
    }
    history_before = deepcopy(hass.data[DOMAIN]["history"])
    for obj in (local, remote):
        assert await async_migrate_entry(hass, obj)
        assert obj.minor_version == 15
        assert {
            key: dict(child.data) for key, child in obj.subentries.items()
        } == before[obj.entry_id]
    assert registry.async_get(history.entity_id) == history
    assert dr.async_get(hass).async_get(device.id) == device
    assert hass.data[DOMAIN]["history"] == history_before
    assert remote.data["remote_token"] == "secret"

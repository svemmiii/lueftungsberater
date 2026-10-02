from datetime import timedelta
from types import SimpleNamespace

import pytest

from custom_components.lueftungsberater.const import (
    CONF_HARDWARE_CONNECTION_TYPE,
    CONF_HARDWARE_DEVICE_ID,
    CONF_HARDWARE_ID,
    CONF_HARDWARE_LOCATION_MODE,
    CONF_HARDWARE_MASTER_SECRET,
    CONF_HARDWARE_MASTER_CREDENTIAL_RESET,
    CONF_HARDWARE_MASTER_SUBENTRY_ID,
    CONF_HARDWARE_PARTICIPANTS_HASH,
    CONF_HARDWARE_ROLE,
    CONF_HARDWARE_ROOM_ID,
    HARDWARE_CONNECTION_DIRECT,
    HARDWARE_CONNECTION_MASTER,
    HARDWARE_LOCATION_LOCAL,
    HARDWARE_ROLE_MASTER,
    HARDWARE_ROLE_NODE,
    HARDWARE_ROLE_STANDALONE,
    SUBENTRY_TYPE_ROOM,
    SUBENTRY_TYPE_STATION,
)
from custom_components.lueftungsberater.hardware_provisioning import (
    HardwareProvisioningError,
    _wait_for_diagnostic_state,
    async_provision_station,
    async_start_master_participant_retry,
    async_sync_master_participants,
    master_participant_topology_hash,
    station_physical_hardware_id,
)


async def _esphome_device(hass, *, name="esp4", mac="AA:BB:CC:DD:EE:04"):
    from homeassistant.helpers import device_registry as dr, entity_registry as er
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
    registry = er.async_get(hass)

    def diagnostic(platform, key, original_name, state):
        item = registry.async_get_or_create(
            platform,
            "esphome",
            f"{mac}-{key}",
            device_id=device.id,
            original_name=original_name,
        )
        hass.states.async_set(item.entity_id, state)
        return item.entity_id

    diagnostics = {
        "provisioned": diagnostic(
            "binary_sensor", "provisioned", "Lüftungsstation Provisioniert", "on"
        ),
        "credential": diagnostic(
            "binary_sensor",
            "credential",
            "Lüftungsstation Master-Credential konfiguriert",
            "on",
        ),
        "wireguard": diagnostic(
            "binary_sensor",
            "wireguard",
            "Lüftungsstation WireGuard konfiguriert",
            "on",
        ),
        "role": diagnostic("sensor", "role", "Lüftungsstation Rolle", "standalone"),
        "location": diagnostic(
            "sensor", "location", "Lüftungsstation Standort", "local"
        ),
        "room": diagnostic("sensor", "room", "Lüftungsstation Raum-ID", "old-room"),
        "master": diagnostic("sensor", "master", "Lüftungsstation Master", "-"),
        "paired": diagnostic(
            "sensor", "paired", "Lüftungsstation Gekoppelte Nodes", "0"
        ),
        "topology": diagnostic(
            "sensor", "topology", "Lüftungsstation Topologie-Hash", "unknown"
        ),
    }
    return device, diagnostics


def _register_firmware_services(hass, name, diagnostics, calls):
    async def apply_config(call):
        calls.append((call.service, dict(call.data)))
        hass.states.async_set(diagnostics["provisioned"], "on", force_update=True)
        hass.states.async_set(diagnostics["role"], str(call.data["role"]), force_update=True)
        hass.states.async_set(diagnostics["location"], str(call.data["location_mode"]), force_update=True)
        hass.states.async_set(diagnostics["room"], str(call.data["room_id"] or "-"), force_update=True)
        hass.states.async_set(
            diagnostics["master"], str(call.data["master_hardware_id"] or "-"), force_update=True
        )
        if call.data["role"] != "master":
            hass.states.async_set(diagnostics["credential"], "off", force_update=True)

    async def apply_credential(call):
        calls.append((call.service, dict(call.data)))
        hass.states.async_set(diagnostics["credential"], "on", force_update=True)

    async def clear_wireguard(call):
        calls.append((call.service, dict(call.data)))
        hass.states.async_set(diagnostics["wireguard"], "off", force_update=True)

    async def apply_participants(call):
        calls.append((call.service, dict(call.data)))
        hass.states.async_set(
            diagnostics["paired"], str(len(call.data.get("hardware_ids", []))), force_update=True
        )
        hass.states.async_set(
            diagnostics["topology"], str(call.data.get("topology_hash") or ""), force_update=True
        )

    hass.services.async_register(
        "esphome", f"{name}_lueftungsstation_apply_station_config", apply_config
    )
    hass.services.async_register(
        "esphome",
        f"{name}_lueftungsstation_apply_master_credential",
        apply_credential,
    )
    hass.services.async_register(
        "esphome", f"{name}_lueftungsstation_clear_wireguard", clear_wireguard
    )
    hass.services.async_register(
        "esphome",
        f"{name}_lueftungsstation_apply_participants",
        apply_participants,
    )

@pytest.mark.asyncio
async def test_physical_station_id_comes_from_network_mac(hass, enable_custom_integrations):
    device, _diagnostics = await _esphome_device(hass)
    assert station_physical_hardware_id(hass, device.id, direct=True) == "DIRECT:AA:BB:CC:DD:EE:04"
    assert station_physical_hardware_id(hass, device.id, direct=False) == "AA:BB:CC:DD:EE:04"


@pytest.mark.asyncio
async def test_master_provisioning_pushes_role_and_generated_secret(hass, enable_custom_integrations):
    device, diagnostics = await _esphome_device(hass)
    calls = []
    _register_firmware_services(hass, "esp4", diagnostics, calls)

    secret = "S" * 43
    station = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "DIRECT:AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ROOM_ID: "room-1",
            CONF_HARDWARE_LOCATION_MODE: HARDWARE_LOCATION_LOCAL,
            CONF_HARDWARE_MASTER_SECRET: secret,
            CONF_HARDWARE_MASTER_CREDENTIAL_RESET: True,
        },
    )
    entry = SimpleNamespace(entry_id="advisor", subentries={"master-subentry": station})

    await async_provision_station(hass, entry, station)

    assert calls[0][0] == "esp4_lueftungsstation_apply_station_config"
    assert calls[0][1]["role"] == "standalone"
    assert calls[1][0] == "esp4_lueftungsstation_apply_station_config"
    assert calls[1][1]["role"] == "master"
    assert calls[1][1]["station_subentry_id"] == "master-subentry"
    assert calls[2] == (
        "esp4_lueftungsstation_apply_master_credential",
        {"master_secret": secret},
    )
    assert calls[3][0] == "esp4_lueftungsstation_clear_wireguard"


@pytest.mark.asyncio
async def test_standalone_provisioning_does_not_require_or_send_master_secret(hass, enable_custom_integrations):
    device, diagnostics = await _esphome_device(hass, name="station")
    calls = []
    _register_firmware_services(hass, "station", diagnostics, calls)

    station = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="standalone-subentry",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "DIRECT:AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_STANDALONE,
            CONF_HARDWARE_ROOM_ID: "room-1",
            CONF_HARDWARE_LOCATION_MODE: HARDWARE_LOCATION_LOCAL,
        },
    )
    entry = SimpleNamespace(entry_id="advisor", subentries={"standalone-subentry": station})

    await async_provision_station(hass, entry, station)

    assert [name for name, _ in calls] == [
        "station_lueftungsstation_apply_station_config",
        "station_lueftungsstation_clear_wireguard",
    ]
    assert all("master_secret" not in data for _, data in calls)


@pytest.mark.asyncio
async def test_stale_on_diagnostic_does_not_confirm_new_provisioning(
    hass, enable_custom_integrations
):
    device, diagnostics = await _esphome_device(hass)
    from homeassistant.util import dt as dt_util

    with pytest.raises(HardwareProvisioningError, match="did not freshly confirm"):
        await _wait_for_diagnostic_state(
            hass,
            device.id,
            name_contains="Lüftungsstation Provisioniert",
            expected="on",
            fresh_after=dt_util.utcnow(),
            timeout=0.05,
        )


@pytest.mark.asyncio
async def test_new_master_credential_forces_off_on_handshake(
    hass, enable_custom_integrations
):
    device, diagnostics = await _esphome_device(hass)
    calls = []
    _register_firmware_services(hass, "esp4", diagnostics, calls)
    station = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ROOM_ID: "room-1",
            CONF_HARDWARE_LOCATION_MODE: HARDWARE_LOCATION_LOCAL,
            CONF_HARDWARE_MASTER_SECRET: "N" * 43,
            CONF_HARDWARE_MASTER_CREDENTIAL_RESET: True,
        },
    )
    entry = SimpleNamespace(entry_id="advisor", subentries={"master-subentry": station})

    await async_provision_station(hass, entry, station)

    config_roles = [
        data["role"]
        for service, data in calls
        if service.endswith("apply_station_config")
    ]
    assert config_roles[:2] == ["standalone", "master"]
    assert hass.states.get(diagnostics["credential"]).state == "on"


@pytest.mark.asyncio
async def test_normal_master_reconfigure_reapplies_same_ha_secret(
    hass, enable_custom_integrations
):
    device, diagnostics = await _esphome_device(hass)
    calls = []
    _register_firmware_services(hass, "esp4", diagnostics, calls)
    secret = "P" * 43
    station = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        title="Master",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ROOM_ID: "room-1",
            CONF_HARDWARE_LOCATION_MODE: HARDWARE_LOCATION_LOCAL,
            CONF_HARDWARE_MASTER_SECRET: secret,
        },
    )
    entry = SimpleNamespace(entry_id="assistant", subentries={"master-subentry": station})

    await async_provision_station(hass, entry, station)

    credential_calls = [
        data
        for service, data in calls
        if service.endswith("lueftungsstation_apply_master_credential")
    ]
    assert credential_calls == [{"master_secret": secret}]


@pytest.mark.asyncio
async def test_master_participant_sync_defers_when_firmware_action_is_missing(
    hass, enable_custom_integrations
):
    device, diagnostics = await _esphome_device(hass)
    calls = []
    _register_firmware_services(hass, "esp4", diagnostics, calls)
    hass.services.async_remove(
        "esphome", "esp4_lueftungsstation_apply_participants"
    )

    room_master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_ROOM, subentry_id="room-master", title="Technik"
    )
    master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        title="Master",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ROOM_ID: "room-master",
        },
    )
    entry = SimpleNamespace(
        entry_id="assistant",
        subentries={"room-master": room_master, "master-subentry": master},
    )

    assert await async_sync_master_participants(hass, entry, master) is False
    assert CONF_HARDWARE_PARTICIPANTS_HASH not in master.data



@pytest.mark.asyncio
async def test_master_participant_sync_replaces_complete_ha_owned_list(
    hass, enable_custom_integrations, monkeypatch
):
    device, diagnostics = await _esphome_device(hass)
    calls = []
    _register_firmware_services(hass, "esp4", diagnostics, calls)

    room_master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_ROOM, subentry_id="room-master", title="Technik"
    )
    room_a = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_ROOM, subentry_id="room-a", title="Wohnzimmer"
    )
    room_b = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_ROOM, subentry_id="room-b", title="Schlafzimmer"
    )
    master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        title="Master",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ROOM_ID: "room-master",
        },
    )
    node_a = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="node-a",
        title="Node A",
        data={
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:11",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_ROOM_ID: "room-a",
            CONF_HARDWARE_MASTER_SUBENTRY_ID: "master-subentry",
        },
    )
    node_b = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="node-b",
        title="Node B",
        data={
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:12",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_ROOM_ID: "room-b",
            CONF_HARDWARE_MASTER_SUBENTRY_ID: "master-subentry",
        },
    )
    entry = SimpleNamespace(
        entry_id="assistant",
        subentries={
            "room-master": room_master,
            "room-a": room_a,
            "room-b": room_b,
            "master-subentry": master,
            "node-a": node_a,
            "node-b": node_b,
        },
    )
    updates = []

    def fake_update_subentry(_entry, _subentry, *, data):
        updates.append(dict(data))
        _subentry.data = dict(data)
        return True

    monkeypatch.setattr(
        hass.config_entries, "async_update_subentry", fake_update_subentry
    )

    expected_hash = master_participant_topology_hash(entry, master)
    assert await async_sync_master_participants(hass, entry, master) is True

    topology_calls = [
        data
        for service, data in calls
        if service.endswith("lueftungsstation_apply_participants")
    ]
    assert topology_calls == [
        {
            "hardware_ids": ["AA:BB:CC:DD:EE:11", "AA:BB:CC:DD:EE:12"],
            "station_subentry_ids": ["node-a", "node-b"],
            "room_ids": ["room-a", "room-b"],
            "topology_hash": expected_hash,
        }
    ]
    assert updates[-1][CONF_HARDWARE_PARTICIPANTS_HASH] == expected_hash

    # A room move is part of HA's desired topology and therefore changes the
    # digest even though the physical MAC list itself stayed identical.
    node_b.data[CONF_HARDWARE_ROOM_ID] = "room-a"
    assert master_participant_topology_hash(entry, master) != expected_hash


@pytest.mark.asyncio
async def test_master_participant_sync_reapplies_after_master_cache_reset(
    hass, enable_custom_integrations, monkeypatch
):
    device, diagnostics = await _esphome_device(hass)
    calls = []
    _register_firmware_services(hass, "esp4", diagnostics, calls)

    room_master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_ROOM, subentry_id="room-master", title="Technik"
    )
    room_a = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_ROOM, subentry_id="room-a", title="Wohnzimmer"
    )
    master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        title="Master",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ROOM_ID: "room-master",
        },
    )
    node = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="node-a",
        title="Node A",
        data={
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:11",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_ROOM_ID: "room-a",
            CONF_HARDWARE_MASTER_SUBENTRY_ID: "master-subentry",
        },
    )
    entry = SimpleNamespace(
        entry_id="assistant",
        subentries={
            "room-master": room_master,
            "room-a": room_a,
            "master-subentry": master,
            "node-a": node,
        },
    )

    def fake_update_subentry(_entry, _subentry, *, data):
        _subentry.data = dict(data)
        return True

    monkeypatch.setattr(
        hass.config_entries, "async_update_subentry", fake_update_subentry
    )

    expected_hash = master_participant_topology_hash(entry, master)
    assert await async_sync_master_participants(hass, entry, master) is True
    assert master.data[CONF_HARDWARE_PARTICIPANTS_HASH] == expected_hash

    # Simulate a master reflash/factory reset: HA still remembers the last hash,
    # but the device itself no longer reports that topology. The stored HA hash
    # must never suppress the full replacement push.
    hass.states.async_set(diagnostics["topology"], "unknown")
    before = len(
        [
            1
            for service, _data in calls
            if service.endswith("lueftungsstation_apply_participants")
        ]
    )
    assert await async_sync_master_participants(hass, entry, master) is True
    after = len(
        [
            1
            for service, _data in calls
            if service.endswith("lueftungsstation_apply_participants")
        ]
    )
    assert after == before + 1
    assert hass.states.get(diagnostics["topology"]).state == expected_hash


@pytest.mark.asyncio
async def test_master_participant_sync_requires_topology_hash_diagnostic(
    hass, enable_custom_integrations, monkeypatch
):
    from homeassistant.helpers import entity_registry as er

    device, diagnostics = await _esphome_device(hass)
    calls = []
    _register_firmware_services(hass, "esp4", diagnostics, calls)
    er.async_get(hass).async_remove(diagnostics["topology"])
    hass.states.async_remove(diagnostics["topology"])

    master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        title="Master",
        data={
            CONF_HARDWARE_DEVICE_ID: device.id,
            CONF_HARDWARE_ID: "AA:BB:CC:DD:EE:04",
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ROOM_ID: "room-master",
            CONF_HARDWARE_PARTICIPANTS_HASH: "legacy-ha-only-hash",
        },
    )
    entry = SimpleNamespace(entry_id="assistant", subentries={"master-subentry": master})

    assert await async_sync_master_participants(hass, entry, master) is False
    assert not [
        service
        for service, _data in calls
        if service.endswith("lueftungsstation_apply_participants")
    ]


@pytest.mark.asyncio
async def test_master_participant_retry_does_not_depend_on_service_registered_event(
    hass, enable_custom_integrations, monkeypatch
):
    import custom_components.lueftungsberater.hardware_provisioning as provisioning

    master = SimpleNamespace(
        subentry_type=SUBENTRY_TYPE_STATION,
        subentry_id="master-subentry",
        title="Master",
        data={CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER},
    )
    unload_callbacks = []
    entry = SimpleNamespace(
        entry_id="assistant",
        data={},
        subentries={"master-subentry": master},
        async_on_unload=unload_callbacks.append,
    )
    scheduled = {}

    def fake_track(_hass, callback, interval):
        scheduled["callback"] = callback
        scheduled["interval"] = interval
        return lambda: None

    attempts = []

    async def fake_sync(_hass, _entry, _master, *, service_timeout=2.0):
        attempts.append(service_timeout)
        return len(attempts) >= 2

    now = [provisioning.dt_util.utcnow()]
    monkeypatch.setattr(provisioning, "async_track_time_interval", fake_track)
    monkeypatch.setattr(provisioning, "async_sync_master_participants", fake_sync)
    monkeypatch.setattr(provisioning.dt_util, "utcnow", lambda: now[0])

    async_start_master_participant_retry(hass, entry)
    assert scheduled["interval"] == timedelta(minutes=1)
    assert len(unload_callbacks) == 1

    # First periodic attempt fails/deferred and schedules the one-minute retry.
    await scheduled["callback"](None)
    assert attempts == [2.0]

    # No service_registered event occurs. Advancing the clock is sufficient for
    # the bounded timer to retry and recover the topology by itself.
    now[0] += timedelta(minutes=1)
    await scheduled["callback"](None)
    assert attempts == [2.0, 2.0]

@pytest.mark.asyncio
async def test_master_id_diagnostic_does_not_select_credential_sensor(hass):
    from custom_components.lueftungsberater.hardware_provisioning import _diagnostic_entity
    device, diagnostics = await _esphome_device(hass)
    assert _diagnostic_entity(hass, device.id, name_contains="Lüftungsstation Master") == diagnostics["master"]
    assert _diagnostic_entity(hass, device.id, name_contains="Master-Credential konfiguriert") == diagnostics["credential"]

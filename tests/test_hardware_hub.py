from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from custom_components.lueftungsberater.const import DATA_HARDWARE_HUBS, DOMAIN
from custom_components.lueftungsberater.hardware_hub import (
    StationRuntime,
    expire_stale_stations,
    station_is_fresh,
)

UTC = timezone.utc


def test_station_freshness_expires_after_three_missed_minutes():
    now = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
    state = StationRuntime(
        hardware_id="AA:BB",
        master_id="master",
        online=True,
        last_seen=now - timedelta(seconds=179),
    )
    assert station_is_fresh(state, now=now) is True

    state.last_seen = now - timedelta(seconds=181)
    assert station_is_fresh(state, now=now) is False


def test_expire_stale_station_marks_it_offline_and_notifies(monkeypatch):
    now = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
    state = StationRuntime(
        hardware_id="AA:BB",
        master_id="master",
        online=True,
        last_seen=now - timedelta(minutes=4),
    )
    hass = SimpleNamespace(
        data={
            DOMAIN: {
                DATA_HARDWARE_HUBS: {
                    "entry": {"states": {"station": state}}
                }
            }
        }
    )
    entry = SimpleNamespace(entry_id="entry")
    sent = []

    monkeypatch.setattr(
        "custom_components.lueftungsberater.hardware_hub.async_dispatcher_send",
        lambda *args: sent.append(args),
    )

    expired = expire_stale_stations(hass, entry, now=now)

    assert expired == ("station",)
    assert state.online is False
    assert sent


def test_legacy_station_defaults_to_master_connection():
    from custom_components.lueftungsberater.hardware_hub import station_connection_type
    from custom_components.lueftungsberater.const import HARDWARE_CONNECTION_MASTER

    station = SimpleNamespace(data={})
    assert station_connection_type(station) == HARDWARE_CONNECTION_MASTER


def test_direct_station_reads_cached_ha_entities_without_master_runtime():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_DIRECT_CO2,
        CONF_HARDWARE_DIRECT_HUMIDITY,
        CONF_HARDWARE_DIRECT_TEMP,
        HARDWARE_CONNECTION_DIRECT,
    )
    from custom_components.lueftungsberater.hardware_hub import direct_station_value

    class States:
        values = {
            "sensor.direct_co2": SimpleNamespace(state="1234"),
            "sensor.direct_temp": SimpleNamespace(state="22.5"),
            "sensor.direct_humidity": SimpleNamespace(state="54.2"),
        }

        def get(self, entity_id):
            return self.values.get(entity_id)

    hass = SimpleNamespace(states=States())
    station = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_DIRECT_CO2: "sensor.direct_co2",
            CONF_HARDWARE_DIRECT_TEMP: "sensor.direct_temp",
            CONF_HARDWARE_DIRECT_HUMIDITY: "sensor.direct_humidity",
        }
    )

    assert direct_station_value(hass, station, "co2") == 1234.0
    assert direct_station_value(hass, station, "temperature") == 22.5
    assert direct_station_value(hass, station, "humidity") == 54.2


def test_direct_station_rejects_unavailable_cached_value():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_DIRECT_CO2,
        CONF_HARDWARE_DIRECT_HUMIDITY,
        CONF_HARDWARE_DIRECT_TEMP,
        HARDWARE_CONNECTION_DIRECT,
    )
    from custom_components.lueftungsberater.hardware_hub import direct_station_value

    class States:
        def get(self, entity_id):
            return SimpleNamespace(state="unavailable")

    hass = SimpleNamespace(states=States())
    station = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_DIRECT_CO2: "sensor.direct_co2",
            CONF_HARDWARE_DIRECT_TEMP: "sensor.direct_temp",
            CONF_HARDWARE_DIRECT_HUMIDITY: "sensor.direct_humidity",
        }
    )
    assert direct_station_value(hass, station, "co2") is None


def test_direct_station_rejects_stale_numeric_state():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_DIRECT_CO2,
        CONF_HARDWARE_DIRECT_HUMIDITY,
        CONF_HARDWARE_DIRECT_TEMP,
        HARDWARE_CONNECTION_DIRECT,
    )
    from custom_components.lueftungsberater.hardware_hub import direct_station_value

    stale = datetime.now(UTC) - timedelta(minutes=4)

    class States:
        def get(self, entity_id):
            return SimpleNamespace(state="1234", last_reported=stale)

    hass = SimpleNamespace(states=States())
    station = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_DIRECT_CO2: "sensor.direct_co2",
            CONF_HARDWARE_DIRECT_TEMP: "sensor.direct_temp",
            CONF_HARDWARE_DIRECT_HUMIDITY: "sensor.direct_humidity",
        }
    )
    assert direct_station_value(hass, station, "co2") is None


def test_master_report_rejects_implausible_sensor_values(monkeypatch):
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
    )
    from custom_components.lueftungsberater.hardware_hub import report_station

    monkeypatch.setattr(
        "custom_components.lueftungsberater.hardware_hub.async_dispatcher_send",
        lambda *_args: None,
    )
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry")
    station = SimpleNamespace(
        subentry_id="station",
        data={CONF_HARDWARE_ID: "AA:BB", CONF_HARDWARE_MASTER_ID: "master"},
    )

    state = report_station(
        hass,
        entry,
        station,
        {"co2": -1, "temperature": 999, "humidity": 140},
    )

    assert state.co2 is None
    assert state.temperature is None
    assert state.humidity is None


def test_v0101_roles_are_separate_from_transport():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_ROLE,
        HARDWARE_CONNECTION_DIRECT,
        HARDWARE_CONNECTION_MASTER,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        HARDWARE_ROLE_STANDALONE,
    )
    from custom_components.lueftungsberater.hardware_hub import (
        station_is_master,
        station_role,
        station_uses_hardware_hub,
    )

    direct_master = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
        }
    )
    assert station_is_master(direct_master) is True
    assert station_uses_hardware_hub(direct_master) is False

    node = SimpleNamespace(
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
        }
    )
    assert station_is_master(node) is False
    assert station_uses_hardware_hub(node) is True

    legacy_direct = SimpleNamespace(
        data={CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT}
    )
    assert station_role(legacy_direct) == HARDWARE_ROLE_STANDALONE

    legacy_hub = SimpleNamespace(data={})
    assert station_role(legacy_hub) == HARDWARE_ROLE_NODE


def test_configured_master_relation_uses_subentry_id_before_legacy_id():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_STATION,
    )
    from custom_components.lueftungsberater.hardware_hub import configured_master_for_station

    master = SimpleNamespace(
        subentry_id="master-subentry",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={CONF_HARDWARE_ID: "AA:BB", CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER},
    )
    node = SimpleNamespace(
        subentry_id="node-subentry",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_MASTER_SUBENTRY_ID: master.subentry_id,
            # Deliberately stale legacy text; the stable subentry relation wins.
            CONF_HARDWARE_MASTER_ID: "OLD",
        },
    )
    entry = SimpleNamespace(subentries={master.subentry_id: master, node.subentry_id: node})
    assert configured_master_for_station(entry, node) is master


def test_legacy_direct_hardware_id_alias_matches_raw_id():
    from custom_components.lueftungsberater.hardware_hub import hardware_id_matches

    assert hardware_id_matches("DIRECT:AA:BB:CC", "AA:BB:CC") is True
    assert hardware_id_matches("AA-BB-CC", "DIRECT:AA:BB:CC") is True
    assert hardware_id_matches("AA:BB:CC", "DD:EE:FF") is False


def test_explicit_master_relation_does_not_fall_back_after_master_deletion():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_STATION,
    )
    from custom_components.lueftungsberater.hardware_hub import (
        configured_master_for_station,
        configured_master_hardware_id,
    )

    replacement = SimpleNamespace(
        subentry_id="replacement-master",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ID: "AA:BB",
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
        },
    )
    node = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_MASTER_SUBENTRY_ID: "deleted-master",
            # A stale cached id must not silently bind the node to replacement.
            CONF_HARDWARE_MASTER_ID: "AA:BB",
        },
    )
    entry = SimpleNamespace(
        subentries={replacement.subentry_id: replacement, node.subentry_id: node}
    )

    assert configured_master_for_station(entry, node) is None
    assert configured_master_hardware_id(entry, node) is None


def test_master_hardware_id_is_derived_from_stable_relation():
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_STATION,
    )
    from custom_components.lueftungsberater.hardware_hub import (
        configured_master_hardware_id,
    )

    master = SimpleNamespace(
        subentry_id="master",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ID: "DIRECT:NEW:MASTER",
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
        },
    )
    node = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_MASTER_SUBENTRY_ID: master.subentry_id,
            CONF_HARDWARE_MASTER_ID: "OLD:MASTER",
        },
    )
    entry = SimpleNamespace(subentries={master.subentry_id: master, node.subentry_id: node})

    assert configured_master_hardware_id(entry, node) == "DIRECT:NEW:MASTER"


def test_explicit_deleted_master_invalidates_station_topology():
    from types import SimpleNamespace

    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        HARDWARE_ROLE_NODE,
    )
    from custom_components.lueftungsberater.hardware_hub import station_topology_valid

    node = SimpleNamespace(
        data={
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_MASTER_SUBENTRY_ID: "deleted-master",
        }
    )
    entry = SimpleNamespace(subentries={})

    assert station_topology_valid(entry, node) is False


def test_legacy_node_without_stable_master_relation_remains_compatible():
    from types import SimpleNamespace

    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ROLE,
        CONF_HARDWARE_ROOM_ID,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_ROOM,
    )
    from custom_components.lueftungsberater.hardware_hub import station_topology_valid

    room = SimpleNamespace(subentry_id="room", subentry_type=SUBENTRY_TYPE_ROOM)
    node = SimpleNamespace(
        data={CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE, CONF_HARDWARE_ROOM_ID: room.subentry_id}
    )
    entry = SimpleNamespace(subentries={room.subentry_id: room})

    assert station_topology_valid(entry, node) is True


def test_deleted_room_invalidates_station_topology_immediately():
    from types import SimpleNamespace

    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ROLE,
        CONF_HARDWARE_ROOM_ID,
        HARDWARE_ROLE_NODE,
    )
    from custom_components.lueftungsberater.hardware_hub import (
        station_topology_error,
        station_topology_valid,
    )

    node = SimpleNamespace(
        data={CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE, CONF_HARDWARE_ROOM_ID: "deleted-room"}
    )
    entry = SimpleNamespace(subentries={})

    assert station_topology_error(entry, node) == "room_missing"
    assert station_topology_valid(entry, node) is False


def test_reported_firmware_updates_device_registry_immediately(monkeypatch):
    from custom_components.lueftungsberater import hardware_hub as hub
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
        CONF_HARDWARE_ROLE,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_STATION,
    )

    station = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ID: "NODE-03",
            CONF_HARDWARE_MASTER_ID: "MASTER-01",  # legacy fallback is enough here
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
        },
    )
    entry = SimpleNamespace(entry_id="entry", subentries={station.subentry_id: station})
    hass = SimpleNamespace(data={})

    device = SimpleNamespace(
        id="device-id",
        identifiers={(hub.DOMAIN, "station:NODE-03")},
    )
    updates = []

    class Registry:
        def async_update_device(self, device_id, **kwargs):
            updates.append((device_id, kwargs))

    registry = Registry()
    monkeypatch.setattr(hub.dr, "async_get", lambda _hass: registry)
    monkeypatch.setattr(
        hub.dr,
        "async_entries_for_config_entry",
        lambda _registry, *, config_entry_id: [device],
    )
    monkeypatch.setattr(hub, "async_dispatcher_send", lambda *_args: None)

    hub.report_station(
        hass,
        entry,
        station,
        {"co2": 900, "temperature": 21.5, "humidity": 48, "firmware": "1.0.3"},
    )

    assert updates == [("device-id", {"sw_version": "1.0.3"})]

import pytest
from types import SimpleNamespace

from custom_components.lueftungsberater.api import REMOTE_ATTRIBUTE_KEYS, _export_attributes


def test_remote_export_does_not_include_local_entity_ids_or_original_warning() -> None:
    attrs = _export_attributes(
        {
            "room_name": "Küche",
            "status": "green",
            "display_mode": "room_air",
            "recommendation": "Jetzt lüften",
            "temperature_inside": 23.0,
            "source_temperature_inside": "sensor.kueche_temperatur",
            "source_absolute_humidity_outside": "sensor.kueche_absolute_feuchte_aussen",
            "original_warning_text": "provider payload",
            "localized_texts": {"de": {"reason": "alt"}},
        },
        "°C",
        remote_export=True,
    )

    assert attrs["room_name"] == "Küche"
    assert attrs["temperature_inside"] == 23.0
    assert attrs["display_mode"] == "room_air"
    assert "source_temperature_inside" not in attrs
    assert "source_absolute_humidity_outside" not in attrs
    assert "original_warning_text" not in attrs
    assert "localized_texts" not in attrs


def test_remote_allow_list_stays_current_only() -> None:
    assert "last_confirmed_airing" not in REMOTE_ATTRIBUTE_KEYS
    assert "source_window_entities" not in REMOTE_ATTRIBUTE_KEYS
    assert "original_warning_text" not in REMOTE_ATTRIBUTE_KEYS
    assert "localized_texts" not in REMOTE_ATTRIBUTE_KEYS
    assert "display_mode" in REMOTE_ATTRIBUTE_KEYS


async def test_snapshot_http_api_rejects_non_admin_user():
    from types import SimpleNamespace
    from custom_components.lueftungsberater.api import LueftungsberaterSnapshotView
    from homeassistant.components.http import KEY_HASS_USER

    class FakeRequest(dict):
        remote = "100.64.0.42"
        query = {}

    request = FakeRequest()
    request[KEY_HASS_USER] = SimpleNamespace(is_admin=False)
    response = await LueftungsberaterSnapshotView().get(request)
    assert response.status == 403


def test_remote_allow_list_contains_forecast_status():
    assert "forecast_data_status" in REMOTE_ATTRIBUTE_KEYS


def test_remote_overview_websocket_requires_admin() -> None:
    from homeassistant.exceptions import Unauthorized
    from custom_components.lueftungsberater.api import websocket_remote_overview

    connection = SimpleNamespace(user=SimpleNamespace(is_admin=False))
    with pytest.raises(Unauthorized):
        websocket_remote_overview(SimpleNamespace(), connection, {"id": 1})


def test_remote_loading_snapshot_does_not_invent_closed_window() -> None:
    from custom_components.lueftungsberater.api import _loading_remote_room_attributes

    entry = SimpleNamespace(entry_id="advisor", title="Meine Wohnung")
    subentry = SimpleNamespace(
        title="Wohnzimmer",
        data={"window_entities": ["binary_sensor.window"], "co2_entity": "sensor.co2"},
    )
    attrs = _loading_remote_room_attributes(entry, subentry)
    assert attrs["availability"] == "loading"
    assert attrs["window_open"] is None
    assert attrs["mode"] == "incomplete_data"


def test_remote_client_values_are_bounded() -> None:
    from custom_components.lueftungsberater.api import (
        REMOTE_CLIENT_ID_MAX_LENGTH,
        REMOTE_CLIENT_NAME_MAX_LENGTH,
        _normalize_remote_client_value,
    )

    assert len(_normalize_remote_client_value("x" * 500, "legacy", REMOTE_CLIENT_ID_MAX_LENGTH)) == 128
    assert len(_normalize_remote_client_value("y" * 500, "Remote Home Assistant", REMOTE_CLIENT_NAME_MAX_LENGTH)) == 128
    assert _normalize_remote_client_value("   ", "legacy", REMOTE_CLIENT_ID_MAX_LENGTH) == "legacy"


def test_remote_protocol_v3_marks_new_night_semantics() -> None:
    from custom_components.lueftungsberater.const import REMOTE_PROTOCOL_VERSION

    assert REMOTE_PROTOCOL_VERSION == 3
    assert "availability" in REMOTE_ATTRIBUTE_KEYS


def test_remote_access_bookkeeping_evicts_oldest_client(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import DATA_REMOTE_ACCESS, DOMAIN

    cancelled: list[bool] = []
    monkeypatch.setattr(
        api_module,
        "async_call_later",
        lambda _hass, _delay, _callback: (lambda: cancelled.append(True)),
    )
    monkeypatch.setattr(api_module, "_refresh_remote_access_entity", lambda *_args: None)

    hass = SimpleNamespace(data={})
    instances = [{"id": "entry", "rooms": [{"id": "room"}]}]
    for index in range(api_module.REMOTE_CLIENTS_PER_ROOM_MAX + 1):
        api_module._record_remote_access(
            hass,
            instances,
            f"client-{index}",
            f"Client {index}",
        )

    clients = hass.data[DOMAIN][DATA_REMOTE_ACCESS]["entry:room"]
    assert len(clients) == api_module.REMOTE_CLIENTS_PER_ROOM_MAX
    assert "client-0" not in clients
    assert f"client-{api_module.REMOTE_CLIENTS_PER_ROOM_MAX}" in clients
    assert cancelled


def test_protocol2_snapshot_suppresses_only_new_night_states() -> None:
    from custom_components.lueftungsberater.api import _remote_instances_for_protocol

    instances = [
        {
            "id": "entry",
            "rooms": [
                {
                    "id": "room",
                    "attributes": {
                        "status": "green",
                        "night_ventilation_status": "short_only",
                        "night_ventilation_key": "night_short_only",
                        "night_ventilation_args": {"thermal_need": True},
                    },
                }
            ],
        }
    ]
    compatible = _remote_instances_for_protocol(instances, 2)
    attrs = compatible[0]["rooms"][0]["attributes"]
    assert attrs["status"] == "green"
    assert attrs["night_ventilation_status"] == "unavailable"
    assert attrs["night_ventilation_key"] is None
    assert attrs["night_ventilation_args"] == {}
    # The full v3 payload remains untouched.
    assert _remote_instances_for_protocol(instances, 3) is instances


def test_remote_access_cleanup_cancels_entry_timers(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import DATA_REMOTE_ACCESS, DOMAIN

    cancelled: list[str] = []
    callbacks = []

    def _later(_hass, _delay, callback):
        callbacks.append(callback)
        token = f"timer-{len(callbacks)}"
        return lambda: cancelled.append(token)

    monkeypatch.setattr(api_module, "async_call_later", _later)
    monkeypatch.setattr(api_module, "_refresh_remote_access_entity", lambda *_args: None)

    hass = SimpleNamespace(data={})
    api_module._record_remote_access(
        hass,
        [{"id": "entry-a", "rooms": [{"id": "room-1"}, {"id": "room-2"}]}],
        "client",
        "Client",
    )
    api_module._record_remote_access(
        hass,
        [{"id": "entry-b", "rooms": [{"id": "room-x"}]}],
        "client",
        "Client",
    )

    api_module.async_clear_remote_access(hass, "entry-a")

    store = hass.data[DOMAIN][DATA_REMOTE_ACCESS]
    assert "entry-a:room-1" not in store
    assert "entry-a:room-2" not in store
    assert "entry-b:room-x" in store
    assert len(cancelled) == 2


def test_hardware_config_payload_exposes_master_topology_and_wireguard_only_to_master():
    from types import SimpleNamespace
    from custom_components.lueftungsberater.api import _station_config_payload
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_ID,
        CONF_HARDWARE_LOCATION_MODE,
        CONF_HARDWARE_MASTER_ID,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        CONF_HARDWARE_ROOM_ID,
        CONF_HARDWARE_WG_ADDRESS,
        CONF_HARDWARE_WG_ALLOWED_IPS,
        CONF_HARDWARE_WG_ENDPOINT,
        CONF_HARDWARE_WG_ENDPOINT_HOST,
        CONF_HARDWARE_WG_ENDPOINT_PORT,
        CONF_HARDWARE_WG_KEEPALIVE,
        CONF_HARDWARE_WG_PEER_PUBLIC_KEY,
        CONF_HARDWARE_WG_PRIVATE_KEY,
        HARDWARE_CONNECTION_DIRECT,
        HARDWARE_CONNECTION_MASTER,
        HARDWARE_LOCATION_REMOTE,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_ROOM,
        SUBENTRY_TYPE_STATION,
    )

    room_master = SimpleNamespace(subentry_id="room-master", subentry_type=SUBENTRY_TYPE_ROOM, title="Wohnzimmer")
    room_node = SimpleNamespace(subentry_id="room-node", subentry_type=SUBENTRY_TYPE_ROOM, title="Schlafzimmer")
    master = SimpleNamespace(
        subentry_id="master",
        subentry_type=SUBENTRY_TYPE_STATION,
        title="Wohnzimmer · Master",
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ID: "DIRECT:AA:BB",
            CONF_HARDWARE_ROOM_ID: room_master.subentry_id,
            CONF_HARDWARE_LOCATION_MODE: HARDWARE_LOCATION_REMOTE,
            CONF_HARDWARE_WG_ADDRESS: "10.0.0.2/32",
            CONF_HARDWARE_WG_PRIVATE_KEY: "private",
            CONF_HARDWARE_WG_PEER_PUBLIC_KEY: "public",
            CONF_HARDWARE_WG_ENDPOINT: "host:53907",
            CONF_HARDWARE_WG_ENDPOINT_HOST: "host",
            CONF_HARDWARE_WG_ENDPOINT_PORT: 53907,
            CONF_HARDWARE_WG_ALLOWED_IPS: "192.168.178.0/24",
            CONF_HARDWARE_WG_KEEPALIVE: 45,
        },
    )
    node = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        title="Schlafzimmer · Station",
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_ID: "CC:DD",
            CONF_HARDWARE_ROOM_ID: room_node.subentry_id,
            CONF_HARDWARE_MASTER_ID: "DIRECT:AA:BB",
            CONF_HARDWARE_MASTER_SUBENTRY_ID: master.subentry_id,
        },
    )
    entry = SimpleNamespace(
        subentries={
            room_master.subentry_id: room_master,
            room_node.subentry_id: room_node,
            master.subentry_id: master,
            node.subentry_id: node,
        }
    )

    master_payload = _station_config_payload(entry, master)
    assert master_payload["role"] == HARDWARE_ROLE_MASTER
    assert master_payload["participants"][0]["hardware_id"] == "CC:DD"
    assert master_payload["wireguard"]["private_key"] == "private"

    node_payload = _station_config_payload(entry, node)
    assert node_payload["role"] == HARDWARE_ROLE_NODE
    assert node_payload["master"]["subentry_id"] == "master"
    assert "wireguard" not in node_payload


def test_hardware_report_rejects_wrong_or_missing_configured_master():
    from custom_components.lueftungsberater.api import _hardware_report_master_error
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_STATION,
    )

    master = SimpleNamespace(
        subentry_id="master",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ID: "DIRECT:AA:BB",
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
        },
    )
    node = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        data={
            CONF_HARDWARE_ID: "CC:DD",
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_MASTER_SUBENTRY_ID: master.subentry_id,
            CONF_HARDWARE_MASTER_ID: "STALE",
        },
    )
    entry = SimpleNamespace(subentries={master.subentry_id: master, node.subentry_id: node})

    assert _hardware_report_master_error(entry, node, "AA:BB") is None
    assert _hardware_report_master_error(entry, node, "EE:FF") == "master_mismatch"

    broken_entry = SimpleNamespace(subentries={node.subentry_id: node})
    assert _hardware_report_master_error(broken_entry, node, "AA:BB") == "master_missing"


def test_hardware_config_marks_node_with_deleted_master_as_configuration_error():
    from custom_components.lueftungsberater.api import _station_config_payload
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_ID,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        CONF_HARDWARE_ROOM_ID,
        HARDWARE_CONNECTION_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_ROOM,
        SUBENTRY_TYPE_STATION,
    )

    room = SimpleNamespace(
        subentry_id="room",
        subentry_type=SUBENTRY_TYPE_ROOM,
        title="Schlafzimmer",
    )
    node = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        title="Schlafzimmer · Station",
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_ID: "CC:DD",
            CONF_HARDWARE_ROOM_ID: room.subentry_id,
            CONF_HARDWARE_MASTER_SUBENTRY_ID: "deleted-master",
            CONF_HARDWARE_MASTER_ID: "AA:BB",
        },
    )
    entry = SimpleNamespace(subentries={room.subentry_id: room, node.subentry_id: node})

    payload = _station_config_payload(entry, node)
    assert payload["master"] is None
    assert payload["configuration_error"] == "master_missing"



def test_hardware_config_marks_deleted_room_and_master_omits_orphaned_node():
    from custom_components.lueftungsberater.api import _station_config_payload
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_ID,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_ROLE,
        CONF_HARDWARE_ROOM_ID,
        HARDWARE_CONNECTION_DIRECT,
        HARDWARE_CONNECTION_MASTER,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_ROOM,
        SUBENTRY_TYPE_STATION,
    )

    master_room = SimpleNamespace(
        subentry_id="master-room", subentry_type=SUBENTRY_TYPE_ROOM, title="Wohnzimmer"
    )
    master = SimpleNamespace(
        subentry_id="master",
        subentry_type=SUBENTRY_TYPE_STATION,
        title="Wohnzimmer · Master",
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ID: "DIRECT:AA:BB",
            CONF_HARDWARE_ROOM_ID: master_room.subentry_id,
        },
    )
    orphan = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        title="Altes Zimmer · Station",
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_ID: "CC:DD",
            CONF_HARDWARE_ROOM_ID: "deleted-room",
            CONF_HARDWARE_MASTER_SUBENTRY_ID: master.subentry_id,
        },
    )
    entry = SimpleNamespace(
        subentries={
            master_room.subentry_id: master_room,
            master.subentry_id: master,
            orphan.subentry_id: orphan,
        }
    )

    orphan_payload = _station_config_payload(entry, orphan)
    assert orphan_payload["configuration_error"] == "room_missing"
    assert orphan_payload["room_name"] is None

    master_payload = _station_config_payload(entry, master)
    assert master_payload["participants"] == []

def test_hardware_display_payload_uses_coordinator_snapshot_not_advisor_entity(monkeypatch):
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import (
        CONF_DISPLAY_MODE,
        DISPLAY_MODE_ROOM_AIR,
        SUBENTRY_TYPE_ROOM,
    )

    room = SimpleNamespace(
        subentry_id="room",
        subentry_type=SUBENTRY_TYPE_ROOM,
        title="Wohnzimmer",
    )
    result = SimpleNamespace(
        safety_lock=False,
        room_recommendation_key="can_close",
        recommendation_key="keep_open",
        room_status_color="green",
        color="orange",
    )
    snapshot = SimpleNamespace(result=result)
    coordinator = SimpleNamespace(data=snapshot)
    monkeypatch.setattr(api_module, "get_room_coordinator", lambda *_args: coordinator)

    hass = SimpleNamespace(config=SimpleNamespace(language="de"))
    entry = SimpleNamespace(
        data={CONF_DISPLAY_MODE: DISPLAY_MODE_ROOM_AIR},
        subentries={room.subentry_id: room},
    )

    payload = api_module._hardware_display_payload(hass, entry, room.subentry_id)
    assert payload["room_name"] == "Wohnzimmer"
    assert payload["status"] == "green"
    assert payload["recommendation_key"] == "can_close"
    assert payload["recommendation"] is not None
    assert payload["display_mode"] == DISPLAY_MODE_ROOM_AIR



def _native_report_fixture(location_mode: str):
    from custom_components.lueftungsberater.const import (
        CONF_HARDWARE_CONNECTION_TYPE,
        CONF_HARDWARE_ID,
        CONF_HARDWARE_LOCATION_MODE,
        CONF_HARDWARE_MASTER_SUBENTRY_ID,
        CONF_HARDWARE_MASTER_SECRET,
        CONF_HARDWARE_ROLE,
        CONF_HARDWARE_ROOM_ID,
        DOMAIN,
        ENTRY_KIND_LOCAL,
        HARDWARE_CONNECTION_DIRECT,
        HARDWARE_CONNECTION_MASTER,
        HARDWARE_ROLE_MASTER,
        HARDWARE_ROLE_NODE,
        SUBENTRY_TYPE_ROOM,
        SUBENTRY_TYPE_STATION,
    )
    from homeassistant.config_entries import ConfigEntryState

    room = SimpleNamespace(
        subentry_id="room-node",
        subentry_type=SUBENTRY_TYPE_ROOM,
        title="Schlafzimmer",
    )
    master = SimpleNamespace(
        subentry_id="master",
        subentry_type=SUBENTRY_TYPE_STATION,
        title="Wohnzimmer · Master",
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_MASTER,
            CONF_HARDWARE_ID: "DIRECT:B0:CB:D8:09:AB:1C",
            CONF_HARDWARE_LOCATION_MODE: location_mode,
            CONF_HARDWARE_ROOM_ID: "master-room",
            CONF_HARDWARE_MASTER_SECRET: "fixture-master-secret-0123456789abcdef",
        },
    )
    station = SimpleNamespace(
        subentry_id="node",
        subentry_type=SUBENTRY_TYPE_STATION,
        title="Schlafzimmer · Station",
        data={
            CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
            CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
            CONF_HARDWARE_ID: "B0:CB:D8:09:4C:C8",
            CONF_HARDWARE_MASTER_SUBENTRY_ID: master.subentry_id,
            CONF_HARDWARE_ROOM_ID: room.subentry_id,
        },
    )
    entry = SimpleNamespace(
        entry_id="entry",
        domain=DOMAIN,
        state=ConfigEntryState.LOADED,
        data={"entry_kind": ENTRY_KIND_LOCAL},
        subentries={room.subentry_id: room, master.subentry_id: master, station.subentry_id: station},
    )
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda _domain: [entry]),
        config=SimpleNamespace(language="de"),
    )
    return hass, entry, master, station


def test_native_hardware_report_action_uses_same_report_and_display_path(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import HARDWARE_LOCATION_LOCAL

    hass, entry, _master, station = _native_report_fixture(HARDWARE_LOCATION_LOCAL)
    reported = []
    monkeypatch.setattr(
        api_module,
        "report_station",
        lambda _hass, _entry, _station, payload: reported.append(dict(payload)),
    )
    monkeypatch.setattr(
        api_module,
        "_hardware_display_payload",
        lambda *_args: {
            "room_name": "Schlafzimmer",
            "status": "green",
            "recommendation": "Keine Aktion nötig",
            "recommendation_key": "no_action",
            "display_mode": "room_air",
            "safety_lock": False,
        },
    )

    result = api_module._apply_hardware_report(
        hass,
        entry,
        station,
        {
            "hardware_id": "B0:CB:D8:09:4C:C8",
            "master_id": "B0:CB:D8:09:AB:1C",
            "co2": 1234.0,
            "temperature": 21.56,
            "humidity": 47.25,
            "round_id": 17,
            "request_id": 9,
        },
    )

    assert reported and reported[0]["co2"] == 1234.0
    assert result["status"] == "green"
    assert result["recommendation_key"] == "no_action"
    assert result["round_id"] == 17
    assert result["request_id"] == 9
    assert result["master_id"] == "DIRECT:B0:CB:D8:09:AB:1C"
    assert result["master_location_mode"] == "local"


@pytest.mark.parametrize("location_mode", ["local", "remote"])
def test_native_hardware_report_location_comes_from_configured_master(
    monkeypatch, location_mode
) -> None:
    from custom_components.lueftungsberater import api as api_module

    hass, entry, _master, station = _native_report_fixture(location_mode)
    monkeypatch.setattr(api_module, "report_station", lambda *_args: None)
    monkeypatch.setattr(
        api_module,
        "_hardware_display_payload",
        lambda *_args: {
            "room_name": "Schlafzimmer",
            "status": "yellow",
            "recommendation": "Beobachten",
            "recommendation_key": "unknown",
            "display_mode": "room_air",
            "safety_lock": False,
        },
    )

    result = api_module._apply_hardware_report(
        hass,
        entry,
        station,
        {
            "hardware_id": "B0:CB:D8:09:4C:C8",
            "master_id": "B0:CB:D8:09:AB:1C",
            "round_id": 1,
            "request_id": 2,
        },
    )
    assert result["master_location_mode"] == location_mode


def test_native_hardware_report_rejects_wrong_master_before_storage(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import HARDWARE_LOCATION_REMOTE

    hass, entry, _master, station = _native_report_fixture(HARDWARE_LOCATION_REMOTE)
    reported = []
    monkeypatch.setattr(
        api_module, "report_station", lambda *_args: reported.append(True)
    )

    with pytest.raises(api_module._HardwareReportRejected, match="does not match"):
        api_module._apply_hardware_report(
            hass,
            entry,
            station,
            {
                "hardware_id": "B0:CB:D8:09:4C:C8",
                "master_id": "AA:BB:CC:DD:EE:FF",
                "round_id": 1,
                "request_id": 1,
            },
        )
    assert reported == []


def test_native_hardware_report_target_rejects_duplicate_hardware_id(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.exceptions import ServiceValidationError
    station = SimpleNamespace(subentry_id="node", data={})
    entries = [
        SimpleNamespace(entry_id="one", state=ConfigEntryState.LOADED, data={}, subentries={}),
        SimpleNamespace(entry_id="two", state=ConfigEntryState.LOADED, data={}, subentries={}),
    ]
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda _domain: entries)
    )
    monkeypatch.setattr(api_module, "station_by_hardware_id", lambda *_args: station)

    with pytest.raises(ServiceValidationError, match="more than one"):
        api_module._hardware_report_action_target(hass, "AA:BB")



def test_native_hardware_report_auth_rejects_other_master_credential() -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import HARDWARE_LOCATION_LOCAL

    _hass, entry, _master, station = _native_report_fixture(HARDWARE_LOCATION_LOCAL)

    assert (
        api_module._hardware_report_native_auth_error(
            entry,
            station,
            "B0:CB:D8:09:AB:1C",
            "fixture-master-secret-0123456789abcdef",
        )
        is None
    )
    assert (
        api_module._hardware_report_native_auth_error(
            entry,
            station,
            "B0:CB:D8:09:AB:1C",
            "different-master-secret-0123456789abcdef",
        )
        == "master_auth_failed"
    )


@pytest.mark.asyncio
async def test_native_hardware_report_rejects_bad_secret_before_storage(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import HARDWARE_LOCATION_LOCAL
    from homeassistant.exceptions import ServiceValidationError

    hass, _entry, _master, _station = _native_report_fixture(HARDWARE_LOCATION_LOCAL)
    reported = []
    monkeypatch.setattr(
        api_module,
        "report_station",
        lambda *_args: reported.append(True),
    )
    call = SimpleNamespace(
        hass=hass,
        data={
            "hardware_id": "B0:CB:D8:09:4C:C8",
            "master_id": "B0:CB:D8:09:AB:1C",
            "master_secret": "different-master-secret-0123456789abcdef",
            "co2": 1450.0,
            "round_id": 9,
            "request_id": 3,
        },
    )

    with pytest.raises(ServiceValidationError, match="credential is invalid"):
        await api_module._async_hardware_report_action(call)
    assert reported == []


def test_hardware_action_registration_is_once_and_requires_response(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import DOMAIN
    from homeassistant.core import SupportsResponse

    registrations = []
    hass = SimpleNamespace(
        data={},
        http=SimpleNamespace(register_view=lambda *_args: None),
        services=SimpleNamespace(
            async_register=lambda *args, **kwargs: registrations.append((args, kwargs))
        ),
    )
    monkeypatch.setattr(api_module.websocket_api, "async_register_command", lambda *_args: None)

    api_module.async_register_hardware_service(hass)
    api_module.async_register_hardware_service(hass)
    api_module.async_register_api(hass)

    assert len(registrations) == 1
    args, kwargs = registrations[0]
    assert args[0] == DOMAIN
    assert args[1] == api_module.SERVICE_HARDWARE_REPORT
    assert kwargs["supports_response"] is SupportsResponse.ONLY

def test_native_hardware_report_schema_accepts_esphome_string_payloads() -> None:
    from custom_components.lueftungsberater.api import HARDWARE_REPORT_ACTION_SCHEMA

    data = HARDWARE_REPORT_ACTION_SCHEMA(
        {
            "hardware_id": "B0:CB:D8:09:4C:C8",
            "master_id": "B0:CB:D8:09:AB:1C",
            "master_secret": "fixture-master-secret-0123456789abcdef",
            "co2": "1234",
            "temperature": "21.56",
            "humidity": "47.25",
            "rssi": "-54",
            "round_id": "6",
            "request_id": "6",
            "online": "true",
        }
    )

    assert data["co2"] == 1234.0
    assert data["temperature"] == 21.56
    assert data["humidity"] == 47.25
    assert data["rssi"] == -54
    assert data["round_id"] == 6
    assert data["request_id"] == 6
    assert data["online"] is True

def test_native_hardware_report_schema_rejects_out_of_range_correlation_ids() -> None:
    import voluptuous as vol

    from custom_components.lueftungsberater.api import HARDWARE_REPORT_ACTION_SCHEMA

    base = {
        "hardware_id": "B0:CB:D8:09:4C:C8",
        "master_id": "B0:CB:D8:09:AB:1C",
        "master_secret": "fixture-master-secret-0123456789abcdef",
        "round_id": 1,
        "request_id": 1,
    }
    with pytest.raises(vol.Invalid):
        HARDWARE_REPORT_ACTION_SCHEMA({**base, "round_id": -1})
    with pytest.raises(vol.Invalid):
        HARDWARE_REPORT_ACTION_SCHEMA({**base, "request_id": 0x1_0000_0000})



@pytest.mark.asyncio
async def test_integration_setup_registers_hardware_service(monkeypatch) -> None:
    import custom_components.lueftungsberater as integration

    hass = SimpleNamespace()
    registered = []
    monkeypatch.setattr(
        integration,
        "async_register_hardware_service",
        lambda value: registered.append(value),
    )

    assert await integration.async_setup(hass, {}) is True
    assert registered == [hass]


@pytest.mark.asyncio
async def test_native_hardware_report_action_resolves_node_and_returns_display(monkeypatch) -> None:
    from custom_components.lueftungsberater import api as api_module
    from custom_components.lueftungsberater.const import HARDWARE_LOCATION_LOCAL

    hass, _entry, _master, _station = _native_report_fixture(HARDWARE_LOCATION_LOCAL)
    reported = []
    monkeypatch.setattr(
        api_module,
        "report_station",
        lambda _hass, _entry, _station, payload: reported.append(dict(payload)),
    )
    monkeypatch.setattr(
        api_module,
        "_hardware_display_payload",
        lambda *_args: {
            "room_name": "Schlafzimmer",
            "status": "orange",
            "recommendation": "Lüften ist sinnvoll",
            "recommendation_key": "open_now",
            "display_mode": "room_air",
            "safety_lock": False,
        },
    )
    call = SimpleNamespace(
        hass=hass,
        data={
            "hardware_id": "B0:CB:D8:09:4C:C8",
            "master_id": "B0:CB:D8:09:AB:1C",
            "master_secret": "fixture-master-secret-0123456789abcdef",
            "co2": 1450.0,
            "temperature": 22.1,
            "humidity": 51.0,
            "round_id": 9,
            "request_id": 3,
        },
    )

    result = await api_module._async_hardware_report_action(call)

    assert reported and reported[0]["co2"] == 1450.0
    assert result["status"] == "orange"
    assert result["recommendation_key"] == "open_now"
    assert result["round_id"] == 9
    assert result["request_id"] == 3

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

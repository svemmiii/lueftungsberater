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

from types import SimpleNamespace

import pytest
from homeassistant.components.http import KEY_HASS, KEY_HASS_USER

from custom_components.lueftungsberater.api import (
    REMOTE_ATTRIBUTE_KEYS,
    LueftungsberaterSnapshotView,
    _export_attributes,
)


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
    assert "forecast_data_status" in REMOTE_ATTRIBUTE_KEYS


@pytest.mark.asyncio
async def test_snapshot_http_api_rejects_non_admin_user() -> None:
    class Request(dict):
        remote = "100.64.0.10"
        query = {}

    request = Request({
        KEY_HASS: SimpleNamespace(),
        KEY_HASS_USER: SimpleNamespace(is_admin=False),
    })
    request.app = request
    response = await LueftungsberaterSnapshotView().get(request)
    assert response.status == 403

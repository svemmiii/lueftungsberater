from custom_components.lueftungsberater.api import REMOTE_ATTRIBUTE_KEYS, _export_attributes


def test_remote_export_does_not_include_local_entity_ids_or_original_warning() -> None:
    attrs = _export_attributes(
        {
            "room_name": "Küche",
            "status": "green",
            "recommendation": "Jetzt lüften",
            "temperature_inside": 23.0,
            "source_temperature_inside": "sensor.kueche_temperatur",
            "source_absolute_humidity_outside": "sensor.kueche_absolute_feuchte_aussen",
            "original_warning_text": "provider payload",
        },
        "°C",
        remote_export=True,
    )

    assert attrs["room_name"] == "Küche"
    assert attrs["temperature_inside"] == 23.0
    assert "source_temperature_inside" not in attrs
    assert "source_absolute_humidity_outside" not in attrs
    assert "original_warning_text" not in attrs


def test_remote_allow_list_stays_current_only() -> None:
    assert "last_confirmed_airing" not in REMOTE_ATTRIBUTE_KEYS
    assert "source_window_entities" not in REMOTE_ATTRIBUTE_KEYS
    assert "original_warning_text" not in REMOTE_ATTRIBUTE_KEYS

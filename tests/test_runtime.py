from homeassistant.const import UnitOfTemperature

from custom_components.lueftungsberater.runtime import _to_celsius


def test_fahrenheit_is_normalized_to_celsius():
    assert round(_to_celsius(77, UnitOfTemperature.FAHRENHEIT), 2) == 25.0


def test_celsius_stays_celsius():
    assert _to_celsius(23.5, UnitOfTemperature.CELSIUS) == 23.5


def test_warning_source_none_is_not_configured():
    from types import SimpleNamespace
    from custom_components.lueftungsberater.runtime import warning_source_configured

    assert warning_source_configured(SimpleNamespace(data={"warning_source": "none"})) is False
    assert warning_source_configured(SimpleNamespace(data={"warning_source": "abc123"})) is True


def test_plausibility_filters_keep_extreme_but_possible_values():
    from custom_components.lueftungsberater.runtime import (
        _plausible_co2,
        _plausible_humidity,
        _plausible_temperature,
    )

    assert _plausible_temperature(60) == 60
    assert _plausible_humidity(102) == 102
    assert _plausible_co2(7000) == 7000
    assert _plausible_co2(0) is None
    assert _plausible_co2(249) is None
    assert _plausible_co2(250) == 250
    assert _plausible_humidity(150) is None
    assert _plausible_co2(1_100_000) is None


async def test_compact_air_quality_store_migrates_v0623_points(hass, enable_custom_integrations):
    """Updating to v0.6.24 keeps learned local air context without raw-history growth."""
    from datetime import timedelta
    from types import SimpleNamespace

    from custom_components.lueftungsberater.air_quality import OutdoorAirQualityTracker
    from homeassistant.util import dt as dt_util

    now = dt_util.utcnow()
    legacy = {
        "buckets": {
            "50.75,7.00": {
                "pm2_5": [
                    [(now - timedelta(hours=2)).isoformat(), 10.0],
                    [(now - timedelta(hours=1)).isoformat(), 12.0],
                    [now.isoformat(), 11.0],
                ]
            }
        }
    }

    class FakeStore:
        async def async_load(self):
            return legacy

        async def async_save(self, _data):
            return None

    entry = SimpleNamespace(entry_id="advisor-air", data={})
    tracker = OutdoorAirQualityTracker(hass, entry)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    stats = tracker._buckets["50.75,7.00"]["pm2_5"]
    assert stats["count"] == 3
    assert stats["baseline"] == 11.0
    assert isinstance(tracker._serialize()["buckets"]["50.75,7.00"]["pm2_5"], dict)


def test_unknown_temperature_unit_is_not_assumed_to_be_celsius():
    assert _to_celsius(75, "definitely-not-a-temperature-unit") is None


def test_missing_comfort_data_preserves_hard_weather_safety_result():
    from custom_components.lueftungsberater.runtime import _incomplete_data_safety_result

    result = _incomplete_data_safety_result(
        {"window_open": False, "co2_ppm": 1200.0},
        {
            "nina_status": "none",
            "nina_reason_key": None,
            "nina_reason_args": {},
            "nina_original_reason": None,
            "weather_danger": True,
            "weather_reason_key": "weather_lightning_danger",
            "weather_reason_args": {},
            "weather_original_reason": "Amtliche Gewitterwarnung",
        },
    )

    assert result is not None
    assert result.color == "red"
    assert result.safety_lock is True
    assert result.recommendation_key == "keep_closed"
    assert result.reason_key == "weather_lightning_danger"


def test_warning_context_never_uses_weaker_caution_reason_for_hard_danger(hass):
    from types import SimpleNamespace
    from custom_components.lueftungsberater.providers import WeatherAssessment, WarningAssessment
    from custom_components.lueftungsberater.runtime import _warning_context

    entry = SimpleNamespace(data={"warning_source": "provider-entry"})
    weather = WeatherAssessment(
        weather_danger=True,
        weather_reason_key="weather_lightning_danger",
        weather_original_reason="Gewitter / Blitz",
    )
    warnings = WarningAssessment(
        weather_caution=True,
        weather_reason_key="weather_wind_caution",
        weather_original_reason="Starker Wind",
    )

    context = _warning_context(hass, entry, weather, warnings)
    assert context["weather_danger"] is True
    assert context["weather_caution"] is False
    assert context["weather_reason_key"] == "weather_lightning_danger"
    assert context["weather_original_reason"] == "Gewitter / Blitz"


def test_build_snapshot_keeps_hard_warning_when_humidity_sensor_is_unavailable(hass):
    from types import SimpleNamespace
    from homeassistant.const import UnitOfTemperature
    from custom_components.lueftungsberater.const import (
        CONF_INDOOR_HUMIDITY,
        CONF_INDOOR_TEMP,
        CONF_TARGET_TEMP,
        CONF_WARNING_SOURCE,
    )
    from custom_components.lueftungsberater.providers import WeatherAssessment, WarningAssessment
    from custom_components.lueftungsberater.runtime import build_room_snapshot

    hass.states.async_set(
        "sensor.room_temp", 21.0, {"unit_of_measurement": UnitOfTemperature.CELSIUS}
    )
    hass.states.async_set("sensor.room_humidity", "unavailable")
    entry = SimpleNamespace(
        entry_id="entry",
        data={CONF_WARNING_SOURCE: "provider-entry"},
    )
    subentry = SimpleNamespace(
        subentry_id="room",
        title="Raum",
        data={
            CONF_INDOOR_TEMP: "sensor.room_temp",
            CONF_INDOOR_HUMIDITY: "sensor.room_humidity",
            CONF_TARGET_TEMP: 21.0,
        },
    )
    weather = WeatherAssessment(
        temperature=20.0,
        humidity=50.0,
        weather_danger=True,
        weather_reason_key="weather_lightning_danger",
        weather_original_reason="Gewitter / Blitz",
    )

    snapshot = build_room_snapshot(
        hass, entry, subentry, weather=weather, warnings=WarningAssessment()
    )

    assert snapshot.values["humidity_inside"] is None
    assert snapshot.result is not None
    assert snapshot.result.safety_lock is True
    assert snapshot.result.color == "red"
    assert snapshot.result.reason_key == "weather_lightning_danger"


async def test_last_entry_removal_deletes_auto_lovelace_resource(hass):
    from types import SimpleNamespace
    from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
    from custom_components.lueftungsberater.__init__ import (
        _async_remove_frontend_resource_if_unused,
    )

    class Resources:
        def __init__(self):
            self.deleted = []

        async def async_get_info(self):
            return {}

        def async_items(self):
            return [
                {
                    "id": "lb-card",
                    "url": "/lueftungsberater/frontend/lueftungsberater-card.js?v=0.9.4",
                    "type": "module",
                },
                {"id": "other", "url": "/local/other.js", "type": "module"},
            ]

        async def async_delete_item(self, item_id):
            self.deleted.append(item_id)

    resources = Resources()
    hass.data[LOVELACE_DATA] = SimpleNamespace(
        resource_mode=MODE_STORAGE,
        resources=resources,
    )

    await _async_remove_frontend_resource_if_unused(hass)
    assert resources.deleted == ["lb-card"]


def test_room_source_entities_leave_window_contacts_to_airing_tracker():
    """Coordinator must not race the tracker on a close event."""
    from types import SimpleNamespace

    from custom_components.lueftungsberater.const import (
        CONF_CLIMATE,
        CONF_CO2,
        CONF_INDOOR_HUMIDITY,
        CONF_INDOOR_TEMP,
        CONF_SURFACE_TEMP,
        CONF_WINDOWS,
    )
    from custom_components.lueftungsberater.runtime import room_source_entities

    room = SimpleNamespace(
        data={
            CONF_INDOOR_TEMP: "sensor.room_temp",
            CONF_INDOOR_HUMIDITY: "sensor.room_humidity",
            CONF_CO2: "sensor.room_co2",
            CONF_CLIMATE: "climate.room",
            CONF_SURFACE_TEMP: "sensor.wall_temp",
            CONF_WINDOWS: ["binary_sensor.window_a", "binary_sensor.window_b"],
        }
    )
    entry = SimpleNamespace(data={})

    entities = room_source_entities(None, entry, room)

    assert "sensor.room_temp" in entities
    assert "sensor.room_humidity" in entities
    assert "sensor.room_co2" in entities
    assert "climate.room" in entities
    assert "sensor.wall_temp" in entities
    assert "binary_sensor.window_a" not in entities
    assert "binary_sensor.window_b" not in entities

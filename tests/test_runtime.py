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

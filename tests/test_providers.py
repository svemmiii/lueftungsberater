from types import SimpleNamespace
from unittest.mock import patch

from custom_components.lueftungsberater.providers import weather_assessment


class FakeState:
    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class FakeStates:
    def __init__(self, values):
        self._values = values

    def get(self, entity_id):
        return self._values.get(entity_id)


class FakeHass:
    def __init__(self, values):
        self.states = FakeStates(values)


WEATHER = "weather.home"
TEMP = "sensor.outdoor_temperature"
HUM = "sensor.outdoor_humidity"


def assess(values, *, temp=TEMP, humidity=HUM):
    entry = SimpleNamespace(
        data={
            "weather_entity": WEATHER,
            "manual_outdoor": {
                "outdoor_temperature": temp,
                "outdoor_humidity": humidity,
            },
        }
    )
    hass = FakeHass(values)
    with (
        patch(
            "custom_components.lueftungsberater.providers._provider_domain_for_entity",
            return_value="test_weather",
        ),
        patch(
            "custom_components.lueftungsberater.providers._discover_dwd_radar_entities",
            return_value=(None, None, set()),
        ),
    ):
        return weather_assessment(hass, entry)


def test_local_outdoor_sensors_are_preferred():
    result = assess(
        {
            WEATHER: FakeState("sunny", {"temperature": 18, "humidity": 70}),
            TEMP: FakeState("20.5"),
            HUM: FakeState("61"),
        }
    )
    assert result.temperature == 20.5
    assert result.humidity == 61
    assert result.source_temperature == TEMP
    assert result.source_humidity == HUM
    assert result.temperature_source_kind == "local_sensor"
    assert result.humidity_source_kind == "local_sensor"


def test_temperature_can_fallback_independently():
    result = assess(
        {
            WEATHER: FakeState("cloudy", {"temperature": 17.2, "humidity": 74}),
            TEMP: FakeState("unavailable"),
            HUM: FakeState("62"),
        }
    )
    assert result.temperature == 17.2
    assert result.humidity == 62
    assert result.source_temperature == WEATHER
    assert result.source_humidity == HUM
    assert result.temperature_source_kind == "weather_fallback"
    assert result.humidity_source_kind == "local_sensor"


def test_humidity_can_fallback_independently():
    result = assess(
        {
            WEATHER: FakeState("rainy", {"temperature": 16.8, "humidity": 91}),
            TEMP: FakeState("18.1"),
            HUM: FakeState("unknown"),
        }
    )
    assert result.temperature == 18.1
    assert result.humidity == 91
    assert result.source_temperature == TEMP
    assert result.source_humidity == WEATHER
    assert result.temperature_source_kind == "local_sensor"
    assert result.humidity_source_kind == "weather_fallback"


def test_weather_service_is_used_when_no_local_sensors_are_configured():
    result = assess(
        {
            WEATHER: FakeState("sunny", {"temperature": 19.0, "humidity": 55}),
        },
        temp=None,
        humidity=None,
    )
    assert result.temperature == 19.0
    assert result.humidity == 55
    assert result.temperature_source_kind == "weather_service"
    assert result.humidity_source_kind == "weather_service"


def test_missing_weather_humidity_does_not_break_valid_local_temperature():
    result = assess(
        {
            WEATHER: FakeState("cloudy", {"temperature": 17.0}),
            TEMP: FakeState("18.0"),
            HUM: FakeState("unavailable"),
        }
    )
    assert result.temperature == 18.0
    assert result.humidity is None
    assert result.temperature_source_kind == "local_sensor"
    assert result.humidity_source_kind == "unavailable"


def test_unavailable_weather_is_not_used_as_fallback():
    result = assess(
        {
            WEATHER: FakeState("unavailable", {"temperature": 17.0, "humidity": 80}),
            TEMP: FakeState("unavailable"),
            HUM: FakeState("unknown"),
        }
    )
    assert result.temperature is None
    assert result.humidity is None
    assert result.temperature_source_kind == "unavailable"
    assert result.humidity_source_kind == "unavailable"


def test_pouring_is_rain_but_not_automatically_weather_danger():
    result = assess(
        {
            WEATHER: FakeState("pouring", {"temperature": 16.0, "humidity": 95}),
        },
        temp=None,
        humidity=None,
    )
    assert result.rain_now is True
    assert result.weather_danger is False
    assert result.weather_caution is False
    assert result.weather_reason_key == "weather_heavy_rain_current"


def test_dwd_level_2_warning_is_caution_not_red_danger():
    from custom_components.lueftungsberater.providers import _evaluate_dwd_warning_entities

    entity = "sensor.dwd_weather_warnings_current_warning_level"
    hass = FakeHass(
        {
            entity: FakeState(
                "2",
                {
                    "warning_count": 1,
                    "warning_1_name": "STARKREGEN",
                    "warning_1_level": 2,
                    "warning_1_headline": "Amtliche Warnung vor Starkregen",
                },
            )
        }
    )
    result = _evaluate_dwd_warning_entities(hass, [entity])
    assert result.weather_caution is True
    assert result.weather_danger is False
    assert result.weather_reason_key == "weather_heavy_rain_caution"


def test_dwd_level_3_warning_is_red_danger():
    from custom_components.lueftungsberater.providers import _evaluate_dwd_warning_entities

    entity = "sensor.dwd_weather_warnings_current_warning_level"
    hass = FakeHass(
        {
            entity: FakeState(
                "3",
                {
                    "warning_count": 1,
                    "warning_1_name": "HEFTIGER STARKREGEN",
                    "warning_1_level": 3,
                    "warning_1_headline": "Amtliche Unwetterwarnung vor heftigem Starkregen",
                },
            )
        }
    )
    result = _evaluate_dwd_warning_entities(hass, [entity])
    assert result.weather_danger is True
    assert result.weather_caution is False
    assert result.weather_reason_key == "weather_heavy_rain_danger"



def test_dwd_uses_level_of_relevant_warning_not_sensor_maximum():
    from custom_components.lueftungsberater.providers import _evaluate_dwd_warning_entities

    entity = "sensor.dwd_weather_warnings_current_warning_level"
    hass = FakeHass(
        {
            entity: FakeState(
                "3",
                {
                    "warning_count": 2,
                    "warning_1_name": "HITZE",
                    "warning_1_level": 3,
                    "warning_1_headline": "Amtliche Unwetterwarnung vor Hitze",
                    "warning_2_name": "STARKREGEN",
                    "warning_2_level": 2,
                    "warning_2_headline": "Amtliche Warnung vor Starkregen",
                },
            )
        }
    )
    result = _evaluate_dwd_warning_entities(hass, [entity])
    assert result.weather_caution is True
    assert result.weather_danger is False
    assert result.weather_reason_key == "weather_heavy_rain_caution"

def test_generic_moderate_weather_warning_is_caution():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    entity = "binary_sensor.warning"
    hass = FakeHass(
        {
            entity: FakeState(
                "on",
                {
                    "headline": "Warnung vor Starkregen",
                    "severity": "Moderate",
                },
            )
        }
    )
    result = _evaluate_nina_like_entities(hass, [entity])
    assert result.weather_caution is True
    assert result.weather_danger is False
    assert result.weather_reason_key == "weather_heavy_rain_caution"


def test_generic_severe_weather_warning_is_danger():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    entity = "binary_sensor.warning"
    hass = FakeHass(
        {
            entity: FakeState(
                "on",
                {
                    "headline": "Unwetterwarnung vor heftigem Starkregen",
                    "severity": "Severe",
                },
            )
        }
    )
    result = _evaluate_nina_like_entities(hass, [entity])
    assert result.weather_danger is True
    assert result.weather_caution is False
    assert result.weather_reason_key == "weather_heavy_rain_danger"


def test_nina_new_detail_sensors_are_used_when_legacy_attributes_are_missing():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    warning = "binary_sensor.nina_warning_1"
    headline = "sensor.nina_warning_1_headline"
    severity = "sensor.nina_warning_1_severity"
    hass = FakeHass(
        {
            warning: FakeState("on", {}),
            headline: FakeState("Amtliche Warnung vor Starkregen"),
            severity: FakeState("moderate"),
        }
    )

    registry_entries = {
        warning: SimpleNamespace(unique_id="09123-1"),
        headline: SimpleNamespace(unique_id="09123-1-headline"),
        severity: SimpleNamespace(unique_id="09123-1-severity"),
    }
    registry = SimpleNamespace(async_get=lambda entity_id: registry_entries.get(entity_id))

    with patch("custom_components.lueftungsberater.providers.er.async_get", return_value=registry):
        result = _evaluate_nina_like_entities(hass, [warning, headline, severity])

    assert result.weather_caution is True
    assert result.weather_danger is False
    assert result.weather_reason_key == "weather_heavy_rain_caution"


def test_nina_new_severity_sensor_can_mark_warning_as_danger():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    warning = "binary_sensor.nina_warning_1"
    headline = "sensor.nina_warning_1_headline"
    severity = "sensor.nina_warning_1_severity"
    hass = FakeHass(
        {
            warning: FakeState("on", {}),
            headline: FakeState("Amtliche Unwetterwarnung vor heftigem Starkregen"),
            severity: FakeState("severe"),
        }
    )

    registry_entries = {
        warning: SimpleNamespace(unique_id="09123-1"),
        headline: SimpleNamespace(unique_id="09123-1-headline"),
        severity: SimpleNamespace(unique_id="09123-1-severity"),
    }
    registry = SimpleNamespace(async_get=lambda entity_id: registry_entries.get(entity_id))

    with patch("custom_components.lueftungsberater.providers.er.async_get", return_value=registry):
        result = _evaluate_nina_like_entities(hass, [warning, headline, severity])

    assert result.weather_danger is True
    assert result.weather_caution is False
    assert result.weather_reason_key == "weather_heavy_rain_danger"

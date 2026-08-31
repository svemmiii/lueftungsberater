from datetime import datetime, timedelta, timezone
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
        patch(
            "custom_components.lueftungsberater.providers._discover_air_quality",
            return_value=("unknown", None, None, {}, set()),
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


def test_short_term_forecast_detects_upcoming_thunderstorm():
    from custom_components.lueftungsberater.providers import _short_term_forecast_outlook

    now = datetime(2026, 8, 31, 16, 50, tzinfo=timezone.utc)
    change, kind, minutes, condition = _short_term_forecast_outlook(
        now=now,
        current_condition="cloudy",
        current_wind_kmh=10,
        current_gust_kmh=20,
        rain_now=False,
        hourly_forecast=[
            {
                "datetime": now + timedelta(minutes=10),
                "temperature": 21,
                "condition": "lightning-rainy",
            }
        ],
    )
    assert change == "worsening"
    assert kind == "thunderstorm"
    assert round(minutes or 0) == 10
    assert condition == "lightning-rainy"


def test_short_term_forecast_detects_weather_improving_again():
    from custom_components.lueftungsberater.providers import _short_term_forecast_outlook

    now = datetime(2026, 8, 31, 16, 50, tzinfo=timezone.utc)
    change, kind, minutes, _condition = _short_term_forecast_outlook(
        now=now,
        current_condition="lightning-rainy",
        current_wind_kmh=20,
        current_gust_kmh=30,
        rain_now=True,
        hourly_forecast=[
            {
                "datetime": now + timedelta(minutes=10),
                "temperature": 20,
                "condition": "cloudy",
            }
        ],
    )
    assert change == "improving"
    assert kind == "thunderstorm"
    assert round(minutes or 0) == 10


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

def test_generic_warning_is_not_reinterpreted_by_event_type_or_severity():
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
    assert result.weather_danger is False
    assert result.weather_caution is False
    assert result.nina_status == "none"


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

    assert result.weather_caution is False
    assert result.weather_danger is False
    assert result.nina_status == "none"


def test_nina_new_severity_sensor_does_not_override_missing_protection_instruction():
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

    assert result.weather_danger is False
    assert result.weather_caution is False
    assert result.nina_status == "none"



def test_air_warning_with_explicit_no_danger_is_none_without_close_instruction():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Brandentwicklung",
            "Es besteht keine Gefahr für die Bevölkerung durch den Rauch.",
            "Bitte informieren Sie sich weiter.",
            "Moderate",
        )
        == "none"
    )


def test_warning_without_air_protection_instruction_is_ignored_but_close_instruction_locks():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Rauchentwicklung",
            "Rauch zieht über das Gebiet.",
            "Meiden Sie den Bereich.",
            "Moderate",
        )
        == "none"
    )
    assert (
        _evaluate_air_warning(
            "Gefahrstoffaustritt",
            "Gefahrstoffe befinden sich in der Außenluft.",
            "Fenster und Türen geschlossen halten.",
            "Moderate",
        )
        == "danger"
    )



def test_precautionary_close_windows_instruction_is_authoritative():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Chemischer Unfall - mögliche Gefahrstofffreisetzung",
            "Eine Freisetzung kann derzeit nicht ausgeschlossen werden.",
            "Schließen Sie vorsorglich Fenster und Türen. Schalten Sie Lüftungs- und Klimaanlagen ab.",
            "Moderate",
        )
        == "danger"
    )


def test_nina_like_close_instruction_marks_official_lock():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    entity = "binary_sensor.warning"
    hass = FakeHass(
        {
            entity: FakeState(
                "on",
                {
                    "headline": "Evakuierungsmaßnahme",
                    "recommended_actions": "Fenster und Türen geschlossen halten.",
                    "severity": "Minor",
                },
            )
        }
    )
    result = _evaluate_nina_like_entities(hass, [entity])
    assert result.nina_status == "danger"
    assert result.official_close_instruction is True


def test_all_clear_is_context_not_a_hard_lock():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Entwarnung",
            "Die Warnung wird aufgehoben.",
            "",
            "Minor",
        )
        == "clear"
    )


def test_negated_all_clear_does_not_clear_warning():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Lageupdate",
            "Eine Entwarnung liegt noch nicht vor.",
            "Fenster und Türen geschlossen halten.",
            "Moderate",
        )
        == "danger"
    )


def test_dwd_explicit_close_instruction_overrides_warning_level():
    from custom_components.lueftungsberater.providers import _evaluate_dwd_warning_entities

    entity = "sensor.dwd_weather_warnings_current_warning_level"
    hass = FakeHass(
        {
            entity: FakeState(
                "1",
                {
                    "warning_count": 1,
                    "warning_1_name": "GEWITTER",
                    "warning_1_level": 1,
                    "warning_1_headline": "Amtliche Warnung vor Gewitter",
                    "warning_1_instruction": "Fenster und Türen geschlossen halten.",
                },
            )
        }
    )
    result = _evaluate_dwd_warning_entities(hass, [entity])
    assert result.weather_danger is True
    assert result.weather_reason_key == "official_close_instruction"
    assert result.official_close_instruction is True

def test_uba_air_quality_classes_use_worst_available_pollutant():
    from custom_components.lueftungsberater.providers import (
        AIR_QUALITY_RANK,
        _air_quality_class,
    )

    classes = {
        "pm2_5": _air_quality_class("pm2_5", 35),
        "o3": _air_quality_class("o3", 80),
        "no2": _air_quality_class("no2", 20),
    }
    worst = max(classes, key=lambda key: AIR_QUALITY_RANK[classes[key]])
    assert classes["pm2_5"] == "poor"
    assert classes["o3"] == "moderate"
    assert classes["no2"] == "good"
    assert worst == "pm2_5"


def test_lone_zero_with_unavailable_air_quality_siblings_is_ignored():
    from custom_components.lueftungsberater.providers import _discover_air_quality

    weather = "weather.bornheim"
    pm25 = "sensor.bornheim_luftqualitat_pm2_5"
    pm10 = "sensor.bornheim_luftqualitat_pm10"
    ozone = "sensor.bornheim_luftqualitat_ozon"
    values = {
        pm25: FakeState("0", {"unit_of_measurement": "µg/m³"}),
        pm10: FakeState("unknown", {"unit_of_measurement": "µg/m³"}),
        ozone: FakeState("unknown", {"unit_of_measurement": "µg/m³"}),
    }
    hass = FakeHass(values)
    registry_items = {
        pm25: SimpleNamespace(original_name="Luftqualität PM2.5"),
        pm10: SimpleNamespace(original_name="Luftqualität PM10"),
        ozone: SimpleNamespace(original_name="Luftqualität Ozon"),
    }
    registry = SimpleNamespace(async_get=lambda entity_id: registry_items.get(entity_id))
    with (
        patch(
            "custom_components.lueftungsberater.providers._registry_entry",
            return_value=SimpleNamespace(config_entry_id="weather-entry"),
        ),
        patch(
            "custom_components.lueftungsberater.providers._config_entry_entities",
            return_value=[pm25, pm10, ozone],
        ),
        patch(
            "custom_components.lueftungsberater.providers.er.async_get",
            return_value=registry,
        ),
    ):
        quality, pollutant, value, found, used = _discover_air_quality(hass, weather)

    assert quality == "unknown"
    assert pollutant is None and value is None and found == {}
    assert used == {pm25, pm10, ozone}


def test_wind_thresholds_split_orange_disadvantage_from_red_hazard():
    ordinary = assess(
        {
            WEATHER: FakeState(
                "sunny",
                {
                    "temperature": 18,
                    "humidity": 60,
                    "wind_speed": 42,
                    "wind_gust_speed": 55,
                    "wind_speed_unit": "km/h",
                },
            )
        },
        temp=None,
        humidity=None,
    )
    disadvantage = assess(
        {
            WEATHER: FakeState(
                "sunny",
                {
                    "temperature": 18,
                    "humidity": 60,
                    "wind_speed": 50,
                    "wind_gust_speed": 65,
                    "wind_speed_unit": "km/h",
                },
            )
        },
        temp=None,
        humidity=None,
    )
    hazard = assess(
        {
            WEATHER: FakeState(
                "sunny",
                {
                    "temperature": 18,
                    "humidity": 60,
                    "wind_speed": 75,
                    "wind_gust_speed": 105,
                    "wind_speed_unit": "km/h",
                },
            )
        },
        temp=None,
        humidity=None,
    )
    assert ordinary.weather_caution is False and ordinary.weather_danger is False
    assert disadvantage.weather_caution is True and disadvantage.weather_danger is False
    assert hazard.weather_danger is True


async def test_nina_get_details_is_cached_by_warning_id(hass, enable_custom_integrations):
    """Full NINA actions are fetched once and reused until the warning id changes."""
    from unittest.mock import AsyncMock, patch

    from homeassistant.core import SupportsResponse
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.lueftungsberater.const import CONF_WARNING_SOURCE
    from custom_components.lueftungsberater.providers import (
        _evaluate_nina_like_entities,
        async_refresh_nina_details,
    )

    nina = MockConfigEntry(domain="nina", title="NINA", data={})
    nina.add_to_hass(hass)
    advisor = SimpleNamespace(entry_id="advisor-entry", data={CONF_WARNING_SOURCE: nina.entry_id})
    warning = "binary_sensor.nina_warning_1"
    hass.states.async_set(warning, "on", {"id": "warning-123"})

    response = {
        warning: {
            "headline": "Gefahrstoffaustritt",
            "description": "Gefahrstoffe befinden sich in der Außenluft.",
            "recommended_actions": "Fenster und Türen geschlossen halten.",
            "severity": "Moderate",
            "id": "warning-123",
        }
    }
    service_handler = AsyncMock(return_value=response)
    hass.services.async_register(
        "nina",
        "get_details",
        service_handler,
        supports_response=SupportsResponse.ONLY,
    )

    try:
        with patch(
            "custom_components.lueftungsberater.providers._config_entry_entities",
            return_value=[warning],
        ):
            await async_refresh_nina_details(hass, advisor)
            await async_refresh_nina_details(hass, advisor)
            result = _evaluate_nina_like_entities(hass, advisor, [warning])
    finally:
        hass.services.async_remove("nina", "get_details")

    assert service_handler.await_count == 1
    assert result.nina_status == "danger"


def test_qualified_all_clear_phrases_are_not_full_clear():
    from custom_components.lueftungsberater.providers import _is_clear_warning

    for text in (
        "Bedingte Entwarnung für das betroffene Gebiet.",
        "Teilentwarnung: Die Lage wird weiter beobachtet.",
        "Teilweise Entwarnung, einzelne Maßnahmen bleiben bestehen.",
        "Entwarnung mit Einschränkungen.",
    ):
        assert _is_clear_warning(text) is False


def test_explicit_close_instruction_wins_even_if_payload_says_entwarnung():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Entwarnung",
            "Die Lage hat sich verbessert.",
            "Fenster und Türen weiterhin geschlossen halten.",
            "Minor",
        )
        == "danger"
    )


def test_nina_like_payload_never_clears_an_explicit_close_instruction():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    entity = "binary_sensor.warning_clear_but_close"
    hass = FakeHass(
        {
            entity: FakeState(
                "on",
                {
                    "headline": "Entwarnung",
                    "description": "Die Lage hat sich verbessert.",
                    "recommended_actions": "Fenster und Türen weiterhin geschlossen halten.",
                    "severity": "Minor",
                },
            )
        }
    )
    result = _evaluate_nina_like_entities(hass, [entity])
    assert result.nina_status == "danger"
    assert result.official_close_instruction is True


def test_strong_nina_all_clear_beats_stale_old_close_action():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Entwarnung: Rauchentwicklung",
            "Die Warnung ist aufgehoben.",
            "Schließen Sie Fenster und Türen und schalten Sie Lüftungen und Klimaanlagen ab.",
        )
        == "clear"
    )


def test_partial_all_clear_with_flexible_close_wording_remains_danger():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Teilentwarnung nach Rauchentwicklung",
            "Für Teile des Gebietes kann Entwarnung gegeben werden.",
            "Halten Sie im betroffenen Bereich weiterhin Fenster und Türen geschlossen. "
            "Lüftungs- und Klimaanlagen sollen weiterhin ausgeschaltet bleiben.",
        )
        == "danger"
    )


def test_flexible_mowas_style_close_variants_are_recognized():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    variants = (
        "Schließen Sie alle Fenster und Türen.",
        "Bitte schließen Sie sofort Fenster und Türen.",
        "Halten Sie Türen und Fenster vorsorglich geschlossen.",
        "Schalten Sie die Belüftung aus und schließen Sie die Fenster.",
    )
    for action in variants:
        assert _evaluate_air_warning("Rauchentwicklung", "", action) == "danger"


def test_release_wording_is_not_misclassified_as_close_instruction():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    for action in (
        "Fenster und Türen können wieder geöffnet werden.",
        "Fenster und Türen müssen nicht mehr geschlossen bleiben.",
        "Sie müssen Fenster und Türen nicht geschlossen halten.",
        "Lüftungsanlagen können wieder eingeschaltet werden.",
    ):
        assert _evaluate_air_warning("Entwarnung", "Die Warnung wird aufgehoben.", action) == "clear"


def test_simultaneous_nina_danger_suppresses_other_slot_all_clear():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    clear = "binary_sensor.warning_clear"
    danger = "binary_sensor.warning_danger"
    hass = FakeHass(
        {
            clear: FakeState(
                "on",
                {
                    "id": "clear-1",
                    "headline": "Entwarnung: Rauchentwicklung",
                    "description": "Die Warnung ist aufgehoben.",
                },
            ),
            danger: FakeState(
                "on",
                {
                    "id": "danger-1",
                    "headline": "Rauchentwicklung",
                    "recommended_actions": "Halten Sie Fenster und Türen geschlossen.",
                },
            ),
        }
    )

    result = _evaluate_nina_like_entities(hass, [clear, danger])
    assert result.nina_status == "danger"
    assert result.warning_notice_kind is None
    assert result.warning_notice_text is None
    assert result.warning_ids == {"danger-1"}
    assert result.source_nina_entity == danger


def test_irrelevant_nina_warning_does_not_change_relevant_warning_fingerprint_ids():
    from custom_components.lueftungsberater.providers import _evaluate_nina_like_entities

    oil = "binary_sensor.oil_warning"
    smoke = "binary_sensor.smoke_warning"
    hass = FakeHass(
        {
            oil: FakeState(
                "on",
                {
                    "id": "oil-1",
                    "headline": "Verunreinigung eines Gewässers mit Öl",
                    "recommended_actions": "Entnehmen Sie kein Wasser aus dem Gewässer.",
                },
            ),
            smoke: FakeState(
                "on",
                {
                    "id": "smoke-1",
                    "headline": "Rauchentwicklung",
                    "recommended_actions": "Fenster und Türen geschlossen halten.",
                },
            ),
        }
    )

    result = _evaluate_nina_like_entities(hass, [oil, smoke])
    assert result.warning_ids == {"smoke-1"}


def test_provider_float_rejects_non_finite_values():
    from custom_components.lueftungsberater.providers import _float

    assert _float("nan") is None
    assert _float("inf") is None
    assert _float("-inf") is None
    assert _float("12.5") == 12.5


def test_official_entwarnung_headline_can_clear_stale_action_without_description():
    from custom_components.lueftungsberater.providers import _evaluate_air_warning

    assert (
        _evaluate_air_warning(
            "Entwarnung: Rauchentwicklung nach Brand",
            "",
            "Fenster und Türen geschlossen halten.",
        )
        == "clear"
    )


def test_unknown_forecast_temperature_unit_is_ignored():
    from custom_components.lueftungsberater.providers import _forecast_temperature_to_celsius

    assert _forecast_temperature_to_celsius(75, "definitely-not-a-temperature-unit") is None

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.lueftungsberater.auto_providers import (
    AutoProviderState,
    AutoWeatherData,
    AutoWarningData,
    AutoWarningRecord,
    _fetch_auto_warning,
    _fetch_auto_weather,
    _parse_dwd_station_index,
    _resolve_dwd_station,
    _fetch_nina_warnings,
    _parse_cap_document,
    warning_mode,
    weather_mode,
)
from custom_components.lueftungsberater.const import (
    CONF_WARNING_SOURCE,
    CONF_WARNING_SOURCE_MODE,
    CONF_WEATHER,
    CONF_WEATHER_SOURCE_MODE,
    WARNING_SOURCE_AUTO,
    WARNING_SOURCE_AUTO_PLUS_MANUAL,
    WARNING_SOURCE_MANUAL,
    WEATHER_SOURCE_AUTO,
    WEATHER_SOURCE_MANUAL,
)
from custom_components.lueftungsberater.location import EffectiveLocation
from custom_components.lueftungsberater.providers import _automatic_warning_assessment


NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def _location(lat=50.7, lon=7.1, country="DE"):
    return EffectiveLocation(
        latitude=lat,
        longitude=lon,
        elevation=60.0,
        country=country,
        source="home",
        updated_at=NOW,
    )


def test_legacy_source_modes_preserve_existing_manual_selections():
    entry = SimpleNamespace(data={CONF_WEATHER: "weather.home", CONF_WARNING_SOURCE: "nina-entry"})
    assert weather_mode(entry) == WEATHER_SOURCE_MANUAL
    assert warning_mode(entry) == WARNING_SOURCE_MANUAL


def test_new_source_modes_allow_auto_and_auto_plus_manual():
    auto = SimpleNamespace(
        data={
            CONF_WEATHER_SOURCE_MODE: WEATHER_SOURCE_AUTO,
            CONF_WARNING_SOURCE_MODE: WARNING_SOURCE_AUTO,
        }
    )
    combined = SimpleNamespace(
        data={
            CONF_WEATHER_SOURCE_MODE: WEATHER_SOURCE_MANUAL,
            CONF_WARNING_SOURCE_MODE: WARNING_SOURCE_AUTO_PLUS_MANUAL,
            CONF_WARNING_SOURCE: "nina-entry",
        }
    )
    assert weather_mode(auto) == WEATHER_SOURCE_AUTO
    assert warning_mode(auto) == WARNING_SOURCE_AUTO
    assert weather_mode(combined) == WEATHER_SOURCE_MANUAL
    assert warning_mode(combined) == WARNING_SOURCE_AUTO_PLUS_MANUAL




def test_dwd_station_index_uses_only_measurement_plus_forecast_stations():
    catalog = """
10505 ---- Aachen-Orsbach 50.48 6.02 231
10655 ---- Wuerzburg 49.46 9.58 268
99999 ---- Forecast-Only 50.42 7.06 100
"""
    measurement = '<a href="10505-BEOB.csv">A</a><a href="10655_-BEOB.csv">B</a>'
    forecast = '<a href="10505/">A</a><a href="10655/">B</a><a href="99999/">C</a>'

    stations = _parse_dwd_station_index(catalog, measurement, forecast)

    assert [item.station_id for item in stations] == ["10505", "10655"]
    assert stations[0].name == "Aachen-Orsbach"


@pytest.mark.asyncio
async def test_dwd_station_resolution_selects_nearest_usable_station():
    catalog = (
        b"10505 ---- Aachen-Orsbach 50.48 6.02 231\n"
        b"10655 ---- Wuerzburg 49.46 9.58 268\n"
    )
    state = AutoProviderState()
    with (
        patch(
            "custom_components.lueftungsberater.auto_providers._get_bytes",
            AsyncMock(return_value=catalog),
        ),
        patch(
            "custom_components.lueftungsberater.auto_providers._get_text",
            AsyncMock(side_effect=[
                '<a href="10505-BEOB.csv"></a><a href="10655-BEOB.csv"></a>',
                '<a href="10505/"></a><a href="10655/"></a>',
            ]),
        ),
    ):
        station, distance = await _resolve_dwd_station(
            object(), _location(lat=50.80, lon=6.02), state
        )

    assert station.station_id == "10505"
    assert distance < 2.0


@pytest.mark.asyncio
async def test_german_auto_weather_prefers_resolved_dwd_station():
    expected = AutoWeatherData(
        provider_domain="dwd_station",
        fetched_at=NOW,
        country="DE",
        temperature=16.5,
        humidity=70.0,
        station_id="10505",
        station_name="Aachen-Orsbach",
        station_distance_km=8.2,
    )
    state = AutoProviderState()
    with patch(
        "custom_components.lueftungsberater.auto_providers._fetch_dwd_station_weather",
        AsyncMock(return_value=expected),
    ) as station_weather:
        result = await _fetch_auto_weather(object(), _location(), "DE", state)

    station_weather.assert_awaited_once()
    assert result is expected
    assert result.provider_domain == "dwd_station"
    assert result.station_name == "Aachen-Orsbach"


@pytest.mark.asyncio
async def test_german_auto_weather_uses_dwd_icon_and_normalizes_current_forecast():
    payload = {
        "timezone": "Europe/Berlin",
        "current": {
            "temperature_2m": 17.5,
            "relative_humidity_2m": 67,
            "precipitation": 0.0,
            "rain": 0.0,
            "showers": 0.0,
            "weather_code": 3,
            "wind_speed_10m": 18.0,
            "wind_gusts_10m": 31.0,
        },
        "hourly": {
            "time": ["2026-10-02T14:00"],
            "temperature_2m": [18.0],
            "relative_humidity_2m": [65],
            "precipitation_probability": [20],
            "precipitation": [0.0],
            "weather_code": [2],
            "wind_speed_10m": [20.0],
            "wind_gusts_10m": [35.0],
        },
    }
    with patch(
        "custom_components.lueftungsberater.auto_providers._get_json",
        AsyncMock(return_value=payload),
    ) as get_json:
        result = await _fetch_auto_weather(object(), _location(), "DE")

    assert result.provider_domain == "dwd_icon"
    assert result.country == "DE"
    assert result.temperature == 17.5
    assert result.humidity == 67
    assert result.condition == "cloudy"
    assert result.wind_gust_kmh == 31.0
    assert result.hourly_forecast[0]["condition"] == "cloudy"
    assert "dwd-icon" in get_json.await_args.args[1]


@pytest.mark.asyncio
async def test_mobile_location_switches_to_dwd_after_timezone_country_resolution():
    generic = {
        "timezone": "Europe/Berlin",
        "current": {"temperature_2m": 16, "relative_humidity_2m": 70, "weather_code": 2},
        "hourly": {"time": [], "temperature_2m": []},
    }
    dwd = {
        "timezone": "Europe/Berlin",
        "current": {"temperature_2m": 15, "relative_humidity_2m": 72, "weather_code": 3},
        "hourly": {"time": [], "temperature_2m": []},
    }
    tracker_location = EffectiveLocation(
        latitude=50.7,
        longitude=7.1,
        elevation=None,
        country=None,
        source="device_tracker.wohnmobil",
        updated_at=NOW,
    )
    with patch(
        "custom_components.lueftungsberater.auto_providers._get_json",
        AsyncMock(side_effect=[generic, dwd]),
    ) as get_json:
        result = await _fetch_auto_weather(object(), tracker_location, None)

    assert get_json.await_count == 2
    assert result.provider_domain == "dwd_icon"
    assert result.country == "DE"
    assert result.temperature == 15


@pytest.mark.asyncio
async def test_nina_combines_sources_point_filters_and_marks_dwd_as_weather():
    square = {
        "type": "Polygon",
        "coordinates": [[[7.0, 50.6], [7.2, 50.6], [7.2, 50.8], [7.0, 50.8], [7.0, 50.6]]],
    }
    far = {
        "type": "Polygon",
        "coordinates": [[[8.0, 51.0], [8.1, 51.0], [8.1, 51.1], [8.0, 51.1], [8.0, 51.0]]],
    }

    async def fake_get_json(_session, url, **_kwargs):
        if url.endswith("/mowas/mapData.json"):
            return [{"id": "mow-1", "version": "1"}]
        if url.endswith("/dwd/mapData.json"):
            return [{"id": "dwd-1", "version": "1"}]
        if url.endswith("/police/mapData.json"):
            return [{"id": "police-far", "version": "1"}]
        if url.endswith("/mapData.json"):
            return []
        if url.endswith("/warnings/mow-1.json"):
            return {
                "msgType": "Alert",
                "info": [{
                    "language": "de-DE",
                    "headline": "Rauchentwicklung",
                    "description": "Rauch zieht durch das Gebiet.",
                    "parameter": [{"valueName": "instructionText", "value": "Fenster und Türen geschlossen halten."}],
                    "severity": "Severe",
                }],
            }
        if url.endswith("/warnings/dwd-1.json"):
            return {
                "msgType": "Alert",
                "info": [{
                    "language": "de-DE",
                    "headline": "Amtliche Unwetterwarnung",
                    "description": "Schweres Gewitter.",
                    "severity": "Severe",
                }],
            }
        if url.endswith("/warnings/police-far.json"):
            return {"msgType": "Alert", "info": [{"language": "de-DE", "headline": "Polizei"}]}
        if url.endswith("/warnings/mow-1.geojson") or url.endswith("/warnings/dwd-1.geojson"):
            return square
        if url.endswith("/warnings/police-far.geojson"):
            return far
        raise AssertionError(url)

    with patch(
        "custom_components.lueftungsberater.auto_providers._get_json",
        side_effect=fake_get_json,
    ):
        result = await _fetch_nina_warnings(object(), _location(), AutoProviderState())

    by_id = {item.warning_id: item for item in result.warnings}
    assert set(by_id) == {"mow-1", "dwd-1"}
    assert by_id["mow-1"].category == "civil"
    assert "Fenster" in by_id["mow-1"].instruction
    assert by_id["dwd-1"].category == "weather"
    assert result.available is True


def test_cap_parser_matches_only_actual_warning_geometry():
    cap = """<?xml version='1.0' encoding='UTF-8'?>
    <alert xmlns='urn:oasis:names:tc:emergency:cap:1.2'>
      <identifier>cap-1</identifier><msgType>Alert</msgType><sent>2026-10-02T10:00:00Z</sent>
      <info><event>Storm</event><severity>Severe</severity><headline>Storm warning</headline>
      <area><areaDesc>Example</areaDesc><polygon>50.6,7.0 50.6,7.2 50.8,7.2 50.8,7.0 50.6,7.0</polygon></area>
      </info>
    </alert>"""
    assert _parse_cap_document(cap, 50.7, 7.1) is not None
    assert _parse_cap_document(cap, 49.0, 7.1) is None


def test_cap_parser_prefers_english_instruction_when_multiple_languages_exist():
    cap = """<?xml version='1.0' encoding='UTF-8'?>
    <alert xmlns='urn:oasis:names:tc:emergency:cap:1.2'>
      <identifier>cap-multi</identifier><msgType>Alert</msgType><sent>2026-10-02T10:00:00Z</sent>
      <info><language>fr-FR</language><event>Incident</event><severity>Severe</severity>
        <instruction>Gardez les fenêtres fermées.</instruction>
        <area><areaDesc>Zone</areaDesc><polygon>50.6,7.0 50.6,7.2 50.8,7.2 50.8,7.0 50.6,7.0</polygon></area>
      </info>
      <info><language>en-GB</language><event>Incident</event><severity>Severe</severity>
        <instruction>Keep windows and doors closed.</instruction>
        <area><areaDesc>Zone</areaDesc><polygon>50.6,7.0 50.6,7.2 50.8,7.2 50.8,7.0 50.6,7.0</polygon></area>
      </info>
    </alert>"""
    record = _parse_cap_document(cap, 50.7, 7.1)
    assert record is not None
    assert record.instruction == "Keep windows and doors closed."



@pytest.mark.asyncio
async def test_unsupported_country_is_explicit_no_coverage_not_an_outage():
    result = await _fetch_auto_warning(
        SimpleNamespace(), object(), _location(country="CA"), "CA", AutoProviderState()
    )
    assert result.available is True
    assert result.error == "unsupported_country"
    assert result.warnings == []


@pytest.mark.asyncio
async def test_unresolved_country_is_unknown_not_an_all_clear():
    location = _location(country=None)
    result = await _fetch_auto_warning(
        SimpleNamespace(), object(), location, None, AutoProviderState()
    )
    assert result.available is False
    assert result.error == "country_unresolved"
    assert result.safety_source_key == "auto_warning:50.7000:7.1000"
    assert result.warnings == []


def test_safety_keys_are_location_stable_and_provider_independent():
    from custom_components.lueftungsberater.auto_providers import _safety_location_key

    location = _location()
    assert _safety_location_key("weather", location) == "auto_weather:50.7000:7.1000"
    assert _safety_location_key("warning", location) == "auto_warning:50.7000:7.1000"


def test_auto_warning_close_instruction_hard_locks_but_severe_weather_stays_soft():
    data = AutoWarningData(
        provider_domain="nina_auto",
        fetched_at=NOW,
        available=True,
        country="DE",
        safety_source_key="auto_warning:50.7000:7.1000",
        warnings=[
            AutoWarningRecord(
                warning_id="civil",
                provider_domain="nina_auto",
                category="civil",
                headline="Rauchentwicklung",
                instruction="Fenster und Türen geschlossen halten.",
                evidence_at=NOW,
            ),
            AutoWarningRecord(
                warning_id="weather",
                provider_domain="nina_auto",
                category="weather",
                headline="Schweres Gewitter",
                severity="Severe",
                evidence_at=NOW,
            ),
        ],
    )
    with patch(
        "custom_components.lueftungsberater.providers.auto_warning_data",
        return_value=data,
    ):
        assessed = _automatic_warning_assessment(SimpleNamespace(), SimpleNamespace())

    assert assessed.official_close_instruction is True
    assert assessed.nina_status == "danger"
    assert assessed.weather_danger is True
    assert assessed.weather_hard_lock is False


def test_auto_warning_cancel_cannot_reactivate_stale_close_instruction_or_weather_severity():
    data = AutoWarningData(
        provider_domain="nina_auto",
        fetched_at=NOW,
        available=True,
        country="DE",
        safety_source_key="auto_warning:50.7000:7.1000",
        warnings=[
            AutoWarningRecord(
                warning_id="cancelled",
                provider_domain="nina_auto",
                category="weather",
                headline="Entwarnung: Gefahr ist vorüber",
                description="Die Warnung wurde aufgehoben.",
                instruction="Fenster und Türen geschlossen halten.",
                severity="Extreme",
                msg_type="Cancel",
                evidence_at=NOW,
            )
        ],
    )
    with patch(
        "custom_components.lueftungsberater.providers.auto_warning_data",
        return_value=data,
    ):
        assessed = _automatic_warning_assessment(SimpleNamespace(), SimpleNamespace())

    assert assessed.official_close_instruction is False
    assert assessed.nina_status == "none"
    assert assessed.weather_danger is False
    assert assessed.weather_hard_lock is False

@pytest.mark.asyncio
async def test_v014_migration_preserves_existing_weather_and_adds_auto_warning(
    hass, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.lueftungsberater import async_migrate_entry
    from custom_components.lueftungsberater.const import DOMAIN, ENTRY_KIND_LOCAL, CONF_ENTRY_KIND

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bestehend",
        version=1,
        minor_version=13,
        data={
            CONF_ENTRY_KIND: ENTRY_KIND_LOCAL,
            CONF_WEATHER: "weather.home",
            CONF_WARNING_SOURCE: "existing-warning-entry",
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.minor_version == 14
    assert entry.data[CONF_WEATHER_SOURCE_MODE] == WEATHER_SOURCE_MANUAL
    assert entry.data[CONF_WEATHER] == "weather.home"
    assert entry.data[CONF_WARNING_SOURCE_MODE] == WARNING_SOURCE_AUTO_PLUS_MANUAL
    assert entry.data[CONF_WARNING_SOURCE] == "existing-warning-entry"


@pytest.mark.asyncio
async def test_v014_migration_defaults_empty_legacy_sources_to_auto(
    hass, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.lueftungsberater import async_migrate_entry
    from custom_components.lueftungsberater.const import DOMAIN, ENTRY_KIND_LOCAL, CONF_ENTRY_KIND

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Neu ohne Quellen",
        version=1,
        minor_version=13,
        data={CONF_ENTRY_KIND: ENTRY_KIND_LOCAL, CONF_WARNING_SOURCE: "none"},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.data[CONF_WEATHER_SOURCE_MODE] == WEATHER_SOURCE_AUTO
    assert entry.data[CONF_WARNING_SOURCE_MODE] == WARNING_SOURCE_AUTO

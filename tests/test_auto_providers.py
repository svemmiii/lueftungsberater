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
    _parse_dwd_measurement,
    _dwd_observation_is_fresh,
    _parse_uba_stations,
    _parse_uba_components,
    _parse_uba_airquality,
    _parse_nina_district_geometries,
    _geojson_contains_point,
    _resolve_dwd_station,
    _resolve_nina_region_arses,
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


def test_dwd_station_index_uses_all_current_measurement_stations_even_without_forecast():
    catalog = """clu;CofX;id;ICAO;name;latitude;longitude;elevation;Hmod_H;type
1;8;10505;----;Aachen-Orsbach;50.48;6.02;231;;LAND
2;8;10655;----;Wuerzburg;49.46;9.58;268;;LAND
3;8;99999;----;Forecast-Only;50.42;7.06;100;;LAND
"""
    measurement = '<a href="10505-BEOB.csv">A</a><a href="10655_-BEOB.csv">B</a>'
    forecast = '<a href="99999/">C</a>'

    stations = _parse_dwd_station_index(catalog, measurement, forecast)

    assert [item.station_id for item in stations] == ["10505", "10655"]
    assert stations[0].name == "Aachen-Orsbach"
    assert stations[0].longitude == pytest.approx(6 + 2 / 60)


def test_dwd_live_station_catalog_headers_are_supported():
    catalog = """Kennung;Stationsname;Geog_Breite;Geog_Laenge;Stationshoehe
10505;Aachen-Orsbach;50.7983;6.0244;231
10655;Wuerzburg;49.7700;9.9570;268
"""
    measurement = '<a href="10505-BEOB.csv"></a><a href="10655-BEOB.csv"></a>'
    stations = _parse_dwd_station_index(catalog, measurement)
    assert [item.station_id for item in stations] == ["10505", "10655"]
    assert stations[0].latitude == pytest.approx(50.7983)
    assert stations[0].longitude == pytest.approx(6.0244)


def test_dwd_measurement_uses_one_coherent_observation_row():
    data = (
        "meta;meta;dry_bulb_temperature_at_2_meter_above_ground;relative_humidity\n"
        "unit;unit;C;%\n"
        "desc;desc;temp;humidity\n"
        "202610061400;X;18,0;---\n"
        "202610061300;X;17,0;61\n"
    ).encode("iso-8859-1")
    parsed = _parse_dwd_measurement(data)
    assert parsed["dry_bulb_temperature_at_2_meter_above_ground"] == "18,0"
    assert "relative_humidity" not in parsed


def test_uba_v4_metadata_and_airquality_arrays_are_supported():
    stations = _parse_uba_stations({
        "data": {
            "123": [123, "DENW123", "Teststation", "City", None, None, None, 7.10, 50.70]
        }
    })
    assert len(stations) == 1
    assert stations[0].code == "DENW123"
    assert stations[0].latitude == pytest.approx(50.70)
    assert stations[0].longitude == pytest.approx(7.10)

    components = _parse_uba_components({
        "data": {
            "1": [1, "PM10", "Feinstaub PM10"],
            "5": [5, "NO2", "Stickstoffdioxid"],
            "9": [9, "PM2.5", "Feinstaub PM2.5"],
        }
    })
    assert components[1] == "pm10"
    assert components[5] == "no2"
    assert components[9] == "pm2_5"

    values = _parse_uba_airquality({
        "data": {
            "123": {
                "2026-10-06 14:00:00": [
                    "2026-10-06 15:00:00", 1, 0,
                    [1, 18.0, 1, "1.0"],
                    [5, 22.0, 1, "1.0"],
                    [9, 7.0, 1, "1.0"],
                ]
            }
        }
    }, components)
    assert values == {"pm10": 18.0, "no2": 22.0, "pm2_5": 7.0}


def test_nina_district_geometry_resolves_ars_and_polygon_border_is_inside():
    payload = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"RS": "05314"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[7.0, 50.6], [7.2, 50.6], [7.2, 50.8], [7.0, 50.8], [7.0, 50.6]]],
            },
        }],
    }
    districts = _parse_nina_district_geometries(payload)
    assert districts[0][0] == "053140000000"
    assert _geojson_contains_point(districts[0][1], 50.7, 7.0) is True


@pytest.mark.asyncio
async def test_dwd_station_resolution_selects_nearest_usable_station():
    catalog = (
        b"clu;CofX;id;ICAO;name;latitude;longitude;elevation;Hmod_H;type\n"
        b"1;8;10505;----;Aachen-Orsbach;50.48;6.02;231;;LAND\n"
        b"2;8;10655;----;Wuerzburg;49.46;9.58;268;;LAND\n"
    )
    state = AutoProviderState()
    with (
        patch(
            "custom_components.lueftungsberater.auto_providers._get_bytes",
            AsyncMock(return_value=catalog),
        ),
        patch(
            "custom_components.lueftungsberater.auto_providers._get_text",
            AsyncMock(return_value='<a href="10505-BEOB.csv"></a><a href="10655-BEOB.csv"></a>'),
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
    with (
        patch(
            "custom_components.lueftungsberater.auto_providers._get_json",
            AsyncMock(return_value=payload),
        ) as get_json,
        patch(
            "custom_components.lueftungsberater.auto_providers._fetch_coordinate_air_quality",
            AsyncMock(return_value=({}, {}, None)),
        ),
    ):
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
    with (
        patch(
            "custom_components.lueftungsberater.auto_providers._get_json",
            AsyncMock(side_effect=[generic, dwd]),
        ) as get_json,
        patch(
            "custom_components.lueftungsberater.auto_providers._fetch_coordinate_air_quality",
            AsyncMock(return_value=({}, {}, None)),
        ),
    ):
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


def test_auto_warning_close_instruction_hard_locks_but_severe_weather_stays_soft(freezer):
    freezer.move_to(NOW)
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
        assessed = _automatic_warning_assessment(SimpleNamespace(), SimpleNamespace(data={}))

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
        assessed = _automatic_warning_assessment(SimpleNamespace(), SimpleNamespace(data={}))

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
    assert entry.minor_version == 15
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


def test_dwd_measurement_chooses_newest_timestamp_and_exposes_it():
    data = (
        "date;time;dry_bulb_temperature_at_2_meter_above_ground;relative_humidity\n"
        "unit;unit;C;%\n"
        "desc;desc;temp;humidity\n"
        "20261006;1300;17,0;61\n"
        "20261006;1400;18,0;60\n"
    ).encode("iso-8859-1")
    parsed = _parse_dwd_measurement(data)
    assert parsed["dry_bulb_temperature_at_2_meter_above_ground"] == "18,0"
    assert parsed["relative_humidity"] == "60"
    assert parsed["__observation_at"].startswith("2026-10-06T14:00:00")


def test_dwd_observation_freshness_requires_recent_verified_timestamp():
    now = datetime(2026, 10, 6, 16, 0, tzinfo=timezone.utc)
    assert _dwd_observation_is_fresh({"__observation_at": "2026-10-06T14:00:00+00:00"}, now=now)
    assert not _dwd_observation_is_fresh({"__observation_at": "2026-10-06T12:59:59+00:00"}, now=now)
    assert not _dwd_observation_is_fresh({"__observation_at": "2026-10-06T16:31:00+00:00"}, now=now)
    assert not _dwd_observation_is_fresh({}, now=now)


@pytest.mark.asyncio
async def test_nina_region_prefers_current_bkg_vg250_geometry():
    payload = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"ars": "05314"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[7.0, 50.6], [7.2, 50.6], [7.2, 50.8], [7.0, 50.8], [7.0, 50.6]]],
            },
        }],
    }
    state = AutoProviderState()
    with patch(
        "custom_components.lueftungsberater.auto_providers._get_json",
        AsyncMock(return_value=payload),
    ) as get_json:
        result = await _resolve_nina_region_arses(object(), _location(lat=50.7, lon=7.1), state)
    assert result == ["053140000000"]
    assert state.nina_region_source == "bkg_vg250"
    assert "wfs_vg250" in get_json.await_args.args[1]
    assert get_json.await_args.kwargs["params"]["typenames"] == "vg250_krs"


@pytest.mark.asyncio
async def test_nina_region_keeps_both_exact_boundary_districts():
    left = {"type": "Polygon", "coordinates": [[[7.0, 50.6], [7.1, 50.6], [7.1, 50.8], [7.0, 50.8], [7.0, 50.6]]]}
    right = {"type": "Polygon", "coordinates": [[[7.1, 50.6], [7.2, 50.6], [7.2, 50.8], [7.1, 50.8], [7.1, 50.6]]]}
    payload = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"ars": "05314"}, "geometry": left},
        {"type": "Feature", "properties": {"ars": "05382"}, "geometry": right},
    ]}
    with patch(
        "custom_components.lueftungsberater.auto_providers._get_json",
        AsyncMock(return_value=payload),
    ):
        result = await _resolve_nina_region_arses(
            object(), _location(lat=50.7, lon=7.1), AutoProviderState()
        )
    assert result == ["053140000000", "053820000000"]


# CAP language/normalization regressions retained in the existing test file.
from datetime import datetime as _cap_regression_datetime, timedelta as _cap_regression_timedelta, timezone as _cap_regression_timezone
import json as _cap_regression_json
from types import SimpleNamespace as _cap_regression_SimpleNamespace
from unittest.mock import patch as _cap_regression_patch
import xml.etree.ElementTree as _cap_regression_ET
import pytest as _cap_regression_pytest
from custom_components.lueftungsberater import auto_providers as _cap_regression_ap
from custom_components.lueftungsberater import providers as _cap_regression_providers
from custom_components.lueftungsberater.warning_language import json_infos as _cap_regression_json_infos
from custom_components.lueftungsberater.warning_policy import assess_official_warning as _cap_regression_assess_official_warning
_cap_regression_NOW = _cap_regression_datetime(2026, 10, 25, 12, tzinfo=_cap_regression_timezone.utc)
_cap_regression_NEAR = '50.6,7.0 50.6,7.2 50.8,7.2 50.8,7.0 50.6,7.0'
_cap_regression_FAR = '51.0,8.0 51.0,8.2 51.2,8.2 51.2,8.0 51.0,8.0'

def _cap_regression_info(text, language='de-DE', **changes):
    return {'language': language, 'headline': 'Wind gusts', 'description': text, 'effective': (_cap_regression_NOW - _cap_regression_timedelta(hours=1)).isoformat(), 'onset': _cap_regression_NOW.isoformat(), 'expires': (_cap_regression_NOW + _cap_regression_timedelta(hours=3)).isoformat(), 'area': {'polygon': _cap_regression_NEAR}, **changes}

def _cap_regression_document(infos):
    root = _cap_regression_ET.Element('alert', xmlns='urn:oasis:names:tc:emergency:cap:1.2')
    for key, value in {'identifier': 'multilingual', 'sender': 'authority@example.org', 'sent': (_cap_regression_NOW - _cap_regression_timedelta(hours=1)).isoformat(), 'msgType': 'Alert', 'status': 'Actual', 'scope': 'Public'}.items():
        _cap_regression_ET.SubElement(root, key).text = value

    def add(parent, key, value):
        for item in value if isinstance(value, list) else [value]:
            child = _cap_regression_ET.SubElement(parent, key)
            if isinstance(item, dict):
                for nested, contents in item.items():
                    add(child, nested, contents)
            else:
                child.text = str(item)
    for block in infos:
        add(root, 'info', block)
    return _cap_regression_ET.tostring(root, encoding='unicode')

def _cap_regression_parse(infos):
    with _cap_regression_patch.object(_cap_regression_ap.dt_util, 'utcnow', return_value=_cap_regression_NOW):
        return _cap_regression_ap._parse_cap_document(_cap_regression_document(infos), 50.7, 7.1)

def _cap_regression_notice(infos):
    record = _cap_regression_parse(infos)
    assert record is not None
    result = _cap_regression_assess_official_warning(record, _cap_regression_NOW, elevation=60)
    assert result is not None
    _cap_regression_json.dumps(result, allow_nan=False)
    return (record, result)

def test_all_language_blocks_are_retained_and_equal_claims_merge_with_provenance():
    record, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h erwartet.'), _cap_regression_info('Gusts 110 km/h expected.', 'en-GB'), _cap_regression_info('Rüzgâr hamleleri 110 km/sa bekleniyor.', 'tr-TR')])
    assert len(record.info_blocks) == 3
    assert result['hard_lock']
    assert len(result['gust_evidence']) == 1
    assert {source['language'] for source in result['gust_evidence'][0]['provenance']} == {'de-DE', 'en-GB', 'tr-TR'}
    assert result['cap_languages'] == ['de-DE', 'en-GB', 'tr-TR']

def test_conflicting_translations_are_explicit_and_no_confirmed_clear_is_invented():
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h erwartet.'), _cap_regression_info('Gusts 110 km/h are now ruled out.', 'en-GB')])
    assert not result['hard_lock']
    assert result['gust_polarity_conflict'] and result['interpretation_uncertain']

def test_conflicting_values_keep_the_confirmed_higher_peak_and_all_originals():
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h erwartet.'), _cap_regression_info('Gusts 70 km/h expected.', 'en-GB')])
    assert result['hard_lock'] and result['gust_value_conflict']
    assert {item['max'] for item in result['gust_evidence']} == {70, 110}

def test_far_away_translation_cannot_supply_a_local_gust_or_cancel_it():
    record, result = _cap_regression_notice([_cap_regression_info('Böen 70 km/h erwartet.'), _cap_regression_info('Gusts 145 km/h expected.', 'en-GB', area={'polygon': _cap_regression_FAR})])
    assert len(record.info_blocks) == 2
    assert not result['hard_lock'] and result['gust_max_kmh'] == 70
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h erwartet.'), _cap_regression_info('Gusts 110 km/h ruled out.', 'en-GB', area={'polygon': _cap_regression_FAR})])
    assert result['hard_lock'] and (not result['gust_polarity_conflict'])

def test_future_and_expired_infos_never_become_current_confirmed_gusts():
    _, result = _cap_regression_notice([_cap_regression_info('Böen 70 km/h erwartet.'), _cap_regression_info('Gusts 145 km/h expected.', 'en-GB', effective=(_cap_regression_NOW + _cap_regression_timedelta(hours=1)).isoformat(), onset=(_cap_regression_NOW + _cap_regression_timedelta(hours=1)).isoformat()), _cap_regression_info('Rüzgâr hamleleri 145 km/h bekleniyor.', 'tr-TR', expires=(_cap_regression_NOW - _cap_regression_timedelta(seconds=1)).isoformat())])
    assert not result['hard_lock']
    assert result['next_transition'] is not None

def test_denial_in_a_different_time_period_does_not_cancel_current_wind():
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h erwartet.', expires=(_cap_regression_NOW + _cap_regression_timedelta(hours=1)).isoformat()), _cap_regression_info('Gusts 110 km/h are ruled out.', 'en-GB', onset=(_cap_regression_NOW + _cap_regression_timedelta(hours=2)).isoformat())])
    assert result['hard_lock'] and (not result['gust_polarity_conflict'])

@_cap_regression_pytest.mark.parametrize('change', [{'onset': 'invalid'}, {'onset': '0001-01-01T00:00:00Z'}, {'area': {'areaDesc': 'Unknown'}}])
def test_unverifiable_other_info_never_erases_a_valid_hazard(change):
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h erwartet.'), _cap_regression_info('Gusts 110 km/h are ruled out.', 'en-GB', **change)])
    assert result['hard_lock']
    assert result['interpretation_uncertain'] or result['timing_uncertain']

def test_all_original_parameter_values_event_codes_and_provenance_are_retained():
    block = _cap_regression_info('Böen 110 km/h.', parameter=[{'valueName': 'gusts', 'value': '70 km/h'}, {'valueName': 'gusts', 'value': '110 km/h'}], eventCode=[{'valueName': 'II', 'value': '51'}, {'valueName': 'II', 'value': '52'}])
    record, result = _cap_regression_notice([block])
    variant = record.info_blocks[0].to_record(record)
    assert variant.parameters['gusts'] == ['70 km/h', '110 km/h']
    assert variant.event_codes['II'] == ['51', '52']
    assert result['hard_lock'] and result['gust_conflict']
    assert result['gust_evidence'][0]['provenance'][0]['sender'] == 'authority@example.org'

def test_nina_keeps_all_languages_instead_of_only_german():
    with _cap_regression_patch.object(_cap_regression_ap.dt_util, 'utcnow', return_value=_cap_regression_NOW):
        record = _cap_regression_ap._nina_record('dwd-multi', {'sender': 'dwd', 'sent': _cap_regression_NOW.isoformat(), 'info': [_cap_regression_info('Böen 110 km/h erwartet.'), _cap_regression_info('Gusts 110 km/h are now ruled out.', 'en-GB')]}, source='dwd', lat=50.7, lon=7.1)
    assert len(record.info_blocks) == 2
    assert _cap_regression_assess_official_warning(record, _cap_regression_NOW, elevation=60)['gust_polarity_conflict']

def test_json_wrappers_do_not_merge_independent_warning_versions():
    payload = {'alerts': [{'info': [_cap_regression_info('Böen 110 km/h.')]}, {'info': [_cap_regression_info('Keine Böen.')]}]}
    assert not _cap_regression_json_infos(payload)
    assert len(_cap_regression_json_infos({'alert': {'info': [_cap_regression_info('Böen 110 km/h.')]}})) == 1

def _cap_regression_automatic(record):
    data = _cap_regression_ap.AutoWarningData('meteoalarm_auto', _cap_regression_NOW, True, 'DE', safety_source_key='auto_warning:50.7:7.1', warnings=[record])
    with _cap_regression_patch.object(_cap_regression_providers, 'auto_warning_data', return_value=data), _cap_regression_patch.object(_cap_regression_providers.dt_util, 'utcnow', return_value=_cap_regression_NOW), _cap_regression_patch.object(_cap_regression_providers, 'effective_location', return_value=_cap_regression_SimpleNamespace(elevation=60)):
        return _cap_regression_providers._automatic_warning_assessment(_cap_regression_SimpleNamespace(), _cap_regression_SimpleNamespace(data={}))

def test_cross_language_conflict_marks_existing_safety_as_unknown():
    record = _cap_regression_parse([_cap_regression_info('Böen 110 km/h erwartet.'), _cap_regression_info('Gusts 110 km/h are now ruled out.', 'en-GB')])
    result = _cap_regression_automatic(record)
    assert not result.weather_hard_lock
    assert result.warning_ambiguous_clear

def test_original_close_order_in_a_nonpreferred_language_is_honored():
    record = _cap_regression_parse([_cap_regression_info('Rauch', 'de-DE', instruction='Fenster und Türen schließen.', headline='Rauch'), _cap_regression_info('Smoke', 'en-GB', headline='Smoke')])
    result = _cap_regression_automatic(record)
    assert result.official_close_instruction
    assert result.nina_status == 'danger'

def test_unverified_close_order_cannot_create_a_new_hard_lock():
    record = _cap_regression_parse([_cap_regression_info('Rauch', 'de-DE', instruction='Fenster und Türen schließen.', headline='Rauch', area={'areaDesc': 'Unknown region'}), _cap_regression_info('Smoke', 'en-GB', headline='Smoke')])
    result = _cap_regression_automatic(record)
    assert not result.official_close_instruction
    assert result.warning_ambiguous_clear

def test_valid_lower_wind_is_still_a_confirmed_reachable_feed():
    record = _cap_regression_parse([_cap_regression_info('Böen 70 km/h erwartet.'), _cap_regression_info('Gusts 70 km/h expected.', 'en-GB')])
    result = _cap_regression_automatic(record)
    assert not result.weather_hard_lock
    assert not result.warning_ambiguous_clear

def test_exact_thirty_minute_lead_is_unchanged_per_info():
    onset = _cap_regression_NOW + _cap_regression_timedelta(minutes=30)
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h erwartet.', onset=onset.isoformat())])
    assert result['hard_lock'] and result['phase'] == 'prelock'
    record = _cap_regression_parse([_cap_regression_info('Böen 110 km/h erwartet.', onset=(onset + _cap_regression_timedelta(microseconds=1)).isoformat())])
    assert not _cap_regression_assess_official_warning(record, _cap_regression_NOW, elevation=60)['hard_lock']

def test_nina_point_checked_geometry_preserves_single_and_identical_geocoded_infos():
    area = {'geocode': {'valueName': 'WARNCELLID', 'value': 'unlisted-cell'}}
    with _cap_regression_patch.object(_cap_regression_ap.dt_util, 'utcnow', return_value=_cap_regression_NOW):
        for blocks in ([_cap_regression_info('Böen 110 km/h.', area=area)], [_cap_regression_info('Böen 110 km/h.', area=area), _cap_regression_info('Gusts 110 km/h.', 'en-GB', area=area)]):
            record = _cap_regression_ap._nina_record('dwd-geometry', {'sender': 'dwd', 'info': blocks}, source='dwd', lat=50.7, lon=7.1, geometry_verified=True)
            assert _cap_regression_assess_official_warning(record, _cap_regression_NOW, elevation=60)['hard_lock']

def test_nina_envelope_geometry_does_not_verify_different_unknown_subregions():
    areas = [{'geocode': {'valueName': 'WARNCELLID', 'value': value}} for value in ('one', 'two')]
    with _cap_regression_patch.object(_cap_regression_ap.dt_util, 'utcnow', return_value=_cap_regression_NOW):
        record = _cap_regression_ap._nina_record('dwd-geometry', {'sender': 'dwd', 'info': [_cap_regression_info('Böen 110 km/h.', area=areas[0]), _cap_regression_info('Gusts 70 km/h.', 'en-GB', area=areas[1])]}, source='dwd', lat=50.7, lon=7.1, geometry_verified=True)
    result = _cap_regression_assess_official_warning(record, _cap_regression_NOW, elevation=60)
    assert not result['hard_lock'] and result['interpretation_uncertain']

def test_numeric_height_of_an_unmatched_area_does_not_restrict_the_matched_area():
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h.', area=[{'polygon': _cap_regression_NEAR, 'altitude': '0'}, {'polygon': _cap_regression_FAR, 'altitude': '9000'}])])
    assert result['hard_lock']

@_cap_regression_pytest.mark.parametrize('value', ['unknown', 'NaN', 'Infinity'])
def test_malformed_matched_area_altitude_is_preserved_as_unknown(value):
    _, result = _cap_regression_notice([_cap_regression_info('Böen 110 km/h.', area={'polygon': _cap_regression_NEAR, 'altitude': value})])
    assert not result['hard_lock'] and result['interpretation_uncertain']

def test_missing_effective_defaults_to_original_cap_sent_time():
    record = _cap_regression_parse([_cap_regression_info('Böen 110 km/h.', effective='')])
    assert record.info_blocks[0].to_record(record).effective == record.issued_at

def test_future_effective_on_a_wind_info_does_not_delay_an_active_close_order():
    record = _cap_regression_parse([_cap_regression_info('Gusts 145 km/h.', 'en-GB', effective=(_cap_regression_NOW + _cap_regression_timedelta(hours=1)).isoformat(), onset=(_cap_regression_NOW + _cap_regression_timedelta(hours=1)).isoformat()), _cap_regression_info('Rauch', headline='Rauch', instruction='Fenster schließen.')])
    assert _cap_regression_automatic(record).official_close_instruction

def test_unknown_language_text_cannot_confirm_an_all_clear():
    record = _cap_regression_parse([_cap_regression_info('Unbekannter Text', 'ja-JP', headline='Entwarnung')])
    result = _cap_regression_automatic(record)
    assert result.warning_ambiguous_clear
    assert result.warning_notice_kind != 'all_clear'


def test_actual_nws_adapter_keeps_profiled_gust_with_japanese_text():
    with _cap_regression_patch.object(_cap_regression_ap.dt_util, "utcnow", return_value=_cap_regression_NOW):
        record = _cap_regression_ap._nws_record({"properties": {
            "id": "nws-profiled-japanese", "sender": "nws@example.org", "language": "ja-JP",
            "headline": "強風", "description": "風が強まります", "messageType": "Alert",
            "sent": (_cap_regression_NOW - _cap_regression_timedelta(hours=1)).isoformat(),
            "effective": (_cap_regression_NOW - _cap_regression_timedelta(hours=1)).isoformat(),
            "onset": (_cap_regression_NOW - _cap_regression_timedelta(minutes=10)).isoformat(),
            "expires": (_cap_regression_NOW + _cap_regression_timedelta(hours=2)).isoformat(),
            "parameters": {"maxWindGust": ["110 km/h"]},
        }})
    result = _cap_regression_automatic(record)
    assert result.weather_hard_lock and result.weather_danger
    assert result.weather_reason_args["gust_kmh"] == 110
    assert result.warning_ambiguous_clear  # The free text remains unsupported.
    assert result.warning_observations[0]["notice"]["gust_evidence"][0]["evidence_kind"] == "structured_cap"


def test_actual_nina_adapter_keeps_a_recognized_command_under_wrong_language_metadata():
    with _cap_regression_patch.object(_cap_regression_ap.dt_util, "utcnow", return_value=_cap_regression_NOW):
        record = _cap_regression_ap._nina_record("nina-wrong-language", {
            "sender": "authority@example.org", "sent": _cap_regression_NOW.isoformat(),
            "info": [_cap_regression_info("Giftiger Rauch zieht auf.", "ja-JP", headline="Rauch",
                                           instruction="Fenster und Türen schließen.")],
        }, lat=50.7, lon=7.1, geometry_verified=True)
    result = _cap_regression_automatic(record)
    assert result.official_close_instruction and result.nina_status == "danger"
    assert result.warning_ambiguous_clear
    proof = result.warning_observations[0]
    assert proof["official_close_instruction"]
    assert proof["notice"]["close_evidence"][0]["provenance"]["language_mismatch"]

"""Location-driven automatic weather and official-warning providers.

The automatic provider layer deliberately does not create or reconfigure other
Home Assistant integrations.  It consumes public coordinate-based provider APIs
and exposes a small normalized cache to ``providers.py``.  User-selected HA
weather/warning integrations remain available as explicit overrides.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from io import BytesIO
from datetime import datetime, timedelta, timezone
import logging
import math
import re
import zipfile
from typing import Any
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    AUTO_PROVIDER_STALE_MAX_AGE,
    AUTO_WARNING_REFRESH_INTERVAL,
    AUTO_WEATHER_REFRESH_INTERVAL,
    CONF_WARNING_SOURCE,
    CONF_WARNING_SOURCE_MODE,
    CONF_WEATHER,
    CONF_WEATHER_SOURCE_MODE,
    DATA_AUTO_PROVIDER_CACHE,
    DEFAULT_WARNING_SOURCE_MODE,
    DEFAULT_WEATHER_SOURCE_MODE,
    DOMAIN,
    WARNING_SOURCE_AUTO,
    WARNING_SOURCE_AUTO_PLUS_MANUAL,
    WARNING_SOURCE_NONE,
    WEATHER_SOURCE_AUTO,
    WEATHER_SOURCE_MANUAL,
)
from .location import EffectiveLocation
from .warning_regions import geocode_geometry, coordinate_country

_LOGGER = logging.getLogger(__name__)

_OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
_OPEN_METEO_DWD = "https://api.open-meteo.com/v1/dwd-icon"
_DWD_STATION_CATALOG = "https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication"
_DWD_MEASUREMENT_INDEX = "https://opendata.dwd.de/weather/weather_reports/poi/"
_DWD_FORECAST_INDEX = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/"
_DWD_MEASUREMENT_URL = "https://opendata.dwd.de/weather/weather_reports/poi/{station_id:_<5}-BEOB.csv"
_DWD_FORECAST_URL = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/{station_id}/kml/MOSMIX_L_LATEST_{station_id}.kmz"
_NINA_BASE = "https://warnung.bund.de/api31"
_NWS_ALERTS = "https://api.weather.gov/alerts/active"
_METEOALARM_FEED = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-{slug}"
_HTTP_TIMEOUT = aiohttp.ClientTimeout(total=20)

# Only providers explicitly listed here are treated as supported automatic
# warning providers.  This is intentionally a controlled registry rather than
# guessing arbitrary alert feeds at runtime.
_METEOALARM_COUNTRIES: dict[str, str] = {
    "AD": "andorra",
    "AT": "austria",
    "BE": "belgium",
    "BA": "bosnia-herzegovina",
    "BG": "bulgaria",
    "HR": "croatia",
    "CY": "cyprus",
    "CZ": "czechia",
    "DK": "denmark",
    "EE": "estonia",
    "FI": "finland",
    "FR": "france",
    "GR": "greece",
    "HU": "hungary",
    "IS": "iceland",
    "IE": "ireland",
    "IL": "israel",
    "IT": "italy",
    "LV": "latvia",
    "LT": "lithuania",
    "LU": "luxembourg",
    "MT": "malta",
    "MD": "moldova",
    "ME": "montenegro",
    "NL": "netherlands",
    "MK": "republic-of-north-macedonia",
    "NO": "norway",
    "PL": "poland",
    "PT": "portugal",
    "RO": "romania",
    "RS": "serbia",
    "SK": "slovakia",
    "SI": "slovenia",
    "ES": "spain",
    "SE": "sweden",
    "CH": "switzerland",
    "UA": "ukraine",
    "GB": "united-kingdom",
}

# Compatibility mapping for direct weather-adapter calls. The coordinator
# resolves countries from geographic boundaries before choosing warning feeds.
_TIMEZONE_COUNTRY: dict[str, str] = {
    "Europe/Andorra": "AD", "Europe/Vienna": "AT", "Europe/Brussels": "BE",
    "Europe/Sarajevo": "BA", "Europe/Sofia": "BG", "Europe/Zagreb": "HR",
    "Asia/Nicosia": "CY", "Europe/Prague": "CZ", "Europe/Copenhagen": "DK",
    "Europe/Tallinn": "EE", "Europe/Helsinki": "FI", "Europe/Paris": "FR",
    "Europe/Athens": "GR", "Europe/Budapest": "HU", "Atlantic/Reykjavik": "IS",
    "Europe/Dublin": "IE", "Asia/Jerusalem": "IL", "Europe/Rome": "IT", "Europe/Riga": "LV",
    "Europe/Vilnius": "LT", "Europe/Luxembourg": "LU", "Europe/Malta": "MT",
    "Europe/Chisinau": "MD", "Europe/Podgorica": "ME", "Europe/Amsterdam": "NL",
    "Europe/Skopje": "MK", "Europe/Oslo": "NO", "Europe/Warsaw": "PL",
    "Europe/Lisbon": "PT", "Atlantic/Madeira": "PT", "Atlantic/Azores": "PT",
    "Europe/Bucharest": "RO", "Europe/Belgrade": "RS", "Europe/Bratislava": "SK",
    "Europe/Ljubljana": "SI", "Europe/Madrid": "ES", "Atlantic/Canary": "ES",
    "Europe/Stockholm": "SE", "Europe/Zurich": "CH", "Europe/London": "GB",
    "Europe/Kyiv": "UA", "Europe/Kiev": "UA", "Europe/Uzhgorod": "UA", "Europe/Zaporozhye": "UA",
    "Europe/Mariehamn": "FI", "Africa/Ceuta": "ES",
    "Europe/Berlin": "DE", "Europe/Busingen": "DE",
    "America/New_York": "US", "America/Detroit": "US", "America/Kentucky/Louisville": "US",
    "America/Kentucky/Monticello": "US", "America/Indiana/Indianapolis": "US",
    "America/Indiana/Vincennes": "US", "America/Indiana/Winamac": "US",
    "America/Indiana/Marengo": "US", "America/Indiana/Petersburg": "US",
    "America/Indiana/Vevay": "US", "America/Chicago": "US", "America/Indiana/Knox": "US",
    "America/Menominee": "US", "America/North_Dakota/Center": "US",
    "America/North_Dakota/New_Salem": "US", "America/North_Dakota/Beulah": "US",
    "America/Denver": "US", "America/Boise": "US", "America/Phoenix": "US",
    "America/Los_Angeles": "US", "America/Anchorage": "US", "America/Juneau": "US",
    "America/Sitka": "US", "America/Metlakatla": "US", "America/Yakutat": "US",
    "America/Nome": "US", "America/Adak": "US", "Pacific/Honolulu": "US",
}


@dataclass(frozen=True, slots=True)
class DwdStation:
    """One DWD station that provides both measurement and MOSMIX data."""

    station_id: str
    name: str
    latitude: float
    longitude: float
    altitude: float | None = None


@dataclass(slots=True)
class AutoWeatherData:
    """Normalized coordinate weather from the automatic provider."""

    provider_domain: str
    fetched_at: datetime
    safety_source_key: str = ""
    available: bool = True
    timezone: str | None = None
    country: str | None = None
    temperature: float | None = None
    humidity: float | None = None
    condition: str | None = None
    precipitation: float | None = None
    wind_speed_kmh: float | None = None
    wind_gust_kmh: float | None = None
    hourly_forecast: list[dict[str, Any]] = field(default_factory=list)
    station_id: str | None = None
    station_name: str | None = None
    station_distance_km: float | None = None


@dataclass(slots=True)
class AutoWarningRecord:
    """One location-matched official warning."""

    warning_id: str
    provider_domain: str
    category: str  # civil | weather
    headline: str = ""
    description: str = ""
    instruction: str = ""
    event: str = ""
    severity: str = "unknown"
    msg_type: str = "Alert"
    effective: datetime | None = None
    expires: datetime | None = None
    evidence_at: datetime | None = None


@dataclass(slots=True)
class AutoWarningData:
    """Result of one automatic warning-provider refresh."""

    provider_domain: str
    fetched_at: datetime
    available: bool
    country: str | None
    safety_source_key: str = ""
    warnings: list[AutoWarningRecord] = field(default_factory=list)
    error: str | None = None
    coverage: str = "weather_only"
    source_availability: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class AutoProviderState:
    """Per-entry automatic provider cache."""

    location_key: tuple[float, float] | None = None
    weather: AutoWeatherData | None = None
    weather_attempted_at: datetime | None = None
    weather_available: bool = False
    warning: AutoWarningData | None = None
    warning_attempted_at: datetime | None = None
    nina_cache: dict[str, tuple[datetime, dict[str, Any] | None, Any]] = field(default_factory=dict)
    meteoalarm_cache: dict[str, tuple[datetime, str]] = field(default_factory=dict)
    dwd_station_index: list[DwdStation] | None = None
    dwd_station_index_at: datetime | None = None
    dwd_station: DwdStation | None = None


def weather_mode(entry: ConfigEntry) -> str:
    configured = entry.data.get(CONF_WEATHER_SOURCE_MODE)
    if configured is None:
        # Pre-v0.11 entries and lightweight unit-test fixtures have no explicit
        # source mode. Preserve their selected weather entity until migration
        # writes the new field instead of silently switching them to Auto.
        return (
            WEATHER_SOURCE_MANUAL
            if str(entry.data.get(CONF_WEATHER) or "").strip()
            else DEFAULT_WEATHER_SOURCE_MODE
        )
    value = str(configured)
    return value if value in {WEATHER_SOURCE_AUTO, WEATHER_SOURCE_MANUAL} else DEFAULT_WEATHER_SOURCE_MODE


def warning_mode(entry: ConfigEntry) -> str:
    configured = entry.data.get(CONF_WARNING_SOURCE_MODE)
    if configured is None:
        # Same compatibility rule for legacy warning selections. Real migrated
        # entries with an existing provider are explicitly upgraded to
        # auto_plus_manual; this branch keeps pre-migration/test callers stable.
        source = str(entry.data.get(CONF_WARNING_SOURCE) or "").strip()
        return (
            "manual"
            if source and source != WARNING_SOURCE_NONE
            else DEFAULT_WARNING_SOURCE_MODE
        )
    value = str(configured)
    return value if value in {WARNING_SOURCE_AUTO, "manual", WARNING_SOURCE_AUTO_PLUS_MANUAL} else DEFAULT_WARNING_SOURCE_MODE


def uses_auto_weather(entry: ConfigEntry) -> bool:
    return weather_mode(entry) == WEATHER_SOURCE_AUTO


def uses_auto_warning(entry: ConfigEntry) -> bool:
    return warning_mode(entry) in {WARNING_SOURCE_AUTO, WARNING_SOURCE_AUTO_PLUS_MANUAL}


def _bucket(hass: HomeAssistant) -> dict[str, AutoProviderState]:
    return hass.data.setdefault(DOMAIN, {}).setdefault(DATA_AUTO_PROVIDER_CACHE, {})


def _state(hass: HomeAssistant, entry: ConfigEntry) -> AutoProviderState:
    bucket = _bucket(hass)
    current = bucket.get(entry.entry_id)
    if isinstance(current, AutoProviderState):
        return current
    current = AutoProviderState()
    bucket[entry.entry_id] = current
    return current


def auto_weather_data(hass: HomeAssistant, entry: ConfigEntry) -> AutoWeatherData | None:
    return _state(hass, entry).weather


def auto_warning_data(hass: HomeAssistant, entry: ConfigEntry) -> AutoWarningData | None:
    return _state(hass, entry).warning


def auto_weather_available(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return _state(hass, entry).weather_available


def auto_weather_safety_key(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    state = _state(hass, entry)
    if state.weather is not None and state.weather.safety_source_key:
        return state.weather.safety_source_key
    if state.location_key is None:
        return None
    return f"auto_weather:{state.location_key[0]:.4f}:{state.location_key[1]:.4f}"


def clear_auto_provider_cache(hass: HomeAssistant, entry: ConfigEntry) -> None:
    domain_data = hass.data.get(DOMAIN)
    if not isinstance(domain_data, dict):
        return
    bucket = domain_data.get(DATA_AUTO_PROVIDER_CACHE)
    if isinstance(bucket, dict):
        bucket.pop(entry.entry_id, None)
        if not bucket:
            domain_data.pop(DATA_AUTO_PROVIDER_CACHE, None)


def _location_key(location: EffectiveLocation) -> tuple[float, float]:
    # ~100 m precision is enough to prevent GPS jitter from creating unique
    # provider cache keys while remaining far smaller than warning polygons.
    return (round(float(location.latitude), 3), round(float(location.longitude), 3))


def _safety_location_key(kind: str, location: EffectiveLocation) -> str:
    """Return a provider-independent safety identity for one accepted place.

    Persisted safety must survive Home Assistant/provider restarts at the same
    coordinate, but must never follow a vehicle to another place.  Provider
    names therefore deliberately do not participate in this key.
    """
    return f"auto_{kind}:{location.latitude:.4f}:{location.longitude:.4f}"


def _fresh(stamp: datetime | None, interval: timedelta, now: datetime) -> bool:
    if not isinstance(stamp, datetime):
        return False
    try:
        age = now - stamp
    except TypeError:
        return False
    return timedelta(0) <= age < interval


async def _get_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    async with session.get(url, params=params, headers=headers, timeout=_HTTP_TIMEOUT) as response:
        response.raise_for_status()
        return await response.json(content_type=None)


async def _get_text(
    session: aiohttp.ClientSession,
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> str:
    async with session.get(url, headers=headers, timeout=_HTTP_TIMEOUT) as response:
        response.raise_for_status()
        return await response.text()


async def _get_bytes(
    session: aiohttp.ClientSession,
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> bytes:
    async with session.get(url, headers=headers, timeout=_HTTP_TIMEOUT) as response:
        response.raise_for_status()
        return await response.read()


def _as_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _open_meteo_condition(code: Any) -> str | None:
    try:
        value = int(code)
    except (TypeError, ValueError):
        return None
    if value == 0:
        return "sunny"
    if value == 1:
        return "partlycloudy"
    if value in {2, 3}:
        return "cloudy"
    if value in {45, 48}:
        return "fog"
    if value in {51, 53, 55, 56, 57, 61, 63, 80, 81}:
        return "rainy"
    if value in {65, 82}:
        return "pouring"
    if value in {66, 67}:
        return "snowy-rainy"
    if value in {71, 73, 75, 77, 85, 86}:
        return "snowy"
    if value == 95:
        return "lightning-rainy"
    if value in {96, 99}:
        return "hail"
    return None


def _forecast_timezone(name: Any) -> ZoneInfo:
    if isinstance(name, str) and name:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            pass
    return ZoneInfo("UTC")


def _normalize_open_meteo_hourly(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return []
    times = hourly.get("time")
    temperatures = hourly.get("temperature_2m")
    if not isinstance(times, list) or not isinstance(temperatures, list):
        return []
    tz = _forecast_timezone(payload.get("timezone"))
    normalized: list[dict[str, Any]] = []
    for index, raw_time in enumerate(times[:36]):
        if index >= len(temperatures):
            break
        temp = _as_float(temperatures[index])
        if temp is None:
            continue
        try:
            stamp = datetime.fromisoformat(str(raw_time))
        except ValueError:
            continue
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=tz)
        item: dict[str, Any] = {"datetime": stamp, "temperature": temp}
        for source_key, target_key in (
            ("relative_humidity_2m", "humidity"),
            ("precipitation_probability", "precipitation_probability"),
            ("precipitation", "precipitation"),
            ("wind_speed_10m", "wind_speed"),
            ("wind_gusts_10m", "wind_gust_speed"),
        ):
            values = hourly.get(source_key)
            if isinstance(values, list) and index < len(values):
                value = _as_float(values[index])
                if value is not None:
                    item[target_key] = value
        codes = hourly.get("weather_code")
        if isinstance(codes, list) and index < len(codes):
            condition = _open_meteo_condition(codes[index])
            if condition:
                item["condition"] = condition
        normalized.append(item)
    return normalized


_DWD_STATION_LINE = re.compile(
    r"^([^ ]+)\s+([^ ]+)\s+(.+?[^ ])\s+(-?[0-9]+\.[0-9]+)\s+(-?[0-9]+\.[0-9]+)\s+(-?[0-9]+?)\s*$"
)
_DWD_MEASUREMENT_HREF = re.compile(
    r'''href=["']([^"']*?-BEOB\.csv)["']''', re.IGNORECASE
)
_DWD_FORECAST_HREF = re.compile(
    r'''href=["']([^"']+/)["']''', re.IGNORECASE
)


def _dwd_station_id_from_measurement_href(href: str) -> str | None:
    name = href.rsplit("/", 1)[-1]
    match = re.match(r"^(.*?)[_]*-BEOB\.csv$", name, re.IGNORECASE)
    if not match:
        return None
    station_id = match.group(1).strip()
    return station_id or None


def _dwd_catalog_coordinate(value: str, limit: int) -> float:
    """Convert MOSMIX DD.MM (degrees/minutes), preserving negative zero."""
    match = re.fullmatch(r"([+-]?)(\d+)\.(\d{2})", value.strip())
    if match is None:
        raise ValueError("invalid MOSMIX coordinate")
    sign, degrees, minutes = match.groups()
    degree, minute = int(degrees), int(minutes)
    if minute >= 60 or degree > limit or (degree == limit and minute):
        raise ValueError("MOSMIX coordinate out of range")
    return (-1 if sign == "-" else 1) * (degree + minute / 60)


def _parse_dwd_station_index(
    catalog_text: str, measurement_index: str, forecast_index: str
) -> list[DwdStation]:
    """Build a DWD station index from the official OpenData listings."""
    measurement_ids = {
        station_id
        for href in _DWD_MEASUREMENT_HREF.findall(measurement_index)
        if (station_id := _dwd_station_id_from_measurement_href(href))
    }
    forecast_ids = {
        href.rstrip("/").rsplit("/", 1)[-1]
        for href in _DWD_FORECAST_HREF.findall(forecast_index)
        if href.rstrip("/").rsplit("/", 1)[-1]
    }
    available = measurement_ids & forecast_ids
    result: list[DwdStation] = []
    for raw_line in catalog_text.splitlines():
        match = _DWD_STATION_LINE.match(raw_line.strip())
        if not match:
            continue
        station_id, _icao, name, lat, lon, altitude = match.groups()
        if station_id not in available:
            continue
        try:
            latitude = _dwd_catalog_coordinate(lat, 90)
            longitude = _dwd_catalog_coordinate(lon, 180)
        except ValueError:
            continue
        result.append(
            DwdStation(
                station_id=station_id,
                name=" ".join(name.split()),
                latitude=latitude,
                longitude=longitude,
                altitude=float(altitude),
            )
        )
    return result


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = p2 - p1
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))


async def _resolve_dwd_station(
    session: aiohttp.ClientSession,
    location: EffectiveLocation,
    state: AutoProviderState,
) -> tuple[DwdStation, float]:
    now = dt_util.utcnow()
    if state.dwd_station_index is None or not _fresh(
        state.dwd_station_index_at, timedelta(hours=24), now
    ):
        catalog_raw, measurement_raw, forecast_raw = await asyncio.gather(
            _get_bytes(session, _DWD_STATION_CATALOG),
            _get_text(session, _DWD_MEASUREMENT_INDEX),
            _get_text(session, _DWD_FORECAST_INDEX),
        )
        catalog_text = catalog_raw.decode("iso-8859-1", errors="replace")
        stations = _parse_dwd_station_index(
            catalog_text, measurement_raw, forecast_raw
        )
        if not stations:
            raise ValueError("DWD station index contains no usable stations")
        state.dwd_station_index = stations
        state.dwd_station_index_at = now

    assert state.dwd_station_index is not None
    station = min(
        state.dwd_station_index,
        key=lambda item: _distance_km(
            location.latitude, location.longitude, item.latitude, item.longitude
        ),
    )
    state.dwd_station = station
    return station, _distance_km(
        location.latitude, location.longitude, station.latitude, station.longitude
    )


def _dwd_current_condition(value: Any) -> str | None:
    try:
        code = int(round(float(str(value).replace(",", "."))))
    except (TypeError, ValueError):
        return None
    if code == 1:
        return "sunny"
    if code in {2, 3}:
        return "partlycloudy"
    if code == 4:
        return "cloudy"
    if code in {5, 6}:
        return "fog"
    if code in {7, 8, 18}:
        return "rainy"
    if code in {9, 19}:
        return "pouring"
    if code in {10, 11, 12, 13, 20, 21}:
        return "snowy-rainy"
    if code in {14, 15, 16, 22, 23, 24, 25}:
        return "snowy"
    if code == 17:
        return "hail"
    if code == 26:
        return "lightning"
    if code in {27, 28, 29, 30}:
        return "lightning-rainy"
    if code == 31:
        return "windy"
    return None


def _dwd_forecast_condition(value: Any) -> str | None:
    try:
        code = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if code == 0:
        return "sunny"
    if code in {1, 2}:
        return "partlycloudy"
    if code == 3:
        return "cloudy"
    if 4 <= code <= 12:
        return "fog"
    if code in {13, 17, 29, 95}:
        return "lightning"
    if code in {
        14, 15, 16, 20, 21, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
        60, 61, 62, 63, 80, 81, 82,
    }:
        return "rainy"
    if code in {18, 19}:
        return "windy"
    if code in {22, 70, 71, 72, 73, 74, 75, 85, 86}:
        return "snowy"
    if code in {23, 24, 66, 67, 68, 69, 83, 84}:
        return "snowy-rainy"
    if code in {87, 88, 89, 90, 96, 99}:
        return "hail"
    return None


def _parse_dwd_measurement(data: bytes) -> dict[str, str]:
    text = data.decode("iso-8859-1", errors="replace")
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    if len(rows) < 4:
        return {}
    columns = [item.strip() for item in rows[0].split(";")]
    result: dict[str, str] = {}
    for raw in rows[3:7]:
        fields = [item.strip() for item in raw.split(";")]
        for index in range(2, min(len(columns), len(fields))):
            value = fields[index]
            if value and value != "---" and columns[index] not in result:
                result[columns[index]] = value
    return result


def _rh_from_temp_dewpoint(temp_c: float | None, dew_c: float | None) -> float | None:
    if temp_c is None or dew_c is None:
        return None
    try:
        a, b = 17.625, 243.04
        numerator = math.exp((a * dew_c) / (b + dew_c))
        denominator = math.exp((a * temp_c) / (b + temp_c))
        return max(0.0, min(100.0, 100.0 * numerator / denominator))
    except (OverflowError, ZeroDivisionError):
        return None


def _parse_dwd_mosmix(data: bytes) -> list[dict[str, Any]]:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        name = next(
            (item for item in archive.namelist() if item.lower().endswith(".kml")),
            None,
        )
        if not name:
            return []
        root = ET.fromstring(archive.read(name))

    ns_dwd = "https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd"
    times: list[datetime] = []
    for node in root.findall(
        ".//{%s}ProductDefinition/{%s}ForecastTimeSteps/{%s}TimeStep"
        % (ns_dwd, ns_dwd, ns_dwd)
    ):
        if node.text and (stamp := _parse_dt(node.text)) is not None:
            times.append(stamp)

    values: dict[str, list[str]] = {}
    for forecast in root.findall(".//{%s}Forecast" % ns_dwd):
        element_name = forecast.attrib.get("{%s}elementName" % ns_dwd)
        value_node = forecast.find("{%s}value" % ns_dwd)
        if element_name and value_node is not None and value_node.text:
            values[element_name] = value_node.text.split()

    now = dt_util.utcnow().astimezone(timezone.utc)
    result: list[dict[str, Any]] = []
    for index, stamp in enumerate(times):
        stamp_utc = stamp.astimezone(timezone.utc)
        if stamp_utc < now - timedelta(hours=1) or stamp_utc > now + timedelta(hours=36):
            continue

        def number(
            key: str, *, factor: float = 1.0, offset: float = 0.0
        ) -> float | None:
            seq = values.get(key, [])
            if index >= len(seq) or seq[index] == "-":
                return None
            raw = _as_float(seq[index])
            return None if raw is None else raw * factor + offset

        temp = number("TTT", offset=-273.15)
        if temp is None:
            continue
        item: dict[str, Any] = {"datetime": stamp, "temperature": temp}
        dew = number("Td", offset=-273.15)
        humidity = _rh_from_temp_dewpoint(temp, dew)
        if humidity is not None:
            item["humidity"] = humidity
        precip = number("RR1c")
        if precip is not None:
            item["precipitation"] = precip
        probability = number("wwP")
        if probability is not None:
            item["precipitation_probability"] = probability
        wind = number("FF", factor=3.6)
        if wind is not None:
            item["wind_speed"] = wind
        gust = number("FX1", factor=3.6)
        if gust is not None:
            item["wind_gust_speed"] = gust
        ww = number("ww")
        condition = _dwd_forecast_condition(ww) if ww is not None else None
        if condition:
            item["condition"] = condition
        result.append(item)
    return result


async def _fetch_dwd_station_weather(
    session: aiohttp.ClientSession,
    location: EffectiveLocation,
    state: AutoProviderState,
) -> AutoWeatherData:
    station, distance = await _resolve_dwd_station(session, location, state)
    measurement_raw, forecast_raw = await asyncio.gather(
        _get_bytes(
            session, _DWD_MEASUREMENT_URL.format(station_id=station.station_id)
        ),
        _get_bytes(
            session, _DWD_FORECAST_URL.format(station_id=station.station_id)
        ),
    )
    measurement = _parse_dwd_measurement(measurement_raw)
    forecast = _parse_dwd_mosmix(forecast_raw)

    def measurement_number(key: str) -> float | None:
        raw = measurement.get(key)
        if raw is None:
            return None
        return _as_float(raw.replace(",", "."))

    temperature = measurement_number("dry_bulb_temperature_at_2_meter_above_ground")
    humidity = measurement_number("relative_humidity")
    condition = _dwd_current_condition(measurement.get("present_weather"))
    wind = measurement_number(
        "mean_wind_speed_during last_10_min_at_10_meters_above_ground"
    )
    gust = measurement_number("maximum_wind_speed_last_hour")

    first = forecast[0] if forecast else {}
    if temperature is None:
        temperature = _as_float(first.get("temperature"))
    if humidity is None:
        humidity = _as_float(first.get("humidity"))
    if condition is None:
        condition = str(first.get("condition") or "") or None
    if wind is None:
        wind = _as_float(first.get("wind_speed"))
    if gust is None:
        gust = _as_float(first.get("wind_gust_speed"))

    return AutoWeatherData(
        provider_domain="dwd_station",
        fetched_at=dt_util.utcnow(),
        safety_source_key=_safety_location_key("weather", location),
        timezone="Europe/Berlin",
        country="DE",
        temperature=temperature,
        humidity=humidity,
        condition=condition,
        precipitation=_as_float(first.get("precipitation")) or 0.0,
        wind_speed_kmh=wind,
        wind_gust_kmh=gust,
        hourly_forecast=forecast,
        station_id=station.station_id,
        station_name=station.name,
        station_distance_km=distance,
    )


async def _fetch_auto_weather(
    session: aiohttp.ClientSession,
    location: EffectiveLocation,
    country_hint: str | None,
    state: AutoProviderState | None = None,
) -> AutoWeatherData:
    country = str(country_hint or "").upper() or None
    if country == "DE" and state is not None:
        try:
            return await _fetch_dwd_station_weather(session, location, state)
        except Exception as exc:  # noqa: BLE001 - DWD station service has a safe fallback
            _LOGGER.debug("DWD station weather unavailable; using ICON fallback: %s", exc)

    endpoint = _OPEN_METEO_DWD if country == "DE" else _OPEN_METEO_FORECAST
    provider = "dwd_icon" if country == "DE" else "open_meteo"
    params: dict[str, Any] = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "current": ",".join((
            "temperature_2m", "relative_humidity_2m", "precipitation", "rain",
            "showers", "weather_code", "wind_speed_10m", "wind_gusts_10m",
        )),
        "hourly": ",".join((
            "temperature_2m", "relative_humidity_2m", "precipitation_probability",
            "precipitation", "weather_code", "wind_speed_10m", "wind_gusts_10m",
        )),
        "forecast_hours": 36,
        "timezone": "auto",
        "wind_speed_unit": "kmh",
    }
    if location.elevation is not None:
        params["elevation"] = location.elevation
    payload = await _get_json(session, endpoint, params=params)
    if not isinstance(payload, dict):
        raise ValueError("automatic weather provider returned a non-object response")

    timezone_name = str(payload.get("timezone") or "") or None
    resolved_country = country or _TIMEZONE_COUNTRY.get(str(timezone_name or ""))

    # A mobile tracker intentionally has no static country hint.  Resolve its
    # country from Open-Meteo's coordinate timezone first and, when that puts
    # the effective location in Germany, immediately switch the same refresh to
    # the DWD ICON endpoint.  Otherwise a German camper would stay on the
    # generic worldwide model forever simply because hass.config.country still
    # belongs to the stationary Home location.
    if country is None and resolved_country == "DE":
        if state is not None:
            try:
                return await _fetch_dwd_station_weather(session, location, state)
            except Exception as exc:  # noqa: BLE001 - fall back to the DWD ICON coordinate model
                _LOGGER.debug("DWD station weather unavailable for mobile location; using ICON fallback: %s", exc)
        if endpoint != _OPEN_METEO_DWD:
            payload = await _get_json(session, _OPEN_METEO_DWD, params=params)
            if not isinstance(payload, dict):
                raise ValueError("DWD automatic weather provider returned a non-object response")
            provider = "dwd_icon"
            timezone_name = str(payload.get("timezone") or timezone_name or "") or None
            resolved_country = "DE"

    current = payload.get("current")
    if not isinstance(current, dict):
        current = {}
    precipitation = sum(
        value or 0.0
        for value in (
            _as_float(current.get("rain")),
            _as_float(current.get("showers")),
        )
    )
    if precipitation <= 0:
        precipitation = _as_float(current.get("precipitation")) or 0.0
    return AutoWeatherData(
        provider_domain=provider,
        fetched_at=dt_util.utcnow(),
        safety_source_key=_safety_location_key("weather", location),
        timezone=timezone_name,
        country=resolved_country,
        temperature=_as_float(current.get("temperature_2m")),
        humidity=_as_float(current.get("relative_humidity_2m")),
        condition=_open_meteo_condition(current.get("weather_code")),
        precipitation=precipitation,
        wind_speed_kmh=_as_float(current.get("wind_speed_10m")),
        wind_gust_kmh=_as_float(current.get("wind_gusts_10m")),
        hourly_forecast=_normalize_open_meteo_hourly(payload),
    )


def _point_in_ring(lat: float, lon: float, ring: list[Any], *, geojson: bool) -> bool:
    points: list[tuple[float, float]] = []
    for point in ring:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        try:
            if geojson:
                px, py = float(point[0]), float(point[1])  # lon, lat
            else:
                py, px = float(point[0]), float(point[1])  # lat, lon (CAP)
        except (TypeError, ValueError):
            continue
        points.append((px, py))
    if len(points) < 3:
        return False
    inside = False
    j = len(points) - 1
    for i, (xi, yi) in enumerate(points):
        xj, yj = points[j]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _point_in_polygon(lat: float, lon: float, rings: Any, *, geojson: bool) -> bool:
    if not isinstance(rings, list) or not rings:
        return False
    if not _point_in_ring(lat, lon, rings[0], geojson=geojson):
        return False
    return not any(
        _point_in_ring(lat, lon, hole, geojson=geojson)
        for hole in rings[1:]
        if isinstance(hole, list)
    )


def _geojson_contains_point(obj: Any, lat: float, lon: float) -> bool:
    if not isinstance(obj, dict):
        return False
    kind = str(obj.get("type") or "")
    if kind == "Feature":
        return _geojson_contains_point(obj.get("geometry"), lat, lon)
    if kind == "FeatureCollection":
        return any(_geojson_contains_point(item, lat, lon) for item in obj.get("features", []))
    if kind == "GeometryCollection":
        return any(_geojson_contains_point(item, lat, lon) for item in obj.get("geometries", []))
    coords = obj.get("coordinates")
    if kind == "Polygon":
        return _point_in_polygon(lat, lon, coords, geojson=True)
    if kind == "MultiPolygon" and isinstance(coords, list):
        return any(_point_in_polygon(lat, lon, polygon, geojson=True) for polygon in coords)
    return False


def _iter_warning_texts(payload: Any) -> list[dict[str, Any]]:
    """Return CAP-like info blocks from nested NINA detail JSON."""
    found: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        info = payload.get("info")
        if isinstance(info, list):
            found.extend(item for item in info if isinstance(item, dict))
        elif isinstance(info, dict):
            found.append(info)
        for value in payload.values():
            if isinstance(value, (dict, list)):
                found.extend(_iter_warning_texts(value))
    elif isinstance(payload, list):
        for value in payload:
            if isinstance(value, (dict, list)):
                found.extend(_iter_warning_texts(value))
    # Keep order but deduplicate objects repeated through wrapper structures.
    unique: list[dict[str, Any]] = []
    seen: set[int] = set()
    for item in found:
        marker = id(item)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)
    return unique


def _pick_info(payload: dict[str, Any]) -> dict[str, Any]:
    infos = _iter_warning_texts(payload)
    if not infos:
        return payload
    for info in infos:
        language = str(info.get("language") or "").lower()
        if language.startswith("de"):
            return info
    return infos[0]


def _nina_parameter_text(info: dict[str, Any], *names: str) -> str:
    wanted = {name.lower() for name in names}
    params = info.get("parameter")
    if not isinstance(params, list):
        return ""
    values: list[str] = []
    for item in params:
        if not isinstance(item, dict):
            continue
        key = str(item.get("valueName") or item.get("name") or "").strip().lower()
        if key not in wanted:
            continue
        value = item.get("value")
        if isinstance(value, list):
            values.extend(str(part).strip() for part in value if str(part).strip())
        elif value is not None and str(value).strip():
            values.append(str(value).strip())
    return " ".join(values)


def _nina_record(
    identifier: str, detail: dict[str, Any], *, source: str = "mowas"
) -> AutoWarningRecord:
    info = _pick_info(detail)
    instruction = str(info.get("instruction") or detail.get("instruction") or "").strip()
    if not instruction:
        instruction = _nina_parameter_text(
            info, "instructionText", "recommendedActions", "recommended_actions"
        )
    return AutoWarningRecord(
        warning_id=identifier,
        provider_domain=f"nina_auto_{source}",
        category="weather" if source == "dwd" else "civil",
        headline=str(info.get("headline") or detail.get("headline") or "").strip(),
        description=str(info.get("description") or detail.get("description") or "").strip(),
        instruction=instruction,
        event=str(info.get("event") or detail.get("event") or "").strip(),
        severity=str(info.get("severity") or detail.get("severity") or "unknown"),
        msg_type=str(detail.get("msgType") or info.get("msgType") or "Alert"),
        effective=_parse_dt(info.get("effective") or info.get("onset") or detail.get("effective")),
        expires=_parse_dt(info.get("expires") or detail.get("expires")),
        evidence_at=_parse_dt(detail.get("sent") or info.get("sent")) or dt_util.utcnow(),
    )


async def _fetch_nina_warnings(
    session: aiohttp.ClientSession,
    location: EffectiveLocation,
    state: AutoProviderState,
) -> AutoWarningData:
    now = dt_util.utcnow()
    # NINA/warnung.bund.de combines civil-protection and official warning
    # sources. DWD is normalized as weather (soft severity semantics), while
    # flood/police/civil sources can create a hard lock only from an explicit
    # close/ventilation instruction.
    endpoints = ("mowas", "katwarn", "biwapp", "dwd", "lhp", "police")
    responses = await asyncio.gather(
        *(_get_json(session, f"{_NINA_BASE}/{name}/mapData.json") for name in endpoints),
        return_exceptions=True,
    )
    if all(isinstance(item, Exception) for item in responses):
        raise RuntimeError("all NINA map-data endpoints failed")
    candidates: dict[str, tuple[str, str, Any]] = {}
    source_availability = {
        f"nina_auto_{source}": isinstance(response, list)
        for source, response in zip(endpoints, responses, strict=True)
    }
    for source, response in zip(endpoints, responses, strict=True):
        if not isinstance(response, list):
            continue
        for item in response:
            if not isinstance(item, dict):
                continue
            identifier = str(item.get("id") or "").strip()
            if not identifier:
                continue
            candidates[identifier] = (source, str(item.get("version") or ""), item)

    # A nationwide NINA map can contain many simultaneous warnings.  Limit
    # detail/GeoJSON fetches so the first uncached refresh does not create a
    # burst of hundreds of concurrent HTTP requests.  Cached revisions bypass
    # the semaphore entirely.
    detail_limit = asyncio.Semaphore(8)

    async def resolve(
        identifier: str, source: str, version: str
    ) -> AutoWarningRecord | None:
        cache_key = f"{source}:{identifier}:{version}"
        cached = state.nina_cache.get(cache_key)
        if cached and _fresh(cached[0], timedelta(minutes=30), now):
            detail, geometry = cached[1], cached[2]
        else:
            async with detail_limit:
                detail_result, geometry_result = await asyncio.gather(
                    _get_json(session, f"{_NINA_BASE}/warnings/{identifier}.json"),
                    _get_json(session, f"{_NINA_BASE}/warnings/{identifier}.geojson"),
                    return_exceptions=True,
                )
            detail = detail_result if isinstance(detail_result, dict) else None
            geometry = None if isinstance(geometry_result, Exception) else geometry_result
            if detail is not None and isinstance(geometry, dict):
                state.nina_cache[cache_key] = (now, detail, geometry)
        if not isinstance(geometry, dict) or geometry.get("type") not in {
            "Feature", "FeatureCollection", "GeometryCollection", "Polygon", "MultiPolygon"
        }:
            source_availability[f"nina_auto_{source}"] = False
            return None
        if not _geojson_contains_point(geometry, location.latitude, location.longitude):
            return None
        if detail is None:
            source_availability[f"nina_auto_{source}"] = False
            return None
        if str(detail.get("status") or "Actual").lower() != "actual":
            return None
        try:
            return _nina_record(identifier, detail, source=source)
        except (ValueError, TypeError):
            source_availability[f"nina_auto_{source}"] = False
            return None

    records = await asyncio.gather(
        *(
            resolve(identifier, source, version)
            for identifier, (source, version, _item) in candidates.items()
        ),
        return_exceptions=True,
    )
    warnings = [item for item in records if isinstance(item, AutoWarningRecord)]
    # Drop old cache revisions once the active map no longer references them.
    active_prefixes = {
        f"{source}:{identifier}:"
        for identifier, (source, _version, _item) in candidates.items()
    }
    state.nina_cache = {
        key: value
        for key, value in state.nina_cache.items()
        if any(key.startswith(prefix) for prefix in active_prefixes)
        and _fresh(value[0], timedelta(hours=2), now)
    }
    return AutoWarningData(
        provider_domain="nina_auto",
        fetched_at=now,
        available=all(source_availability.values()) and not any(isinstance(item, Exception) for item in records),
        country="DE",
        safety_source_key=_safety_location_key("warning", location),
        warnings=warnings,
        error="nina_partial_failure" if not all(source_availability.values()) or any(isinstance(item, Exception) for item in records) else None,
        coverage="civil_and_weather",
        source_availability=source_availability,
    )


def _nws_record(feature: dict[str, Any]) -> AutoWarningRecord | None:
    props = feature.get("properties")
    if not isinstance(props, dict):
        return None
    identifier = str(props.get("id") or feature.get("id") or "").strip()
    if not identifier:
        return None
    return AutoWarningRecord(
        warning_id=identifier,
        provider_domain="nws_auto",
        category="weather",
        headline=str(props.get("headline") or "").strip(),
        description=str(props.get("description") or "").strip(),
        instruction=str(props.get("instruction") or "").strip(),
        event=str(props.get("event") or "").strip(),
        severity=str(props.get("severity") or "unknown"),
        msg_type=str(props.get("messageType") or "Alert"),
        effective=_parse_dt(props.get("effective") or props.get("onset")),
        expires=_parse_dt(props.get("expires") or props.get("ends")),
        evidence_at=_parse_dt(props.get("sent")) or dt_util.utcnow(),
    )


async def _fetch_nws_warnings(
    session: aiohttp.ClientSession, location: EffectiveLocation
) -> AutoWarningData:
    payload = await _get_json(
        session,
        _NWS_ALERTS,
        params={"point": f"{location.latitude:.5f},{location.longitude:.5f}"},
        headers={"User-Agent": "HomeAssistant-Lueftungsassistent/0.11.0"},
    )
    features = payload.get("features") if isinstance(payload, dict) else None
    warnings: list[AutoWarningRecord] = []
    if isinstance(features, list):
        for feature in features:
            if isinstance(feature, dict) and (record := _nws_record(feature)) is not None:
                warnings.append(record)
    return AutoWarningData(
        provider_domain="nws_auto",
        fetched_at=dt_util.utcnow(),
        available=True,
        country="US",
        safety_source_key=_safety_location_key("warning", location),
        warnings=warnings,
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first_text(element: ET.Element, *names: str) -> str:
    wanted = set(names)
    for child in element.iter():
        if _local_name(child.tag) in wanted and child.text:
            text = child.text.strip()
            if text:
                return text
    return ""


def _cap_polygon_contains(text: str, lat: float, lon: float) -> bool:
    ring = []
    try:
        for pair in text.replace(";", " ").split():
            parts = pair.split(",")
            if len(parts) != 2:
                raise ValueError("CAP polygon coordinate pair required")
            point = [float(parts[0]), float(parts[1])]
            if not all(math.isfinite(value) for value in point) or not -90 <= point[0] <= 90 or not -180 <= point[1] <= 180:
                raise ValueError("CAP polygon coordinate out of range")
            ring.append(point)
        if len(ring) < 4 or ring[0] != ring[-1]:
            raise ValueError("CAP polygon must be closed")
    except ValueError as exc:
        raise UnresolvedWarningArea("invalid CAP polygon") from exc
    return _point_in_ring(lat, lon, ring, geojson=False)


def _cap_circle_contains(text: str, lat: float, lon: float) -> bool:
    try:
        parts = text.split()
        center = parts[0].split(",")
        if len(parts) != 2 or len(center) != 2:
            raise ValueError("CAP circle coordinate/radius required")
        clat, clon, radius = float(center[0]), float(center[1]), float(parts[1])
        if not all(math.isfinite(value) for value in (clat, clon, radius)) or not -90 <= clat <= 90 or not -180 <= clon <= 180 or radius < 0:
            raise ValueError("CAP circle values out of range")
    except (IndexError, ValueError) as exc:
        raise UnresolvedWarningArea("invalid CAP circle") from exc
    dy = (lat - clat) * 111.32
    dx = (lon - clon) * 111.32 * math.cos(math.radians((lat + clat) / 2))
    return math.hypot(dx, dy) <= radius


def _cap_preferred_info(element: ET.Element) -> ET.Element:
    """Prefer an English CAP info block for provider-neutral safety text.

    MeteoAlarm member CAP documents can contain several localized ``info``
    blocks. The hard-close parser intentionally does not machine-translate
    safety instructions, so prefer an available English block and otherwise
    keep the authority's first original-language block.
    """
    infos = [child for child in element.iter() if _local_name(child.tag) == "info"]
    if not infos:
        return element
    for info in infos:
        language = _first_text(info, "language").lower()
        if language.startswith("en"):
            return info
    return infos[0]


class UnresolvedWarningArea(ValueError):
    """An active warning cannot be safely assigned to a location."""


def _cap_area_matches(element: ET.Element, lat: float, lon: float) -> bool:
    unknown = False
    areas = [item for item in element.iter() if _local_name(item.tag) == "area"] or [element]
    for area in areas:
        polygons = [str(item.text or "") for item in area.iter() if _local_name(item.tag) == "polygon"]
        circles = [str(item.text or "") for item in area.iter() if _local_name(item.tag) == "circle"]
        # An explicit footprint is authoritative over the broader region code.
        if polygons or circles:
            if any(_cap_polygon_contains(item, lat, lon) for item in polygons) or any(
                _cap_circle_contains(item, lat, lon) for item in circles
            ):
                return True
            continue
        codes = [item for item in area.iter() if _local_name(item.tag) == "geocode"]
        if not codes:
            unknown = True
        for code in codes:
            geometry = geocode_geometry(_first_text(code, "valueName"), _first_text(code, "value"))
            if geometry is None:
                unknown = True
            elif _geojson_contains_point(geometry, lat, lon):
                return True
    if unknown:
        raise UnresolvedWarningArea("unresolved CAP geocode/area")
    return False


def _cap_element_record(
    element: ET.Element, *, provider: str, lat: float, lon: float,
) -> AutoWarningRecord | None:
    if _first_text(element, "status").lower() not in {"", "actual"}:
        return None
    if _first_text(element, "scope").lower() not in {"", "public"}:
        return None
    identifier = _first_text(element, "identifier", "id")
    if not identifier:
        return None
    info = _cap_preferred_info(element)
    expires = _parse_dt(_first_text(info, "expires"))
    if expires is not None and expires <= dt_util.utcnow():
        return None
    if not _cap_area_matches(info, lat, lon):
        return None
    return AutoWarningRecord(
        warning_id=identifier, provider_domain=provider, category="weather",
        headline=_first_text(info, "headline", "title"),
        description=_first_text(info, "description", "summary"),
        instruction=_first_text(info, "instruction"), event=_first_text(info, "event"),
        severity=_first_text(info, "severity") or "unknown",
        msg_type=_first_text(element, "msgType") or "Alert",
        effective=_parse_dt(_first_text(info, "onset") or _first_text(info, "effective")), expires=expires,
        evidence_at=_parse_dt(_first_text(element, "sent", "updated")) or dt_util.utcnow(),
    )


def _parse_atom_entries(text: str, lat: float, lon: float) -> tuple[list[AutoWarningRecord], list[str], int]:
    root = ET.fromstring(text)
    records: list[AutoWarningRecord] = []
    cap_links: list[str] = []
    unresolved = 0
    for entry in root.iter():
        if _local_name(entry.tag) != "entry":
            continue
        unknown = False
        try:
            record = _cap_element_record(entry, provider="meteoalarm_auto", lat=lat, lon=lon)
        except UnresolvedWarningArea:
            record, unknown = None, True
        # Linked CAP contains full instructions/localizations missing in Atom.
        links = [str(item.attrib.get("href") or "").strip() for item in entry.iter()
                 if _local_name(item.tag) == "link" and (
                     "cap" in str(item.attrib.get("type") or "").lower()
                     or "cap" in str(item.attrib.get("rel") or "").lower()
                     or str(item.attrib.get("href") or "").lower().endswith((".xml", ".cap")))]
        if (record is not None or unknown) and links:
            cap_links.append(links[0])
        elif record is not None:
            records.append(record)
        elif unknown:
            unresolved += 1
    return records, list(dict.fromkeys(cap_links)), unresolved


def _parse_cap_document(text: str, lat: float, lon: float) -> AutoWarningRecord | None:
    root = ET.fromstring(text)
    return _cap_element_record(root, provider="meteoalarm_auto", lat=lat, lon=lon)


def _safe_meteoalarm_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (
        host == "meteoalarm.org" or host.endswith(".meteoalarm.org")
    )


async def _fetch_meteoalarm_warnings(
    hass: HomeAssistant, session: aiohttp.ClientSession,
    location: EffectiveLocation, country: str, state: AutoProviderState,
) -> AutoWarningData:
    slug = _METEOALARM_COUNTRIES[country]
    text = await _get_text(session, _METEOALARM_FEED.format(slug=slug))
    records, links, unresolved = await hass.async_add_executor_job(
        _parse_atom_entries, text, location.latitude, location.longitude
    )
    now = dt_util.utcnow()
    limit = asyncio.Semaphore(4)

    async def resolve(url: str) -> AutoWarningRecord | None:
        if not _safe_meteoalarm_url(url):
            raise UnresolvedWarningArea("untrusted CAP link")
        cached = state.meteoalarm_cache.get(url)
        if cached and _fresh(cached[0], timedelta(minutes=5), now):
            cap_text = cached[1]
        else:
            async with limit:
                cap_text = await _get_text(session, url)
            # Cache raw CAP, never a location-filtered record or a failed fetch.
            state.meteoalarm_cache[url] = (now, cap_text)
        return await hass.async_add_executor_job(
            _parse_cap_document, cap_text, location.latitude, location.longitude
        )

    if links:
        linked = await asyncio.gather(*(resolve(url) for url in links), return_exceptions=True)
        records.extend(item for item in linked if isinstance(item, AutoWarningRecord))
        unresolved += sum(isinstance(item, Exception) for item in linked)
    state.meteoalarm_cache = {
        key: value for key, value in state.meteoalarm_cache.items()
        if _fresh(value[0], timedelta(hours=2), now)
    }
    unique = {record.warning_id: record for record in records}
    return AutoWarningData(
        provider_domain="meteoalarm_auto", fetched_at=now, available=not unresolved,
        country=country, safety_source_key=_safety_location_key("warning", location),
        warnings=list(unique.values()), error="unresolved_warning_areas" if unresolved else None,
    )


async def _fetch_auto_warning(
    hass: HomeAssistant,
    session: aiohttp.ClientSession,
    location: EffectiveLocation,
    country: str | None,
    state: AutoProviderState,
) -> AutoWarningData:
    normalized = str(country or "").upper() or None
    if normalized == "DE":
        result = await _fetch_nina_warnings(session, location, state)
        result.coverage = "civil_and_weather"
        return result
    if normalized == "US":
        return await _fetch_nws_warnings(session, location)
    if normalized in _METEOALARM_COUNTRIES:
        from .national_warnings import CIVIL_PROVIDERS, combine_warning_sources
        if normalized in CIVIL_PROVIDERS:
            return await combine_warning_sources(
                hass, session, location, normalized,
                _fetch_meteoalarm_warnings(hass, session, location, normalized, state),
            )
        return await _fetch_meteoalarm_warnings(
            hass, session, location, normalized, state
        )
    if normalized is None:
        # Especially after a mobile/HA restart, country resolution may depend on
        # the weather request.  Failure to resolve the country is an outage /
        # unknown state, not proof that no warning applies.  This distinction is
        # important for bounded persistence of an already confirmed hard lock.
        return AutoWarningData(
            provider_domain="auto_warning_unresolved",
            fetched_at=dt_util.utcnow(),
            available=False,
            country=None,
            safety_source_key=_safety_location_key("warning", location),
            warnings=[],
            error="country_unresolved",
            coverage="none",
        )

    # Unsupported is a known state, not a provider outage. It must not claim
    # coverage, but it also must not leave a hard lock from a previous country.
    return AutoWarningData(
        provider_domain="auto_warning_unsupported",
        fetched_at=dt_util.utcnow(),
        available=True,
        country=normalized,
        safety_source_key=_safety_location_key("warning", location),
        warnings=[],
        error="unsupported_country",
        coverage="none",
    )


async def async_refresh_auto_providers(
    hass: HomeAssistant,
    entry: ConfigEntry,
    location: EffectiveLocation,
    *,
    force: bool = False,
) -> None:
    """Refresh only the automatic sources enabled for this config entry."""
    want_weather = uses_auto_weather(entry)
    want_warning = uses_auto_warning(entry)
    if not want_weather and not want_warning:
        return

    state = _state(hass, entry)
    now = dt_util.utcnow()
    if not location.available:
        # No new evidence may be generated from a vehicle's lost position.
        # The existing bounded safety store handles the previous confirmed lock.
        state.weather = None
        state.weather_available = False
        previous = state.warning
        state.warning = AutoWarningData(
            provider_domain=previous.provider_domain if previous else "auto_warning",
            fetched_at=previous.fetched_at if previous else now,
            available=False,
            country=previous.country if previous else None,
            safety_source_key=previous.safety_source_key if previous else _safety_location_key("warning", location),
            error="location_stale",
            coverage=previous.coverage if previous else "none",
            source_availability={domain: False for domain in previous.source_availability} if previous else {},
        )
        state.weather_attempted_at = None
        state.warning_attempted_at = None
        return
    key = _location_key(location)
    changed_location = state.location_key != key
    if changed_location:
        state.location_key = key
        # Never reuse successful data from a different physical location.
        state.weather = None
        state.weather_available = False
        state.warning = None
        state.weather_attempted_at = None
        state.warning_attempted_at = None
        state.nina_cache.clear()
        state.meteoalarm_cache.clear()
        state.dwd_station = None

    # Timezone borders are not national borders (e.g. Canada/US or Balkans).
    # Resolve the accepted point locally, also after moving HA's Home location.
    country = await hass.async_add_executor_job(
        coordinate_country, location.latitude, location.longitude
    )
    location = replace(location, country=country)
    session = async_get_clientsession(hass)
    if want_weather and (
        force
        or changed_location
        or not _fresh(state.weather_attempted_at, AUTO_WEATHER_REFRESH_INTERVAL, now)
    ):
        state.weather_attempted_at = now
        country_hint = str(location.country or "").upper() or None
        try:
            state.weather = await _fetch_auto_weather(session, location, country_hint, state)
            state.weather_available = True
        except Exception as exc:  # noqa: BLE001 - network must never break ventilation logic
            _LOGGER.debug("Automatic weather refresh failed for %s: %s", entry.title, exc)
            state.weather_available = False
            # Preserve only same-location successful data within a bounded age.
            if state.weather is not None and not _fresh(
                state.weather.fetched_at, AUTO_PROVIDER_STALE_MAX_AGE, now
            ):
                state.weather = None

    if want_warning and (
        force
        or changed_location
        or not _fresh(state.warning_attempted_at, AUTO_WARNING_REFRESH_INTERVAL, now)
    ):
        state.warning_attempted_at = now
        country = location.country
        try:
            state.warning = await _fetch_auto_warning(
                hass, session, location, country, state
            )
        except Exception as exc:  # noqa: BLE001 - warning outages are fail-safe/deferred
            _LOGGER.debug("Automatic warning refresh failed for %s: %s", entry.title, exc)
            previous = state.warning
            if previous is None or not _fresh(
                previous.fetched_at, AUTO_PROVIDER_STALE_MAX_AGE, now
            ):
                state.warning = AutoWarningData(
                    provider_domain=(previous.provider_domain if previous else "auto_warning"),
                    fetched_at=(previous.fetched_at if previous else now),
                    available=False,
                    country=(previous.country if previous else country),
                    safety_source_key=(previous.safety_source_key if previous else _safety_location_key("warning", location)),
                    warnings=[],
                    error=str(exc),
                    coverage=previous.coverage if previous else "none",
                    source_availability={domain: False for domain in previous.source_availability} if previous else {},
                )
            else:
                # Keep the last successful warning list, but mark availability
                # unknown so persistent safety cannot extend its evidence forever.
                state.warning = AutoWarningData(
                    provider_domain=previous.provider_domain,
                    fetched_at=previous.fetched_at,
                    available=False,
                    country=previous.country,
                    safety_source_key=previous.safety_source_key,
                    warnings=list(previous.warnings),
                    error=str(exc),
                    coverage=previous.coverage,
                    source_availability={domain: False for domain in previous.source_availability},
                )

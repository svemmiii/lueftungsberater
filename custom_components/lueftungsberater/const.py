"""Constants for Lüftungsberater."""

from datetime import timedelta

DOMAIN = "lueftungsberater"
PLATFORMS = ["sensor", "binary_sensor"]
SUBENTRY_TYPE_ROOM = "room"

CONF_ENTRY_KIND = "entry_kind"
ENTRY_KIND_LOCAL = "local"
ENTRY_KIND_REMOTE = "remote"
CONF_INSTANCE_NAME = "instance_name"

CONF_OUTDOOR_TEMP = "outdoor_temperature"
CONF_OUTDOOR_HUMIDITY = "outdoor_humidity"
CONF_WEATHER = "weather_entity"
CONF_WEATHER_DANGER = "weather_danger_entity"
CONF_WEATHER_REASON = "weather_reason_entity"
CONF_NINA_STATUS = "nina_status_entity"
CONF_RAIN_NOW = "rain_now_entity"
CONF_RAIN_SOON = "rain_soon_entity"

CONF_WARNING_SOURCE = "warning_source"
CONF_MANUAL_OUTDOOR = "manual_outdoor"
WARNING_SOURCE_NONE = "none"

CONF_REMOTE_HOST = "remote_host"
CONF_REMOTE_PORT = "remote_port"
CONF_REMOTE_TOKEN = "remote_access_token"
CONF_REMOTE_USE_SSL = "remote_use_ssl"
DEFAULT_REMOTE_PORT = 8123
REMOTE_UPDATE_INTERVAL = timedelta(seconds=30)
REMOTE_OFFLINE_GRACE = timedelta(minutes=3)
REMOTE_PROTOCOL_VERSION = 1

CONF_ROOM_NAME = "room_name"
CONF_INDOOR_TEMP = "indoor_temperature"
CONF_INDOOR_HUMIDITY = "indoor_humidity"
CONF_CO2 = "co2_entity"
CONF_WINDOWS = "window_entities"
CONF_CLIMATE = "climate_entity"
CONF_TARGET_TEMP = "target_temperature"

# Kept only so old v0.1/v0.2 config subentries remain readable.
# v0.3 no longer asks for or uses this external helper.
CONF_HOURS_SINCE_AIRING = "hours_since_airing_entity"

DEFAULT_TARGET_TEMP = 21.0
MIN_CONFIRMED_AIRING = timedelta(minutes=5)
CO2_GRACE_PERIOD = timedelta(seconds=60)

DATA_TRACKERS = "airing_trackers"
DATA_CO2_TRACKERS = "co2_trackers"
DATA_COORDINATORS = "room_coordinators"
DATA_REMOTE_COORDINATORS = "remote_coordinators"
DATA_API_REGISTERED = "api_registered"
STORAGE_VERSION = 1


def entry_kind(entry) -> str:
    """Return the config-entry kind while keeping pre-v0.6.10 entries local."""
    return entry.data.get(CONF_ENTRY_KIND, ENTRY_KIND_LOCAL)

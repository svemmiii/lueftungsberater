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

CONF_NOTIFY_TARGET = "notify_target"
CONF_NOTIFY_MOBILE_SERVICE = "notify_mobile_service"
CONF_NOTIFY_TRIGGERS = "notify_triggers"
CONF_NOTIFY_CAUTION_VIBRATION = "notify_caution_vibration"
CONF_NOTIFY_DANGER_VIBRATION = "notify_danger_vibration"
CONF_NOTIFY_CRITICAL_BYPASS = "notify_critical_bypass"

NOTIFY_TRIGGER_AIRING_RECOMMENDED = "airing_recommended"
NOTIFY_TRIGGER_AIRING_FINISHED = "airing_finished"
NOTIFY_TRIGGER_AIR_DANGER = "air_danger"
NOTIFY_TRIGGER_AIR_CAUTION = "air_caution"
NOTIFY_TRIGGER_WEATHER_DANGER = "weather_danger"
NOTIFY_TRIGGER_WEATHER_CAUTION = "weather_caution"
DEFAULT_NOTIFY_TRIGGERS = [
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_WEATHER_DANGER,
]

NOTIFY_VIBRATION_OFF = "off"
NOTIFY_VIBRATION_GENTLE = "gentle"
NOTIFY_VIBRATION_NORMAL = "normal"
NOTIFY_VIBRATION_STRONG = "strong"
DEFAULT_NOTIFY_CAUTION_VIBRATION = NOTIFY_VIBRATION_OFF
DEFAULT_NOTIFY_DANGER_VIBRATION = NOTIFY_VIBRATION_STRONG
DEFAULT_NOTIFY_CRITICAL_BYPASS = False

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
CONF_SURFACE_TEMP = "surface_temperature"

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
DATA_NOTIFICATION_STATE = "notification_state"
STORAGE_VERSION = 1


def entry_kind(entry) -> str:
    """Return the config-entry kind while keeping pre-v0.6.10 entries local."""
    return entry.data.get(CONF_ENTRY_KIND, ENTRY_KIND_LOCAL)

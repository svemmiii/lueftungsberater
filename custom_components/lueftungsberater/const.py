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
CONF_OUTDOOR_CO2 = "outdoor_co2"
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
CONF_NOTIFY_TRIGGERS = "notify_triggers"

CONF_DISPLAY_MODE = "display_mode"
DISPLAY_MODE_VENTILATION = "ventilation"
DISPLAY_MODE_ROOM_AIR = "room_air"
DEFAULT_DISPLAY_MODE = DISPLAY_MODE_ROOM_AIR

# Removed with v0.6.20. Kept as one private migration list only so existing
# config entries can be cleaned without breaking setup after the update.
LEGACY_NOTIFY_KEYS = (
    "notify_mobile_service",
    "notify_caution_vibration",
    "notify_danger_vibration",
    "notify_critical_bypass",
)

NOTIFY_TRIGGER_AIRING_RECOMMENDED = "airing_recommended"
NOTIFY_TRIGGER_AIRING_FINISHED = "airing_finished"
NOTIFY_TRIGGER_AIR_DANGER = "air_danger"
NOTIFY_TRIGGER_AIR_CAUTION = "air_caution"
NOTIFY_TRIGGER_WEATHER_DANGER = "weather_danger"
NOTIFY_TRIGGER_WEATHER_CAUTION = "weather_caution"
NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED = "official_warning_closed"
NOTIFY_TRIGGER_ALL_CLEAR = "all_clear"
DEFAULT_NOTIFY_TRIGGERS = [
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_WEATHER_DANGER,
]

CONF_REMOTE_HOST = "remote_host"
CONF_REMOTE_PORT = "remote_port"
CONF_REMOTE_TOKEN = "remote_access_token"
CONF_REMOTE_USE_SSL = "remote_use_ssl"
CONF_REMOTE_SELECTED_ROOMS = "remote_selected_rooms"
CONF_REMOTE_CLIENT_ID = "remote_client_id"
CONF_REMOTE_ROOM_SHARE = "remote_share"
DEFAULT_REMOTE_PORT = 8123
REMOTE_UPDATE_INTERVAL = timedelta(seconds=30)
REMOTE_OFFLINE_GRACE = timedelta(minutes=3)
REMOTE_PROTOCOL_VERSION = 2
FORECAST_REFRESH_INTERVAL = timedelta(minutes=45)

CONF_ROOM_NAME = "room_name"
CONF_INDOOR_TEMP = "indoor_temperature"
CONF_INDOOR_HUMIDITY = "indoor_humidity"
CONF_CO2 = "co2_entity"
CONF_WINDOWS = "window_entities"
CONF_CLIMATE = "climate_entity"
CONF_TARGET_TEMP = "target_temperature"
CONF_SURFACE_TEMP = "surface_temperature"
CONF_NIGHT_START_HOUR = "night_advice_start_hour"  # legacy v0.6.22/v0.6.23
CONF_NIGHT_START_TIME = "night_advice_start_time"
CONF_NIGHT_END_TIME = "night_advice_end_time"
DEFAULT_NIGHT_START_HOUR = 22
DEFAULT_NIGHT_START_TIME = "22:00"
DEFAULT_NIGHT_END_TIME = "07:00"

# Kept only so old v0.1/v0.2 config subentries remain readable.
# v0.3 no longer asks for or uses this external helper.
CONF_HOURS_SINCE_AIRING = "hours_since_airing_entity"

DEFAULT_TARGET_TEMP = 21.0
MIN_CONFIRMED_AIRING = timedelta(minutes=5)
CO2_GRACE_PERIOD = timedelta(seconds=60)

# The mould tracker is optional and only exists when a surface-temperature
# sensor is configured. It keeps only compact measured critical intervals and
# escalates softly for long current exposure or repeated affected days; these
# are product-side hints, not medical/DIN thresholds or proof of mould growth.
MOLD_SAMPLE_INTERVAL = timedelta(minutes=5)
MOLD_HISTORY_WINDOW = timedelta(hours=24)
MOLD_HISTORY_RETENTION = timedelta(days=7)
# Product-side persistence hints only; not medical/DIN thresholds.
MOLD_CURRENT_LONG = timedelta(hours=6)
MOLD_REPEATED_DAY_MIN = timedelta(hours=1)
MOLD_REPEATED_DAYS = 3

DATA_TRACKERS = "airing_trackers"
DATA_CO2_TRACKERS = "co2_trackers"
DATA_MOLD_TRACKERS = "mold_trackers"
DATA_COORDINATORS = "room_coordinators"
DATA_OUTSIDE_COORDINATORS = "outside_coordinators"
DATA_REMOTE_COORDINATORS = "remote_coordinators"
DATA_API_REGISTERED = "api_registered"
DATA_NOTIFICATION_STATE = "notification_state"
DATA_FORECAST_CACHE = "hourly_forecast_cache"
DATA_AIR_QUALITY_TRACKERS = "air_quality_trackers"
DATA_REMOTE_ACCESS = "remote_access"
AIR_QUALITY_HISTORY_MIN_SAMPLES = 24
AIR_QUALITY_SAMPLE_MIN_INTERVAL = timedelta(minutes=30)
AIR_QUALITY_RECENT_SAMPLES = 12
AIR_QUALITY_MAX_LOCATIONS = 8
AIR_QUALITY_BASELINE_ALPHA = 0.0025
DECISION_MEMORY_TTL = timedelta(hours=3)
STORAGE_VERSION = 1


def entry_kind(entry) -> str:
    """Return the config-entry kind, including legacy remote entries.

    Remote entries created before the explicit ``entry_kind`` marker can still
    be identified safely by their required remote host. Treating those as
    remote keeps their topology read-only without changing any snapshot data.
    """
    kind = entry.data.get(CONF_ENTRY_KIND)
    if kind in {ENTRY_KIND_LOCAL, ENTRY_KIND_REMOTE}:
        return kind
    if entry.data.get(CONF_REMOTE_HOST):
        return ENTRY_KIND_REMOTE
    return ENTRY_KIND_LOCAL

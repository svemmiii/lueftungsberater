"""Config flow for Lüftungsberater."""
from __future__ import annotations

import asyncio
import logging
import uuid
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.config_entries import ConfigEntry, ConfigSubentry, ConfigSubentryFlow
from homeassistant.const import UnitOfTemperature
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import SectionConfig, section
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    AreaSelector,
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    FileSelector,
    FileSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    selector,
)
from homeassistant.util.unit_conversion import TemperatureConverter

from .areas import room_area_name
from .hardware_hub import (
    direct_device_sensor_candidates,
    direct_device_sensor_map,
    discovered_stations,
    hardware_id_matches,
    station_connection_type,
    station_is_master,
    station_role,
    station_subentries,
)
from .const import (
    CONF_AREA_ID,
    CONF_CLIMATE,
    CONF_DISPLAY_MODE,
    CONF_CO2,
    CONF_INDOOR_PM25,
    CONF_INDOOR_PM10,
    CONF_INDOOR_VOC,
    CONF_INDOOR_NO2,
    CONF_INDOOR_FORMALDEHYDE,
    CONF_ENTRY_KIND,
    CONF_INDOOR_HUMIDITY,
    CONF_INDOOR_TEMP,
    CONF_INSTANCE_NAME,
    CONF_HARDWARE_ID,
    CONF_HARDWARE_MASTER_ID,
    CONF_HARDWARE_ROOM_ID,
    CONF_HARDWARE_DISCOVERY_ID,
    CONF_HARDWARE_CONNECTION_TYPE,
    CONF_HARDWARE_ROLE,
    CONF_HARDWARE_MASTER_SUBENTRY_ID,
    CONF_HARDWARE_MASTER_SECRET,
    CONF_HARDWARE_ROOM_MODE,
    CONF_HARDWARE_LOCATION_MODE,
    CONF_HARDWARE_WIREGUARD_FILE,
    CONF_HARDWARE_WG_ADDRESS,
    CONF_HARDWARE_WG_PRIVATE_KEY,
    CONF_HARDWARE_WG_PEER_PUBLIC_KEY,
    CONF_HARDWARE_WG_PRESHARED_KEY,
    CONF_HARDWARE_WG_ENDPOINT,
    CONF_HARDWARE_WG_ENDPOINT_HOST,
    CONF_HARDWARE_WG_ENDPOINT_PORT,
    CONF_HARDWARE_WG_ALLOWED_IPS,
    CONF_HARDWARE_WG_KEEPALIVE,
    CONF_HARDWARE_DEVICE_ID,
    CONF_HARDWARE_DIRECT_CO2,
    CONF_HARDWARE_DIRECT_TEMP,
    CONF_HARDWARE_DIRECT_HUMIDITY,
    HARDWARE_CONNECTION_DIRECT,
    HARDWARE_CONNECTION_MASTER,
    HARDWARE_ROLE_STANDALONE,
    HARDWARE_ROLE_MASTER,
    HARDWARE_ROLE_NODE,
    HARDWARE_ROOM_CREATE,
    HARDWARE_ROOM_EXISTING,
    HARDWARE_LOCATION_LOCAL,
    HARDWARE_LOCATION_REMOTE,
    CONF_MANUAL_OUTDOOR,
    CONF_NOTIFY_TARGET,
    CONF_NOTIFY_TRIGGERS,
    CONF_ROOM_NOTIFY_TRIGGERS,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_CO2,
    CONF_OUTDOOR_WIND,
    CONF_OUTDOOR_GUST,
    CONF_OUTDOOR_RAIN,
    CONF_OUTDOOR_PM25,
    CONF_OUTDOOR_PM10,
    CONF_OUTDOOR_VOC,
    CONF_OUTDOOR_NO2,
    CONF_OUTDOOR_O3,
    CONF_OUTDOOR_TEMP,
    CONF_REMOTE_HOST,
    CONF_REMOTE_PORT,
    CONF_REMOTE_TOKEN,
    CONF_REMOTE_USE_SSL,
    CONF_REMOTE_SELECTED_ROOMS,
    CONF_REMOTE_CLIENT_ID,
    CONF_REMOTE_SERVER_ID,
    CONF_REMOTE_ROOM_SHARE,
    CONF_ROOM_NAME,
    CONF_TARGET_TEMP,
    CONF_SURFACE_TEMP,
    CONF_NIGHT_START_HOUR,
    CONF_NIGHT_START_TIME,
    CONF_NIGHT_END_TIME,
    CONF_WARNING_SOURCE,
    CONF_WEATHER,
    CONF_WINDOWS,
    DEFAULT_REMOTE_PORT,
    DEFAULT_DISPLAY_MODE,
    DEFAULT_NIGHT_START_HOUR,
    DEFAULT_NIGHT_START_TIME,
    DEFAULT_NIGHT_END_TIME,
    DEFAULT_NOTIFY_TRIGGERS,
    DEFAULT_ROOM_NOTIFY_TRIGGERS,
    DEFAULT_TARGET_TEMP,
    DOMAIN,
    DISPLAY_MODE_ROOM_AIR,
    DISPLAY_MODE_VENTILATION,
    ENTRY_KIND_LOCAL,
    ENTRY_KIND_REMOTE,
    SUBENTRY_TYPE_ROOM,
    SUBENTRY_TYPE_STATION,
    WARNING_SOURCE_NONE,
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_AIRING_FINISHED,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED,
    NOTIFY_TRIGGER_ALL_CLEAR,
    entry_kind,
)
_LOGGER = logging.getLogger(__name__)


# Visual grouping only. Stored ConfigEntry/Subentry data intentionally remains
# flat (apart from the existing manual_outdoor mapping) so the runtime and old
# installations do not depend on frontend form layout.
SECTION_GENERAL = "general"
SECTION_OUTDOOR = "outdoor"
SECTION_NOTIFICATIONS = "notifications"
SECTION_ROOM_CLIMATE = "room_climate"
SECTION_ROOM_NIGHT = "room_night"
SECTION_ROOM_SENSORS = "room_sensors"
SECTION_ROOM_OPENINGS = "room_openings"
SECTION_ROOM_REMOTE = "room_remote"
SECTION_ROOM_NOTIFICATIONS = "room_notifications"

NOTIFY_TRIGGER_OPTIONS = [
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED,
    NOTIFY_TRIGGER_ALL_CLEAR,
]
ROOM_NOTIFY_TRIGGER_OPTIONS = [
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_AIRING_FINISHED,
]


from .remote import (
    RemoteAdminRequiredError,
    RemoteAuthError,
    RemoteConnectionError,
    async_fetch_remote_snapshot,
    async_host_is_tailscale,
    normalize_remote_host,
)


def _entity(
    domain: str | list[str],
    multiple: bool = False,
    device_class: str | list[str] | None = None,
) -> EntitySelector:
    config: dict[str, Any] = {"domain": domain, "multiple": multiple}
    if device_class is not None:
        config["device_class"] = device_class
    return EntitySelector(EntitySelectorConfig(**config))


def _warning_source_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    """Build a friendly list of installed warning providers.

    A broken/unusual entity-registry entry must never make the whole local
    config flow unusable. Known warning integrations are included directly;
    the generic warning-name scan is best-effort only.
    """
    language = str(getattr(hass.config, "language", "en") or "en").lower()
    if language.startswith("de"):
        none_label = "Kein Warndienst"
    elif language.startswith("tr"):
        none_label = "Uyarı hizmeti yok"
    else:
        none_label = "No warning service"

    # SelectSelector requires one homogeneous option format. Dynamic provider
    # labels need SelectOptionDict, so the optional "none" entry must use the
    # same format instead of mixing a plain string with labelled dictionaries.
    options: list[SelectOptionDict] = [
        SelectOptionDict(value=WARNING_SOURCE_NONE, label=none_label)
    ]
    known_domains = {"nina", "dwd_weather_warnings"}

    try:
        registry = er.async_get(hass)
        entries = hass.config_entries.async_entries()
    except Exception:  # noqa: BLE001 - config flow must remain available
        _LOGGER.exception("Unable to read warning providers for config flow")
        return options

    for entry in entries:
        if entry.domain == DOMAIN:
            continue

        looks_like_warning = entry.domain in known_domains
        if not looks_like_warning:
            try:
                entities = er.async_entries_for_config_entry(registry, entry.entry_id)
            except Exception:  # noqa: BLE001 - skip only the broken provider
                _LOGGER.exception(
                    "Unable to inspect entities for config entry %s", entry.entry_id
                )
                entities = []

            for entity in entities:
                original_name = getattr(entity, "original_name", None) or ""
                entity_id = getattr(entity, "entity_id", "") or ""
                low = f"{entity_id} {original_name}".lower()
                if "warn" in low or "warning" in low or "nina" in low:
                    looks_like_warning = True
                    break

        if looks_like_warning:
            options.append(
                SelectOptionDict(
                    value=entry.entry_id,
                    label=f"{entry.title} ({entry.domain})",
                )
            )
    return options


def _global_schema(hass: HomeAssistant) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(SECTION_GENERAL): section(
                vol.Schema(
                    {
                        vol.Required(CONF_WEATHER): _entity("weather"),
                        vol.Optional(
                            CONF_WARNING_SOURCE, default=WARNING_SOURCE_NONE
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=_warning_source_options(hass),
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="warning_source",
                            )
                        ),
                        vol.Optional(
                            CONF_DISPLAY_MODE, default=DEFAULT_DISPLAY_MODE
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=[DISPLAY_MODE_ROOM_AIR, DISPLAY_MODE_VENTILATION],
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="display_mode",
                            )
                        ),
                    }
                ),
                SectionConfig(collapsed=False),
            ),
            vol.Optional(SECTION_OUTDOOR): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_OUTDOOR_TEMP): _entity(
                            "sensor", device_class=SensorDeviceClass.TEMPERATURE
                        ),
                        vol.Optional(CONF_OUTDOOR_HUMIDITY): _entity(
                            "sensor", device_class=SensorDeviceClass.HUMIDITY
                        ),
                        vol.Optional(CONF_OUTDOOR_CO2): _entity(
                            "sensor", device_class=SensorDeviceClass.CO2
                        ),
                        vol.Optional(CONF_OUTDOOR_WIND): _entity("sensor"),
                        vol.Optional(CONF_OUTDOOR_GUST): _entity("sensor"),
                        vol.Optional(CONF_OUTDOOR_RAIN): EntitySelector(
                            EntitySelectorConfig(
                                filter=[
                                    {"domain": "binary_sensor"},
                                    {
                                        "domain": "sensor",
                                        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
                                    },
                                ]
                            )
                        ),
                        vol.Optional(CONF_OUTDOOR_PM25): _entity("sensor"),
                        vol.Optional(CONF_OUTDOOR_PM10): _entity("sensor"),
                        vol.Optional(CONF_OUTDOOR_VOC): _entity("sensor"),
                        vol.Optional(CONF_OUTDOOR_NO2): _entity("sensor"),
                        vol.Optional(CONF_OUTDOOR_O3): _entity("sensor"),
                    }
                ),
                SectionConfig(collapsed=True),
            ),
            vol.Optional(SECTION_NOTIFICATIONS): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_NOTIFY_TARGET): _entity("notify"),
                        vol.Optional(
                            CONF_NOTIFY_TRIGGERS, default=DEFAULT_NOTIFY_TRIGGERS
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=NOTIFY_TRIGGER_OPTIONS,
                                multiple=True,
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="notify_triggers",
                            )
                        ),
                    }
                ),
                SectionConfig(collapsed=True),
            ),
        }
    )


def _local_schema(hass: HomeAssistant) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_INSTANCE_NAME, default="Lüftungsassistent"): TextSelector(
                TextSelectorConfig()
            ),
            **dict(_global_schema(hass).schema),
        }
    )


def _normalize_local_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Flatten visual sections into the stable ConfigEntry data shape."""
    if SECTION_GENERAL not in user_input:
        # Compatibility for programmatic callers/tests that still use the old
        # flat form shape.
        return dict(user_input)

    data: dict[str, Any] = {}
    if CONF_INSTANCE_NAME in user_input:
        data[CONF_INSTANCE_NAME] = user_input[CONF_INSTANCE_NAME]

    general = user_input.get(SECTION_GENERAL)
    if isinstance(general, dict):
        for key in (CONF_WEATHER, CONF_WARNING_SOURCE, CONF_DISPLAY_MODE):
            if key in general:
                data[key] = general[key]

    outdoor = user_input.get(SECTION_OUTDOOR)
    if isinstance(outdoor, dict):
        manual = {
            key: value
            for key, value in outdoor.items()
            if key in {
                CONF_OUTDOOR_TEMP, CONF_OUTDOOR_HUMIDITY, CONF_OUTDOOR_CO2,
                CONF_OUTDOOR_WIND, CONF_OUTDOOR_GUST, CONF_OUTDOOR_RAIN,
                CONF_OUTDOOR_PM25, CONF_OUTDOOR_PM10, CONF_OUTDOOR_VOC,
                CONF_OUTDOOR_NO2, CONF_OUTDOOR_O3,
            }
            and value not in (None, "")
        }
        if manual:
            data[CONF_MANUAL_OUTDOOR] = manual

    notifications = user_input.get(SECTION_NOTIFICATIONS)
    if isinstance(notifications, dict):
        for key in (CONF_NOTIFY_TARGET, CONF_NOTIFY_TRIGGERS):
            if key in notifications and notifications[key] not in (None, ""):
                data[key] = notifications[key]

    return data


def _local_form_defaults(entry: ConfigEntry) -> dict[str, Any]:
    """Return section-shaped defaults from stable flat entry data."""
    manual = entry.data.get(CONF_MANUAL_OUTDOOR)
    if not isinstance(manual, dict):
        manual = {}
    # Preserve legacy top-level manual sensor keys when reconfiguring an older
    # entry, but keep the newly stored shape compact.
    outdoor = dict(manual)
    for key in (
        CONF_OUTDOOR_TEMP, CONF_OUTDOOR_HUMIDITY, CONF_OUTDOOR_CO2,
        CONF_OUTDOOR_WIND, CONF_OUTDOOR_GUST, CONF_OUTDOOR_RAIN,
        CONF_OUTDOOR_PM25, CONF_OUTDOOR_PM10, CONF_OUTDOOR_VOC,
        CONF_OUTDOOR_NO2, CONF_OUTDOOR_O3,
    ):
        if not outdoor.get(key):
            old = entry.data.get(key)
            if isinstance(old, str) and old:
                outdoor[key] = old

    notifications: dict[str, Any] = {}
    if entry.data.get(CONF_NOTIFY_TARGET):
        notifications[CONF_NOTIFY_TARGET] = entry.data.get(CONF_NOTIFY_TARGET)
    notifications[CONF_NOTIFY_TRIGGERS] = entry.data.get(
        CONF_NOTIFY_TRIGGERS, DEFAULT_NOTIFY_TRIGGERS
    )

    defaults: dict[str, Any] = {
        CONF_INSTANCE_NAME: entry.title,
        SECTION_GENERAL: {
            CONF_WEATHER: entry.data.get(CONF_WEATHER),
            CONF_WARNING_SOURCE: entry.data.get(
                CONF_WARNING_SOURCE, WARNING_SOURCE_NONE
            ),
            CONF_DISPLAY_MODE: entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE),
        },
        SECTION_NOTIFICATIONS: notifications,
    }
    if outdoor:
        defaults[SECTION_OUTDOOR] = outdoor
    return defaults



def _remote_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_INSTANCE_NAME): TextSelector(TextSelectorConfig()),
            vol.Required(CONF_REMOTE_HOST): TextSelector(
                TextSelectorConfig(autocomplete="off")
            ),
            vol.Required(CONF_REMOTE_PORT, default=DEFAULT_REMOTE_PORT): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=65535,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(CONF_REMOTE_TOKEN): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD,
                    autocomplete="current-password",
                )
            ),
            vol.Required(CONF_REMOTE_USE_SSL, default=False): BooleanSelector(),
        }
    )


def _display_temperature(hass: HomeAssistant, value_c: float) -> float:
    unit = str(hass.config.units.temperature_unit)
    if unit == UnitOfTemperature.CELSIUS:
        return value_c
    return float(TemperatureConverter.convert(value_c, UnitOfTemperature.CELSIUS, unit))


def _stored_temperature(hass: HomeAssistant, value: Any) -> float:
    number = float(value)
    unit = str(hass.config.units.temperature_unit)
    if unit == UnitOfTemperature.CELSIUS:
        return number
    return float(TemperatureConverter.convert(number, unit, UnitOfTemperature.CELSIUS))


def _room_schema(hass: HomeAssistant) -> vol.Schema:
    unit = str(hass.config.units.temperature_unit)
    min_value = _display_temperature(hass, 5.0)
    max_value = _display_temperature(hass, 35.0)
    default_value = _display_temperature(hass, DEFAULT_TARGET_TEMP)
    step = 0.5 if unit == UnitOfTemperature.CELSIUS else 1.0
    if unit != UnitOfTemperature.CELSIUS:
        default_value = round(default_value)

    return vol.Schema(
        {
            vol.Optional(CONF_AREA_ID): AreaSelector(),
            vol.Optional(CONF_ROOM_NAME): TextSelector(TextSelectorConfig()),
            vol.Required(SECTION_ROOM_CLIMATE): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_INDOOR_TEMP): _entity(
                            "sensor", device_class=SensorDeviceClass.TEMPERATURE
                        ),
                        vol.Optional(CONF_INDOOR_HUMIDITY): _entity(
                            "sensor", device_class=SensorDeviceClass.HUMIDITY
                        ),
                        vol.Optional(CONF_CLIMATE): _entity("climate"),
                        vol.Optional(
                            CONF_TARGET_TEMP, default=default_value
                        ): NumberSelector(
                            NumberSelectorConfig(
                                min=min_value,
                                max=max_value,
                                step=step,
                                mode=NumberSelectorMode.BOX,
                                unit_of_measurement=unit,
                            )
                        ),
                    }
                ),
                SectionConfig(collapsed=False),
            ),
            vol.Required(SECTION_ROOM_NIGHT): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_NIGHT_START_TIME, default=DEFAULT_NIGHT_START_TIME
                        ): selector({"time": {}}),
                        vol.Optional(
                            CONF_NIGHT_END_TIME, default=DEFAULT_NIGHT_END_TIME
                        ): selector({"time": {}}),
                    }
                ),
                SectionConfig(collapsed=False),
            ),
            vol.Optional(SECTION_ROOM_SENSORS): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_CO2): _entity(
                            "sensor", device_class=SensorDeviceClass.CO2
                        ),
                        vol.Optional(CONF_SURFACE_TEMP): _entity(
                            "sensor", device_class=SensorDeviceClass.TEMPERATURE
                        ),
                        vol.Optional(CONF_INDOOR_PM25): _entity("sensor"),
                        vol.Optional(CONF_INDOOR_PM10): _entity("sensor"),
                        vol.Optional(CONF_INDOOR_VOC): _entity("sensor"),
                        vol.Optional(CONF_INDOOR_NO2): _entity("sensor"),
                        vol.Optional(CONF_INDOOR_FORMALDEHYDE): _entity("sensor"),
                    }
                ),
                SectionConfig(collapsed=True),
            ),
            vol.Optional(SECTION_ROOM_NOTIFICATIONS): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_ROOM_NOTIFY_TRIGGERS,
                            default=DEFAULT_ROOM_NOTIFY_TRIGGERS,
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=ROOM_NOTIFY_TRIGGER_OPTIONS,
                                multiple=True,
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="room_notify_triggers",
                            )
                        ),
                    }
                ),
                SectionConfig(collapsed=True),
            ),
            vol.Optional(SECTION_ROOM_REMOTE): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_REMOTE_ROOM_SHARE, default=False): BooleanSelector(),
                    }
                ),
                SectionConfig(collapsed=True),
            ),
            vol.Optional(SECTION_ROOM_OPENINGS): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_WINDOWS): _entity(
                            "binary_sensor",
                            multiple=True,
                            device_class=[
                                BinarySensorDeviceClass.WINDOW,
                                BinarySensorDeviceClass.DOOR,
                                BinarySensorDeviceClass.OPENING,
                                BinarySensorDeviceClass.GARAGE_DOOR,
                            ],
                        ),
                    }
                ),
                SectionConfig(collapsed=True),
            ),
        }
    )


def _flatten_room_input(user_input: dict[str, Any]) -> dict[str, Any]:
    if SECTION_ROOM_CLIMATE not in user_input:
        return dict(user_input)
    data: dict[str, Any] = {}
    if CONF_AREA_ID in user_input:
        data[CONF_AREA_ID] = user_input[CONF_AREA_ID]
    if CONF_ROOM_NAME in user_input:
        data[CONF_ROOM_NAME] = user_input[CONF_ROOM_NAME]
    for section_key in (
        SECTION_ROOM_CLIMATE,
        SECTION_ROOM_NIGHT,
        SECTION_ROOM_SENSORS,
        SECTION_ROOM_OPENINGS,
        SECTION_ROOM_REMOTE,
        SECTION_ROOM_NOTIFICATIONS,
    ):
        values = user_input.get(section_key)
        if isinstance(values, dict):
            data.update(values)
    return data


def _normalize_room_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, Any]:
    data = _flatten_room_input(user_input)
    if CONF_ROOM_NAME in data:
        room_name = str(data[CONF_ROOM_NAME] or "").strip()
        if room_name:
            data[CONF_ROOM_NAME] = room_name
        else:
            data.pop(CONF_ROOM_NAME, None)
    if CONF_AREA_ID in data:
        raw_area_id = data.get(CONF_AREA_ID)
        if raw_area_id:
            data[CONF_AREA_ID] = str(raw_area_id).strip()
        else:
            data.pop(CONF_AREA_ID, None)
    if CONF_TARGET_TEMP in data:
        data[CONF_TARGET_TEMP] = _stored_temperature(hass, data[CONF_TARGET_TEMP])
    for time_key in (CONF_NIGHT_START_TIME, CONF_NIGHT_END_TIME):
        raw_time = data.get(time_key)
        if raw_time is not None and not isinstance(raw_time, str):
            if hasattr(raw_time, "strftime"):
                data[time_key] = raw_time.strftime("%H:%M")
            else:
                data[time_key] = str(raw_time)
    data.pop(CONF_NIGHT_START_HOUR, None)
    return data


def _room_form_defaults(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    flat = dict(data)
    if CONF_NIGHT_START_TIME not in flat:
        try:
            old_hour = int(flat.get(CONF_NIGHT_START_HOUR, DEFAULT_NIGHT_START_HOUR))
        except (TypeError, ValueError):
            old_hour = DEFAULT_NIGHT_START_HOUR
        flat[CONF_NIGHT_START_TIME] = f"{max(0, min(23, old_hour)):02d}:00"
    flat.pop(CONF_NIGHT_START_HOUR, None)
    if CONF_TARGET_TEMP in flat:
        flat[CONF_TARGET_TEMP] = _display_temperature(hass, float(flat[CONF_TARGET_TEMP]))

    form: dict[str, Any] = {
        CONF_ROOM_NAME: flat.get(CONF_ROOM_NAME, ""),
        SECTION_ROOM_CLIMATE: {
            key: flat[key]
            for key in (
                CONF_INDOOR_TEMP,
                CONF_INDOOR_HUMIDITY,
                CONF_CLIMATE,
                CONF_TARGET_TEMP,
            )
            if key in flat and flat[key] not in (None, "")
        },
        SECTION_ROOM_NIGHT: {
            CONF_NIGHT_START_TIME: flat.get(
                CONF_NIGHT_START_TIME, DEFAULT_NIGHT_START_TIME
            ),
            CONF_NIGHT_END_TIME: flat.get(
                CONF_NIGHT_END_TIME, DEFAULT_NIGHT_END_TIME
            ),
        },
    }
    sensors = {
        key: flat[key]
        for key in (
            CONF_CO2, CONF_SURFACE_TEMP, CONF_INDOOR_PM25, CONF_INDOOR_PM10,
            CONF_INDOOR_VOC, CONF_INDOOR_NO2, CONF_INDOOR_FORMALDEHYDE,
        )
        if key in flat and flat[key] not in (None, "")
    }
    if sensors:
        form[SECTION_ROOM_SENSORS] = sensors
    # Existing v0.6.x rooms had no explicit remote-share flag. Keep those
    # available to existing remote installations; newly created rooms default
    # to not shared until the user enables it.
    form[SECTION_ROOM_REMOTE] = {
        CONF_REMOTE_ROOM_SHARE: bool(flat.get(CONF_REMOTE_ROOM_SHARE, True))
    }
    form[SECTION_ROOM_NOTIFICATIONS] = {
        CONF_ROOM_NOTIFY_TRIGGERS: flat.get(
            CONF_ROOM_NOTIFY_TRIGGERS, DEFAULT_ROOM_NOTIFY_TRIGGERS
        )
    }
    openings = flat.get(CONF_WINDOWS)
    if openings:
        form[SECTION_ROOM_OPENINGS] = {CONF_WINDOWS: openings}
    configured_area = flat.get(CONF_AREA_ID)
    if configured_area and room_area_name(hass, str(configured_area)) is not None:
        form[CONF_AREA_ID] = str(configured_area)
    return form



def _remote_data(user_input: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    data = dict(user_input)
    name = str(data.pop(CONF_INSTANCE_NAME)).strip()
    data[CONF_ENTRY_KIND] = ENTRY_KIND_REMOTE
    data[CONF_REMOTE_HOST] = normalize_remote_host(data[CONF_REMOTE_HOST])
    data[CONF_REMOTE_PORT] = int(data[CONF_REMOTE_PORT])
    data.setdefault(CONF_REMOTE_CLIENT_ID, uuid.uuid4().hex)
    return name, data


async def _test_remote(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    """Validate a remote and return its current snapshot when successful."""
    host = str(data[CONF_REMOTE_HOST])
    port = int(data[CONF_REMOTE_PORT])
    if not await async_host_is_tailscale(hass, host, port):
        return "not_tailscale", None
    try:
        payload = await async_fetch_remote_snapshot(hass, data, discovery=True)
    except RemoteAuthError:
        return "invalid_auth", None
    except RemoteAdminRequiredError:
        return "admin_required", None
    except RemoteConnectionError:
        return "cannot_connect", None
    server_id = str(payload.get("home_assistant_instance_id") or "").strip().lower()
    if server_id:
        data[CONF_REMOTE_SERVER_ID] = server_id
    return None, payload


async def _validate_remote(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Compatibility wrapper used by tests and reconfiguration helpers."""
    error, _payload = await _test_remote(hass, data)
    return error


def _remote_room_options(payload: dict[str, Any] | None) -> list[SelectOptionDict]:
    """Return rooms advertised by a remote as stable multi-select options."""
    options: list[SelectOptionDict] = []
    instances = payload.get("instances", []) if isinstance(payload, dict) else []
    if not isinstance(instances, list):
        return options
    for instance in instances:
        if not isinstance(instance, dict):
            continue
        instance_id = str(instance.get("id") or "")
        instance_name = str(instance.get("name") or "Fresh Air Assistant")
        rooms = instance.get("rooms", [])
        if not instance_id or not isinstance(rooms, list):
            continue
        for room in rooms:
            if not isinstance(room, dict):
                continue
            room_id = str(room.get("id") or "")
            if not room_id:
                continue
            room_name = str(room.get("name") or room_id)
            options.append(
                SelectOptionDict(
                    value=f"{instance_id}:{room_id}",
                    label=f"{instance_name} · {room_name}",
                )
            )
    return options


def _remote_selection_schema(
    payload: dict[str, Any] | None,
    selected: list[str] | None = None,
) -> vol.Schema:
    options = _remote_room_options(payload)
    available = {str(option["value"]) for option in options}
    if selected is None:
        # First-time setup may conveniently default to every advertised room.
        defaults = sorted(available)
    else:
        # Reconfigure must preserve the semantic meaning of the old selection.
        # If every old ID disappeared, default to none rather than silently
        # sharing every newly-created room.
        defaults = [item for item in selected if item in available]
    return vol.Schema(
        {
            vol.Required(CONF_REMOTE_SELECTED_ROOMS, default=defaults): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _remote_endpoint_is_duplicate(
    entries: list[ConfigEntry],
    data: dict[str, Any],
    *,
    exclude_entry_id: str | None = None,
) -> bool:
    """Return whether another remote entry targets the same endpoint."""
    host = normalize_remote_host(data.get(CONF_REMOTE_HOST, ""))
    port = int(data.get(CONF_REMOTE_PORT, DEFAULT_REMOTE_PORT))
    server_id = str(data.get(CONF_REMOTE_SERVER_ID) or "").strip().lower()
    for current in entries:
        if current.entry_id == exclude_entry_id or entry_kind(current) != ENTRY_KIND_REMOTE:
            continue
        current_server_id = str(
            current.data.get(CONF_REMOTE_SERVER_ID) or ""
        ).strip().lower()
        if server_id and current_server_id and current_server_id == server_id:
            return True
        current_host = normalize_remote_host(current.data.get(CONF_REMOTE_HOST, ""))
        current_port = int(current.data.get(CONF_REMOTE_PORT, DEFAULT_REMOTE_PORT))
        if current_host == host and current_port == port:
            return True
    return False


def _remote_summary(
    payload: dict[str, Any] | None,
    fallback_name: str = "Home Assistant",
) -> dict[str, str]:
    """Return a compact, human-friendly summary of the remote snapshot."""
    instances = payload.get("instances", []) if isinstance(payload, dict) else []
    if not isinstance(instances, list):
        instances = []

    room_count = 0
    blocks: list[str] = []
    for index, instance in enumerate(instances, start=1):
        if not isinstance(instance, dict):
            continue
        instance_name = str(instance.get("name") or f"Lüftungsassistent {index}")
        rooms = instance.get("rooms", [])
        if not isinstance(rooms, list):
            rooms = []
        room_names = [
            str(room.get("name") or f"Raum {room_index}")
            for room_index, room in enumerate(rooms, start=1)
            if isinstance(room, dict)
        ]
        room_count += len(room_names)
        room_lines = "\n".join(f"• {name}" for name in room_names) or "• —"
        blocks.append(f"{instance_name}\n{room_lines}")

    return {
        "instances": str(len(instances)),
        "rooms": str(room_count),
        "details": "\n\n".join(blocks) or "—",
        "remote_name": str(payload.get("home_assistant_name") or fallback_name)
        if isinstance(payload, dict)
        else fallback_name,
    }


class LueftungsberaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure local and Tailscale-remote Lüftungsberater instances."""

    VERSION = 1
    MINOR_VERSION = 12

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="user",
            menu_options=["local", "remote"],
        )

    async def async_step_local(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = _normalize_local_input(user_input)
            title = str(data.pop(CONF_INSTANCE_NAME)).strip() or "Lüftungsassistent"
            data[CONF_ENTRY_KIND] = ENTRY_KIND_LOCAL
            # Local advisors are manually created, repeatable config entries.
            # They intentionally do not use ConfigEntry.unique_id: Home Assistant
            # reserves that field for stable identifiers of a real device/API.
            return self.async_create_entry(title=title, data=data)

        try:
            schema = _local_schema(self.hass)
        except Exception:  # noqa: BLE001 - never strand the user on a generic error
            _LOGGER.exception("Unable to build local Lüftungsberater setup form")
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_INSTANCE_NAME, default="Lüftungsassistent"
                    ): TextSelector(TextSelectorConfig()),
                    vol.Required(CONF_WEATHER): _entity("weather"),
                    vol.Optional(
                        CONF_WARNING_SOURCE, default=WARNING_SOURCE_NONE
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[WARNING_SOURCE_NONE],
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="warning_source",
                        )
                    ),
                }
            )
        return self.async_show_form(step_id="local", data_schema=schema)

    async def async_step_remote(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            title, data = _remote_data(user_input)
            if _remote_endpoint_is_duplicate(self._async_current_entries(), data):
                return self.async_abort(reason="already_configured")

            self._pending_remote_title = title
            self._pending_remote_data = data
            self._pending_remote_input = dict(user_input)
            self._pending_remote_error = None
            self._remote_test_task = self.hass.async_create_task(
                _test_remote(self.hass, data),
                f"Test Lüftungsberater remote {title}",
            )
            return await self.async_step_remote_progress()

        return self.async_show_form(
            step_id="remote",
            data_schema=_remote_schema(),
            errors=errors,
            last_step=False,
        )

    async def async_step_remote_progress(
        self, user_input: dict[str, Any] | None = None
    ):
        """Show HA's native progress UI while Tailscale and the remote API are tested."""
        task: asyncio.Task | None = getattr(self, "_remote_test_task", None)
        if task is None:
            return await self.async_step_remote()
        if not task.done():
            return self.async_show_progress(
                step_id="remote_progress",
                progress_action="testing_remote",
                progress_task=task,
            )

        try:
            error, payload = await task
        except Exception:  # noqa: BLE001 - convert unexpected network/API failures
            _LOGGER.exception("Unexpected error while testing remote Lüftungsberater")
            error, payload = "cannot_connect", None
        finally:
            self._remote_test_task = None

        if error is None:
            pending_data = getattr(self, "_pending_remote_data", None)
            if isinstance(pending_data, dict) and _remote_endpoint_is_duplicate(
                self._async_current_entries(), pending_data
            ):
                error, payload = "already_configured", None

        self._pending_remote_error = error
        if error is None:
            fallback_title = getattr(self, "_pending_remote_title", "Home Assistant")
            self._pending_remote_summary = _remote_summary(payload, fallback_title)
            self._pending_remote_payload = payload
        return self.async_show_progress_done(next_step_id="remote_confirm")

    async def async_step_remote_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Show the successful connection test before storing credentials."""
        data = getattr(self, "_pending_remote_data", None)
        title = getattr(self, "_pending_remote_title", None)
        if not isinstance(data, dict) or not isinstance(title, str):
            return await self.async_step_remote()

        error = getattr(self, "_pending_remote_error", None)
        if isinstance(error, str) and error:
            previous = getattr(self, "_pending_remote_input", {})
            self._pending_remote_error = None
            return self.async_show_form(
                step_id="remote",
                data_schema=self.add_suggested_values_to_schema(
                    _remote_schema(), previous if isinstance(previous, dict) else {}
                ),
                errors={"base": error},
                last_step=False,
            )

        payload = getattr(self, "_pending_remote_payload", None)
        if user_input is not None:
            selected = [str(item) for item in user_input.get(CONF_REMOTE_SELECTED_ROOMS, [])]
            if not selected:
                return self.async_show_form(
                    step_id="remote_confirm",
                    data_schema=_remote_selection_schema(payload, []),
                    errors={"base": "select_room"},
                    description_placeholders=getattr(
                        self, "_pending_remote_summary", {"instances": "0", "rooms": "0"}
                    ),
                    last_step=True,
                )
            data[CONF_REMOTE_SELECTED_ROOMS] = selected
            return self.async_create_entry(title=title, data=data)
        return self.async_show_form(
            step_id="remote_confirm",
            data_schema=_remote_selection_schema(payload),
            description_placeholders=getattr(
                self,
                "_pending_remote_summary",
                {"instances": "0", "rooms": "0"},
            ),
            last_step=True,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Start reauthentication for a rejected remote access token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Validate and store a replacement remote access token."""
        entry = self._get_reauth_entry()
        if entry_kind(entry) != ENTRY_KIND_REMOTE:
            return self.async_abort(reason="reauth_not_supported")

        errors: dict[str, str] = {}
        if user_input is not None:
            data = dict(entry.data)
            data[CONF_REMOTE_TOKEN] = str(user_input.get(CONF_REMOTE_TOKEN, "")).strip()
            error, _payload = await _test_remote(self.hass, data)
            if error is None and _remote_endpoint_is_duplicate(
                self._async_current_entries(), data, exclude_entry_id=entry.entry_id
            ):
                error = "duplicate_remote"
            if error is None:
                # Remote entries deliberately do not install an update listener.
                # A reauth can start after the *initial* setup failed, where no
                # listener could exist yet, so let the config-flow helper own the
                # reload. This also avoids the listener + reload-helper double
                # reload deprecated by Home Assistant 2026.6+.
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_REMOTE_TOKEN: data[CONF_REMOTE_TOKEN],
                        **(
                            {CONF_REMOTE_SERVER_ID: data[CONF_REMOTE_SERVER_ID]}
                            if data.get(CONF_REMOTE_SERVER_ID)
                            else {}
                        ),
                    },
                    reason="reauth_successful",
                )
            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(CONF_REMOTE_TOKEN): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                )
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"remote_name": entry.title},
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entry = self._get_reconfigure_entry()
        if entry_kind(entry) == ENTRY_KIND_REMOTE:
            return await self._async_reconfigure_remote(entry, user_input)
        return await self._async_reconfigure_local(entry, user_input)

    async def _async_reconfigure_local(
        self,
        entry: ConfigEntry,
        user_input: dict[str, Any] | None,
    ):
        if user_input is not None:
            data = _normalize_local_input(user_input)
            title = str(data.pop(CONF_INSTANCE_NAME)).strip() or entry.title
            data[CONF_ENTRY_KIND] = ENTRY_KIND_LOCAL
            self.hass.config_entries.async_update_entry(entry, title=title, data=data)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _local_schema(self.hass),
                _local_form_defaults(entry),
            ),
        )

    async def _async_reconfigure_remote(
        self,
        entry: ConfigEntry,
        user_input: dict[str, Any] | None,
    ):
        errors: dict[str, str] = {}
        if user_input is not None:
            title, data = _remote_data(user_input)
            data[CONF_REMOTE_CLIENT_ID] = str(
                entry.data.get(CONF_REMOTE_CLIENT_ID) or data[CONF_REMOTE_CLIENT_ID]
            )
            if _remote_endpoint_is_duplicate(
                self._async_current_entries(),
                data,
                exclude_entry_id=entry.entry_id,
            ):
                errors["base"] = "duplicate_remote"
                payload = None
                error = "duplicate_remote"
            else:
                error, payload = await _test_remote(self.hass, data)
                if error is None and _remote_endpoint_is_duplicate(
                    self._async_current_entries(),
                    data,
                    exclude_entry_id=entry.entry_id,
                ):
                    error, payload = "duplicate_remote", None
            if error is None:
                self._pending_remote_title = title
                self._pending_remote_data = data
                self._pending_remote_summary = _remote_summary(payload, title)
                self._pending_remote_payload = payload
                self._pending_remote_previous_selection = list(
                    entry.data.get(CONF_REMOTE_SELECTED_ROOMS, []) or []
                )
                return await self.async_step_reconfigure_confirm()
            errors["base"] = error

        defaults = {
            CONF_INSTANCE_NAME: entry.title,
            CONF_REMOTE_HOST: entry.data.get(CONF_REMOTE_HOST),
            CONF_REMOTE_PORT: entry.data.get(CONF_REMOTE_PORT, DEFAULT_REMOTE_PORT),
            CONF_REMOTE_TOKEN: entry.data.get(CONF_REMOTE_TOKEN, ""),
            CONF_REMOTE_USE_SSL: entry.data.get(CONF_REMOTE_USE_SSL, False),
        }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(_remote_schema(), defaults),
            errors=errors,
            last_step=False,
        )

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Confirm a tested remote reconfiguration."""
        entry = self._get_reconfigure_entry()
        data = getattr(self, "_pending_remote_data", None)
        title = getattr(self, "_pending_remote_title", None)
        if not isinstance(data, dict) or not isinstance(title, str):
            return await self._async_reconfigure_remote(entry, None)
        payload = getattr(self, "_pending_remote_payload", None)
        previous = getattr(self, "_pending_remote_previous_selection", [])
        if user_input is not None:
            selected = [str(item) for item in user_input.get(CONF_REMOTE_SELECTED_ROOMS, [])]
            if not selected:
                return self.async_show_form(
                    step_id="reconfigure_confirm",
                    data_schema=_remote_selection_schema(payload, previous),
                    errors={"base": "select_room"},
                    description_placeholders=getattr(
                        self, "_pending_remote_summary", {"instances": "0", "rooms": "0"}
                    ),
                    last_step=True,
                )
            data[CONF_REMOTE_SELECTED_ROOMS] = selected
            return self.async_update_reload_and_abort(
                entry,
                title=title,
                data_updates=data,
                reason="reconfigure_successful",
            )
        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=_remote_selection_schema(payload, previous),
            description_placeholders=getattr(
                self,
                "_pending_remote_summary",
                {"instances": "0", "rooms": "0"},
            ),
            last_step=True,
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls,
        config_entry: ConfigEntry,
    ) -> dict[str, type[ConfigSubentryFlow]]:
        # Remote/Tailscale entries are read-only topology. Never offer them as
        # a parent for a locally configured room, including legacy remotes where
        # the explicit entry_kind marker might be missing.
        if (
            entry_kind(config_entry) != ENTRY_KIND_LOCAL
            or bool(config_entry.data.get(CONF_REMOTE_HOST))
        ):
            return {}
        return {SUBENTRY_TYPE_ROOM: RoomSubentryFlow, SUBENTRY_TYPE_STATION: StationSubentryFlow}


def _resolved_room_title(
    hass: HomeAssistant,
    flat_input: dict[str, Any],
) -> tuple[str, str | None]:
    """Resolve room title from an optional custom name or selected HA area."""
    custom_name = str(flat_input.get(CONF_ROOM_NAME, "") or "").strip()
    raw_area_id = flat_input.get(CONF_AREA_ID)
    area_id = str(raw_area_id).strip() if raw_area_id else ""

    if area_id:
        area_name = room_area_name(hass, area_id)
        if area_name is None:
            return custom_name, "area_not_found"
        if not custom_name:
            return area_name.strip(), None

    if not custom_name:
        return "", "room_name_empty"
    return custom_name, None


def _room_name_error(
    entry: ConfigEntry,
    name: str,
    *,
    exclude_subentry_id: str | None = None,
) -> str | None:
    """Validate a resolved human room title without using it as identity."""
    if not name:
        return "room_name_empty"
    folded = name.casefold()
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        if subentry.subentry_id == exclude_subentry_id:
            continue
        if str(subentry.title).strip().casefold() == folded:
            return "room_name_duplicate"
    return None


class RoomSubentryFlow(ConfigSubentryFlow):
    """Room subentry flow."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        if entry_kind(entry) != ENTRY_KIND_LOCAL or entry.data.get(CONF_REMOTE_HOST):
            return self.async_abort(reason="remote_read_only")
        errors: dict[str, str] = {}
        if user_input is not None:
            flat_input = _flatten_room_input(user_input)
            name, error = _resolved_room_title(self.hass, flat_input)
            if error is None:
                error = _room_name_error(entry, name)
            if error:
                errors["base"] = error
            else:
                data = _normalize_room_input(self.hass, user_input)
                # Room names are user-editable labels, not stable identifiers.
                # If no custom label was entered, the selected HA area name is
                # used as the title while the area_id remains the real linkage.
                # The generated subentry_id remains the durable identity used by
                # all entities/devices/stores.
                return self.async_create_entry(title=name, data=data)
        return self.async_show_form(
            step_id="user", data_schema=_room_schema(self.hass), errors=errors
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            flat_input = _flatten_room_input(user_input)
            name, error = _resolved_room_title(self.hass, flat_input)
            if error is None:
                error = _room_name_error(
                    entry, name, exclude_subentry_id=subentry.subentry_id
                )
            if error:
                errors["base"] = error
            else:
                data = _normalize_room_input(self.hass, user_input)
                # Clearing a valid managed area is explicit. If the previously
                # managed HA area was deleted, however, the selector cannot show
                # that stale id. In that case remove the stale integration link
                # and leave the device's current/manual area untouched on sync.
                if CONF_AREA_ID not in flat_input and CONF_AREA_ID in subentry.data:
                    previous_area = subentry.data.get(CONF_AREA_ID)
                    if (
                        previous_area
                        and room_area_name(self.hass, str(previous_area)) is None
                    ):
                        data.pop(CONF_AREA_ID, None)
                    else:
                        data[CONF_AREA_ID] = None
                _sync_station_titles_for_room(
                    self.hass, entry, subentry.subentry_id, name
                )
                return self.async_update_and_abort(
                    entry, subentry, title=name, data=data, unique_id=None
                )

        schema = self.add_suggested_values_to_schema(
            _room_schema(self.hass),
            _room_form_defaults(self.hass, dict(subentry.data)),
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=schema, errors=errors
        )


def _station_room_options(entry: ConfigEntry) -> list[SelectOptionDict]:
    return [
        SelectOptionDict(value=subentry.subentry_id, label=str(subentry.title))
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    ]


def _station_title_for_room(entry: ConfigEntry, station: ConfigSubentry) -> str:
    """Return the current station label derived from its linked room."""
    room_id = str(station.data.get(CONF_HARDWARE_ROOM_ID) or "")
    room = entry.subentries.get(room_id)
    room_title = str(room.title) if room is not None else "Station"
    suffix = "Master" if station_role(station) == HARDWARE_ROLE_MASTER else "Station"
    return f"{room_title} · {suffix}"


def _sync_station_titles_for_room(
    hass: HomeAssistant, entry: ConfigEntry, room_id: str, room_title: str
) -> None:
    """Keep station subentry titles aligned with editable room names."""
    for station in station_subentries(entry):
        if str(station.data.get(CONF_HARDWARE_ROOM_ID) or "") != room_id:
            continue
        suffix = "Master" if station_role(station) == HARDWARE_ROLE_MASTER else "Station"
        title = f"{room_title} · {suffix}"
        if str(station.title) != title:
            hass.config_entries.async_update_subentry(entry, station, title=title)


def _localized_hardware_labels(
    hass: HomeAssistant,
    labels: dict[str, dict[str, str]],
) -> dict[str, str]:
    language = str(getattr(hass.config, "language", "en") or "en").lower()[:2]
    return labels.get(language, labels["en"])


def _station_role_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    labels = _localized_hardware_labels(
        hass,
        {
            "de": {
                HARDWARE_ROLE_STANDALONE: "Einzelstation direkt über Home Assistant",
                HARDWARE_ROLE_MASTER: "ESP-NOW-Master",
                HARDWARE_ROLE_NODE: "ESP-NOW-Raumstation",
            },
            "tr": {
                HARDWARE_ROLE_STANDALONE: "Home Assistant üzerinden doğrudan tek istasyon",
                HARDWARE_ROLE_MASTER: "ESP-NOW master",
                HARDWARE_ROLE_NODE: "ESP-NOW oda istasyonu",
            },
            "en": {
                HARDWARE_ROLE_STANDALONE: "Standalone station directly via Home Assistant",
                HARDWARE_ROLE_MASTER: "ESP-NOW master",
                HARDWARE_ROLE_NODE: "ESP-NOW room station",
            },
        },
    )
    return [
        SelectOptionDict(value=value, label=labels[value])
        for value in (HARDWARE_ROLE_STANDALONE, HARDWARE_ROLE_MASTER, HARDWARE_ROLE_NODE)
    ]


def _room_mode_options(hass: HomeAssistant, *, existing_available: bool) -> list[SelectOptionDict]:
    labels = _localized_hardware_labels(
        hass,
        {
            "de": {
                HARDWARE_ROOM_CREATE: "Neuen Raum automatisch anlegen",
                HARDWARE_ROOM_EXISTING: "Vorhandenen Raum verwenden",
            },
            "tr": {
                HARDWARE_ROOM_CREATE: "Yeni odayı otomatik oluştur",
                HARDWARE_ROOM_EXISTING: "Mevcut odayı kullan",
            },
            "en": {
                HARDWARE_ROOM_CREATE: "Create a new room automatically",
                HARDWARE_ROOM_EXISTING: "Use an existing room",
            },
        },
    )
    values = [HARDWARE_ROOM_CREATE]
    if existing_available:
        values.append(HARDWARE_ROOM_EXISTING)
    return [SelectOptionDict(value=value, label=labels[value]) for value in values]


def _location_mode_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    labels = _localized_hardware_labels(
        hass,
        {
            "de": {
                HARDWARE_LOCATION_LOCAL: "Lokal / im selben Netz",
                HARDWARE_LOCATION_REMOTE: "Entfernt / über WireGuard",
            },
            "tr": {
                HARDWARE_LOCATION_LOCAL: "Yerel / aynı ağda",
                HARDWARE_LOCATION_REMOTE: "Uzak / WireGuard üzerinden",
            },
            "en": {
                HARDWARE_LOCATION_LOCAL: "Local / same network",
                HARDWARE_LOCATION_REMOTE: "Remote / via WireGuard",
            },
        },
    )
    return [
        SelectOptionDict(value=value, label=labels[value])
        for value in (HARDWARE_LOCATION_LOCAL, HARDWARE_LOCATION_REMOTE)
    ]


def _direct_station_candidates(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    current_subentry_id: str | None = None,
    require_sensors: bool = True,
) -> dict[str, dict[str, Any]]:
    """Return selectable ESPHome devices, optionally requiring CO2/temp/RH."""
    device_registry = dr.async_get(hass)
    assigned = {
        str(station.data.get(CONF_HARDWARE_DEVICE_ID) or "")
        for station in station_subentries(entry)
        if station.subentry_id != current_subentry_id
        and station_connection_type(station) == HARDWARE_CONNECTION_DIRECT
    }
    result: dict[str, dict[str, Any]] = {}
    for esphome_entry in hass.config_entries.async_entries("esphome"):
        for device in dr.async_entries_for_config_entry(
            device_registry, config_entry_id=esphome_entry.entry_id
        ):
            if device.id in assigned or device.disabled_by is not None:
                continue
            sensor_candidates = direct_device_sensor_candidates(hass, device.id)
            sensors = direct_device_sensor_map(hass, device.id)
            if require_sensors and any(
                not sensor_candidates[kind]
                for kind in ("co2", "temperature", "humidity")
            ):
                continue
            name = str(device.name_by_user or device.name or esphome_entry.title or device.id)
            external_id = next(
                (
                    str(identifier)
                    for domain, identifier in device.identifiers
                    if str(domain) == "esphome"
                ),
                device.id,
            )
            result[device.id] = {
                "device_id": device.id,
                "name": name,
                "external_id": external_id,
                "sensor_candidates": sensor_candidates,
                **(sensors or {}),
            }
    return result


def _direct_station_options(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    current_subentry_id: str | None = None,
    require_sensors: bool = True,
) -> list[SelectOptionDict]:
    candidates = _direct_station_candidates(
        hass,
        entry,
        current_subentry_id=current_subentry_id,
        require_sensors=require_sensors,
    )
    language = str(getattr(hass.config, "language", "en") or "en").lower()[:2]
    pending_label = {
        "de": "Provisionierung · Messwerte folgen mit der ESP-Firmware",
        "tr": "Kurulum · ölçümler ESP firmware ile gelecek",
        "en": "Provisioning · measurements will follow with ESP firmware",
    }.get(language, "Provisioning · measurements will follow with ESP firmware")
    choose_label = {
        "de": "Sensoren einmal auswählen",
        "tr": "Sensörleri bir kez seç",
        "en": "Select sensors once",
    }.get(language, "Select sensors once")
    return sorted(
        [
            SelectOptionDict(
                value=device_id,
                label=(
                    f"{item['name']} · CO₂ / Temperatur / Luftfeuchtigkeit"
                    if all(key in item for key in ("co2", "temperature", "humidity"))
                    else (
                        f"{item['name']} · {choose_label}"
                        if all(
                            item.get("sensor_candidates", {}).get(kind)
                            for kind in ("co2", "temperature", "humidity")
                        )
                        else f"{item['name']} · {pending_label}"
                    )
                ),
            )
            for device_id, item in candidates.items()
        ],
        key=lambda item: str(item["label"]).casefold(),
    )


def _station_discovery_options(hass: HomeAssistant, entry: ConfigEntry) -> list[SelectOptionDict]:
    options: list[SelectOptionDict] = []
    for hardware_id, item in discovered_stations(hass, entry.entry_id).items():
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or hardware_id)
        master = str(item.get("master_id") or "default")
        options.append(
            SelectOptionDict(
                value=hardware_id,
                label=f"{name} · {hardware_id} · Master {master}",
            )
        )
    return sorted(options, key=lambda item: str(item["label"]).casefold())


def _configured_master_options(
    entry: ConfigEntry,
    *,
    current_subentry_id: str | None = None,
) -> list[SelectOptionDict]:
    return sorted(
        [
            SelectOptionDict(
                value=station.subentry_id, label=_station_title_for_room(entry, station)
            )
            for station in station_subentries(entry)
            if station.subentry_id != current_subentry_id and station_is_master(station)
        ],
        key=lambda item: str(item["label"]).casefold(),
    )


def _direct_sensor_selection_schema(
    hass: HomeAssistant, device_id: str, *, defaults: dict[str, Any] | None = None
) -> vol.Schema:
    candidates = direct_device_sensor_candidates(hass, device_id)
    defaults = defaults or {}
    fields: dict[Any, Any] = {}
    labels = {
        CONF_HARDWARE_DIRECT_CO2: ("co2", "CO₂"),
        CONF_HARDWARE_DIRECT_TEMP: ("temperature", "Temperatur"),
        CONF_HARDWARE_DIRECT_HUMIDITY: ("humidity", "Luftfeuchtigkeit"),
    }
    for field, (kind, _label) in labels.items():
        options = [
            SelectOptionDict(value=entity_id, label=entity_id)
            for entity_id in candidates[kind]
        ]
        default = str(defaults.get(field) or "")
        key = vol.Required(field, default=default) if default in candidates[kind] else vol.Required(field)
        fields[key] = SelectSelector(
            SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
        )
    return vol.Schema(fields)


def _validate_direct_sensor_selection(
    hass: HomeAssistant, device_id: str, user_input: dict[str, Any]
) -> dict[str, str] | None:
    candidates = direct_device_sensor_candidates(hass, device_id)
    selected = {
        "co2": str(user_input.get(CONF_HARDWARE_DIRECT_CO2) or "").strip(),
        "temperature": str(user_input.get(CONF_HARDWARE_DIRECT_TEMP) or "").strip(),
        "humidity": str(user_input.get(CONF_HARDWARE_DIRECT_HUMIDITY) or "").strip(),
    }
    if any(not selected[kind] or selected[kind] not in candidates[kind] for kind in selected):
        return None
    return selected


def _station_role_schema(hass: HomeAssistant) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_HARDWARE_ROLE,
                default=HARDWARE_ROLE_STANDALONE,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_station_role_options(hass),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _station_room_schema_fields(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    defaults: dict[str, Any] | None = None,
    allow_create: bool = True,
) -> dict[Any, Any]:
    defaults = defaults or {}
    rooms = _station_room_options(entry)
    mode_default = str(defaults.get(CONF_HARDWARE_ROOM_MODE) or "").strip()
    if mode_default not in {HARDWARE_ROOM_CREATE, HARDWARE_ROOM_EXISTING}:
        mode_default = HARDWARE_ROOM_EXISTING if defaults.get(CONF_HARDWARE_ROOM_ID) else HARDWARE_ROOM_CREATE
    room_mode_options = _room_mode_options(hass, existing_available=bool(rooms))
    if not allow_create:
        mode_default = HARDWARE_ROOM_EXISTING
        room_mode_options = [
            option for option in room_mode_options
            if option["value"] == HARDWARE_ROOM_EXISTING
        ]
    fields: dict[Any, Any] = {
        vol.Required(CONF_HARDWARE_ROOM_MODE, default=mode_default): SelectSelector(
            SelectSelectorConfig(
                options=room_mode_options,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }
    if allow_create:
        fields[vol.Optional(CONF_ROOM_NAME)] = TextSelector(TextSelectorConfig())
        fields[vol.Optional(CONF_AREA_ID)] = AreaSelector()
    if rooms:
        room_default = str(defaults.get(CONF_HARDWARE_ROOM_ID) or "")
        key = (
            vol.Optional(CONF_HARDWARE_ROOM_ID, default=room_default)
            if room_default
            else vol.Optional(CONF_HARDWARE_ROOM_ID)
        )
        fields[key] = SelectSelector(
            SelectSelectorConfig(options=rooms, mode=SelectSelectorMode.DROPDOWN)
        )
    return fields


def _default_station_room_data(
    name: str,
    *,
    area_id: str | None = None,
) -> dict[str, Any]:
    """Return the same quiet defaults as a newly created manual room."""
    data: dict[str, Any] = {
        CONF_ROOM_NAME: name,
        CONF_TARGET_TEMP: DEFAULT_TARGET_TEMP,
        CONF_NIGHT_START_TIME: DEFAULT_NIGHT_START_TIME,
        CONF_NIGHT_END_TIME: DEFAULT_NIGHT_END_TIME,
        CONF_ROOM_NOTIFY_TRIGGERS: list(DEFAULT_ROOM_NOTIFY_TRIGGERS),
        CONF_REMOTE_ROOM_SHARE: False,
    }
    if area_id:
        data[CONF_AREA_ID] = area_id
    return data


def _prepare_station_room(
    hass: HomeAssistant,
    entry: ConfigEntry,
    user_input: dict[str, Any],
    *,
    current_subentry_id: str | None = None,
) -> tuple[str | None, ConfigSubentry | None, str | None]:
    """Resolve an existing room or prepare a new default room for the station."""
    mode = str(user_input.get(CONF_HARDWARE_ROOM_MODE) or HARDWARE_ROOM_CREATE).strip()
    if mode == HARDWARE_ROOM_EXISTING:
        room_id = str(user_input.get(CONF_HARDWARE_ROOM_ID) or "").strip()
        if error := _station_room_error(
            entry, room_id, current_subentry_id=current_subentry_id
        ):
            return None, None, error
        return room_id, None, None
    if mode != HARDWARE_ROOM_CREATE:
        return None, None, "hardware_room_mode_invalid"

    name = str(user_input.get(CONF_ROOM_NAME) or "").strip()
    if not name:
        return None, None, "hardware_room_name_empty"
    if error := _room_name_error(entry, name):
        return None, None, error

    raw_area = user_input.get(CONF_AREA_ID)
    area_id = str(raw_area).strip() if raw_area else None
    if area_id and room_area_name(hass, area_id) is None:
        return None, None, "area_not_found"

    room = ConfigSubentry(
        data=MappingProxyType(_default_station_room_data(name, area_id=area_id)),
        subentry_type=SUBENTRY_TYPE_ROOM,
        title=name,
        unique_id=None,
    )
    return room.subentry_id, room, None


def _commit_station_room(hass: HomeAssistant, entry: ConfigEntry, room: ConfigSubentry | None) -> None:
    if room is not None:
        hass.config_entries.async_add_subentry(entry, room)


def _normalize_station_id(value: Any) -> str:
    return str(value or "").strip().upper().replace("-", ":")


def _station_room_error(
    entry: ConfigEntry,
    room_id: str,
    *,
    current_subentry_id: str | None = None,
) -> str | None:
    valid_rooms = {str(item["value"]) for item in _station_room_options(entry)}
    if room_id not in valid_rooms:
        return "hardware_room_invalid"
    if any(
        station.subentry_id != current_subentry_id
        and str(station.data.get(CONF_HARDWARE_ROOM_ID) or "") == room_id
        for station in station_subentries(entry)
    ):
        return "hardware_room_duplicate"
    return None


def _hardware_id_duplicate(
    entry: ConfigEntry,
    hardware_id: str,
    *,
    current_subentry_id: str | None = None,
) -> bool:
    wanted = _normalize_station_id(hardware_id)
    return any(
        station.subentry_id != current_subentry_id
        and hardware_id_matches(station.data.get(CONF_HARDWARE_ID), wanted)
        for station in station_subentries(entry)
    )


def _direct_station_input(
    hass: HomeAssistant,
    entry: ConfigEntry,
    user_input: dict[str, Any],
    *,
    role: str,
    current_subentry_id: str | None = None,
) -> tuple[dict[str, Any] | None, ConfigSubentry | None, str | None]:
    room_id, room, error = _prepare_station_room(
        hass,
        entry,
        user_input,
        current_subentry_id=current_subentry_id,
    )
    if error is not None:
        return None, None, error
    assert room_id is not None

    device_id = str(user_input.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
    candidates = _direct_station_candidates(
        hass,
        entry,
        current_subentry_id=current_subentry_id,
        require_sensors=role != HARDWARE_ROLE_MASTER,
    )
    candidate = candidates.get(device_id)
    if candidate is None:
        return None, None, "hardware_direct_device_invalid"

    hardware_id = f"DIRECT:{candidate['external_id']}"
    if _hardware_id_duplicate(
        entry, hardware_id, current_subentry_id=current_subentry_id
    ):
        return None, None, "hardware_id_duplicate"

    data = {
        CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_DIRECT,
        CONF_HARDWARE_ROLE: role,
        CONF_HARDWARE_DEVICE_ID: device_id,
        CONF_HARDWARE_ID: hardware_id,
        CONF_HARDWARE_ROOM_ID: room_id,
    }
    if all(key in candidate for key in ("co2", "temperature", "humidity")):
        data.update(
            {
                CONF_HARDWARE_DIRECT_CO2: candidate["co2"],
                CONF_HARDWARE_DIRECT_TEMP: candidate["temperature"],
                CONF_HARDWARE_DIRECT_HUMIDITY: candidate["humidity"],
            }
        )
    else:
        manual = _validate_direct_sensor_selection(hass, device_id, user_input)
        if manual is None and current_subentry_id:
            current = entry.subentries.get(current_subentry_id)
            if current is not None:
                manual = _validate_direct_sensor_selection(
                    hass, device_id, dict(current.data)
                )
        sensor_candidates = direct_device_sensor_candidates(hass, device_id)
        complete_sensor_set = all(
            sensor_candidates[kind]
            for kind in ("co2", "temperature", "humidity")
        )
        if manual is not None:
            data.update(
                {
                    CONF_HARDWARE_DIRECT_CO2: manual["co2"],
                    CONF_HARDWARE_DIRECT_TEMP: manual["temperature"],
                    CONF_HARDWARE_DIRECT_HUMIDITY: manual["humidity"],
                }
            )
        elif complete_sensor_set:
            return data, room, "hardware_direct_sensor_selection_required"
        elif role != HARDWARE_ROLE_MASTER:
            return None, None, "hardware_direct_device_invalid"
    if role == HARDWARE_ROLE_MASTER:
        location = str(
            user_input.get(CONF_HARDWARE_LOCATION_MODE) or HARDWARE_LOCATION_LOCAL
        ).strip()
        if location not in {HARDWARE_LOCATION_LOCAL, HARDWARE_LOCATION_REMOTE}:
            return None, None, "hardware_location_invalid"
        data[CONF_HARDWARE_LOCATION_MODE] = location
    return data, room, None


def _node_station_input(
    hass: HomeAssistant,
    entry: ConfigEntry,
    user_input: dict[str, Any],
    *,
    current_subentry_id: str | None = None,
) -> tuple[dict[str, Any] | None, ConfigSubentry | None, str | None]:
    room_id, room, error = _prepare_station_room(
        hass,
        entry,
        user_input,
        current_subentry_id=current_subentry_id,
    )
    if error is not None:
        return None, None, error
    assert room_id is not None

    if current_subentry_id:
        current = entry.subentries.get(current_subentry_id)
        hardware_id = (
            _normalize_station_id(current.data.get(CONF_HARDWARE_ID))
            if current is not None
            else ""
        )
    else:
        discovery_id = _normalize_station_id(user_input.get(CONF_HARDWARE_DISCOVERY_ID))
        discovery = (
            discovered_stations(hass, entry.entry_id).get(discovery_id)
            if discovery_id
            else None
        )
        hardware_id = _normalize_station_id(
            (discovery or {}).get("hardware_id")
            if isinstance(discovery, dict)
            else user_input.get(CONF_HARDWARE_ID)
        )
        if not hardware_id:
            hardware_id = _normalize_station_id(user_input.get(CONF_HARDWARE_ID))
    if not hardware_id:
        return None, None, "hardware_id_required"
    if _hardware_id_duplicate(
        entry, hardware_id, current_subentry_id=current_subentry_id
    ):
        return None, None, "hardware_id_duplicate"

    master_subentry_id = str(
        user_input.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or ""
    ).strip()
    master = entry.subentries.get(master_subentry_id)
    if (
        master is None
        or master.subentry_type != SUBENTRY_TYPE_STATION
        or not station_is_master(master)
    ):
        return None, None, "hardware_master_invalid"
    if not _normalize_station_id(master.data.get(CONF_HARDWARE_ID)):
        return None, None, "hardware_master_invalid"

    return {
        CONF_HARDWARE_CONNECTION_TYPE: HARDWARE_CONNECTION_MASTER,
        CONF_HARDWARE_ROLE: HARDWARE_ROLE_NODE,
        CONF_HARDWARE_ID: hardware_id,
        CONF_HARDWARE_MASTER_SUBENTRY_ID: master.subentry_id,
        CONF_HARDWARE_ROOM_ID: room_id,
    }, room, None


def _direct_station_schema(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    role: str,
    current_subentry_id: str | None = None,
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    options = _direct_station_options(
        hass,
        entry,
        current_subentry_id=current_subentry_id,
        require_sensors=role != HARDWARE_ROLE_MASTER,
    )
    defaults = defaults or {}
    device_default = str(defaults.get(CONF_HARDWARE_DEVICE_ID) or "")
    device_key = (
        vol.Required(CONF_HARDWARE_DEVICE_ID, default=device_default)
        if device_default
        else vol.Required(CONF_HARDWARE_DEVICE_ID)
    )
    fields: dict[Any, Any] = {
        device_key: SelectSelector(
            SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
        )
    }
    if role == HARDWARE_ROLE_MASTER:
        fields[
            vol.Required(
                CONF_HARDWARE_LOCATION_MODE,
                default=str(
                    defaults.get(CONF_HARDWARE_LOCATION_MODE)
                    or HARDWARE_LOCATION_LOCAL
                ),
            )
        ] = SelectSelector(
            SelectSelectorConfig(
                options=_location_mode_options(hass),
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
    fields.update(
        _station_room_schema_fields(
            hass,
            entry,
            defaults=defaults,
            allow_create=not bool(defaults.get("_reconfigure_existing_only")),
        )
    )
    return vol.Schema(fields)


def _node_station_schema(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    current_subentry_id: str | None = None,
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    defaults = defaults or {}
    masters = _configured_master_options(
        entry, current_subentry_id=current_subentry_id
    )
    fields: dict[Any, Any] = {}
    if current_subentry_id is None:
        discoveries = _station_discovery_options(hass, entry)
        if discoveries:
            fields[vol.Optional(CONF_HARDWARE_DISCOVERY_ID)] = SelectSelector(
                SelectSelectorConfig(
                    options=discoveries, mode=SelectSelectorMode.DROPDOWN
                )
            )
        hardware_default = str(defaults.get(CONF_HARDWARE_ID) or "")
        hardware_key = (
            vol.Optional(CONF_HARDWARE_ID, default=hardware_default)
            if hardware_default
            else vol.Optional(CONF_HARDWARE_ID)
        )
        fields[hardware_key] = TextSelector(TextSelectorConfig(autocomplete="off"))
    master_default = str(defaults.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or "")
    master_key = (
        vol.Required(CONF_HARDWARE_MASTER_SUBENTRY_ID, default=master_default)
        if master_default
        else vol.Required(CONF_HARDWARE_MASTER_SUBENTRY_ID)
    )
    fields[master_key] = SelectSelector(
        SelectSelectorConfig(options=masters, mode=SelectSelectorMode.DROPDOWN)
    )
    fields.update(
        _station_room_schema_fields(
            hass,
            entry,
            defaults=defaults,
            allow_create=not bool(defaults.get("_reconfigure_existing_only")),
        )
    )
    return vol.Schema(fields)


def _split_wireguard_endpoint(value: str) -> tuple[str, int]:
    endpoint = value.strip()
    if endpoint.startswith("["):
        closing = endpoint.rfind("]")
        if closing <= 0 or closing + 1 >= len(endpoint) or endpoint[closing + 1] != ":":
            raise ValueError("invalid endpoint")
        host = endpoint[1:closing].strip()
        port_text = endpoint[closing + 2 :].strip()
    else:
        if ":" not in endpoint:
            raise ValueError("invalid endpoint")
        host, port_text = endpoint.rsplit(":", 1)
        host = host.strip()
    port = int(port_text)
    if not host or not 1 <= port <= 65535:
        raise ValueError("invalid endpoint")
    return host, port


def _parse_wireguard_config(contents: str) -> dict[str, Any]:
    """Parse the common single-peer WireGuard client export format."""
    sections: dict[str, list[dict[str, str]]] = {"interface": [], "peer": []}
    current: dict[str, str] | None = None
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            if section not in sections:
                current = None
                continue
            current = {}
            sections[section].append(current)
            continue
        if current is None or "=" not in line:
            continue
        key, value = line.split("=", 1)
        current[key.strip().lower()] = value.strip()

    if len(sections["interface"]) != 1 or len(sections["peer"]) != 1:
        raise ValueError("exactly one Interface and one Peer are required")
    interface = sections["interface"][0]
    peer = sections["peer"][0]
    private_key = interface.get("privatekey", "").strip()
    address = interface.get("address", "").split(",", 1)[0].strip()
    public_key = peer.get("publickey", "").strip()
    endpoint = peer.get("endpoint", "").strip()
    allowed_ips = peer.get("allowedips", "").strip()
    if not all((private_key, address, public_key, endpoint, allowed_ips)):
        raise ValueError("required WireGuard values missing")
    host, port = _split_wireguard_endpoint(endpoint)
    keepalive_raw = peer.get("persistentkeepalive", "").strip()
    keepalive = int(keepalive_raw) if keepalive_raw else 0
    if keepalive < 0 or keepalive > 65535:
        raise ValueError("invalid keepalive")

    data: dict[str, Any] = {
        CONF_HARDWARE_WG_ADDRESS: address,
        CONF_HARDWARE_WG_PRIVATE_KEY: private_key,
        CONF_HARDWARE_WG_PEER_PUBLIC_KEY: public_key,
        CONF_HARDWARE_WG_ENDPOINT: endpoint,
        CONF_HARDWARE_WG_ENDPOINT_HOST: host,
        CONF_HARDWARE_WG_ENDPOINT_PORT: port,
        CONF_HARDWARE_WG_ALLOWED_IPS: allowed_ips,
        CONF_HARDWARE_WG_KEEPALIVE: keepalive,
    }
    preshared = peer.get("presharedkey", "").strip()
    if preshared:
        data[CONF_HARDWARE_WG_PRESHARED_KEY] = preshared
    return data


def _read_uploaded_wireguard(hass: HomeAssistant, uploaded_file_id: str) -> dict[str, Any]:
    with process_uploaded_file(hass, uploaded_file_id) as file_path:
        return _parse_wireguard_config(file_path.read_text(encoding="utf-8"))


_WIREGUARD_DATA_KEYS = (
    CONF_HARDWARE_WG_ADDRESS,
    CONF_HARDWARE_WG_PRIVATE_KEY,
    CONF_HARDWARE_WG_PEER_PUBLIC_KEY,
    CONF_HARDWARE_WG_PRESHARED_KEY,
    CONF_HARDWARE_WG_ENDPOINT,
    CONF_HARDWARE_WG_ENDPOINT_HOST,
    CONF_HARDWARE_WG_ENDPOINT_PORT,
    CONF_HARDWARE_WG_ALLOWED_IPS,
    CONF_HARDWARE_WG_KEEPALIVE,
)


def _wireguard_config_complete(data: dict[str, Any] | Any) -> bool:
    required = (
        CONF_HARDWARE_WG_ADDRESS,
        CONF_HARDWARE_WG_PRIVATE_KEY,
        CONF_HARDWARE_WG_PEER_PUBLIC_KEY,
        CONF_HARDWARE_WG_ENDPOINT,
        CONF_HARDWARE_WG_ALLOWED_IPS,
    )
    return all(bool(data.get(key)) for key in required)


def _clear_wireguard_config(data: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(data)
    for key in _WIREGUARD_DATA_KEYS:
        cleaned.pop(key, None)
    return cleaned



class StationSubentryFlow(ConfigSubentryFlow):
    """Create HA-owned room/station topology for one physical Lüftungsstation."""

    def _finish_station(
        self,
        entry: ConfigEntry,
        data: dict[str, Any],
        room: ConfigSubentry | None,
    ):
        _commit_station_room(self.hass, entry, room)
        if room is not None:
            room_title = room.title
        else:
            existing = entry.subentries.get(str(data.get(CONF_HARDWARE_ROOM_ID) or ""))
            room_title = str(existing.title) if existing is not None else "Station"
        role = str(data.get(CONF_HARDWARE_ROLE) or HARDWARE_ROLE_STANDALONE)
        data = dict(data)
        if role == HARDWARE_ROLE_MASTER:
            if not str(data.get(CONF_HARDWARE_MASTER_SECRET) or "").strip():
                data[CONF_HARDWARE_MASTER_SECRET] = secrets.token_urlsafe(32)
        else:
            data.pop(CONF_HARDWARE_MASTER_SECRET, None)
        suffix = "Master" if role == HARDWARE_ROLE_MASTER else "Station"
        return self.async_create_entry(
            title=f"{room_title} · {suffix}",
            data=data,
        )

    async def _continue_direct_setup(
        self,
        entry: ConfigEntry,
        data: dict[str, Any],
        room: ConfigSubentry | None,
    ):
        if (
            data.get(CONF_HARDWARE_ROLE) == HARDWARE_ROLE_MASTER
            and data.get(CONF_HARDWARE_LOCATION_MODE) == HARDWARE_LOCATION_REMOTE
        ):
            self._pending_station_data = data
            self._pending_station_room = room
            return await self.async_step_wireguard()
        return self._finish_station(entry, data, room)

    def _finish_reconfigure(
        self,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        data: dict[str, Any],
    ):
        role = station_role(subentry)
        data = dict(data)
        if role == HARDWARE_ROLE_MASTER:
            old_hardware_id = str(subentry.data.get(CONF_HARDWARE_ID) or "")
            new_hardware_id = str(data.get(CONF_HARDWARE_ID) or "")
            existing_secret = str(
                subentry.data.get(CONF_HARDWARE_MASTER_SECRET) or ""
            ).strip()
            if (
                existing_secret
                and hardware_id_matches(old_hardware_id, new_hardware_id)
            ):
                data[CONF_HARDWARE_MASTER_SECRET] = existing_secret
            else:
                # A physical master replacement receives a fresh credential;
                # ordinary local/remote reconfiguration keeps the old one.
                data[CONF_HARDWARE_MASTER_SECRET] = secrets.token_urlsafe(32)
        else:
            data.pop(CONF_HARDWARE_MASTER_SECRET, None)
        room = entry.subentries.get(str(data.get(CONF_HARDWARE_ROOM_ID) or ""))
        room_title = str(room.title) if room is not None else "Station"
        suffix = "Master" if role == HARDWARE_ROLE_MASTER else "Station"
        return self.async_update_and_abort(
            entry,
            subentry,
            title=f"{room_title} · {suffix}",
            data=data,
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        if entry_kind(entry) != ENTRY_KIND_LOCAL or entry.data.get(CONF_REMOTE_HOST):
            return self.async_abort(reason="remote_read_only")
        if user_input is not None:
            role = str(user_input.get(CONF_HARDWARE_ROLE) or "").strip()
            if role == HARDWARE_ROLE_STANDALONE:
                return await self.async_step_direct()
            if role == HARDWARE_ROLE_MASTER:
                return await self.async_step_master()
            if role == HARDWARE_ROLE_NODE:
                return await self.async_step_node()
            return self.async_show_form(
                step_id="user",
                data_schema=_station_role_schema(self.hass),
                errors={"base": "hardware_role_invalid"},
            )
        return self.async_show_form(
            step_id="user", data_schema=_station_role_schema(self.hass)
        )

    async def async_step_direct(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        if not _direct_station_candidates(self.hass, entry):
            return self.async_abort(reason="hardware_no_direct_devices")
        errors: dict[str, str] = {}
        if user_input is not None:
            data, room, error = _direct_station_input(
                self.hass,
                entry,
                user_input,
                role=HARDWARE_ROLE_STANDALONE,
            )
            if error == "hardware_direct_sensor_selection_required":
                assert data is not None
                self._pending_direct_station_data = data
                self._pending_direct_station_room = room
                return await self.async_step_direct_sensors()
            if error is not None:
                errors["base"] = error
            else:
                assert data is not None
                return await self._continue_direct_setup(entry, data, room)
        return self.async_show_form(
            step_id="direct",
            data_schema=_direct_station_schema(
                self.hass, entry, role=HARDWARE_ROLE_STANDALONE
            ),
            errors=errors,
        )

    async def async_step_master(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        if not _direct_station_candidates(self.hass, entry, require_sensors=False):
            return self.async_abort(reason="hardware_no_direct_devices")
        errors: dict[str, str] = {}
        if user_input is not None:
            data, room, error = _direct_station_input(
                self.hass,
                entry,
                user_input,
                role=HARDWARE_ROLE_MASTER,
            )
            if error == "hardware_direct_sensor_selection_required":
                assert data is not None
                self._pending_direct_station_data = data
                self._pending_direct_station_room = room
                return await self.async_step_direct_sensors()
            if error is not None:
                errors["base"] = error
            else:
                assert data is not None
                return await self._continue_direct_setup(entry, data, room)
        return self.async_show_form(
            step_id="master",
            data_schema=_direct_station_schema(
                self.hass, entry, role=HARDWARE_ROLE_MASTER
            ),
            errors=errors,
        )

    async def async_step_direct_sensors(
        self, user_input: dict[str, Any] | None = None
    ):
        entry = self._get_entry()
        data = getattr(self, "_pending_direct_station_data", None)
        room = getattr(self, "_pending_direct_station_room", None)
        if not isinstance(data, dict):
            return self.async_abort(reason="hardware_setup_lost")
        device_id = str(data.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
        if not device_id:
            return self.async_abort(reason="hardware_setup_lost")

        errors: dict[str, str] = {}
        if user_input is not None:
            selected = _validate_direct_sensor_selection(
                self.hass, device_id, user_input
            )
            if selected is None:
                errors["base"] = "hardware_direct_sensor_selection_invalid"
            else:
                data = dict(data)
                data.update(
                    {
                        CONF_HARDWARE_DIRECT_CO2: selected["co2"],
                        CONF_HARDWARE_DIRECT_TEMP: selected["temperature"],
                        CONF_HARDWARE_DIRECT_HUMIDITY: selected["humidity"],
                    }
                )
                self._pending_direct_station_data = None
                self._pending_direct_station_room = None
                return await self._continue_direct_setup(entry, data, room)

        return self.async_show_form(
            step_id="direct_sensors",
            data_schema=_direct_sensor_selection_schema(self.hass, device_id),
            errors=errors,
        )

    async def async_step_wireguard(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        pending = getattr(self, "_pending_station_data", None)
        if not isinstance(pending, dict):
            return self.async_abort(reason="hardware_setup_lost")
        errors: dict[str, str] = {}
        if user_input is not None:
            uploaded = str(user_input.get(CONF_HARDWARE_WIREGUARD_FILE) or "").strip()
            try:
                wireguard = await self.hass.async_add_executor_job(
                    _read_uploaded_wireguard, self.hass, uploaded
                )
            except (OSError, UnicodeError, ValueError):
                errors["base"] = "hardware_wireguard_invalid"
            else:
                data = {**pending, **wireguard}
                room = getattr(self, "_pending_station_room", None)
                self._pending_station_data = None
                self._pending_station_room = None
                return self._finish_station(entry, data, room)
        return self.async_show_form(
            step_id="wireguard",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HARDWARE_WIREGUARD_FILE): FileSelector(
                        FileSelectorConfig(accept=".conf,.txt,text/plain")
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_node(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        if not _configured_master_options(entry):
            return self.async_abort(reason="hardware_no_masters")
        errors: dict[str, str] = {}
        if user_input is not None:
            data, room, error = _node_station_input(self.hass, entry, user_input)
            if error is not None:
                errors["base"] = error
            else:
                assert data is not None
                return self._finish_station(entry, data, room)
        return self.async_show_form(
            step_id="node",
            data_schema=_node_station_schema(self.hass, entry),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        subentry = self._get_reconfigure_subentry()
        role = station_role(subentry)
        if role == HARDWARE_ROLE_NODE:
            return await self.async_step_reconfigure_node(user_input)
        return await self.async_step_reconfigure_direct(user_input)

    async def async_step_reconfigure_direct(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        role = station_role(subentry)
        errors: dict[str, str] = {}
        defaults = dict(subentry.data)
        defaults[CONF_HARDWARE_ROOM_MODE] = HARDWARE_ROOM_EXISTING
        defaults["_reconfigure_existing_only"] = True
        if user_input is not None:
            data, _room, error = _direct_station_input(
                self.hass,
                entry,
                user_input,
                role=role,
                current_subentry_id=subentry.subentry_id,
            )
            if error == "hardware_direct_sensor_selection_required":
                assert data is not None
                self._pending_reconfigure_sensor_data = {**dict(subentry.data), **data}
                self._pending_reconfigure_sensor_subentry_id = subentry.subentry_id
                return await self.async_step_reconfigure_direct_sensors()
            if error is not None:
                errors["base"] = error
            else:
                assert data is not None
                # Reconfigure never creates a second room; the existing room can
                # be renamed/configured through the normal room subentry flow.
                data = {**dict(subentry.data), **data}
                if role == HARDWARE_ROLE_MASTER:
                    location = str(
                        data.get(CONF_HARDWARE_LOCATION_MODE)
                        or HARDWARE_LOCATION_LOCAL
                    )
                    if location == HARDWARE_LOCATION_LOCAL:
                        data = _clear_wireguard_config(data)
                        return self._finish_reconfigure(entry, subentry, data)
                    self._pending_reconfigure_data = data
                    self._pending_reconfigure_subentry_id = subentry.subentry_id
                    previous_location = str(
                        subentry.data.get(CONF_HARDWARE_LOCATION_MODE)
                        or HARDWARE_LOCATION_LOCAL
                    )
                    self._pending_reconfigure_wireguard_required = (
                        previous_location != HARDWARE_LOCATION_REMOTE
                        or not _wireguard_config_complete(dict(subentry.data))
                    )
                    return await self.async_step_reconfigure_wireguard()
                return self._finish_reconfigure(entry, subentry, data)
        return self.async_show_form(
            step_id="reconfigure_direct",
            data_schema=_direct_station_schema(
                self.hass,
                entry,
                role=role,
                current_subentry_id=subentry.subentry_id,
                defaults=defaults,
            ),
            errors=errors,
        )

    async def async_step_reconfigure_direct_sensors(
        self, user_input: dict[str, Any] | None = None
    ):
        entry = self._get_entry()
        data = getattr(self, "_pending_reconfigure_sensor_data", None)
        subentry_id = str(
            getattr(self, "_pending_reconfigure_sensor_subentry_id", "") or ""
        )
        subentry = entry.subentries.get(subentry_id)
        if not isinstance(data, dict) or subentry is None:
            return self.async_abort(reason="hardware_setup_lost")
        device_id = str(data.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
        if not device_id:
            return self.async_abort(reason="hardware_setup_lost")

        errors: dict[str, str] = {}
        if user_input is not None:
            selected = _validate_direct_sensor_selection(
                self.hass, device_id, user_input
            )
            if selected is None:
                errors["base"] = "hardware_direct_sensor_selection_invalid"
            else:
                data = dict(data)
                data.update(
                    {
                        CONF_HARDWARE_DIRECT_CO2: selected["co2"],
                        CONF_HARDWARE_DIRECT_TEMP: selected["temperature"],
                        CONF_HARDWARE_DIRECT_HUMIDITY: selected["humidity"],
                    }
                )
                self._pending_reconfigure_sensor_data = None
                self._pending_reconfigure_sensor_subentry_id = None
                if station_role(subentry) == HARDWARE_ROLE_MASTER:
                    location = str(
                        data.get(CONF_HARDWARE_LOCATION_MODE)
                        or HARDWARE_LOCATION_LOCAL
                    )
                    if location == HARDWARE_LOCATION_LOCAL:
                        return self._finish_reconfigure(
                            entry, subentry, _clear_wireguard_config(data)
                        )
                    self._pending_reconfigure_data = data
                    self._pending_reconfigure_subentry_id = subentry.subentry_id
                    previous_location = str(
                        subentry.data.get(CONF_HARDWARE_LOCATION_MODE)
                        or HARDWARE_LOCATION_LOCAL
                    )
                    self._pending_reconfigure_wireguard_required = (
                        previous_location != HARDWARE_LOCATION_REMOTE
                        or not _wireguard_config_complete(dict(subentry.data))
                    )
                    return await self.async_step_reconfigure_wireguard()
                return self._finish_reconfigure(entry, subentry, data)

        return self.async_show_form(
            step_id="reconfigure_direct_sensors",
            data_schema=_direct_sensor_selection_schema(
                self.hass, device_id, defaults=dict(subentry.data)
            ),
            errors=errors,
        )

    async def async_step_reconfigure_wireguard(
        self, user_input: dict[str, Any] | None = None
    ):
        entry = self._get_entry()
        data = getattr(self, "_pending_reconfigure_data", None)
        subentry_id = str(
            getattr(self, "_pending_reconfigure_subentry_id", "") or ""
        )
        subentry = entry.subentries.get(subentry_id)
        if not isinstance(data, dict) or subentry is None:
            return self.async_abort(reason="hardware_setup_lost")

        required = bool(
            getattr(self, "_pending_reconfigure_wireguard_required", False)
        )
        errors: dict[str, str] = {}
        if user_input is not None:
            uploaded = str(
                user_input.get(CONF_HARDWARE_WIREGUARD_FILE) or ""
            ).strip()
            if not uploaded and required:
                errors["base"] = "hardware_wireguard_required"
            elif uploaded:
                try:
                    wireguard = await self.hass.async_add_executor_job(
                        _read_uploaded_wireguard, self.hass, uploaded
                    )
                except (OSError, UnicodeError, ValueError):
                    errors["base"] = "hardware_wireguard_invalid"
                else:
                    data = {**_clear_wireguard_config(data), **wireguard}
                    self._pending_reconfigure_data = None
                    self._pending_reconfigure_subentry_id = None
                    self._pending_reconfigure_wireguard_required = False
                    return self._finish_reconfigure(entry, subentry, data)
            else:
                # remote -> remote without a new upload explicitly keeps the
                # already stored profile. local -> remote never reaches here
                # without `required=True`.
                self._pending_reconfigure_data = None
                self._pending_reconfigure_subentry_id = None
                self._pending_reconfigure_wireguard_required = False
                return self._finish_reconfigure(entry, subentry, data)

        file_key = (
            vol.Required(CONF_HARDWARE_WIREGUARD_FILE)
            if required
            else vol.Optional(CONF_HARDWARE_WIREGUARD_FILE)
        )
        return self.async_show_form(
            step_id="reconfigure_wireguard",
            data_schema=vol.Schema(
                {
                    file_key: FileSelector(
                        FileSelectorConfig(accept=".conf,.txt,text/plain")
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure_node(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        defaults = dict(subentry.data)
        defaults[CONF_HARDWARE_ROOM_MODE] = HARDWARE_ROOM_EXISTING
        defaults["_reconfigure_existing_only"] = True
        if user_input is not None:
            data, _room, error = _node_station_input(
                self.hass,
                entry,
                user_input,
                current_subentry_id=subentry.subentry_id,
            )
            if error is not None:
                errors["base"] = error
            else:
                assert data is not None
                data = {**dict(subentry.data), **data}
                data.pop(CONF_HARDWARE_MASTER_ID, None)
                return self._finish_reconfigure(entry, subentry, data)
        return self.async_show_form(
            step_id="reconfigure_node",
            data_schema=_node_station_schema(
                self.hass,
                entry,
                current_subentry_id=subentry.subentry_id,
                defaults=defaults,
            ),
            errors=errors,
        )


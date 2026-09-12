"""Config flow for Lüftungsberater."""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigSubentryFlow
from homeassistant.const import UnitOfTemperature
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import SectionConfig, section
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    AreaSelector,
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
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
from .const import (
    CONF_AREA_ID,
    CONF_CLIMATE,
    CONF_DISPLAY_MODE,
    CONF_CO2,
    CONF_ENTRY_KIND,
    CONF_INDOOR_HUMIDITY,
    CONF_INDOOR_TEMP,
    CONF_INSTANCE_NAME,
    CONF_MANUAL_OUTDOOR,
    CONF_NOTIFY_TARGET,
    CONF_NOTIFY_TRIGGERS,
    CONF_ROOM_NOTIFY_TRIGGERS,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_CO2,
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
            if key in {CONF_OUTDOOR_TEMP, CONF_OUTDOOR_HUMIDITY, CONF_OUTDOOR_CO2}
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
    for key in (CONF_OUTDOOR_TEMP, CONF_OUTDOOR_HUMIDITY, CONF_OUTDOOR_CO2):
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
                        vol.Required(CONF_INDOOR_TEMP): _entity(
                            "sensor", device_class=SensorDeviceClass.TEMPERATURE
                        ),
                        vol.Required(CONF_INDOOR_HUMIDITY): _entity(
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
        for key in (CONF_CO2, CONF_SURFACE_TEMP)
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
    MINOR_VERSION = 9

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
        return {SUBENTRY_TYPE_ROOM: RoomSubentryFlow}


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

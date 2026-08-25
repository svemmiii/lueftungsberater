"""Config flow for Lüftungsberater."""
from __future__ import annotations

import asyncio
import logging
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
)
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import (
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
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_CO2,
    CONF_OUTDOOR_TEMP,
    CONF_REMOTE_HOST,
    CONF_REMOTE_PORT,
    CONF_REMOTE_TOKEN,
    CONF_REMOTE_USE_SSL,
    CONF_ROOM_NAME,
    CONF_TARGET_TEMP,
    CONF_SURFACE_TEMP,
    CONF_NIGHT_START_HOUR,
    CONF_WARNING_SOURCE,
    CONF_WEATHER,
    CONF_WINDOWS,
    DEFAULT_REMOTE_PORT,
    DEFAULT_DISPLAY_MODE,
    DEFAULT_NIGHT_START_HOUR,
    DEFAULT_NOTIFY_TRIGGERS,
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
    entry_kind,
)
_LOGGER = logging.getLogger(__name__)


from .remote import (
    RemoteAuthError,
    RemoteConnectionError,
    async_fetch_remote_snapshot,
    async_host_is_tailscale,
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
    schema: dict[Any, Any] = {
        vol.Required(CONF_WEATHER): _entity("weather"),
        vol.Optional(CONF_WARNING_SOURCE, default=WARNING_SOURCE_NONE): SelectSelector(
            SelectSelectorConfig(
                options=_warning_source_options(hass),
                mode=SelectSelectorMode.DROPDOWN,
                translation_key="warning_source",
            )
        ),
        vol.Optional(CONF_DISPLAY_MODE, default=DEFAULT_DISPLAY_MODE): SelectSelector(
            SelectSelectorConfig(
                options=[DISPLAY_MODE_VENTILATION, DISPLAY_MODE_ROOM_AIR],
                mode=SelectSelectorMode.DROPDOWN,
                translation_key="display_mode",
            )
        ),
        vol.Optional(CONF_MANUAL_OUTDOOR): section(
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
        vol.Optional(CONF_NOTIFY_TARGET): _entity("notify"),
        vol.Optional(
            CONF_NOTIFY_TRIGGERS, default=DEFAULT_NOTIFY_TRIGGERS
        ): SelectSelector(
            SelectSelectorConfig(
                options=[
                    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
                    NOTIFY_TRIGGER_AIRING_FINISHED,
                    NOTIFY_TRIGGER_AIR_DANGER,
                    NOTIFY_TRIGGER_AIR_CAUTION,
                    NOTIFY_TRIGGER_WEATHER_DANGER,
                    NOTIFY_TRIGGER_WEATHER_CAUTION,
                ],
                multiple=True,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key="notify_triggers",
            )
        ),
    }

    return vol.Schema(schema)


def _local_schema(hass: HomeAssistant) -> vol.Schema:
    base = dict(_global_schema(hass).schema)
    return vol.Schema(
        {
            vol.Required(CONF_INSTANCE_NAME, default="Lüftungsberater"): TextSelector(
                TextSelectorConfig()
            ),
            **base,
        }
    )


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
            vol.Required(CONF_ROOM_NAME): TextSelector(TextSelectorConfig()),
            vol.Required(CONF_INDOOR_TEMP): _entity(
                "sensor", device_class=SensorDeviceClass.TEMPERATURE
            ),
            vol.Required(CONF_INDOOR_HUMIDITY): _entity(
                "sensor", device_class=SensorDeviceClass.HUMIDITY
            ),
            vol.Optional(CONF_CO2): _entity(
                "sensor", device_class=SensorDeviceClass.CO2
            ),
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
            vol.Optional(CONF_SURFACE_TEMP): _entity(
                "sensor", device_class=SensorDeviceClass.TEMPERATURE
            ),
            vol.Optional(CONF_CLIMATE): _entity("climate"),
            vol.Optional(CONF_NIGHT_START_HOUR, default=DEFAULT_NIGHT_START_HOUR): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=23,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="h",
                )
            ),
            vol.Optional(CONF_TARGET_TEMP, default=default_value): NumberSelector(
                NumberSelectorConfig(
                    min=min_value,
                    max=max_value,
                    step=step,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement=unit,
                )
            ),
        }
    )


def _normalize_room_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, Any]:
    data = dict(user_input)
    if CONF_TARGET_TEMP in data:
        data[CONF_TARGET_TEMP] = _stored_temperature(hass, data[CONF_TARGET_TEMP])
    return data


def _remote_data(user_input: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    data = dict(user_input)
    name = str(data.pop(CONF_INSTANCE_NAME)).strip()
    data[CONF_ENTRY_KIND] = ENTRY_KIND_REMOTE
    data[CONF_REMOTE_HOST] = str(data[CONF_REMOTE_HOST]).strip().strip("[]").rstrip("/")
    data[CONF_REMOTE_PORT] = int(data[CONF_REMOTE_PORT])
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
        payload = await async_fetch_remote_snapshot(hass, data)
    except RemoteAuthError:
        return "invalid_auth", None
    except RemoteConnectionError:
        return "cannot_connect", None
    return None, payload


async def _validate_remote(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Compatibility wrapper used by tests and reconfiguration helpers."""
    error, _payload = await _test_remote(hass, data)
    return error


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
        instance_name = str(instance.get("name") or f"Lüftungsberater {index}")
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
    MINOR_VERSION = 4

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="user",
            menu_options=["local", "remote"],
        )

    async def async_step_local(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = dict(user_input)
            title = str(data.pop(CONF_INSTANCE_NAME)).strip() or "Lüftungsberater"
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
                        CONF_INSTANCE_NAME, default="Lüftungsberater"
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
            duplicate = any(
                entry_kind(entry) == ENTRY_KIND_REMOTE
                and entry.data.get(CONF_REMOTE_HOST) == data.get(CONF_REMOTE_HOST)
                and int(entry.data.get(CONF_REMOTE_PORT, DEFAULT_REMOTE_PORT))
                == data.get(CONF_REMOTE_PORT)
                for entry in self._async_current_entries()
            )
            if duplicate:
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

        self._pending_remote_error = error
        if error is None:
            fallback_title = getattr(self, "_pending_remote_title", "Home Assistant")
            self._pending_remote_summary = _remote_summary(payload, fallback_title)
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

        if user_input is not None:
            return self.async_create_entry(title=title, data=data)
        self._set_confirm_only()
        return self.async_show_form(
            step_id="remote_confirm",
            data_schema=vol.Schema({}),
            description_placeholders=getattr(
                self,
                "_pending_remote_summary",
                {"instances": "0", "rooms": "0"},
            ),
            last_step=True,
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
            data = dict(user_input)
            title = str(data.pop(CONF_INSTANCE_NAME)).strip() or entry.title
            data[CONF_ENTRY_KIND] = ENTRY_KIND_LOCAL
            self.hass.config_entries.async_update_entry(entry, title=title, data=data)
            return self.async_abort(reason="reconfigure_successful")

        manual = entry.data.get(CONF_MANUAL_OUTDOOR)
        if not isinstance(manual, dict):
            manual = {}
        if not manual.get(CONF_OUTDOOR_TEMP):
            old = entry.data.get(CONF_OUTDOOR_TEMP)
            if isinstance(old, str) and old:
                manual[CONF_OUTDOOR_TEMP] = old
        if not manual.get(CONF_OUTDOOR_HUMIDITY):
            old = entry.data.get(CONF_OUTDOOR_HUMIDITY)
            if isinstance(old, str) and old:
                manual[CONF_OUTDOOR_HUMIDITY] = old

        if not manual.get(CONF_OUTDOOR_CO2):
            old = entry.data.get(CONF_OUTDOOR_CO2)
            if isinstance(old, str) and old:
                manual[CONF_OUTDOOR_CO2] = old

        defaults: dict[str, Any] = {
            CONF_INSTANCE_NAME: entry.title,
            CONF_WEATHER: entry.data.get(CONF_WEATHER),
            CONF_WARNING_SOURCE: entry.data.get(CONF_WARNING_SOURCE, WARNING_SOURCE_NONE),
            CONF_DISPLAY_MODE: entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE),
            CONF_NOTIFY_TARGET: entry.data.get(CONF_NOTIFY_TARGET),
            CONF_NOTIFY_TRIGGERS: entry.data.get(
                CONF_NOTIFY_TRIGGERS, DEFAULT_NOTIFY_TRIGGERS
            ),
        }
        if manual:
            defaults[CONF_MANUAL_OUTDOOR] = manual
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _local_schema(self.hass),
                defaults,
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
            error, payload = await _test_remote(self.hass, data)
            if error is None:
                self._pending_remote_title = title
                self._pending_remote_data = data
                self._pending_remote_summary = _remote_summary(payload, title)
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
        if user_input is not None:
            self.hass.config_entries.async_update_entry(entry, title=title, data=data)
            return self.async_abort(reason="reconfigure_successful")
        self._set_confirm_only()
        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=vol.Schema({}),
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


class RoomSubentryFlow(ConfigSubentryFlow):
    """Room subentry flow."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        if entry_kind(entry) != ENTRY_KIND_LOCAL or entry.data.get(CONF_REMOTE_HOST):
            return self.async_abort(reason="remote_read_only")
        if user_input is not None:
            name = user_input[CONF_ROOM_NAME].strip()
            data = _normalize_room_input(self.hass, user_input)
            return self.async_create_entry(title=name, data=data, unique_id=name.casefold())
        return self.async_show_form(step_id="user", data_schema=_room_schema(self.hass))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            name = user_input[CONF_ROOM_NAME].strip()
            data = _normalize_room_input(self.hass, user_input)
            return self.async_update_and_abort(entry, subentry, title=name, data=data)

        defaults = dict(subentry.data)
        if CONF_TARGET_TEMP in defaults:
            defaults[CONF_TARGET_TEMP] = _display_temperature(
                self.hass, float(defaults[CONF_TARGET_TEMP])
            )
        schema = self.add_suggested_values_to_schema(_room_schema(self.hass), defaults)
        return self.async_show_form(step_id="reconfigure", data_schema=schema)

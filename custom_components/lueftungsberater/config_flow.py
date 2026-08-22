"""Config flow for Lüftungsberater."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigSubentryFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import SectionConfig, section
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
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
)

from .const import (
    CONF_CLIMATE,
    CONF_CO2,
    CONF_INDOOR_HUMIDITY,
    CONF_INDOOR_TEMP,
    CONF_MANUAL_OUTDOOR,
    CONF_OUTDOOR_HUMIDITY,
    CONF_OUTDOOR_TEMP,
    CONF_ROOM_NAME,
    CONF_TARGET_TEMP,
    CONF_WARNING_SOURCE,
    CONF_WEATHER,
    CONF_WINDOWS,
    DEFAULT_TARGET_TEMP,
    DOMAIN,
    SUBENTRY_TYPE_ROOM,
    WARNING_SOURCE_NONE,
)


def _entity(
    domain: str | list[str],
    multiple: bool = False,
) -> EntitySelector:
    return EntitySelector(
        EntitySelectorConfig(
            domain=domain,
            multiple=multiple,
        )
    )


def _warning_source_options(
    hass: HomeAssistant,
) -> list[SelectOptionDict]:
    """Build a friendly list of installed warning providers."""
    registry = er.async_get(hass)
    options: list[SelectOptionDict] = [
        SelectOptionDict(
            value=WARNING_SOURCE_NONE,
            label="Kein Warndienst",
        )
    ]

    known_domains = {
        "nina",
        "dwd_weather_warnings",
    }

    for entry in hass.config_entries.async_entries():
        if entry.domain == DOMAIN:
            continue

        entities = er.async_entries_for_config_entry(
            registry,
            entry.entry_id,
        )

        looks_like_warning = entry.domain in known_domains

        if not looks_like_warning:
            for entity in entities:
                low = " ".join(
                    (
                        entity.entity_id,
                        entity.original_name or "",
                    )
                ).lower()
                if (
                    "warn" in low
                    or "warning" in low
                    or "nina" in low
                ):
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
    """Build the simple global setup form."""
    return vol.Schema(
        {
            vol.Required(CONF_WEATHER): _entity("weather"),
            vol.Optional(
                CONF_WARNING_SOURCE,
                default=WARNING_SOURCE_NONE,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_warning_source_options(hass),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_MANUAL_OUTDOOR): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_OUTDOOR_TEMP): _entity("sensor"),
                        vol.Optional(CONF_OUTDOOR_HUMIDITY): _entity("sensor"),
                    }
                ),
                SectionConfig(collapsed=True),
            ),
        }
    )


ROOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ROOM_NAME): TextSelector(TextSelectorConfig()),
        vol.Required(CONF_INDOOR_TEMP): _entity("sensor"),
        vol.Required(CONF_INDOOR_HUMIDITY): _entity("sensor"),
        vol.Optional(CONF_CO2): _entity("sensor"),
        vol.Optional(CONF_WINDOWS): _entity(
            "binary_sensor",
            multiple=True,
        ),
        vol.Optional(CONF_CLIMATE): _entity("climate"),
        vol.Optional(
            CONF_TARGET_TEMP,
            default=DEFAULT_TARGET_TEMP,
        ): NumberSelector(
            NumberSelectorConfig(
                min=5,
                max=35,
                step=0.5,
                mode=NumberSelectorMode.BOX,
            )
        ),
    }
)


class LueftungsberaterConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Global config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        if user_input is not None:
            if self._async_current_entries():
                return self.async_abort(
                    reason="single_instance_allowed"
                )
            return self.async_create_entry(
                title="Lüftungsberater",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_global_schema(self.hass),
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            return self.async_update_and_abort(
                entry,
                data_updates=user_input,
            )

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

        defaults = {
            CONF_WEATHER: entry.data.get(CONF_WEATHER),
            CONF_WARNING_SOURCE: entry.data.get(
                CONF_WARNING_SOURCE,
                WARNING_SOURCE_NONE,
            ),
        }
        if manual:
            defaults[CONF_MANUAL_OUTDOOR] = manual

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _global_schema(self.hass),
                defaults,
            ),
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls,
        config_entry: ConfigEntry,
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_TYPE_ROOM: RoomSubentryFlow}


class RoomSubentryFlow(ConfigSubentryFlow):
    """Room subentry flow."""

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        if user_input is not None:
            name = user_input[CONF_ROOM_NAME].strip()
            return self.async_create_entry(
                title=name,
                data=user_input,
                unique_id=name.casefold(),
            )
        return self.async_show_form(
            step_id="user",
            data_schema=ROOM_SCHEMA,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()

        if user_input is not None:
            name = user_input[CONF_ROOM_NAME].strip()
            return self.async_update_and_abort(
                entry,
                subentry,
                title=name,
                data=user_input,
            )

        schema = self.add_suggested_values_to_schema(
            ROOM_SCHEMA,
            dict(subentry.data),
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
        )

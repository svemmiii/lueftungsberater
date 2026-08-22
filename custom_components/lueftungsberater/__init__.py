"""Lüftungsberater integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .airing import async_get_or_create_tracker, async_stop_entry_trackers
from .co2 import async_get_or_create_co2_tracker, async_stop_entry_co2_trackers
from .const import PLATFORMS, SUBENTRY_TYPE_ROOM

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = "/lueftungsberater/frontend"
FRONTEND_FILE = "lueftungsberater-card.js"
FRONTEND_VERSION = "0.6.6"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve and automatically register the dashboard cards."""
    frontend_dir = Path(__file__).parent / "frontend"

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL, str(frontend_dir), False)]
        )
    except RuntimeError:
        pass

    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        _LOGGER.warning("Lovelace is unavailable; card resource was not registered")
        return

    if lovelace.resource_mode != MODE_STORAGE:
        _LOGGER.warning(
            "Lovelace resources are not in storage mode. Register %s/%s manually.",
            FRONTEND_URL,
            FRONTEND_FILE,
        )
        return

    resources = lovelace.resources
    await resources.async_get_info()

    base_url = f"{FRONTEND_URL}/{FRONTEND_FILE}"
    wanted_url = f"{base_url}?v={FRONTEND_VERSION}"

    existing = None
    for resource in resources.async_items():
        resource_url = str(resource.get("url", ""))
        if resource_url.split("?", 1)[0] == base_url:
            existing = resource
            break

    if existing is None:
        await resources.async_create_item(
            {"res_type": "module", "url": wanted_url}
        )
        _LOGGER.info("Registered Lüftungsberater dashboard cards")
        return

    if existing.get("url") != wanted_url or existing.get("type") != "module":
        await resources.async_update_item(
            existing["id"],
            {"res_type": "module", "url": wanted_url},
        )
        _LOGGER.info(
            "Updated Lüftungsberater dashboard cards to frontend %s",
            FRONTEND_VERSION,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lüftungsberater."""
    await _async_register_frontend(hass)

    for subentry in entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM:
            await async_get_or_create_tracker(hass, entry, subentry)
            await async_get_or_create_co2_tracker(hass, entry, subentry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration after config/subentry changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload platforms and trackers."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await async_stop_entry_trackers(hass, entry)
        await async_stop_entry_co2_trackers(hass, entry)
    return unloaded

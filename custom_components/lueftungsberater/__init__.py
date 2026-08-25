"""Lüftungsberater integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .airing import async_get_or_create_tracker, async_stop_entry_trackers
from .air_quality import async_get_or_create_air_quality_tracker, async_stop_air_quality_tracker
from .api import async_register_api
from .co2 import async_get_or_create_co2_tracker, async_stop_entry_co2_trackers
from .mold import async_get_or_create_mold_tracker, async_stop_entry_mold_trackers
from .coordinator import (
    async_get_or_create_room_coordinator,
    async_stop_entry_coordinators,
)
from .const import (
    CONF_ENTRY_KIND,
    CONF_REMOTE_HOST,
    ENTRY_KIND_LOCAL,
    ENTRY_KIND_REMOTE,
    LEGACY_NOTIFY_KEYS,
    PLATFORMS,
    SUBENTRY_TYPE_ROOM,
    entry_kind,
)
from .remote import (
    async_get_or_create_remote_coordinator,
    async_stop_remote_coordinator,
)
from .remote_devices import async_sync_remote_room_devices

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = "/lueftungsberater/frontend"
FRONTEND_FILE = "lueftungsberater-card.js"
FRONTEND_VERSION = "0.6.23"


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
        await resources.async_create_item({"res_type": "module", "url": wanted_url})
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


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate Lüftungsberater config entries without guessing replacements."""
    updates: dict[str, object] = {}

    if entry.version == 1 and entry.minor_version < 2:
        # v0.6.12 briefly assigned random local unique IDs. A ConfigEntry unique
        # ID must be stable and identify a real device/service, so remove only
        # that known temporary format. The normal entry_id remains untouched.
        if (
            entry_kind(entry) == ENTRY_KIND_LOCAL
            and isinstance(entry.unique_id, str)
            and entry.unique_id.startswith("local:")
        ):
            updates["unique_id"] = None

    if entry.version == 1 and entry.minor_version < 3:
        # v0.6.20 uses Home Assistant's notify entity action exclusively. Old
        # Companion-App-specific service/vibration options are removed rather
        # than guessed into a new target. A configured notify_target survives.
        cleaned_data = dict(entry.data)
        for key in LEGACY_NOTIFY_KEYS:
            cleaned_data.pop(key, None)
        if cleaned_data != dict(entry.data):
            updates["data"] = cleaned_data
        updates["minor_version"] = 3

    if entry.version == 1 and entry.minor_version < 4:
        # v0.6.23 changes which config-entry kinds support room subentries.
        # Persist the kind for older Tailscale entries which predate the marker
        # so Home Assistant can always expose them as read-only afterwards.
        cleaned_data = dict(updates.get("data", entry.data))
        if cleaned_data.get(CONF_REMOTE_HOST) and not cleaned_data.get(CONF_ENTRY_KIND):
            cleaned_data[CONF_ENTRY_KIND] = ENTRY_KIND_REMOTE
            updates["data"] = cleaned_data
        updates["minor_version"] = 4

    if updates:
        hass.config_entries.async_update_entry(entry, **updates)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one local or Tailscale-remote Lüftungsberater entry."""
    # Home Assistant caches supported_subentry_types on the ConfigEntry object.
    # Custom integration reloads keep that object alive, so a remote entry may
    # otherwise keep the old "Add room" capability until a full HA restart.
    # There is currently no public invalidation method for this cache.
    if hasattr(entry, "_supported_subentry_types"):
        object.__setattr__(entry, "_supported_subentry_types", None)
        entry.clear_state_cache()

    await _async_register_frontend(hass)
    async_register_api(hass)

    kind = entry_kind(entry)
    if kind == ENTRY_KIND_REMOTE:
        coordinator = await async_get_or_create_remote_coordinator(hass, entry)
        # Receiving Home Assistants deliberately keep remote measurements
        # transient: no mirrored entities, recorder rows or histories are
        # created. Only lightweight room cards are mirrored into the device
        # registry so the remote connection remains visible without the old
        # duplicate Remote-HA -> Lüftungsberater hierarchy.
        async_sync_remote_room_devices(hass, entry, coordinator.data)

        # A coordinator without entities needs a listener both to keep polling
        # active and to keep the lightweight room topology in sync.
        entry.async_on_unload(
            coordinator.async_add_listener(
                lambda: async_sync_remote_room_devices(hass, entry, coordinator.data)
            )
        )
        entry.async_on_unload(entry.add_update_listener(_async_reload))
        return True

    await async_get_or_create_air_quality_tracker(hass, entry)

    for subentry in entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM:
            await async_get_or_create_tracker(hass, entry, subentry)
            await async_get_or_create_co2_tracker(hass, entry, subentry)
            await async_get_or_create_mold_tracker(hass, entry, subentry)
            await async_get_or_create_room_coordinator(hass, entry, subentry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration after config/subentry changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload local platforms/trackers or a remote coordinator."""
    if entry_kind(entry) == ENTRY_KIND_REMOTE:
        await async_stop_remote_coordinator(hass, entry)
        return True

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_stop_air_quality_tracker(hass, entry)
        await async_stop_entry_coordinators(hass, entry)
        await async_stop_entry_trackers(hass, entry)
        await async_stop_entry_co2_trackers(hass, entry)
        await async_stop_entry_mold_trackers(hass, entry)
    return unloaded

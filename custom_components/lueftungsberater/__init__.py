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
from .history import async_stop_entry_histories
from .outside import async_get_or_create_outside_coordinator, async_stop_outside_coordinator
from .coordinator import (
    async_get_or_create_room_coordinator,
    async_stop_entry_coordinators,
)
from .const import (
    CONF_ENTRY_KIND,
    CONF_REMOTE_HOST,
    CONF_NIGHT_START_HOUR,
    CONF_NIGHT_START_TIME,
    CONF_NIGHT_END_TIME,
    CONF_REMOTE_CLIENT_ID,
    CONF_REMOTE_ROOM_SHARE,
    CONF_NOTIFY_TRIGGERS,
    CONF_ROOM_NOTIFY_TRIGGERS,
    DEFAULT_NIGHT_START_HOUR,
    DEFAULT_NIGHT_END_TIME,
    ENTRY_KIND_LOCAL,
    ENTRY_KIND_REMOTE,
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_AIRING_FINISHED,
    LEGACY_NOTIFY_KEYS,
    PLATFORMS,
    SUBENTRY_TYPE_ROOM,
    entry_kind,
)
from .remote import (
    async_get_or_create_remote_coordinator,
    async_stop_remote_coordinator,
)
from .remote_devices import async_clear_remote_device_sync_cache, async_sync_remote_room_devices
from .providers import async_clear_nina_details_cache

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = "/lueftungsberater/frontend"
FRONTEND_FILE = "lueftungsberater-card.js"
FRONTEND_VERSION = "0.7.2"


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
        _LOGGER.info("Registered Lüftungsassistent dashboard cards")
        return

    if existing.get("url") != wanted_url or existing.get("type") != "module":
        await resources.async_update_item(
            existing["id"],
            {"res_type": "module", "url": wanted_url},
        )
        _LOGGER.info(
            "Updated Lüftungsassistent dashboard cards to frontend %s",
            FRONTEND_VERSION,
        )


def _pin_subentry_capabilities(entry: ConfigEntry) -> None:
    """Keep read-only remote entries out of Home Assistant's room parent picker.

    Home Assistant caches supported subentry types on each ConfigEntry. Older
    remote entries may have cached the room type before they were marked
    read-only, so clear/pin the cache whenever the entry is migrated or set up.
    """
    if not hasattr(entry, "_supported_subentry_types"):
        return
    remote = entry_kind(entry) == ENTRY_KIND_REMOTE or bool(entry.data.get(CONF_REMOTE_HOST))
    object.__setattr__(entry, "_supported_subentry_types", {} if remote else None)
    entry.clear_state_cache()


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

    if entry.version == 1 and entry.minor_version < 5:
        # v0.6.24 uses a real time selector for the per-room night hint. Keep
        # existing hour choices without changing behaviour.
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
                continue
            data = dict(subentry.data)
            if CONF_NIGHT_START_TIME not in data:
                try:
                    hour = int(data.get(CONF_NIGHT_START_HOUR, DEFAULT_NIGHT_START_HOUR))
                except (TypeError, ValueError):
                    hour = DEFAULT_NIGHT_START_HOUR
                data[CONF_NIGHT_START_TIME] = f"{max(0, min(23, hour)):02d}:00"
                data.pop(CONF_NIGHT_START_HOUR, None)
                hass.config_entries.async_update_subentry(entry, subentry, data=data)
        updates["minor_version"] = 5


    if entry.version == 1 and entry.minor_version < 6:
        # v0.7.0 adds a configurable end time for night advice and explicit
        # per-room remote sharing. Existing rooms stay shared so active remote
        # setups do not silently lose access; newly created rooms default off.
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
                continue
            data = dict(subentry.data)
            changed = False
            if CONF_NIGHT_END_TIME not in data:
                data[CONF_NIGHT_END_TIME] = DEFAULT_NIGHT_END_TIME
                changed = True
            if CONF_REMOTE_ROOM_SHARE not in data:
                data[CONF_REMOTE_ROOM_SHARE] = True
                changed = True
            if changed:
                hass.config_entries.async_update_subentry(entry, subentry, data=data)
        cleaned_data = dict(updates.get("data", entry.data))
        if entry_kind(entry) == ENTRY_KIND_REMOTE or cleaned_data.get(CONF_REMOTE_HOST):
            cleaned_data[CONF_ENTRY_KIND] = ENTRY_KIND_REMOTE
            cleaned_data.setdefault(CONF_REMOTE_CLIENT_ID, entry.entry_id)
            updates["data"] = cleaned_data
        updates["minor_version"] = 6

    if entry.version == 1 and entry.minor_version < 7:
        # v0.7.1 republishes per-entry subentry capabilities after pinning them.
        # This makes Home Assistant's parent picker immediately see remote peers
        # as read-only instead of retaining a stale cached room capability.
        updates["minor_version"] = 7

    if entry.version == 1 and entry.minor_version < 8:
        # v0.7.2 separates assistant-wide warnings from opt-in room ventilation
        # notifications. Do not silently enable room messages for every room.
        cleaned_data = dict(updates.get("data", entry.data))
        configured = cleaned_data.get(CONF_NOTIFY_TRIGGERS)
        if isinstance(configured, str):
            configured = [configured]
        if isinstance(configured, (list, tuple, set)):
            cleaned_data[CONF_NOTIFY_TRIGGERS] = [
                item
                for item in configured
                if item not in {
                    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
                    NOTIFY_TRIGGER_AIRING_FINISHED,
                }
            ]
            updates["data"] = cleaned_data
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
                continue
            data = dict(subentry.data)
            if CONF_ROOM_NOTIFY_TRIGGERS not in data:
                data[CONF_ROOM_NOTIFY_TRIGGERS] = []
                hass.config_entries.async_update_subentry(entry, subentry, data=data)
        updates["minor_version"] = 8

    # Pin before async_update_entry: the update event serializes the ConfigEntry
    # for the frontend, so its supported_subentry_types must already be correct.
    _pin_subentry_capabilities(entry)
    if updates:
        hass.config_entries.async_update_entry(entry, **updates)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one local or Tailscale-remote Lüftungsberater entry."""
    # Keep Home Assistant's per-entry subentry capability cache in sync with
    # our local-vs-remote model. Remote/Tailscale peers are read-only.
    _pin_subentry_capabilities(entry)

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
    await async_get_or_create_outside_coordinator(hass, entry)

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
        async_clear_remote_device_sync_cache(hass, entry)
        async_clear_nina_details_cache(hass, entry)
        return True

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await async_stop_entry_coordinators(hass, entry)
        await async_stop_entry_histories(hass, entry)
        await async_stop_outside_coordinator(hass, entry)
        await async_stop_air_quality_tracker(hass, entry)
        await async_stop_entry_trackers(hass, entry)
        await async_stop_entry_co2_trackers(hass, entry)
        await async_stop_entry_mold_trackers(hass, entry)
        async_clear_nina_details_cache(hass, entry)
    return unloaded

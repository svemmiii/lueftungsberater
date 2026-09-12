"""Home Assistant area helpers for Lüftungsassistent rooms."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr

from .const import CONF_AREA_ID, DOMAIN, SUBENTRY_TYPE_ROOM

_LOGGER = logging.getLogger(__name__)


@callback
def room_area_name(hass: HomeAssistant, area_id: str | None) -> str | None:
    """Return the current Home Assistant area name for an area id."""
    if not area_id:
        return None
    area = ar.async_get(hass).async_get_area(str(area_id))
    if area is None:
        return None
    return str(area.name)


@callback
def _room_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
):
    """Find the room device without using deprecated lookup APIs on new HA."""
    registry = dr.async_get(hass)
    identifier = (DOMAIN, subentry.subentry_id)

    # HA 2026.8+ scopes identifiers to their owning config entry. Keep a small
    # compatibility fallback for the integration's supported HA 2026.6/2026.7
    # line where async_get_device_by_identifier() does not exist yet.
    get_by_identifier = getattr(registry, "async_get_device_by_identifier", None)
    if callable(get_by_identifier):
        return get_by_identifier(identifier, entry.entry_id)
    return registry.async_get_device(identifiers={identifier})


@callback
def async_sync_room_device_areas(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply explicitly configured room areas to their HA device entries.

    Older rooms which have no ``area_id`` key are deliberately left untouched,
    so updating to v0.9.4 cannot erase an area a user may already have assigned
    manually in Home Assistant. Once a room has used the v0.9.4 area option, the
    stored value becomes authoritative; storing ``None`` explicitly clears a
    previous integration-managed assignment.
    """
    registry = dr.async_get(hass)
    area_registry = ar.async_get(hass)

    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        if CONF_AREA_ID not in subentry.data:
            continue

        configured = subentry.data.get(CONF_AREA_ID)
        area_id = str(configured).strip() if configured else None
        if area_id and area_registry.async_get_area(area_id) is None:
            _LOGGER.warning(
                "Configured Home Assistant area %s for room %s no longer exists; "
                "leaving the current device area unchanged and releasing area management",
                area_id,
                subentry.title,
            )
            # The selector cannot display a deleted area. Remove the stale
            # integration-managed link now so a later unrelated room edit cannot
            # reinterpret the absent selector value as an explicit request to
            # clear a manually reassigned device area.
            updated_data = dict(subentry.data)
            updated_data.pop(CONF_AREA_ID, None)
            hass.config_entries.async_update_subentry(
                entry, subentry, data=updated_data
            )
            continue

        device = _room_device(hass, entry, subentry)
        if device is None:
            _LOGGER.debug(
                "Room device for %s is not registered yet; area sync skipped",
                subentry.title,
            )
            continue
        if device.area_id == area_id:
            continue
        registry.async_update_device(device.id, area_id=area_id)

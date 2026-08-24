"""Cleanup helpers for legacy remote Lüftungsberater device-registry entries.

Remote/Tailscale values intentionally remain transient snapshots. Since v0.6.20
no mirrored remote devices or entities are created on the receiving Home
Assistant. This module only removes the empty topology devices created by older
versions.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LEGACY_REMOTE_PREFIXES = ("remote_ha:", "remote_advisor:", "remote_room:")


def async_cleanup_remote_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove empty legacy remote topology devices for this config entry."""
    registry = dr.async_get(hass)
    for device in list(dr.async_entries_for_config_entry(registry, entry.entry_id)):
        legacy = any(
            domain == DOMAIN and identifier.startswith(_LEGACY_REMOTE_PREFIXES)
            for domain, identifier in device.identifiers
        )
        if legacy:
            registry.async_remove_device(device.id)

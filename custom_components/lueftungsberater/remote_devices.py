"""Device-registry representation of remote Lüftungsberater snapshots."""
from __future__ import annotations

import inspect
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .remote import RemoteData, remote_base_url


def _identifier(kind: str, *parts: object) -> tuple[str, str]:
    return (DOMAIN, ":".join((kind, *(str(part) for part in parts))))


def _create_device(
    registry: dr.DeviceRegistry,
    entry: ConfigEntry,
    *,
    identifier: tuple[str, str],
    name: str,
    model: str,
    parent: dr.DeviceEntry | None = None,
    parent_identifier: tuple[str, str] | None = None,
    configuration_url: str | None = None,
) -> dr.DeviceEntry:
    kwargs: dict[str, Any] = {
        "config_entry_id": entry.entry_id,
        "identifiers": {identifier},
        "manufacturer": "Lüftungsberater",
        "model": model,
        "name": name,
        "sw_version": "0.6.19",
    }
    if configuration_url:
        kwargs["configuration_url"] = configuration_url
    if parent is not None:
        # via_device_id is the current API (HA 2026.8+). Keep the old identifier
        # form as a compatibility path for the advertised HA 2026.6 minimum.
        parameters = inspect.signature(registry.async_get_or_create).parameters
        if "via_device_id" in parameters:
            kwargs["via_device_id"] = parent.id
        elif parent_identifier is not None:
            kwargs["via_device"] = parent_identifier
    return registry.async_get_or_create(**kwargs)


def async_sync_remote_devices(
    hass: HomeAssistant,
    entry: ConfigEntry,
    data: RemoteData | None,
) -> None:
    """Mirror only remote topology into the device registry, never entities."""
    registry = dr.async_get(hass)
    root_identifier = _identifier("remote_ha", entry.entry_id)
    root = _create_device(
        registry,
        entry,
        identifier=root_identifier,
        name=entry.title,
        model="Tailscale Remote Home Assistant",
        configuration_url=remote_base_url(dict(entry.data)),
    )

    # Keep the last known hierarchy while the peer is unreachable. The overview
    # handles availability separately and no stale measurement values live here.
    if data is None or not data.available:
        return

    wanted = {root_identifier}
    for instance_index, instance in enumerate(data.instances, start=1):
        if not isinstance(instance, dict):
            continue
        instance_id = str(instance.get("id") or f"instance-{instance_index}")
        instance_identifier = _identifier("remote_advisor", entry.entry_id, instance_id)
        wanted.add(instance_identifier)
        advisor = _create_device(
            registry,
            entry,
            identifier=instance_identifier,
            name=str(instance.get("name") or f"Lüftungsberater {instance_index}"),
            model="Remote Lüftungsberater",
            parent=root,
            parent_identifier=root_identifier,
        )

        rooms = instance.get("rooms", [])
        if not isinstance(rooms, list):
            rooms = []
        for room_index, room in enumerate(rooms, start=1):
            if not isinstance(room, dict):
                continue
            room_id = str(room.get("id") or f"room-{room_index}")
            room_identifier = _identifier(
                "remote_room", entry.entry_id, instance_id, room_id
            )
            wanted.add(room_identifier)
            _create_device(
                registry,
                entry,
                identifier=room_identifier,
                name=str(room.get("name") or f"Raum {room_index}"),
                model="Remote Lüftungsberater-Raum",
                parent=advisor,
                parent_identifier=instance_identifier,
            )

    # Remove topology entries that really disappeared from an available peer.
    # No entities are attached to these devices, so removal cannot delete history.
    for device in list(dr.async_entries_for_config_entry(registry, entry.entry_id)):
        ours = {identifier for identifier in device.identifiers if identifier[0] == DOMAIN}
        if ours and not ours.intersection(wanted):
            registry.async_remove_device(device.id)

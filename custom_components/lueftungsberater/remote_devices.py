"""Device-registry representation of transient remote room topology.

Remote/Tailscale measurements remain snapshots in memory only: no mirrored
entities, recorder rows or measurement history are created on the receiving
Home Assistant. The registry contains only one lightweight device card per
remote room so users can still see the connected topology without the former
extra Remote-HA -> Lüftungsberater hierarchy.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .remote import RemoteData

_LEGACY_REMOTE_PREFIXES = ("remote_ha:", "remote_advisor:")
_REMOTE_ROOM_PREFIX = "remote_room:"

_TOPOLOGY_SIGNATURES = "remote_topology_signatures"
_REMOTE_CLEANUP_DONE = "remote_topology_cleanup_done"


def _topology_signature(data: RemoteData) -> tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...]:
    signature: list[tuple[str, str, tuple[tuple[str, str], ...]]] = []
    for instance_index, instance in enumerate(data.instances, start=1):
        if not isinstance(instance, dict):
            continue
        instance_id = str(instance.get("id") or f"instance-{instance_index}")
        instance_name = str(instance.get("name") or "Lüftungsassistent")
        rooms_raw = instance.get("rooms", [])
        rooms: list[tuple[str, str]] = []
        if isinstance(rooms_raw, list):
            for room_index, room in enumerate(rooms_raw, start=1):
                if not isinstance(room, dict):
                    continue
                rooms.append((
                    str(room.get("id") or f"room-{room_index}"),
                    str(room.get("name") or f"Raum {room_index}"),
                ))
        signature.append((instance_id, instance_name, tuple(rooms)))
    return tuple(signature)


def _identifier(entry: ConfigEntry, instance_id: str, room_id: str) -> tuple[str, str]:
    return (DOMAIN, f"remote_room:{entry.entry_id}:{instance_id}:{room_id}")


def async_sync_remote_room_devices(
    hass: HomeAssistant,
    entry: ConfigEntry,
    data: RemoteData | None,
) -> None:
    """Keep only lightweight room cards for a remote connection.

    The cards contain topology metadata only. Current room values continue to
    come exclusively from the transient remote coordinator used by the custom
    card and are never exposed as local entities.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    cleanup_done = domain_data.setdefault(_REMOTE_CLEANUP_DONE, set())
    registry = dr.async_get(hass)

    # Remove obsolete intermediate levels once per entry. Repeating registry
    # scans for every 30-second remote measurement update serves no purpose.
    if entry.entry_id not in cleanup_done:
        for device in list(dr.async_entries_for_config_entry(registry, entry.entry_id)):
            if any(
                domain == DOMAIN and identifier.startswith(_LEGACY_REMOTE_PREFIXES)
                for domain, identifier in device.identifiers
            ):
                registry.async_remove_device(device.id)
        cleanup_done.add(entry.entry_id)

    # Keep the last known room cards while a peer is temporarily unreachable.
    if data is None or not data.available:
        return

    topology = _topology_signature(data)
    signatures = domain_data.setdefault(_TOPOLOGY_SIGNATURES, {})
    if signatures.get(entry.entry_id) == topology:
        return
    signatures[entry.entry_id] = topology

    instances = [item for item in data.instances if isinstance(item, dict)]
    wanted: set[tuple[str, str]] = set()
    multiple_instances = len(instances) > 1

    for instance_index, instance in enumerate(instances, start=1):
        instance_id = str(instance.get("id") or f"instance-{instance_index}")
        instance_name = str(instance.get("name") or "Lüftungsassistent")
        rooms = instance.get("rooms", [])
        if not isinstance(rooms, list):
            continue

        for room_index, room in enumerate(rooms, start=1):
            if not isinstance(room, dict):
                continue
            room_id = str(room.get("id") or f"room-{room_index}")
            room_name = str(room.get("name") or f"Raum {room_index}")
            identifier = _identifier(entry, instance_id, room_id)
            wanted.add(identifier)
            registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={identifier},
                manufacturer="Lüftungsassistent",
                model="Tailscale Remote-Raum",
                name=(f"{instance_name} · {room_name}" if multiple_instances else room_name),
                sw_version="0.7.1",
            )

    # Remove remote room cards only when an available peer confirms that the
    # corresponding room no longer exists. No entities/history are attached.
    for device in list(dr.async_entries_for_config_entry(registry, entry.entry_id)):
        ours = {
            identifier
            for identifier in device.identifiers
            if identifier[0] == DOMAIN and identifier[1].startswith(_REMOTE_ROOM_PREFIX)
        }
        if ours and not ours.intersection(wanted):
            registry.async_remove_device(device.id)


def async_clear_remote_device_sync_cache(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Forget in-memory sync signatures while leaving remote room cards intact."""
    domain_data = hass.data.get(DOMAIN, {})
    signatures = domain_data.get(_TOPOLOGY_SIGNATURES)
    if isinstance(signatures, dict):
        signatures.pop(entry.entry_id, None)
    cleanup_done = domain_data.get(_REMOTE_CLEANUP_DONE)
    if isinstance(cleanup_done, set):
        cleanup_done.discard(entry.entry_id)

"""One-shot Home Assistant -> ESPHome station provisioning.

The ESP firmware is intentionally identical for standalone/master/node devices.
Home Assistant owns the desired role/topology and pushes it over ESPHome's
native API only after an explicit station create/reconfigure flow. The device
persists the configuration; normal boots do not fetch HA config again.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import ATTR_DOMAIN, ATTR_SERVICE, EVENT_SERVICE_REGISTERED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HARDWARE_DEVICE_ID,
    CONF_HARDWARE_ID,
    CONF_HARDWARE_LOCATION_MODE,
    CONF_HARDWARE_MASTER_SECRET,
    CONF_HARDWARE_MASTER_CREDENTIAL_RESET,
    CONF_HARDWARE_PARTICIPANTS_HASH,
    CONF_HARDWARE_PARTICIPANTS_SYNCED_AT,
    CONF_HARDWARE_PROVISIONED_AT,
    CONF_HARDWARE_PROVISION_PENDING,
    CONF_HARDWARE_ROOM_ID,
    CONF_HARDWARE_WG_ADDRESS,
    CONF_HARDWARE_WG_ALLOWED_IPS,
    CONF_HARDWARE_WG_ENDPOINT_HOST,
    CONF_HARDWARE_WG_ENDPOINT_PORT,
    CONF_HARDWARE_WG_KEEPALIVE,
    CONF_HARDWARE_WG_PRESHARED_KEY,
    CONF_HARDWARE_WG_PEER_PUBLIC_KEY,
    CONF_HARDWARE_WG_PRIVATE_KEY,
    HARDWARE_LOCATION_LOCAL,
    HARDWARE_LOCATION_REMOTE,
    HARDWARE_ROLE_MASTER,
    HARDWARE_ROLE_NODE,
    DOMAIN,
    ENTRY_KIND_LOCAL,
    SUBENTRY_TYPE_STATION,
    entry_kind,
)
from .hardware_hub import (
    configured_master_hardware_id,
    master_participants,
    station_role,
    station_subentries,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_APPLY_CONFIG = "lueftungsstation_apply_station_config"
SERVICE_APPLY_CREDENTIAL = "lueftungsstation_apply_master_credential"
SERVICE_APPLY_WIREGUARD = "lueftungsstation_apply_wireguard"
SERVICE_CLEAR_WIREGUARD = "lueftungsstation_clear_wireguard"
# Future-proof participant replacement contract. The current unified firmware may
# not expose this action yet; HA treats its absence as a deferred topology sync,
# never as a failure of ordinary station/master provisioning.
SERVICE_APPLY_PARTICIPANTS = "lueftungsstation_apply_participants"

DIAGNOSTIC_CONFIRM_TIMEOUT = 40.0
RETRY_BACKOFF_MINUTES = (1, 2, 5, 10)


class HardwareProvisioningError(RuntimeError):
    """Station could not be provisioned through its ESPHome native API."""


@dataclass(frozen=True, slots=True)
class ESPHomeProvisionTarget:
    """Stable HA-side information required to address one ESPHome node."""

    device_id: str
    entry_id: str
    device_name: str
    mac: str

    @property
    def service_prefix(self) -> str:
        return self.device_name.replace("-", "_")

    def service(self, suffix: str) -> str:
        return f"{self.service_prefix}_{suffix}"


def _network_mac(device: dr.DeviceEntry | None) -> str | None:
    """Return canonical network MAC from the HA device registry."""
    if device is None:
        return None
    for connection_type, value in device.connections:
        if connection_type != dr.CONNECTION_NETWORK_MAC:
            continue
        try:
            return dr.format_mac(str(value)).upper()
        except (TypeError, ValueError):
            continue
    return None


def esphome_device_network_mac(hass: HomeAssistant, device_id: str) -> str | None:
    """Resolve a selected ESPHome device to its physical network MAC."""
    return _network_mac(dr.async_get(hass).async_get(device_id))


def _esphome_entry_for_device(
    hass: HomeAssistant, device: dr.DeviceEntry
) -> ConfigEntry | None:
    """Return the ESPHome config entry which owns the selected device."""
    entry_ids = set(getattr(device, "config_entries", set()) or set())
    for entry_id in entry_ids:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and entry.domain == "esphome":
            return entry

    # Compatibility with lightweight HA/test objects and older registry shapes.
    for entry in hass.config_entries.async_entries("esphome"):
        try:
            devices = dr.async_entries_for_config_entry(
                dr.async_get(hass), config_entry_id=entry.entry_id
            )
        except (AttributeError, TypeError):
            continue
        if any(item.id == device.id for item in devices):
            return entry
    return None


def esphome_provision_target(
    hass: HomeAssistant, device_id: str
) -> ESPHomeProvisionTarget | None:
    """Resolve service-addressing data without using IPs or internal IDs as HW IDs."""
    device = dr.async_get(hass).async_get(device_id)
    mac = _network_mac(device)
    if device is None or mac is None:
        return None
    entry = _esphome_entry_for_device(hass, device)
    if entry is None:
        return None

    device_name = str(entry.data.get("device_name") or "").strip()
    runtime_data = getattr(entry, "runtime_data", None)
    device_info = getattr(runtime_data, "device_info", None)
    runtime_name = str(getattr(device_info, "name", "") or "").strip()
    if runtime_name:
        device_name = runtime_name
    if not device_name:
        return None

    return ESPHomeProvisionTarget(
        device_id=device.id,
        entry_id=entry.entry_id,
        device_name=device_name,
        mac=mac,
    )


def station_physical_hardware_id(
    hass: HomeAssistant,
    device_id: str,
    *,
    direct: bool,
) -> str | None:
    """Return MAC-derived station ID, with DIRECT prefix only for direct roles."""
    mac = esphome_device_network_mac(hass, device_id)
    if mac is None:
        return None
    return f"DIRECT:{mac}" if direct else mac


def _protocol_hardware_id(value: Any) -> str:
    """Return raw MAC protocol id from a stored DIRECT:<MAC> alias."""
    text = str(value or "").strip().upper().replace("-", ":")
    if text.startswith("DIRECT:"):
        text = text.removeprefix("DIRECT:")
    compact = text.replace(":", "")
    if len(compact) == 12 and all(char in "0123456789ABCDEF" for char in compact):
        return ":".join(compact[i : i + 2] for i in range(0, 12, 2))
    return text


def _canonical_physical_mac(value: Any) -> str | None:
    """Return a real canonical 48-bit MAC or ``None`` for legacy opaque ids."""
    raw = _protocol_hardware_id(value)
    compact = raw.replace(":", "")
    if len(compact) != 12 or not all(char in "0123456789ABCDEF" for char in compact):
        return None
    return ":".join(compact[index : index + 2] for index in range(0, 12, 2))


def _participant_payload(
    entry: ConfigEntry, master: ConfigSubentry
) -> tuple[list[str], list[str], list[str], str]:
    """Return the complete ordered topology payload and its non-secret digest.

    Parallel string arrays intentionally map to ESPHome's native ``STRING_ARRAY``
    user-service type. The future firmware action must validate equal lengths and
    atomically replace its complete participant cache instead of applying ADD/REMOVE
    deltas. Including room/subentry ids means a room move also changes the digest,
    exactly matching HA's source-of-truth topology.
    """
    participants = master_participants(entry, master)
    hardware_ids = [
        _protocol_hardware_id(item.get("hardware_id")) for item in participants
    ]
    station_ids = [str(item.get("station_subentry_id") or "") for item in participants]
    room_ids = [str(item.get("room_id") or "") for item in participants]
    digest_source = {
        "hardware_ids": hardware_ids,
        "station_subentry_ids": station_ids,
        "room_ids": room_ids,
    }
    topology_hash = hashlib.sha256(
        json.dumps(
            digest_source,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return hardware_ids, station_ids, room_ids, topology_hash


def master_participant_topology_hash(entry: ConfigEntry, master: ConfigSubentry) -> str:
    """Return the current HA-owned participant topology hash for diagnostics/tests."""
    return _participant_payload(entry, master)[3]


async def _wait_for_service(
    hass: HomeAssistant,
    service_name: str,
    *,
    timeout: float = 12.0,
) -> None:
    """Allow ESPHome a short startup window to register custom actions."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if hass.services.has_service("esphome", service_name):
            return
        await asyncio.sleep(0.25)
    raise HardwareProvisioningError(
        f"ESPHome action esphome.{service_name} is not registered"
    )


async def _call_esphome(
    hass: HomeAssistant,
    target: ESPHomeProvisionTarget,
    suffix: str,
    data: dict[str, Any] | None = None,
    *,
    service_timeout: float = 12.0,
) -> None:
    service_name = target.service(suffix)
    await _wait_for_service(hass, service_name, timeout=service_timeout)
    await hass.services.async_call(
        "esphome",
        service_name,
        data or {},
        blocking=True,
    )


def _diagnostic_entity(
    hass: HomeAssistant, device_id: str, *, name_contains: str
) -> str | None:
    """Return one ESPHome diagnostic entity belonging to the selected device."""
    registry = er.async_get(hass)
    needle = name_contains.casefold()
    try:
        entries = er.async_entries_for_device(registry, device_id)
    except (AttributeError, TypeError):
        entries = [
            item
            for item in registry.entities.values()
            if getattr(item, "device_id", None) == device_id
        ]
    # A broad substring such as "Lüftungsstation Master" also matches
    # "Lüftungsstation Master-Credential konfiguriert". Prefer the exact
    # diagnostic name so registry order cannot select the credential sensor
    # instead of the master-id text sensor during confirmation.
    for item in entries:
        if str(getattr(item, "original_name", "") or "").casefold() == needle:
            return str(item.entity_id)
    for item in entries:
        original = str(getattr(item, "original_name", "") or "")
        entity_id = str(getattr(item, "entity_id", "") or "")
        if needle in f"{original} {entity_id}".casefold():
            return entity_id
    return None


def _diagnostic_current_state(
    hass: HomeAssistant, device_id: str, *, name_contains: str
) -> str | None:
    """Return the current diagnostic state, requiring the entity to exist."""
    entity_id = _diagnostic_entity(hass, device_id, name_contains=name_contains)
    if entity_id is None:
        raise HardwareProvisioningError(
            f"Required ESPHome provisioning diagnostic is missing: {name_contains}"
        )
    state = hass.states.get(entity_id)
    return str(getattr(state, "state", "") or "").strip() if state is not None else None


async def _wait_for_diagnostic_state(
    hass: HomeAssistant,
    device_id: str,
    *,
    name_contains: str,
    expected: str,
    fresh_after: datetime | None = None,
    timeout: float = DIAGNOSTIC_CONFIRM_TIMEOUT,
    normalize=None,
) -> None:
    """Wait for a *fresh* firmware diagnostic matching the desired state.

    A pre-existing ``on`` value is not confirmation of a new provisioning run.
    Home Assistant's ``State.last_reported`` advances even when an entity reports
    the same state again, so requiring a report after the native-API action
    prevents an old cached confirmation from satisfying the transaction.
    """
    entity_id = _diagnostic_entity(hass, device_id, name_contains=name_contains)
    if entity_id is None:
        raise HardwareProvisioningError(
            f"Required ESPHome provisioning diagnostic is missing: {name_contains}"
        )

    expected_value = normalize(expected) if normalize else expected
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        state = hass.states.get(entity_id)
        if state is not None:
            reported = getattr(state, "last_reported", None) or getattr(
                state, "last_updated", None
            )
            fresh = fresh_after is None or (
                isinstance(reported, datetime) and reported >= fresh_after
            )
            actual = normalize(state.state) if normalize else state.state
            if fresh and actual == expected_value:
                return
        await asyncio.sleep(0.25)

    state = hass.states.get(entity_id)
    reported = (
        getattr(state, "last_reported", None)
        if state is not None
        else None
    )
    raise HardwareProvisioningError(
        f"ESPHome diagnostic {entity_id} did not freshly confirm {expected!r}; "
        f"current={getattr(state, 'state', None)!r}, last_reported={reported!r}"
    )


def _casefold(value: Any) -> str:
    return str(value or "").strip().casefold()


def _normalized_protocol_id(value: Any) -> str:
    text = _protocol_hardware_id(value)
    return text if text else "-"


async def _confirm_station_config(
    hass: HomeAssistant,
    target: ESPHomeProvisionTarget,
    *,
    role: str,
    room_id: str,
    master_id: str,
    location_mode: str,
    fresh_after: datetime,
) -> None:
    """Confirm the common firmware now exposes the requested HA-owned state."""
    await _wait_for_diagnostic_state(
        hass,
        target.device_id,
        name_contains="Lüftungsstation Provisioniert",
        expected="on",
        # The exact role/room/master/location text sensors below are the
        # transaction proof. This binary sensor is a coarse readiness gate and
        # may legitimately have stayed ON from the previous configuration.
        fresh_after=None,
        timeout=15.0,
    )
    await _wait_for_diagnostic_state(
        hass,
        target.device_id,
        name_contains="Lüftungsstation Rolle",
        expected=role,
        fresh_after=fresh_after,
        normalize=_casefold,
    )
    await _wait_for_diagnostic_state(
        hass,
        target.device_id,
        name_contains="Lüftungsstation Raum-ID",
        expected=room_id or "-",
        fresh_after=fresh_after,
    )
    await _wait_for_diagnostic_state(
        hass,
        target.device_id,
        name_contains="Lüftungsstation Master",
        expected=master_id or "-",
        fresh_after=fresh_after,
        normalize=_normalized_protocol_id,
    )
    await _wait_for_diagnostic_state(
        hass,
        target.device_id,
        name_contains="Lüftungsstation Standort",
        expected=location_mode,
        fresh_after=fresh_after,
        normalize=_casefold,
    )


async def async_provision_station(
    hass: HomeAssistant,
    entry: ConfigEntry,
    station: ConfigSubentry,
    *,
    service_timeout: float = 12.0,
) -> None:
    """Push one station's HA-owned desired state to the common firmware."""
    if station.subentry_type != SUBENTRY_TYPE_STATION:
        raise HardwareProvisioningError("Not a hardware station subentry")

    device_id = str(station.data.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
    if not device_id:
        raise HardwareProvisioningError(
            "Station has no selected ESPHome device; reconfigure it once"
        )
    target = esphome_provision_target(hass, device_id)
    if target is None:
        raise HardwareProvisioningError(
            "Selected ESPHome device has no usable network MAC/device name"
        )

    expected_hardware_id = str(station.data.get(CONF_HARDWARE_ID) or "")
    if target.mac not in {_protocol_hardware_id(expected_hardware_id)}:
        raise HardwareProvisioningError(
            "Selected ESPHome device MAC does not match stored station hardware ID"
        )

    role = station_role(station)
    master_id = ""
    if role == HARDWARE_ROLE_NODE:
        master_id = _protocol_hardware_id(
            configured_master_hardware_id(entry, station) or ""
        )
        if not master_id:
            raise HardwareProvisioningError("Configured node master is missing")

    location_mode = str(
        station.data.get(CONF_HARDWARE_LOCATION_MODE) or HARDWARE_LOCATION_LOCAL
    )
    room_id = str(station.data.get(CONF_HARDWARE_ROOM_ID) or "")

    # A newly generated/replaced master credential must never be "confirmed"
    # by an old ON state left on a previously used ESP. The common firmware
    # already clears its credential whenever it is deliberately provisioned as a
    # non-master, so use that existing contract as a one-shot reset handshake.
    credential_reset_required = bool(
        role == HARDWARE_ROLE_MASTER
        and station.data.get(CONF_HARDWARE_MASTER_CREDENTIAL_RESET) is True
    )
    if credential_reset_required:
        credential_before_reset = _casefold(
            _diagnostic_current_state(
                hass,
                target.device_id,
                name_contains="Master-Credential konfiguriert",
            )
        )
        reset_started = dt_util.utcnow()
        await _call_esphome(
            hass,
            target,
            SERVICE_APPLY_CONFIG,
            {
                "role": "standalone",
                "entry_id": entry.entry_id,
                "station_subentry_id": station.subentry_id,
                "room_id": room_id,
                "master_hardware_id": "",
                "location_mode": location_mode,
            },
            service_timeout=service_timeout,
        )
        await _wait_for_diagnostic_state(
            hass,
            target.device_id,
            name_contains="Master-Credential konfiguriert",
            expected="off",
            # If the old state was ON, require the reset transition to be freshly
            # reported. If the ESP was already credential-free, OFF is already
            # the exact safe precondition and need not manufacture a same-state
            # binary-sensor report.
            fresh_after=(reset_started if credential_before_reset == "on" else None),
            timeout=15.0,
        )

    config_started = dt_util.utcnow()
    await _call_esphome(
        hass,
        target,
        SERVICE_APPLY_CONFIG,
        {
            "role": role,
            "entry_id": entry.entry_id,
            "station_subentry_id": station.subentry_id,
            "room_id": room_id,
            "master_hardware_id": master_id,
            "location_mode": location_mode,
        },
        service_timeout=service_timeout,
    )
    await _confirm_station_config(
        hass,
        target,
        role=role,
        room_id=room_id,
        master_id=master_id,
        location_mode=location_mode,
        fresh_after=config_started,
    )

    if role == HARDWARE_ROLE_MASTER:
        secret = str(station.data.get(CONF_HARDWARE_MASTER_SECRET) or "").strip()
        if len(secret) < 32:
            raise HardwareProvisioningError(
                "Configured master has no valid hardware_master_secret"
            )
        # Always re-apply HA's persisted credential during an explicit master
        # provisioning transaction, even when the firmware already reports that
        # *some* credential exists. This preserves the same HA secret on ordinary
        # reconfigure while repairing the rare drift case where a manually
        # restored/flashed master contains a different secret. No secret value is
        # exposed by diagnostics; the fresh ON report only confirms the apply.
        credential_started = dt_util.utcnow()
        await _call_esphome(
            hass,
            target,
            SERVICE_APPLY_CREDENTIAL,
            {"master_secret": secret},
            service_timeout=service_timeout,
        )
        await _wait_for_diagnostic_state(
            hass,
            target.device_id,
            name_contains="Master-Credential konfiguriert",
            expected="on",
            fresh_after=credential_started,
            timeout=15.0,
        )
        # A stale WireGuard=ON flag cannot prove that a newly edited remote
        # profile was accepted. Deliberately clear first and require a fresh OFF
        # report, then apply the requested profile and require a fresh ON report.
        # This turns the existing boolean firmware diagnostic into an unambiguous
        # one-shot acknowledgement without exposing any private key material.
        wireguard_before_clear = _casefold(
            _diagnostic_current_state(
                hass, target.device_id, name_contains="WireGuard konfiguriert"
            )
        )
        wireguard_clear_started = dt_util.utcnow()
        await _call_esphome(
            hass,
            target,
            SERVICE_CLEAR_WIREGUARD,
            service_timeout=service_timeout,
        )
        await _wait_for_diagnostic_state(
            hass,
            target.device_id,
            name_contains="WireGuard konfiguriert",
            expected="off",
            fresh_after=(wireguard_clear_started if wireguard_before_clear == "on" else None),
            timeout=15.0,
        )
        if location_mode == HARDWARE_LOCATION_REMOTE:
            wireguard_apply_started = dt_util.utcnow()
            await _call_esphome(
                hass,
                target,
                SERVICE_APPLY_WIREGUARD,
                {
                    "address": str(station.data.get(CONF_HARDWARE_WG_ADDRESS) or ""),
                    "private_key": str(
                        station.data.get(CONF_HARDWARE_WG_PRIVATE_KEY) or ""
                    ),
                    "peer_public_key": str(
                        station.data.get(CONF_HARDWARE_WG_PEER_PUBLIC_KEY) or ""
                    ),
                    "preshared_key": str(
                        station.data.get(CONF_HARDWARE_WG_PRESHARED_KEY) or ""
                    ),
                    "endpoint_host": str(
                        station.data.get(CONF_HARDWARE_WG_ENDPOINT_HOST) or ""
                    ),
                    "endpoint_port": int(
                        station.data.get(CONF_HARDWARE_WG_ENDPOINT_PORT) or 0
                    ),
                    "allowed_ips": str(
                        station.data.get(CONF_HARDWARE_WG_ALLOWED_IPS) or ""
                    ),
                    "keepalive": int(
                        station.data.get(CONF_HARDWARE_WG_KEEPALIVE) or 0
                    ),
                },
                service_timeout=service_timeout,
            )
            await _wait_for_diagnostic_state(
                hass,
                target.device_id,
                name_contains="WireGuard konfiguriert",
                expected="on",
                fresh_after=wireguard_apply_started,
                timeout=15.0,
            )
    else:
        # A former master that is deliberately reconfigured as another role must
        # not retain a WireGuard profile. The station-config action already clears
        # a master credential for non-master roles.
        wireguard_before_clear = _casefold(
            _diagnostic_current_state(
                hass, target.device_id, name_contains="WireGuard konfiguriert"
            )
        )
        wireguard_started = dt_util.utcnow()
        await _call_esphome(
            hass,
            target,
            SERVICE_CLEAR_WIREGUARD,
            service_timeout=service_timeout,
        )
        await _wait_for_diagnostic_state(
            hass,
            target.device_id,
            name_contains="WireGuard konfiguriert",
            expected="off",
            fresh_after=(wireguard_started if wireguard_before_clear == "on" else None),
            timeout=15.0,
        )


async def _confirm_master_participants(
    hass: HomeAssistant,
    target: ESPHomeProvisionTarget,
    *,
    topology_hash: str,
    fresh_after: datetime,
) -> None:
    """Confirm the exact participant replacement through the firmware hash.

    The participant cache is safety-relevant HA-owned desired state. A node count
    cannot prove that the correct MAC/room/station tuples are present, and an HA-
    persisted hash cannot prove that a reflashed master still has the cache. The
    firmware contract therefore requires an exact ``Lüftungsstation Topologie-
    Hash`` diagnostic which is freshly reported after every replacement.
    """
    if _diagnostic_entity(
        hass, target.device_id, name_contains="Lüftungsstation Topologie-Hash"
    ) is None:
        raise HardwareProvisioningError(
            "Participant action exists but firmware exposes no topology hash diagnostic"
        )

    await _wait_for_diagnostic_state(
        hass,
        target.device_id,
        name_contains="Lüftungsstation Topologie-Hash",
        expected=topology_hash,
        fresh_after=fresh_after,
    )


async def async_sync_master_participants(
    hass: HomeAssistant,
    entry: ConfigEntry,
    master: ConfigSubentry,
    *,
    service_timeout: float = 2.0,
) -> bool:
    """Push HA's complete node list to one master when firmware supports it.

    This is deliberately separate from normal station provisioning. v0.11.0 can
    therefore run against the already deployed unified firmware which has not yet
    implemented ``lueftungsstation_apply_participants``. Once that action appears,
    HA automatically replaces the complete list instead of relying on incremental
    pairing drift.

    Return ``True`` when the desired topology is already synchronized or was
    successfully applied; return ``False`` when the firmware action is not yet
    available and synchronization is therefore deferred.
    """
    if (
        master.subentry_type != SUBENTRY_TYPE_STATION
        or station_role(master) != HARDWARE_ROLE_MASTER
    ):
        return True

    device_id = str(master.data.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
    if not device_id:
        return False
    target = esphome_provision_target(hass, device_id)
    if target is None:
        return False

    hardware_ids, station_ids, room_ids, topology_hash = _participant_payload(
        entry, master
    )
    topology_entity = _diagnostic_entity(
        hass, target.device_id, name_contains="Lüftungsstation Topologie-Hash"
    )
    if topology_entity is None:
        _LOGGER.debug(
            "Participant topology for master %s is pending; firmware exposes no topology-hash diagnostic yet",
            master.title,
        )
        return False

    topology_state = hass.states.get(topology_entity)
    if (
        topology_state is not None
        and str(topology_state.state).strip() == topology_hash
    ):
        # The device itself is the source of truth for whether this exact desired
        # topology is applied. HA's persisted hash is only audit metadata and is
        # never trusted on its own, so a master reflash/factory reset heals itself.
        return True

    service_name = target.service(SERVICE_APPLY_PARTICIPANTS)
    if not hass.services.has_service("esphome", service_name):
        _LOGGER.debug(
            "Participant topology for master %s is pending; ESPHome action %s is not available yet",
            master.title,
            service_name,
        )
        return False

    started = dt_util.utcnow()
    await _call_esphome(
        hass,
        target,
        SERVICE_APPLY_PARTICIPANTS,
        {
            "hardware_ids": hardware_ids,
            "station_subentry_ids": station_ids,
            "room_ids": room_ids,
            "topology_hash": topology_hash,
        },
        service_timeout=service_timeout,
    )
    await _confirm_master_participants(
        hass,
        target,
        topology_hash=topology_hash,
        fresh_after=started,
    )

    data = dict(master.data)
    data[CONF_HARDWARE_PARTICIPANTS_HASH] = topology_hash
    data[CONF_HARDWARE_PARTICIPANTS_SYNCED_AT] = dt_util.utcnow().isoformat()
    hass.config_entries.async_update_subentry(entry, master, data=data)
    return True


async def async_sync_master_participant_lists(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Synchronize every physical master's complete HA-owned participant list."""
    if entry_kind(entry) != ENTRY_KIND_LOCAL:
        return
    for master in tuple(station_subentries(entry)):
        if station_role(master) != HARDWARE_ROLE_MASTER:
            continue
        try:
            await async_sync_master_participants(hass, entry, master)
        except Exception:  # noqa: BLE001 - topology retry must not break HA setup
            _LOGGER.exception(
                "Unable to synchronize participant topology for master %s",
                master.title,
            )


def async_watch_master_participant_service(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Retry deferred topology when ESPHome registers the new action after OTA.

    Config/subentry changes already reload the entry, so node create/delete/move
    naturally recomputes the desired digest. This listener covers the remaining
    case where the ESP firmware gains the participant action while HA stays up.
    """
    running = False

    async def _sync() -> None:
        nonlocal running
        if running:
            return
        running = True
        try:
            await async_sync_master_participant_lists(hass, entry)
        finally:
            running = False

    @callback
    def _service_registered(event) -> None:
        if event.data.get(ATTR_DOMAIN) != "esphome":
            return
        service = str(event.data.get(ATTR_SERVICE) or "")
        if not service.endswith(f"_{SERVICE_APPLY_PARTICIPANTS}"):
            return
        hass.async_create_task(
            _sync(),
            f"{DOMAIN} synchronize master participant topology",
        )

    entry.async_on_unload(
        hass.bus.async_listen(EVENT_SERVICE_REGISTERED, _service_registered)
    )


def _has_master_stations(entry: ConfigEntry) -> bool:
    """Return whether this local entry owns at least one physical master."""
    return any(
        station_role(station) == HARDWARE_ROLE_MASTER
        for station in station_subentries(entry)
    )


def async_start_master_participant_retry(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Continuously heal master topology drift with bounded retry backoff.

    Pending state is derived from the firmware-reported topology hash rather than
    an HA-only flag. This means an offline master, a missed service-registration
    event, or a later firmware reset all converge back to HA's full desired list.
    The timer is lightweight and performs no work for masters whose reported hash
    already equals the current desired hash.
    """
    if entry_kind(entry) != ENTRY_KIND_LOCAL or not _has_master_stations(entry):
        return

    running = False
    failures: dict[str, int] = {}
    next_due: dict[str, datetime] = {}

    async def _retry(_now=None) -> None:
        nonlocal running
        if running:
            return
        running = True
        try:
            now = dt_util.utcnow()
            current_master_ids: set[str] = set()
            for master in tuple(station_subentries(entry)):
                if station_role(master) != HARDWARE_ROLE_MASTER:
                    continue
                current_master_ids.add(master.subentry_id)
                due = next_due.get(master.subentry_id)
                if due is not None and now < due:
                    continue

                try:
                    synced = await async_sync_master_participants(
                        hass, entry, master, service_timeout=2.0
                    )
                except Exception:  # noqa: BLE001 - topology retry is resilient
                    synced = False
                    _LOGGER.warning(
                        "Participant topology retry for master %s failed",
                        master.title,
                        exc_info=True,
                    )

                if synced:
                    failures.pop(master.subentry_id, None)
                    next_due.pop(master.subentry_id, None)
                    continue

                count = failures.get(master.subentry_id, 0) + 1
                failures[master.subentry_id] = count
                delay = RETRY_BACKOFF_MINUTES[
                    min(count - 1, len(RETRY_BACKOFF_MINUTES) - 1)
                ]
                next_due[master.subentry_id] = now + timedelta(minutes=delay)
                _LOGGER.debug(
                    "Participant topology for master %s is still pending; next retry in %s min",
                    master.title,
                    delay,
                )

            for stale_id in set(failures) - current_master_ids:
                failures.pop(stale_id, None)
                next_due.pop(stale_id, None)
        finally:
            running = False

    unsub = async_track_time_interval(hass, _retry, timedelta(minutes=1))
    entry.async_on_unload(unsub)


def async_update_duplicate_hardware_issues(hass: HomeAssistant) -> None:
    """Surface legacy cross-entry MAC collisions created before v0.11.0.

    New config flows reject duplicates globally. Migration 1.13 cannot safely
    decide which of two historic owners should win, so it preserves both and
    creates a Repairs warning instead of silently deleting/reassigning hardware.
    """
    owners: dict[str, list[str]] = {}
    for candidate_entry in hass.config_entries.async_entries(DOMAIN):
        if entry_kind(candidate_entry) != ENTRY_KIND_LOCAL:
            continue
        for station in station_subentries(candidate_entry):
            mac = _canonical_physical_mac(station.data.get(CONF_HARDWARE_ID))
            if mac is None:
                continue
            owners.setdefault(mac, []).append(
                f"{candidate_entry.title} / {station.title}"
            )

    registry = ir.async_get(hass)
    prefix = "duplicate_station_mac_"
    wanted_issue_ids: set[str] = set()
    for mac, labels in owners.items():
        if len(labels) < 2:
            continue
        issue_id = f"{prefix}{mac.replace(':', '').lower()}"
        wanted_issue_ids.add(issue_id)
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="duplicate_station_mac",
            translation_placeholders={
                "mac": mac,
                "stations": ", ".join(labels),
            },
        )

    for (issue_domain, issue_id) in tuple(registry.issues):
        if issue_domain != DOMAIN or not issue_id.startswith(prefix):
            continue
        if issue_id not in wanted_issue_ids:
            ir.async_delete_issue(hass, DOMAIN, issue_id)


def _has_pending_stations(entry: ConfigEntry) -> bool:
    """Return whether an explicit provisioning transaction is still pending."""
    return any(
        station.subentry_type == SUBENTRY_TYPE_STATION
        and station.data.get(CONF_HARDWARE_PROVISION_PENDING) is True
        for station in entry.subentries.values()
    )


async def _mark_station_provisioned(
    hass: HomeAssistant, entry: ConfigEntry, station: ConfigSubentry
) -> None:
    data = dict(station.data)
    data.pop(CONF_HARDWARE_PROVISION_PENDING, None)
    data.pop(CONF_HARDWARE_MASTER_CREDENTIAL_RESET, None)
    data[CONF_HARDWARE_PROVISIONED_AT] = dt_util.utcnow().isoformat()
    hass.config_entries.async_update_subentry(entry, station, data=data)


async def async_provision_pending_stations(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    service_timeout: float = 12.0,
) -> None:
    """Provision only stations explicitly marked by a user flow.

    Existing stations from pre-provisioning versions are intentionally left
    untouched. This prevents an update from silently repurposing a device or
    manufacturing a master credential for a station the user never selected as
    a master.
    """
    for station in tuple(entry.subentries.values()):
        if station.subentry_type != SUBENTRY_TYPE_STATION:
            continue
        if station.data.get(CONF_HARDWARE_PROVISION_PENDING) is not True:
            continue
        try:
            await async_provision_station(
                hass, entry, station, service_timeout=service_timeout
            )
        except Exception:  # noqa: BLE001 - keep integration usable; retry later
            _LOGGER.exception(
                "Unable to provision Lüftungsstation %s through ESPHome",
                station.title,
            )
            continue
        await _mark_station_provisioned(hass, entry, station)


def async_start_pending_provision_retry(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Retry an explicit provisioning transaction with bounded backoff.

    The timer exists only while a user-created ``provision_pending`` marker is
    present. Each offline station backs off 1 -> 2 -> 5 -> 10 minutes, avoiding
    repeated long Native-API waits/log spam in larger installations. A successful
    push removes the marker and its retry state immediately.
    """
    if not _has_pending_stations(entry):
        return

    running = False
    failures: dict[str, int] = {}
    next_due: dict[str, datetime] = {}

    async def _retry(_now=None) -> None:
        nonlocal running
        if running or not _has_pending_stations(entry):
            return
        running = True
        try:
            now = dt_util.utcnow()
            for station in tuple(entry.subentries.values()):
                if station.subentry_type != SUBENTRY_TYPE_STATION:
                    continue
                if station.data.get(CONF_HARDWARE_PROVISION_PENDING) is not True:
                    failures.pop(station.subentry_id, None)
                    next_due.pop(station.subentry_id, None)
                    continue
                due = next_due.get(station.subentry_id)
                if due is not None and now < due:
                    continue
                try:
                    # Retries should fail fast when the ESPHome custom action is
                    # absent. The first setup attempt already gave it the longer
                    # startup allowance.
                    await async_provision_station(
                        hass, entry, station, service_timeout=2.0
                    )
                except Exception:  # noqa: BLE001 - retry is deliberately resilient
                    count = failures.get(station.subentry_id, 0) + 1
                    failures[station.subentry_id] = count
                    delay = RETRY_BACKOFF_MINUTES[min(count - 1, len(RETRY_BACKOFF_MINUTES) - 1)]
                    next_due[station.subentry_id] = now + timedelta(minutes=delay)
                    _LOGGER.warning(
                        "Provisioning retry %s for Lüftungsstation %s failed; "
                        "next attempt in %s min",
                        count,
                        station.title,
                        delay,
                        exc_info=True,
                    )
                    continue

                failures.pop(station.subentry_id, None)
                next_due.pop(station.subentry_id, None)
                await _mark_station_provisioned(hass, entry, station)
        finally:
            running = False

    # A lightweight one-minute scheduler implements the per-station backoff; it
    # performs no work for stations whose next_due has not arrived.
    unsub = async_track_time_interval(hass, _retry, timedelta(minutes=1))
    entry.async_on_unload(unsub)


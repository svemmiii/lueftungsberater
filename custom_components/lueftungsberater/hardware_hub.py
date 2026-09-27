"""Home Assistant side of Lüftungsstation hub/station support.

The ESP master remains a transport gateway. Home Assistant/Lüftungsberater stays
responsible for all ventilation decisions. This module only tracks paired
hardware stations and their latest raw measurements/diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HARDWARE_ID,
    CONF_HARDWARE_MASTER_ID,
    CONF_HARDWARE_ROOM_ID,
    CONF_HARDWARE_CONNECTION_TYPE,
    CONF_HARDWARE_ROLE,
    CONF_HARDWARE_MASTER_SUBENTRY_ID,
    CONF_HARDWARE_DEVICE_ID,
    CONF_HARDWARE_DIRECT_CO2,
    CONF_HARDWARE_DIRECT_TEMP,
    CONF_HARDWARE_DIRECT_HUMIDITY,
    HARDWARE_CONNECTION_DIRECT,
    HARDWARE_CONNECTION_MASTER,
    HARDWARE_ROLE_STANDALONE,
    HARDWARE_ROLE_MASTER,
    HARDWARE_ROLE_NODE,
    DATA_HARDWARE_HUBS,
    DOMAIN,
    HARDWARE_STATION_STALE_AFTER,
    HARDWARE_STATION_STALE_CHECK_INTERVAL,
    SUBENTRY_TYPE_ROOM,
    SUBENTRY_TYPE_STATION,
)


@dataclass(slots=True)
class StationRuntime:
    """Latest transient state reported by one physical station."""

    hardware_id: str
    master_id: str
    co2: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    rssi: int | None = None
    hops: int | None = None
    latency_ms: int | None = None
    retries: int | None = None
    firmware: str | None = None
    online: bool = False
    last_seen: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def station_signal(entry_id: str, station_subentry_id: str) -> str:
    return f"{DOMAIN}:hardware_station:{entry_id}:{station_subentry_id}"


def pairing_signal(entry_id: str) -> str:
    return f"{DOMAIN}:hardware_pairing:{entry_id}"


def _domain_store(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.setdefault(DOMAIN, {}).setdefault(DATA_HARDWARE_HUBS, {})


def _normalize_hardware_id(value: Any) -> str:
    text = str(value or "").strip().upper().replace("-", ":")
    return text


def _hardware_id_aliases(value: Any) -> set[str]:
    normalized = _normalize_hardware_id(value)
    if not normalized:
        return set()
    aliases = {normalized}
    if normalized.startswith("DIRECT:"):
        raw = normalized.removeprefix("DIRECT:")
        if raw:
            aliases.add(raw)
    else:
        aliases.add(f"DIRECT:{normalized}")
    return aliases


def hardware_id_matches(left: Any, right: Any) -> bool:
    """Treat legacy DIRECT:<id> and the raw physical id as the same station."""
    return bool(_hardware_id_aliases(left) & _hardware_id_aliases(right))


def station_subentries(entry: ConfigEntry) -> list[ConfigSubentry]:
    return [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_STATION
    ]


def station_connection_type(station: ConfigSubentry) -> str:
    """Return station transport type; pre-v0.10.0 station entries are master-backed."""
    value = str(station.data.get(CONF_HARDWARE_CONNECTION_TYPE) or "").strip().lower()
    return HARDWARE_CONNECTION_DIRECT if value == HARDWARE_CONNECTION_DIRECT else HARDWARE_CONNECTION_MASTER


def station_is_direct(station: ConfigSubentry) -> bool:
    """Return whether this station reads its own values directly from HA/ESPHome."""
    return station_connection_type(station) == HARDWARE_CONNECTION_DIRECT


def station_uses_hardware_hub(station: ConfigSubentry) -> bool:
    """Return whether raw values arrive through the master/hardware API path."""
    return station_connection_type(station) == HARDWARE_CONNECTION_MASTER


def station_role(station: ConfigSubentry) -> str:
    """Return the v0.10.1 station role with backward-compatible inference."""
    value = str(station.data.get(CONF_HARDWARE_ROLE) or "").strip().lower()
    if value in {HARDWARE_ROLE_STANDALONE, HARDWARE_ROLE_MASTER, HARDWARE_ROLE_NODE}:
        return value
    # v0.10.0 did not distinguish a physical master from a node.  Direct
    # stations were standalone; every master-backed entry represented a room
    # node behind the (then implicit) hub.  Preserve that meaning on upgrade.
    return HARDWARE_ROLE_STANDALONE if station_is_direct(station) else HARDWARE_ROLE_NODE


def station_is_master(station: ConfigSubentry) -> bool:
    return station_role(station) == HARDWARE_ROLE_MASTER


def station_is_node(station: ConfigSubentry) -> bool:
    return station_role(station) == HARDWARE_ROLE_NODE


def _entity_device_class(hass: HomeAssistant, entity_entry) -> str | None:
    state = hass.states.get(entity_entry.entity_id)
    raw = state.attributes.get("device_class") if state is not None else None
    if raw is None:
        raw = getattr(entity_entry, "device_class", None)
    if raw is None:
        raw = getattr(entity_entry, "original_device_class", None)
    if raw is None:
        return None
    return str(getattr(raw, "value", raw))


def direct_device_sensor_candidates(
    hass: HomeAssistant, device_id: str
) -> dict[str, list[str]]:
    """Return all usable CO2/temp/RH entities belonging to one HA device."""
    registry = er.async_get(hass)
    by_class: dict[str, list[str]] = {
        "co2": [],
        "temperature": [],
        "humidity": [],
    }
    class_to_key = {
        SensorDeviceClass.CO2.value: "co2",
        SensorDeviceClass.TEMPERATURE.value: "temperature",
        SensorDeviceClass.HUMIDITY.value: "humidity",
    }
    for entity_entry in er.async_entries_for_device(
        registry, device_id=device_id, include_disabled_entities=False
    ):
        if entity_entry.domain != "sensor":
            continue
        key = class_to_key.get(_entity_device_class(hass, entity_entry))
        if key is not None:
            by_class[key].append(entity_entry.entity_id)
    for values in by_class.values():
        values.sort()
    return by_class


def direct_device_sensor_map(
    hass: HomeAssistant, device_id: str
) -> dict[str, str] | None:
    """Return an unambiguous CO2/temp/RH mapping for one HA device."""
    candidates = direct_device_sensor_candidates(hass, device_id)
    if any(len(values) != 1 for values in candidates.values()):
        return None
    return {key: values[0] for key, values in candidates.items()}


def direct_station_entities(
    hass: HomeAssistant, station: ConfigSubentry
) -> tuple[str, str, str] | None:
    """Return current direct-station sensor ids, surviving entity-id renames."""
    if not station_is_direct(station):
        return None
    cached = (
        str(station.data.get(CONF_HARDWARE_DIRECT_CO2) or "").strip(),
        str(station.data.get(CONF_HARDWARE_DIRECT_TEMP) or "").strip(),
        str(station.data.get(CONF_HARDWARE_DIRECT_HUMIDITY) or "").strip(),
    )
    device_id = direct_station_device_id(station)
    if device_id:
        current = direct_device_sensor_map(hass, device_id)
        if current is not None:
            return current["co2"], current["temperature"], current["humidity"]

        # If another same-class sensor is added later (for example a DS18B20
        # next to the SCD41 temperature entity), automatic discovery becomes
        # ambiguous. Do not take an already configured station offline merely
        # because of that addition: retain its explicitly stored three-source
        # mapping while those entities still belong to the same device and
        # still have the expected device classes.
        if all(cached):
            registry = er.async_get(hass)
            expected = (
                SensorDeviceClass.CO2.value,
                SensorDeviceClass.TEMPERATURE.value,
                SensorDeviceClass.HUMIDITY.value,
            )
            valid_cached = True
            for entity_id, device_class in zip(cached, expected, strict=True):
                entity_entry = registry.async_get(entity_id)
                if (
                    entity_entry is None
                    or entity_entry.device_id != device_id
                    or _entity_device_class(hass, entity_entry) != device_class
                ):
                    valid_cached = False
                    break
            if valid_cached:
                return cached
        return None
    return cached if all(cached) else None


def direct_station_device_id(station: ConfigSubentry) -> str | None:
    if not station_is_direct(station):
        return None
    value = str(station.data.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
    return value or None


def direct_station_value(
    hass: HomeAssistant, station: ConfigSubentry, kind: str
) -> float | None:
    """Read one recent raw value from an integrated direct ESPHome station."""
    entities = direct_station_entities(hass, station)
    if entities is None:
        return None
    mapping = {
        "co2": entities[0],
        "temperature": entities[1],
        "humidity": entities[2],
    }
    entity_id = mapping.get(kind)
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", ""}:
        return None
    # ESPHome normally reports the SCD41 about once per minute.  A still
    # numeric HA state is not sufficient proof that the sensor is alive: if
    # reports stop entirely, ``last_reported`` stops advancing even when the
    # last value remains unchanged.  Use the same three-missed-report horizon
    # as master-backed stations.  The fallback keeps lightweight test doubles
    # and older restored state objects usable; real HA State objects expose
    # ``last_reported``.
    reported = getattr(state, "last_reported", None)
    if reported is None:
        reported = getattr(state, "last_updated", None)
    if isinstance(reported, datetime):
        now = dt_util.utcnow()
        if reported.tzinfo is None:
            reported = reported.replace(tzinfo=now.tzinfo)
        if now - reported > HARDWARE_STATION_STALE_AFTER:
            return None
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None


def station_for_room(entry: ConfigEntry, room_subentry_id: str) -> ConfigSubentry | None:
    for station in station_subentries(entry):
        if str(station.data.get(CONF_HARDWARE_ROOM_ID) or "") == room_subentry_id:
            return station
    return None


def station_by_hardware_id(entry: ConfigEntry, hardware_id: str) -> ConfigSubentry | None:
    """Return a station addressable through the master/hardware API."""
    wanted = _normalize_hardware_id(hardware_id)
    for station in station_subentries(entry):
        if not station_uses_hardware_hub(station):
            continue
        if hardware_id_matches(station.data.get(CONF_HARDWARE_ID), wanted):
            return station
    return None


def station_by_any_hardware_id(entry: ConfigEntry, hardware_id: str) -> ConfigSubentry | None:
    """Return any configured physical station, including direct ESPHome stations."""
    wanted = _normalize_hardware_id(hardware_id)
    for station in station_subentries(entry):
        if hardware_id_matches(station.data.get(CONF_HARDWARE_ID), wanted):
            return station
    return None


def configured_master_for_station(
    entry: ConfigEntry, station: ConfigSubentry
) -> ConfigSubentry | None:
    """Resolve the HA-selected master for one ESP-NOW node.

    Once a node has the stable v0.10.1 subentry relation, that relation is the
    only source of truth. Falling back to an old hardware id after that master
    was deleted could silently bind the node to a different physical device.
    The hardware-id lookup remains only for migrated v0.10.0 nodes which do not
    yet have a master-subentry relation.
    """
    subentry_id = str(station.data.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or "").strip()
    if subentry_id:
        candidate = entry.subentries.get(subentry_id)
        if (
            candidate is not None
            and candidate.subentry_type == SUBENTRY_TYPE_STATION
            and station_is_master(candidate)
        ):
            return candidate
        return None

    wanted = _normalize_hardware_id(station.data.get(CONF_HARDWARE_MASTER_ID))
    if wanted:
        for candidate in station_subentries(entry):
            if not station_is_master(candidate):
                continue
            if hardware_id_matches(candidate.data.get(CONF_HARDWARE_ID), wanted):
                return candidate
    return None


def station_topology_error(entry: ConfigEntry, station: ConfigSubentry) -> str | None:
    """Return a stable HA-owned topology error for one physical station.

    Every station is owned by exactly one room.  A deleted room therefore
    invalidates the station immediately, just like a deleted explicitly
    selected master invalidates a v0.10.1 ESP-NOW node.  Legacy nodes without
    a stable master-subentry relation retain their v0.10.0 master-id fallback.
    """
    room_id = str(station.data.get(CONF_HARDWARE_ROOM_ID) or "").strip()
    room = entry.subentries.get(room_id) if room_id else None
    if room is None or room.subentry_type != SUBENTRY_TYPE_ROOM:
        return "room_missing"

    if station_role(station) != HARDWARE_ROLE_NODE:
        return None
    explicit = str(
        station.data.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or ""
    ).strip()
    if explicit and configured_master_for_station(entry, station) is None:
        return "master_missing"
    return None


def station_topology_valid(entry: ConfigEntry, station: ConfigSubentry) -> bool:
    """Return whether this station still has a usable HA-owned topology."""
    return station_topology_error(entry, station) is None


def configured_master_hardware_id(
    entry: ConfigEntry, station: ConfigSubentry
) -> str | None:
    """Return the current master hardware id without trusting stale node data."""
    master = configured_master_for_station(entry, station)
    if master is not None:
        value = _normalize_hardware_id(master.data.get(CONF_HARDWARE_ID))
        return value or None
    # Legacy v0.10.0 nodes had no stable master-subentry relation. Preserve the
    # old raw master id only for those entries. Explicit v0.10.1 relations that
    # no longer resolve are configuration errors and must not fall back.
    if not str(station.data.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or "").strip():
        value = _normalize_hardware_id(station.data.get(CONF_HARDWARE_MASTER_ID))
        return value or None
    return None


def master_device_id_for_station(
    hass: HomeAssistant, entry: ConfigEntry, station: ConfigSubentry
) -> str | None:
    """Return the concrete HA device used as this node's configured master."""
    if station_is_master(station):
        return None
    master = configured_master_for_station(entry, station)
    if master is None:
        if str(station.data.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or "").strip():
            return None
        return master_device_id(hass, entry.entry_id)
    if station_is_direct(master):
        return direct_station_device_id(master)

    hardware_id = _normalize_hardware_id(master.data.get(CONF_HARDWARE_ID))
    if hardware_id:
        identifier = (DOMAIN, f"station:{hardware_id}")
        registry = dr.async_get(hass)
        for device in dr.async_entries_for_config_entry(
            registry, config_entry_id=entry.entry_id
        ):
            if identifier in device.identifiers:
                return device.id
    return None


def station_runtime(
    hass: HomeAssistant, entry_id: str, station_subentry_id: str
) -> StationRuntime | None:
    entry_state = _domain_store(hass).get(entry_id)
    if not isinstance(entry_state, dict):
        return None
    states = entry_state.get("states")
    if not isinstance(states, dict):
        return None
    value = states.get(station_subentry_id)
    return value if isinstance(value, StationRuntime) else None


def station_is_fresh(
    state: StationRuntime | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a station has a recent usable report."""
    if state is None or not state.online or state.last_seen is None:
        return False
    reference = now or dt_util.utcnow()
    return reference - state.last_seen <= HARDWARE_STATION_STALE_AFTER


@callback
def expire_stale_stations(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    now: datetime | None = None,
) -> tuple[str, ...]:
    """Mark overdue stations offline and notify linked entities/coordinators."""
    reference = now or dt_util.utcnow()
    entry_state = _domain_store(hass).get(entry.entry_id)
    if not isinstance(entry_state, dict):
        return ()
    states = entry_state.get("states")
    if not isinstance(states, dict):
        return ()

    expired: list[str] = []
    for subentry_id, state in states.items():
        if not isinstance(state, StationRuntime) or not state.online:
            continue
        if station_is_fresh(state, now=reference):
            continue
        state.online = False
        expired.append(str(subentry_id))
        async_dispatcher_send(
            hass, station_signal(entry.entry_id, str(subentry_id))
        )
    return tuple(expired)


def discovered_stations(hass: HomeAssistant, entry_id: str) -> dict[str, dict[str, Any]]:
    entry_state = _domain_store(hass).setdefault(entry_id, {})
    discoveries = entry_state.setdefault("discoveries", {})
    return discoveries if isinstance(discoveries, dict) else {}


@callback
def remember_discovery(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    hardware_id: str,
    master_id: str,
    name: str | None = None,
    capabilities: dict[str, Any] | None = None,
) -> None:
    """Remember a master-reported JOIN candidate for the station config flow."""
    hardware_id = _normalize_hardware_id(hardware_id)
    if not hardware_id:
        return
    # Keep the old generic hub only for an as-yet unknown/legacy master.  Once
    # HA has an explicit master station, ESP-NOW nodes can point at that real
    # physical device instead of a synthetic topology placeholder.
    if station_by_any_hardware_id(entry, master_id) is None:
        ensure_master_device(hass, entry)
    discoveries = discovered_stations(hass, entry.entry_id)
    discoveries[hardware_id] = {
        "hardware_id": hardware_id,
        "master_id": str(master_id or "default").strip() or "default",
        "name": str(name or hardware_id).strip() or hardware_id,
        "capabilities": dict(capabilities or {}),
        "seen_at": dt_util.utcnow().isoformat(),
    }
    async_dispatcher_send(hass, pairing_signal(entry.entry_id))


@callback
def report_station(
    hass: HomeAssistant,
    entry: ConfigEntry,
    station: ConfigSubentry,
    payload: dict[str, Any],
) -> StationRuntime:
    """Update latest station measurements and notify its linked room/entities."""
    entry_state = _domain_store(hass).setdefault(entry.entry_id, {})
    states = entry_state.setdefault("states", {})
    current = states.get(station.subentry_id)
    if not isinstance(current, StationRuntime):
        current = StationRuntime(
            hardware_id=_normalize_hardware_id(station.data.get(CONF_HARDWARE_ID)),
            master_id=configured_master_hardware_id(entry, station) or "default",
        )
        states[station.subentry_id] = current

    def number(key: str, *, minimum: float, maximum: float) -> float | None:
        value = payload.get(key)
        try:
            parsed = float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
        if parsed is None or not minimum <= parsed <= maximum:
            return None
        return parsed

    # Keep impossible hardware values out of both the engine and the diagnostic
    # entities.  These limits are intentionally broad enough for realistic
    # indoor sensors while rejecting protocol corruption and sentinel values.
    current.master_id = configured_master_hardware_id(entry, station) or current.master_id
    current.co2 = number("co2", minimum=250.0, maximum=10000.0)
    current.temperature = number("temperature", minimum=-50.0, maximum=80.0)
    current.humidity = number("humidity", minimum=0.0, maximum=100.0)
    try:
        current.rssi = int(payload["rssi"]) if payload.get("rssi") is not None else None
    except (TypeError, ValueError):
        current.rssi = None
    try:
        current.hops = int(payload["hops"]) if payload.get("hops") is not None else None
    except (TypeError, ValueError):
        current.hops = None
    try:
        current.latency_ms = int(payload["latency_ms"]) if payload.get("latency_ms") is not None else None
    except (TypeError, ValueError):
        current.latency_ms = None
    try:
        current.retries = int(payload["retries"]) if payload.get("retries") is not None else None
    except (TypeError, ValueError):
        current.retries = None
    reported_firmware = str(payload.get("firmware") or "").strip()
    firmware_changed = bool(reported_firmware and reported_firmware != current.firmware)
    if reported_firmware:
        current.firmware = reported_firmware
    current.online = bool(payload.get("online", True))
    current.last_seen = dt_util.utcnow()
    current.extra = {
        key: value
        for key, value in payload.items()
        if key not in {
            "co2", "temperature", "humidity", "rssi", "hops",
            "latency_ms", "retries", "firmware",
        }
    }
    if firmware_changed:
        registry = dr.async_get(hass)
        identifier = (
            DOMAIN,
            f"station:{station.data.get(CONF_HARDWARE_ID)}",
        )
        for device in dr.async_entries_for_config_entry(
            registry, config_entry_id=entry.entry_id
        ):
            if identifier in device.identifiers:
                registry.async_update_device(device.id, sw_version=current.firmware)
                break
    async_dispatcher_send(hass, station_signal(entry.entry_id, station.subentry_id))
    return current


@callback
def ensure_master_device(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Create/return the Lüftungsstation master device only when it is actually needed."""
    entry_state = _domain_store(hass).setdefault(entry.entry_id, {})
    existing = entry_state.get("master_device_id")
    if existing:
        return str(existing)

    registry = dr.async_get(hass)
    master = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.entry_id}:hardware_master")},
        name=f"{entry.title} · Lüftungsstation-Master",
        manufacturer="Lüftungsassistent",
        model="ESP-NOW / WireGuard Hub",
    )
    entry_state["master_device_id"] = master.id
    return master.id


async def async_setup_hardware_hub(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Initialize station runtime; create a master device only for master-backed stations."""
    entry_state = _domain_store(hass).setdefault(entry.entry_id, {})
    entry_state.setdefault("states", {})
    entry_state.setdefault("discoveries", {})
    entry_state.setdefault("pairing_until", None)

    previous_unsub = entry_state.pop("stale_unsub", None)
    if callable(previous_unsub):
        previous_unsub()

    @callback
    def _expire_stale(now: datetime) -> None:
        expire_stale_stations(hass, entry, now=now)

    entry_state["stale_unsub"] = async_track_time_interval(
        hass, _expire_stale, HARDWARE_STATION_STALE_CHECK_INTERVAL
    )

    hub_stations = [
        station for station in station_subentries(entry) if station_uses_hardware_hub(station)
    ]
    needs_legacy_master = any(
        not station_is_master(station)
        and not str(
            station.data.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or ""
        ).strip()
        and configured_master_for_station(entry, station) is None
        for station in hub_stations
    )
    discoveries = entry_state.get("discoveries")
    if isinstance(discoveries, dict):
        needs_legacy_master = needs_legacy_master or any(
            station_by_any_hardware_id(entry, item.get("master_id")) is None
            for item in discoveries.values()
            if isinstance(item, dict)
        )

    if needs_legacy_master:
        ensure_master_device(hass, entry)
    else:
        # v0.10.0 used one synthetic master device.  v0.10.1 prefers the real
        # HA-selected master device and removes the placeholder once nothing
        # legacy depends on it.
        registry = dr.async_get(hass)
        master_identifier = (DOMAIN, f"{entry.entry_id}:hardware_master")
        for device in dr.async_entries_for_config_entry(
            registry, config_entry_id=entry.entry_id
        ):
            if master_identifier in device.identifiers:
                registry.async_remove_device(device.id)
                break
        entry_state.pop("master_device_id", None)


def master_device_id(hass: HomeAssistant, entry_id: str) -> str | None:
    entry_state = _domain_store(hass).get(entry_id)
    if not isinstance(entry_state, dict):
        return None
    value = entry_state.get("master_device_id")
    return str(value) if value else None


async def async_unload_hardware_hub(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop transient hardware data on unload."""
    entry_state = _domain_store(hass).pop(entry.entry_id, None)
    if isinstance(entry_state, dict):
        unsub = entry_state.get("stale_unsub")
        if callable(unsub):
            unsub()

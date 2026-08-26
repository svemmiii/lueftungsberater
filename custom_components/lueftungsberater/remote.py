"""Tailscale-only remote Lüftungsberater support."""
from __future__ import annotations

from dataclasses import dataclass
import asyncio
import ipaddress
import logging
import socket
import time
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_REMOTE_HOST,
    CONF_REMOTE_PORT,
    CONF_REMOTE_TOKEN,
    CONF_REMOTE_SELECTED_ROOMS,
    CONF_REMOTE_CLIENT_ID,
    CONF_REMOTE_USE_SSL,
    DATA_REMOTE_COORDINATORS,
    DEFAULT_REMOTE_PORT,
    DOMAIN,
    REMOTE_OFFLINE_GRACE,
    REMOTE_PROTOCOL_VERSION,
    REMOTE_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

TAILSCALE_V4 = ipaddress.ip_network("100.64.0.0/10")
TAILSCALE_V6 = ipaddress.ip_network("fd7a:115c:a1e0::/48")
REMOTE_PATH = "/api/lueftungsberater/snapshot"


class RemoteConnectionError(Exception):
    """Remote Lüftungsberater could not be reached or returned invalid data."""


class RemoteAuthError(RemoteConnectionError):
    """Remote Home Assistant rejected the access token."""


@dataclass(frozen=True)
class RemoteData:
    """Current transient snapshot of a remote Home Assistant."""

    available: bool
    instances: tuple[dict[str, Any], ...] = ()


def _ip_is_tailscale(value: str) -> bool:
    """Return whether an IP belongs to Tailscale's assigned address ranges."""
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False

    # aiohttp may expose an IPv4 peer as an IPv4-mapped IPv6 address.
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped

    return address in TAILSCALE_V4 or address in TAILSCALE_V6


def _resolve_host(host: str, port: int) -> set[str]:
    addresses: set[str] = set()
    for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        sockaddr = info[4]
        if sockaddr:
            addresses.add(str(sockaddr[0]))
    return addresses


async def async_host_is_tailscale(hass: HomeAssistant, host: str, port: int) -> bool:
    """Verify that a host resolves to a Tailscale-assigned address."""
    clean = host.strip().strip("[]")
    if _ip_is_tailscale(clean):
        return True

    try:
        addresses = await hass.async_add_executor_job(_resolve_host, clean, port)
    except OSError:
        return False
    # Never accept a hostname that can also resolve outside Tailscale. This keeps
    # the remote transport constrained to the tailnet even with multi-address DNS.
    return bool(addresses) and all(_ip_is_tailscale(address) for address in addresses)


def remote_base_url(config: dict[str, Any]) -> str:
    """Build the remote Home Assistant base URL."""
    host = str(config[CONF_REMOTE_HOST]).strip().strip("[]")
    port = int(config.get(CONF_REMOTE_PORT, DEFAULT_REMOTE_PORT))
    scheme = "https" if config.get(CONF_REMOTE_USE_SSL, False) else "http"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        display_host = host
    else:
        display_host = f"[{host}]" if address.version == 6 else host
    return f"{scheme}://{display_host}:{port}"


async def async_fetch_remote_snapshot(
    hass: HomeAssistant,
    config: dict[str, Any],
    *,
    discovery: bool = False,
) -> dict[str, Any]:
    """Fetch the remote snapshot, optionally as unfiltered room discovery."""
    host = str(config[CONF_REMOTE_HOST])
    port = int(config.get(CONF_REMOTE_PORT, DEFAULT_REMOTE_PORT))
    if not await async_host_is_tailscale(hass, host, port):
        raise RemoteConnectionError("Remote host no longer resolves to a Tailscale address")

    session = async_get_clientsession(hass)
    url = f"{remote_base_url(config)}{REMOTE_PATH}"
    headers = {
        "Authorization": f"Bearer {config[CONF_REMOTE_TOKEN]}",
        "Accept": "application/json",
    }
    params = {
        "temperature_unit": str(hass.config.units.temperature_unit),
        "client_id": str(config.get(CONF_REMOTE_CLIENT_ID) or "legacy"),
        "client_name": str(hass.config.location_name or "Home Assistant"),
    }
    if discovery:
        params["discovery"] = "1"
    elif CONF_REMOTE_SELECTED_ROOMS in config:
        selected = [str(item) for item in config.get(CONF_REMOTE_SELECTED_ROOMS, []) or []]
        params["rooms"] = ",".join(selected)

    try:
        async with asyncio.timeout(10):
            response = await session.get(url, headers=headers, params=params)
            async with response:
                if response.status == 401:
                    raise RemoteAuthError("Remote Home Assistant rejected the token")
                if response.status == 403:
                    raise RemoteConnectionError(
                        "Remote snapshot endpoint requires a direct Tailscale source"
                    )
                if response.status >= 400:
                    raise RemoteConnectionError(
                        f"Remote Home Assistant returned HTTP {response.status}"
                    )
                payload = await response.json(content_type=None)
    except RemoteConnectionError:
        raise
    except (TimeoutError, aiohttp.ClientError, ValueError) as err:
        raise RemoteConnectionError(str(err)) from err

    if not isinstance(payload, dict):
        raise RemoteConnectionError("Remote response is not an object")
    protocol = payload.get("protocol")
    if protocol not in {1, REMOTE_PROTOCOL_VERSION}:
        raise RemoteConnectionError("Unsupported remote snapshot protocol")
    instances = payload.get("instances")
    if not isinstance(instances, list):
        raise RemoteConnectionError("Remote response contains no instance list")

    # Protocol 1 peers predate server-side room filtering. Keep rolling upgrades
    # working, but still enforce the local selection before the snapshot reaches
    # the card. Protocol 2 peers already filter at the source as well.
    if not discovery and CONF_REMOTE_SELECTED_ROOMS in config:
        selected = {
            str(item) for item in config.get(CONF_REMOTE_SELECTED_ROOMS, []) or []
        }
        filtered_instances: list[dict[str, Any]] = []
        for instance in instances:
            if not isinstance(instance, dict):
                continue
            instance_id = str(instance.get("id") or "")
            rooms = instance.get("rooms", [])
            if not isinstance(rooms, list):
                rooms = []
            kept_rooms = [
                room
                for room in rooms
                if isinstance(room, dict)
                and f"{instance_id}:{room.get('id')}" in selected
            ]
            if kept_rooms:
                filtered = dict(instance)
                filtered["rooms"] = kept_rooms
                filtered_instances.append(filtered)
        payload = dict(payload)
        payload["instances"] = filtered_instances

    return payload


class LueftungsberaterRemoteCoordinator(DataUpdateCoordinator[RemoteData]):
    """Keep only the newest remote snapshots in memory."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_remote_{entry.entry_id}",
            update_interval=REMOTE_UPDATE_INTERVAL,
            always_update=False,
        )
        self.entry = entry
        self._last_success_monotonic: float | None = None
        self._reported_unavailable = False

    async def _async_update_data(self) -> RemoteData:
        try:
            payload = await async_fetch_remote_snapshot(self.hass, dict(self.entry.data))
        except (RemoteAuthError, RemoteConnectionError) as err:
            if self._last_success_monotonic is not None:
                elapsed = time.monotonic() - self._last_success_monotonic
                if elapsed < REMOTE_OFFLINE_GRACE.total_seconds() and self.data:
                    _LOGGER.debug(
                        "Remote Lüftungsberater %s temporarily unreachable: %s",
                        self.entry.title,
                        err,
                    )
                    return self.data

            if not self._reported_unavailable:
                _LOGGER.warning(
                    "Remote Lüftungsberater %s is not reachable after the grace period: %s",
                    self.entry.title,
                    err,
                )
                self._reported_unavailable = True
            else:
                _LOGGER.debug(
                    "Remote Lüftungsberater %s remains unreachable: %s",
                    self.entry.title,
                    err,
                )
            return RemoteData(available=False)

        if self._reported_unavailable:
            _LOGGER.info("Remote Lüftungsberater %s is reachable again", self.entry.title)
        self._reported_unavailable = False
        self._last_success_monotonic = time.monotonic()
        return RemoteData(
            available=True,
            instances=tuple(payload.get("instances", [])),
        )


async def async_get_or_create_remote_coordinator(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> LueftungsberaterRemoteCoordinator:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_REMOTE_COORDINATORS, {})
    coordinator = store.get(entry.entry_id)
    if coordinator is None:
        coordinator = LueftungsberaterRemoteCoordinator(hass, entry)
        store[entry.entry_id] = coordinator
        await coordinator.async_config_entry_first_refresh()
    return coordinator


def get_remote_coordinator(
    hass: HomeAssistant,
    entry_id: str,
) -> LueftungsberaterRemoteCoordinator | None:
    return (
        hass.data.get(DOMAIN, {})
        .get(DATA_REMOTE_COORDINATORS, {})
        .get(entry_id)
    )


async def async_stop_remote_coordinator(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Forget a remote coordinator during entry unload.

    DataUpdateCoordinator registers its own shutdown callback when it is tied to a
    config entry, so removing our runtime reference is enough here.
    """
    store = hass.data.get(DOMAIN, {}).get(DATA_REMOTE_COORDINATORS, {})
    store.pop(entry.entry_id, None)

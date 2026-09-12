"""Tailscale-only remote Lüftungsberater support."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import ipaddress
import logging
import socket
import time
from typing import Any

import aiohttp
from aiohttp.abc import AbstractResolver, ResolveResult

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_REMOTE_HOST,
    CONF_REMOTE_PORT,
    CONF_REMOTE_TOKEN,
    CONF_REMOTE_SELECTED_ROOMS,
    CONF_REMOTE_CLIENT_ID,
    CONF_REMOTE_SERVER_ID,
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


class RemoteAdminRequiredError(RemoteConnectionError):
    """Remote endpoint is reachable but the authenticated user is not admin."""


def normalize_remote_host(value: Any) -> str:
    """Return one canonical host spelling for storage and comparison."""
    clean = str(value).strip().strip("[]").rstrip("/").strip()
    try:
        address = ipaddress.ip_address(clean)
    except ValueError:
        # DNS names are case-insensitive and a final root dot is equivalent.
        return clean.lower().rstrip(".")
    return str(address)


def _forbidden_remote_error(body: str) -> RemoteConnectionError:
    """Classify a forbidden remote response for useful config-flow feedback."""
    if "Administrator access required" in body:
        return RemoteAdminRequiredError(
            "Remote Home Assistant user requires administrator access"
        )
    return RemoteConnectionError(
        "Remote snapshot endpoint requires a recognized Tailscale source address"
    )


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


class _PinnedTailscaleResolver(AbstractResolver):
    """Resolve exactly one verified host to exactly the verified addresses.

    The remote client deliberately does not use Home Assistant's shared HTTP
    connector here.  A hostname is security-sensitive because the access token
    must only ever be sent across the tailnet.  Verify once, then bind the
    actual aiohttp connection to those exact addresses so DNS cannot change
    between the policy check and the TCP connection.
    """

    def __init__(self, host: str, addresses: set[str]) -> None:
        self._host = normalize_remote_host(host)
        self._addresses = tuple(sorted(addresses))

    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: int = socket.AF_UNSPEC,
    ) -> list[ResolveResult]:
        clean = normalize_remote_host(host)
        if clean != self._host:
            raise OSError("Pinned remote resolver rejected a different host")

        results: list[ResolveResult] = []
        for address in self._addresses:
            ip = ipaddress.ip_address(address)
            address_family = socket.AF_INET6 if ip.version == 6 else socket.AF_INET
            if family not in {socket.AF_UNSPEC, address_family}:
                continue
            results.append(
                ResolveResult(
                    hostname=host,
                    host=address,
                    port=port,
                    family=address_family,
                    proto=socket.IPPROTO_TCP,
                    flags=socket.AI_NUMERICHOST,
                )
            )
        if not results:
            raise OSError("Pinned remote resolver has no usable address")
        return results

    async def close(self) -> None:
        """No resources are owned by the resolver."""


async def async_host_is_tailscale(hass: HomeAssistant, host: str, port: int) -> bool:
    """Verify that a host resolves to a Tailscale-assigned address."""
    clean = normalize_remote_host(host)
    if _ip_is_tailscale(clean):
        return True

    try:
        addresses = await hass.async_add_executor_job(_resolve_host, clean, port)
    except OSError:
        return False
    # Never accept a hostname that can also resolve outside Tailscale. This keeps
    # the remote transport constrained to the tailnet even with multi-address DNS.
    return bool(addresses) and all(_ip_is_tailscale(address) for address in addresses)


async def _async_verified_tailscale_addresses(
    hass: HomeAssistant,
    host: str,
    port: int,
) -> set[str]:
    """Return the exact verified addresses to which the request may connect."""
    clean = normalize_remote_host(host)
    if _ip_is_tailscale(clean):
        return {clean}
    try:
        addresses = await hass.async_add_executor_job(_resolve_host, clean, port)
    except OSError as err:
        raise RemoteConnectionError("Remote host could not be resolved") from err
    if not addresses or not all(_ip_is_tailscale(address) for address in addresses):
        raise RemoteConnectionError(
            "Remote host no longer resolves exclusively to Tailscale addresses"
        )
    return addresses


def remote_base_url(config: dict[str, Any]) -> str:
    """Build the remote Home Assistant base URL."""
    host = normalize_remote_host(config[CONF_REMOTE_HOST])
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
    host = normalize_remote_host(config[CONF_REMOTE_HOST])
    port = int(config.get(CONF_REMOTE_PORT, DEFAULT_REMOTE_PORT))
    addresses = await _async_verified_tailscale_addresses(hass, host, port)
    resolver = _PinnedTailscaleResolver(host, addresses)
    connector = aiohttp.TCPConnector(
        resolver=resolver,
        use_dns_cache=False,
    )
    url = f"{remote_base_url(config)}{REMOTE_PATH}"
    headers = {
        "Authorization": f"Bearer {config[CONF_REMOTE_TOKEN]}",
        "Accept": "application/json",
    }
    params = {
        "temperature_unit": str(hass.config.units.temperature_unit),
        "client_id": str(config.get(CONF_REMOTE_CLIENT_ID) or "legacy"),
        "client_name": str(hass.config.location_name or "Home Assistant"),
        "protocol": str(REMOTE_PROTOCOL_VERSION),
    }
    if discovery:
        params["discovery"] = "1"
    elif CONF_REMOTE_SELECTED_ROOMS in config:
        selected = [str(item) for item in config.get(CONF_REMOTE_SELECTED_ROOMS, []) or []]
        params["rooms"] = ",".join(selected)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with asyncio.timeout(10):
                response = await session.get(
                    url,
                    headers=headers,
                    params=params,
                    allow_redirects=False,
                )
                async with response:
                    if response.status == 401:
                        raise RemoteAuthError("Remote Home Assistant rejected the token")
                    if response.status == 403:
                        try:
                            error_body = await response.text()
                        except aiohttp.ClientError:
                            error_body = ""
                        raise _forbidden_remote_error(error_body)
                    if 300 <= response.status < 400:
                        raise RemoteConnectionError(
                            "Remote Home Assistant redirected the pinned request"
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
    remote_server_id = payload.get("home_assistant_instance_id")
    if remote_server_id is not None:
        if not isinstance(remote_server_id, str) or not remote_server_id.strip() or len(remote_server_id) > 128:
            raise RemoteConnectionError("Remote response contains an invalid Home Assistant instance ID")
        payload = dict(payload)
        payload["home_assistant_instance_id"] = remote_server_id.strip().lower()
    protocol = payload.get("protocol")
    if protocol not in {1, 2, REMOTE_PROTOCOL_VERSION}:
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


_DATA_REPORTED_REMOTE_DUPLICATES = "_reported_remote_duplicates"


def _remote_entries_with_server_id(
    hass: HomeAssistant,
    server_id: str,
) -> list[ConfigEntry]:
    """Return configured remote entries which identify the same HA server."""
    normalized = str(server_id or "").strip().lower()
    if not normalized:
        return []
    return [
        candidate
        for candidate in hass.config_entries.async_entries(DOMAIN)
        if candidate.data.get(CONF_REMOTE_HOST)
        and str(candidate.data.get(CONF_REMOTE_SERVER_ID) or "").strip().lower()
        == normalized
    ]


def _remote_canonical_entry(entries: list[ConfigEntry]) -> ConfigEntry:
    """Choose one deterministic legacy entry to keep for a duplicated server."""
    far_future = datetime.max.replace(tzinfo=timezone.utc)
    return min(
        entries,
        key=lambda item: (getattr(item, "created_at", None) or far_future, item.entry_id),
    )


def _merge_duplicate_remote_room_selection(
    hass: HomeAssistant,
    canonical: ConfigEntry,
    entries: list[ConfigEntry],
) -> None:
    """Preserve the union of selected rooms when legacy duplicates are found."""
    selected: set[str] = set()
    for candidate in entries:
        selected.update(
            str(item)
            for item in candidate.data.get(CONF_REMOTE_SELECTED_ROOMS, []) or []
            if item
        )
    current = {
        str(item)
        for item in canonical.data.get(CONF_REMOTE_SELECTED_ROOMS, []) or []
        if item
    }
    if selected == current:
        return
    data = dict(canonical.data)
    data[CONF_REMOTE_SELECTED_ROOMS] = sorted(selected)
    hass.config_entries.async_update_entry(canonical, data=data)


def _reconcile_remote_server_identity(
    hass: HomeAssistant,
    entry: ConfigEntry,
    server_id: str,
) -> ConfigEntry | None:
    """Reconcile pre-v0.9.4 duplicates once the stable HA UUID is known.

    New config flows already reject a duplicate server UUID. Older installations
    may however already contain the same remote once by MagicDNS name and once
    by Tailscale IP. Keep the oldest entry, merge room selections into it and
    force any already-loaded duplicates through a reload so they stop polling.
    """
    matches = _remote_entries_with_server_id(hass, server_id)
    if len(matches) <= 1:
        return None

    canonical = _remote_canonical_entry(matches)
    _merge_duplicate_remote_room_selection(hass, canonical, matches)
    duplicates = [candidate for candidate in matches if candidate.entry_id != canonical.entry_id]

    for duplicate in duplicates:
        if duplicate.state is ConfigEntryState.LOADED:
            # Use HA's scheduled reload helper: it cancels any pending setup
            # retry before reloading and avoids a retry/reload race.
            hass.config_entries.async_schedule_reload(duplicate.entry_id)

    duplicate_ids = tuple(sorted(candidate.entry_id for candidate in duplicates))
    reported = hass.data.setdefault(DOMAIN, {}).setdefault(
        _DATA_REPORTED_REMOTE_DUPLICATES, set()
    )
    report_key = (str(server_id).strip().lower(), canonical.entry_id, duplicate_ids)
    if report_key not in reported:
        reported.add(report_key)
        _LOGGER.warning(
            "Multiple Lüftungsberater remote entries identify Home Assistant %s; "
            "keeping %s and rejecting duplicate %s",
            server_id,
            canonical.entry_id,
            ", ".join(duplicate_ids),
        )
    return canonical


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
        except RemoteAuthError as err:
            # Authentication failures are not connectivity problems. Home
            # Assistant will put the entry into reauth and surface the repair to
            # the user instead of silently retrying a revoked token forever.
            raise ConfigEntryAuthFailed(
                f"Remote Home Assistant rejected the access token for {self.entry.title}"
            ) from err
        except RemoteConnectionError as err:
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

        remote_server_id = str(payload.get("home_assistant_instance_id") or "").strip()
        if remote_server_id and self.entry.data.get(CONF_REMOTE_SERVER_ID) != remote_server_id:
            data = dict(self.entry.data)
            data[CONF_REMOTE_SERVER_ID] = remote_server_id
            # Remote entries deliberately have no update listener, so learning
            # the stable peer ID does not cause a reload loop.
            self.hass.config_entries.async_update_entry(self.entry, data=data)

        if remote_server_id:
            canonical = _reconcile_remote_server_identity(
                self.hass, self.entry, remote_server_id
            )
            if canonical is not None and canonical.entry_id != self.entry.entry_id:
                # During first setup this turns the old duplicate into a visible
                # config-entry error instead of letting it start a second poller.
                # If it was already loaded, the canonical entry has scheduled a
                # reload above; that reload reaches this same first-refresh path.
                raise ConfigEntryError(
                    "This remote Home Assistant is already configured as "
                    f"{canonical.title!r}; remove the duplicate entry"
                )

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
    if coordinator is not None:
        return coordinator

    # Never publish a half-initialized coordinator. A failed first refresh can
    # trigger ConfigEntry retry/reauth and Home Assistant will shut down the
    # temporary coordinator through the ConfigEntry lifecycle. Keeping that
    # object in our own cache would make the retry reuse an already-shutdown
    # coordinator whose future refreshes are ignored.
    coordinator = LueftungsberaterRemoteCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    store[entry.entry_id] = coordinator
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

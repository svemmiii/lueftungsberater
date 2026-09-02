import asyncio
import socket
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.lueftungsberater.remote import (
    _PinnedResolver,
    _ip_is_tailscale,
    async_fetch_remote_snapshot,
)


def test_tailscale_ipv4_range_is_accepted() -> None:
    assert _ip_is_tailscale("100.64.0.1") is True
    assert _ip_is_tailscale("100.127.255.254") is True


def test_normal_private_or_public_ipv4_is_rejected() -> None:
    assert _ip_is_tailscale("192.168.178.10") is False
    assert _ip_is_tailscale("8.8.8.8") is False


def test_tailscale_ipv6_range_is_accepted() -> None:
    assert _ip_is_tailscale("fd7a:115c:a1e0::1234") is True
    assert _ip_is_tailscale("fd00::1") is False


def test_ipv4_mapped_tailscale_address_is_accepted() -> None:
    assert _ip_is_tailscale("::ffff:100.64.0.42") is True
    assert _ip_is_tailscale("::ffff:192.168.178.10") is False


def test_pinned_resolver_never_performs_a_second_dns_lookup() -> None:
    resolver = _PinnedResolver("remote.tailnet.ts.net", ("100.64.0.10",))
    rows = asyncio.run(resolver.resolve("remote.tailnet.ts.net", 8123))
    assert rows[0]["host"] == "100.64.0.10"
    assert rows[0]["family"] == socket.AF_INET
    with pytest.raises(OSError):
        asyncio.run(resolver.resolve("attacker.example", 8123))


@pytest.mark.asyncio
async def test_small_buffered_json_response_does_not_require_response_connection() -> None:
    class Response:
        status = 200
        connection = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def json(self, **_kwargs):
            return {"protocol": 2, "instances": []}

    class Session:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, *_args, **_kwargs):
            return Response()

    hass = SimpleNamespace(
        config=SimpleNamespace(
            units=SimpleNamespace(temperature_unit="°C"),
            location_name="Test HA",
        )
    )
    config = {
        "remote_host": "peer.tailnet.ts.net",
        "remote_port": 8123,
        "remote_access_token": "secret",
    }
    with (
        patch(
            "custom_components.lueftungsberater.remote._async_resolve_tailscale_addresses",
            new=AsyncMock(return_value=("100.64.0.10",)),
        ),
        patch("custom_components.lueftungsberater.remote.aiohttp.TCPConnector"),
        patch("custom_components.lueftungsberater.remote.aiohttp.ClientSession", Session),
    ):
        payload = await async_fetch_remote_snapshot(hass, config)
    assert payload == {"protocol": 2, "instances": []}

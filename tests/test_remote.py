from custom_components.lueftungsberater.remote import _ip_is_tailscale


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


async def test_pinned_resolver_never_performs_a_second_dns_lookup():
    import socket
    from custom_components.lueftungsberater.remote import _PinnedTailscaleResolver

    resolver = _PinnedTailscaleResolver("peer.tailnet.ts.net", {"100.64.0.42"})
    rows = await resolver.resolve("peer.tailnet.ts.net", 8123, socket.AF_UNSPEC)
    assert [row["host"] for row in rows] == ["100.64.0.42"]

    try:
        await resolver.resolve("changed.example.org", 8123, socket.AF_UNSPEC)
    except OSError:
        pass
    else:
        raise AssertionError("Pinned resolver accepted a different hostname")


def test_remote_forbidden_admin_response_is_classified_separately() -> None:
    from custom_components.lueftungsberater.remote import (
        RemoteAdminRequiredError,
        RemoteConnectionError,
        _forbidden_remote_error,
    )

    admin_error = _forbidden_remote_error('{"message":"Administrator access required"}')
    source_error = _forbidden_remote_error('{"message":"Tailscale connection required"}')

    assert isinstance(admin_error, RemoteAdminRequiredError)
    assert isinstance(source_error, RemoteConnectionError)
    assert not isinstance(source_error, RemoteAdminRequiredError)

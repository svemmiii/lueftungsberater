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

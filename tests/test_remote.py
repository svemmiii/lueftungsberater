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


def test_v093_client_requests_protocol_3() -> None:
    source = __import__("pathlib").Path(
        "custom_components/lueftungsberater/remote.py"
    ).read_text(encoding="utf-8")
    assert '"protocol": str(REMOTE_PROTOCOL_VERSION)' in source


def test_remote_host_normalization_is_canonical() -> None:
    from custom_components.lueftungsberater.remote import normalize_remote_host

    assert normalize_remote_host(" MeinPi.TS.NET. ") == "meinpi.ts.net"
    assert normalize_remote_host("[fd7a:115c:a1e0:0:0:0:0:42]") == "fd7a:115c:a1e0::42"
    assert normalize_remote_host("100.064.0.1") == "100.064.0.1"  # invalid IPv4 stays a hostname string


async def test_remote_auth_failure_requests_reauthentication(monkeypatch) -> None:
    from types import SimpleNamespace

    import pytest
    from homeassistant.exceptions import ConfigEntryAuthFailed

    from custom_components.lueftungsberater import remote
    from custom_components.lueftungsberater.remote import (
        LueftungsberaterRemoteCoordinator,
        RemoteAuthError,
    )

    coordinator = object.__new__(LueftungsberaterRemoteCoordinator)
    coordinator.hass = SimpleNamespace()
    coordinator.entry = SimpleNamespace(title="Wohnmobil", data={})

    async def _reject(_hass, _data):
        raise RemoteAuthError("bad token")

    monkeypatch.setattr(remote, "async_fetch_remote_snapshot", _reject)
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_failed_remote_first_refresh_is_never_published_to_runtime_cache(monkeypatch) -> None:
    """A setup retry must not reuse a coordinator that failed first refresh."""
    import pytest
    from types import SimpleNamespace

    from custom_components.lueftungsberater import remote
    from custom_components.lueftungsberater.const import DATA_REMOTE_COORDINATORS, DOMAIN

    created = []

    class FailedCoordinator:
        def __init__(self, _hass, _entry):
            created.append(self)

        async def async_config_entry_first_refresh(self):
            raise RuntimeError("initial refresh failed")

    monkeypatch.setattr(remote, "LueftungsberaterRemoteCoordinator", FailedCoordinator)
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="remote-retry")

    with pytest.raises(RuntimeError, match="initial refresh failed"):
        await remote.async_get_or_create_remote_coordinator(hass, entry)

    assert created
    assert hass.data[DOMAIN][DATA_REMOTE_COORDINATORS].get(entry.entry_id) is None


def test_legacy_remote_duplicates_are_reconciled_by_stable_server_id() -> None:
    """Old MagicDNS/IP duplicates converge once both learn the HA core UUID."""
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from custom_components.lueftungsberater.const import (
        CONF_REMOTE_HOST,
        CONF_REMOTE_SELECTED_ROOMS,
        CONF_REMOTE_SERVER_ID,
    )
    from custom_components.lueftungsberater.remote import _reconcile_remote_server_identity

    server_id = "01234567-89ab-cdef-0123-456789abcdef"
    first = SimpleNamespace(
        entry_id="old-magicdns",
        title="Wohnmobil DNS",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state=None,
        data={
            CONF_REMOTE_HOST: "wohnmobil-pi.tailnet.ts.net",
            CONF_REMOTE_SERVER_ID: server_id,
            CONF_REMOTE_SELECTED_ROOMS: ["instance:living"],
        },
    )
    second = SimpleNamespace(
        entry_id="old-ip",
        title="Wohnmobil IP",
        created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        state=None,
        data={
            CONF_REMOTE_HOST: "100.90.0.42",
            CONF_REMOTE_SERVER_ID: server_id,
            CONF_REMOTE_SELECTED_ROOMS: ["instance:bedroom"],
        },
    )
    updates = []

    class FakeConfigEntries:
        def async_entries(self, _domain):
            return [first, second]

        def async_update_entry(self, entry, *, data):
            updates.append((entry, data))
            entry.data = data

    hass = SimpleNamespace(config_entries=FakeConfigEntries(), data={})

    canonical = _reconcile_remote_server_identity(hass, second, server_id)

    assert canonical is first
    assert updates and updates[0][0] is first
    assert set(first.data[CONF_REMOTE_SELECTED_ROOMS]) == {
        "instance:living",
        "instance:bedroom",
    }


def test_legacy_remote_duplicate_warning_is_logged_only_once(caplog) -> None:
    """A known legacy duplicate must not spam the log every poll cycle."""
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from custom_components.lueftungsberater.const import (
        CONF_REMOTE_HOST,
        CONF_REMOTE_SERVER_ID,
    )
    from custom_components.lueftungsberater.remote import _reconcile_remote_server_identity

    server_id = "01234567-89ab-cdef-0123-456789abcdef"
    first = SimpleNamespace(
        entry_id="first",
        title="First",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state=None,
        data={CONF_REMOTE_HOST: "first.ts.net", CONF_REMOTE_SERVER_ID: server_id},
    )
    second = SimpleNamespace(
        entry_id="second",
        title="Second",
        created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        state=None,
        data={CONF_REMOTE_HOST: "100.90.0.42", CONF_REMOTE_SERVER_ID: server_id},
    )

    class FakeConfigEntries:
        def async_entries(self, _domain):
            return [first, second]

        def async_update_entry(self, _entry, *, data):
            _entry.data = data

    hass = SimpleNamespace(config_entries=FakeConfigEntries(), data={})

    with caplog.at_level(30):
        _reconcile_remote_server_identity(hass, first, server_id)
        _reconcile_remote_server_identity(hass, first, server_id)

    messages = [record.getMessage() for record in caplog.records if "Multiple Lüftungsberater remote entries" in record.getMessage()]
    assert len(messages) == 1

from types import SimpleNamespace

from custom_components.lueftungsberater.config_flow import SECTION_GENERAL, _remote_summary


def test_remote_summary_counts_instances_and_rooms() -> None:
    payload = {
        "home_assistant_name": "Raspberry Wohnmobil",
        "instances": [
            {"name": "Wohnmobil", "rooms": [{"id": "1", "name": "Wohnraum"}, {"id": "2", "name": "Bad"}]},
            {"name": "Technik", "rooms": [{"id": "3", "name": "Heckgarage"}]},
        ],
    }

    summary = _remote_summary(payload)
    assert summary["instances"] == "2"
    assert summary["rooms"] == "3"
    assert summary["remote_name"] == "Raspberry Wohnmobil"
    assert "Wohnmobil" in summary["details"]
    assert "Wohnraum" in summary["details"]
    assert "Heckgarage" in summary["details"]


def test_remote_summary_handles_missing_payload() -> None:
    summary = _remote_summary(None)
    assert summary["instances"] == "0"
    assert summary["rooms"] == "0"


async def test_multiple_local_entries_can_be_created(hass, enable_custom_integrations) -> None:
    """A second local Lüftungsberater must not be blocked by the first one."""
    from unittest.mock import AsyncMock, patch

    from homeassistant.config_entries import SOURCE_USER
    from homeassistant.data_entry_flow import FlowResultType

    from custom_components.lueftungsberater.const import (
        CONF_ENTRY_KIND,
        CONF_INSTANCE_NAME,
        CONF_WARNING_SOURCE,
        CONF_WEATHER,
        DOMAIN,
        ENTRY_KIND_LOCAL,
        WARNING_SOURCE_NONE,
    )

    async def create_local(title: str):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] is FlowResultType.MENU

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "local"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "local"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INSTANCE_NAME: title,
                SECTION_GENERAL: {
                    CONF_WEATHER: "weather.home",
                    CONF_WARNING_SOURCE: WARNING_SOURCE_NONE,
                },
            },
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENTRY_KIND] == ENTRY_KIND_LOCAL
        return result

    with patch(
        "custom_components.lueftungsberater.async_setup_entry",
        AsyncMock(return_value=True),
    ):
        first = await create_local("Wohnung 1")
        second = await create_local("Wohnung 2")

    assert first["title"] == "Wohnung 1"
    assert second["title"] == "Wohnung 2"
    # Repeatable manual local entries intentionally have no ConfigEntry unique_id.
    assert first["context"].get("unique_id") is None
    assert second["context"].get("unique_id") is None


async def test_remote_success_progress_reaches_confirmation(hass, enable_custom_integrations) -> None:
    """A valid remote must survive the progress step and reach confirmation."""
    import asyncio
    from unittest.mock import AsyncMock, patch

    from homeassistant.config_entries import SOURCE_USER
    from homeassistant.data_entry_flow import FlowResultType

    from custom_components.lueftungsberater.const import (
        CONF_INSTANCE_NAME,
        CONF_REMOTE_HOST,
        CONF_REMOTE_PORT,
        CONF_REMOTE_SELECTED_ROOMS,
        CONF_REMOTE_TOKEN,
        CONF_REMOTE_USE_SSL,
        DOMAIN,
    )

    payload = {
        "protocol": 1,
        "home_assistant_name": "Raspberry Wohnmobil",
        "instances": [
            {"id": "advisor-1", "name": "Wohnmobil", "rooms": [{"id": "room-1", "name": "Wohnraum"}]}
        ],
    }

    setup_entry = AsyncMock(return_value=True)

    # This test verifies only the config-flow progression. Once CREATE_ENTRY is
    # reached, Home Assistant automatically schedules setup of the new config
    # entry. A real remote entry would start its coordinator and perform an HTTP
    # request, which must not happen in a unit test.
    with (
        patch(
            "custom_components.lueftungsberater.config_flow._test_remote",
            AsyncMock(return_value=(None, payload)),
        ),
        patch(
            "custom_components.lueftungsberater.async_setup_entry",
            setup_entry,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "remote"}
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INSTANCE_NAME: "Wohnmobil",
                CONF_REMOTE_HOST: "100.86.162.62",
                CONF_REMOTE_PORT: 8123,
                CONF_REMOTE_TOKEN: "test-token",
                CONF_REMOTE_USE_SSL: False,
            },
        )

        # Consume HA's progress step the same way the frontend does.
        for _ in range(20):
            if result["type"] is not FlowResultType.SHOW_PROGRESS:
                break
            await hass.async_block_till_done()
            await asyncio.sleep(0)
            result = await hass.config_entries.flow.async_configure(result["flow_id"])

        if result["type"] is FlowResultType.SHOW_PROGRESS_DONE:
            result = await hass.config_entries.flow.async_configure(result["flow_id"])

        # Depending on the Home Assistant flow-manager version/timing, a
        # confirm-only empty form may either be exposed to the caller or be
        # consumed immediately after SHOW_PROGRESS_DONE. Both are valid.
        if result["type"] is FlowResultType.FORM:
            assert result["step_id"] == "remote_confirm"
            assert result["description_placeholders"]["remote_name"] == "Raspberry Wohnmobil"
            assert result["description_placeholders"]["rooms"] == "1"
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_REMOTE_SELECTED_ROOMS: ["advisor-1:room-1"]},
            )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Wohnmobil"
        assert result["data"][CONF_REMOTE_HOST] == "100.86.162.62"
        assert result["data"][CONF_REMOTE_PORT] == 8123
        assert result["data"][CONF_REMOTE_SELECTED_ROOMS] == ["advisor-1:room-1"]

        # CREATE_ENTRY schedules config-entry setup. Keep the setup mock active
        # until those tasks have finished so the test never opens a real socket.
        await hass.async_block_till_done()

    setup_entry.assert_awaited_once()


def test_remote_summary_keeps_v0610_protocol_shape() -> None:
    """Current summary must accept the protocol-1 payload used since v0.6.10."""
    payload = {
        "protocol": 1,
        "home_assistant_name": "Older Remote",
        "instances": [{"id": "x", "name": "Advisor", "rooms": []}],
    }
    summary = _remote_summary(payload)
    assert summary["remote_name"] == "Older Remote"
    assert summary["instances"] == "1"


async def test_warning_source_options_include_none_nina_and_dwd(
    hass, enable_custom_integrations
) -> None:
    """Optional warning source must coexist with dynamic labelled providers."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.lueftungsberater.config_flow import (
        _global_schema,
        _warning_source_options,
    )
    from custom_components.lueftungsberater.const import (
        CONF_WARNING_SOURCE,
        CONF_WEATHER,
        WARNING_SOURCE_NONE,
    )

    nina = MockConfigEntry(domain="nina", title="NINA", data={}, entry_id="nina-test")
    dwd = MockConfigEntry(
        domain="dwd_weather_warnings",
        title="DWD Warnungen",
        data={},
        entry_id="dwd-test",
    )
    nina.add_to_hass(hass)
    dwd.add_to_hass(hass)

    options = _warning_source_options(hass)
    values = [option["value"] for option in options]

    assert WARNING_SOURCE_NONE in values
    assert nina.entry_id in values
    assert dwd.entry_id in values
    assert all("value" in option and "label" in option for option in options)

    # The warning provider remains optional: omitting the field must select none.
    validated = _global_schema(hass)(
        {SECTION_GENERAL: {CONF_WEATHER: "weather.home"}}
    )
    assert validated[SECTION_GENERAL][CONF_WARNING_SOURCE] == WARNING_SOURCE_NONE
    # Notification defaults live in their optional section and are supplied by
    # the runtime when the section is not configured.
    assert "notifications" not in validated


async def test_global_schema_uses_only_notify_entity_target(
    hass, enable_custom_integrations
) -> None:
    """The setup exposes one modern notify-entity path and no Companion controls."""
    from custom_components.lueftungsberater.config_flow import (
        SECTION_GENERAL,
        SECTION_NOTIFICATIONS,
        _global_schema,
        _normalize_local_input,
    )
    from custom_components.lueftungsberater.const import (
        CONF_NOTIFY_TARGET,
        CONF_WEATHER,
    )

    schema = _global_schema(hass)
    validated = schema(
        {
            SECTION_GENERAL: {CONF_WEATHER: "weather.home"},
            SECTION_NOTIFICATIONS: {CONF_NOTIFY_TARGET: "notify.phone"},
        }
    )
    flattened = _normalize_local_input(validated)
    assert flattened[CONF_NOTIFY_TARGET] == "notify.phone"
    assert not any("mobile" in str(key).lower() for key in schema.schema)
    assert not any("vibration" in str(key).lower() for key in schema.schema)


def test_notification_trigger_selector_has_no_duplicate_values() -> None:
    """Each notification choice must appear only once in the dropdown."""
    from custom_components.lueftungsberater.config_flow import NOTIFY_TRIGGER_OPTIONS

    assert len(NOTIFY_TRIGGER_OPTIONS) == len(set(NOTIFY_TRIGGER_OPTIONS))


def test_room_schema_accepts_required_room_inputs_with_filtered_selectors(
    hass, enable_custom_integrations
) -> None:
    """The room form must remain usable with strict sensor-class selectors."""
    from custom_components.lueftungsberater.config_flow import (
        SECTION_ROOM_CLIMATE,
        SECTION_ROOM_NIGHT,
        _flatten_room_input,
        _room_schema,
    )
    from custom_components.lueftungsberater.const import (
        CONF_INDOOR_HUMIDITY,
        CONF_INDOOR_TEMP,
        CONF_ROOM_NAME,
    )

    validated = _room_schema(hass)(
        {
            CONF_ROOM_NAME: "Küche",
            SECTION_ROOM_CLIMATE: {
                CONF_INDOOR_TEMP: "sensor.kueche_temperatur",
                CONF_INDOOR_HUMIDITY: "sensor.kueche_luftfeuchtigkeit",
            },
            SECTION_ROOM_NIGHT: {},
        }
    )
    flattened = _flatten_room_input(validated)
    assert flattened[CONF_ROOM_NAME] == "Küche"
    assert flattened[CONF_INDOOR_TEMP] == "sensor.kueche_temperatur"
    assert flattened[CONF_INDOOR_HUMIDITY] == "sensor.kueche_luftfeuchtigkeit"


def test_remote_entry_is_not_offered_as_room_parent() -> None:
    """Tailscale peers are read-only and must not appear in Add room targets."""
    from types import SimpleNamespace

    from custom_components.lueftungsberater.config_flow import LueftungsberaterConfigFlow
    from custom_components.lueftungsberater.const import (
        CONF_ENTRY_KIND,
        CONF_REMOTE_HOST,
        ENTRY_KIND_REMOTE,
    )

    remote = SimpleNamespace(
        data={CONF_ENTRY_KIND: ENTRY_KIND_REMOTE, CONF_REMOTE_HOST: "100.64.0.5"}
    )
    assert LueftungsberaterConfigFlow.async_get_supported_subentry_types(remote) == {}


def test_legacy_remote_host_is_not_offered_as_room_parent() -> None:
    """A legacy remote without entry_kind must still stay read-only."""
    from types import SimpleNamespace

    from custom_components.lueftungsberater.config_flow import LueftungsberaterConfigFlow
    from custom_components.lueftungsberater.const import CONF_REMOTE_HOST

    legacy_remote = SimpleNamespace(data={CONF_REMOTE_HOST: "100.64.0.6"})
    assert LueftungsberaterConfigFlow.async_get_supported_subentry_types(legacy_remote) == {}


def test_room_air_status_is_the_default_display_mode(hass, enable_custom_integrations) -> None:
    """New local setups default to room-air status, while the other mode stays optional."""
    from custom_components.lueftungsberater.config_flow import (
        SECTION_GENERAL,
        _global_schema,
        _normalize_local_input,
    )
    from custom_components.lueftungsberater.const import (
        CONF_DISPLAY_MODE,
        CONF_WEATHER,
        DISPLAY_MODE_ROOM_AIR,
    )

    validated = _global_schema(hass)(
        {SECTION_GENERAL: {CONF_WEATHER: "weather.home"}}
    )
    flattened = _normalize_local_input(validated)
    assert flattened[CONF_DISPLAY_MODE] == DISPLAY_MODE_ROOM_AIR


def test_room_schema_uses_a_real_night_time_field(hass, enable_custom_integrations) -> None:
    """Night display time must be separate from the numeric temperature fallback."""
    from custom_components.lueftungsberater.config_flow import (
        SECTION_ROOM_CLIMATE,
        SECTION_ROOM_NIGHT,
        _room_schema,
    )
    from custom_components.lueftungsberater.const import (
        CONF_INDOOR_HUMIDITY,
        CONF_INDOOR_TEMP,
        CONF_NIGHT_END_TIME,
        CONF_NIGHT_START_TIME,
        CONF_REMOTE_ROOM_SHARE,
        CONF_ROOM_NAME,
    )

    validated = _room_schema(hass)(
        {
            CONF_ROOM_NAME: "Wohnzimmer",
            SECTION_ROOM_CLIMATE: {
                CONF_INDOOR_TEMP: "sensor.wohnzimmer_temperatur",
                CONF_INDOOR_HUMIDITY: "sensor.wohnzimmer_luftfeuchtigkeit",
            },
            SECTION_ROOM_NIGHT: {},
        }
    )
    assert str(validated[SECTION_ROOM_NIGHT][CONF_NIGHT_START_TIME]).startswith("22:00")
    assert str(validated[SECTION_ROOM_NIGHT][CONF_NIGHT_END_TIME]).startswith("07:00")
    assert validated.get("room_remote", {}).get(CONF_REMOTE_ROOM_SHARE, False) is False


async def test_remote_supported_subentry_cache_is_pinned_read_only(
    hass, enable_custom_integrations
) -> None:
    """Even an already-cached room capability must be removed from a remote entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.lueftungsberater.compat import pin_subentry_capabilities
    from custom_components.lueftungsberater.const import (
        CONF_ENTRY_KIND,
        CONF_REMOTE_HOST,
        DOMAIN,
        ENTRY_KIND_REMOTE,
        SUBENTRY_TYPE_ROOM,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Wohnmobil",
        data={
            CONF_ENTRY_KIND: ENTRY_KIND_REMOTE,
            CONF_REMOTE_HOST: "100.64.0.5",
        },
    )
    entry.add_to_hass(hass)

    # Reproduce the stale Home Assistant cache which kept the remote visible in
    # the parent picker across an integration reload.
    object.__setattr__(
        entry,
        "_supported_subentry_types",
        {SUBENTRY_TYPE_ROOM: {"supports_reconfigure": True}},
    )
    entry.clear_state_cache()
    assert SUBENTRY_TYPE_ROOM in entry.supported_subentry_types

    pin_subentry_capabilities(entry)

    assert entry.supported_subentry_types == {}
    assert entry.supported_subentry_types == {}


def test_v071_config_flow_minor_version_republishes_remote_capabilities() -> None:
    """The v0.7.1 remote-capability migration must remain reachable."""
    from custom_components.lueftungsberater.config_flow import LueftungsberaterConfigFlow

    assert LueftungsberaterConfigFlow.MINOR_VERSION >= 7


def test_v072_notification_choices_are_split_between_assistant_and_room():
    """Global hazards belong to the assistant; ventilation transitions to rooms."""
    from custom_components.lueftungsberater.config_flow import (
        NOTIFY_TRIGGER_OPTIONS,
        ROOM_NOTIFY_TRIGGER_OPTIONS,
    )
    from custom_components.lueftungsberater.const import (
        NOTIFY_TRIGGER_AIR_DANGER,
        NOTIFY_TRIGGER_AIRING_FINISHED,
        NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    )

    assert NOTIFY_TRIGGER_AIR_DANGER in NOTIFY_TRIGGER_OPTIONS
    assert NOTIFY_TRIGGER_AIRING_RECOMMENDED not in NOTIFY_TRIGGER_OPTIONS
    assert NOTIFY_TRIGGER_AIRING_FINISHED not in NOTIFY_TRIGGER_OPTIONS
    assert ROOM_NOTIFY_TRIGGER_OPTIONS == [
        NOTIFY_TRIGGER_AIRING_RECOMMENDED,
        NOTIFY_TRIGGER_AIRING_FINISHED,
    ]


def test_room_name_validation_rejects_empty_and_case_insensitive_duplicate():
    from types import SimpleNamespace
    from custom_components.lueftungsberater.config_flow import _room_name_error
    from custom_components.lueftungsberater.const import SUBENTRY_TYPE_ROOM

    entry = SimpleNamespace(
        subentries={
            "room-1": SimpleNamespace(
                subentry_id="room-1",
                subentry_type=SUBENTRY_TYPE_ROOM,
                title="Wohnzimmer",
            )
        }
    )
    assert _room_name_error(entry, "") == "room_name_empty"
    assert _room_name_error(entry, "wohnzimmer") == "room_name_duplicate"
    assert _room_name_error(entry, "Büro") is None
    assert _room_name_error(entry, "Wohnzimmer", exclude_subentry_id="room-1") is None


def test_v091_room_identity_migration_minor_version_is_enabled():
    from custom_components.lueftungsberater.config_flow import LueftungsberaterConfigFlow

    assert LueftungsberaterConfigFlow.MINOR_VERSION >= 9


async def test_remote_non_admin_error_is_reported_separately():
    from unittest.mock import AsyncMock, patch
    from custom_components.lueftungsberater.config_flow import _test_remote
    from custom_components.lueftungsberater.remote import RemoteAdminRequiredError

    hass = SimpleNamespace()
    data = {"remote_host": "100.64.0.42", "remote_port": 8123}
    with (
        patch(
            "custom_components.lueftungsberater.config_flow.async_host_is_tailscale",
            AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.lueftungsberater.config_flow.async_fetch_remote_snapshot",
            AsyncMock(side_effect=RemoteAdminRequiredError("admin required")),
        ),
    ):
        error, payload = await _test_remote(hass, data)

    assert error == "admin_required"
    assert payload is None


def test_remote_duplicate_detection_normalizes_equivalent_hosts() -> None:
    from custom_components.lueftungsberater.config_flow import _remote_endpoint_is_duplicate
    from custom_components.lueftungsberater.const import (
        CONF_ENTRY_KIND,
        CONF_REMOTE_HOST,
        CONF_REMOTE_PORT,
        ENTRY_KIND_REMOTE,
    )

    existing = SimpleNamespace(
        entry_id="remote-a",
        data={
            CONF_ENTRY_KIND: ENTRY_KIND_REMOTE,
            CONF_REMOTE_HOST: "MeinPi.ts.net.",
            CONF_REMOTE_PORT: 8123,
        },
    )
    candidate = {CONF_REMOTE_HOST: "meinpi.TS.NET", CONF_REMOTE_PORT: 8123}
    assert _remote_endpoint_is_duplicate([existing], candidate) is True
    assert (
        _remote_endpoint_is_duplicate(
            [existing], candidate, exclude_entry_id="remote-a"
        )
        is False
    )


def test_remote_reconfigure_does_not_auto_select_all_rooms_when_old_ids_disappear() -> None:
    from custom_components.lueftungsberater.config_flow import _remote_selection_schema
    from custom_components.lueftungsberater.const import CONF_REMOTE_SELECTED_ROOMS

    payload = {
        "instances": [
            {
                "id": "new-instance",
                "name": "Remote",
                "rooms": [
                    {"id": "new-1", "name": "Küche"},
                    {"id": "new-2", "name": "Bad"},
                ],
            }
        ]
    }

    first_setup = _remote_selection_schema(payload)({})
    reconfigure = _remote_selection_schema(payload, ["old-instance:old-room"])({})

    assert first_setup[CONF_REMOTE_SELECTED_ROOMS] == [
        "new-instance:new-1",
        "new-instance:new-2",
    ]
    assert reconfigure[CONF_REMOTE_SELECTED_ROOMS] == []


async def test_remote_reauth_updates_token_and_owns_reload_without_update_listener(monkeypatch) -> None:
    """Initial auth failure must recover even when setup never installed a listener."""
    from custom_components.lueftungsberater import config_flow as flow_module
    from custom_components.lueftungsberater.config_flow import LueftungsberaterConfigFlow
    from custom_components.lueftungsberater.const import (
        CONF_ENTRY_KIND,
        CONF_REMOTE_TOKEN,
        ENTRY_KIND_REMOTE,
    )

    entry = SimpleNamespace(
        entry_id="remote-entry",
        title="Wohnmobil",
        data={CONF_ENTRY_KIND: ENTRY_KIND_REMOTE, CONF_REMOTE_TOKEN: "old-token"},
    )
    calls = []

    async def _valid_remote(_hass, data):
        assert data[CONF_REMOTE_TOKEN] == "new-token"
        return None, {"instances": []}

    fake_flow = SimpleNamespace(
        hass=SimpleNamespace(),
        _get_reauth_entry=lambda: entry,
        # async_step_reauth_confirm performs the same duplicate-endpoint guard as
        # the real flow before it reaches async_update_reload_and_abort().
        _async_current_entries=lambda: [entry],
        async_update_reload_and_abort=lambda target, **kwargs: (
            calls.append((target, kwargs)) or {"type": "abort", "reason": kwargs["reason"]}
        ),
    )
    monkeypatch.setattr(flow_module, "_test_remote", _valid_remote)

    result = await LueftungsberaterConfigFlow.async_step_reauth_confirm(
        fake_flow, {CONF_REMOTE_TOKEN: "new-token"}
    )

    assert result["reason"] == "reauth_successful"
    assert len(calls) == 1
    target, kwargs = calls[0]
    assert target is entry
    assert kwargs["data_updates"] == {CONF_REMOTE_TOKEN: "new-token"}


async def test_remote_reconfigure_replaces_entry_data_and_owns_reload() -> None:
    """Remote reconfigure must not depend on an update listener for its reload."""
    from custom_components.lueftungsberater.config_flow import LueftungsberaterConfigFlow
    from custom_components.lueftungsberater.const import CONF_REMOTE_SELECTED_ROOMS

    entry = SimpleNamespace(entry_id="remote-entry")
    replacement = {"entry_kind": "remote", "remote_host": "peer.ts.net"}
    calls = []
    fake_flow = SimpleNamespace(
        _get_reconfigure_entry=lambda: entry,
        _pending_remote_data=replacement,
        _pending_remote_title="Wohnmobil",
        _pending_remote_payload={"instances": []},
        _pending_remote_previous_selection=["old:room"],
        async_update_reload_and_abort=lambda target, **kwargs: (
            calls.append((target, kwargs)) or {"type": "abort", "reason": kwargs["reason"]}
        ),
    )

    result = await LueftungsberaterConfigFlow.async_step_reconfigure_confirm(
        fake_flow, {CONF_REMOTE_SELECTED_ROOMS: ["new:room"]}
    )

    assert result["reason"] == "reconfigure_successful"
    assert len(calls) == 1
    target, kwargs = calls[0]
    assert target is entry
    assert kwargs["title"] == "Wohnmobil"
    assert kwargs["data_updates"][CONF_REMOTE_SELECTED_ROOMS] == ["new:room"]


def test_remote_duplicate_detection_uses_stable_home_assistant_instance_id() -> None:
    from custom_components.lueftungsberater.config_flow import _remote_endpoint_is_duplicate
    from custom_components.lueftungsberater.const import (
        CONF_ENTRY_KIND,
        CONF_REMOTE_HOST,
        CONF_REMOTE_PORT,
        CONF_REMOTE_SERVER_ID,
        ENTRY_KIND_REMOTE,
    )

    existing = SimpleNamespace(
        entry_id="remote-a",
        data={
            CONF_ENTRY_KIND: ENTRY_KIND_REMOTE,
            CONF_REMOTE_HOST: "wohnmobil-pi.tailnet.ts.net",
            CONF_REMOTE_PORT: 8123,
            CONF_REMOTE_SERVER_ID: "abc123",
        },
    )
    candidate = {
        CONF_REMOTE_HOST: "100.90.1.2",
        CONF_REMOTE_PORT: 8123,
        CONF_REMOTE_SERVER_ID: "ABC123",
    }
    assert _remote_endpoint_is_duplicate([existing], candidate) is True

async def test_remote_test_learns_stable_home_assistant_instance_id() -> None:
    from unittest.mock import AsyncMock, patch

    from custom_components.lueftungsberater.config_flow import _test_remote
    from custom_components.lueftungsberater.const import CONF_REMOTE_SERVER_ID

    hass = SimpleNamespace()
    data = {"remote_host": "100.64.0.42", "remote_port": 8123}
    payload = {
        "protocol": 3,
        "home_assistant_instance_id": "ABCDEF0123456789",
        "instances": [],
    }
    with (
        patch(
            "custom_components.lueftungsberater.config_flow.async_host_is_tailscale",
            AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.lueftungsberater.config_flow.async_fetch_remote_snapshot",
            AsyncMock(return_value=payload),
        ),
    ):
        error, returned = await _test_remote(hass, data)

    assert error is None
    assert returned is payload
    assert data[CONF_REMOTE_SERVER_ID] == "abcdef0123456789"

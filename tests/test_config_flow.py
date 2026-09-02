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

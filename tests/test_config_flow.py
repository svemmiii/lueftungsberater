from custom_components.lueftungsberater.config_flow import _remote_summary


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
                CONF_WEATHER: "weather.home",
                CONF_WARNING_SOURCE: WARNING_SOURCE_NONE,
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

    with patch(
        "custom_components.lueftungsberater.config_flow._test_remote",
        AsyncMock(return_value=(None, payload)),
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

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remote_confirm"
    assert result["description_placeholders"]["remote_name"] == "Raspberry Wohnmobil"
    assert result["description_placeholders"]["rooms"] == "1"


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

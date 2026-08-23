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
    assert first["context"]["unique_id"] != second["context"]["unique_id"]

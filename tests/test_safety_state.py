"""Regression tests for persistent provider-independent hard safety state."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.lueftungsberater.const import (
    CONF_WARNING_SOURCE,
    CONF_WEATHER,
    DATA_SAFETY_STATE,
    DOMAIN,
)
from custom_components.lueftungsberater.providers import WeatherAssessment, WarningAssessment
from custom_components.lueftungsberater.safety_state import async_apply_persistent_safety_state


@pytest.mark.asyncio
async def test_nina_hard_lock_survives_reload_and_unavailable_provider(
    hass, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    nina = MockConfigEntry(domain="nina", title="NINA", data={})
    nina.add_to_hass(hass)
    advisor = MockConfigEntry(
        domain=DOMAIN,
        title="Advisor",
        data={CONF_WARNING_SOURCE: nina.entry_id},
        entry_id="advisor-safety-nina",
    )
    advisor.add_to_hass(hass)
    warning_entity = "binary_sensor.nina_warning_1"

    with patch(
        "custom_components.lueftungsberater.safety_state._entry_entity_ids",
        return_value=[warning_entity],
    ):
        hass.states.async_set(warning_entity, "on", {"id": "warning-123"})
        active = WarningAssessment(
            provider_domain="nina",
            nina_status="danger",
            nina_reason_key="official_close_instruction",
            official_close_instruction=True,
            warning_ids={"warning-123"},
            source_nina_entity=warning_entity,
        )
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), active
        )

        # Simulate an integration/HA reload: in-memory state is gone, while the
        # Store remains. The provider is still unknown, so the last hard lock
        # must be restored from persistent normalized state.
        hass.data.setdefault(DOMAIN, {}).pop(DATA_SAFETY_STATE, None)
        hass.states.async_set(warning_entity, "unavailable", {"id": "warning-123"})
        restored = WarningAssessment(provider_domain="nina")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), restored
        )
        assert restored.nina_status == "danger"
        assert restored.official_close_instruction is True
        assert restored.warning_ids == {"warning-123"}

        # Explicit off is authoritative and deletes the persistent fallback.
        hass.states.async_set(warning_entity, "off", {"id": "warning-123"})
        cleared = WarningAssessment(provider_domain="nina")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), cleared
        )
        assert cleared.nina_status == "none"

        hass.data.setdefault(DOMAIN, {}).pop(DATA_SAFETY_STATE, None)
        hass.states.async_set(warning_entity, "unavailable", {"id": "warning-123"})
        after_clear = WarningAssessment(provider_domain="nina")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), after_clear
        )
        assert after_clear.nina_status == "none"


@pytest.mark.asyncio
async def test_dwd_hard_warning_survives_temporary_unavailable(
    hass, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    dwd = MockConfigEntry(domain="dwd_weather_warnings", title="DWD", data={})
    dwd.add_to_hass(hass)
    advisor = MockConfigEntry(
        domain=DOMAIN,
        title="Advisor",
        data={CONF_WARNING_SOURCE: dwd.entry_id},
        entry_id="advisor-safety-dwd",
    )
    advisor.add_to_hass(hass)
    entity = "sensor.dwd_weather_warnings_current_warning_level"

    with patch(
        "custom_components.lueftungsberater.safety_state._entry_entity_ids",
        return_value=[entity],
    ):
        hass.states.async_set(entity, "3", {"warning_count": 1})
        active = WarningAssessment(
            provider_domain="dwd_weather_warnings",
            weather_danger=True,
            weather_reason_key="weather_thunderstorm_danger",
            warning_ids={"dwd-warning"},
            source_weather_entity=entity,
        )
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), active
        )

        hass.data.setdefault(DOMAIN, {}).pop(DATA_SAFETY_STATE, None)
        hass.states.async_set(entity, "unavailable", {})
        restored = WarningAssessment(provider_domain="dwd_weather_warnings")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), restored
        )
        assert restored.weather_danger is True
        assert restored.weather_reason_key == "weather_thunderstorm_danger"

        # Available warning data with no hard danger is a real clear.
        hass.states.async_set(entity, "0", {"warning_count": 0})
        cleared = WarningAssessment(provider_domain="dwd_weather_warnings")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), cleared
        )
        assert cleared.weather_danger is False


@pytest.mark.asyncio
async def test_live_weather_hard_danger_survives_weather_entity_outage(
    hass, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    advisor = MockConfigEntry(
        domain=DOMAIN,
        title="Advisor",
        data={CONF_WEATHER: "weather.home"},
        entry_id="advisor-safety-weather",
    )
    advisor.add_to_hass(hass)
    hass.states.async_set("weather.home", "lightning", {})
    active = WeatherAssessment(
        provider_domain="met",
        weather_danger=True,
        weather_reason_key="weather_thunderstorm_danger",
    )
    await async_apply_persistent_safety_state(
        hass, advisor, active, WarningAssessment()
    )

    hass.data.setdefault(DOMAIN, {}).pop(DATA_SAFETY_STATE, None)
    hass.states.async_set("weather.home", "unavailable", {})
    restored = WeatherAssessment(provider_domain="met")
    await async_apply_persistent_safety_state(
        hass, advisor, restored, WarningAssessment()
    )
    assert restored.weather_danger is True
    assert restored.weather_reason_key == "weather_thunderstorm_danger"

    hass.states.async_set("weather.home", "sunny", {})
    cleared = WeatherAssessment(provider_domain="met")
    await async_apply_persistent_safety_state(
        hass, advisor, cleared, WarningAssessment()
    )
    assert cleared.weather_danger is False


@pytest.mark.asyncio
async def test_persisted_warning_is_not_inherited_by_new_warning_identity(
    hass, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    nina = MockConfigEntry(domain="nina", title="NINA", data={})
    nina.add_to_hass(hass)
    advisor = MockConfigEntry(
        domain=DOMAIN,
        title="Advisor",
        data={CONF_WARNING_SOURCE: nina.entry_id},
        entry_id="advisor-safety-new-id",
    )
    advisor.add_to_hass(hass)
    entity = "binary_sensor.nina_warning_identity"

    with patch(
        "custom_components.lueftungsberater.safety_state._entry_entity_ids",
        return_value=[entity],
    ):
        hass.states.async_set(entity, "on", {"id": "old-warning"})
        active = WarningAssessment(
            provider_domain="nina",
            nina_status="danger",
            nina_reason_key="official_close_instruction",
            official_close_instruction=True,
            warning_ids={"old-warning"},
            source_nina_entity=entity,
        )
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), active
        )

        hass.data.setdefault(DOMAIN, {}).pop(DATA_SAFETY_STATE, None)
        hass.states.async_set(entity, "on", {"id": "new-warning"})
        replacement = WarningAssessment(provider_domain="nina")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), replacement
        )
        assert replacement.nina_status == "none"
        assert replacement.official_close_instruction is False


@pytest.mark.asyncio
async def test_generic_warning_provider_uses_same_bounded_unavailable_fallback(
    hass, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    provider = MockConfigEntry(domain="custom_warning", title="Warnings", data={})
    provider.add_to_hass(hass)
    advisor = MockConfigEntry(
        domain=DOMAIN,
        title="Advisor",
        data={CONF_WARNING_SOURCE: provider.entry_id},
        entry_id="advisor-safety-generic",
    )
    advisor.add_to_hass(hass)
    entity = "binary_sensor.custom_warning"

    with patch(
        "custom_components.lueftungsberater.safety_state._entry_entity_ids",
        return_value=[entity],
    ):
        hass.states.async_set(entity, "on", {"id": "generic-1"})
        active = WarningAssessment(
            provider_domain="custom_warning",
            nina_status="danger",
            nina_reason_key="official_close_instruction",
            official_close_instruction=True,
            warning_ids={"generic-1"},
            source_nina_entity=entity,
        )
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), active
        )

        hass.data.setdefault(DOMAIN, {}).pop(DATA_SAFETY_STATE, None)
        hass.states.async_set(entity, "unavailable", {"id": "generic-1"})
        restored = WarningAssessment(provider_domain="custom_warning")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), restored
        )
        assert restored.nina_status == "danger"
        assert restored.official_close_instruction is True

@pytest.mark.asyncio
async def test_persisted_hard_lock_expires_after_maximum_fallback_age(
    hass, enable_custom_integrations, monkeypatch
):
    from datetime import datetime, timedelta, timezone
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    nina = MockConfigEntry(domain="nina", title="NINA", data={})
    nina.add_to_hass(hass)
    advisor = MockConfigEntry(
        domain=DOMAIN,
        title="Advisor",
        data={CONF_WARNING_SOURCE: nina.entry_id},
        entry_id="advisor-safety-expiry",
    )
    advisor.add_to_hass(hass)
    entity = "binary_sensor.nina_warning_expiry"
    start = datetime(2026, 9, 12, 8, 0, tzinfo=timezone.utc)

    with patch(
        "custom_components.lueftungsberater.safety_state._entry_entity_ids",
        return_value=[entity],
    ):
        monkeypatch.setattr(
            "custom_components.lueftungsberater.safety_state.dt_util.utcnow",
            lambda: start,
        )
        hass.states.async_set(entity, "on", {"id": "warning-expiry"})
        active = WarningAssessment(
            provider_domain="nina",
            nina_status="danger",
            nina_reason_key="official_close_instruction",
            official_close_instruction=True,
            warning_ids={"warning-expiry"},
            source_nina_entity=entity,
        )
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), active
        )

        # One minute beyond the hard one-hour maximum, UNKNOWN must no longer
        # inherit the old lock even if the provider still exposes the same ID.
        monkeypatch.setattr(
            "custom_components.lueftungsberater.safety_state.dt_util.utcnow",
            lambda: start + timedelta(minutes=61),
        )
        hass.states.async_set(entity, "unavailable", {"id": "warning-expiry"})
        expired = WarningAssessment(provider_domain="nina")
        await async_apply_persistent_safety_state(
            hass, advisor, WeatherAssessment(), expired
        )
        assert expired.nina_status == "none"
        assert expired.official_close_instruction is False

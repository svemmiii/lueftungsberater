"""Tests for optional Home Assistant area assignment."""
from __future__ import annotations

from types import SimpleNamespace


def test_room_title_uses_custom_name_or_selected_area(
    hass, enable_custom_integrations
) -> None:
    """A free room name stays independent; the HA area is a fallback label."""
    from homeassistant.helpers import area_registry as ar

    from custom_components.lueftungsberater.config_flow import _resolved_room_title
    from custom_components.lueftungsberater.const import CONF_AREA_ID, CONF_ROOM_NAME

    area = ar.async_get(hass).async_create("Wohnzimmer")

    assert _resolved_room_title(
        hass,
        {CONF_AREA_ID: area.id},
    ) == ("Wohnzimmer", None)
    assert _resolved_room_title(
        hass,
        {CONF_AREA_ID: area.id, CONF_ROOM_NAME: "Wohnbereich unten"},
    ) == ("Wohnbereich unten", None)
    assert _resolved_room_title(
        hass,
        {CONF_ROOM_NAME: "Wohnmobil vorne"},
    ) == ("Wohnmobil vorne", None)
    assert _resolved_room_title(hass, {}) == ("", "room_name_empty")
    assert _resolved_room_title(
        hass,
        {CONF_AREA_ID: "area-does-not-exist"},
    ) == ("", "area_not_found")


def test_room_schema_allows_area_without_custom_name(
    hass, enable_custom_integrations
) -> None:
    """Selecting an HA area must make a separate custom label optional."""
    from homeassistant.helpers import area_registry as ar

    from custom_components.lueftungsberater.config_flow import (
        SECTION_ROOM_CLIMATE,
        SECTION_ROOM_NIGHT,
        _flatten_room_input,
        _resolved_room_title,
        _room_schema,
    )
    from custom_components.lueftungsberater.const import (
        CONF_AREA_ID,
        CONF_INDOOR_HUMIDITY,
        CONF_INDOOR_TEMP,
        CONF_ROOM_NAME,
    )

    area = ar.async_get(hass).async_create("Küche")
    validated = _room_schema(hass)(
        {
            CONF_AREA_ID: area.id,
            SECTION_ROOM_CLIMATE: {
                CONF_INDOOR_TEMP: "sensor.kueche_temperatur",
                CONF_INDOOR_HUMIDITY: "sensor.kueche_luftfeuchtigkeit",
            },
            SECTION_ROOM_NIGHT: {},
        }
    )
    flattened = _flatten_room_input(validated)

    assert flattened[CONF_AREA_ID] == area.id
    assert CONF_ROOM_NAME not in flattened
    assert _resolved_room_title(hass, flattened) == ("Küche", None)


async def test_room_device_area_sync_and_legacy_preservation(
    hass, enable_custom_integrations
) -> None:
    """Configured areas are applied while legacy/manual assignments survive."""
    from homeassistant.helpers import area_registry as ar
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.lueftungsberater.areas import async_sync_room_device_areas
    from custom_components.lueftungsberater.const import (
        CONF_AREA_ID,
        DOMAIN,
        SUBENTRY_TYPE_ROOM,
    )

    area_registry = ar.async_get(hass)
    living = area_registry.async_create("Wohnzimmer")
    manual = area_registry.async_create("Manuell")

    entry = MockConfigEntry(domain=DOMAIN, title="Wohnung", data={})
    entry.add_to_hass(hass)

    registry = dr.async_get(hass)
    managed_device = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "room-managed")},
        name="Lüftungsassistent · Wohnzimmer",
    )
    legacy_device = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "room-legacy")},
        name="Lüftungsassistent · Alt",
    )
    registry.async_update_device(legacy_device.id, area_id=manual.id)

    managed = SimpleNamespace(
        subentry_id="room-managed",
        subentry_type=SUBENTRY_TYPE_ROOM,
        title="Wohnzimmer",
        data={CONF_AREA_ID: living.id},
    )
    legacy = SimpleNamespace(
        subentry_id="room-legacy",
        subentry_type=SUBENTRY_TYPE_ROOM,
        title="Alt",
        data={},
    )
    fake_entry = SimpleNamespace(
        entry_id=entry.entry_id,
        subentries={"room-managed": managed, "room-legacy": legacy},
    )

    async_sync_room_device_areas(hass, fake_entry)
    assert registry.async_get(managed_device.id).area_id == living.id
    assert registry.async_get(legacy_device.id).area_id == manual.id

    # Once a room has opted in to v0.9.4 area management, explicitly clearing
    # the selector removes only that integration-managed area assignment.
    managed.data = {CONF_AREA_ID: None}
    async_sync_room_device_areas(hass, fake_entry)
    assert registry.async_get(managed_device.id).area_id is None
    assert registry.async_get(legacy_device.id).area_id == manual.id


async def test_deleted_configured_area_does_not_overwrite_current_device_area(
    hass, enable_custom_integrations, monkeypatch
) -> None:
    """A stale saved area id must not silently clear or move a room device."""
    from homeassistant.helpers import area_registry as ar
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.lueftungsberater.areas import async_sync_room_device_areas
    from custom_components.lueftungsberater.const import (
        CONF_AREA_ID,
        DOMAIN,
        SUBENTRY_TYPE_ROOM,
    )

    area_registry = ar.async_get(hass)
    current = area_registry.async_create("Aktuell")

    entry = MockConfigEntry(domain=DOMAIN, title="Wohnung", data={})
    entry.add_to_hass(hass)
    registry = dr.async_get(hass)
    device = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "room-1")},
        name="Lüftungsassistent · Wohnzimmer",
    )
    registry.async_update_device(device.id, area_id=current.id)

    subentry = SimpleNamespace(
        subentry_id="room-1",
        subentry_type=SUBENTRY_TYPE_ROOM,
        title="Wohnzimmer",
        data={CONF_AREA_ID: "deleted-area"},
    )
    fake_entry = SimpleNamespace(
        entry_id=entry.entry_id,
        subentries={"room-1": subentry},
    )

    updates = []

    def _update_subentry(entry_obj, subentry_obj, *, data):
        updates.append(dict(data))
        subentry_obj.data = dict(data)
        return True

    monkeypatch.setattr(hass.config_entries, "async_update_subentry", _update_subentry)

    async_sync_room_device_areas(hass, fake_entry)
    assert registry.async_get(device.id).area_id == current.id
    assert updates == [{}]
    assert CONF_AREA_ID not in subentry.data

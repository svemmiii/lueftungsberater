"""Lifecycle cleanup regression tests for integration-owned stores."""
from types import SimpleNamespace

import pytest

from custom_components.lueftungsberater import storage_cleanup
from custom_components.lueftungsberater.const import SUBENTRY_TYPE_ROOM


@pytest.mark.asyncio
async def test_orphaned_room_stores_are_removed_but_active_room_survives(hass, monkeypatch):
    names = [
        "lueftungsberater.airing.entry.active",
        "lueftungsberater.co2.entry.deleted",
        "lueftungsberater.decision.entry.deleted",
        "lueftungsberater.mold.entry.deleted",
        "lueftungsberater.air_quality.entry",
        "other.integration.data",
    ]
    removed = []

    async def fake_names(_hass):
        return names

    class FakeStore:
        def __init__(self, _hass, _version, key):
            self.key = key

        async def async_remove(self):
            removed.append(self.key)

    monkeypatch.setattr(storage_cleanup, "_storage_names", fake_names)
    monkeypatch.setattr(storage_cleanup, "Store", FakeStore)
    entry = SimpleNamespace(
        entry_id="entry",
        subentries={
            "active": SimpleNamespace(
                subentry_id="active", subentry_type=SUBENTRY_TYPE_ROOM
            )
        },
    )

    result = await storage_cleanup.async_cleanup_orphaned_room_stores(hass, entry)

    assert result == {
        "lueftungsberater.co2.entry.deleted",
        "lueftungsberater.decision.entry.deleted",
        "lueftungsberater.mold.entry.deleted",
    }
    assert set(removed) == result


@pytest.mark.asyncio
async def test_remove_entry_stores_removes_room_and_entry_scoped_data(hass, monkeypatch):
    names = [
        "lueftungsberater.airing.entry.room",
        "lueftungsberater.co2.entry.room",
        "lueftungsberater.decision.entry.room",
        "lueftungsberater.mold.entry.room",
        "lueftungsberater.air_quality.entry",
        "lueftungsberater.recorder_entities.entry",
        "lueftungsberater.air_quality.other",
        "other.integration.data",
    ]
    removed = []

    async def fake_names(_hass):
        return names

    class FakeStore:
        def __init__(self, _hass, _version, key):
            self.key = key

        async def async_remove(self):
            removed.append(self.key)

    monkeypatch.setattr(storage_cleanup, "_storage_names", fake_names)
    monkeypatch.setattr(storage_cleanup, "Store", FakeStore)

    result = await storage_cleanup.async_remove_entry_stores(hass, "entry")

    assert result == {
        "lueftungsberater.airing.entry.room",
        "lueftungsberater.co2.entry.room",
        "lueftungsberater.decision.entry.room",
        "lueftungsberater.mold.entry.room",
        "lueftungsberater.air_quality.entry",
    }
    assert "lueftungsberater.recorder_entities.entry" not in result
    # Recorder entity IDs have their own purge-aware remover. Generic cleanup
    # must not delete its retry index after a failed recorder.purge_entities call.
    assert set(removed) == result

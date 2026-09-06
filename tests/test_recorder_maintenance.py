"""Tests for Lüftungsassistent Recorder retention."""
from types import SimpleNamespace

import pytest

from custom_components.lueftungsberater.const import DOMAIN, RECORDER_RETENTION_DAYS
from custom_components.lueftungsberater import recorder_maintenance as maintenance


def _entry(entity_id: str, unique_id: str, *, platform: str = DOMAIN):
    return SimpleNamespace(entity_id=entity_id, unique_id=unique_id, platform=platform)


def test_recorder_retention_is_capped_at_twenty_days():
    assert RECORDER_RETENTION_DAYS == 20


def test_history_partition_keeps_only_useful_room_history():
    entries = [
        _entry("sensor.living_advisor", "living_advisor"),
        _entry("sensor.living_ah", "living_absolute_humidity"),
        _entry("sensor.living_last_airing", "living_last_airing"),
        _entry("binary_sensor.living_danger", "living_critical_danger"),
        _entry("sensor.living_outdoor_ah", "living_absolute_humidity_outside"),
        _entry("sensor.living_ah_diff", "living_absolute_humidity_difference"),
        _entry("sensor.living_co2_status", "living_co2_status"),
        _entry("sensor.living_airing_status", "living_airing_status"),
        _entry("sensor.living_hours", "living_hours_since_airing"),
        _entry("sensor.unrelated", "unrelated", platform="other"),
    ]

    retained, transient = maintenance._partition_history(entries)

    assert retained == [
        "binary_sensor.living_danger",
        "sensor.living_advisor",
        "sensor.living_ah",
        "sensor.living_last_airing",
    ]
    assert transient == [
        "sensor.living_ah_diff",
        "sensor.living_airing_status",
        "sensor.living_co2_status",
        "sensor.living_hours",
        "sensor.living_outdoor_ah",
    ]


@pytest.mark.asyncio
async def test_purge_keeps_useful_history_and_drops_redundant_helpers(hass, monkeypatch):
    calls = []

    async def _handler(call):
        calls.append(dict(call.data))

    hass.services.async_register("recorder", "purge_entities", _handler)

    monkeypatch.setattr(
        maintenance.er,
        "async_entries_for_config_entry",
        lambda _registry, entry_id: [
            _entry(
                f"sensor.{entry_id}_advisor",
                f"{entry_id}_advisor",
            ),
            _entry(
                f"sensor.{entry_id}_co2_status",
                f"{entry_id}_co2_status",
            ),
            _entry(f"sensor.other_{entry_id}", "other", platform="other"),
        ],
    )

    await maintenance.async_purge_recorder_history(hass, {"entry_a", "entry_b"})
    await hass.async_block_till_done()

    assert calls == [
        {
            "entity_id": [
                "sensor.entry_a_advisor",
                "sensor.entry_b_advisor",
            ],
            "keep_days": 20,
        },
        {
            "entity_id": [
                "sensor.entry_a_co2_status",
                "sensor.entry_b_co2_status",
            ],
            "keep_days": 0,
        },
    ]


@pytest.mark.asyncio
async def test_removed_entity_ids_are_purged_from_recorder_index(hass, monkeypatch):
    calls = []

    async def _handler(call):
        calls.append(dict(call.data))

    hass.services.async_register("recorder", "purge_entities", _handler)
    monkeypatch.setattr(
        maintenance.er,
        "async_entries_for_config_entry",
        lambda _registry, _entry_id: [
            _entry("sensor.current_advisor", "current_advisor")
        ],
    )

    class FakeStore:
        def __init__(self):
            self.saved = None

        async def async_load(self):
            return {
                "entity_ids": [
                    "sensor.current_advisor",
                    "sensor.deleted_room_advisor",
                ]
            }

        async def async_save(self, data):
            self.saved = data

    store = FakeStore()
    monkeypatch.setattr(maintenance, "_index_store", lambda _hass, _entry_id: store)

    await maintenance.async_refresh_recorder_entity_index(
        hass, SimpleNamespace(entry_id="entry_a")
    )
    await hass.async_block_till_done()

    assert calls == [
        {
            "entity_id": ["sensor.deleted_room_advisor"],
            "keep_days": 0,
        }
    ]
    assert store.saved == {"entity_ids": ["sensor.current_advisor"]}

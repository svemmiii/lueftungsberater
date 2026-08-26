"""Tests for Lüftungsassistent Recorder retention."""
from types import SimpleNamespace

import pytest

from custom_components.lueftungsberater.const import DOMAIN, RECORDER_RETENTION_DAYS
from custom_components.lueftungsberater import recorder_maintenance as maintenance


def test_recorder_retention_is_capped_at_twenty_days():
    assert RECORDER_RETENTION_DAYS == 20


def test_selected_entity_ids_only_returns_our_platform():
    entries = [
        SimpleNamespace(entity_id="sensor.lueftungsberater_room", platform=DOMAIN),
        SimpleNamespace(entity_id="binary_sensor.lueftungsberater_danger", platform=DOMAIN),
        SimpleNamespace(entity_id="sensor.unrelated", platform="other"),
    ]
    assert maintenance._selected_entity_ids(entries) == [
        "binary_sensor.lueftungsberater_danger",
        "sensor.lueftungsberater_room",
    ]


@pytest.mark.asyncio
async def test_purge_targets_exact_integration_entities(hass, monkeypatch):
    calls = []

    async def _handler(call):
        calls.append(dict(call.data))

    hass.services.async_register("recorder", "purge_entities", _handler)

    monkeypatch.setattr(
        maintenance.er,
        "async_entries_for_config_entry",
        lambda _registry, entry_id: [
            SimpleNamespace(
                entity_id=f"sensor.lueftungsberater_{entry_id}",
                platform=DOMAIN,
            ),
            SimpleNamespace(entity_id=f"sensor.other_{entry_id}", platform="other"),
        ],
    )

    await maintenance.async_purge_recorder_history(hass, {"entry_a", "entry_b"})
    await hass.async_block_till_done()

    assert calls == [
        {
            "entity_id": [
                "sensor.lueftungsberater_entry_a",
                "sensor.lueftungsberater_entry_b",
            ],
            "keep_days": 20,
        }
    ]

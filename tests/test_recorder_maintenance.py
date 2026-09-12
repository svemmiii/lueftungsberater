"""Tests for Lüftungsassistent Recorder retention."""
import asyncio
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


@pytest.mark.asyncio
async def test_daily_retention_task_is_cancelled_when_last_entry_unloads(hass, monkeypatch):
    callbacks = []
    unsubscribed = []
    started = asyncio.Event()

    def _track(_hass, action, **_kwargs):
        callbacks.append(action)
        return lambda: unsubscribed.append(True)

    async def _purge(_hass):
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(maintenance, "async_track_time_change", _track)
    monkeypatch.setattr(maintenance, "async_purge_recorder_history", _purge)

    class FakeEntry:
        entry_id = "entry_a"

        def async_create_background_task(self, _hass, coro, name):
            return hass.async_create_background_task(coro, name)

    unregister = maintenance.async_register_recorder_retention(hass, FakeEntry())
    assert len(callbacks) == 1

    callbacks[0](None)
    await started.wait()
    state = hass.data[DOMAIN][maintenance.DATA_RECORDER_RETENTION]
    task = state["task"]
    assert task is not None and not task.done()

    unregister()
    await asyncio.sleep(0)

    assert task.cancelled()
    assert unsubscribed == [True]
    assert maintenance.DATA_RECORDER_RETENTION not in hass.data[DOMAIN]

@pytest.mark.asyncio
async def test_domain_retention_task_survives_one_of_multiple_entries_unloading(hass, monkeypatch):
    """A shared purge run must not belong to the first config entry."""
    callbacks = []
    started = asyncio.Event()

    def _track(_hass, action, **_kwargs):
        callbacks.append(action)
        return lambda: None

    async def _purge(_hass):
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(maintenance, "async_track_time_change", _track)
    monkeypatch.setattr(maintenance, "async_purge_recorder_history", _purge)

    first = SimpleNamespace(entry_id="entry_a")
    second = SimpleNamespace(entry_id="entry_b")
    unregister_first = maintenance.async_register_recorder_retention(hass, first)
    unregister_second = maintenance.async_register_recorder_retention(hass, second)
    assert len(callbacks) == 1

    callbacks[0](None)
    await started.wait()
    state = hass.data[DOMAIN][maintenance.DATA_RECORDER_RETENTION]
    task = state["task"]
    assert task is not None and not task.done()

    unregister_first()
    await asyncio.sleep(0)
    assert not task.done()
    assert state["entry_ids"] == {"entry_b"}

    unregister_second()
    await asyncio.sleep(0)
    assert task.cancelled()


@pytest.mark.asyncio
async def test_failed_removed_entity_purge_is_kept_for_retry(hass, monkeypatch):
    async def _handler(_call):
        raise RuntimeError("recorder unavailable")

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

    assert store.saved == {
        "entity_ids": [
            "sensor.current_advisor",
            "sensor.deleted_room_advisor",
        ]
    }

@pytest.mark.asyncio
async def test_removed_config_entry_keeps_recorder_index_and_schedules_independent_retry(hass, monkeypatch):
    """A failed final purge must still have a retry after the entry is gone."""
    scheduled = []

    class FakeStore:
        def __init__(self):
            self.removed = False

        async def async_load(self):
            return {"entity_ids": ["sensor.removed_room_advisor"]}

        async def async_remove(self):
            self.removed = True

    store = FakeStore()
    monkeypatch.setattr(maintenance, "_index_store", lambda _hass, _entry_id: store)

    async def _fail(_hass, _ids, *, keep_days):
        assert keep_days == 0
        return False

    monkeypatch.setattr(maintenance, "_async_purge_ids", _fail)
    remembered = []

    async def _remember(_hass, entry_id):
        remembered.append(entry_id)

    monkeypatch.setattr(maintenance, "_remember_orphan_entry_id", _remember)
    monkeypatch.setattr(
        maintenance,
        "_schedule_removed_recorder_index_retry",
        lambda _hass, entry_id, attempt=0: scheduled.append((entry_id, attempt)),
    )

    await maintenance.async_remove_recorder_entity_index(hass, "removed_entry")

    assert store.removed is False
    assert remembered == ["removed_entry"]
    assert scheduled == [("removed_entry", 0)]


@pytest.mark.asyncio
async def test_removed_config_entry_recorder_retry_removes_index_after_success(hass, monkeypatch):
    """The HA-owned orphan retry completes cleanup without a ConfigEntry."""
    removed = []

    class FakeStore:
        async def async_load(self):
            return {"entity_ids": ["sensor.removed_room_advisor"]}

        async def async_remove(self):
            removed.append(True)

    monkeypatch.setattr(maintenance, "_index_store", lambda _hass, _entry_id: FakeStore())

    async def _succeed(_hass, ids, *, keep_days):
        assert ids == ["sensor.removed_room_advisor"]
        assert keep_days == 0
        return True

    monkeypatch.setattr(maintenance, "_async_purge_ids", _succeed)
    forgotten = []

    async def _forget(_hass, entry_id):
        forgotten.append(entry_id)

    monkeypatch.setattr(maintenance, "_forget_orphan_entry_id", _forget)

    await maintenance._async_retry_removed_recorder_index(hass, "removed_entry", 0)

    assert removed == [True]
    assert forgotten == ["removed_entry"]


@pytest.mark.asyncio
async def test_persistent_orphan_recorder_index_is_retried_after_later_startup(hass, monkeypatch):
    """The persistent orphan list survives timers/restarts and is retried later."""
    saved = []
    removed = []

    async def _load(_hass):
        return {"removed_entry"}

    async def _save(_hass, entry_ids):
        saved.append(set(entry_ids))

    class FakeStore:
        async def async_load(self):
            return {"entity_ids": ["sensor.removed_room_advisor"]}

        async def async_remove(self):
            removed.append(True)

    async def _succeed(_hass, ids, *, keep_days):
        assert ids == ["sensor.removed_room_advisor"]
        assert keep_days == 0
        return True

    monkeypatch.setattr(maintenance, "_load_orphan_entry_ids", _load)
    monkeypatch.setattr(maintenance, "_save_orphan_entry_ids", _save)
    monkeypatch.setattr(maintenance, "_index_store", lambda _hass, _entry_id: FakeStore())
    monkeypatch.setattr(maintenance, "_async_purge_ids", _succeed)

    remaining = await maintenance.async_retry_orphaned_recorder_indexes(hass)

    assert remaining == set()
    assert removed == [True]
    assert saved[-1] == set()

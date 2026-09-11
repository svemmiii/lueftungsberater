from __future__ import annotations

from types import SimpleNamespace


async def test_outside_registry_refresh_does_not_rebind_listener_after_shutdown():
    from custom_components.lueftungsberater.outside import LueftungsberaterOutsideCoordinator

    coordinator = object.__new__(LueftungsberaterOutsideCoordinator)
    coordinator._started = True
    coordinator._registry_refresh_pending = True
    calls: list[str] = []

    async def _refresh():
        # Simulate unload while provider I/O is still awaited.
        coordinator._started = False

    coordinator.async_request_refresh = _refresh
    coordinator._replace_source_listener = lambda: calls.append("rebound")

    await coordinator._async_refresh_after_registry_change()
    assert calls == []
    assert coordinator._registry_refresh_pending is False


def test_room_coordinator_background_tasks_prefer_config_entry_lifecycle():
    from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator

    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    captured = []

    class Entry:
        def async_create_background_task(self, hass, target, name):
            captured.append((hass, name))
            target.close()
            return "task"

    coordinator.entry = Entry()
    coordinator.hass = SimpleNamespace(
        async_create_task=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("hass.async_create_task fallback should not be used")
        )
    )

    async def _job():
        return None

    assert coordinator._create_background_task(_job(), "room task") == "task"
    assert captured and captured[0][1] == "room task"


def test_airing_background_tasks_prefer_config_entry_lifecycle():
    from custom_components.lueftungsberater.airing import RoomAiringTracker

    tracker = object.__new__(RoomAiringTracker)
    captured = []

    class Entry:
        def async_create_background_task(self, hass, target, name):
            captured.append((hass, name))
            target.close()
            return "task"

    tracker.entry = Entry()
    tracker.hass = SimpleNamespace(
        async_create_task=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("hass.async_create_task fallback should not be used")
        )
    )

    async def _job():
        return None

    assert tracker._create_background_task(_job(), "airing save") == "task"
    assert captured and captured[0][1] == "airing save"

async def test_room_coordinator_shutdown_drains_notification_tasks_before_clearing_state(monkeypatch):
    import asyncio
    from custom_components.lueftungsberater import coordinator as coordinator_module
    from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator

    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    coordinator._co2_hysteresis_unsub = None
    coordinator._unsubs = []
    coordinator._notification_tasks = set()
    coordinator._started = True
    coordinator._previous_mode = None
    coordinator._previous_decision_need = None
    coordinator._previous_mode_at = None
    coordinator.data = None
    coordinator.entry = SimpleNamespace(entry_id="entry")
    coordinator.subentry = SimpleNamespace(subentry_id="room")
    coordinator.hass = SimpleNamespace()

    async def _save(_payload):
        return None

    coordinator._memory_store = SimpleNamespace(async_save=_save)
    monkeypatch.setattr(coordinator, "_memory_payload", lambda: {})
    monkeypatch.setattr(
        coordinator_module.DataUpdateCoordinator,
        "async_shutdown",
        lambda _self: _save({}),
    )

    order: list[str] = []
    monkeypatch.setattr(
        coordinator_module,
        "clear_room_notification_state",
        lambda *_args: order.append("clear"),
    )

    async def _pending_notification():
        try:
            await asyncio.sleep(60)
        finally:
            order.append("notification_done")

    task = asyncio.create_task(_pending_notification())
    coordinator._notification_tasks.add(task)
    await coordinator.async_shutdown()

    assert task.done()
    assert order.index("notification_done") < order.index("clear")


async def test_airing_stop_cancels_older_background_saves_before_final_save():
    import asyncio
    from custom_components.lueftungsberater.airing import RoomAiringTracker

    tracker = object.__new__(RoomAiringTracker)
    tracker._unsub_state = None
    tracker._unsub_tick = None
    tracker._unsub_fallback = None
    tracker._unsub_unknown_grace = None
    tracker._save_tasks = set()
    saves: list[str] = []

    async def _older_save():
        try:
            await asyncio.sleep(60)
            saves.append("old")
        finally:
            pass

    older = asyncio.create_task(_older_save())
    tracker._save_tasks.add(older)

    async def _final_save():
        saves.append("final")

    tracker._async_save = _final_save
    await tracker.async_stop()

    assert older.done()
    assert saves == ["final"]


def test_room_coordinator_publish_is_noop_after_shutdown_started(monkeypatch):
    from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator

    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    coordinator._started = False
    called: list[str] = []
    coordinator._remember_snapshot = lambda _snapshot: called.append("remember")
    coordinator.async_set_updated_data = lambda _snapshot: called.append("publish")
    coordinator._queue_notification = lambda _snapshot: called.append("notify")

    coordinator._publish_snapshot(SimpleNamespace())
    assert called == []


def test_airing_window_callback_is_noop_after_stop_started():
    from custom_components.lueftungsberater.airing import RoomAiringTracker

    tracker = object.__new__(RoomAiringTracker)
    tracker._active = False
    tracker._async_window_changed(SimpleNamespace())

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

    started = asyncio.Event()

    async def _pending_notification():
        try:
            started.set()
            await asyncio.Event().wait()
        finally:
            order.append("notification_done")

    task = asyncio.create_task(_pending_notification())
    coordinator._notification_tasks.add(task)
    await started.wait()
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


def test_room_notifications_stay_suppressed_until_startup_barrier_releases() -> None:
    """First room refreshes must not notify while other room states are unknown."""
    from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator

    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    coordinator._notifications_enabled = False
    coordinator._started = True
    coordinator.hass = SimpleNamespace(
        async_create_task=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("notification task must not be created before barrier release")
        )
    )
    coordinator._queue_notification(SimpleNamespace())




async def test_first_coordinator_refresh_obeys_notification_startup_barrier(monkeypatch):
    """The real first-refresh path must not bypass the multi-room barrier."""
    from custom_components.lueftungsberater import coordinator as coordinator_module
    from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator

    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    snapshot = SimpleNamespace()
    coordinator._notifications_enabled = False
    coordinator._build_snapshot = lambda: snapshot
    coordinator._remember_snapshot = lambda _snapshot: None
    coordinator.hass = SimpleNamespace()
    coordinator.entry = SimpleNamespace()
    coordinator.subentry = SimpleNamespace()
    calls = []

    async def _notify(*_args):
        calls.append("sent")

    monkeypatch.setattr(coordinator_module, "async_handle_room_notification", _notify)

    assert await coordinator._async_update_data() is snapshot
    assert calls == []

    coordinator._notifications_enabled = True
    assert await coordinator._async_update_data() is snapshot
    assert calls == ["sent"]

def test_enable_notifications_replays_current_snapshot_once(monkeypatch) -> None:
    from custom_components.lueftungsberater.coordinator import LueftungsberaterRoomCoordinator

    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    coordinator._notifications_enabled = False
    snapshot = SimpleNamespace()
    coordinator.data = snapshot
    queued = []
    monkeypatch.setattr(coordinator, "_queue_notification", queued.append)

    coordinator.enable_notifications()
    coordinator.enable_notifications()
    assert queued == [snapshot]


async def test_entry_reload_preserves_assistant_warning_fingerprint(hass) -> None:
    """A normal reload must not re-send the same active official warning."""
    from custom_components.lueftungsberater.const import (
        DATA_COORDINATORS,
        DATA_NOTIFICATION_STATE,
        DOMAIN,
    )
    from custom_components.lueftungsberater.coordinator import async_stop_entry_coordinators

    entry = SimpleNamespace(entry_id="entry")
    assistant_key = "assistant:entry"
    hass.data.setdefault(DOMAIN, {})[DATA_COORDINATORS] = {}
    hass.data[DOMAIN][DATA_NOTIFICATION_STATE] = {assistant_key: {"fingerprint": "same"}}

    await async_stop_entry_coordinators(hass, entry)
    assert assistant_key in hass.data[DOMAIN][DATA_NOTIFICATION_STATE]


async def test_failed_factories_do_not_publish_partial_runtime_objects(monkeypatch):
    """Factories must initialize first and publish to hass.data only on success."""
    import pytest
    from custom_components.lueftungsberater import (
        air_quality,
        airing,
        co2,
        coordinator,
        mold,
        outside,
    )
    from custom_components.lueftungsberater.const import (
        CONF_CO2,
        CONF_SURFACE_TEMP,
        CONF_WINDOWS,
        DATA_AIR_QUALITY_TRACKERS,
        DATA_CO2_TRACKERS,
        DATA_COORDINATORS,
        DATA_MOLD_TRACKERS,
        DATA_OUTSIDE_COORDINATORS,
        DATA_TRACKERS,
        DOMAIN,
    )

    class FailedAiring:
        stopped = False
        def __init__(self, *_args):
            pass
        async def async_initialize(self):
            raise RuntimeError("airing init")
        async def async_stop(self):
            self.stopped = True

    class FailedCo2:
        stopped = False
        def __init__(self, *_args):
            pass
        async def async_initialize(self):
            raise RuntimeError("co2 init")
        async def async_stop(self):
            self.stopped = True

    class FailedOutside:
        stopped = False
        def __init__(self, *_args):
            pass
        async def async_start(self):
            raise RuntimeError("outside init")
        async def async_shutdown(self):
            self.stopped = True

    class FailedMold:
        def __init__(self, *_args):
            pass
        async def async_initialize(self):
            raise RuntimeError("mold init")

    class FailedAirQuality:
        def __init__(self, *_args):
            pass
        async def async_initialize(self):
            raise RuntimeError("air quality init")

    class FailedRoom:
        stopped = False
        def __init__(self, *_args):
            pass
        async def async_start(self):
            raise RuntimeError("room init")
        async def async_shutdown(self):
            self.stopped = True

    monkeypatch.setattr(airing, "RoomAiringTracker", FailedAiring)
    monkeypatch.setattr(co2, "RoomCo2Tracker", FailedCo2)
    monkeypatch.setattr(outside, "LueftungsberaterOutsideCoordinator", FailedOutside)
    monkeypatch.setattr(mold, "RoomMoldTracker", FailedMold)
    monkeypatch.setattr(air_quality, "OutdoorAirQualityTracker", FailedAirQuality)
    monkeypatch.setattr(coordinator, "LueftungsberaterRoomCoordinator", FailedRoom)

    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry")
    room = SimpleNamespace(
        subentry_id="room",
        data={
            CONF_WINDOWS: ["binary_sensor.window"],
            CONF_CO2: "sensor.co2",
            CONF_SURFACE_TEMP: "sensor.surface",
        },
    )

    with pytest.raises(RuntimeError, match="airing init"):
        await airing.async_get_or_create_tracker(hass, entry, room)
    assert hass.data[DOMAIN][entry.entry_id][DATA_TRACKERS] == {}

    with pytest.raises(RuntimeError, match="co2 init"):
        await co2.async_get_or_create_co2_tracker(hass, entry, room)
    assert hass.data[DOMAIN][entry.entry_id][DATA_CO2_TRACKERS] == {}

    with pytest.raises(RuntimeError, match="outside init"):
        await outside.async_get_or_create_outside_coordinator(hass, entry)
    assert hass.data[DOMAIN][DATA_OUTSIDE_COORDINATORS] == {}

    with pytest.raises(RuntimeError, match="mold init"):
        await mold.async_get_or_create_mold_tracker(hass, entry, room)
    assert hass.data[DOMAIN][DATA_MOLD_TRACKERS] == {}

    with pytest.raises(RuntimeError, match="air quality init"):
        await air_quality.async_get_or_create_air_quality_tracker(hass, entry)
    assert hass.data[DOMAIN][DATA_AIR_QUALITY_TRACKERS] == {}

    with pytest.raises(RuntimeError, match="room init"):
        await coordinator.async_get_or_create_room_coordinator(hass, entry, room)
    assert hass.data[DOMAIN][DATA_COORDINATORS] == {}


async def test_failed_entry_setup_cleanup_drains_every_published_runtime_bucket(monkeypatch):
    """A later setup error must roll back components that already initialized."""
    from custom_components import lueftungsberater as integration
    from custom_components.lueftungsberater.const import CONF_ENTRY_KIND, ENTRY_KIND_LOCAL

    order: list[str] = []

    def async_stub(name):
        async def _stub(_hass, _entry):
            order.append(name)
        return _stub

    monkeypatch.setattr(integration, "async_stop_entry_coordinators", async_stub("rooms"))
    monkeypatch.setattr(integration, "async_stop_outside_coordinator", async_stub("outside"))
    monkeypatch.setattr(integration, "async_stop_air_quality_tracker", async_stub("air_quality"))
    monkeypatch.setattr(integration, "async_stop_entry_trackers", async_stub("airing"))
    monkeypatch.setattr(integration, "async_stop_entry_co2_trackers", async_stub("co2"))
    monkeypatch.setattr(integration, "async_stop_entry_mold_trackers", async_stub("mold"))
    monkeypatch.setattr(
        integration,
        "async_clear_remote_access",
        lambda _hass, _entry_id: order.append("remote_access"),
    )
    monkeypatch.setattr(
        integration,
        "async_clear_nina_details_cache",
        lambda _hass, _entry: order.append("nina"),
    )

    entry = SimpleNamespace(entry_id="entry", data={CONF_ENTRY_KIND: ENTRY_KIND_LOCAL})
    await integration._async_cleanup_runtime_after_failed_setup(SimpleNamespace(), entry)

    assert order == [
        "rooms",
        "outside",
        "air_quality",
        "airing",
        "co2",
        "mold",
        "remote_access",
        "nina",
    ]


async def test_setup_failure_during_platform_forwarding_rolls_back_partial_platforms(monkeypatch):
    """A platform exception after partial forwarding must unload that partial setup."""
    import pytest
    from custom_components import lueftungsberater as integration
    from custom_components.lueftungsberater.const import CONF_ENTRY_KIND, ENTRY_KIND_LOCAL

    calls: list[str] = []

    async def _noop_async(*_args, **_kwargs):
        return None

    class ConfigEntries:
        async def async_forward_entry_setups(self, _entry, _platforms):
            calls.append("forward")
            raise RuntimeError("platform setup failed")

        async def async_unload_platforms(self, _entry, _platforms):
            calls.append("unload")
            return True

    hass = SimpleNamespace(config_entries=ConfigEntries())
    entry = SimpleNamespace(
        entry_id="entry",
        data={CONF_ENTRY_KIND: ENTRY_KIND_LOCAL},
        subentries={},
        async_on_unload=lambda _callback: None,
        add_update_listener=lambda _callback: None,
    )

    monkeypatch.setattr(integration, "pin_subentry_capabilities", lambda _entry: None)
    monkeypatch.setattr(integration, "_async_register_frontend", _noop_async)
    monkeypatch.setattr(integration, "async_register_api", lambda _hass: None)
    monkeypatch.setattr(integration, "async_cleanup_legacy_room_history", _noop_async)
    monkeypatch.setattr(integration, "async_cleanup_orphaned_room_stores", _noop_async)
    monkeypatch.setattr(integration, "async_register_recorder_retention", lambda *_args: lambda: None)
    monkeypatch.setattr(integration, "async_get_or_create_air_quality_tracker", _noop_async)
    monkeypatch.setattr(integration, "async_get_or_create_outside_coordinator", _noop_async)
    monkeypatch.setattr(integration, "async_sync_room_device_areas", lambda *_args: None)
    monkeypatch.setattr(integration, "async_refresh_recorder_entity_index", _noop_async)
    monkeypatch.setattr(integration, "async_purge_recorder_history", _noop_async)

    async def _cleanup(_hass, _entry):
        calls.append("cleanup")

    monkeypatch.setattr(integration, "_async_cleanup_runtime_after_failed_setup", _cleanup)

    with pytest.raises(RuntimeError, match="platform setup failed"):
        await integration.async_setup_entry(hass, entry)

    assert calls == ["forward", "unload", "cleanup"]

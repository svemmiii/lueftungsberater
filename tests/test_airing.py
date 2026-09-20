from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from homeassistant.util import dt as dt_util

from custom_components.lueftungsberater.airing import RoomAiringTracker
from custom_components.lueftungsberater.const import CONF_WINDOWS


class _FakeEntry:
    """Minimal ConfigEntry test double with lifecycle-bound task API."""

    entry_id = "advisor"

    def __init__(self, hass) -> None:
        self._hass = hass

    def async_create_background_task(self, hass, target, name):
        assert hass is self._hass
        return hass.async_create_background_task(target, name)


async def test_open_session_survives_unknown_contact_during_restart(
    hass, enable_custom_integrations
) -> None:
    """A startup `unknown` contact is not proof that an airing ended."""
    opened_at = dt_util.utcnow() - timedelta(minutes=17)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "last_confirmed_airing": None,
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "unknown")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.open_since == opened_at
    assert tracker.is_open is True

    # Once the contact really reports open, the original start time is kept.
    hass.states.async_set("binary_sensor.living_window", "on")
    await hass.async_block_till_done()
    assert tracker.open_since == opened_at

    await tracker.async_stop()


async def test_definitively_closed_contact_discards_stale_open_session(
    hass, enable_custom_integrations
) -> None:
    """A stored open session must not survive a definitive closed state."""
    opened_at = dt_util.utcnow() - timedelta(minutes=17)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "last_confirmed_airing": None,
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "off")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.open_since is None
    await tracker.async_stop()


async def test_long_unknown_contact_time_is_not_counted_as_successful_airing(
    hass, enable_custom_integrations
) -> None:
    """Only definitely-open time may satisfy the five-minute airing minimum."""
    opened_at = dt_util.utcnow() - timedelta(minutes=1)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "last_confirmed_airing": None,
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "unknown")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    unknown_since = tracker._unknown_since
    assert unknown_since is not None
    tracker._cancel_unknown_grace()
    assert tracker.is_open is True
    tracker._async_unknown_grace_expired(unknown_since + timedelta(minutes=3))
    await hass.async_block_till_done()

    assert tracker.is_open is False
    assert tracker.open_since is None
    assert tracker.last_confirmed_airing is None
    await tracker.async_stop()


async def test_confirmed_close_dispatches_only_after_last_airing_is_updated(
    hass, enable_custom_integrations
) -> None:
    """A close event must not publish stale hours-since-airing to the coordinator."""
    from homeassistant.helpers.dispatcher import async_dispatcher_connect

    from custom_components.lueftungsberater.airing import tracker_signal

    opened_at = dt_util.utcnow() - timedelta(minutes=8)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "last_confirmed_airing": None,
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "on")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    observed = []

    def _capture():
        observed.append((tracker.is_open, tracker.last_confirmed_airing))

    unsub = async_dispatcher_connect(
        hass, tracker_signal(entry.entry_id, room.subentry_id), _capture
    )
    hass.states.async_set("binary_sensor.living_window", "off")
    await hass.async_block_till_done()

    assert observed
    assert observed[-1][0] is False
    assert observed[-1][1] is not None
    assert tracker.hours_since_last_airing is not None
    assert tracker.hours_since_last_airing < 0.01

    unsub()
    await tracker.async_stop()


async def test_new_room_gets_24h_routine_anchor_before_first_confirmed_airing(
    hass, enable_custom_integrations
) -> None:
    """A brand-new room starts the fallback clock without inventing an airing."""
    tracking_started = dt_util.utcnow() - timedelta(hours=25)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": None,
                "last_confirmed_airing": None,
                "tracking_started_at": tracking_started.isoformat(),
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "off")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.last_confirmed_airing is None
    assert tracker.hours_since_last_airing is None
    assert tracker.hours_since_routine_anchor is not None
    assert tracker.hours_since_routine_anchor >= 24.9

    await tracker.async_stop()


def test_registry_identity_includes_domain_and_never_matches_cross_domain():
    """A sensor must never replace a binary_sensor solely by shared unique_id."""
    binary = SimpleNamespace(
        entity_id="binary_sensor.window",
        platform="test",
        unique_id="SAME",
        device_id="device",
        original_name="Window",
        original_device_class="window",
    )
    sensor = SimpleNamespace(
        entity_id="sensor.other",
        platform="test",
        unique_id="SAME",
        device_id="device",
        original_name="Window",
        original_device_class="window",
    )

    old_identity = RoomAiringTracker._registry_identity(binary)
    new_identity = RoomAiringTracker._registry_identity(sensor)

    assert old_identity is not None and old_identity[0] == "binary_sensor"
    assert new_identity is not None and new_identity[0] == "sensor"
    assert RoomAiringTracker._identity_match_rank(old_identity, new_identity) == 0


def test_startup_repair_uses_persisted_identity_when_recreate_happened_while_ha_was_down(
    monkeypatch,
):
    """Persisted registry identity repairs an entity already recreated at startup."""
    from custom_components.lueftungsberater import airing as airing_module

    old_identity = (
        "binary_sensor",
        "zha",
        "ALT123",
        "device-1",
        "Fenster",
        "window",
    )
    recreated = SimpleNamespace(
        entity_id="binary_sensor.fenster_2",
        domain="binary_sensor",
        platform="zha",
        unique_id="NEU456",
        device_id="device-1",
        original_name="Fenster",
        original_device_class="window",
    )

    class FakeRegistry:
        def __init__(self):
            self.entities = {recreated.entity_id: recreated}

        def async_get(self, entity_id):
            return self.entities.get(entity_id)

    tracker = object.__new__(RoomAiringTracker)
    tracker.hass = SimpleNamespace()
    tracker._configured_windows = ("binary_sensor.fenster",)
    tracker.windows = tracker._configured_windows
    tracker._window_aliases = {}
    tracker._window_identities = {"binary_sensor.fenster": old_identity}

    registry = FakeRegistry()
    monkeypatch.setattr(airing_module.er, "async_get", lambda _hass: registry)

    tracker._repair_missing_windows_from_registry()

    assert tracker.windows == ("binary_sensor.fenster_2",)
    assert tracker._window_aliases == {
        "binary_sensor.fenster": "binary_sensor.fenster_2"
    }
    assert tracker._window_identities["binary_sensor.fenster"][0] == "binary_sensor"
    assert tracker._window_identities["binary_sensor.fenster"][2] == "NEU456"


async def test_airing_store_persists_registry_identity_for_restart_repair():
    """The identity required for an across-restart recreate must survive shutdown."""
    saved = []

    class FakeStore:
        async def async_save(self, data):
            saved.append(data)

    tracker = object.__new__(RoomAiringTracker)
    tracker.open_since = None
    tracker._unknown_since = None
    tracker.minimum_reached_at = None
    tracker.last_qualified_airing_seen_at = None
    tracker.last_confirmed_airing = None
    tracker.tracking_started_at = None
    tracker._window_aliases = {}
    tracker._window_identities = {
        "binary_sensor.fenster": (
            "binary_sensor",
            "zha",
            "ABC123",
            "device-1",
            "Fenster",
            "window",
        )
    }
    tracker._store = FakeStore()

    await tracker._async_save()

    assert saved[0]["last_qualified_airing_seen_at"] is None
    assert saved[0]["window_identities"]["binary_sensor.fenster"] == [
        "binary_sensor",
        "zha",
        "ABC123",
        "device-1",
        "Fenster",
        "window",
    ]


async def test_running_session_latches_after_five_minutes_but_history_waits_for_close(
    hass, enable_custom_integrations
) -> None:
    """The live five-minute latch must not advance last_confirmed_airing early."""
    now = dt_util.utcnow()
    opened_at = now - timedelta(minutes=6)
    old_confirmed = now - timedelta(hours=36)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "minimum_reached_at": None,
                "last_confirmed_airing": old_confirmed.isoformat(),
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "on")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.current_airing_qualified is True
    assert tracker.minimum_reached_at == opened_at + timedelta(minutes=5)
    assert tracker.last_qualified_airing_seen_at == opened_at + timedelta(minutes=5)
    assert tracker.last_confirmed_airing == old_confirmed

    hass.states.async_set("binary_sensor.living_window", "off")
    await hass.async_block_till_done()

    assert tracker.current_airing_qualified is False
    assert tracker.minimum_reached_at is None
    assert tracker.last_qualified_airing_seen_at is None
    assert tracker.last_confirmed_airing is not None
    assert tracker.last_confirmed_airing > old_confirmed
    assert tracker.hours_since_last_airing is not None
    assert tracker.hours_since_last_airing < 0.01

    await tracker.async_stop()


async def test_unknown_time_does_not_newly_qualify_running_airing(
    hass, enable_custom_integrations
) -> None:
    """Crossing minute five while the contact is unknown must not create proof."""
    opened_at = dt_util.utcnow() - timedelta(minutes=6)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "minimum_reached_at": None,
                "last_confirmed_airing": None,
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "unknown")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.minimum_reached_at is None
    assert tracker.current_airing_qualified is False

    # Once the same session is definitely open again, the elapsed known-open
    # session may latch immediately because the five-minute deadline is past.
    hass.states.async_set("binary_sensor.living_window", "on")
    await hass.async_block_till_done()
    assert tracker.current_airing_qualified is True
    assert tracker.minimum_reached_at == opened_at + timedelta(minutes=5)

    await tracker.async_stop()


async def test_qualified_latch_survives_short_unknown_restart_phase(
    hass, enable_custom_integrations
) -> None:
    """An already-proven five-minute session stays qualified through unknown grace."""
    now = dt_util.utcnow()
    opened_at = now - timedelta(minutes=12)
    reached_at = opened_at + timedelta(minutes=5)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "minimum_reached_at": reached_at.isoformat(),
                "last_confirmed_airing": None,
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "unknown")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.minimum_reached_at == reached_at
    assert tracker.current_airing_qualified is True
    assert tracker.last_qualified_airing_seen_at == reached_at
    assert tracker.last_confirmed_airing is None

    hass.states.async_set("binary_sensor.living_window", "on")
    await hass.async_block_till_done()
    assert tracker.current_airing_qualified is True
    assert tracker.minimum_reached_at == reached_at

    await tracker.async_stop()


async def test_qualified_session_lost_to_unknown_grace_does_not_invent_close(
    hass, enable_custom_integrations
) -> None:
    """A long unknown outage ends live tracking without fabricating history."""
    now = dt_util.utcnow()
    opened_at = now - timedelta(minutes=10)
    reached_at = opened_at + timedelta(minutes=5)
    old_confirmed = now - timedelta(hours=30)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "minimum_reached_at": reached_at.isoformat(),
                "last_confirmed_airing": old_confirmed.isoformat(),
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "on")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.current_airing_qualified is True
    assert tracker.last_confirmed_airing == old_confirmed

    hass.states.async_set("binary_sensor.living_window", "unavailable")
    await hass.async_block_till_done()
    unknown_since = tracker._unknown_since
    assert unknown_since is not None

    tracker._cancel_unknown_grace()
    tracker._async_unknown_grace_expired(unknown_since + timedelta(minutes=3))
    await hass.async_block_till_done()

    assert tracker.open_since is None
    assert tracker.minimum_reached_at is None
    assert tracker.current_airing_qualified is False
    # No OFF was observed, so the old historical close timestamp must survive.
    assert tracker.last_confirmed_airing == old_confirmed
    # The weaker routine evidence must survive the lost contact.  Otherwise the
    # 30-hour-old routine would immediately reappear after grace expiry.
    assert tracker.last_qualified_airing_seen_at == unknown_since
    assert tracker.hours_since_routine_anchor is not None
    assert tracker.hours_since_routine_anchor < 0.1

    await tracker.async_stop()


async def test_startup_closed_after_qualified_opening_keeps_routine_evidence_only(
    hass, enable_custom_integrations
) -> None:
    """A close during HA downtime must not erase a proven five-minute airing."""
    now = dt_util.utcnow()
    opened_at = now - timedelta(minutes=9)
    reached_at = opened_at + timedelta(minutes=5)
    old_confirmed = now - timedelta(hours=30)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "minimum_reached_at": reached_at.isoformat(),
                "last_confirmed_airing": old_confirmed.isoformat(),
            }

        async def async_save(self, _data):
            return None

    # HA starts after the physical close. There is no observed OFF transition,
    # therefore history must remain old while routine evidence is retained.
    hass.states.async_set("binary_sensor.living_window", "off")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()

    assert tracker.open_since is None
    assert tracker.minimum_reached_at is None
    assert tracker.last_confirmed_airing == old_confirmed
    assert tracker.last_qualified_airing_seen_at == reached_at
    assert tracker.hours_since_routine_anchor is not None
    assert tracker.hours_since_routine_anchor < 0.2

    await tracker.async_stop()


async def test_real_off_after_short_unknown_uses_observed_off_as_close_time(
    hass, enable_custom_integrations
) -> None:
    """A qualified session may close after a brief outage, but at the OFF time."""
    now = dt_util.utcnow()
    opened_at = now - timedelta(minutes=10)
    reached_at = opened_at + timedelta(minutes=5)
    entry = _FakeEntry(hass)
    room = SimpleNamespace(
        subentry_id="living",
        data={CONF_WINDOWS: ["binary_sensor.living_window"]},
    )

    class FakeStore:
        async def async_load(self):
            return {
                "open_since": opened_at.isoformat(),
                "minimum_reached_at": reached_at.isoformat(),
                "last_confirmed_airing": None,
            }

        async def async_save(self, _data):
            return None

    hass.states.async_set("binary_sensor.living_window", "on")
    tracker = RoomAiringTracker(hass, entry, room)
    tracker._store = FakeStore()
    await tracker.async_initialize()
    tracker.last_qualified_airing_seen_at = now - timedelta(hours=1)

    hass.states.async_set("binary_sensor.living_window", "unknown")
    await hass.async_block_till_done()
    assert tracker._unknown_since is not None
    # Make the distinction from the later observed OFF large and deterministic.
    tracker._unknown_since = dt_util.utcnow() - timedelta(minutes=1)
    unknown_started = tracker._unknown_since

    hass.states.async_set("binary_sensor.living_window", "off")
    await hass.async_block_till_done()

    assert tracker.last_confirmed_airing is not None
    assert tracker.last_confirmed_airing > unknown_started
    assert tracker.last_qualified_airing_seen_at is None
    assert tracker.hours_since_last_airing is not None
    assert tracker.hours_since_last_airing < 0.01

    await tracker.async_stop()

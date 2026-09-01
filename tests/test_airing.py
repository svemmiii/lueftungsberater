from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from homeassistant.util import dt as dt_util

from custom_components.lueftungsberater.airing import RoomAiringTracker
from custom_components.lueftungsberater.const import CONF_WINDOWS


async def test_open_session_survives_unknown_contact_during_restart(
    hass, enable_custom_integrations
) -> None:
    """A startup `unknown` contact is not proof that an airing ended."""
    opened_at = dt_util.utcnow() - timedelta(minutes=17)
    entry = SimpleNamespace(entry_id="advisor")
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
    entry = SimpleNamespace(entry_id="advisor")
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
    entry = SimpleNamespace(entry_id="advisor")
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
    tracker._async_unknown_grace_expired(unknown_since + timedelta(minutes=3))
    await hass.async_block_till_done()

    assert tracker.open_since is None
    assert tracker.last_confirmed_airing is None
    await tracker.async_stop()

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from homeassistant.util import dt as dt_util

from custom_components.lueftungsberater.co2 import RoomCo2Tracker
from custom_components.lueftungsberater.const import CONF_CO2


class FakeStore:
    def __init__(self, data):
        self.data = data
        self.saved = []

    async def async_load(self):
        return self.data

    async def async_save(self, data):
        self.saved.append(data)

    def async_delay_save(self, save_func, _delay):
        # Home Assistant owns the actual debounce timing. The tests only need a
        # compatible store stub; shutdown persists the final state explicitly.
        self._pending = save_func


async def test_co2_restart_restores_only_remaining_short_grace(
    hass, enable_custom_integrations
) -> None:
    """A restart must not turn the 60-second CO₂ dropout grace into a reset."""
    now = dt_util.utcnow()
    entry = SimpleNamespace(entry_id="advisor")
    room = SimpleNamespace(subentry_id="living", data={CONF_CO2: "sensor.living_co2"})
    store = FakeStore(
        {
            "last_valid_value": 1234.0,
            "last_valid_at": (now - timedelta(seconds=20)).isoformat(),
            "unavailable_since": (now - timedelta(seconds=20)).isoformat(),
        }
    )

    hass.states.async_set("sensor.living_co2", "unavailable")
    tracker = RoomCo2Tracker(hass, entry, room)
    tracker._store = store
    await tracker.async_initialize()

    assert tracker.current_value == 1234.0
    assert tracker.data_status == "grace"
    assert tracker.unavailable_since is not None

    await tracker.async_stop()


async def test_co2_restart_does_not_restore_expired_value(
    hass, enable_custom_integrations
) -> None:
    """An old persisted CO₂ value is never reused as current sensor data."""
    now = dt_util.utcnow()
    entry = SimpleNamespace(entry_id="advisor")
    room = SimpleNamespace(subentry_id="living", data={CONF_CO2: "sensor.living_co2"})
    store = FakeStore(
        {
            "last_valid_value": 1234.0,
            "last_valid_at": (now - timedelta(seconds=90)).isoformat(),
            "unavailable_since": (now - timedelta(seconds=90)).isoformat(),
        }
    )

    hass.states.async_set("sensor.living_co2", "unavailable")
    tracker = RoomCo2Tracker(hass, entry, room)
    tracker._store = store
    await tracker.async_initialize()

    assert tracker.current_value is None
    assert tracker.data_status == "unavailable"

    await tracker.async_stop()


def test_co2_state_parser_rejects_non_finite_and_implausible_values():
    from custom_components.lueftungsberater.co2 import _state_to_float

    for raw in ("nan", "inf", "-inf", -1, 1_000_001):
        assert _state_to_float(SimpleNamespace(state=raw)) is None
    assert _state_to_float(SimpleNamespace(state="1400")) == 1400.0

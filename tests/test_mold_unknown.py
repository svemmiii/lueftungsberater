from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from custom_components.lueftungsberater.mold import RoomMoldTracker


class FakeStore:
    def async_delay_save(self, _callback, _delay):
        return None



def test_long_missing_surface_sensor_time_is_not_counted_as_measured_exposure(hass):
    tracker = RoomMoldTracker(
        hass,
        SimpleNamespace(entry_id="advisor"),
        SimpleNamespace(subentry_id="living", data={}),
    )
    tracker._store = FakeStore()
    start = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    tracker.observe(85.0, start)
    tracker.observe(85.0, start + timedelta(minutes=5))
    tracker.observe(None, start + timedelta(hours=7))

    assert tracker.critical_since is None
    assert tracker.intervals == [(start, start + timedelta(minutes=5))]

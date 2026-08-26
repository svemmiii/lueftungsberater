"""Regression tests for removal of the experimental v0.7.2 RoomHistory."""
from custom_components.lueftungsberater.history import _legacy_history_keys


def test_only_legacy_lueftungsassistent_history_store_keys_are_selected():
    assert _legacy_history_keys(
        [
            "lueftungsberater.history.entry.room1",
            "lueftungsberater.decision.entry.room1",
            "other.history.entry.room1",
            "lueftungsberater.history.entry.room2",
        ]
    ) == [
        "lueftungsberater.history.entry.room1",
        "lueftungsberater.history.entry.room2",
    ]

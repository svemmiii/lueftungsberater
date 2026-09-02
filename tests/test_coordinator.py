from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from custom_components.lueftungsberater.co2_hysteresis import (
    Co2HysteresisState,
    Co2MinimumAiringState,
)
from custom_components.lueftungsberater.coordinator import (
    LueftungsberaterRoomCoordinator,
)

UTC = timezone.utc


def _snapshot(*, window_open: bool, target: float | None, need: str | None, mode: str):
    color = "yellow" if "abwaegung" in mode or "vorsicht" in mode else "green"
    return SimpleNamespace(
        result=SimpleNamespace(
            safety_lock=False,
            co2_session_need=need,
            co2_session_target=target,
            mode=mode,
            color=color,
        ),
        values={
            "window_open": window_open,
            "co2_ppm": 1500.0,
            "_co2_outdoor_context": {},
        },
    )


def _coordinator(monkeypatch, previous_snapshot, opened_at):
    coordinator = object.__new__(LueftungsberaterRoomCoordinator)
    coordinator.hass = SimpleNamespace()
    coordinator.entry = SimpleNamespace(entry_id="advisor")
    coordinator.subentry = SimpleNamespace(subentry_id="living")
    coordinator.data = previous_snapshot
    coordinator._co2_hysteresis = Co2HysteresisState()
    coordinator._co2_minimum_airing = Co2MinimumAiringState()

    monkeypatch.setattr(
        "custom_components.lueftungsberater.coordinator.get_tracker",
        lambda *_args, **_kwargs: SimpleNamespace(open_since=opened_at),
    )
    return coordinator


@pytest.mark.parametrize("target", [850.0, 1250.0, 1550.0, 1850.0, 1950.0])
def test_coordinator_starts_exact_engine_co2_target(monkeypatch, target):
    """Opening the window must preserve the exact target calculated while closed."""
    now = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
    previous = _snapshot(
        window_open=False,
        target=target,
        need="co2_high",
        mode="co2_lueften",
    )
    current = _snapshot(
        window_open=True,
        target=target,
        need="co2_high",
        mode="weiter_lueften",
    )
    coordinator = _coordinator(monkeypatch, previous, now)

    started = coordinator._start_co2_minimum_airing_if_needed(current, now)

    assert started is True
    assert coordinator._co2_hysteresis.session_active is True
    assert coordinator._co2_hysteresis.session_target_ppm == target


def test_coordinator_does_not_invent_session_when_engine_target_is_none(monkeypatch):
    """Engine target=None is authoritative and must never become a fallback 850 ppm."""
    now = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
    previous = _snapshot(
        window_open=False,
        target=None,
        need="co2_elevated",
        mode="co2_lueften_mit_nachteil",
    )
    current = _snapshot(
        window_open=True,
        target=None,
        need="co2_elevated",
        mode="weiter_lueften",
    )
    coordinator = _coordinator(monkeypatch, previous, now)

    started = coordinator._start_co2_minimum_airing_if_needed(current, now)

    assert started is False
    assert coordinator._co2_hysteresis.session_active is False
    assert coordinator._co2_hysteresis.session_target_ppm is None
    assert coordinator._co2_minimum_airing.started_at is None

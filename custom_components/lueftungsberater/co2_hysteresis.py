"""Stateful CO₂ hysteresis for user-facing airing sessions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

CO2_RECOMMEND_ON = 1000.0
CO2_RECOMMEND_RELEASE = 900.0
CO2_AIRING_FINISH = 850.0
CO2_RECOMMEND_RELEASE_STABLE = timedelta(minutes=3)
CO2_AIRING_FINISH_STABLE = timedelta(minutes=2)

_CO2_NEEDS = {"co2_elevated", "co2_high", "co2_critical"}
_CO2_MODES = {
    "co2_kritisch",
    "co2_kritisch_vorsicht",
    "co2_lueften",
    "co2_lueften_mit_nachteil",
    "co2_abwaegung",
    "co2_warten",
}


def is_co2_context(previous_mode: str | None, previous_need: str | None) -> bool:
    """Return whether the previous advisor state was CO₂-driven."""
    return previous_need in _CO2_NEEDS or previous_mode in _CO2_MODES


@dataclass(slots=True)
class Co2HysteresisDecision:
    """Flags consumed by the pure ventilation engine."""

    pending_hold: bool = False
    airing_active: bool = False
    finish_ready: bool = False
    next_check_seconds: float | None = None


@dataclass(slots=True)
class Co2HysteresisState:
    """Remember when CO₂ crossed the two release thresholds."""

    pending_below_since: datetime | None = None
    finish_below_since: datetime | None = None

    def reset(self) -> None:
        self.pending_below_since = None
        self.finish_below_since = None

    def as_dict(self) -> dict[str, str | None]:
        """Return the tiny restart-safe timer state."""
        return {
            "pending_below_since": (
                self.pending_below_since.isoformat() if self.pending_below_since else None
            ),
            "finish_below_since": (
                self.finish_below_since.isoformat() if self.finish_below_since else None
            ),
        }

    def restore(
        self,
        *,
        pending_below_since: datetime | None,
        finish_below_since: datetime | None,
    ) -> None:
        """Restore timers; normal evaluate() validation still decides relevance."""
        self.pending_below_since = pending_below_since
        self.finish_below_since = finish_below_since

    def evaluate(
        self,
        *,
        now: datetime,
        co2: float | None,
        window_open: bool,
        previous_mode: str | None,
        previous_need: str | None,
    ) -> Co2HysteresisDecision:
        """Return stable hysteresis flags without ever delaying fresh danger."""
        if co2 is None or not is_co2_context(previous_mode, previous_need):
            self.reset()
            return Co2HysteresisDecision()

        # Waiting for the user to act on an already-issued CO₂ recommendation.
        if not window_open:
            self.finish_below_since = None
            if co2 >= CO2_RECOMMEND_RELEASE:
                self.pending_below_since = None
                return Co2HysteresisDecision()

            if self.pending_below_since is None:
                self.pending_below_since = now
            elapsed = now - self.pending_below_since
            remaining = CO2_RECOMMEND_RELEASE_STABLE - elapsed
            hold = remaining.total_seconds() > 0
            return Co2HysteresisDecision(
                pending_hold=hold,
                next_check_seconds=max(0.0, remaining.total_seconds()) if hold else None,
            )

        # The user opened a window during a CO₂-driven recommendation. From this
        # point on the session has its own finish target and should not bounce at
        # the original 1000 ppm trigger.
        self.pending_below_since = None
        if co2 > CO2_AIRING_FINISH:
            self.finish_below_since = None
            return Co2HysteresisDecision(airing_active=True)

        if self.finish_below_since is None:
            self.finish_below_since = now
        elapsed = now - self.finish_below_since
        remaining = CO2_AIRING_FINISH_STABLE - elapsed
        ready = remaining.total_seconds() <= 0
        return Co2HysteresisDecision(
            airing_active=True,
            finish_ready=ready,
            next_check_seconds=max(0.0, remaining.total_seconds()) if not ready else None,
        )

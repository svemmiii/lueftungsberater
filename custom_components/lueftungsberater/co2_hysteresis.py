"""Stateful CO₂ hysteresis for user-facing airing sessions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

CO2_RECOMMEND_ON = 1000.0
CO2_RECOMMEND_RELEASE = 900.0
CO2_AIRING_FINISH = 850.0
CO2_AIRING_NEAR_TARGET_MARGIN = 50.0
CO2_AIRING_TARGET_DROP = 150.0
CO2_RECOMMEND_RELEASE_STABLE = timedelta(minutes=3)
CO2_AIRING_FINISH_STABLE = timedelta(minutes=2)
CO2_MINIMUM_AIRING = timedelta(minutes=5)

_CO2_NEEDS = {"co2_elevated", "co2_high", "co2_critical"}
_CO2_MODES = {
    "co2_kritisch",
    "co2_kritisch_vorsicht",
    "co2_lueften",
    "co2_lueften_mit_nachteil",
    "co2_abwaegung",
    "co2_warten",
    "co2_mindestlueftung",
    "co2_mindestlueftung_vorsicht",
}


def is_co2_context(previous_mode: str | None, previous_need: str | None) -> bool:
    """Return whether the previous advisor state was CO₂-driven."""
    return previous_need in _CO2_NEEDS or previous_mode in _CO2_MODES


def co2_session_target(
    *,
    co2: float | None,
    primary_need: str | None,
    mode: str | None,
) -> float:
    """Return the finish target for a CO₂ airing session.

    The target follows the CO₂ decision band that made airing worthwhile rather
    than forcing every session all the way down to 850 ppm.  The 150 ppm buffer
    retains the original anti-flicker idea while respecting trade-offs that only
    justify airing at substantially higher CO₂ levels.

    Examples:
    - normal elevated recommendation from 1000 ppm -> 850 ppm target
    - high recommendation from 1400 ppm -> 1250 ppm target
    - strong-disadvantage override from 1700 ppm -> 1550 ppm target
    - critical recommendation above 2000 ppm -> 1850 ppm target
    """
    need = str(primary_need or "")
    current = float(co2) if co2 is not None else CO2_RECOMMEND_ON
    current_mode = str(mode or "")

    if need == "co2_critical":
        trigger = 2000.0
    elif need == "co2_high":
        # The engine has an explicit >=1700 ppm override for situations where
        # otherwise unfavourable temperature/humidity would still argue against
        # airing.  If that override is what made the recommendation actionable,
        # use its own release band instead of demanding a drop to 1250 ppm.
        if current >= 1700.0 and current_mode in {
            "co2_lueften_mit_nachteil",
            "co2_abwaegung",
        }:
            trigger = 1700.0
        else:
            trigger = 1400.0
    else:
        trigger = CO2_RECOMMEND_ON

    return max(CO2_AIRING_FINISH, trigger - CO2_AIRING_TARGET_DROP)


@dataclass(slots=True)
class Co2HysteresisDecision:
    """Flags consumed by the pure ventilation engine."""

    pending_hold: bool = False
    airing_active: bool = False
    finish_ready: bool = False
    finish_target_ppm: float | None = None
    near_target_ppm: float | None = None
    next_check_seconds: float | None = None


@dataclass(slots=True)
class Co2HysteresisState:
    """Remember CO₂ recommendation and explicit airing-session state."""

    pending_below_since: datetime | None = None
    finish_below_since: datetime | None = None
    session_active: bool = False
    session_target_ppm: float | None = None
    completed_for_open_window: bool = False

    def reset(self) -> None:
        self.pending_below_since = None
        self.finish_below_since = None
        self.session_active = False
        self.session_target_ppm = None
        self.completed_for_open_window = False

    def _clear_session(self, *, keep_completed: bool = False) -> None:
        self.finish_below_since = None
        self.session_active = False
        self.session_target_ppm = None
        if not keep_completed:
            self.completed_for_open_window = False

    def end_airing_session(self, *, keep_completed: bool = True) -> None:
        """End the explicit open-window CO₂ session immediately."""
        self._clear_session(keep_completed=keep_completed)
        if keep_completed:
            self.completed_for_open_window = True

    def start_airing_session(self, *, target_ppm: float) -> bool:
        """Start a real CO₂ airing session with a fixed finish target."""
        if self.session_active or self.completed_for_open_window:
            return False
        self.pending_below_since = None
        self.finish_below_since = None
        self.session_active = True
        self.session_target_ppm = max(CO2_AIRING_FINISH, float(target_ppm))
        return True

    def as_dict(self) -> dict[str, Any]:
        """Return the tiny restart-safe timer/session state."""
        return {
            "pending_below_since": (
                self.pending_below_since.isoformat() if self.pending_below_since else None
            ),
            "finish_below_since": (
                self.finish_below_since.isoformat() if self.finish_below_since else None
            ),
            "session_active": self.session_active,
            "session_target_ppm": self.session_target_ppm,
            "completed_for_open_window": self.completed_for_open_window,
        }

    def restore(
        self,
        *,
        pending_below_since: datetime | None,
        finish_below_since: datetime | None,
        session_active: bool = False,
        session_target_ppm: float | None = None,
        completed_for_open_window: bool = False,
    ) -> None:
        """Restore timers/session; live evaluate() still validates relevance."""
        self.pending_below_since = pending_below_since
        self.finish_below_since = finish_below_since
        self.session_active = bool(session_active)
        self.completed_for_open_window = bool(completed_for_open_window)
        try:
            target = float(session_target_ppm) if session_target_ppm is not None else None
        except (TypeError, ValueError):
            target = None
        self.session_target_ppm = (
            max(CO2_AIRING_FINISH, target) if self.session_active and target is not None else None
        )
        if self.session_active and self.session_target_ppm is None:
            # Backwards-compatible fallback for a partially written store.
            self.session_target_ppm = CO2_AIRING_FINISH

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
        # Closing the window ends the explicit open-window session.  The normal
        # closed-window recommendation hysteresis can then take over again.
        if not window_open:
            if self.session_active or self.completed_for_open_window:
                self._clear_session()

        # An explicit session no longer depends on whichever mode happens to be
        # prominent on the next sensor update.  This prevents a 1400 -> 1399 ppm
        # transition or a temporary humidity/temperature priority change from
        # accidentally forgetting that the user is still airing because of CO₂.
        if window_open and self.session_active:
            self.pending_below_since = None
            target = self.session_target_ppm or CO2_AIRING_FINISH
            near_target = target + CO2_AIRING_NEAR_TARGET_MARGIN

            # A temporarily unavailable CO₂ value must never be interpreted as
            # "target reached".  The session stays remembered and can resume as
            # soon as the existing 60-second source grace/live sensor returns.
            if co2 is None:
                self.finish_below_since = None
                return Co2HysteresisDecision(
                    airing_active=True,
                    finish_target_ppm=target,
                    near_target_ppm=near_target,
                )

            if co2 > target:
                self.finish_below_since = None
                return Co2HysteresisDecision(
                    airing_active=True,
                    finish_target_ppm=target,
                    near_target_ppm=near_target,
                )

            if self.finish_below_since is None:
                self.finish_below_since = now
            elapsed = now - self.finish_below_since
            remaining = CO2_AIRING_FINISH_STABLE - elapsed
            ready = remaining.total_seconds() <= 0
            return Co2HysteresisDecision(
                airing_active=True,
                finish_ready=ready,
                finish_target_ppm=target,
                near_target_ppm=near_target,
                next_check_seconds=max(0.0, remaining.total_seconds()) if not ready else None,
            )

        if co2 is None or not is_co2_context(previous_mode, previous_need):
            self.pending_below_since = None
            self.finish_below_since = None
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

        # Compatibility path for an already-open CO₂ session restored from an
        # older release that did not persist an explicit session flag.  Use the
        # previous CO₂ band to choose the new dynamic target once, then keep it.
        if self.completed_for_open_window:
            return Co2HysteresisDecision()

        target = co2_session_target(
            co2=co2,
            primary_need=previous_need,
            mode=previous_mode,
        )
        self.start_airing_session(target_ppm=target)
        return self.evaluate(
            now=now,
            co2=co2,
            window_open=window_open,
            previous_mode=previous_mode,
            previous_need=previous_need,
        )


@dataclass(slots=True)
class Co2MinimumAiringDecision:
    """State of the short minimum CO₂ airing phase."""

    active: bool = False
    cautious: bool = False
    next_check_seconds: float | None = None
    aborted_for_outdoor_worsening: bool = False


@dataclass(slots=True)
class Co2MinimumAiringState:
    """Keep an accepted CO₂ airing recommendation stable for five minutes.

    The normal engine still decides whether airing should start at all. This
    state only remembers that the user followed such a recommendation by
    opening a window. Known outdoor drawbacks are therefore not re-litigated
    every few seconds merely because indoor CO₂ falls quickly. A newly worse
    outdoor category or any hard safety lock may end the minimum phase early.
    """

    started_at: datetime | None = None
    cautious: bool = False
    baseline_context: dict[str, Any] = field(default_factory=dict)
    completed_for_open_window: bool = False

    def reset(self, *, keep_completed: bool = False) -> None:
        self.started_at = None
        self.cautious = False
        self.baseline_context = {}
        if not keep_completed:
            self.completed_for_open_window = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "cautious": self.cautious,
            "baseline_context": dict(self.baseline_context),
            "completed_for_open_window": self.completed_for_open_window,
        }

    def restore(
        self,
        *,
        started_at: datetime | None,
        cautious: bool,
        baseline_context: dict[str, Any] | None,
        completed_for_open_window: bool = False,
    ) -> None:
        self.started_at = started_at
        self.cautious = bool(cautious)
        self.baseline_context = dict(baseline_context or {})
        self.completed_for_open_window = bool(completed_for_open_window)

    def start(
        self,
        *,
        started_at: datetime,
        cautious: bool,
        baseline_context: dict[str, Any],
    ) -> bool:
        if self.started_at is not None or self.completed_for_open_window:
            return False
        self.started_at = started_at
        self.cautious = bool(cautious)
        self.baseline_context = dict(baseline_context)
        return True

    @staticmethod
    def _outdoor_worsened(
        baseline: dict[str, Any], current: dict[str, Any]
    ) -> bool:
        # Air-quality/CO₂ levels describe outdoor data directly, so a higher
        # category is a genuine new disadvantage.
        for key in ("air_quality", "outdoor_co2"):
            try:
                before = int(baseline.get(key, 0) or 0)
                now = int(current.get(key, 0) or 0)
            except (TypeError, ValueError):
                continue
            if now > before:
                return True

        # Temperature and absolute-humidity bands are relative to the room.
        # Require the outdoor reading itself to have moved in the bad direction
        # as well, so improving indoor values cannot accidentally cancel the
        # promised five-minute minimum.
        try:
            temp_before = int(baseline.get("temperature", 0) or 0)
            temp_now = int(current.get("temperature", 0) or 0)
            ta_before = float(baseline.get("outdoor_temp"))
            ta_now = float(current.get("outdoor_temp"))
            direction = str(baseline.get("temperature_direction") or "neutral")
            if temp_now > temp_before:
                if direction == "hot" and ta_now > ta_before + 0.5:
                    return True
                if direction == "cold" and ta_now < ta_before - 0.5:
                    return True
                if direction == "neutral" and abs(ta_now - ta_before) > 0.5:
                    return True
        except (TypeError, ValueError):
            pass

        try:
            humidity_before = int(baseline.get("humidity", 0) or 0)
            humidity_now = int(current.get("humidity", 0) or 0)
            ah_before = float(baseline.get("outdoor_absolute_humidity"))
            ah_now = float(current.get("outdoor_absolute_humidity"))
            if humidity_now > humidity_before and ah_now > ah_before + 0.2:
                return True
        except (TypeError, ValueError):
            pass

        for key in ("nina_caution", "weather_caution", "rain"):
            if bool(current.get(key)) and not bool(baseline.get(key)):
                return True
        return False

    def evaluate(
        self,
        *,
        now: datetime,
        window_open: bool,
        current_context: dict[str, Any] | None,
        safety_lock: bool,
    ) -> Co2MinimumAiringDecision:
        if not window_open:
            self.reset()
            return Co2MinimumAiringDecision()

        if self.started_at is None:
            return Co2MinimumAiringDecision()

        if safety_lock:
            self.reset(keep_completed=True)
            self.completed_for_open_window = True
            return Co2MinimumAiringDecision()

        if current_context is not None and self._outdoor_worsened(
            self.baseline_context, current_context
        ):
            self.reset(keep_completed=True)
            self.completed_for_open_window = True
            return Co2MinimumAiringDecision(aborted_for_outdoor_worsening=True)

        elapsed = now - self.started_at
        remaining = CO2_MINIMUM_AIRING - elapsed
        if remaining.total_seconds() <= 0:
            self.reset(keep_completed=True)
            self.completed_for_open_window = True
            return Co2MinimumAiringDecision()

        return Co2MinimumAiringDecision(
            active=True,
            cautious=self.cautious,
            next_check_seconds=max(0.0, remaining.total_seconds()),
        )

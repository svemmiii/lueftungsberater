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
CO2_REARM_MARGIN = 50.0
CO2_RECOMMEND_RELEASE_STABLE = timedelta(minutes=3)
CO2_AIRING_FINISH_STABLE = timedelta(minutes=2)
CO2_REARM_STABLE = timedelta(minutes=2)
CO2_MINIMUM_AIRING = timedelta(minutes=5)
CO2_MEASUREMENT_MISSING_TIMEOUT = timedelta(minutes=5)
CO2_FAST_REBOUND_WINDOW = timedelta(minutes=90)
CO2_REBOUND_MEMORY = timedelta(hours=2)
CO2_HIGH_LOAD_HOLD = timedelta(hours=2)

CO2_TRIGGER_STAGES = (1000.0, 1400.0, 1700.0, 2000.0)

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
    "co2_messung_verloren",
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
    rearm_threshold_ppm: float | None = None
    next_check_seconds: float | None = None
    measurement_timed_out: bool = False
    trend_ppm_per_min: float | None = None
    minutes_to_2000: float | None = None


@dataclass(slots=True)
class Co2HysteresisState:
    """Remember CO₂ recommendation and explicit airing-session state."""

    pending_below_since: datetime | None = None
    finish_below_since: datetime | None = None
    session_active: bool = False
    session_target_ppm: float | None = None
    completed_for_open_window: bool = False
    rearm_threshold_ppm: float | None = None
    rearm_below_since: datetime | None = None
    rearm_candidate_ppm: float | None = None
    measurement_missing_since: datetime | None = None
    measurement_timed_out_for_open_window: bool = False
    measurement_timeout_target_ppm: float | None = None
    last_completed_at: datetime | None = None
    last_completed_trigger_ppm: float | None = None
    rebound_count: int = 0
    rebound_counted_for_completion: bool = False
    high_load_until: datetime | None = None
    trend_anchor_ppm: float | None = None
    trend_anchor_at: datetime | None = None
    trend_ppm_per_min: float | None = None
    trend_positive_intervals: int = 0

    def reset(self) -> None:
        self.pending_below_since = None
        self.finish_below_since = None
        self.session_active = False
        self.session_target_ppm = None
        self.completed_for_open_window = False
        self.rearm_threshold_ppm = None
        self.rearm_below_since = None
        self.rearm_candidate_ppm = None
        self.measurement_missing_since = None
        self.measurement_timed_out_for_open_window = False
        self.measurement_timeout_target_ppm = None
        self.last_completed_at = None
        self.last_completed_trigger_ppm = None
        self.rebound_count = 0
        self.rebound_counted_for_completion = False
        self.high_load_until = None
        self.trend_anchor_ppm = None
        self.trend_anchor_at = None
        self.trend_ppm_per_min = None
        self.trend_positive_intervals = 0

    def high_load_active(self, now: datetime) -> bool:
        """Return whether repeated quick rebound is currently active."""
        return bool(self.high_load_until is not None and now < self.high_load_until)

    def _update_trend(self, *, now: datetime, co2: float | None) -> tuple[float | None, float | None]:
        """Track a conservative CO2 rise rate from real value changes.

        Coordinator refreshes may occur for unrelated entities, so an unchanged
        CO2 state must not be treated as a fresh zero-slope sample.  We only
        advance the anchor when the numeric CO2 reading itself changes and use
        samples at least one minute apart to avoid amplifying sensor jitter.
        """
        if co2 is None:
            return self.trend_ppm_per_min, None

        current = float(co2)
        if self.trend_anchor_ppm is None or self.trend_anchor_at is None:
            self.trend_anchor_ppm = current
            self.trend_anchor_at = now
            self.trend_ppm_per_min = None
            return None, None

        if current != self.trend_anchor_ppm:
            elapsed_minutes = (now - self.trend_anchor_at).total_seconds() / 60.0
            if elapsed_minutes >= 1.0:
                raw_slope = (current - self.trend_anchor_ppm) / elapsed_minutes
                # Smooth the live slope, but do not let the *first* positive
                # interval authorize a predictive high-load re-trigger. A
                # second consecutive real rise (each at least one minute
                # apart) is required before minutes_to_2000 becomes actionable.
                # Any flat/falling interval breaks that confirmation chain.
                self.trend_ppm_per_min = (
                    raw_slope
                    if self.trend_ppm_per_min is None
                    else 0.65 * raw_slope + 0.35 * self.trend_ppm_per_min
                )
                if raw_slope > 0:
                    self.trend_positive_intervals += 1
                else:
                    self.trend_positive_intervals = 0
                self.trend_anchor_ppm = current
                self.trend_anchor_at = now

        minutes_to_2000 = None
        slope = self.trend_ppm_per_min
        if (
            slope is not None
            and slope > 0
            and current < 2000.0
            and self.trend_positive_intervals >= 2
        ):
            minutes_to_2000 = max(0.0, (2000.0 - current) / slope)
        return slope, minutes_to_2000

    def _clear_session(self, *, keep_completed: bool = False) -> None:
        self.finish_below_since = None
        self.measurement_missing_since = None
        self.session_active = False
        self.session_target_ppm = None
        if not keep_completed:
            self.completed_for_open_window = False
            self.measurement_timed_out_for_open_window = False
            self.measurement_timeout_target_ppm = None

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
        self.measurement_missing_since = None
        self.measurement_timed_out_for_open_window = False
        self.measurement_timeout_target_ppm = None
        return True

    @staticmethod
    def _trigger_for_target(target_ppm: float) -> float:
        """Return the decision band that belongs to a fixed session target."""
        raw = float(target_ppm) + CO2_AIRING_TARGET_DROP
        return min(CO2_TRIGGER_STAGES, key=lambda stage: abs(stage - raw))

    def _arm_rearm_from_session(self, *, now: datetime) -> None:
        """Remember completed band and prepare fast-rebound diagnostics."""
        if self.session_target_ppm is None:
            return
        trigger = self._trigger_for_target(self.session_target_ppm)
        if self.last_completed_at is None or now - self.last_completed_at > CO2_REBOUND_MEMORY:
            self.rebound_count = 0
        self.last_completed_at = now
        self.last_completed_trigger_ppm = trigger
        self.rebound_counted_for_completion = False
        # The just-completed session is the newest proof. If better current
        # conditions justified a lower 850-ppm target even though an older
        # 1400-band lock was active, successfully reaching that target may
        # legitimately re-arm the 1000 band immediately after closing.
        self.rearm_threshold_ppm = trigger
        self.rearm_below_since = None
        self.rearm_candidate_ppm = None

    def _rearm_candidate(self, co2: float | None) -> float | None:
        """Return the lowest lower trigger band proven reachable by live CO₂."""
        if co2 is None or self.rearm_threshold_ppm is None:
            return None

        lower_stages = [
            stage for stage in CO2_TRIGGER_STAGES if stage < self.rearm_threshold_ppm
        ]
        candidates = [
            stage for stage in lower_stages if co2 <= stage - CO2_REARM_MARGIN
        ]
        return min(candidates) if candidates else None

    def _update_rearm(self, *, now: datetime, co2: float | None) -> float | None:
        """Lower a post-airing trigger lock only after a stable 50 ppm deadband.

        Example: a completed 1400 -> 1250 ppm session stays blocked below 1400.
        Only after CO₂ has remained at or below 950 ppm for two minutes is the
        normal 1000-ppm band allowed to trigger again. This prevents a noisy
        999 -> 1000 ppm update immediately after closing from reopening the same
        conversation with the user.
        """
        if self.rearm_threshold_ppm is None:
            self.rearm_below_since = None
            self.rearm_candidate_ppm = None
            return None

        candidate = self._rearm_candidate(co2)
        if candidate is None:
            self.rearm_below_since = None
            self.rearm_candidate_ppm = None
            return None

        if self.rearm_candidate_ppm != candidate:
            self.rearm_candidate_ppm = candidate
            self.rearm_below_since = now

        if self.rearm_below_since is None:
            self.rearm_below_since = now

        elapsed = now - self.rearm_below_since
        remaining = CO2_REARM_STABLE - elapsed
        if remaining.total_seconds() <= 0:
            self.rearm_threshold_ppm = candidate
            self.rearm_below_since = None
            self.rearm_candidate_ppm = None
            return None
        return max(0.0, remaining.total_seconds())

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
            "rearm_threshold_ppm": self.rearm_threshold_ppm,
            "rearm_below_since": (
                self.rearm_below_since.isoformat() if self.rearm_below_since else None
            ),
            "rearm_candidate_ppm": self.rearm_candidate_ppm,
            "measurement_missing_since": (
                self.measurement_missing_since.isoformat()
                if self.measurement_missing_since
                else None
            ),
            "measurement_timed_out_for_open_window": self.measurement_timed_out_for_open_window,
            "measurement_timeout_target_ppm": self.measurement_timeout_target_ppm,
            "last_completed_at": (
                self.last_completed_at.isoformat() if self.last_completed_at else None
            ),
            "last_completed_trigger_ppm": self.last_completed_trigger_ppm,
            "rebound_count": self.rebound_count,
            "rebound_counted_for_completion": self.rebound_counted_for_completion,
            "high_load_until": (
                self.high_load_until.isoformat() if self.high_load_until else None
            ),
            "trend_anchor_ppm": self.trend_anchor_ppm,
            "trend_anchor_at": (self.trend_anchor_at.isoformat() if self.trend_anchor_at else None),
            "trend_ppm_per_min": self.trend_ppm_per_min,
            "trend_positive_intervals": self.trend_positive_intervals,
        }

    def restore(
        self,
        *,
        pending_below_since: datetime | None,
        finish_below_since: datetime | None,
        session_active: bool = False,
        session_target_ppm: float | None = None,
        completed_for_open_window: bool = False,
        rearm_threshold_ppm: float | None = None,
        rearm_below_since: datetime | None = None,
        rearm_candidate_ppm: float | None = None,
        measurement_missing_since: datetime | None = None,
        measurement_timed_out_for_open_window: bool = False,
        measurement_timeout_target_ppm: float | None = None,
        last_completed_at: datetime | None = None,
        last_completed_trigger_ppm: float | None = None,
        rebound_count: int = 0,
        rebound_counted_for_completion: bool = False,
        high_load_until: datetime | None = None,
        trend_anchor_ppm: float | None = None,
        trend_anchor_at: datetime | None = None,
        trend_ppm_per_min: float | None = None,
        trend_positive_intervals: int = 0,
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

        try:
            rearm = (
                float(rearm_threshold_ppm)
                if rearm_threshold_ppm is not None
                else None
            )
        except (TypeError, ValueError):
            rearm = None
        self.rearm_threshold_ppm = (
            min(CO2_TRIGGER_STAGES, key=lambda stage: abs(stage - rearm))
            if rearm is not None
            else None
        )
        self.rearm_below_since = rearm_below_since
        try:
            candidate = (
                float(rearm_candidate_ppm)
                if rearm_candidate_ppm is not None
                else None
            )
        except (TypeError, ValueError):
            candidate = None
        self.rearm_candidate_ppm = (
            min(CO2_TRIGGER_STAGES, key=lambda stage: abs(stage - candidate))
            if candidate is not None
            else None
        )
        self.measurement_missing_since = measurement_missing_since
        self.measurement_timed_out_for_open_window = bool(
            measurement_timed_out_for_open_window
        )
        try:
            timeout_target = (
                float(measurement_timeout_target_ppm)
                if measurement_timeout_target_ppm is not None
                else None
            )
        except (TypeError, ValueError):
            timeout_target = None
        self.measurement_timeout_target_ppm = timeout_target
        self.last_completed_at = last_completed_at
        self.last_completed_trigger_ppm = _float_or_none(last_completed_trigger_ppm)
        try:
            self.rebound_count = max(0, int(rebound_count))
        except (TypeError, ValueError):
            self.rebound_count = 0
        self.rebound_counted_for_completion = bool(rebound_counted_for_completion)
        self.high_load_until = high_load_until
        self.trend_anchor_ppm = _float_or_none(trend_anchor_ppm)
        self.trend_anchor_at = trend_anchor_at
        self.trend_ppm_per_min = _float_or_none(trend_ppm_per_min)
        try:
            self.trend_positive_intervals = max(0, int(trend_positive_intervals))
        except (TypeError, ValueError):
            self.trend_positive_intervals = 0

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
        trend_ppm_per_min, minutes_to_2000 = self._update_trend(now=now, co2=co2)

        def _decision(**kwargs: Any) -> Co2HysteresisDecision:
            return Co2HysteresisDecision(
                trend_ppm_per_min=trend_ppm_per_min,
                minutes_to_2000=minutes_to_2000,
                **kwargs,
            )

        # A completed session arms a band-specific post-airing re-trigger lock.
        # Do this before clearing the open-window session so the information is
        # not lost when the user follows the "finished" recommendation.
        if (
            not window_open
            and
            self.session_active
            and self.session_target_ppm is not None
            and co2 is not None
            and co2 <= self.session_target_ppm
            and self.finish_below_since is not None
            and now - self.finish_below_since >= CO2_AIRING_FINISH_STABLE
        ):
            self._arm_rearm_from_session(now=now)

        # Closing the window ends the explicit open-window session. The rearm
        # threshold intentionally survives; only the short open-window marker is
        # cleared here.
        if not window_open:
            if self.session_active or self.completed_for_open_window:
                self._clear_session()

            rearm_check = self._update_rearm(now=now, co2=co2)
        else:
            # The downward rearm deadband begins only after the user closes the
            # window. This keeps the semantics simple: finish the current airing
            # first, then prove that a lower CO₂ band has genuinely been reached.
            self.rearm_below_since = None
            self.rearm_candidate_ppm = None
            rearm_check = None

        if self.high_load_until is not None and now >= self.high_load_until:
            self.high_load_until = None

        if (
            not window_open
            and co2 is not None
            and self.last_completed_at is not None
            and self.last_completed_trigger_ppm is not None
            and not self.rebound_counted_for_completion
            and co2 >= self.last_completed_trigger_ppm
        ):
            if now - self.last_completed_at <= CO2_FAST_REBOUND_WINDOW:
                self.rebound_count += 1
                if self.rebound_count >= 2:
                    self.high_load_until = now + CO2_HIGH_LOAD_HOLD
            else:
                self.rebound_count = 0
            self.rebound_counted_for_completion = True

        if window_open and self.measurement_timed_out_for_open_window:
            if co2 is None:
                return _decision(
                    measurement_timed_out=True,
                    finish_target_ppm=self.measurement_timeout_target_ppm,
                    rearm_threshold_ppm=self.rearm_threshold_ppm,
                )
            # The sensor recovered while the same window is still open. Resume
            # the remembered session target instead of starting a brand-new
            # conversation. If the target is already met, the normal two-minute
            # stability check below confirms it with the dedicated
            # target-confirming wording.
            recovered_target = (
                self.measurement_timeout_target_ppm or CO2_AIRING_FINISH
            )
            self.measurement_timed_out_for_open_window = False
            self.measurement_timeout_target_ppm = None
            self.completed_for_open_window = False
            self.session_active = True
            self.session_target_ppm = recovered_target
            self.measurement_missing_since = None

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
                if self.measurement_missing_since is None:
                    self.measurement_missing_since = now
                elapsed_missing = now - self.measurement_missing_since
                remaining_missing = CO2_MEASUREMENT_MISSING_TIMEOUT - elapsed_missing
                if remaining_missing.total_seconds() <= 0:
                    self.measurement_timed_out_for_open_window = True
                    self.measurement_timeout_target_ppm = target
                    self._clear_session(keep_completed=True)
                    self.completed_for_open_window = True
                    return _decision(
                        measurement_timed_out=True,
                        finish_target_ppm=target,
                        rearm_threshold_ppm=self.rearm_threshold_ppm,
                    )
                return _decision(
                    airing_active=True,
                    finish_target_ppm=target,
                    near_target_ppm=near_target,
                    rearm_threshold_ppm=self.rearm_threshold_ppm,
                    next_check_seconds=max(0.0, remaining_missing.total_seconds()),
                )

            self.measurement_missing_since = None
            if co2 > target:
                self.finish_below_since = None
                return _decision(
                    airing_active=True,
                    finish_target_ppm=target,
                    near_target_ppm=near_target,
                    rearm_threshold_ppm=self.rearm_threshold_ppm,
                )

            if self.finish_below_since is None:
                self.finish_below_since = now
            elapsed = now - self.finish_below_since
            remaining = CO2_AIRING_FINISH_STABLE - elapsed
            ready = remaining.total_seconds() <= 0
            return _decision(
                airing_active=True,
                finish_ready=ready,
                finish_target_ppm=target,
                near_target_ppm=near_target,
                rearm_threshold_ppm=self.rearm_threshold_ppm,
                next_check_seconds=max(0.0, remaining.total_seconds()) if not ready else None,
            )

        if co2 is None or not is_co2_context(previous_mode, previous_need):
            self.pending_below_since = None
            self.finish_below_since = None
            return _decision(
                rearm_threshold_ppm=self.rearm_threshold_ppm,
                next_check_seconds=rearm_check,
            )

        # Waiting for the user to act on an already-issued CO₂ recommendation.
        if not window_open:
            self.finish_below_since = None
            if co2 >= CO2_RECOMMEND_RELEASE:
                self.pending_below_since = None
                return _decision(
                    rearm_threshold_ppm=self.rearm_threshold_ppm,
                    next_check_seconds=rearm_check,
                )

            if self.pending_below_since is None:
                self.pending_below_since = now
            elapsed = now - self.pending_below_since
            remaining = CO2_RECOMMEND_RELEASE_STABLE - elapsed
            hold = remaining.total_seconds() > 0
            return _decision(
                pending_hold=hold,
                rearm_threshold_ppm=self.rearm_threshold_ppm,
                next_check_seconds=(
                    min(
                        seconds
                        for seconds in (
                            max(0.0, remaining.total_seconds()) if hold else None,
                            rearm_check,
                        )
                        if seconds is not None
                    )
                    if hold or rearm_check is not None
                    else None
                ),
            )

        # An open window alone must never manufacture a CO₂ session. The engine
        # computes the situation-specific target while the window is still
        # closed, and the room coordinator is the single owner that starts the
        # explicit session when the user follows that recommendation. This is
        # important for targets adapted to outdoor conditions and for deliberate
        # ``target=None`` decisions where no reachable explicit CO₂ goal exists.
        return _decision(
            rearm_threshold_ppm=self.rearm_threshold_ppm,
            next_check_seconds=rearm_check,
        )


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


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

        for key in ("nina_caution", "weather_caution", "weather_forecast", "rain"):
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

"""Reason-specific session memory for calm, human-facing ventilation advice.

The pure engine deliberately evaluates current physics.  This module adds the
small amount of history that current values cannot express on their own:

* whether a humidity airing attempt is still making measurable progress,
* whether the same already-treated humidity situation is merely hovering near
  its previous level,
* whether outdoor drying potential has become materially better,
* and whether a short humidity peak is in a normal recovery phase.

The state is intentionally per reason.  It must never suppress CO2, measured
indoor-air pollutants, mould/surface risk or a hard safety instruction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


HUMIDITY_PROGRESS_WINDOW = timedelta(minutes=15)
HUMIDITY_PROGRESS_MIN_DROP = 0.25  # g/m3; practical sensor/UX dead-band
HUMIDITY_MIN_REST = timedelta(hours=1)
HUMIDITY_REARM_STABLE = timedelta(minutes=15)
HUMIDITY_REARM_RH_RISE = 3.0  # percentage points above post-session level
HUMIDITY_OUTDOOR_IMPROVEMENT = 1.0  # g/m3 more drying potential
HUMIDITY_RESOLVED_RH = 57.0
HUMIDITY_PEAK_RISE = 6.0
HUMIDITY_PEAK_WINDOW = timedelta(minutes=15)
HUMIDITY_PEAK_RECOVERY_DROP = 3.0
HUMIDITY_PEAK_RECOVERY_MAX_RH = 65.0


@dataclass(slots=True)
class HumiditySessionDecision:
    """Flags consumed by the room engine/coordinator."""

    session_active: bool = False
    exhausted: bool = False
    disarmed: bool = False
    optional_opportunity: bool = False
    peak_recovery: bool = False
    progress_drop: float | None = None
    next_check_seconds: float | None = None


@dataclass(slots=True)
class HumiditySessionState:
    """Remember one room's humidity attempt and reason-specific re-arm state."""

    session_active: bool = False
    session_started_at: datetime | None = None
    session_start_ah: float | None = None
    session_start_rh: float | None = None
    session_start_temp: float | None = None
    progress_anchor_at: datetime | None = None
    progress_anchor_ah: float | None = None
    best_ah: float | None = None

    disarmed: bool = False
    exhausted: bool = False
    exhausted_at: datetime | None = None
    reference_rh: float | None = None
    reference_ah: float | None = None
    reference_drying_potential: float | None = None

    rearm_rh_since: datetime | None = None
    outdoor_better_since: datetime | None = None
    resolved_since: datetime | None = None

    peak_active: bool = False
    peak_started_at: datetime | None = None
    peak_baseline_rh: float | None = None
    peak_rh: float | None = None
    peak_recovery: bool = False

    # Short live-only sample history for rapid-peak detection.  It is not worth
    # persisting; persistent peak/session flags are stored separately.
    samples: list[tuple[datetime, float, float]] = field(default_factory=list)

    def reset(self) -> None:
        self.session_active = False
        self.session_started_at = None
        self.session_start_ah = None
        self.session_start_rh = None
        self.session_start_temp = None
        self.progress_anchor_at = None
        self.progress_anchor_ah = None
        self.best_ah = None
        self.disarmed = False
        self.exhausted = False
        self.exhausted_at = None
        self.reference_rh = None
        self.reference_ah = None
        self.reference_drying_potential = None
        self.rearm_rh_since = None
        self.outdoor_better_since = None
        self.resolved_since = None
        self.peak_active = False
        self.peak_started_at = None
        self.peak_baseline_rh = None
        self.peak_rh = None
        self.peak_recovery = False
        self.samples.clear()

    def _end_live_session(self) -> None:
        self.session_active = False
        self.session_started_at = None
        self.session_start_ah = None
        self.session_start_rh = None
        self.session_start_temp = None
        self.progress_anchor_at = None
        self.progress_anchor_ah = None
        self.best_ah = None

    def _arm_quiet_state(
        self,
        *,
        now: datetime,
        indoor_rh: float,
        indoor_ah: float,
        drying_potential: float,
        exhausted: bool,
    ) -> None:
        self._end_live_session()
        self.disarmed = True
        self.exhausted = bool(exhausted)
        self.exhausted_at = now
        self.reference_rh = float(indoor_rh)
        self.reference_ah = float(indoor_ah)
        self.reference_drying_potential = float(drying_potential)
        self.rearm_rh_since = None
        self.outdoor_better_since = None
        self.resolved_since = None
        # A peak that has already fallen substantially is now considered a
        # recovery phase; do not manufacture another >60 % session immediately.
        if self.peak_active and self.peak_rh is not None:
            self.peak_recovery = (
                indoor_rh <= self.peak_rh - HUMIDITY_PEAK_RECOVERY_DROP
                and indoor_rh <= HUMIDITY_PEAK_RECOVERY_MAX_RH
            )

    def _clear_quiet_state(self) -> None:
        self.disarmed = False
        self.exhausted = False
        self.exhausted_at = None
        self.reference_rh = None
        self.reference_ah = None
        self.reference_drying_potential = None
        self.rearm_rh_since = None
        self.outdoor_better_since = None
        self.resolved_since = None
        self.peak_recovery = False

    def _clear_peak_state(self) -> None:
        self.peak_active = False
        self.peak_started_at = None
        self.peak_baseline_rh = None
        self.peak_rh = None
        self.peak_recovery = False

    def _observe_peak(self, *, now: datetime, rh: float, ah: float) -> bool:
        cutoff = now - HUMIDITY_PEAK_WINDOW
        self.samples = [sample for sample in self.samples if sample[0] >= cutoff]
        baseline = min((sample[1] for sample in self.samples), default=rh)
        self.samples.append((now, float(rh), float(ah)))

        new_peak = rh >= baseline + HUMIDITY_PEAK_RISE
        if new_peak:
            if not self.peak_active:
                self.peak_started_at = now
                self.peak_baseline_rh = baseline
            self.peak_active = True
            self.peak_rh = max(float(rh), float(self.peak_rh or rh))
            self.peak_recovery = False
            # A genuine rapid event is a new situation and may break the normal
            # humidity quiet state immediately (mould/safety remain separate).
            self._clear_quiet_state()
            return True

        if self.peak_active:
            self.peak_rh = max(float(rh), float(self.peak_rh or rh))
            if (
                self.peak_rh is not None
                and rh <= self.peak_rh - HUMIDITY_PEAK_RECOVERY_DROP
                and rh <= HUMIDITY_PEAK_RECOVERY_MAX_RH
            ):
                self.peak_recovery = True
        return False

    def start_session(
        self,
        *,
        now: datetime,
        indoor_temp: float,
        indoor_rh: float,
        indoor_ah: float,
    ) -> bool:
        if self.session_active or self.disarmed:
            return False
        self.session_active = True
        self.session_started_at = now
        self.session_start_ah = float(indoor_ah)
        self.session_start_rh = float(indoor_rh)
        self.session_start_temp = float(indoor_temp)
        self.progress_anchor_at = now
        self.progress_anchor_ah = float(indoor_ah)
        self.best_ah = float(indoor_ah)
        return True

    def as_dict(self) -> dict[str, Any]:
        def stamp(value: datetime | None) -> str | None:
            return value.isoformat() if value else None

        return {
            "session_active": self.session_active,
            "session_started_at": stamp(self.session_started_at),
            "session_start_ah": self.session_start_ah,
            "session_start_rh": self.session_start_rh,
            "session_start_temp": self.session_start_temp,
            "progress_anchor_at": stamp(self.progress_anchor_at),
            "progress_anchor_ah": self.progress_anchor_ah,
            "best_ah": self.best_ah,
            "disarmed": self.disarmed,
            "exhausted": self.exhausted,
            "exhausted_at": stamp(self.exhausted_at),
            "reference_rh": self.reference_rh,
            "reference_ah": self.reference_ah,
            "reference_drying_potential": self.reference_drying_potential,
            "rearm_rh_since": stamp(self.rearm_rh_since),
            "outdoor_better_since": stamp(self.outdoor_better_since),
            "resolved_since": stamp(self.resolved_since),
            "peak_active": self.peak_active,
            "peak_started_at": stamp(self.peak_started_at),
            "peak_baseline_rh": self.peak_baseline_rh,
            "peak_rh": self.peak_rh,
            "peak_recovery": self.peak_recovery,
        }

    def restore(self, data: dict[str, Any], *, parse_dt) -> None:
        """Restore compact persistent state; ``parse_dt`` is HA-time aware."""
        self.session_active = bool(data.get("session_active"))
        self.session_started_at = parse_dt(data.get("session_started_at"))
        self.session_start_ah = _float_or_none(data.get("session_start_ah"))
        self.session_start_rh = _float_or_none(data.get("session_start_rh"))
        self.session_start_temp = _float_or_none(data.get("session_start_temp"))
        self.progress_anchor_at = parse_dt(data.get("progress_anchor_at"))
        self.progress_anchor_ah = _float_or_none(data.get("progress_anchor_ah"))
        self.best_ah = _float_or_none(data.get("best_ah"))
        self.disarmed = bool(data.get("disarmed"))
        self.exhausted = bool(data.get("exhausted"))
        self.exhausted_at = parse_dt(data.get("exhausted_at"))
        self.reference_rh = _float_or_none(data.get("reference_rh"))
        self.reference_ah = _float_or_none(data.get("reference_ah"))
        self.reference_drying_potential = _float_or_none(
            data.get("reference_drying_potential")
        )
        self.rearm_rh_since = parse_dt(data.get("rearm_rh_since"))
        self.outdoor_better_since = parse_dt(data.get("outdoor_better_since"))
        self.resolved_since = parse_dt(data.get("resolved_since"))
        self.peak_active = bool(data.get("peak_active"))
        self.peak_started_at = parse_dt(data.get("peak_started_at"))
        self.peak_baseline_rh = _float_or_none(data.get("peak_baseline_rh"))
        self.peak_rh = _float_or_none(data.get("peak_rh"))
        self.peak_recovery = bool(data.get("peak_recovery"))
        self.samples.clear()

        # A partially restored live session without its progress anchors is not
        # trustworthy enough to keep a window open indefinitely.
        if self.session_active and (
            self.progress_anchor_at is None or self.progress_anchor_ah is None
        ):
            self._end_live_session()

    def evaluate(
        self,
        *,
        now: datetime,
        indoor_temp: float,
        indoor_rh: float,
        indoor_ah: float,
        outdoor_ah: float,
        window_open: bool,
        humidity_actionable: bool,
        humidity_still_needed: bool,
        safety_lock: bool,
        mold_risk: bool,
    ) -> HumiditySessionDecision:
        """Advance humidity session/re-arm memory and return engine flags."""
        drying_potential = float(indoor_ah) - float(outdoor_ah)
        new_peak = self._observe_peak(now=now, rh=indoor_rh, ah=indoor_ah)

        if mold_risk:
            # Surface/mould protection is a separate, stronger reason.  Do not
            # let humidity comfort memory suppress it.
            self._clear_quiet_state()

        if safety_lock:
            # Safety owns the window. Preserve the last quiet reference, but a
            # live humidity session cannot continue through the hard lock.
            self._end_live_session()
            return self._decision(now=now)

        if (
            window_open
            and humidity_actionable
            and not self.session_active
            and not self.disarmed
        ):
            self.start_session(
                now=now,
                indoor_temp=indoor_temp,
                indoor_rh=indoor_rh,
                indoor_ah=indoor_ah,
            )

        if self.session_active:
            if not window_open:
                # The user deliberately ended this comfort airing. Treat that
                # as a completed attempt, otherwise the identical sensor sample
                # would immediately produce ``open_now`` again after closing.
                # This is reason-specific quiet memory only: CO2, pollutants,
                # mould and safety remain fully able to react.
                self._arm_quiet_state(
                    now=now,
                    indoor_rh=indoor_rh,
                    indoor_ah=indoor_ah,
                    drying_potential=drying_potential,
                    exhausted=False,
                )
            elif not humidity_still_needed:
                # A real successful reduction is still a completed attempt. Keep
                # the achieved level as the new reference so 59↔61 % does not
                # immediately start the same conversation again.
                self._arm_quiet_state(
                    now=now,
                    indoor_rh=indoor_rh,
                    indoor_ah=indoor_ah,
                    drying_potential=drying_potential,
                    exhausted=False,
                )
            else:
                self.best_ah = min(float(self.best_ah or indoor_ah), float(indoor_ah))
                anchor_at = self.progress_anchor_at or now
                anchor_ah = float(self.progress_anchor_ah or indoor_ah)
                elapsed = now - anchor_at
                if elapsed >= HUMIDITY_PROGRESS_WINDOW:
                    drop = anchor_ah - float(self.best_ah)
                    if drop < HUMIDITY_PROGRESS_MIN_DROP:
                        self._arm_quiet_state(
                            now=now,
                            indoor_rh=indoor_rh,
                            indoor_ah=indoor_ah,
                            drying_potential=drying_potential,
                            exhausted=True,
                        )
                    else:
                        self.progress_anchor_at = now
                        self.progress_anchor_ah = float(self.best_ah)
                        self.best_ah = float(indoor_ah)

        # A short peak can also recover without an explicit window session
        # (for example after showering ends or an extractor fan does the work).
        # Once the value has clearly fallen from the peak, treat that recovered
        # level as a quiet reference as well. Otherwise ``peak_recovery`` could
        # remain true indefinitely and suppress a later gradual +3 %-point
        # deterioration forever. The ordinary re-arm logic below then owns the
        # same stable-worsening rule as after a completed airing session.
        if (
            self.peak_active
            and self.peak_recovery
            and not self.session_active
            and not self.disarmed
            and not mold_risk
        ):
            self._arm_quiet_state(
                now=now,
                indoor_rh=indoor_rh,
                indoor_ah=indoor_ah,
                drying_potential=drying_potential,
                exhausted=False,
            )

        optional_opportunity = False
        next_checks: list[float] = []
        if self.disarmed and not mold_risk:
            quiet_since = self.exhausted_at or now
            rest_done = now - quiet_since >= HUMIDITY_MIN_REST
            if not rest_done:
                next_checks.append(
                    max(0.0, (HUMIDITY_MIN_REST - (now - quiet_since)).total_seconds())
                )

            # A rapid new peak is a genuinely new event and may re-arm before the
            # ordinary one-hour comfort rest.
            if new_peak:
                self._clear_quiet_state()
            else:
                reference_rh = float(self.reference_rh if self.reference_rh is not None else indoor_rh)
                reference_potential = float(
                    self.reference_drying_potential
                    if self.reference_drying_potential is not None
                    else drying_potential
                )

                if indoor_rh <= min(HUMIDITY_RESOLVED_RH, reference_rh - HUMIDITY_REARM_RH_RISE):
                    if self.resolved_since is None:
                        self.resolved_since = now
                    remaining = HUMIDITY_REARM_STABLE - (now - self.resolved_since)
                    if remaining.total_seconds() <= 0:
                        self._clear_quiet_state()
                        self._clear_peak_state()
                    else:
                        next_checks.append(max(0.0, remaining.total_seconds()))
                else:
                    self.resolved_since = None

                if self.disarmed:
                    if indoor_rh >= reference_rh + HUMIDITY_REARM_RH_RISE:
                        if self.rearm_rh_since is None:
                            self.rearm_rh_since = now
                        remaining = HUMIDITY_REARM_STABLE - (now - self.rearm_rh_since)
                        if rest_done and remaining.total_seconds() <= 0:
                            self._clear_quiet_state()
                            self._clear_peak_state()
                        elif remaining.total_seconds() > 0:
                            next_checks.append(remaining.total_seconds())
                        # If the +3 %-point condition is already stable while
                        # the minimum one-hour rest is still running, keep the
                        # rest timer queued above. Never replace it with 0 s.
                    else:
                        self.rearm_rh_since = None

                if self.disarmed:
                    improved = (
                        drying_potential
                        >= reference_potential + HUMIDITY_OUTDOOR_IMPROVEMENT
                    )
                    if improved:
                        if self.outdoor_better_since is None:
                            self.outdoor_better_since = now
                        remaining = HUMIDITY_REARM_STABLE - (now - self.outdoor_better_since)
                        if rest_done and remaining.total_seconds() <= 0:
                            optional_opportunity = True
                        elif remaining.total_seconds() > 0:
                            next_checks.append(remaining.total_seconds())
                        # Same rule for better outdoor conditions: once the
                        # 15-minute stability window is complete, the remaining
                        # minimum-rest timer must stay alive instead of becoming
                        # an ignored zero-second check.
                    else:
                        self.outdoor_better_since = None

        return HumiditySessionDecision(
            session_active=self.session_active,
            exhausted=self.exhausted,
            disarmed=self.disarmed,
            optional_opportunity=optional_opportunity,
            peak_recovery=self.peak_recovery,
            progress_drop=(
                float(self.progress_anchor_ah) - float(self.best_ah)
                if self.session_active
                and self.progress_anchor_ah is not None
                and self.best_ah is not None
                else None
            ),
            next_check_seconds=min(next_checks) if next_checks else self._session_next_check(now),
        )

    def _session_next_check(self, now: datetime) -> float | None:
        if not self.session_active or self.progress_anchor_at is None:
            return None
        remaining = HUMIDITY_PROGRESS_WINDOW - (now - self.progress_anchor_at)
        return max(0.0, remaining.total_seconds())

    def _decision(self, *, now: datetime) -> HumiditySessionDecision:
        return HumiditySessionDecision(
            session_active=self.session_active,
            exhausted=self.exhausted,
            disarmed=self.disarmed,
            peak_recovery=self.peak_recovery,
            next_check_seconds=self._session_next_check(now),
        )


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None

INDOOR_AIR_QUIET = timedelta(minutes=10)


@dataclass(slots=True)
class IndoorAirSessionDecision:
    """Small per-reason aftercare state for measured indoor pollutants."""

    session_active: bool = False
    disarmed: bool = False
    next_check_seconds: float | None = None


@dataclass(slots=True)
class IndoorAirSessionState:
    """Keep a short calm phase after a successful pollutant airing.

    This state only suppresses the mild ``moderate`` class. A renewed ``poor``
    or ``very_poor`` reading, or a moderate reading with a clearly rising/
    unusual trend, immediately re-arms the reason.
    """

    session_active: bool = False
    quiet_until: datetime | None = None
    disarmed: bool = False

    def reset(self) -> None:
        self.session_active = False
        self.quiet_until = None
        self.disarmed = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_active": self.session_active,
            "quiet_until": self.quiet_until.isoformat() if self.quiet_until else None,
            "disarmed": self.disarmed,
        }

    def restore(self, data: dict[str, Any], *, parse_dt) -> None:
        self.session_active = bool(data.get("session_active"))
        self.quiet_until = parse_dt(data.get("quiet_until"))
        self.disarmed = bool(data.get("disarmed"))

    def evaluate(
        self,
        *,
        now: datetime,
        window_open: bool,
        quality: str,
        trend: str = "unknown",
        unusual: bool = False,
        safety_lock: bool = False,
    ) -> IndoorAirSessionDecision:
        quality = str(quality or "unknown")
        urgent = quality in {"poor", "very_poor"}
        mild = quality == "moderate"
        renewed_rise = mild and (bool(unusual) or str(trend) == "rising")

        if urgent or renewed_rise:
            self.quiet_until = None

        if safety_lock:
            self.session_active = False
        elif window_open and quality in {"moderate", "poor", "very_poor"}:
            self.session_active = True

        if self.session_active and (
            not window_open or quality in {"good", "very_good", "unknown"}
        ):
            self.session_active = False
            self.quiet_until = now + INDOOR_AIR_QUIET

        disarmed = bool(
            mild
            and self.quiet_until is not None
            and now < self.quiet_until
            and not renewed_rise
        )
        if self.quiet_until is not None and now >= self.quiet_until:
            self.quiet_until = None
            disarmed = False
        self.disarmed = disarmed

        remaining = (
            max(0.0, (self.quiet_until - now).total_seconds())
            if self.quiet_until is not None
            else None
        )
        return IndoorAirSessionDecision(
            session_active=self.session_active,
            disarmed=disarmed,
            next_check_seconds=remaining,
        )

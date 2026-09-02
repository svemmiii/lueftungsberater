"""Shared event-driven room coordinator for Lüftungsberater."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_call_later, async_track_state_change_event, async_track_time_change, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .airing import get_tracker, tracker_signal
from .co2 import co2_tracker_signal
from .co2_hysteresis import (
    Co2HysteresisState,
    Co2MinimumAiringState,
)
from .const import (
    CONF_CO2,
    CONF_NIGHT_START_HOUR,
    CONF_NIGHT_START_TIME,
    CONF_NIGHT_END_TIME,
    CONF_SURFACE_TEMP,
    CONF_WINDOWS,
    DATA_COORDINATORS,
    DECISION_MEMORY_TTL,
    DEFAULT_NIGHT_START_HOUR,
    DEFAULT_NIGHT_END_TIME,
    DOMAIN,
    MOLD_SAMPLE_INTERVAL,
    STORAGE_VERSION,
)
from .notifications import (
    async_handle_room_notification,
    clear_assistant_notification_state,
    clear_room_notification_state,
)
from .outside import async_get_or_create_outside_coordinator, get_outside_coordinator
from .night import NIGHT_MAX_TEMP_DELTA, NightAdvice, display_interval, stabilize_night_advice
from .runtime import RoomSnapshot, build_room_snapshot, room_co2_window_values, room_source_entities

_LOGGER = logging.getLogger(__name__)

_CO2_MINIMUM_GREEN_START_MODES = {
    "co2_kritisch",
    "co2_lueften",
    "co2_lueften_mit_nachteil",
}
_CO2_MINIMUM_CAUTION_START_MODES = {
    "co2_kritisch_vorsicht",
    "co2_abwaegung",
}


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed


def _clock_from_value(value: Any, fallback: str) -> tuple[int, int]:
    if isinstance(value, str):
        parts = value.split(":")
        try:
            return max(0, min(23, int(parts[0]))), max(0, min(59, int(parts[1])))
        except (ValueError, IndexError):
            pass
    try:
        hour, minute = str(fallback).split(":", 1)
        return max(0, min(23, int(hour))), max(0, min(59, int(minute)))
    except (TypeError, ValueError):
        return 0, 0


def _night_clock(subentry: ConfigSubentry) -> tuple[int, int]:
    raw = subentry.data.get(CONF_NIGHT_START_TIME)
    if raw is not None:
        return _clock_from_value(raw, f"{DEFAULT_NIGHT_START_HOUR:02d}:00")
    try:
        hour = int(subentry.data.get(CONF_NIGHT_START_HOUR, DEFAULT_NIGHT_START_HOUR))
    except (TypeError, ValueError):
        hour = DEFAULT_NIGHT_START_HOUR
    return max(0, min(23, hour)), 0


def _night_end_clock(subentry: ConfigSubentry) -> tuple[int, int]:
    return _clock_from_value(
        subentry.data.get(CONF_NIGHT_END_TIME),
        DEFAULT_NIGHT_END_TIME,
    )


class LueftungsberaterRoomCoordinator(DataUpdateCoordinator[RoomSnapshot]):
    """Compute one shared room snapshot whenever one of its inputs changes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{subentry.subentry_id}",
            update_interval=None,
            always_update=False,
        )
        self.entry = entry
        self.subentry = subentry
        self._unsubs: list[Callable[[], None]] = []
        self._started = False
        self._previous_mode: str | None = None
        self._previous_decision_need: str | None = None
        self._previous_mode_at: datetime | None = None
        self._co2_hysteresis = Co2HysteresisState()
        self._co2_minimum_airing = Co2MinimumAiringState()
        self._co2_hysteresis_unsub: Callable[[], None] | None = None
        self._night_memory: NightAdvice | None = None
        self._night_memory_start: datetime | None = None
        self._night_memory_end: datetime | None = None
        self._memory_store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.decision.{entry.entry_id}.{subentry.subentry_id}",
        )

    async def _restore_memory(self) -> None:
        stored = await self._memory_store.async_load() or {}
        mode = stored.get("mode")
        need = stored.get("decision_need")
        if not isinstance(need, str) or not need:
            # v0.9.0 pre-release builds stored the UI-oriented primary_need
            # here. Read it once as a migration fallback, then persist the
            # decision-oriented value on the next save.
            need = stored.get("primary_need")
        stamp = _parse_dt(stored.get("updated_at"))
        now_utc = dt_util.utcnow()
        if isinstance(mode, str) and mode and stamp is not None and now_utc - stamp <= DECISION_MEMORY_TTL:
            self._previous_mode = mode
            self._previous_decision_need = need if isinstance(need, str) and need else None
            self._previous_mode_at = stamp

        co2_memory = stored.get("co2_hysteresis")
        if isinstance(co2_memory, dict):
            pending = _parse_dt(co2_memory.get("pending_below_since"))
            finish = _parse_dt(co2_memory.get("finish_below_since"))
            rearm_below = _parse_dt(co2_memory.get("rearm_below_since"))
            # These timers are only a few minutes long. Reuse them only while
            # the surrounding decision memory is still fresh; evaluate() will
            # immediately reset them if the live CO2 context no longer matches.
            memory_fresh = (
                stamp is not None and now_utc - stamp <= DECISION_MEMORY_TTL
            )
            self._co2_hysteresis.restore(
                pending_below_since=pending if memory_fresh else None,
                finish_below_since=finish if memory_fresh else None,
                session_active=(
                    bool(co2_memory.get("session_active")) if memory_fresh else False
                ),
                session_target_ppm=(
                    co2_memory.get("session_target_ppm") if memory_fresh else None
                ),
                completed_for_open_window=(
                    bool(co2_memory.get("completed_for_open_window"))
                    if memory_fresh
                    else False
                ),
                # The post-airing re-trigger band is not a short timer. Keep it
                # across restarts until live CO₂ has genuinely proven a lower
                # band via the deadband below. The two-minute candidate timer is
                # only resumed while the surrounding memory is fresh.
                rearm_threshold_ppm=co2_memory.get("rearm_threshold_ppm"),
                rearm_below_since=rearm_below if memory_fresh else None,
                rearm_candidate_ppm=(
                    co2_memory.get("rearm_candidate_ppm") if memory_fresh else None
                ),
            )

        minimum_memory = stored.get("co2_minimum_airing")
        if isinstance(minimum_memory, dict):
            started_at = _parse_dt(minimum_memory.get("started_at"))
            baseline_context = minimum_memory.get("baseline_context")
            if stamp is not None and now_utc - stamp <= DECISION_MEMORY_TTL:
                self._co2_minimum_airing.restore(
                    started_at=started_at,
                    cautious=bool(minimum_memory.get("cautious")),
                    baseline_context=(
                        baseline_context if isinstance(baseline_context, dict) else {}
                    ),
                    completed_for_open_window=bool(
                        minimum_memory.get("completed_for_open_window")
                    ),
                )

        night = stored.get("night")
        if isinstance(night, dict):
            start = _parse_dt(night.get("interval_start"))
            end = _parse_dt(night.get("interval_end"))
            status = night.get("status")
            reason_key = night.get("reason_key")
            reason_args = night.get("reason_args")
            now_local = dt_util.now()
            if (
                start is not None
                and end is not None
                and start <= now_local < end
                and isinstance(status, str)
                and status in {"now", "later", "conditional", "blocked"}
                and isinstance(reason_key, str)
                and isinstance(reason_args, dict)
            ):
                self._night_memory = NightAdvice(
                    status=status,
                    reason_key=reason_key,
                    reason_args=dict(reason_args),
                )
                self._night_memory_start = start
                self._night_memory_end = end

    def _night_memory_payload(self) -> dict[str, Any] | None:
        if (
            self._night_memory is None
            or self._night_memory_start is None
            or self._night_memory_end is None
        ):
            return None
        return {
            "interval_start": self._night_memory_start.isoformat(),
            "interval_end": self._night_memory_end.isoformat(),
            "status": self._night_memory.status,
            "reason_key": self._night_memory.reason_key,
            "reason_args": dict(self._night_memory.reason_args),
        }

    def _memory_payload(self) -> dict[str, Any]:
        return {
            "mode": self._previous_mode,
            "decision_need": self._previous_decision_need,
            "updated_at": self._previous_mode_at.isoformat() if self._previous_mode_at else None,
            "co2_hysteresis": self._co2_hysteresis.as_dict(),
            "co2_minimum_airing": self._co2_minimum_airing.as_dict(),
            "night": self._night_memory_payload(),
        }

    def _queue_memory_save(self) -> None:
        self._memory_store.async_delay_save(self._memory_payload, 5)

    def _clear_night_memory(self) -> None:
        if self._night_memory is None and self._night_memory_end is None:
            return
        self._night_memory = None
        self._night_memory_start = None
        self._night_memory_end = None
        self._queue_memory_save()

    def _night_interval(self, now: datetime) -> tuple[datetime, datetime] | None:
        start_hour, start_minute = _night_clock(self.subentry)
        end_hour, end_minute = _night_end_clock(self.subentry)
        return display_interval(
            now,
            start_hour * 60 + start_minute,
            end_hour * 60 + end_minute,
        )

    def _remember_night_advice(
        self,
        advice: NightAdvice,
        interval: tuple[datetime, datetime],
    ) -> None:
        start, end = interval
        if advice.status == "unavailable" or advice.safety_block:
            return
        if (
            self._night_memory is not None
            and self._night_memory_start == start
            and self._night_memory_end == end
            and self._night_memory.status == advice.status
            and self._night_memory.reason_key == advice.reason_key
            and self._night_memory.reason_args == advice.reason_args
        ):
            return
        self._night_memory = NightAdvice(
            advice.status, advice.reason_key, dict(advice.reason_args)
        )
        self._night_memory_start = start
        self._night_memory_end = end
        self._queue_memory_save()

    def _apply_night_memory(self, snapshot: RoomSnapshot) -> RoomSnapshot:
        """Keep the last trustworthy night plan stable near the configured end."""
        now = dt_util.now()
        interval = self._night_interval(now)
        if interval is None:
            self._clear_night_memory()
            return snapshot

        start, end = interval
        if self._night_memory_end is not None and self._night_memory_end != end:
            self._clear_night_memory()

        values = snapshot.values
        raw = NightAdvice(
            status=str(values.get("night_ventilation_status") or "unavailable"),
            reason_key=values.get("night_ventilation_key"),
            reason_args=dict(values.get("night_ventilation_args") or {}),
            safety_block=bool(values.get("_night_ventilation_safety_block")),
        )

        # If the actual reason for a long night opening is gone, do not preserve
        # an old plan merely for visual stability. CO2 alone intentionally does
        # not create the all-night hint, matching night.py.
        ti = values.get("temperature_inside")
        hi = values.get("humidity_inside")
        target = values.get("target_temperature")
        ta = values.get("temperature_outside")
        planning_need = (
            ti is not None
            and hi is not None
            and target is not None
            and (float(ti) > float(target) + 0.5 or float(hi) >= 60.0)
        )
        current_delta_ok = (
            ti is None
            or ta is None
            or abs(float(ta) - float(ti)) <= NIGHT_MAX_TEMP_DELTA
        )
        if not planning_need or not current_delta_ok:
            self._clear_night_memory()
            return snapshot

        memory_valid = (
            self._night_memory is not None
            and self._night_memory_start == start
            and self._night_memory_end == end
        )
        previous = self._night_memory if memory_valid else None
        chosen, remembered = stabilize_night_advice(
            now=now,
            interval_end=end,
            raw=raw,
            previous=previous,
            planning_need=planning_need,
            current_delta_ok=current_delta_ok,
        )
        if remembered is None:
            if memory_valid:
                self._clear_night_memory()
        elif (
            not memory_valid
            or remembered.status != self._night_memory.status
            or remembered.reason_key != self._night_memory.reason_key
            or remembered.reason_args != self._night_memory.reason_args
        ):
            self._remember_night_advice(remembered, interval)

        values["night_ventilation_status"] = chosen.status
        values["night_ventilation_key"] = chosen.reason_key
        values["night_ventilation_args"] = dict(chosen.reason_args)
        return snapshot

    def _remember_snapshot(self, snapshot: RoomSnapshot) -> None:
        if snapshot.result is None:
            return
        mode = snapshot.result.mode
        need = snapshot.result.decision_need
        if mode == self._previous_mode and need == self._previous_decision_need:
            return
        self._previous_mode = mode
        self._previous_decision_need = need
        self._previous_mode_at = dt_util.utcnow()
        self._queue_memory_save()

    def _start_co2_minimum_airing_if_needed(
        self, snapshot: RoomSnapshot, now_utc: datetime
    ) -> bool:
        """Start the five-minute hold only after a real CO₂ airing decision."""
        if self._co2_minimum_airing.started_at is not None:
            return False
        if self._co2_minimum_airing.completed_for_open_window:
            return False
        if self._co2_hysteresis.completed_for_open_window:
            return False
        if snapshot.result is None or not bool(snapshot.values.get("window_open")):
            return False
        if snapshot.result.safety_lock:
            return False

        source = snapshot
        previous = self.data
        # When the window has just been opened, the decision immediately before
        # that action is the cleanest proof that the user followed the advisor.
        if (
            previous is not None
            and previous.result is not None
            and not bool(previous.values.get("window_open"))
        ):
            source = previous

        result = source.result
        if (
            result is None
            or result.co2_session_need is None
            or result.co2_session_target is None
        ):
            # ``None`` is an intentional engine decision: there is no explicit
            # reachable CO₂ finish target for this opening opportunity. Never
            # recreate a generic 850/1250/1850 ppm target here.
            return False

        mode = result.mode
        cautious = mode in _CO2_MINIMUM_CAUTION_START_MODES
        eligible = (
            mode in _CO2_MINIMUM_GREEN_START_MODES
            or mode in _CO2_MINIMUM_CAUTION_START_MODES
            # A different indoor reason may be the visible green reason while
            # the independently evaluated CO₂ need benefits from the same air
            # exchange. The engine only exposes a CO₂ session target when that
            # CO₂ candidate itself is actionable.
            or (result.color == "green" and result.co2_session_target is not None)
            # If the window was already open when CO₂ became the new reason,
            # the normal engine rewrites a green mode to weiter_lueften.
            or (mode == "weiter_lueften" and source is snapshot)
        )
        if not eligible:
            return False

        baseline = source.values.get("_co2_outdoor_context")
        if not isinstance(baseline, dict):
            baseline = snapshot.values.get("_co2_outdoor_context")
        if not isinstance(baseline, dict):
            baseline = {}

        # The five-minute hold and the longer CO₂ finish hysteresis belong to
        # the same user action.  Start an explicit session now so later mode
        # changes (for example 1400 -> 1399 ppm) cannot forget the CO₂ goal.
        target_ppm = result.co2_session_target
        self._co2_hysteresis.start_airing_session(target_ppm=target_ppm)

        tracker = get_tracker(self.hass, self.entry, self.subentry)
        started_at = (
            tracker.open_since
            if tracker is not None and tracker.open_since is not None
            else now_utc
        )
        return self._co2_minimum_airing.start(
            started_at=started_at,
            cautious=cautious,
            baseline_context=baseline,
        )

    def _schedule_co2_hysteresis_check(self, seconds: float | None) -> None:
        """Schedule the exact point where a stable CO₂ threshold can release."""
        if self._co2_hysteresis_unsub is not None:
            self._co2_hysteresis_unsub()
            self._co2_hysteresis_unsub = None
        if seconds is None or seconds <= 0:
            return

        @callback
        def _refresh(_now) -> None:
            self._co2_hysteresis_unsub = None
            self._handle_tracker_change()

        self._co2_hysteresis_unsub = async_call_later(
            self.hass,
            seconds + 0.05,
            _refresh,
        )

    def _build_snapshot(self) -> RoomSnapshot:
        outside_coordinator = get_outside_coordinator(self.hass, self.entry)
        weather = outside_coordinator.data.weather if outside_coordinator is not None and outside_coordinator.data is not None else None
        warnings = outside_coordinator.data.warnings if outside_coordinator is not None and outside_coordinator.data is not None else None
        previous_mode = (
            self.data.result.mode
            if self.data is not None and self.data.result is not None
            else self._previous_mode
        )
        previous_need = (
            self.data.result.decision_need
            if self.data is not None and self.data.result is not None
            else self._previous_decision_need
        )
        now_utc = dt_util.utcnow()
        co2, window_open = room_co2_window_values(self.hass, self.entry, self.subentry)

        co2_before = self._co2_hysteresis.as_dict()
        co2_hysteresis = self._co2_hysteresis.evaluate(
            now=now_utc,
            co2=co2,
            window_open=window_open,
            previous_mode=previous_mode,
            previous_need=previous_need,
        )

        def _snapshot_for_co2_state() -> RoomSnapshot:
            return build_room_snapshot(
                self.hass,
                self.entry,
                self.subentry,
                previous_mode=previous_mode,
                previous_need=previous_need,
                co2_pending_hold=co2_hysteresis.pending_hold,
                co2_airing_active=co2_hysteresis.airing_active,
                co2_finish_ready=co2_hysteresis.finish_ready,
                co2_finish_target=co2_hysteresis.finish_target_ppm,
                co2_near_target=co2_hysteresis.near_target_ppm,
                co2_rearm_threshold=co2_hysteresis.rearm_threshold_ppm,
                weather=weather,
                warnings=warnings,
            )

        # First calculate the untouched normal decision. The minimum-airing
        # layer may then preserve an already accepted CO₂ session, but it never
        # decides whether the user should have started airing in the first place.
        base_snapshot = _snapshot_for_co2_state()

        minimum_before = self._co2_minimum_airing.as_dict()
        minimum = self._co2_minimum_airing.evaluate(
            now=now_utc,
            window_open=window_open,
            current_context=(
                base_snapshot.values.get("_co2_outdoor_context")
                if isinstance(base_snapshot.values.get("_co2_outdoor_context"), dict)
                else None
            ),
            safety_lock=bool(
                base_snapshot.result is not None and base_snapshot.result.safety_lock
            ),
        )

        # A hard lock or a genuinely new outdoor deterioration is allowed to
        # cancel the user session immediately. Mark it completed for the still
        # open window so the previous CO₂ mode cannot auto-restart it a moment
        # later. Closing the window clears that marker.
        abort_session = bool(
            base_snapshot.result is not None and base_snapshot.result.safety_lock
        ) or minimum.aborted_for_outdoor_worsening
        if abort_session and self._co2_hysteresis.session_active:
            self._co2_hysteresis.end_airing_session(keep_completed=True)
            co2_hysteresis = self._co2_hysteresis.evaluate(
                now=now_utc,
                co2=co2,
                window_open=window_open,
                previous_mode=previous_mode,
                previous_need=previous_need,
            )
            base_snapshot = _snapshot_for_co2_state()

        if not minimum.active and self._start_co2_minimum_airing_if_needed(
            base_snapshot, now_utc
        ):
            # Starting the five-minute hold also starts the explicit CO₂ session.
            # Re-evaluate once so the very same snapshot already carries the
            # correct dynamic target and cannot lose its CO₂ context.
            co2_hysteresis = self._co2_hysteresis.evaluate(
                now=now_utc,
                co2=co2,
                window_open=window_open,
                previous_mode=previous_mode,
                previous_need=previous_need,
            )
            base_snapshot = _snapshot_for_co2_state()
            minimum = self._co2_minimum_airing.evaluate(
                now=now_utc,
                window_open=window_open,
                current_context=(
                    base_snapshot.values.get("_co2_outdoor_context")
                    if isinstance(base_snapshot.values.get("_co2_outdoor_context"), dict)
                    else None
                ),
                safety_lock=bool(
                    base_snapshot.result is not None and base_snapshot.result.safety_lock
                ),
            )

        hysteresis_changed = self._co2_hysteresis.as_dict() != co2_before
        minimum_changed = self._co2_minimum_airing.as_dict() != minimum_before
        if hysteresis_changed or minimum_changed:
            self._queue_memory_save()

        checks = [
            seconds
            for seconds in (
                co2_hysteresis.next_check_seconds,
                minimum.next_check_seconds,
            )
            if seconds is not None and seconds > 0
        ]
        self._schedule_co2_hysteresis_check(min(checks) if checks else None)

        if minimum.active:
            snapshot = build_room_snapshot(
                self.hass,
                self.entry,
                self.subentry,
                previous_mode=previous_mode,
                previous_need=previous_need,
                co2_pending_hold=co2_hysteresis.pending_hold,
                co2_airing_active=co2_hysteresis.airing_active,
                co2_finish_ready=co2_hysteresis.finish_ready,
                co2_finish_target=co2_hysteresis.finish_target_ppm,
                co2_near_target=co2_hysteresis.near_target_ppm,
                co2_rearm_threshold=co2_hysteresis.rearm_threshold_ppm,
                co2_minimum_airing_active=True,
                co2_minimum_airing_cautious=minimum.cautious,
                weather=weather,
                warnings=warnings,
            )
        else:
            snapshot = base_snapshot
        return self._apply_night_memory(snapshot)

    async def _async_update_data(self) -> RoomSnapshot:
        snapshot = self._build_snapshot()
        self._remember_snapshot(snapshot)
        await async_handle_room_notification(self.hass, self.entry, self.subentry, snapshot)
        return snapshot

    async def async_start(self) -> None:
        if self._started:
            return
        self._started = True
        await self._restore_memory()
        outside = await async_get_or_create_outside_coordinator(self.hass, self.entry)
        await self.async_config_entry_first_refresh()

        entities = room_source_entities(self.hass, self.entry, self.subentry)
        if entities:
            self._unsubs.append(async_track_state_change_event(self.hass, entities, self._handle_source_change))

        self._unsubs.append(outside.async_add_listener(self._handle_tracker_change))

        if self.subentry.data.get(CONF_WINDOWS):
            self._unsubs.append(
                async_dispatcher_connect(
                    self.hass,
                    tracker_signal(self.entry.entry_id, self.subentry.subentry_id),
                    self._handle_tracker_change,
                )
            )

        if self.subentry.data.get(CONF_CO2):
            self._unsubs.append(
                async_dispatcher_connect(
                    self.hass,
                    co2_tracker_signal(self.entry.entry_id, self.subentry.subentry_id),
                    self._handle_tracker_change,
                )
            )

        if self.subentry.data.get(CONF_SURFACE_TEMP):
            self._unsubs.append(
                async_track_time_interval(
                    self.hass,
                    lambda _now: self._handle_tracker_change(),
                    MOLD_SAMPLE_INTERVAL,
                )
            )

        # Re-evaluate exactly when this room's night hint becomes visible. The
        # shared outside coordinator handles the actual forecast refreshes.
        night_hour, night_minute = _night_clock(self.subentry)
        self._unsubs.append(
            async_track_time_change(
                self.hass,
                self._handle_night_start,
                hour=night_hour,
                minute=night_minute,
                second=0,
            )
        )
        night_end_hour, night_end_minute = _night_end_clock(self.subentry)
        self._unsubs.append(
            async_track_time_change(
                self.hass,
                self._handle_night_end,
                hour=night_end_hour,
                minute=night_end_minute,
                second=0,
            )
        )

    def _publish_snapshot(self, snapshot: RoomSnapshot) -> None:
        self._remember_snapshot(snapshot)
        self.async_set_updated_data(snapshot)
        self.hass.async_create_task(
            async_handle_room_notification(self.hass, self.entry, self.subentry, snapshot),
            f"Lüftungsberater notification check {self.subentry.subentry_id}",
        )

    @callback
    def _handle_night_start(self, _now: datetime) -> None:
        """Refresh the shared forecast exactly when this room starts showing it."""
        outside = get_outside_coordinator(self.hass, self.entry)
        if outside is None:
            self._handle_tracker_change()
            return
        self.hass.async_create_task(
            outside.async_request_refresh(),
            f"Lüftungsberater night forecast {self.subentry.subentry_id}",
        )

    @callback
    def _handle_night_end(self, _now: datetime) -> None:
        """Re-evaluate exactly when this room's night display window ends."""
        self._handle_tracker_change()

    @callback
    def _handle_source_change(self, _event: Event) -> None:
        self._publish_snapshot(self._build_snapshot())

    @callback
    def _handle_tracker_change(self) -> None:
        self._publish_snapshot(self._build_snapshot())

    async def async_shutdown(self) -> None:
        if self._co2_hysteresis_unsub is not None:
            self._co2_hysteresis_unsub()
            self._co2_hysteresis_unsub = None
        while self._unsubs:
            self._unsubs.pop()()
        clear_room_notification_state(self.hass, self.entry.entry_id, self.subentry.subentry_id)
        self._started = False
        # A clean Home Assistant restart should not discard a long-stable
        # hysteresis mode merely because the last mode *change* happened more
        # than DECISION_MEMORY_TTL ago. Refresh the tiny memory timestamp only
        # on clean shutdown; after an unclean stop the existing TTL still keeps
        # stale decisions from being resurrected.
        if self.data is not None and self.data.result is not None:
            self._previous_mode = self.data.result.mode
            self._previous_decision_need = self.data.result.decision_need
            self._previous_mode_at = dt_util.utcnow()
        await self._memory_store.async_save(self._memory_payload())
        await super().async_shutdown()


def _coordinator_key(entry: ConfigEntry, subentry: ConfigSubentry) -> str:
    return f"{entry.entry_id}:{subentry.subentry_id}"


async def async_get_or_create_room_coordinator(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> LueftungsberaterRoomCoordinator:
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_COORDINATORS, {})
    key = _coordinator_key(entry, subentry)
    coordinator = store.get(key)
    if coordinator is None:
        coordinator = LueftungsberaterRoomCoordinator(hass, entry, subentry)
        store[key] = coordinator
        await coordinator.async_start()
    return coordinator


def get_room_coordinator(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> LueftungsberaterRoomCoordinator | None:
    return hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {}).get(_coordinator_key(entry, subentry))


async def async_stop_entry_coordinators(hass: HomeAssistant, entry: ConfigEntry) -> None:
    store = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {})
    prefix = f"{entry.entry_id}:"
    for key in [item for item in store if item.startswith(prefix)]:
        coordinator = store.pop(key, None)
        if coordinator is not None:
            await coordinator.async_shutdown()
    clear_assistant_notification_state(hass, entry.entry_id)

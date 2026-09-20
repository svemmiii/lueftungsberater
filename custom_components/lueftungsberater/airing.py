"""Internal airing-session tracking for rooms with window contacts."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .time_utils import clamp_not_future

from .const import (
    CONF_WINDOWS,
    DATA_TRACKERS,
    DOMAIN,
    MIN_CONFIRMED_AIRING,
    STORAGE_VERSION,
    WINDOW_UNKNOWN_GRACE,
)

_LOGGER = logging.getLogger(__name__)

_UNKNOWN = {"unknown", "unavailable", "none", ""}


def tracker_signal(entry_id: str, subentry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_{subentry_id}_airing_update"


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed


class RoomAiringTracker:
    """Track real airing sessions while doing no idle minute polling."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self._configured_windows = tuple(subentry.data.get(CONF_WINDOWS, []) or [])
        self.windows = self._configured_windows
        self._window_aliases: dict[str, str] = {}
        self._window_identities: dict[str, tuple[Any, ...]] = {}
        self.open_since: datetime | None = None
        self.minimum_reached_at: datetime | None = None
        # Fallback routine anchor for a session that was definitely long enough
        # but whose real closing time could not be observed (for example after
        # an extended unknown/unavailable contact outage).  This must never be
        # exposed as last_confirmed_airing because it is not a close timestamp.
        self.last_qualified_airing_seen_at: datetime | None = None
        self.last_confirmed_airing: datetime | None = None
        self.tracking_started_at: datetime | None = None
        self._unsub_state = None
        self._unsub_registry = None
        self._unsub_tick = None
        self._unsub_fallback = None
        self._unsub_minimum = None
        self._unsub_unknown_grace = None
        self._unknown_since: datetime | None = None
        self._active = False
        self._save_tasks: set[asyncio.Task[Any]] = set()
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.airing.{entry.entry_id}.{subentry.subentry_id}"
        )

    def _create_background_task(self, target, name: str):
        # Home Assistant 2026.6+ provides lifecycle-bound task creation on
        # ConfigEntry. The integration's declared minimum already guarantees
        # this API, so do not fall back to hass.async_create_task (which could
        # outlive entry unload).
        return self.entry.async_create_background_task(self.hass, target, name)

    def _queue_save(self) -> None:
        task = self._create_background_task(
            self._async_save(),
            f"Lüftungsberater airing save {self.subentry.subentry_id}",
        )
        if isinstance(task, asyncio.Task):
            self._save_tasks.add(task)
            task.add_done_callback(self._save_tasks.discard)

    async def _drain_save_tasks(self) -> None:
        tasks = tuple(self._save_tasks)
        if not tasks:
            return
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._save_tasks.clear()

    def _subscribe_window_states(self) -> None:
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        if self.windows:
            self._unsub_state = async_track_state_change_event(
                self.hass, self.windows, self._async_window_changed
            )

    @staticmethod
    def _registry_identity(entry: Any) -> tuple[Any, ...] | None:
        if entry is None:
            return None
        entity_id = getattr(entry, "entity_id", None)
        domain = getattr(entry, "domain", None)
        if domain is None and isinstance(entity_id, str) and "." in entity_id:
            domain = entity_id.split(".", 1)[0]
        return (
            domain,
            getattr(entry, "platform", None),
            getattr(entry, "unique_id", None),
            getattr(entry, "device_id", None),
            getattr(entry, "original_name", None),
            getattr(entry, "original_device_class", None),
        )

    @staticmethod
    def _identity_match_rank(previous: tuple[Any, ...], candidate: tuple[Any, ...]) -> int:
        """Return 2 for exact registry identity, 1 for a safe device fallback.

        Home Assistant identifies registry entities by entity domain + integration
        platform + unique_id.  The fallback is intentionally stricter than a
        name-only comparison and is only used when a recreated integration
        changed the unique_id while still pointing at the same device.
        """
        if len(previous) != 6 or len(candidate) != 6:
            return 0
        prev_domain, prev_platform, prev_unique, prev_device, prev_name, prev_class = previous
        new_domain, new_platform, new_unique, new_device, new_name, new_class = candidate
        if not prev_domain or prev_domain != new_domain:
            return 0
        if not prev_platform or prev_platform != new_platform:
            return 0
        if prev_unique is not None and prev_unique == new_unique:
            return 2
        if (
            prev_device is not None
            and prev_device == new_device
            and prev_name is not None
            and prev_name == new_name
            and prev_class == new_class
        ):
            return 1
        return 0

    def _restore_window_identities(self, stored: dict[str, Any]) -> None:
        raw_identities = stored.get("window_identities")
        if not isinstance(raw_identities, dict):
            return
        for configured in self._configured_windows:
            raw_identity = raw_identities.get(configured)
            if not isinstance(raw_identity, (list, tuple)) or len(raw_identity) != 6:
                continue
            if any(value is not None and not isinstance(value, str) for value in raw_identity):
                continue
            self._window_identities[configured] = tuple(raw_identity)

    def _refresh_window_identities(self) -> None:
        registry = er.async_get(self.hass)
        for configured, resolved in zip(self._configured_windows, self.windows, strict=False):
            identity = self._registry_identity(registry.async_get(resolved))
            if identity is not None:
                self._window_identities[configured] = identity

    def _repair_missing_windows_from_registry(self) -> None:
        """Resolve a recreated window entity that already exists at startup.

        Registry create events are not replayed after Home Assistant starts the
        integration.  Persisted identities therefore need one proactive lookup
        for configured/aliased entity IDs that disappeared while HA was down.
        Only one unambiguous best match is accepted.
        """
        registry = er.async_get(self.hass)
        entities = getattr(registry, "entities", None)
        values = getattr(entities, "values", None)
        if not callable(values):
            return

        candidates = tuple(values())
        current = list(self.windows)
        occupied = set(current)
        changed = False

        for index, configured in enumerate(self._configured_windows):
            current_entity_id = current[index]
            if registry.async_get(current_entity_id) is not None:
                continue
            previous = self._window_identities.get(configured)
            if previous is None:
                continue

            ranked: dict[int, list[str]] = {2: [], 1: []}
            for entry in candidates:
                candidate_entity_id = getattr(entry, "entity_id", None)
                if not isinstance(candidate_entity_id, str):
                    continue
                if candidate_entity_id in occupied and candidate_entity_id != current_entity_id:
                    continue
                candidate_identity = self._registry_identity(entry)
                if candidate_identity is None:
                    continue
                rank = self._identity_match_rank(previous, candidate_identity)
                if rank:
                    ranked[rank].append(candidate_entity_id)

            matches = ranked[2] or ranked[1]
            if len(matches) != 1:
                continue
            replacement = matches[0]
            occupied.discard(current_entity_id)
            occupied.add(replacement)
            current[index] = replacement
            self._window_aliases[configured] = replacement
            changed = True

        if changed:
            self.windows = tuple(current)
            self._refresh_window_identities()

    def _restore_window_aliases(self, stored: dict[str, Any]) -> None:
        raw_aliases = stored.get("window_aliases")
        if not isinstance(raw_aliases, dict):
            raw_aliases = {}
        registry = er.async_get(self.hass)
        resolved: list[str] = []
        for configured in self._configured_windows:
            alias = raw_aliases.get(configured)
            if isinstance(alias, str) and alias and (
                self.hass.states.get(alias) is not None or registry.async_get(alias) is not None
            ):
                self._window_aliases[configured] = alias
                resolved.append(alias)
            else:
                resolved.append(configured)
        self.windows = tuple(resolved)
        self._refresh_window_identities()

    def _replace_window_entity(self, old_entity_id: str, new_entity_id: str) -> bool:
        if old_entity_id == new_entity_id or old_entity_id not in self.windows:
            return False
        current = list(self.windows)
        changed = False
        for index, entity_id in enumerate(current):
            if entity_id != old_entity_id:
                continue
            current[index] = new_entity_id
            configured = self._configured_windows[index]
            self._window_aliases[configured] = new_entity_id
            changed = True
        if not changed:
            return False
        self.windows = tuple(current)
        self._subscribe_window_states()
        self._refresh_window_identities()
        self._queue_save()
        self._async_window_changed(None)
        return True

    @callback
    def _async_entity_registry_updated(self, event: Event) -> None:
        if not self._active:
            return
        data = event.data
        action = data.get("action")
        entity_id = data.get("entity_id")
        if not isinstance(entity_id, str):
            return

        if action == "update":
            old_entity_id = data.get("old_entity_id")
            if isinstance(old_entity_id, str) and old_entity_id in self.windows:
                self._replace_window_entity(old_entity_id, entity_id)
            return

        if action != "create" or entity_id in self.windows:
            return

        # A real re-created registry entity cannot be followed from its new
        # entity_id alone. Repair only when its stored registry identity is
        # unambiguous. Home Assistant's exact identity is
        # domain+platform+unique_id; a stricter device/name/class fallback is
        # used only when the integration itself changed the unique_id.
        registry = er.async_get(self.hass)
        new_entry = registry.async_get(entity_id)
        new_identity = self._registry_identity(new_entry)
        if new_identity is None:
            return
        exact_matches: list[str] = []
        fallback_matches: list[str] = []
        for index, configured in enumerate(self._configured_windows):
            current = self.windows[index]
            # If the original registry entity still exists, an unavailable state
            # is not enough evidence that it was recreated. Never jump away from
            # a still-registered contact merely because another similar entity
            # appeared.
            if registry.async_get(current) is not None:
                continue
            current_state = self.hass.states.get(current)
            if current_state is not None and current_state.state not in _UNKNOWN:
                continue
            previous = self._window_identities.get(configured)
            if previous is None:
                continue
            rank = self._identity_match_rank(previous, new_identity)
            if rank == 2:
                exact_matches.append(current)
            elif rank == 1:
                fallback_matches.append(current)

        matches = exact_matches or fallback_matches
        if len(matches) == 1:
            self._replace_window_entity(matches[0], entity_id)

    def _contact_state(self) -> tuple[bool, bool]:
        """Return (any_open, all_contacts_known)."""
        if not self.windows:
            return False, True
        any_open = False
        all_known = True
        for entity_id in self.windows:
            state = self.hass.states.get(entity_id)
            if state is None or state.state in _UNKNOWN:
                all_known = False
                continue
            if state.state == "on":
                any_open = True
        return any_open, all_known

    @property
    def is_open(self) -> bool:
        """Return the effective open state including the short unknown grace.

        A contact that briefly becomes ``unknown``/``unavailable`` must not be
        interpreted as an immediate close by the CO2 state machines. The
        airing tracker already preserves ``open_since`` for WINDOW_UNKNOWN_GRACE;
        expose the same conservative state here so all consumers share one
        definition of "still open". Once the grace expires,
        _async_unknown_grace_expired() ends the session at the last definitely
        open instant.
        """
        any_open, all_known = self._contact_state()
        if any_open:
            return True
        if all_known or self.open_since is None or self._unknown_since is None:
            return False
        return dt_util.utcnow() < self._unknown_since + WINDOW_UNKNOWN_GRACE

    @property
    def current_open_minutes(self) -> float | None:
        if self.open_since is None or not self.is_open:
            return None
        return max(0.0, (dt_util.utcnow() - self.open_since).total_seconds() / 60.0)

    @property
    def current_airing_qualified(self) -> bool:
        """Whether the *current* open session has safely reached five minutes.

        This is intentionally separate from ``last_confirmed_airing``. The
        current session may already satisfy the routine while the historical
        "last airing" timestamp must still remain the time when that session is
        actually closed.
        """
        return (
            self.open_since is not None
            and self.minimum_reached_at is not None
            and self.is_open
        )

    @property
    def hours_since_last_airing(self) -> float | None:
        if self.last_confirmed_airing is None:
            return None
        return max(0.0, (dt_util.utcnow() - self.last_confirmed_airing).total_seconds() / 3600.0)

    def _routine_anchor(self) -> datetime | None:
        """Return the newest timestamp that safely satisfies the routine clock.

        ``last_confirmed_airing`` is the preferred historical anchor because an
        actual OFF transition was observed. ``last_qualified_airing_seen_at`` is
        deliberately weaker: it only says that a five-minute-qualified airing
        was still definitely in progress when tracking was lost.  It prevents an
        old 24-hour routine from immediately returning without inventing a close.
        """
        anchors = (
            self.last_confirmed_airing,
            self.last_qualified_airing_seen_at,
            self.tracking_started_at,
        )
        valid = [anchor for anchor in anchors if anchor is not None]
        return max(valid) if valid else None

    @property
    def hours_since_routine_anchor(self) -> float | None:
        """Hours since the newest safe routine anchor.

        The 24-hour fallback needs a time anchor even for a brand-new room that
        has never completed a confirmed airing.  A qualified session whose real
        close was lost may also satisfy the routine clock through the separate
        ``last_qualified_airing_seen_at`` fallback, while the public historical
        last-airing timestamp remains untouched.
        """
        anchor = self._routine_anchor()
        if anchor is None:
            return None
        return max(0.0, (dt_util.utcnow() - anchor).total_seconds() / 3600.0)

    async def async_initialize(self) -> None:
        stored = await self._store.async_load() or {}
        now = dt_util.utcnow()
        self.last_confirmed_airing = clamp_not_future(
            now, _parse_dt(stored.get("last_confirmed_airing"))
        )
        self.last_qualified_airing_seen_at = clamp_not_future(
            now, _parse_dt(stored.get("last_qualified_airing_seen_at"))
        )
        self.tracking_started_at = clamp_not_future(
            now, _parse_dt(stored.get("tracking_started_at"))
        ) or now
        self._restore_window_identities(stored)
        self._restore_window_aliases(stored)
        self._repair_missing_windows_from_registry()
        stored_open_since = clamp_not_future(now, _parse_dt(stored.get("open_since")))
        stored_unknown_since = clamp_not_future(
            now, _parse_dt(stored.get("unknown_since"))
        )
        stored_minimum_reached_at = clamp_not_future(
            now, _parse_dt(stored.get("minimum_reached_at"))
        )

        any_open, all_known = self._contact_state()
        if any_open:
            self.open_since = stored_open_since or now
            self._unknown_since = None
            self.minimum_reached_at = self._valid_minimum_reached_at(
                stored_minimum_reached_at
            )
            self._remember_qualified_airing_seen_at(self.minimum_reached_at)
            self._mark_minimum_reached_if_due(now)
        elif not all_known:
            # Startup often exposes contacts as unknown for a moment. Preserve a
            # running session briefly, but never let an unknown state count as
            # confirmed airing without a time limit.
            self.open_since = stored_open_since
            self._unknown_since = (
                stored_unknown_since
                if stored_open_since is not None
                else None
            ) or (now if stored_open_since is not None else None)
            # Preserve an already-qualified session through a short unknown
            # startup phase, but never let unknown time newly satisfy the
            # five-minute minimum.
            self.minimum_reached_at = self._valid_minimum_reached_at(
                stored_minimum_reached_at
            )
            self._remember_qualified_airing_seen_at(self.minimum_reached_at)
        else:
            # If HA comes back with the contact already definitively closed, an
            # open session from before shutdown cannot receive a trustworthy OFF
            # timestamp.  Still preserve the weaker fact that it had already
            # reached the five-minute minimum, so an old 24-hour routine does not
            # immediately reappear.  The minimum timestamp is the latest point
            # we can prove from the stored session without inventing downtime.
            if stored_open_since is not None:
                self.open_since = stored_open_since
                qualified_at = self._valid_minimum_reached_at(
                    stored_minimum_reached_at
                )
                self._remember_qualified_airing_seen_at(qualified_at)
            self.open_since = None
            self._unknown_since = None
            self.minimum_reached_at = None

        self._active = True
        if self.windows:
            self._subscribe_window_states()
            self._unsub_registry = self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED, self._async_entity_registry_updated
            )
        self._sync_timers()
        await self._async_save()

    async def async_stop(self) -> None:
        # If HA stops while a qualified contact is still definitely ON, remember
        # the latest point at which that successful airing was actually observed.
        # This is only a routine fallback anchor; it is never a fabricated close.
        if getattr(self, "minimum_reached_at", None) is not None:
            any_open, _all_known = self._contact_state()
            if any_open:
                seen_at = dt_util.utcnow()
                self._remember_qualified_airing_seen_at(seen_at)
        self._active = False
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        if getattr(self, "_unsub_registry", None):
            self._unsub_registry()
            self._unsub_registry = None
        self._cancel_tick()
        self._cancel_fallback()
        self._cancel_minimum()
        self._cancel_unknown_grace()
        # Cancel any older fire-and-forget Store writes before the final save so
        # an earlier snapshot cannot finish after shutdown and overwrite it.
        await self._drain_save_tasks()
        await self._async_save()

    def _cancel_tick(self) -> None:
        if self._unsub_tick:
            self._unsub_tick()
            self._unsub_tick = None

    def _cancel_fallback(self) -> None:
        if self._unsub_fallback:
            self._unsub_fallback()
            self._unsub_fallback = None

    def _cancel_minimum(self) -> None:
        if self._unsub_minimum:
            self._unsub_minimum()
            self._unsub_minimum = None

    def _cancel_unknown_grace(self) -> None:
        if self._unsub_unknown_grace:
            self._unsub_unknown_grace()
            self._unsub_unknown_grace = None

    def _schedule_unknown_grace(self) -> None:
        self._cancel_unknown_grace()
        if self.open_since is None or self._unknown_since is None:
            return
        deadline = self._unknown_since + WINDOW_UNKNOWN_GRACE
        now = dt_util.utcnow()
        if deadline <= now:
            self._async_unknown_grace_expired(now)
            return
        self._unsub_unknown_grace = async_track_point_in_utc_time(
            self.hass, self._async_unknown_grace_expired, deadline
        )

    def _valid_minimum_reached_at(
        self, value: datetime | None
    ) -> datetime | None:
        if self.open_since is None or value is None:
            return None
        deadline = self.open_since + MIN_CONFIRMED_AIRING
        if value < deadline:
            return None
        return value

    def _remember_qualified_airing_seen_at(self, value: datetime | None) -> bool:
        """Remember safe routine evidence without pretending a close occurred."""
        if value is None:
            return False
        if (
            self.last_qualified_airing_seen_at is None
            or value > self.last_qualified_airing_seen_at
        ):
            self.last_qualified_airing_seen_at = value
            return True
        return False

    def _mark_minimum_reached_if_due(self, now: datetime) -> bool:
        """Latch the five-minute milestone once, only while definitely open."""
        if self.open_since is None or self.minimum_reached_at is not None:
            return False
        any_open, _all_known = self._contact_state()
        if not any_open:
            return False
        deadline = self.open_since + MIN_CONFIRMED_AIRING
        if now < deadline:
            return False
        self.minimum_reached_at = deadline
        # The five-minute mark itself is already sufficient proof that the old
        # routine was fulfilled, even though the historical close comes later.
        self._remember_qualified_airing_seen_at(deadline)
        return True

    def _schedule_minimum(self) -> None:
        self._cancel_minimum()
        if self.open_since is None or self.minimum_reached_at is not None:
            return
        any_open, _all_known = self._contact_state()
        if not any_open:
            return
        deadline = self.open_since + MIN_CONFIRMED_AIRING
        now = dt_util.utcnow()
        if deadline <= now:
            if self._mark_minimum_reached_if_due(now):
                self._queue_save()
            return
        self._unsub_minimum = async_track_point_in_utc_time(
            self.hass, self._async_minimum_reached, deadline
        )

    @callback
    def _async_minimum_reached(self, now: datetime) -> None:
        self._unsub_minimum = None
        if not self._active:
            return
        changed = self._mark_minimum_reached_if_due(now)
        if changed:
            self._queue_save()
            async_dispatcher_send(
                self.hass,
                tracker_signal(self.entry.entry_id, self.subentry.subentry_id),
            )
        self._sync_timers()

    def _finish_open_session(self, end: datetime, *, observed_close: bool) -> None:
        """End the current session without inventing a close timestamp.

        ``last_confirmed_airing`` is historical data: it represents an airing
        whose *closing* was actually observed.  A contact that times out in
        ``unknown``/``unavailable`` only proves that tracking was lost, not that
        the physical window closed at the start of that outage.

        A real OFF transition may confirm the session when either the five-minute
        latch was already reached, or the contact stayed continuously known-open
        for at least five minutes until that OFF event.  Unknown time is never
        used to newly satisfy the minimum.
        """
        if self.open_since is None:
            self._unknown_since = None
            return

        duration = max(timedelta(0), end - self.open_since)
        minimum_was_proven = self.minimum_reached_at is not None
        continuously_known = self._unknown_since is None
        if observed_close and (
            minimum_was_proven
            or (continuously_known and duration >= MIN_CONFIRMED_AIRING)
        ):
            self.last_confirmed_airing = end
            # A real close is stronger and newer than the fallback evidence.
            self.last_qualified_airing_seen_at = None
        self.open_since = None
        self._unknown_since = None
        self.minimum_reached_at = None

    @callback
    def _async_unknown_grace_expired(self, now: datetime) -> None:
        self._unsub_unknown_grace = None
        if not self._active:
            return
        any_open, all_known = self._contact_state()
        if (
            self.open_since is not None
            and not any_open
            and not all_known
            and self._unknown_since is not None
            and now >= self._unknown_since + WINDOW_UNKNOWN_GRACE
        ):
            # We only know that tracking was lost after a definitely-open
            # period.  Do not invent a physical close at ``_unknown_since`` and
            # do not advance historical last-airing data without a real OFF.
            self._finish_open_session(
                self._unknown_since, observed_close=False
            )
            self._queue_save()
        self._sync_timers()
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    def _sync_timers(self) -> None:
        """Run timers only for states that can still change the recommendation."""
        any_open, all_known = self._contact_state()
        if any_open and self.open_since is not None:
            self._cancel_unknown_grace()
            self._unknown_since = None
            self._cancel_fallback()
            if self.minimum_reached_at is None:
                self._schedule_minimum()
            else:
                self._cancel_minimum()
            if self._unsub_tick is None:
                self._unsub_tick = async_track_time_interval(
                    self.hass, self._async_tick, timedelta(minutes=1)
                )
            return

        self._cancel_tick()
        if not all_known and self.open_since is not None:
            self._cancel_fallback()
            # Do not let unknown/unavailable time newly satisfy the minimum.
            # An already-qualified session remains qualified through the grace.
            self._cancel_minimum()
            if self._unknown_since is None:
                self._unknown_since = dt_util.utcnow()
            if self._unsub_unknown_grace is None:
                self._schedule_unknown_grace()
            return

        self._cancel_unknown_grace()
        self._cancel_minimum()
        self._cancel_fallback()
        anchor = self._routine_anchor()
        if anchor is None:
            return
        target = anchor + timedelta(hours=24)
        now = dt_util.utcnow()
        if target > now:
            self._unsub_fallback = async_track_point_in_utc_time(
                self.hass, self._async_fallback_due, target
            )

    @callback
    def _async_tick(self, _now: datetime) -> None:
        if not self._active:
            return
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    @callback
    def _async_fallback_due(self, _now: datetime) -> None:
        self._unsub_fallback = None
        if not self._active:
            return
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    @callback
    def _async_window_changed(self, _event: Event) -> None:
        if not self._active:
            return
        now = dt_util.utcnow()
        any_open, all_known = self._contact_state()
        changed = False

        if any_open:
            if self.open_since is None:
                self.open_since = now
                self.minimum_reached_at = None
                changed = True
            if self._unknown_since is not None:
                self._unknown_since = None
                changed = True
            if self._mark_minimum_reached_if_due(now):
                changed = True
        elif not all_known and self.open_since is not None:
            if self._unknown_since is None:
                # For a real state-change event from ON to unknown/unavailable,
                # ``now`` is also a safe last-definitely-open observation.  This
                # keeps a long qualified opening from becoming immediately
                # routine-overdue after grace expiry. Synthetic startup/registry
                # callbacks do not get this upgrade because they provide no such
                # continuity evidence.
                old_state = (
                    _event.data.get("old_state")
                    if _event is not None and hasattr(_event, "data")
                    else None
                )
                if (
                    self.minimum_reached_at is not None
                    and getattr(old_state, "state", None) == "on"
                    and self._remember_qualified_airing_seen_at(now)
                ):
                    changed = True
                self._unknown_since = now
                changed = True
        elif all_known and self.open_since is not None:
            # A real OFF is the historical close timestamp. If there was an
            # unknown phase before it, only an already-reached five-minute latch
            # may confirm the airing; unknown time itself never completes it.
            self._finish_open_session(now, observed_close=True)
            changed = True
        elif all_known and self._unknown_since is not None:
            self._unknown_since = None
            changed = True

        if changed:
            self._queue_save()

        self._sync_timers()
        async_dispatcher_send(
            self.hass, tracker_signal(self.entry.entry_id, self.subentry.subentry_id)
        )

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "open_since": self.open_since.isoformat() if self.open_since else None,
                "unknown_since": self._unknown_since.isoformat() if self._unknown_since else None,
                "minimum_reached_at": (
                    self.minimum_reached_at.isoformat()
                    if self.minimum_reached_at
                    else None
                ),
                "last_qualified_airing_seen_at": (
                    self.last_qualified_airing_seen_at.isoformat()
                    if self.last_qualified_airing_seen_at
                    else None
                ),
                "last_confirmed_airing": self.last_confirmed_airing.isoformat() if self.last_confirmed_airing else None,
                "tracking_started_at": (
                    self.tracking_started_at.isoformat()
                    if self.tracking_started_at
                    else None
                ),
                "window_aliases": dict(self._window_aliases),
                "window_identities": {
                    configured: list(identity)
                    for configured, identity in self._window_identities.items()
                },
            }
        )


def _tracker_bucket(hass: HomeAssistant, entry_id: str) -> dict[str, RoomAiringTracker]:
    domain_data = hass.data.setdefault(DOMAIN, {})
    entry_data = domain_data.setdefault(entry_id, {})
    return entry_data.setdefault(DATA_TRACKERS, {})


async def async_get_or_create_tracker(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> RoomAiringTracker | None:
    windows = subentry.data.get(CONF_WINDOWS, []) or []
    if not windows:
        return None
    bucket = _tracker_bucket(hass, entry.entry_id)
    tracker = bucket.get(subentry.subentry_id)
    if tracker is not None:
        return tracker
    tracker = RoomAiringTracker(hass, entry, subentry)
    try:
        await tracker.async_initialize()
    except Exception:
        # async_initialize may already have installed listeners/timers before a
        # late Store write fails. Tear those down before propagating setup
        # failure, and never expose this partial tracker through hass.data.
        try:
            await tracker.async_stop()
        except Exception:  # noqa: BLE001 - preserve the original setup error
            _LOGGER.debug("Unable to clean up failed airing tracker setup", exc_info=True)
        raise
    bucket[subentry.subentry_id] = tracker
    return tracker


def get_tracker(hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> RoomAiringTracker | None:
    try:
        return hass.data[DOMAIN][entry.entry_id][DATA_TRACKERS].get(subentry.subentry_id)
    except KeyError:
        return None


async def async_stop_entry_trackers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    try:
        bucket = hass.data[DOMAIN][entry.entry_id].get(DATA_TRACKERS, {})
    except KeyError:
        return
    for tracker in list(bucket.values()):
        await tracker.async_stop()
    bucket.clear()

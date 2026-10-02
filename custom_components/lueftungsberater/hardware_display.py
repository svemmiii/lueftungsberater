"""Non-blocking HA -> ESPHome display return channel for direct stations."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import ATTR_DOMAIN, ATTR_SERVICE, EVENT_SERVICE_REGISTERED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HARDWARE_DEVICE_ID,
    CONF_HARDWARE_ROOM_ID,
    DATA_HARDWARE_DISPLAY_PUSHERS,
    DOMAIN,
    ENTRY_KIND_LOCAL,
    HARDWARE_ROLE_MASTER,
    HARDWARE_ROLE_NODE,
    HARDWARE_ROLE_STANDALONE,
    SUBENTRY_TYPE_STATION,
    entry_kind,
)
from .display_payload import hardware_display_payload
from .hardware_hub import (
    direct_station_entities,
    station_for_room,
    station_is_direct,
    station_role,
)
from .hardware_provisioning import esphome_provision_target

if TYPE_CHECKING:
    from .runtime import RoomSnapshot

_LOGGER = logging.getLogger(__name__)

SERVICE_APPLY_DISPLAY_RESULT = "lueftungsstation_apply_display_result"
DISPLAY_RETRY_BACKOFF_MINUTES = (1, 2, 5, 10)


def _store(hass: HomeAssistant) -> dict[str, "DirectDisplayDispatcher"]:
    return hass.data.setdefault(DOMAIN, {}).setdefault(
        DATA_HARDWARE_DISPLAY_PUSHERS, {}
    )


def _eligible_direct_display_station(
    hass: HomeAssistant,
    entry: ConfigEntry,
    room_id: str,
) -> ConfigSubentry | None:
    """Return the direct station which owns this room display, if any.

    Nodes never receive direct display pushes. A master only gets its own direct
    room result when it actually has a local direct sensor set; a gateway-only
    master therefore never gets a room display result merely because it routes
    ESP-NOW nodes.
    """
    station = station_for_room(entry, room_id)
    if station is None or station.subentry_type != SUBENTRY_TYPE_STATION:
        return None
    if not station_is_direct(station):
        return None

    role = station_role(station)
    if role == HARDWARE_ROLE_NODE:
        return None
    if role not in {HARDWARE_ROLE_STANDALONE, HARDWARE_ROLE_MASTER}:
        return None
    if role == HARDWARE_ROLE_MASTER and direct_station_entities(hass, station) is None:
        return None
    if not str(station.data.get(CONF_HARDWARE_DEVICE_ID) or "").strip():
        return None
    return station


class DirectDisplayDispatcher:
    """Keep the newest direct display result pending until ESPHome accepts it."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._desired: dict[str, dict[str, Any]] = {}
        self._sent: dict[str, dict[str, Any]] = {}
        self._failures: dict[str, int] = {}
        self._next_due: dict[str, datetime] = {}
        self._running: set[str] = set()
        self._tasks: set[asyncio.Task[Any]] = set()
        self._unsubs: list[Any] = []
        self._stopped = False

    def start(self) -> None:
        """Start lightweight retry and late-firmware service discovery."""
        if self._stopped or self._unsubs:
            return
        self._unsubs.append(
            self.hass.bus.async_listen(
                EVENT_SERVICE_REGISTERED, self._service_registered
            )
        )
        self._unsubs.append(
            async_track_time_interval(
                self.hass, self._retry_pending, timedelta(minutes=1)
            )
        )

    @callback
    def stop(self) -> None:
        """Stop retry/listener state for one unloaded config entry."""
        if self._stopped:
            return
        self._stopped = True
        while self._unsubs:
            unsub = self._unsubs.pop()
            try:
                unsub()
            except Exception:  # noqa: BLE001 - unload cleanup must be best effort
                _LOGGER.debug("Unable to remove direct display listener", exc_info=True)
        for task in tuple(self._tasks):
            if not task.done():
                task.cancel()
        self._tasks.clear()
        self._desired.clear()
        self._sent.clear()
        self._failures.clear()
        self._next_due.clear()
        self._running.clear()
        store = self.hass.data.get(DOMAIN, {}).get(DATA_HARDWARE_DISPLAY_PUSHERS, {})
        if isinstance(store, dict) and store.get(self.entry.entry_id) is self:
            store.pop(self.entry.entry_id, None)

    @callback
    def queue_room(self, room_id: str, snapshot: RoomSnapshot) -> None:
        """Remember and asynchronously send the newest result for one room."""
        if self._stopped or entry_kind(self.entry) != ENTRY_KIND_LOCAL:
            return
        station = _eligible_direct_display_station(
            self.hass, self.entry, room_id
        )
        if station is None:
            # Reconfigure/delete may happen before the entry reload completes.
            # Purge any old in-memory result for this room so it can never be
            # delivered to a no-longer-valid station assignment.
            for station_id, payload in tuple(self._desired.items()):
                if str(payload.get("room_id") or "") == room_id:
                    self._purge_station(station_id)
            return

        payload = {
            "station_subentry_id": station.subentry_id,
            "room_id": room_id,
            **hardware_display_payload(
                self.hass, self.entry, room_id, snapshot=snapshot
            ),
        }
        station_id = station.subentry_id
        previous_desired = self._desired.get(station_id)
        self._desired[station_id] = payload

        if self._sent.get(station_id) == payload:
            self._failures.pop(station_id, None)
            self._next_due.pop(station_id, None)
            return

        # A genuinely changed display result is a new piece of state, not a
        # retry of the old failed transport. Try it immediately even while the
        # previous payload was in backoff (most importantly for safety_lock).
        # Repeated identical room refreshes while an ESP is offline keep the
        # existing bounded retry schedule and therefore cannot create polling.
        if previous_desired != payload:
            self._next_due.pop(station_id, None)
            self._schedule_attempt(station_id)
            return

        due = self._next_due.get(station_id)
        if due is None or dt_util.utcnow() >= due:
            self._schedule_attempt(station_id)

    @callback
    def _service_registered(self, event) -> None:
        """Flush deferred results when a later firmware exposes the action."""
        if self._stopped or event.data.get(ATTR_DOMAIN) != "esphome":
            return
        service = str(event.data.get(ATTR_SERVICE) or "")
        if not service.endswith(f"_{SERVICE_APPLY_DISPLAY_RESULT}"):
            return

        for station_id, payload in tuple(self._desired.items()):
            if self._sent.get(station_id) == payload:
                continue
            station = self.entry.subentries.get(station_id)
            if station is None:
                self._purge_station(station_id)
                continue
            device_id = str(station.data.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
            target = esphome_provision_target(self.hass, device_id) if device_id else None
            if target is None or target.service(SERVICE_APPLY_DISPLAY_RESULT) != service:
                continue
            # The service appearing is a meaningful new opportunity; do not make
            # the user wait for an old offline/missing-action backoff deadline.
            self._next_due.pop(station_id, None)
            self._schedule_attempt(station_id)

    async def _retry_pending(self, _now=None) -> None:
        """Retry only outstanding direct display results with bounded backoff."""
        if self._stopped:
            return
        now = dt_util.utcnow()
        for station_id, payload in tuple(self._desired.items()):
            if self._sent.get(station_id) == payload:
                continue
            due = self._next_due.get(station_id)
            if due is not None and now < due:
                continue
            self._schedule_attempt(station_id)

    @callback
    def _schedule_attempt(self, station_id: str) -> None:
        if self._stopped or station_id in self._running:
            return
        self._running.add(station_id)
        task = self.entry.async_create_background_task(
            self.hass,
            self._attempt_guarded(station_id),
            f"Lüftungsassistent direct display {station_id}",
        )
        if isinstance(task, asyncio.Task):
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _attempt_guarded(self, station_id: str) -> None:
        try:
            await self._attempt_station(station_id)
        except Exception:  # noqa: BLE001 - display delivery must never escape into room logic
            _LOGGER.exception(
                "Unexpected direct-display delivery failure for station %s",
                station_id,
            )
            if station_id in self._desired:
                self._defer(station_id, "unexpected display delivery failure")
        finally:
            self._running.discard(station_id)
            # If a newer snapshot arrived while the previous payload was in
            # flight, immediately send that newest value unless a failure put us
            # into backoff.
            desired = self._desired.get(station_id)
            if (
                not self._stopped
                and desired is not None
                and self._sent.get(station_id) != desired
                and station_id not in self._next_due
            ):
                self._schedule_attempt(station_id)

    async def _attempt_station(self, station_id: str) -> None:
        payload = self._desired.get(station_id)
        if payload is None or self._sent.get(station_id) == payload:
            return

        station = self.entry.subentries.get(station_id)
        room_id = str(payload.get("room_id") or "")
        if (
            station is None
            or station.subentry_type != SUBENTRY_TYPE_STATION
            or str(station.data.get(CONF_HARDWARE_ROOM_ID) or "") != room_id
            or _eligible_direct_display_station(
                self.hass, self.entry, room_id
            ) is not station
        ):
            self._purge_station(station_id)
            return

        device_id = str(station.data.get(CONF_HARDWARE_DEVICE_ID) or "").strip()
        target = esphome_provision_target(self.hass, device_id) if device_id else None
        if target is None:
            self._defer(station_id, "ESPHome target unavailable")
            return

        service_name = target.service(SERVICE_APPLY_DISPLAY_RESULT)
        if not self.hass.services.has_service("esphome", service_name):
            # DEV-0.7 intentionally lands here. Missing firmware support is a
            # deferred display feature, never an integration/setup failure.
            self._defer(station_id, "display action not registered", log_warning=False)
            return

        try:
            await self.hass.services.async_call(
                "esphome",
                service_name,
                dict(payload),
                blocking=True,
            )
        except Exception:  # noqa: BLE001 - display transport may never block decisions
            self._defer(station_id, "display action failed")
            return

        # Do not mark a newer payload as sent merely because an older in-flight
        # call completed. The guard will immediately send the newest one.
        if self._desired.get(station_id) == payload:
            self._sent[station_id] = dict(payload)
            self._failures.pop(station_id, None)
            self._next_due.pop(station_id, None)

    def _defer(
        self, station_id: str, reason: str, *, log_warning: bool = True
    ) -> None:
        count = self._failures.get(station_id, 0) + 1
        self._failures[station_id] = count
        delay = DISPLAY_RETRY_BACKOFF_MINUTES[
            min(count - 1, len(DISPLAY_RETRY_BACKOFF_MINUTES) - 1)
        ]
        self._next_due[station_id] = dt_util.utcnow() + timedelta(minutes=delay)
        log = _LOGGER.warning if log_warning else _LOGGER.debug
        log(
            "Direct display for station %s deferred (%s); next retry in %s min",
            station_id,
            reason,
            delay,
        )

    def _purge_station(self, station_id: str) -> None:
        self._desired.pop(station_id, None)
        self._sent.pop(station_id, None)
        self._failures.pop(station_id, None)
        self._next_due.pop(station_id, None)


def async_setup_direct_display_dispatcher(
    hass: HomeAssistant, entry: ConfigEntry
) -> DirectDisplayDispatcher | None:
    """Create the per-entry dispatcher before room coordinators first refresh."""
    if entry_kind(entry) != ENTRY_KIND_LOCAL:
        return None
    store = _store(hass)
    existing = store.get(entry.entry_id)
    if existing is not None:
        return existing
    dispatcher = DirectDisplayDispatcher(hass, entry)
    store[entry.entry_id] = dispatcher
    dispatcher.start()
    entry.async_on_unload(dispatcher.stop)
    return dispatcher


@callback
def async_stop_direct_display_dispatcher(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Stop and discard one entry's in-memory display delivery state."""
    dispatcher = _store(hass).get(entry.entry_id)
    if dispatcher is not None:
        dispatcher.stop()


@callback
def async_queue_direct_display_result(
    hass: HomeAssistant,
    entry: ConfigEntry,
    room_id: str,
    snapshot: RoomSnapshot,
) -> None:
    """Queue one room snapshot without ever blocking room evaluation."""
    dispatcher = _store(hass).get(entry.entry_id)
    if dispatcher is None:
        return
    dispatcher.queue_room(room_id, snapshot)

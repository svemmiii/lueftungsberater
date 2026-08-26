"""Optional Home Assistant notifications for Lüftungsberater."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_NOTIFY_TARGET,
    CONF_NOTIFY_TRIGGERS,
    CONF_ROOM_NOTIFY_TRIGGERS,
    DATA_NOTIFICATION_STATE,
    DATA_NOTIFICATION_LOCKS,
    DEFAULT_NOTIFY_TRIGGERS,
    DEFAULT_ROOM_NOTIFY_TRIGGERS,
    DOMAIN,
    NOTIFY_TRIGGER_AIRING_FINISHED,
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
    NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED,
    NOTIFY_TRIGGER_ALL_CLEAR,
    SUBENTRY_TYPE_ROOM,
)
from .runtime import RoomSnapshot

_LOGGER = logging.getLogger(__name__)


def _trigger_for_mode(mode: str) -> str | None:
    if mode in {"nina_aussenluftgefahr", "luftqualitaet_sehr_schlecht"}:
        return NOTIFY_TRIGGER_AIR_DANGER
    if mode in {
        "nina_vorsicht",
        "luftqualitaet_maessig",
        "luftqualitaet_schlecht",
        "luftqualitaet_sehr_schlecht_typisch",
    }:
        return NOTIFY_TRIGGER_AIR_CAUTION
    if mode == "wettergefahr":
        return NOTIFY_TRIGGER_WEATHER_DANGER
    if mode == "wetter_vorsicht":
        return NOTIFY_TRIGGER_WEATHER_CAUTION
    return None


def _transition_trigger(
    previous_mode: str | None,
    previous_recommendation: str | None,
    mode: str | None,
    recommendation: str | None,
) -> str | None:
    if recommendation == "open_now" and previous_recommendation != "open_now":
        return NOTIFY_TRIGGER_AIRING_RECOMMENDED
    if mode == "lueftung_fertig" and previous_mode != "lueftung_fertig":
        return NOTIFY_TRIGGER_AIRING_FINISHED
    return None


def _message(language: str | None, room: str, trigger: str) -> tuple[str, str]:
    lang = (language or "en").lower()
    if lang.startswith("de"):
        lang = "de"
    elif lang.startswith("tr"):
        lang = "tr"
    else:
        lang = "en"

    titles = {
        "de": f"Lüftungsassistent · {room}",
        "en": f"Fresh Air Assistant · {room}",
        "tr": f"Fresh Air Assistant · {room}",
    }
    messages = {
        "de": {
            NOTIFY_TRIGGER_AIRING_RECOMMENDED: f"In {room} ist Lüften jetzt wieder sinnvoll.",
            NOTIFY_TRIGGER_AIRING_FINISHED: f"In {room} kannst du die Lüftung jetzt beenden und die Fenster wieder schließen.",
            NOTIFY_TRIGGER_AIR_DANGER: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl die Außenluft gerade stark belastet ist oder eine ernste Warnung vorliegt. Bitte schließe bei einer Schutzwarnung sofort und prüfe bei hoher Luftbelastung die aktuelle Empfehlung.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"In {room} ist noch ein Fenster oder eine Tür offen, während ein Außenluft-Hinweis aktiv ist. Prüfe bitte, ob du schließen solltest.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl eine ernste Wetterlage aktiv ist. Bitte prüfen und bei Bedarf schließen.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"In {room} ist noch ein Fenster oder eine Tür offen, während ein Wetterhinweis aktiv ist. Behalte die Lage im Blick.",
            NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED: f"Für {room} ist eine offizielle Schutzanweisung aktiv. Die überwachten Fenster und Türen sind aktuell geschlossen – bitte geschlossen halten und die amtlichen Hinweise beachten.",
            NOTIFY_TRIGGER_ALL_CLEAR: f"Für {room} ist eine Entwarnung eingegangen. Die harte Schutzsperre wurde aufgehoben; der Lüftungsassistent bewertet die aktuellen Raum- und Außenbedingungen wieder normal.",
        },
        "en": {
            NOTIFY_TRIGGER_AIRING_RECOMMENDED: f"Opening the windows in {room} is useful again now.",
            NOTIFY_TRIGGER_AIRING_FINISHED: f"You can finish airing {room} now and close the windows again.",
            NOTIFY_TRIGGER_AIR_DANGER: f"A window or door in {room} is still open while outdoor air is heavily polluted or a serious warning is active. Please close it immediately for a protection warning and check the current advice when pollution is high.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"A window or door in {room} is still open while an outdoor-air advisory is active. Please check whether it should be closed.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"A window or door in {room} is still open while severe weather is active. Please check it and close it if needed.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"A window or door in {room} is still open while a weather advisory is active. Please keep an eye on the situation.",
            NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED: f"An official protection instruction is active for {room}. The monitored windows and doors are currently closed – keep them closed and follow the official advice.",
            NOTIFY_TRIGGER_ALL_CLEAR: f"An all-clear has been issued for {room}. The hard protection lock has been removed and Fresh Air Assistant is evaluating the current indoor and outdoor conditions normally again.",
        },
        "tr": {
            NOTIFY_TRIGGER_AIRING_RECOMMENDED: f"{room} odasını havalandırmak yeniden uygun.",
            NOTIFY_TRIGGER_AIRING_FINISHED: f"{room} odasını havalandırmayı şimdi bitirip pencereleri yeniden kapatabilirsin.",
            NOTIFY_TRIGGER_AIR_DANGER: f"{room} odasında bir pencere veya kapı hâlâ açıkken dış hava ciddi şekilde kirli ya da önemli bir uyarı aktif. Lütfen kapat; koruyucu bir uyarı varsa bunu hemen yap, hava kirliliği yüksekse güncel öneriyi kontrol et.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"{room} odasında bir pencere veya kapı hâlâ açıkken dış hava uyarısı aktif. Kapatmanın gerekip gerekmediğini kontrol et.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"{room} odasında bir pencere veya kapı hâlâ açıkken ciddi hava koşulları aktif. Lütfen kontrol edip gerekirse kapat.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"{room} odasında bir pencere veya kapı hâlâ açıkken hava durumu uyarısı aktif. Lütfen durumu takip et.",
            NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED: f"{room} için resmî bir koruma talimatı aktif. İzlenen pencere ve kapılar şu anda kapalı; kapalı tut ve resmî talimatları takip et.",
            NOTIFY_TRIGGER_ALL_CLEAR: f"{room} için tehlikenin geçtiğine dair resmî bildirim geldi. Sert koruma kilidi kaldırıldı ve Fresh Air Assistant mevcut iç ve dış koşulları yeniden normal şekilde değerlendiriyor.",
        },
    }
    return titles[lang], messages[lang][trigger]



async def _async_send(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    trigger: str,
    *,
    display_name: str | None = None,
) -> bool:
    """Send through Home Assistant's notify entity action."""
    target = entry.data.get(CONF_NOTIFY_TARGET)
    if not isinstance(target, str) or not target:
        return False

    title, message = _message(
        hass.config.language,
        display_name or subentry.title,
        trigger,
    )
    try:
        await hass.services.async_call(
            "notify",
            "send_message",
            {"message": message, "title": title},
            target={"entity_id": target},
            blocking=False,
        )
        return True
    except Exception:  # noqa: BLE001 - a notification target must not break advice
        _LOGGER.exception("Unable to send Lüftungsassistent notification to %s", target)
        return False


def _assistant_warning_fingerprint(
    snapshot: RoomSnapshot,
    trigger: str | None,
) -> tuple[Any, ...]:
    """Build a stable warning identity shared by every room of an assistant.

    Raw sensor values and mutable human-readable warning text are intentionally
    excluded. The same warning must not notify again merely because an AQ value
    moves from 160 to 161 or an authority edits its description.
    """
    warnings = snapshot.warnings
    weather = snapshot.weather
    warning_ids = tuple(sorted(str(item) for item in warnings.warning_ids))
    if trigger in {NOTIFY_TRIGGER_AIR_DANGER, NOTIFY_TRIGGER_AIR_CAUTION}:
        air_identity = (weather.air_quality_index, weather.air_quality_pollutant)
    else:
        air_identity = (None, None)
    return (
        trigger,
        warnings.provider_domain,
        warning_ids,
        warnings.nina_status,
        warnings.nina_reason_key,
        warnings.weather_reason_key,
        bool(warnings.official_close_instruction),
        air_identity,
    )


def _room_window_state(
    hass: HomeAssistant,
    entry: ConfigEntry,
    current_subentry: ConfigSubentry,
    current_snapshot: RoomSnapshot,
) -> list[str]:
    """Return titles of currently open rooms in one local assistant."""
    # Lazy import avoids notifications.py <-> coordinator.py import recursion.
    from .coordinator import get_room_coordinator

    open_rooms: list[str] = []
    for candidate in entry.subentries.values():
        if candidate.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        if candidate.subentry_id == current_subentry.subentry_id:
            snapshot = current_snapshot
        else:
            coordinator = get_room_coordinator(hass, entry, candidate)
            snapshot = coordinator.data if coordinator is not None else None
        if snapshot is not None and snapshot.values.get("window_open") is True:
            open_rooms.append(candidate.title)
    return open_rooms


def clear_room_notification_state(
    hass: HomeAssistant, entry_id: str, subentry_id: str
) -> None:
    """Forget transient room-level notification state."""
    domain_data = hass.data.get(DOMAIN, {})
    store = domain_data.get(DATA_NOTIFICATION_STATE, {})
    store.pop(f"room:{entry_id}:{subentry_id}", None)
    # Also clean the old pre-v0.7.1 key shape after an in-place update.
    store.pop(f"{entry_id}:{subentry_id}", None)


def clear_assistant_notification_state(hass: HomeAssistant, entry_id: str) -> None:
    """Forget assistant-level warning state and its transient lock."""
    domain_data = hass.data.get(DOMAIN, {})
    store = domain_data.get(DATA_NOTIFICATION_STATE, {})
    store.pop(f"assistant:{entry_id}", None)
    locks = domain_data.get(DATA_NOTIFICATION_LOCKS, {})
    locks.pop(entry_id, None)


async def _async_handle_assistant_warning_notification(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    snapshot: RoomSnapshot,
    enabled: set[str],
) -> None:
    """Handle hazard/all-clear notifications once per assistant, not per room."""
    result = snapshot.result
    if result is None:
        return

    domain_data = hass.data.setdefault(DOMAIN, {})
    store = domain_data.setdefault(DATA_NOTIFICATION_STATE, {})
    locks = domain_data.setdefault(DATA_NOTIFICATION_LOCKS, {})
    lock = locks.setdefault(entry.entry_id, asyncio.Lock())

    async with lock:
        key = f"assistant:{entry.entry_id}"
        stored = store.get(key)
        state: dict[str, Any] = dict(stored) if isinstance(stored, dict) else {}
        initialized = bool(state.get("initialized"))

        open_rooms = _room_window_state(hass, entry, subentry, snapshot)
        any_window_open = bool(open_rooms)
        mode = result.mode
        hazard_trigger = _trigger_for_mode(mode or "")
        all_clear = snapshot.warnings.warning_notice_kind == "all_clear"
        official_active = bool(snapshot.warnings.official_close_instruction and result.safety_lock)

        # Track whether this assistant actually carried the official warning so
        # an all-clear is not emitted for an unrelated/stale notice.
        previously_official = bool(state.get("official_warning_seen"))
        if official_active:
            state["official_warning_seen"] = True

        # One warning per assistant. While any room remains open, additional
        # rooms do not create duplicate messages. Once every room is closed, a
        # later reopening may warn again during the same ongoing hazard.
        hazard_active = (
            any_window_open
            and hazard_trigger is not None
            and hazard_trigger in enabled
        )
        if hazard_active:
            fingerprint = _assistant_warning_fingerprint(snapshot, hazard_trigger)
            if state.get("hazard_fingerprint") != fingerprint:
                if not await _async_send(
                    hass,
                    entry,
                    subentry,
                    hazard_trigger,
                    display_name=entry.title,
                ):
                    return
            state["hazard_fingerprint"] = fingerprint
            if official_active:
                state["closed_official_fingerprint"] = _assistant_warning_fingerprint(
                    snapshot, NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED
                )
        elif not any_window_open:
            state.pop("hazard_fingerprint", None)

        # Optional awareness message while everything is already closed. Send
        # this once per official warning, not once per room.
        if (
            official_active
            and not any_window_open
            and NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED in enabled
        ):
            closed_fp = _assistant_warning_fingerprint(
                snapshot, NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED
            )
            if state.get("closed_official_fingerprint") != closed_fp:
                if not await _async_send(
                    hass,
                    entry,
                    subentry,
                    NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED,
                    display_name=entry.title,
                ):
                    return
                state["closed_official_fingerprint"] = closed_fp
        elif not official_active and not all_clear:
            state.pop("closed_official_fingerprint", None)

        # Entwarnung is an assistant/source event and is therefore also emitted
        # only once, regardless of the number of rooms configured below it.
        if (
            initialized
            and all_clear
            and NOTIFY_TRIGGER_ALL_CLEAR in enabled
            and previously_official
            and not state.get("all_clear_sent")
        ):
            if not await _async_send(
                hass,
                entry,
                subentry,
                NOTIFY_TRIGGER_ALL_CLEAR,
                display_name=entry.title,
            ):
                return
            state["all_clear_sent"] = True
        elif not all_clear:
            state.pop("all_clear_sent", None)
            if not official_active:
                state.pop("official_warning_seen", None)

        state["initialized"] = True
        store[key] = state


async def async_handle_room_notification(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    snapshot: RoomSnapshot,
) -> None:
    """Send selected notifications without warning duplication across rooms."""
    target = entry.data.get(CONF_NOTIFY_TARGET)
    if not isinstance(target, str) or not target:
        return

    configured = entry.data.get(CONF_NOTIFY_TRIGGERS, DEFAULT_NOTIFY_TRIGGERS)
    if isinstance(configured, str):
        configured = [configured]
    enabled = {str(item) for item in (configured or [])}

    await _async_handle_assistant_warning_notification(
        hass, entry, subentry, snapshot, enabled
    )

    room_configured = subentry.data.get(
        CONF_ROOM_NOTIFY_TRIGGERS, DEFAULT_ROOM_NOTIFY_TRIGGERS
    )
    if isinstance(room_configured, str):
        room_configured = [room_configured]
    room_enabled = {str(item) for item in (room_configured or [])}

    # Ordinary ventilation transitions are explicitly opt-in per room.
    result = snapshot.result
    mode = result.mode if result is not None else None
    recommendation_key = result.recommendation_key if result is not None else None
    key = f"room:{entry.entry_id}:{subentry.subentry_id}"
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_NOTIFICATION_STATE, {})
    stored = store.get(key)
    state: dict[str, Any] = dict(stored) if isinstance(stored, dict) else {}
    initialized = bool(state.get("initialized"))

    if initialized and result is not None:
        transition_trigger = _transition_trigger(
            state.get("mode"),
            state.get("recommendation_key"),
            mode,
            recommendation_key,
        )
        if transition_trigger is not None and transition_trigger in room_enabled:
            if not await _async_send(hass, entry, subentry, transition_trigger):
                return

    state["initialized"] = True
    state["mode"] = mode
    state["recommendation_key"] = recommendation_key
    store[key] = state

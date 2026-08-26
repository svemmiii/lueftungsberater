"""Optional Home Assistant notifications for Lüftungsberater."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_NOTIFY_TARGET,
    CONF_NOTIFY_TRIGGERS,
    DATA_NOTIFICATION_STATE,
    DEFAULT_NOTIFY_TRIGGERS,
    DOMAIN,
    NOTIFY_TRIGGER_AIRING_FINISHED,
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
    NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED,
    NOTIFY_TRIGGER_ALL_CLEAR,
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
) -> bool:
    """Send through Home Assistant's notify entity action."""
    target = entry.data.get(CONF_NOTIFY_TARGET)
    if not isinstance(target, str) or not target:
        return False

    title, message = _message(hass.config.language, subentry.title, trigger)
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
        _LOGGER.exception("Unable to send Lüftungsberater notification to %s", target)
        return False


def clear_room_notification_state(
    hass: HomeAssistant, entry_id: str, subentry_id: str
) -> None:
    """Forget the transient notification fingerprint for one room."""
    domain_data = hass.data.get(DOMAIN, {})
    store = domain_data.get(DATA_NOTIFICATION_STATE, {})
    store.pop(f"{entry_id}:{subentry_id}", None)


async def async_handle_room_notification(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    snapshot: RoomSnapshot,
) -> None:
    """Send selected status transitions and hazards without notification flapping."""
    target = entry.data.get(CONF_NOTIFY_TARGET)
    if not isinstance(target, str) or not target:
        return

    configured = entry.data.get(CONF_NOTIFY_TRIGGERS, DEFAULT_NOTIFY_TRIGGERS)
    if isinstance(configured, str):
        configured = [configured]
    enabled = {str(item) for item in (configured or [])}

    result = snapshot.result
    window_open = snapshot.values.get("window_open") is True
    mode = result.mode if result is not None else None
    recommendation_key = result.recommendation_key if result is not None else None
    hazard_trigger = _trigger_for_mode(mode or "")
    all_clear = snapshot.warnings.warning_notice_kind == "all_clear"

    key = f"{entry.entry_id}:{subentry.subentry_id}"
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_NOTIFICATION_STATE, {})
    stored = store.get(key)
    state: dict[str, Any] = dict(stored) if isinstance(stored, dict) else {}
    initialized = bool(state.get("initialized"))

    # Hazards may notify immediately after startup because an open window during
    # an active warning is already actionable. Ordinary status hints are only
    # transition-triggered and intentionally stay quiet on startup/reload.
    hazard_active = (
        window_open
        and hazard_trigger is not None
        and hazard_trigger in enabled
        and result is not None
    )
    if hazard_active:
        fingerprint = (
            hazard_trigger,
            result.reason_key,
            result.original_reason or "",
        )
        if state.get("hazard_fingerprint") != fingerprint:
            if not await _async_send(hass, entry, subentry, hazard_trigger):
                return
        state["hazard_fingerprint"] = fingerprint
    else:
        state.pop("hazard_fingerprint", None)

    # Optional awareness notification for users who explicitly want serious
    # official warnings even while everything is already closed. The wording
    # must make the closed state explicit to avoid implying an open window.
    closed_official_active = (
        not window_open
        and snapshot.warnings.official_close_instruction
        and result is not None
        and result.safety_lock
        and NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED in enabled
    )
    if closed_official_active:
        closed_fp = (result.reason_key, result.original_reason or "")
        if state.get("closed_official_fingerprint") != closed_fp:
            if not await _async_send(
                hass, entry, subentry, NOTIFY_TRIGGER_OFFICIAL_WARNING_CLOSED
            ):
                return
        state["closed_official_fingerprint"] = closed_fp
    else:
        state.pop("closed_official_fingerprint", None)

    if (
        initialized
        and all_clear
        and NOTIFY_TRIGGER_ALL_CLEAR in enabled
        and state.get("mode") == "nina_aussenluftgefahr"
        and not state.get("all_clear_sent")
    ):
        if not await _async_send(hass, entry, subentry, NOTIFY_TRIGGER_ALL_CLEAR):
            return
        state["all_clear_sent"] = True
    elif not all_clear:
        state.pop("all_clear_sent", None)

    if initialized and result is not None:
        transition_trigger = _transition_trigger(
            state.get("mode"),
            state.get("recommendation_key"),
            mode,
            recommendation_key,
        )
        if transition_trigger is not None and transition_trigger in enabled:
            if not await _async_send(hass, entry, subentry, transition_trigger):
                return

    state["initialized"] = True
    state["mode"] = mode
    state["recommendation_key"] = recommendation_key
    state["window_open"] = window_open
    store[key] = state

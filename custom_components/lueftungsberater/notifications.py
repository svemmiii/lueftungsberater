"""Optional status and hazard notifications for Lüftungsberater rooms."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_NOTIFY_CAUTION_VIBRATION,
    CONF_NOTIFY_CRITICAL_BYPASS,
    CONF_NOTIFY_DANGER_VIBRATION,
    CONF_NOTIFY_MOBILE_SERVICE,
    CONF_NOTIFY_TARGET,
    CONF_NOTIFY_TRIGGERS,
    DATA_NOTIFICATION_STATE,
    DEFAULT_NOTIFY_CAUTION_VIBRATION,
    DEFAULT_NOTIFY_CRITICAL_BYPASS,
    DEFAULT_NOTIFY_DANGER_VIBRATION,
    DEFAULT_NOTIFY_TRIGGERS,
    DOMAIN,
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_AIRING_FINISHED,
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
    NOTIFY_VIBRATION_GENTLE,
    NOTIFY_VIBRATION_NORMAL,
    NOTIFY_VIBRATION_OFF,
    NOTIFY_VIBRATION_STRONG,
)
from .localization import normalize_language
from .runtime import RoomSnapshot

_LOGGER = logging.getLogger(__name__)

_INFO_TRIGGERS = {
    NOTIFY_TRIGGER_AIRING_RECOMMENDED,
    NOTIFY_TRIGGER_AIRING_FINISHED,
}
_CAUTION_TRIGGERS = {
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
}
_DANGER_TRIGGERS = {
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_WEATHER_DANGER,
}

_VIBRATION_PATTERNS = {
    NOTIFY_VIBRATION_GENTLE: "0, 150",
    NOTIFY_VIBRATION_NORMAL: "0, 300, 120, 300",
    NOTIFY_VIBRATION_STRONG: "0, 500, 150, 500, 150, 800",
}


def _trigger_for_mode(mode: str) -> str | None:
    """Map explicit warning modes to notification categories."""
    return {
        "nina_aussenluftgefahr": NOTIFY_TRIGGER_AIR_DANGER,
        "nina_vorsicht": NOTIFY_TRIGGER_AIR_CAUTION,
        "wettergefahr": NOTIFY_TRIGGER_WEATHER_DANGER,
        "wetter_vorsicht": NOTIFY_TRIGGER_WEATHER_CAUTION,
    }.get(mode)


def _transition_trigger(
    previous_mode: str | None,
    previous_recommendation_key: str | None,
    mode: str | None,
    recommendation_key: str | None,
) -> str | None:
    """Return a quiet status trigger only for a genuine state transition."""
    if mode == "lueftung_fertig" and previous_mode != "lueftung_fertig":
        return NOTIFY_TRIGGER_AIRING_FINISHED
    if recommendation_key == "open_now" and previous_recommendation_key != "open_now":
        return NOTIFY_TRIGGER_AIRING_RECOMMENDED
    return None


def _message(language: str, room: str, trigger: str) -> tuple[str, str]:
    """Return localized notification title and body."""
    lang = normalize_language(language)
    titles = {
        "de": f"Lüftungsberater · {room}",
        "en": f"Ventilation Advisor · {room}",
        "tr": f"Havalandırma Danışmanı · {room}",
    }
    messages = {
        "de": {
            NOTIFY_TRIGGER_AIRING_RECOMMENDED: f"In {room} ist Lüften jetzt wieder sinnvoll. Du kannst die Fenster öffnen.",
            NOTIFY_TRIGGER_AIRING_FINISHED: f"In {room} kannst du das Lüften jetzt beenden und die Fenster wieder schließen.",
            NOTIFY_TRIGGER_AIR_DANGER: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl eine ernste Warnung zur Außenluft aktiv ist. Bitte schließe sie.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl für die Außenluft ein Vorsichtshinweis gilt. Prüfe bitte, ob du schließen möchtest.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl eine Unwetterlage erkannt wurde. Bitte prüfe und schließe es bei Bedarf.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl eine Wetterwarnung aktiv ist. Behalte die Situation bitte im Blick.",
        },
        "en": {
            NOTIFY_TRIGGER_AIRING_RECOMMENDED: f"Opening the windows in {room} is useful again. You can air the room now.",
            NOTIFY_TRIGGER_AIRING_FINISHED: f"You can finish airing {room} now and close the windows again.",
            NOTIFY_TRIGGER_AIR_DANGER: f"A window or door in {room} is still open while a serious outdoor-air warning is active. Please close it.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"A window or door in {room} is still open while an outdoor-air advisory is active. Please check whether it should be closed.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"A window or door in {room} is still open while severe weather is active. Please check it and close it if needed.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"A window or door in {room} is still open while a weather warning is active. Please keep an eye on the situation.",
        },
        "tr": {
            NOTIFY_TRIGGER_AIRING_RECOMMENDED: f"{room} odasını havalandırmak yeniden uygun. Pencereleri şimdi açabilirsin.",
            NOTIFY_TRIGGER_AIRING_FINISHED: f"{room} odasını havalandırmayı şimdi bitirip pencereleri yeniden kapatabilirsin.",
            NOTIFY_TRIGGER_AIR_DANGER: f"{room} odasında bir pencere veya kapı hâlâ açıkken dış hava için ciddi bir uyarı aktif. Lütfen kapat.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"{room} odasında bir pencere veya kapı hâlâ açıkken dış hava için bir dikkat uyarısı aktif. Kapatmanın gerekip gerekmediğini kontrol et.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"{room} odasında bir pencere veya kapı hâlâ açıkken şiddetli hava koşulları algılandı. Lütfen kontrol edip gerekirse kapat.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"{room} odasında bir pencere veya kapı hâlâ açıkken hava durumu uyarısı aktif. Lütfen durumu takip et.",
        },
    }
    return titles[lang], messages[lang][trigger]


def _vibration_pattern(value: str) -> str | None:
    return _VIBRATION_PATTERNS.get(value)


def _mobile_payload(
    trigger: str,
    room_key: str,
    caution_vibration: str = DEFAULT_NOTIFY_CAUTION_VIBRATION,
    danger_vibration: str = DEFAULT_NOTIFY_DANGER_VIBRATION,
    critical_bypass: bool = DEFAULT_NOTIFY_CRITICAL_BYPASS,
) -> dict[str, Any]:
    """Build one cross-platform Companion App payload.

    Android uses notification channels and vibration patterns. iOS ignores
    those Android-only keys and uses the push interruption level instead.
    """
    if trigger in _INFO_TRIGGERS:
        return {
            "tag": f"lueftungsberater_{room_key}_status",
            "channel": "Lüftungsberater · Hinweise",
            "importance": "low",
            "alert_once": True,
            "push": {
                "interruption-level": "passive",
                "sound": "none",
            },
            "presentation_options": ["alert", "badge"],
        }

    if trigger in _CAUTION_TRIGGERS:
        vibration = caution_vibration
        payload: dict[str, Any] = {
            "tag": f"lueftungsberater_{room_key}_hazard",
            "channel": f"Lüftungsberater · Vorsicht · {vibration}",
            "importance": "default",
            "push": {"interruption-level": "active"},
        }
    else:
        vibration = danger_vibration
        payload = {
            "tag": f"lueftungsberater_{room_key}_hazard",
            "channel": f"Lüftungsberater · Gefahr · {vibration}",
            "importance": "high",
            "priority": "high",
            "ttl": 0,
            "push": {"interruption-level": "active"},
        }
        if critical_bypass:
            payload["channel"] = f"Lüftungsberater · Kritisch · {vibration}"
            payload["importance"] = "max"
            payload["push"] = {
                "interruption-level": "critical",
                "sound": {
                    "name": "default",
                    "critical": 1,
                    "volume": 1.0,
                },
            }

    pattern = _vibration_pattern(vibration)
    if pattern is not None:
        payload["vibrationPattern"] = pattern
    return payload


async def _async_clear_mobile_tag(
    hass: HomeAssistant, entry: ConfigEntry, tag: str
) -> None:
    """Best-effort removal of a stale Companion App notification."""
    mobile_service = entry.data.get(CONF_NOTIFY_MOBILE_SERVICE)
    if not isinstance(mobile_service, str) or not mobile_service:
        return
    service = mobile_service.removeprefix("notify.")
    try:
        await hass.services.async_call(
            "notify",
            service,
            {"message": "clear_notification", "data": {"tag": tag}},
            blocking=False,
        )
    except Exception:  # noqa: BLE001 - stale phone UI must not break advice
        _LOGGER.debug("Unable to clear Lüftungsberater notification tag %s", tag)


async def _async_send(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    trigger: str,
) -> bool:
    """Send through Companion App when configured, otherwise generic notify."""
    target = entry.data.get(CONF_NOTIFY_TARGET)
    mobile_service = entry.data.get(CONF_NOTIFY_MOBILE_SERVICE)
    title, message = _message(hass.config.language, subentry.title, trigger)

    try:
        if isinstance(mobile_service, str) and mobile_service:
            service = mobile_service.removeprefix("notify.")
            payload = _mobile_payload(
                trigger,
                subentry.subentry_id,
                str(
                    entry.data.get(
                        CONF_NOTIFY_CAUTION_VIBRATION,
                        DEFAULT_NOTIFY_CAUTION_VIBRATION,
                    )
                ),
                str(
                    entry.data.get(
                        CONF_NOTIFY_DANGER_VIBRATION,
                        DEFAULT_NOTIFY_DANGER_VIBRATION,
                    )
                ),
                bool(
                    entry.data.get(
                        CONF_NOTIFY_CRITICAL_BYPASS,
                        DEFAULT_NOTIFY_CRITICAL_BYPASS,
                    )
                ),
            )
            await hass.services.async_call(
                "notify",
                service,
                {"message": message, "title": title, "data": payload},
                blocking=False,
            )
            return True

        if isinstance(target, str) and target:
            await hass.services.async_call(
                "notify",
                "send_message",
                {"message": message, "title": title},
                target={"entity_id": target},
                blocking=False,
            )
            return True
    except Exception:  # noqa: BLE001 - a notification target must not break advice
        destination = mobile_service or target
        _LOGGER.exception("Unable to send Lüftungsberater notification to %s", destination)
        return False

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
    mobile_service = entry.data.get(CONF_NOTIFY_MOBILE_SERVICE)
    if not (isinstance(target, str) and target) and not (
        isinstance(mobile_service, str) and mobile_service
    ):
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

    key = f"{entry.entry_id}:{subentry.subentry_id}"
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_NOTIFICATION_STATE, {})
    stored = store.get(key)
    state: dict[str, Any] = dict(stored) if isinstance(stored, dict) else {}
    initialized = bool(state.get("initialized"))

    # Hazards are allowed to notify immediately after startup because an open
    # window during an active danger is already actionable. Status hints below
    # are edge-triggered and intentionally stay quiet on startup/reload.
    hazard_active = (
        window_open
        and hazard_trigger is not None
        and hazard_trigger in enabled
        and result is not None
    )
    if initialized and not hazard_active and state.get("hazard_fingerprint") is not None:
        await _async_clear_mobile_tag(
            hass, entry, f"lueftungsberater_{subentry.subentry_id}_hazard"
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

    if initialized and result is not None:
        transition_trigger = _transition_trigger(
            state.get("mode"),
            state.get("recommendation_key"),
            mode,
            recommendation_key,
        )

        previous_status_visible = (
            state.get("recommendation_key") == "open_now"
            or state.get("mode") == "lueftung_fertig"
        )
        current_status_visible = (
            recommendation_key == "open_now" or mode == "lueftung_fertig"
        )
        if previous_status_visible and not current_status_visible:
            await _async_clear_mobile_tag(
                hass, entry, f"lueftungsberater_{subentry.subentry_id}_status"
            )

        if transition_trigger is not None and transition_trigger in enabled:
            if not await _async_send(hass, entry, subentry, transition_trigger):
                return

    state["initialized"] = True
    state["mode"] = mode
    state["recommendation_key"] = recommendation_key
    state["window_open"] = window_open
    store[key] = state

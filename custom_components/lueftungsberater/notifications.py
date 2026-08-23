"""Optional urgent notifications for open windows during warning situations."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_NOTIFY_TARGET,
    CONF_NOTIFY_TRIGGERS,
    DATA_NOTIFICATION_STATE,
    DEFAULT_NOTIFY_TRIGGERS,
    DOMAIN,
    NOTIFY_TRIGGER_AIR_CAUTION,
    NOTIFY_TRIGGER_AIR_DANGER,
    NOTIFY_TRIGGER_WEATHER_CAUTION,
    NOTIFY_TRIGGER_WEATHER_DANGER,
)
from .localization import normalize_language
from .runtime import RoomSnapshot

_LOGGER = logging.getLogger(__name__)


def _trigger_for_mode(mode: str) -> str | None:
    return {
        "nina_aussenluftgefahr": NOTIFY_TRIGGER_AIR_DANGER,
        "nina_vorsicht": NOTIFY_TRIGGER_AIR_CAUTION,
        "wettergefahr": NOTIFY_TRIGGER_WEATHER_DANGER,
        "wetter_vorsicht": NOTIFY_TRIGGER_WEATHER_CAUTION,
    }.get(mode)


def _message(language: str, room: str, trigger: str) -> tuple[str, str]:
    lang = normalize_language(language)
    titles = {
        "de": f"Lüftungsberater · {room}",
        "en": f"Ventilation Advisor · {room}",
        "tr": f"Havalandırma Danışmanı · {room}",
    }
    messages = {
        "de": {
            NOTIFY_TRIGGER_AIR_DANGER: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl eine ernste Warnung zur Außenluft aktiv ist. Bitte schließe sie.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl für die Außenluft ein Vorsichtshinweis gilt. Prüfe bitte, ob du schließen möchtest.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl eine Unwetterlage erkannt wurde. Bitte prüfe und schließe es bei Bedarf.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"In {room} ist noch ein Fenster oder eine Tür offen, obwohl eine Wetterwarnung aktiv ist. Behalte die Situation bitte im Blick.",
        },
        "en": {
            NOTIFY_TRIGGER_AIR_DANGER: f"A window or door in {room} is still open while a serious outdoor-air warning is active. Please close it.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"A window or door in {room} is still open while an outdoor-air advisory is active. Please check whether it should be closed.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"A window or door in {room} is still open while severe weather is active. Please check it and close it if needed.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"A window or door in {room} is still open while a weather warning is active. Please keep an eye on the situation.",
        },
        "tr": {
            NOTIFY_TRIGGER_AIR_DANGER: f"{room} odasında bir pencere veya kapı hâlâ açıkken dış hava için ciddi bir uyarı aktif. Lütfen kapat.",
            NOTIFY_TRIGGER_AIR_CAUTION: f"{room} odasında bir pencere veya kapı hâlâ açıkken dış hava için bir dikkat uyarısı aktif. Kapatmanın gerekip gerekmediğini kontrol et.",
            NOTIFY_TRIGGER_WEATHER_DANGER: f"{room} odasında bir pencere veya kapı hâlâ açıkken şiddetli hava koşulları algılandı. Lütfen kontrol edip gerekirse kapat.",
            NOTIFY_TRIGGER_WEATHER_CAUTION: f"{room} odasında bir pencere veya kapı hâlâ açıkken hava durumu uyarısı aktif. Lütfen durumu takip et.",
        },
    }
    return titles[lang], messages[lang][trigger]


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
    """Send at most one notification per active incident/window-open cycle."""
    target = entry.data.get(CONF_NOTIFY_TARGET)
    if not isinstance(target, str) or not target:
        return

    configured = entry.data.get(CONF_NOTIFY_TRIGGERS, DEFAULT_NOTIFY_TRIGGERS)
    if isinstance(configured, str):
        configured = [configured]
    enabled = {str(item) for item in (configured or [])}

    result = snapshot.result
    window_open = snapshot.values.get("window_open") is True
    trigger = _trigger_for_mode(result.mode) if result is not None else None
    key = f"{entry.entry_id}:{subentry.subentry_id}"
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_NOTIFICATION_STATE, {})

    if not window_open or trigger is None or trigger not in enabled:
        store.pop(key, None)
        return

    fingerprint = (trigger, result.reason_key, result.original_reason or "")
    if store.get(key) == fingerprint:
        return

    title, message = _message(hass.config.language, subentry.title, trigger)
    try:
        await hass.services.async_call(
            "notify",
            "send_message",
            {"message": message, "title": title},
            target={"entity_id": target},
            blocking=False,
        )
    except Exception:  # noqa: BLE001 - a notification target must not break advice
        _LOGGER.exception("Unable to send Lüftungsberater notification to %s", target)
        return

    store[key] = fingerprint

"""Shared display payloads for node replies and directly connected stations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DISPLAY_MODE,
    DEFAULT_DISPLAY_MODE,
    DISPLAY_MODE_ROOM_AIR,
    SUBENTRY_TYPE_ROOM,
)
from .localization import recommendation_text

if TYPE_CHECKING:
    from .runtime import RoomSnapshot


def hardware_display_payload(
    hass: HomeAssistant,
    entry: ConfigEntry,
    room_id: str,
    *,
    snapshot: RoomSnapshot | None = None,
) -> dict[str, Any]:
    """Build the one canonical ESP display payload for a configured room.

    Both ``lueftungsberater.hardware_report`` (ESP-NOW nodes) and the direct
    ESPHome display-return channel use this helper. Keep all display semantics in
    one place so direct standalone/master displays cannot drift from node output.
    """
    room = entry.subentries.get(room_id)
    if room is None or room.subentry_type != SUBENTRY_TYPE_ROOM:
        return {
            "room_name": None,
            "status": None,
            "recommendation": None,
            "recommendation_key": None,
            "display_mode": entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE),
            "safety_lock": False,
        }

    if snapshot is None:
        # Lazy import avoids a coordinator -> display -> coordinator import cycle.
        from .coordinator import get_room_coordinator

        coordinator = get_room_coordinator(hass, entry, room)
        snapshot = coordinator.data if coordinator is not None else None

    display_mode = entry.data.get(CONF_DISPLAY_MODE, DEFAULT_DISPLAY_MODE)
    if snapshot is None or snapshot.result is None:
        return {
            "room_name": str(room.title),
            "status": "yellow",
            "recommendation": recommendation_text("unknown", hass.config.language),
            "recommendation_key": "unknown",
            "display_mode": display_mode,
            "safety_lock": False,
        }

    result = snapshot.result
    room_view = display_mode == DISPLAY_MODE_ROOM_AIR and not result.safety_lock
    recommendation_key = (
        result.room_recommendation_key if room_view else result.recommendation_key
    )
    status = (
        "locked"
        if result.safety_lock
        else (result.room_status_color if room_view else result.color)
    )
    return {
        "room_name": str(room.title),
        "status": status,
        "recommendation": recommendation_text(
            recommendation_key, hass.config.language
        ),
        "recommendation_key": recommendation_key,
        "display_mode": display_mode,
        "safety_lock": bool(result.safety_lock),
    }

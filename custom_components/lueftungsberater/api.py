"""Small authenticated API used by the overview card and remote peers."""
from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any
import time

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.http import KEY_HASS, HomeAssistantView
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later

from .const import (
    DATA_API_REGISTERED,
    DATA_REMOTE_ACCESS,
    CONF_REMOTE_ROOM_SHARE,
    DOMAIN,
    ENTRY_KIND_LOCAL,
    ENTRY_KIND_REMOTE,
    REMOTE_PROTOCOL_VERSION,
    SUBENTRY_TYPE_ROOM,
    entry_kind,
)
from .localization import (
    duration_text,
    night_advice_text,
    reason_text,
    recommendation_text,
)
from .remote import _ip_is_tailscale, get_remote_coordinator

REMOTE_ATTRIBUTE_KEYS = {
    "room_name",
    "status",
    "display_mode",
    "recommendation",
    "recommendation_key",
    "mode",
    "reason",
    "reason_key",
    "reason_args",
    "duration",
    "duration_key",
    "co2_status",
    "co2_data_status",
    "co2_ppm",
    "temperature_inside",
    "temperature_outside",
    "target_temperature",
    "temperature_display_unit",
    "humidity_inside",
    "humidity_outside",
    "absolute_humidity_inside",
    "absolute_humidity_outside",
    "absolute_humidity_difference",
    "surface_temperature",
    "surface_relative_humidity",
    "mold_risk",
    "mold_persistent",
    "mold_current_critical_minutes",
    "mold_critical_minutes_24h",
    "air_quality",
    "air_quality_pollutant",
    "air_quality_value",
    "air_quality_values",
    "wind_speed_kmh",
    "wind_gust_kmh",
    "rain_minutes_until",
    "short_term_weather_change",
    "short_term_weather_kind",
    "short_term_weather_minutes",
    "night_ventilation_status",
    "night_ventilation_key",
    "night_ventilation_args",
    "warning_notice_kind",
    "warning_notice_text",
    "official_close_instruction",
    "has_co2",
    "has_window_contacts",
    "window_open",
    "open_minutes",
    "hours_since_last_airing",
    "outdoor_temperature_source",
    "outdoor_humidity_source",
}


class LueftungsberaterSnapshotView(HomeAssistantView):
    """Expose only current local Lüftungsberater room snapshots."""

    url = "/api/lueftungsberater/snapshot"
    name = "api:lueftungsberater:snapshot"
    requires_auth = True

    async def get(self, request):
        # Authentication is necessary but not sufficient for this endpoint: remote
        # snapshots are intentionally available only across a real Tailscale path.
        # The client also validates the destination before every request, making the
        # restriction bidirectional instead of merely a config-flow convention.
        if not request.remote or not _ip_is_tailscale(str(request.remote)):
            return self.json_message(
                "Tailscale connection required",
                status_code=HTTPStatus.FORBIDDEN,
            )

        hass: HomeAssistant = request.app[KEY_HASS]
        requested_unit = request.query.get(
            "temperature_unit",
            str(hass.config.units.temperature_unit),
        )
        if requested_unit not in {"°C", "°F"}:
            requested_unit = str(hass.config.units.temperature_unit)
        discovery = request.query.get("discovery") == "1"
        selected_param = request.query.get("rooms")
        selected_room_keys: set[str] | None
        if discovery or selected_param is None:
            selected_room_keys = None
        else:
            selected_room_keys = {
                item for item in str(selected_param).split(",") if item
            }

        instances = _local_instances(
            hass,
            requested_unit,
            remote_export=True,
            selected_room_keys=selected_room_keys,
        )

        if not discovery:
            client_id = str(request.query.get("client_id") or "legacy")
            client_name = str(request.query.get("client_name") or "Remote Home Assistant")
            _record_remote_access(hass, instances, client_id, client_name)

        return self.json(
            {
                "protocol": REMOTE_PROTOCOL_VERSION,
                "home_assistant_name": hass.config.location_name,
                "instances": instances,
            }
        )


def _record_remote_access(
    hass: HomeAssistant,
    instances: list[dict[str, Any]],
    client_id: str,
    client_name: str,
) -> None:
    """Remember which rooms were actually requested by a remote client."""
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_REMOTE_ACCESS, {})
    now = time.monotonic()
    for instance in instances:
        instance_id = str(instance.get("id") or "")
        rooms = instance.get("rooms", [])
        if not instance_id or not isinstance(rooms, list):
            continue
        for room in rooms:
            if not isinstance(room, dict):
                continue
            room_id = str(room.get("id") or "")
            if not room_id:
                continue
            key = f"{instance_id}:{room_id}"
            clients = store.setdefault(key, {})
            previous = clients.get(client_id)
            if isinstance(previous, dict):
                cancel = previous.get("cancel_expiry")
                if callable(cancel):
                    cancel()

            def _expire(_now, *, _key=key, _client_id=client_id, _instance_id=instance_id, _room_id=room_id):
                current_store = hass.data.get(DOMAIN, {}).get(DATA_REMOTE_ACCESS, {})
                current_clients = current_store.get(_key, {})
                if isinstance(current_clients, dict):
                    current_clients.pop(_client_id, None)
                    if not current_clients:
                        current_store.pop(_key, None)
                _refresh_remote_access_entity(hass, _instance_id, _room_id)

            cancel_expiry = async_call_later(hass, 95, _expire)
            clients[client_id] = {
                "name": client_name,
                "last_seen": now,
                "cancel_expiry": cancel_expiry,
            }
            _refresh_remote_access_entity(hass, instance_id, room_id)


def _refresh_remote_access_entity(
    hass: HomeAssistant,
    instance_id: str,
    room_id: str,
) -> None:
    """Refresh only the room entity metadata after remote access changes."""
    entry = hass.config_entries.async_get_entry(instance_id)
    if entry is None:
        return
    subentry = entry.subentries.get(room_id)
    if subentry is None:
        return
    # Lazy import avoids making the API module part of the coordinator's import
    # graph during Home Assistant startup.
    from .coordinator import get_room_coordinator

    coordinator = get_room_coordinator(hass, entry, subentry)
    if coordinator is not None and coordinator.data is not None:
        coordinator.async_set_updated_data(coordinator.data)


def remote_access_info(
    hass: HomeAssistant,
    instance_id: str,
    room_id: str,
    *,
    max_age_seconds: float = 90.0,
) -> tuple[bool, list[str]]:
    """Return active remote access and client names for one room."""
    store = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_REMOTE_ACCESS, {})
    key = f"{instance_id}:{room_id}"
    clients = store.get(key)
    if not isinstance(clients, dict):
        return False, []
    now = time.monotonic()
    active: list[str] = []
    stale: list[str] = []
    for client_id, info in clients.items():
        if not isinstance(info, dict):
            stale.append(client_id)
            continue
        try:
            age = now - float(info.get("last_seen", 0))
        except (TypeError, ValueError):
            stale.append(client_id)
            continue
        if age <= max_age_seconds:
            active.append(str(info.get("name") or client_id))
        else:
            stale.append(client_id)
    for client_id in stale:
        clients.pop(client_id, None)
    if not clients:
        store.pop(key, None)
    return bool(active), sorted(set(active))


def _advisor_entity_id(
    hass: HomeAssistant,
    subentry_id: str,
) -> str | None:
    registry = er.async_get(hass)
    return registry.async_get_entity_id(
        "sensor",
        DOMAIN,
        f"{subentry_id}_advisor",
    )


def _export_attributes(
    attributes: Mapping[str, Any],
    temperature_unit: str,
    *,
    remote_export: bool,
) -> dict[str, Any]:
    attrs = dict(attributes)
    attrs["temperature_display_unit"] = temperature_unit

    if remote_export:
        # Remote cards are intentionally read-only and current-only. Export a
        # strict allow-list rather than leaking unrelated HA entity IDs, provider
        # metadata, or original warning payloads to the receiving installation.
        attrs = {
            key: value
            for key, value in attrs.items()
            if key in REMOTE_ATTRIBUTE_KEYS
        }
    return attrs


def _local_instances(
    hass: HomeAssistant,
    temperature_unit: str,
    *,
    remote_export: bool,
    selected_room_keys: set[str] | None = None,
) -> list[dict[str, Any]]:
    instances: list[dict[str, Any]] = []

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_kind(entry) != ENTRY_KIND_LOCAL:
            continue

        rooms: list[dict[str, Any]] = []
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
                continue
            room_key = f"{entry.entry_id}:{subentry.subentry_id}"
            if remote_export:
                # v0.6.x rooms had no explicit flag; keep them shared for
                # backwards compatibility. Newly created v0.7 rooms store False
                # unless the user explicitly enables remote sharing.
                if subentry.data.get(CONF_REMOTE_ROOM_SHARE, True) is not True:
                    continue
                if selected_room_keys is not None and room_key not in selected_room_keys:
                    continue
            entity_id = _advisor_entity_id(hass, subentry.subentry_id)
            state = hass.states.get(entity_id) if entity_id else None
            if state is None and not remote_export:
                continue

            if state is None:
                # The room configuration is still useful metadata even when its
                # entities are not loaded or its sensor hardware is absent. Remote
                # overviews therefore keep the user-defined room name instead of
                # falling back to generic "Room 1" labels.
                attributes: dict[str, Any] = {
                    "instance_id": entry.entry_id,
                    "instance_name": entry.title,
                    "room_name": subentry.title,
                    "status": "yellow",
                    "recommendation_key": "unknown",
                    "mode": "incomplete_data",
                    "reason_key": "incomplete_data",
                    "reason_args": {},
                    "duration_key": "incomplete_data",
                    "window_open": False,
                    "has_window_contacts": bool(subentry.data.get("window_entities")),
                    "has_co2": bool(subentry.data.get("co2_entity")),
                }
                room_state = "unknown"
            else:
                attributes = dict(state.attributes)
                room_state = state.state

            rooms.append(
                {
                    "id": subentry.subentry_id,
                    "name": subentry.title,
                    "entity_id": None if remote_export else entity_id,
                    "state": room_state,
                    "attributes": _export_attributes(
                        attributes,
                        temperature_unit,
                        remote_export=remote_export,
                    ),
                }
            )

        instances.append(
            {
                "id": entry.entry_id,
                "name": entry.title,
                "available": True,
                "remote": False,
                "rooms": rooms,
            }
        )

    return instances


def _remote_instances(hass: HomeAssistant) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_kind(entry) != ENTRY_KIND_REMOTE:
            continue
        coordinator = get_remote_coordinator(hass, entry.entry_id)
        data = coordinator.data if coordinator is not None else None

        if data is None or not data.available:
            groups.append(
                {
                    "id": f"remote:{entry.entry_id}",
                    "name": entry.title,
                    "available": False,
                    "remote": True,
                    "rooms": [],
                }
            )
            continue

        upstream = list(data.instances)
        if not upstream:
            groups.append(
                {
                    "id": f"remote:{entry.entry_id}",
                    "name": entry.title,
                    "available": True,
                    "remote": True,
                    "rooms": [],
                }
            )
            continue

        for remote_instance in upstream:
            source_name = str(remote_instance.get("name") or "Lüftungsassistent")
            display_name = (
                entry.title
                if len(upstream) == 1
                else f"{entry.title} · {source_name}"
            )
            rooms = remote_instance.get("rooms")
            if not isinstance(rooms, list):
                rooms = []
            groups.append(
                {
                    "id": f"remote:{entry.entry_id}:{remote_instance.get('id', source_name)}",
                    "name": display_name,
                    "available": True,
                    "remote": True,
                    "rooms": rooms,
                }
            )

    return groups


@websocket_api.websocket_command(
    {
        vol.Required("type"): "lueftungsberater/localize",
        vol.Required("language"): str,
        vol.Required("temperature_unit"): str,
        vol.Required("recommendation_key"): str,
        vol.Required("reason_key"): str,
        vol.Optional("reason_args", default={}): dict,
        vol.Required("duration_key"): str,
        vol.Optional("night_ventilation_key"): vol.Any(str, None),
        vol.Optional("night_ventilation_args", default={}): dict,
    }
)
@callback
def websocket_localize(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Render one semantic card-text bundle in the requesting UI language."""
    language = str(msg["language"] or "en")
    temperature_unit = str(msg["temperature_unit"] or hass.config.units.temperature_unit)
    recommendation_key = str(msg["recommendation_key"])
    reason_key = str(msg["reason_key"])
    duration_key = str(msg["duration_key"])
    reason_args = msg.get("reason_args") if isinstance(msg.get("reason_args"), dict) else {}
    night_key = msg.get("night_ventilation_key")
    night_args = (
        msg.get("night_ventilation_args")
        if isinstance(msg.get("night_ventilation_args"), dict)
        else {}
    )
    connection.send_result(
        msg["id"],
        {
            "recommendation": recommendation_text(recommendation_key, language),
            "reason": reason_text(reason_key, reason_args, language, temperature_unit),
            "duration": duration_text(duration_key, language),
            "night": night_advice_text(
                str(night_key) if isinstance(night_key, str) else None,
                night_args,
                language,
                temperature_unit,
            ),
        },
    )


@websocket_api.websocket_command(
    {vol.Required("type"): "lueftungsberater/remote_overview"}
)
@callback
def websocket_remote_overview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return only cached remote snapshots to the local frontend."""
    connection.send_result(msg["id"], _remote_instances(hass))


@callback
def async_register_api(hass: HomeAssistant) -> None:
    """Register API endpoints once for this Home Assistant instance."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_API_REGISTERED):
        return
    domain_data[DATA_API_REGISTERED] = True
    hass.http.register_view(LueftungsberaterSnapshotView())
    websocket_api.async_register_command(hass, websocket_localize)
    websocket_api.async_register_command(hass, websocket_remote_overview)

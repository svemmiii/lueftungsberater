"""Small authenticated API used by the overview card and remote peers."""
from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.http import KEY_HASS, HomeAssistantView
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import (
    DATA_API_REGISTERED,
    DOMAIN,
    ENTRY_KIND_LOCAL,
    ENTRY_KIND_REMOTE,
    REMOTE_PROTOCOL_VERSION,
    SUBENTRY_TYPE_ROOM,
    entry_kind,
)
from .localization import localized_bundle
from .remote import _ip_is_tailscale, get_remote_coordinator

REMOTE_ATTRIBUTE_KEYS = {
    "room_name",
    "status",
    "recommendation",
    "recommendation_key",
    "mode",
    "reason",
    "reason_key",
    "reason_args",
    "duration",
    "duration_key",
    "localized_texts",
    "co2_status",
    "co2_data_status",
    "co2_ppm",
    "temperature_inside",
    "temperature_outside",
    "target_temperature",
    "temperature_unit_internal",
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
        return self.json(
            {
                "protocol": REMOTE_PROTOCOL_VERSION,
                "home_assistant_name": hass.config.location_name,
                "instances": _local_instances(hass, requested_unit, remote_export=True),
            }
        )


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

    recommendation_key = attrs.get("recommendation_key")
    reason_key = attrs.get("reason_key")
    duration_key = attrs.get("duration_key")
    reason_args = attrs.get("reason_args")
    if (
        isinstance(recommendation_key, str)
        and isinstance(reason_key, str)
        and isinstance(duration_key, str)
        and isinstance(reason_args, dict)
    ):
        attrs["localized_texts"] = localized_bundle(
            recommendation_key,
            reason_key,
            reason_args,
            duration_key,
            temperature_unit,
        )

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
) -> list[dict[str, Any]]:
    instances: list[dict[str, Any]] = []

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_kind(entry) != ENTRY_KIND_LOCAL:
            continue

        rooms: list[dict[str, Any]] = []
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
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
            source_name = str(remote_instance.get("name") or "Lüftungsberater")
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
    websocket_api.async_register_command(hass, websocket_remote_overview)

"""Small authenticated API used by the overview card and remote peers."""
from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any
import json
import secrets
import time

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.http import KEY_HASS, KEY_HASS_USER, HomeAssistantView
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.instance_id import async_get as async_get_instance_id

from .const import (
    DATA_API_REGISTERED,
    DATA_HARDWARE_SERVICE_REGISTERED,
    DATA_REMOTE_ACCESS,
    CONF_REMOTE_ROOM_SHARE,
    DOMAIN,
    ENTRY_KIND_LOCAL,
    ENTRY_KIND_REMOTE,
    REMOTE_PROTOCOL_VERSION,
    SUBENTRY_TYPE_ROOM,
    CONF_HARDWARE_ID,
    CONF_HARDWARE_ROOM_ID,
    CONF_HARDWARE_MASTER_SUBENTRY_ID,
    CONF_HARDWARE_MASTER_SECRET,
    CONF_HARDWARE_CONNECTION_TYPE,
    CONF_HARDWARE_LOCATION_MODE,
    CONF_HARDWARE_WG_ADDRESS,
    CONF_HARDWARE_WG_PRIVATE_KEY,
    CONF_HARDWARE_WG_PEER_PUBLIC_KEY,
    CONF_HARDWARE_WG_PRESHARED_KEY,
    CONF_HARDWARE_WG_ENDPOINT,
    CONF_HARDWARE_WG_ENDPOINT_HOST,
    CONF_HARDWARE_WG_ENDPOINT_PORT,
    CONF_HARDWARE_WG_ALLOWED_IPS,
    CONF_HARDWARE_WG_KEEPALIVE,
    HARDWARE_ROLE_MASTER,
    HARDWARE_ROLE_NODE,
    HARDWARE_LOCATION_LOCAL,
    HARDWARE_LOCATION_REMOTE,
    CONF_DISPLAY_MODE,
    DEFAULT_DISPLAY_MODE,
    DISPLAY_MODE_ROOM_AIR,
    entry_kind,
)
from .hardware_hub import (
    configured_master_for_station,
    configured_master_hardware_id,
    hardware_id_matches,
    remember_discovery,
    report_station,
    station_by_any_hardware_id,
    station_by_hardware_id,
    station_role,
    station_subentries,
    station_topology_error,
)
from .coordinator import get_room_coordinator
from .localization import (
    duration_text,
    night_advice_text,
    reason_text,
    recommendation_text,
)
from .remote import _ip_is_tailscale, get_remote_coordinator

REMOTE_CLIENT_ID_MAX_LENGTH = 128
REMOTE_CLIENT_NAME_MAX_LENGTH = 128
REMOTE_CLIENTS_PER_ROOM_MAX = 32

SERVICE_HARDWARE_REPORT = "hardware_report"

_CORRELATION_ID = vol.All(vol.Coerce(int), vol.Range(min=0, max=0xFFFFFFFF))
HARDWARE_REPORT_ACTION_SCHEMA = vol.Schema(
    {
        vol.Required("hardware_id"): str,
        # New native-API masters must identify themselves explicitly. HA still
        # resolves and validates the configured master relationship; this value
        # is never allowed to choose a master on its own.
        vol.Required("master_id"): str,
        vol.Required("master_secret"): vol.All(str, vol.Length(min=32, max=128)),
        vol.Optional("co2"): vol.Coerce(float),
        vol.Optional("temperature"): vol.Coerce(float),
        vol.Optional("humidity"): vol.Coerce(float),
        vol.Optional("rssi"): vol.Coerce(int),
        vol.Optional("hops"): vol.Coerce(int),
        vol.Optional("latency_ms"): vol.Coerce(int),
        vol.Optional("retries"): vol.Coerce(int),
        vol.Optional("firmware"): str,
        vol.Optional("online"): cv.boolean,
        vol.Required("round_id"): _CORRELATION_ID,
        vol.Required("request_id"): _CORRELATION_ID,
    },
    extra=vol.PREVENT_EXTRA,
)


class _HardwareReportRejected(Exception):
    """A known station report was rejected by HA-owned topology checks."""


def _normalize_remote_client_value(value: Any, fallback: str, max_length: int) -> str:
    text = str(value or fallback).strip()[:max_length]
    return text or fallback


REMOTE_ATTRIBUTE_KEYS = {
    "availability",
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
    "indoor_air_quality",
    "indoor_air_quality_pollutant",
    "indoor_air_quality_value",
    "indoor_air_quality_values",
    "indoor_air_quality_baseline_value",
    "indoor_air_quality_typical",
    "indoor_air_quality_unusual",
    "indoor_air_quality_trend",
    "indoor_air_quality_history_samples",
    "wind_speed_kmh",
    "wind_gust_kmh",
    "rain_minutes_until",
    "short_term_weather_change",
    "short_term_weather_kind",
    "short_term_weather_minutes",
    "forecast_data_status",
    "night_ventilation_status",
    "night_ventilation_key",
    "night_ventilation_args",
    "warning_notice_kind",
    "warning_notice_text",
    "official_close_instruction",
    "has_co2",
    "has_window_contacts",
    "window_open",
    "window_data_status",
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
        # snapshots are intentionally available only from the address ranges used by Tailscale.
        # The client also validates the destination before every request, making the
        # restriction bidirectional instead of merely a config-flow convention.
        if not request.remote or not _ip_is_tailscale(str(request.remote)):
            return self.json_message(
                "Tailscale connection required",
                status_code=HTTPStatus.FORBIDDEN,
            )

        user = request.get(KEY_HASS_USER)
        if user is None or not bool(getattr(user, "is_admin", False)):
            return self.json_message(
                "Administrator access required",
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

        try:
            requested_protocol = int(request.query.get("protocol", "2"))
        except (TypeError, ValueError):
            requested_protocol = 2
        response_protocol = REMOTE_PROTOCOL_VERSION if requested_protocol >= 3 else 2

        instances = _local_instances(
            hass,
            requested_unit,
            remote_export=True,
            selected_room_keys=selected_room_keys,
        )
        instances = _remote_instances_for_protocol(instances, response_protocol)

        if not discovery:
            client_id = _normalize_remote_client_value(
                request.query.get("client_id"),
                "legacy",
                REMOTE_CLIENT_ID_MAX_LENGTH,
            )
            client_name = _normalize_remote_client_value(
                request.query.get("client_name"),
                "Remote Home Assistant",
                REMOTE_CLIENT_NAME_MAX_LENGTH,
            )
            _record_remote_access(hass, instances, client_id, client_name)

        return self.json(
            {
                "protocol": response_protocol,
                "home_assistant_name": hass.config.location_name,
                # Home Assistant's core UUID is a stable opaque instance ID. It
                # lets clients recognize the same peer through MagicDNS or a
                # direct Tailscale IP instead of relying only on host spelling.
                "home_assistant_instance_id": await async_get_instance_id(hass),
                "instances": instances,
            }
        )



def _station_config_payload(entry: ConfigEntry, station) -> dict[str, Any]:
    """Build the HA-owned desired configuration for one physical station."""
    room_id = str(station.data.get(CONF_HARDWARE_ROOM_ID) or "")
    room = entry.subentries.get(room_id)
    role = station_role(station)
    payload: dict[str, Any] = {
        "protocol": 1,
        "hardware_id": str(station.data.get(CONF_HARDWARE_ID) or ""),
        "station_subentry_id": station.subentry_id,
        "role": role,
        "transport": str(station.data.get(CONF_HARDWARE_CONNECTION_TYPE) or ""),
        "room_id": room_id,
        "room_name": str(room.title) if room is not None else None,
    }
    topology_error = station_topology_error(entry, station)
    if topology_error is not None:
        payload["configuration_error"] = topology_error

    if role == HARDWARE_ROLE_NODE:
        master = configured_master_for_station(entry, station)
        payload["master"] = (
            {
                "subentry_id": master.subentry_id,
                "hardware_id": str(master.data.get(CONF_HARDWARE_ID) or ""),
                "name": str(master.title),
            }
            if master is not None
            else None
        )
    if role == HARDWARE_ROLE_MASTER:
        payload["location_mode"] = str(
            station.data.get(CONF_HARDWARE_LOCATION_MODE) or "local"
        )
        # Provision only through the existing authenticated/admin-only config
        # endpoint. Never expose this in runtime entities or display responses.
        payload["master_secret"] = str(
            station.data.get(CONF_HARDWARE_MASTER_SECRET) or ""
        )
        participants: list[dict[str, Any]] = []
        for candidate in station_subentries(entry):
            if station_role(candidate) != HARDWARE_ROLE_NODE:
                continue
            if station_topology_error(entry, candidate) is not None:
                continue
            master = configured_master_for_station(entry, candidate)
            if master is None or master.subentry_id != station.subentry_id:
                continue
            candidate_room_id = str(candidate.data.get(CONF_HARDWARE_ROOM_ID) or "")
            candidate_room = entry.subentries.get(candidate_room_id)
            participants.append(
                {
                    "station_subentry_id": candidate.subentry_id,
                    "hardware_id": str(candidate.data.get(CONF_HARDWARE_ID) or ""),
                    "room_id": candidate_room_id,
                    "room_name": (
                        str(candidate_room.title) if candidate_room is not None else None
                    ),
                }
            )
        payload["participants"] = participants

        if station.data.get(CONF_HARDWARE_LOCATION_MODE) == HARDWARE_LOCATION_REMOTE:
            wireguard = {
                "address": station.data.get(CONF_HARDWARE_WG_ADDRESS),
                "private_key": station.data.get(CONF_HARDWARE_WG_PRIVATE_KEY),
                "peer_public_key": station.data.get(CONF_HARDWARE_WG_PEER_PUBLIC_KEY),
                "endpoint": station.data.get(CONF_HARDWARE_WG_ENDPOINT),
                "endpoint_host": station.data.get(CONF_HARDWARE_WG_ENDPOINT_HOST),
                "endpoint_port": station.data.get(CONF_HARDWARE_WG_ENDPOINT_PORT),
                "allowed_ips": station.data.get(CONF_HARDWARE_WG_ALLOWED_IPS),
                "persistent_keepalive": station.data.get(CONF_HARDWARE_WG_KEEPALIVE),
            }
            if station.data.get(CONF_HARDWARE_WG_PRESHARED_KEY):
                wireguard["preshared_key"] = station.data.get(
                    CONF_HARDWARE_WG_PRESHARED_KEY
                )
            payload["wireguard"] = wireguard
    return payload


class LueftungsberaterHardwareConfigView(HomeAssistantView):
    """Return Home Assistant's desired role/network topology to one station."""

    url = "/api/lueftungsberater/hardware/config"
    name = "api:lueftungsberater:hardware_config"
    requires_auth = True

    async def post(self, request):
        hass: HomeAssistant = request.app[KEY_HASS]
        user = request.get(KEY_HASS_USER)
        if user is None or not bool(getattr(user, "is_admin", False)):
            return self.json_message(
                "Administrator access required",
                status_code=HTTPStatus.FORBIDDEN,
            )
        try:
            payload = await request.json()
        except (ValueError, json.JSONDecodeError):
            return self.json_message("Invalid JSON", status_code=HTTPStatus.BAD_REQUEST)
        if not isinstance(payload, dict):
            return self.json_message("Invalid payload", status_code=HTTPStatus.BAD_REQUEST)

        entry_id = str(payload.get("entry_id") or "").strip()
        hardware_id = str(payload.get("hardware_id") or "").strip()
        if not entry_id or not hardware_id:
            return self.json_message(
                "entry_id and hardware_id required", status_code=HTTPStatus.BAD_REQUEST
            )
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN or entry_kind(entry) != ENTRY_KIND_LOCAL:
            return self.json_message(
                "Unknown local Lüftungsberater entry", status_code=HTTPStatus.NOT_FOUND
            )
        station = station_by_any_hardware_id(entry, hardware_id)
        if station is None:
            return self.json_message("Unknown station", status_code=HTTPStatus.NOT_FOUND)
        return self.json(_station_config_payload(entry, station))


class LueftungsberaterHardwareDiscoverView(HomeAssistantView):
    """Receive one authenticated JOIN/discovery report from an ESP master."""

    url = "/api/lueftungsberater/hardware/discover"
    name = "api:lueftungsberater:hardware_discover"
    requires_auth = True

    async def post(self, request):
        hass: HomeAssistant = request.app[KEY_HASS]
        try:
            payload = await request.json()
        except (ValueError, json.JSONDecodeError):
            return self.json_message("Invalid JSON", status_code=HTTPStatus.BAD_REQUEST)
        if not isinstance(payload, dict):
            return self.json_message("Invalid payload", status_code=HTTPStatus.BAD_REQUEST)

        entry_id = str(payload.get("entry_id") or "").strip()
        hardware_id = str(payload.get("hardware_id") or "").strip()
        master_id = str(payload.get("master_id") or "default").strip() or "default"
        if not entry_id or not hardware_id:
            return self.json_message("entry_id and hardware_id required", status_code=HTTPStatus.BAD_REQUEST)
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN or entry_kind(entry) != ENTRY_KIND_LOCAL:
            return self.json_message("Unknown local Lüftungsberater entry", status_code=HTTPStatus.NOT_FOUND)

        remember_discovery(
            hass,
            entry,
            hardware_id=hardware_id,
            master_id=master_id,
            name=str(payload.get("name") or hardware_id),
            capabilities=(payload.get("capabilities") if isinstance(payload.get("capabilities"), dict) else {}),
        )
        return self.json({"accepted": True, "hardware_id": hardware_id})


def _hardware_report_master_error(
    entry: ConfigEntry, station, reported_master_id: Any
) -> str | None:
    """Validate that an ESP-NOW node report arrived through its HA-selected master."""
    if station_role(station) != HARDWARE_ROLE_NODE:
        return None

    explicit_master_relation = bool(
        str(station.data.get(CONF_HARDWARE_MASTER_SUBENTRY_ID) or "").strip()
    )
    configured_master = configured_master_for_station(entry, station)
    if explicit_master_relation and configured_master is None:
        return "master_missing"

    configured_master_id = configured_master_hardware_id(entry, station)
    if configured_master_id is None:
        return None
    incoming = str(reported_master_id or "default").strip() or "default"
    if not hardware_id_matches(incoming, configured_master_id):
        return "master_mismatch"
    return None


def _hardware_report_native_auth_error(
    entry: ConfigEntry,
    station,
    reported_master_id: Any,
    reported_master_secret: Any,
) -> str | None:
    """Authenticate one Native-API node report against its configured master."""
    if station_role(station) != HARDWARE_ROLE_NODE:
        return "node_required"

    master_error = _hardware_report_master_error(
        entry, station, reported_master_id
    )
    if master_error is not None:
        return master_error

    master = configured_master_for_station(entry, station)
    if master is None:
        return "master_missing"

    expected = str(master.data.get(CONF_HARDWARE_MASTER_SECRET) or "").strip()
    incoming = str(reported_master_secret or "").strip()
    if not expected:
        return "master_secret_missing"
    if not incoming or not secrets.compare_digest(incoming, expected):
        return "master_auth_failed"
    return None


def _hardware_display_payload(
    hass: HomeAssistant, entry: ConfigEntry, room_id: str
) -> dict[str, Any]:
    """Build the ESP display response directly from the room coordinator."""
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


def _master_location_mode(entry: ConfigEntry, station) -> str | None:
    """Return the HA-configured location of this node's selected master.

    The network path is never inferred from an IP address, latency or VPN
    appearance. Home Assistant's master subentry remains the source of truth.
    """
    master = configured_master_for_station(entry, station)
    if master is None:
        return None
    value = str(master.data.get(CONF_HARDWARE_LOCATION_MODE) or HARDWARE_LOCATION_LOCAL)
    return value if value in {HARDWARE_LOCATION_LOCAL, HARDWARE_LOCATION_REMOTE} else HARDWARE_LOCATION_LOCAL


def _apply_hardware_report(
    hass: HomeAssistant,
    entry: ConfigEntry,
    station,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Validate/store one known node report and return the current display result.

    Both the authenticated HTTP endpoint and the ESPHome Native-API action use
    this function, so there is only one topology/storage/display decision path.
    """
    topology_error = station_topology_error(entry, station)
    if topology_error == "room_missing":
        raise _HardwareReportRejected("Configured room is missing")

    master_error = _hardware_report_master_error(
        entry, station, payload.get("master_id")
    )
    if master_error == "master_missing":
        raise _HardwareReportRejected("Configured master is missing")
    if master_error == "master_mismatch":
        raise _HardwareReportRejected(
            "Report master does not match configured master"
        )

    report_station(hass, entry, station, payload)

    room_id = str(station.data.get(CONF_HARDWARE_ROOM_ID) or "")
    display = _hardware_display_payload(hass, entry, room_id)

    # Correlation values are transport metadata only. HTTP keeps its permissive
    # v0.10.0/v0.10.1 compatibility contract; the Native-API action schema
    # restricts them to unsigned 32-bit integer values.
    round_id = payload.get("round_id")
    request_id = payload.get("request_id")
    if not isinstance(round_id, (str, int)):
        round_id = None
    if not isinstance(request_id, (str, int)):
        request_id = None

    hardware_id = str(station.data.get(CONF_HARDWARE_ID) or payload.get("hardware_id") or "")
    return {
        "paired": True,
        "hardware_id": hardware_id,
        "master_id": configured_master_hardware_id(entry, station) or "default",
        "master_location_mode": _master_location_mode(entry, station),
        "room_id": room_id,
        **display,
        "round_id": round_id,
        "request_id": request_id,
    }


def _hardware_report_action_target(
    hass: HomeAssistant, hardware_id: str
) -> tuple[ConfigEntry, Any]:
    """Resolve one master-backed station without trusting a supplied entry id."""
    matches: list[tuple[ConfigEntry, Any]] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_kind(entry) != ENTRY_KIND_LOCAL:
            continue
        if entry.state is not ConfigEntryState.LOADED:
            continue
        station = station_by_hardware_id(entry, hardware_id)
        if station is not None:
            matches.append((entry, station))

    if not matches:
        raise ServiceValidationError(
            f"Unknown Lüftungsstation hardware id: {hardware_id}"
        )
    if len(matches) > 1:
        raise ServiceValidationError(
            "Hardware id is assigned to more than one Lüftungsassistent entry: "
            f"{hardware_id}"
        )
    return matches[0]


async def _async_hardware_report_action(call: ServiceCall) -> ServiceResponse:
    """Receive one authenticated node sample over the ESPHome Native API."""
    payload = dict(call.data)
    hardware_id = str(payload["hardware_id"]).strip()
    master_id = str(payload["master_id"]).strip()
    master_secret = str(payload.pop("master_secret", "") or "").strip()
    if not hardware_id:
        raise ServiceValidationError("hardware_id required")
    if not master_id:
        raise ServiceValidationError("master_id required")
    if not master_secret:
        raise ServiceValidationError("master_secret required")
    payload["hardware_id"] = hardware_id
    payload["master_id"] = master_id

    entry, station = _hardware_report_action_target(call.hass, hardware_id)
    auth_error = _hardware_report_native_auth_error(
        entry, station, master_id, master_secret
    )
    if auth_error == "node_required":
        raise ServiceValidationError(
            "Native hardware_report accepts ESP-NOW node reports only"
        )
    if auth_error == "master_missing":
        raise ServiceValidationError("Configured master is missing")
    if auth_error == "master_mismatch":
        raise ServiceValidationError(
            "Report master does not match configured master"
        )
    if auth_error == "master_secret_missing":
        raise ServiceValidationError(
            "Configured master has no Native-API credential"
        )
    if auth_error == "master_auth_failed":
        raise ServiceValidationError("Master credential is invalid")

    try:
        return _apply_hardware_report(call.hass, entry, station, payload)
    except _HardwareReportRejected as err:
        raise ServiceValidationError(str(err)) from err


class LueftungsberaterHardwareReportView(HomeAssistantView):
    """Receive raw station values and return HA's already-computed display result."""

    url = "/api/lueftungsberater/hardware/report"
    name = "api:lueftungsberater:hardware_report"
    requires_auth = True

    async def post(self, request):
        hass: HomeAssistant = request.app[KEY_HASS]
        try:
            payload = await request.json()
        except (ValueError, json.JSONDecodeError):
            return self.json_message("Invalid JSON", status_code=HTTPStatus.BAD_REQUEST)
        if not isinstance(payload, dict):
            return self.json_message("Invalid payload", status_code=HTTPStatus.BAD_REQUEST)

        entry_id = str(payload.get("entry_id") or "").strip()
        hardware_id = str(payload.get("hardware_id") or "").strip()
        if not entry_id or not hardware_id:
            return self.json_message("entry_id and hardware_id required", status_code=HTTPStatus.BAD_REQUEST)
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN or entry_kind(entry) != ENTRY_KIND_LOCAL:
            return self.json_message("Unknown local Lüftungsberater entry", status_code=HTTPStatus.NOT_FOUND)
        station = station_by_hardware_id(entry, hardware_id)
        if station is None:
            # Unknown stations stay discoverable but can never inject room values
            # until the user explicitly assigns them to a room.
            remember_discovery(
                hass, entry, hardware_id=hardware_id,
                master_id=str(payload.get("master_id") or "default"),
                name=str(payload.get("name") or hardware_id),
                capabilities=(payload.get("capabilities") if isinstance(payload.get("capabilities"), dict) else {}),
            )
            return self.json({"paired": False, "hardware_id": hardware_id}, status_code=HTTPStatus.CONFLICT)

        try:
            response = _apply_hardware_report(hass, entry, station, payload)
        except _HardwareReportRejected as err:
            return self.json_message(str(err), status_code=HTTPStatus.CONFLICT)
        return self.json(response)



def _remote_instances_for_protocol(
    instances: list[dict[str, Any]], protocol: int
) -> list[dict[str, Any]]:
    """Return a protocol-compatible snapshot without silently unknown night keys.

    Protocol 2 predates ``short_only``/``not_recommended``. Older clients do not
    send a requested protocol, so keep the room snapshot usable but suppress only
    night advice they cannot localize. Protocol 3 receives the full semantics.
    """
    if protocol >= 3:
        return instances

    compatible: list[dict[str, Any]] = []
    for instance in instances:
        instance_copy = dict(instance)
        rooms_copy: list[dict[str, Any]] = []
        rooms = instance.get("rooms", [])
        if isinstance(rooms, list):
            for room in rooms:
                if not isinstance(room, dict):
                    continue
                room_copy = dict(room)
                attrs = room.get("attributes")
                if isinstance(attrs, dict):
                    attrs_copy = dict(attrs)
                    if attrs_copy.get("night_ventilation_status") in {
                        "short_only",
                        "not_recommended",
                    }:
                        attrs_copy["night_ventilation_status"] = "unavailable"
                        attrs_copy["night_ventilation_key"] = None
                        attrs_copy["night_ventilation_args"] = {}
                    room_copy["attributes"] = attrs_copy
                rooms_copy.append(room_copy)
        instance_copy["rooms"] = rooms_copy
        compatible.append(instance_copy)
    return compatible

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
            if client_id not in clients and len(clients) >= REMOTE_CLIENTS_PER_ROOM_MAX:
                # Bound transient remote-access bookkeeping even for a buggy or
                # hostile authenticated admin client that rotates client IDs.
                def _last_seen(item: str) -> float:
                    info = clients.get(item)
                    if not isinstance(info, dict):
                        return 0.0
                    try:
                        return float(info.get("last_seen", 0))
                    except (TypeError, ValueError):
                        return 0.0

                oldest_id = min(clients, key=_last_seen)
                oldest = clients.pop(oldest_id, None)
                if isinstance(oldest, dict):
                    cancel = oldest.get("cancel_expiry")
                    if callable(cancel):
                        cancel()
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


@callback
def async_clear_remote_access(hass: HomeAssistant, entry_id: str) -> None:
    """Cancel transient remote-access timers owned by one local entry."""
    store = hass.data.get(DOMAIN, {}).get(DATA_REMOTE_ACCESS, {})
    prefix = f"{entry_id}:"
    for key in [item for item in list(store) if item.startswith(prefix)]:
        clients = store.pop(key, None)
        if not isinstance(clients, dict):
            continue
        for info in clients.values():
            if not isinstance(info, dict):
                continue
            cancel = info.get("cancel_expiry")
            if callable(cancel):
                cancel()


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
        info = clients.pop(client_id, None)
        if isinstance(info, dict):
            cancel = info.get("cancel_expiry")
            if callable(cancel):
                cancel()
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


def _loading_remote_room_attributes(entry, subentry) -> dict[str, Any]:
    """Return an explicit loading snapshot without inventing live room state."""
    return {
        "availability": "loading",
        "instance_id": entry.entry_id,
        "instance_name": entry.title,
        "room_name": subentry.title,
        "status": "yellow",
        "recommendation_key": "unknown",
        "mode": "incomplete_data",
        "reason_key": "incomplete_data",
        "reason_args": {},
        "duration_key": "incomplete_data",
        "window_open": None,
        "has_window_contacts": bool(subentry.data.get("window_entities")),
        "has_co2": bool(subentry.data.get("co2_entity")),
    }


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
                # Preserve room metadata during setup/reload, but never invent a
                # concrete window state or safety state when no coherent advisor
                # snapshot exists yet.
                attributes = _loading_remote_room_attributes(entry, subentry)
                room_state = "unavailable"
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


@callback
@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): "lueftungsberater/remote_overview"}
)
def websocket_remote_overview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return only cached remote snapshots to the local frontend."""
    connection.send_result(msg["id"], _remote_instances(hass))


@callback
def async_register_hardware_service(hass: HomeAssistant) -> None:
    """Register the ESPHome runtime action once at integration setup."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_HARDWARE_SERVICE_REGISTERED):
        return
    hass.services.async_register(
        DOMAIN,
        SERVICE_HARDWARE_REPORT,
        _async_hardware_report_action,
        schema=HARDWARE_REPORT_ACTION_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    domain_data[DATA_HARDWARE_SERVICE_REGISTERED] = True


@callback
def async_register_api(hass: HomeAssistant) -> None:
    """Register HTTP/websocket endpoints once for this Home Assistant instance."""
    # Keep this call as a defensive fallback for test/custom-loader paths that
    # may invoke setup_entry directly. Normal HA loading registers the service
    # earlier from async_setup().
    async_register_hardware_service(hass)

    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_API_REGISTERED):
        return
    domain_data[DATA_API_REGISTERED] = True
    hass.http.register_view(LueftungsberaterSnapshotView())
    hass.http.register_view(LueftungsberaterHardwareDiscoverView())
    hass.http.register_view(LueftungsberaterHardwareConfigView())
    hass.http.register_view(LueftungsberaterHardwareReportView())
    websocket_api.async_register_command(hass, websocket_localize)
    websocket_api.async_register_command(hass, websocket_remote_overview)

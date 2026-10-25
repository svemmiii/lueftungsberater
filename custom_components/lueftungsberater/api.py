"""Small authenticated API used by the overview card and remote peers."""
from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any
import logging
import time

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.http import KEY_HASS, KEY_HASS_USER, HomeAssistantView
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.instance_id import async_get as async_get_instance_id

from .const import (
    RECORDER_RETENTION_DAYS,
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
from .history_support import preferred_air_quality_variant
from .coordinator import get_room_coordinator
from .localization import (
    async_prepare_night_args,
    duration_text,
    night_advice_text,
    reason_text,
    recommendation_text,
)
from .remote import _ip_is_tailscale, get_remote_coordinator

_LOGGER = logging.getLogger(__name__)

REMOTE_CLIENT_ID_MAX_LENGTH = 128
REMOTE_CLIENT_NAME_MAX_LENGTH = 128
REMOTE_CLIENTS_PER_ROOM_MAX = 32

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
    "forecast_using_cached_data",
    "forecast_updated_at",
    "forecast_last_attempt_at",
    "forecast_error",
    "forecast_next_retry_at",
    "night_ventilation_status",
    "night_ventilation_key",
    "night_ventilation_args",
    "warning_notice_kind",
    "warning_notice_text",
    "warning_notices",
    "warning_next_transition_at",
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
    """Expose only current local Lüftungsassistent room snapshots."""

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

            # async_call_later must run this HA-state refresh on the event loop,
            # never in a SyncWorker thread.
            @callback
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
@websocket_api.async_response
async def websocket_localize(
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
    if night_key:
        night_args = await async_prepare_night_args(night_args)
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


def _resolve_history_room(hass, entity_id: str):
    """Resolve a configured local room from its registered advisor, not its live state.

    The recorder may have data even when the advisor is unknown, unavailable,
    or temporarily absent. Do not trust client-provided room or instance IDs.
    """
    registry = er.async_get(hass)
    registered = registry.async_get(entity_id)
    if registered is None or registered.platform != DOMAIN or not entity_id.startswith("sensor."):
        return None
    uid = str(registered.unique_id or "")
    if not uid.endswith("_advisor"):
        return None
    room_id = uid[:-len("_advisor")]
    registered_entry_id = getattr(registered, "config_entry_id", None)
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_kind(entry) != ENTRY_KIND_LOCAL:
            continue
        if registered_entry_id and registered_entry_id != entry.entry_id:
            continue
        room = entry.subentries.get(room_id)
        if room is None or room.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        if registry.async_get_entity_id("sensor", DOMAIN, uid) != entity_id:
            continue
        return entry, room
    return None


def _history_room_attributes(hass, entry, room, entity_id: str) -> dict:
    """Retain live bounds when available, fall back to configured measurements.

    Only configured sensors and recorded helper IDs are used; no fresh
    measurements or safe/unsafe thresholds are invented during an outage.
    """
    from .history_support import history_data, finite_value

    state = hass.states.get(entity_id)
    attrs = dict(state.attributes or {}) if state else {}
    room_data = room.data
    manual = entry.data.get("manual_outdoor")
    manual = manual if isinstance(manual, dict) else entry.data
    sources = {
        "source_co2": room_data.get("co2_entity"),
        "source_temperature_inside": room_data.get("indoor_temperature"),
        "source_humidity_inside": room_data.get("indoor_humidity"),
        "source_surface_temperature": room_data.get("surface_temperature"),
        "source_target_temperature": room_data.get("climate_entity"),
        "source_pm25_inside": room_data.get("indoor_pm25"),
        "source_pm10_inside": room_data.get("indoor_pm10"),
        "source_voc_inside": room_data.get("indoor_voc"),
        "source_no2_inside": room_data.get("indoor_no2"),
        "source_formaldehyde_inside": room_data.get("indoor_formaldehyde"),
        "source_temperature_outside": manual.get("outdoor_temperature"),
        "source_humidity_outside": manual.get("outdoor_humidity"),
        "source_outdoor_co2": manual.get("outdoor_co2"),
        "source_wind_outside": manual.get("outdoor_wind_speed"),
        "source_gust_outside": manual.get("outdoor_wind_gust"),
        "source_pm25_outside": manual.get("outdoor_pm25"),
        "source_pm10_outside": manual.get("outdoor_pm10"),
        "source_voc_outside": manual.get("outdoor_voc"),
        "source_no2_outside": manual.get("outdoor_no2"),
        "source_o3_outside": manual.get("outdoor_o3"),
    }
    # Existing derived sensors have stable IDs too. They can be read from
    # Recorder without the advisor being alive; this creates no new entity.
    registry = er.async_get(hass)
    for key, suffix in (
        ("source_absolute_humidity_inside", "absolute_humidity"),
        ("source_absolute_humidity_outside", "absolute_humidity_outside"),
        ("source_absolute_humidity_difference", "absolute_humidity_difference"),
    ):
        if not sources.get(key):
            sources[key] = registry.async_get_entity_id(
                "sensor", DOMAIN, f"{room.subentry_id}_{suffix}"
            )
    # The current config and outside coordinator are authoritative. A previous
    # advisor state may still carry sources from before a room edit, an auto-
    # provider switch or a reload; none of those IDs may leak into Recorder
    # lookups for the current metric.
    for key in sources:
        attrs.pop(key, None)
    for key in (
        "source_absolute_humidity_inside", "source_absolute_humidity_outside",
        "source_absolute_humidity_difference",
    ):
        attrs.pop(key, None)

    from .auto_providers import uses_auto_weather
    from .outside import get_outside_coordinator
    auto_weather = uses_auto_weather(entry)
    outside = get_outside_coordinator(hass, entry)
    weather = getattr(getattr(outside, "data", None), "weather", None)

    # Manual outdoor overrides may also be active in auto mode. They are only
    # valid while present in the *current* entry settings; removed overrides
    # must never be resurrected from an advisor's old source_* attributes.
    for key, value in sources.items():
        if isinstance(value, str) and value.strip():
            attrs[key] = value.strip()

    # Prefer actual effective HA sensor entities over stale advisor attributes.
    # A provider station code is NOT a recorder entity. Missing live weather
    # sources retain only explicitly configured manual sources.
    auto_available = set()
    if auto_weather:
        auto_available.update(("temp_out", "humidity_out"))

    def _ha_source(value):
        return (isinstance(value, str) and
                value.startswith(("sensor.", "number.", "input_number.")))

    if weather is not None:
        for key, field, metric in (
            ("source_temperature_outside", "source_temperature", "temp_out"),
            ("source_humidity_outside", "source_humidity", "humidity_out"),
            ("source_wind_outside", "source_wind", "wind_out"),
            ("source_gust_outside", "source_gust", "gust_out"),
            ("source_outdoor_co2", "outdoor_co2_source", "co2_out"),
        ):
            candidate = getattr(weather, field, None)
            if _ha_source(candidate):
                attrs[key] = candidate
            elif candidate:
                # A named provider/model such as cams_air_quality_model is a
                # provenance tag, NOT a Recorder entity_id. Use the existing
                # persistent per-room helper for its current numeric value.
                attrs.pop(key, None)
                value_field = {
                    "temp_out": "temperature", "humidity_out": "humidity",
                    "wind_out": "wind_speed_kmh", "gust_out": "wind_gust_kmh",
                    "co2_out": "outdoor_co2_ppm",
                }.get(metric)
                if value_field and finite_value(getattr(weather, value_field, None)) is not None:
                    auto_available.add(metric)
            elif auto_weather and metric != "co2_out":
                # No active source: retain only a presently configured manual
                # override, never the removed advisor's old source.
                if not _ha_source(sources.get(key)):
                    attrs.pop(key, None)

        for key, pollutant_names, metric in (
            ("source_pm25_outside", ("pm2_5",), "pm25_out"),
            ("source_pm10_outside", ("pm10",), "pm10_out"),
            ("source_voc_outside", ("voc", "voc_parts", "voc_index"), "voc_out"),
            ("source_no2_outside", ("no2", "no2_parts", "no2_index"), "no2_out"),
            ("source_o3_outside", ("o3", "o3_parts"), "o3_out"),
        ):
            configured = sources.get(key)
            candidates = getattr(weather, "air_quality_sources", None) or {}
            active = preferred_air_quality_variant(weather, pollutant_names)
            candidate = candidates.get(active) if active else None
            if _ha_source(candidate):
                attrs[key] = candidate
            elif candidate:
                attrs.pop(key, None)
                auto_available.add(metric)
            elif auto_weather and not _ha_source(configured):
                attrs.pop(key, None)
                if active is not None:
                    auto_available.add(metric)
            # A configured manual local entity is valid even while its value
            # is unavailable. Keep it as the possible Recorder source.
            if active is None and _ha_source(configured):
                attrs[key] = configured

        if auto_weather:
            for metric, field in (("wind_out", "wind_speed_kmh"),
                                  ("gust_out", "wind_gust_kmh")):
                if getattr(weather, field, None) is not None:
                    auto_available.add(metric)
            air = {
                **(getattr(weather, "air_quality_values", None) or {}),
                **(getattr(weather, "local_station_values", None) or {}),
            }
            for metric, names in (("pm25_out", ("pm2_5",)),
                                  ("pm10_out", ("pm10",)),
                                  ("voc_out", ("voc", "voc_parts", "voc_index")),
                                  ("no2_out", ("no2", "no2_parts", "no2_index")),
                                  ("o3_out", ("o3", "o3_parts"))):
                if any(name in air for name in names):
                    auto_available.add(metric)
    if auto_available:
        attrs["_history_auto_available"] = auto_available

    # A remembered advisor scalar is not proof that its old source remains
    # configured. Previously opted-in history helpers stay selectable so that
    # their Recorder rows remain accessible after a source is removed.
    from .history_support import HISTORY_METRICS
    enabled = set(history_data(hass, entry.entry_id).get(room.subentry_id, []))
    attrs["_history_enabled"] = enabled
    inactive = set()
    for metric, (_, _, _value_path, source_key) in HISTORY_METRICS.items():
        if source_key and metric in {
            "co2_in", "co2_out", "temp_out", "humidity_out",
            "pm25_in", "pm10_in", "no2_in", "voc_in", "hcho_in",
            "pm25_out", "pm10_out", "no2_out", "o3_out", "voc_out",
            "wind_out", "gust_out",
        }:
            if not attrs.get(source_key) and metric not in auto_available:
                inactive.add(metric)
    attrs["_history_inactive_metrics"] = inactive
    attrs["has_co2"] = bool(attrs.get("source_co2")) or "co2_in" in enabled
    attrs["has_window_contacts"] = bool(room_data.get("window_entities"))
    return attrs

@websocket_api.websocket_command(
    {
        vol.Required("type"): "lueftungsberater/history_enable",
        vol.Required("entity"): str,
        vol.Required("metrics"): [str],
        vol.Optional("retry", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_history_enable(hass, connection, msg) -> None:
    """Create persisted helper sensors for selected missing histories only."""
    from .history_support import HISTORY_METRICS, allowed_metric, async_enable_history
    resolved = _resolve_history_room(hass, msg["entity"])
    if resolved is None:
        connection.send_error(msg["id"], "invalid_room", "Select a local room advisor")
        return
    entry, selected_room = resolved
    attrs = _history_room_attributes(hass, entry, selected_room, msg["entity"])
    requested = list(dict.fromkeys(msg["metrics"]))
    if any(key != "decision" and (key not in HISTORY_METRICS or not allowed_metric(attrs, key)) for key in requested):
        connection.send_error(msg["id"], "invalid_metrics", "Only configured measurements are allowed")
        return
    if entry.entry_id in hass.data.get(DOMAIN, {}).get("history_load_errors", {}):
        connection.send_error(msg["id"], "history_store_readonly", "History preferences are damaged or unreadable")
        return
    retry = None
    if msg.get("retry"):
        retry = hass.data.get(DOMAIN, {}).get("history_retry_adders", {}).get(entry.entry_id)
        if retry is None:
            connection.send_error(msg["id"], "history_platform_unavailable", "History sensor platform is not ready")
            return
    try:
        enabled = await async_enable_history(hass, entry, selected_room.subentry_id, requested)
    except Exception:  # noqa: BLE001 - optional history must not crash websocket handling
        _LOGGER.exception("Unable to enable history for %s / %s", entry.entry_id, selected_room.subentry_id)
        connection.send_error(msg["id"], "history_enable_failed", "Could not enable history recording")
        return
    if retry is not None:
        retry()
    connection.send_result(msg["id"], {"enabled": enabled, "room": selected_room.subentry_id})


@websocket_api.websocket_command(
    {vol.Required("type"): "lueftungsberater/history_rooms"}
)
@callback
def websocket_history_rooms(hass, connection, msg) -> None:
    """List configured local rooms, independently of live advisor states.

    The entity registry binds each room to its existing stable advisor ID.
    Missing/unavailable entities stay listed, but no new entity is created.
    Physical ESP station subentries are deliberately excluded.
    """
    registry = er.async_get(hass)
    rooms = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_kind(entry) != ENTRY_KIND_LOCAL:
            continue
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
                continue
            entity_id = registry.async_get_entity_id(
                "sensor", DOMAIN, f"{subentry.subentry_id}_advisor"
            )
            state = hass.states.get(entity_id) if entity_id else None
            rooms.append({
                "instance_id": entry.entry_id,
                "instance_name": entry.title,
                "room_id": subentry.subentry_id,
                "room_name": subentry.title,
                "entity": entity_id,
                "available": state is not None and state.state not in
                ("unknown", "unavailable"),
            })
    connection.send_result(msg["id"], rooms)


@websocket_api.websocket_command(
    {vol.Required("type"): "lueftungsberater/history_room_info", vol.Required("entity"): str}
)
@callback
def websocket_history_room_info(hass, connection, msg) -> None:
    """Read-only access to existing history for any HA user with room access.

    Opt-in creation is a separate, admin-only command. Resolve the room from
    its registered advisor unique ID rather than guessing a frontend room ID.
    """
    from .history_support import history_data, history_sensor_unique_id
    resolved = _resolve_history_room(hass, msg["entity"])
    if resolved is None:
        connection.send_error(msg["id"], "invalid_room", "Select a local room advisor")
        return
    entry, room = resolved
    room_id = room.subentry_id
    registry = er.async_get(hass)
    enabled = list(history_data(hass, entry.entry_id).get(room_id, []))
    helpers = {}
    disabled = []
    for metric in enabled:
        helper_id = registry.async_get_entity_id("sensor", DOMAIN, history_sensor_unique_id(room_id, metric))
        if helper_id:
            # A missing current state does not erase existing Recorder rows.
            helpers[metric] = helper_id
            registry_entry = registry.async_get(helper_id)
            if registry_entry is not None and registry_entry.disabled_by is not None:
                # Reading previous Recorder values remains possible, but an
                # intentionally disabled entity must never be auto-repaired.
                disabled.append(metric)
    # Report confirmed Recorder filtering, not merely an empty/new history.
    # Home Assistant's effective entity_filter includes explicit IDs, domains
    # and globs and is more reliable than interpreting the user's YAML here.
    recorder_excluded: list[str] = []
    try:
        from homeassistant.components.recorder import get_instance

        recorder_instance = get_instance(hass)
        entity_filter = getattr(recorder_instance, "entity_filter", None)
        if entity_filter is not None:
            recorder_excluded = [entity_id for entity_id in helpers.values()
                                 if not entity_filter(entity_id)]
    except (KeyError, RuntimeError, AttributeError, ImportError):
        # Recorder may not be installed/loaded. Do not infer exclusions.
        pass
    domain_data = hass.data.get(DOMAIN, {})
    repair = domain_data.get("history_repair_failed", {}).get(entry.entry_id, {})
    # A previously exhausted registration is not a permanent failure: clear
    # stale status when an entity has subsequently appeared in the state machine.
    rooms = repair.get("rooms", {})
    if room_id in rooms:
        recovered = set(disabled)
        for metric in rooms[room_id]:
            helper_id = registry.async_get_entity_id(
                "sensor", DOMAIN, history_sensor_unique_id(room_id, metric)
            )
            if helper_id and hass.states.get(helper_id) is not None:
                recovered.add(metric)
        pending = [metric for metric in rooms[room_id] if metric not in recovered]
        if len(pending) != len(rooms[room_id]):
            rooms[room_id] = pending
            if not pending:
                rooms.pop(room_id, None)
            if not rooms:
                domain_data.get("history_repair_failed", {}).pop(entry.entry_id, None)
                repair = {}
        elif repair.get("reason") == "registry_unavailable":
            # The registry is answering again; remaining helpers really are
            # missing rather than merely unverifiable.
            repair["reason"] = "helpers_missing"
    connection.send_result(msg["id"], {
        "room": room_id, "room_name": room.title, "enabled": enabled,
        "helpers": helpers, "disabled": disabled,
        "recorder_excluded": recorder_excluded,
        "failed": repair.get("rooms", {}).get(room_id, []),
        "failure_reason": repair.get("reason") if room_id in repair.get("rooms", {}) else None,
        "history_store_readonly": entry.entry_id in domain_data.get("history_load_errors", {}),
    })


@websocket_api.websocket_command(
    {vol.Required("type"): "lueftungsberater/history_recommendations", vol.Required("language"): str}
)
@callback
def websocket_history_recommendations(hass, connection, msg) -> None:
    """Use the existing DE/EN/TR translations, not a second frontend map."""
    from .sensor import RECOMMENDATION_STATES
    keys = (*RECOMMENDATION_STATES, "room_good", "room_watch", "room_need", "room_urgent", "room_keep_brief", "unknown", "window_state_unknown")
    connection.send_result(msg["id"], {
        key: recommendation_text(key, msg["language"]) for key in keys
    })


@websocket_api.websocket_command(
    {vol.Required("type"): "lueftungsberater/history_metrics", vol.Required("entity"): str}
)
@callback
def websocket_history_metrics(hass, connection, msg) -> None:
    """Read current evaluation bands directly from Python source definitions."""
    from .history_support import configured_metrics
    resolved = _resolve_history_room(hass, msg["entity"])
    if resolved is None:
        connection.send_error(msg["id"], "invalid_room", "Select a local room advisor")
        return
    entry, room = resolved
    attrs = _history_room_attributes(hass, entry, room, msg["entity"])
    from .history_support import current_unit, history_sensor_unique_id, history_data
    units = {}
    coordinator = get_room_coordinator(hass, entry, room)
    snapshot = getattr(coordinator, "data", None)
    for metric in ("voc_in", "voc_out", "no2_in", "no2_out", "o3_out"):
        unit = current_unit(snapshot, metric)
        if unit:
            units[metric] = unit
    # When a room is unavailable, use the registered helper's last known
    # actual unit rather than inventing a mass scale from the metric name.
    registry = er.async_get(hass)
    enabled = history_data(hass, entry.entry_id).get(room.subentry_id, ())
    for metric in enabled:
        if metric in units:
            continue
        helper_id = registry.async_get_entity_id(
            "sensor", DOMAIN, history_sensor_unique_id(room.subentry_id, metric)
        )
        state = hass.states.get(helper_id) if helper_id else None
        unit = (state.attributes or {}).get("unit_of_measurement") if state else None
        if isinstance(unit, str) and unit.strip():
            units[metric] = unit.strip()
    attrs["_history_metric_units"] = units
    metrics = configured_metrics(attrs, hass.states)
    # Recorder retention removes integration-owned transient raw timelines
    # daily. Their current numeric state is not a durable history source.
    # A selected helper must therefore be enabled regardless of raw values.
    from .recorder_maintenance import _RETAINED_HISTORY_SUFFIXES
    for metric in metrics:
        source = metric.get("source")
        if not source:
            metric["helper_required"] = True
            continue
        entity = registry.async_get(source) if hasattr(registry, "async_get") else None
        unique_id = str(getattr(entity, "unique_id", "") or "")
        # The integration purges retained raw absolute-humidity history after
        # 20 days, even if the global Recorder retains 30. Tell the card this
        # source's real lifetime so only a longer selected range needs a helper.
        internal = entity is not None and getattr(entity, "platform", None) == DOMAIN
        if (internal and unique_id.endswith("_absolute_humidity")
                and "_history_" not in unique_id):
            metric["raw_retention_days"] = RECORDER_RETENTION_DAYS
        metric["helper_required"] = bool(
            internal and "_history_" not in unique_id
            and not unique_id.endswith(_RETAINED_HISTORY_SUFFIXES)
        )
    connection.send_result(msg["id"], metrics)


@callback
def async_register_api(hass: HomeAssistant) -> None:
    """Register HTTP/websocket endpoints once for this Home Assistant instance."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_API_REGISTERED):
        return
    domain_data[DATA_API_REGISTERED] = True
    hass.http.register_view(LueftungsberaterSnapshotView())
    websocket_api.async_register_command(hass, websocket_localize)
    websocket_api.async_register_command(hass, websocket_remote_overview)
    websocket_api.async_register_command(hass, websocket_history_enable)
    websocket_api.async_register_command(hass, websocket_history_rooms)
    websocket_api.async_register_command(hass, websocket_history_room_info)
    websocket_api.async_register_command(hass, websocket_history_metrics)
    websocket_api.async_register_command(hass, websocket_history_recommendations)

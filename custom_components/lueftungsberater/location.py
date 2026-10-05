"""Effective location for stationary and mobile Lüftungsassistent installs.

Home Assistant remains the source of truth. Stationary installs read the live
core latitude/longitude; an explicit zone or a mobile device_tracker may be used
as the effective location. No coordinates are copied into ConfigEntry data, so
moving Home, a zone or a tracker takes effect without reconfiguration.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import CONF_LOCATION_TRACKER

LOCATION_MOVE_THRESHOLD_KM = 2.0
LOCATION_MAX_MOBILE_AGE = timedelta(minutes=5)
LOCATION_MOBILE_STALE_HOLD = timedelta(minutes=30)
LOCATION_TRACKER_MAX_REPORT_AGE = timedelta(minutes=5)
# A provider needs a local position, not a multi-kilometre uncertainty area.
LOCATION_MAX_GPS_ACCURACY_M = 250.0


@dataclass(frozen=True, slots=True)
class EffectiveLocation:
    latitude: float
    longitude: float
    elevation: float | None
    country: str | None
    source: str
    updated_at: datetime
    available: bool = True
    accuracy_m: float | None = None
    position_valid: bool = True


def _finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _position_reported_at(state: Any) -> datetime | None:
    """Use the source fix timestamp, or HA's last report even at standstill."""
    for name in ("gps_timestamp", "location_updated_at"):
        if name in state.attributes:
            value = state.attributes[name]
            if isinstance(value, datetime):
                stamp = value
            elif isinstance(value, str):
                stamp = dt_util.parse_datetime(value)
            else:
                number = _finite(value)
                try:
                    stamp = datetime.fromtimestamp(number, tz=dt_util.UTC) if number is not None else None
                except (OverflowError, OSError, ValueError):
                    stamp = None
            return dt_util.as_utc(stamp) if stamp is not None and stamp.tzinfo is not None else None
    stamp = getattr(state, "last_reported", None) or getattr(state, "last_updated", None)
    return dt_util.as_utc(stamp) if isinstance(stamp, datetime) and stamp.tzinfo is not None else None


def effective_location(hass: HomeAssistant, entry: ConfigEntry) -> EffectiveLocation:
    """Return configured zone/tracker coordinates, otherwise HA Home."""
    tracker = str(entry.data.get(CONF_LOCATION_TRACKER) or "").strip()
    now = dt_util.utcnow()
    if tracker:
        state = hass.states.get(tracker)
        if state is not None and state.state not in {"unknown", "unavailable", "none", ""}:
            lat = _finite(state.attributes.get("latitude"))
            lon = _finite(state.attributes.get("longitude"))
            if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
                elevation = _finite(state.attributes.get("altitude"))
                # Zones are static Home Assistant locations. They have no GPS
                # freshness/accuracy semantics and remain valid until edited.
                if tracker.startswith("zone."):
                    return EffectiveLocation(
                        latitude=lat,
                        longitude=lon,
                        elevation=elevation,
                        country=None,
                        source=tracker,
                        updated_at=now,
                        available=True,
                        position_valid=True,
                    )

                reported_at = _position_reported_at(state)
                age = now - reported_at if reported_at is not None else None
                accuracy_present = "gps_accuracy" in state.attributes
                accuracy = _finite(state.attributes.get("gps_accuracy"))
                position_valid = (not accuracy_present or (accuracy is not None and not isinstance(state.attributes.get("gps_accuracy"), bool) and 0 <= accuracy <= LOCATION_MAX_GPS_ACCURACY_M))
                return EffectiveLocation(
                    latitude=lat,
                    longitude=lon,
                    elevation=elevation,
                    # HA's configured country describes the installation, not
                    # necessarily a moving tracker. Country-specific provider
                    # adapters must resolve the live coordinate independently.
                    country=None,
                    source=tracker,
                    updated_at=reported_at or now,
                    available=(position_valid and age is not None and timedelta(0) <= age <= LOCATION_TRACKER_MAX_REPORT_AGE),
                    accuracy_m=accuracy,
                    position_valid=position_valid,
                )

        # Home must not silently become the position of an explicitly selected
        # tracker/zone that is unavailable.
        return EffectiveLocation(
            latitude=float(hass.config.latitude),
            longitude=float(hass.config.longitude),
            elevation=None,
            country=None,
            source=tracker,
            updated_at=now,
            available=False,
            position_valid=False,
        )

    return EffectiveLocation(
        latitude=float(hass.config.latitude),
        longitude=float(hass.config.longitude),
        elevation=_finite(getattr(hass.config, "elevation", None)),
        country=(str(hass.config.country).upper() if hass.config.country else None),
        source="home",
        updated_at=now,
    )


def distance_km(left: EffectiveLocation, right: EffectiveLocation) -> float:
    """Great-circle distance between two accepted locations."""
    radius = 6371.0088
    lat1 = math.radians(left.latitude)
    lat2 = math.radians(right.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(right.longitude - left.longitude)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))


def materially_changed(
    previous: EffectiveLocation | None,
    current: EffectiveLocation,
    *,
    now: datetime | None = None,
) -> bool:
    """Throttle mobile jitter while never suppressing a real Home move."""
    if previous is None:
        return True
    if previous.source != current.source:
        return True
    if previous.available != current.available:
        return True
    if current.source == "home":
        return distance_km(previous, current) >= 0.05
    if distance_km(previous, current) >= LOCATION_MOVE_THRESHOLD_KM:
        return True
    moment = now or dt_util.utcnow()
    return moment - previous.updated_at >= LOCATION_MAX_MOBILE_AGE

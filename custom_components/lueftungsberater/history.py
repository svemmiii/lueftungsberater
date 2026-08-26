"""Bounded per-room history owned by Lüftungsassistent.

This is deliberately separate from Home Assistant's shared Recorder database.
The current room state, configuration, hysteresis memory and safety state do not
live in this budget and therefore can never be evicted by history trimming.
"""
from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import storage
from homeassistant.util import dt as dt_util

from .const import (
    DATA_ROOM_HISTORY,
    DOMAIN,
    ROOM_HISTORY_MAX_BYTES,
    ROOM_HISTORY_RETENTION,
    ROOM_HISTORY_TRIM_TARGET_BYTES,
    STORAGE_VERSION,
)
from .runtime import RoomSnapshot


def _sample(snapshot: RoomSnapshot, now: datetime) -> dict[str, Any]:
    """Create a compact, language-neutral history sample."""
    result = snapshot.result
    values = snapshot.values
    weather = snapshot.weather
    warnings = snapshot.warnings
    return {
        "ts": now.isoformat(),
        "recommendation": result.recommendation_key if result else None,
        "mode": result.mode if result else None,
        "safety_lock": bool(result.safety_lock) if result else False,
        "ventilation_status": result.color if result else None,
        "room_status": result.room_status_color if result else None,
        "primary_need": result.primary_need if result else None,
        "temperature_inside": values.get("temperature_inside"),
        "temperature_outside": weather.temperature if weather else None,
        "target_temperature": values.get("target_temperature"),
        "humidity_inside": values.get("humidity_inside"),
        "humidity_outside": weather.humidity if weather else None,
        "absolute_humidity_inside": result.indoor_absolute_humidity if result else None,
        "absolute_humidity_outside": result.outdoor_absolute_humidity if result else None,
        "co2_ppm": values.get("co2_ppm"),
        "outdoor_co2_ppm": values.get("outdoor_co2_ppm"),
        "co2_data_status": values.get("co2_data_status"),
        "surface_temperature": values.get("surface_temperature"),
        "surface_relative_humidity": (
            result.surface_relative_humidity if result else None
        ),
        "mold_risk": bool(result.mold_risk) if result else False,
        "mold_persistent": bool(result.mold_persistent) if result else False,
        "mold_current_critical_minutes": (
            result.mold_current_critical_minutes if result else None
        ),
        "mold_critical_minutes_24h": (
            result.mold_critical_minutes_24h if result else None
        ),
        "window_open": values.get("window_open"),
        "open_minutes": values.get("open_minutes"),
        "hours_since_last_airing": values.get("hours_since_last_airing"),
        "air_quality": weather.air_quality_index if weather else None,
        "air_quality_pollutant": weather.air_quality_pollutant if weather else None,
        "air_quality_value": weather.air_quality_value if weather else None,
        "air_quality_values": dict(weather.air_quality_values) if weather else {},
        "air_quality_baseline_value": values.get("air_quality_baseline_value"),
        "air_quality_typical": values.get("air_quality_typical"),
        "air_quality_unusual": values.get("air_quality_unusual", False),
        "air_quality_trend": values.get("air_quality_trend"),
        "wind_speed_kmh": weather.wind_speed_kmh if weather else None,
        "wind_gust_kmh": weather.wind_gust_kmh if weather else None,
        "rain_minutes_until": weather.rain_minutes_until if weather else None,
        "night_ventilation_status": values.get("night_ventilation_status"),
        "official_close_instruction": bool(warnings.official_close_instruction),
        "warning_notice_kind": warnings.warning_notice_kind,
    }


def _encoded_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


class RoomHistory:
    """Keep up to 30 days / 40 MiB of disposable room history.

    New samples always win. If the byte budget is exceeded, the oldest samples
    are removed until the store is back below the 38 MiB trim target. Nothing
    used for current operation is stored only here.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self._store: storage.Store[dict[str, Any]] = storage.Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.history.{entry.entry_id}.{subentry.subentry_id}",
        )
        self._samples: list[dict[str, Any]] = []
        self._sample_bytes: list[int] = []
        self._bytes = 0
        self._loaded = False
        self._last_signature: tuple[Any, ...] | None = None

    async def async_load(self) -> None:
        if self._loaded:
            return
        payload = await self._store.async_load() or {}
        raw = payload.get("samples")
        if isinstance(raw, list):
            self._samples = [item for item in raw if isinstance(item, dict)]
        self._sample_bytes = [_encoded_size(item) + 1 for item in self._samples]
        self._prune(dt_util.utcnow())
        self._bytes = _encoded_size(self._payload())
        self._loaded = True

    def _payload(self) -> dict[str, Any]:
        return {
            "max_bytes": ROOM_HISTORY_MAX_BYTES,
            "retention_days": int(ROOM_HISTORY_RETENTION.total_seconds() // 86400),
            "samples": self._samples,
        }

    def _signature(self, sample: dict[str, Any]) -> tuple[Any, ...]:
        return tuple((key, value) for key, value in sample.items() if key != "ts")

    def _drop_oldest(self) -> None:
        if not self._samples:
            return
        self._samples.pop(0)
        if self._sample_bytes:
            self._sample_bytes.pop(0)

    def _estimated_size(self) -> int:
        # The fixed envelope is tiny compared with the 40 MiB budget. Keep a
        # small safety margin so routine observations never need to serialize
        # the whole history just to check the cap.
        return 512 + sum(self._sample_bytes)

    def _prune(self, now: datetime) -> None:
        cutoff = now - ROOM_HISTORY_RETENTION
        while self._samples:
            try:
                stamp = dt_util.parse_datetime(str(self._samples[0].get("ts", "")))
            except (TypeError, ValueError):
                stamp = None
            if stamp is not None and stamp >= cutoff:
                break
            self._drop_oldest()

        # Fast byte-budget trim using per-sample serialized sizes. New data is
        # never rejected: oldest disposable samples are removed first.
        estimated = self._estimated_size()
        while len(self._samples) > 1 and estimated > ROOM_HISTORY_TRIM_TARGET_BYTES:
            removed = self._sample_bytes[0] if self._sample_bytes else 0
            self._drop_oldest()
            estimated -= removed

    def _enforce_exact_cap(self) -> None:
        """Verify the serialized Store payload never exceeds 40 MiB."""
        exact = _encoded_size(self._payload())
        if exact <= ROOM_HISTORY_MAX_BYTES:
            self._bytes = exact
            return
        # Remove enough old samples to get close to the trim target, then make
        # one exact verification. This avoids O(n²) full-history serialization.
        need = exact - ROOM_HISTORY_TRIM_TARGET_BYTES
        removed = 0
        while len(self._samples) > 1 and removed < need:
            removed += self._sample_bytes[0] if self._sample_bytes else 0
            self._drop_oldest()
        exact = _encoded_size(self._payload())
        while len(self._samples) > 1 and exact > ROOM_HISTORY_MAX_BYTES:
            # Extremely defensive fallback; normally the batch above is enough.
            self._drop_oldest()
            exact = _encoded_size(self._payload())
        self._bytes = exact

    def observe(self, snapshot: RoomSnapshot) -> None:
        if not self._loaded:
            return
        now = dt_util.utcnow()
        sample = _sample(snapshot, now)
        signature = self._signature(sample)
        # Exact repeated snapshots add no information. Any actual optimized
        # room value/status change is retained.
        if signature == self._last_signature:
            return
        self._last_signature = signature
        self._samples.append(sample)
        self._sample_bytes.append(_encoded_size(sample) + 1)
        self._prune(now)
        self._bytes = self._estimated_size()
        self._store.async_delay_save(self._payload_for_save, 300)

    @property
    def stats(self) -> dict[str, Any]:
        oldest = self._samples[0].get("ts") if self._samples else None
        newest = self._samples[-1].get("ts") if self._samples else None
        return {
            "history_bytes": self._bytes,
            "history_limit_bytes": ROOM_HISTORY_MAX_BYTES,
            "history_samples": len(self._samples),
            "history_oldest": oldest,
            "history_newest": newest,
        }

    def _payload_for_save(self) -> dict[str, Any]:
        self._prune(dt_util.utcnow())
        self._enforce_exact_cap()
        return self._payload()

    async def async_save(self) -> None:
        if self._loaded:
            await self._store.async_save(self._payload_for_save())


async def async_get_or_create_room_history(
    hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry
) -> RoomHistory:
    histories = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_ROOM_HISTORY, {})
    key = f"{entry.entry_id}:{subentry.subentry_id}"
    history = histories.get(key)
    if history is None:
        history = RoomHistory(hass, entry, subentry)
        histories[key] = history
        await history.async_load()
    return history


def get_room_history(hass: HomeAssistant, entry_id: str, subentry_id: str) -> RoomHistory | None:
    return hass.data.get(DOMAIN, {}).get(DATA_ROOM_HISTORY, {}).get(f"{entry_id}:{subentry_id}")


async def async_stop_entry_histories(hass: HomeAssistant, entry: ConfigEntry) -> None:
    histories = hass.data.get(DOMAIN, {}).get(DATA_ROOM_HISTORY, {})
    prefix = f"{entry.entry_id}:"
    for key in [item for item in histories if item.startswith(prefix)]:
        history = histories.pop(key)
        await history.async_save()

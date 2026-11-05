"""Bounded, observational room-air patterns (no extra polling or ML model).

Only a configured contact proves a window was opened. Sensor changes can
indicate improved air or *suspected* exchange, never confirmed window airing.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from math import isfinite
from statistics import median
from typing import Any

MAX_SAMPLES = 64
MIN_SAMPLE_INTERVAL = timedelta(minutes=15)
MAX_SAMPLE_AGE = timedelta(hours=24)
# A single drop is a recent observation, not a persistent ventilation state.
# A missing measurement must eventually clear the displayed suspicion.
MAX_OBSERVATION_AGE = timedelta(minutes=60)
GOOD_CO2 = 1000.0
# A good CO2 *level* alone is not evidence of stable air. The 400-990 ppm
# sawtooth reported in review must not silence a routine reminder.
MAX_STABLE_CO2_SPREAD = 250.0
MAX_STABLE_CO2_STEP = 160.0
_ALLOWED_POLLUTANTS = frozenset({
    "pm2_5", "pm25", "pm10", "formaldehyde", "voc", "no2", "no2_parts", "voc_parts",
})


def _value(raw: Any) -> float | None:
    try:
        num = float(raw) if raw is not None else None
        return num if num is not None and isfinite(num) else None
    except (TypeError, ValueError):
        return None


def _pollutants(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    clean: dict[str, float] = {}
    for key, value in raw.items():
        if key in _ALLOWED_POLLUTANTS:
            number = _value(value)
            if number is not None and number >= 0:
                clean[key] = number
    return clean


class RoomAirPattern:
    """Observe at most 64 sparse samples with independently missing sensors."""

    def __init__(self) -> None:
        # timestamp, CO2, relative humidity, temperature, pollutants
        self._samples: deque[tuple[datetime, float | None, float | None,
                                    float | None, dict[str, float]]] = deque(maxlen=MAX_SAMPLES)
        self._source_stamp: datetime | None = None
        self._last_observation = "none"

    def invalidate_for_open_window(self) -> bool:
        """Do not learn background ventilation from an actual open window."""
        changed = bool(self._samples)
        self._samples.clear()
        self._last_observation = "contact_confirmed"
        return changed

    def restore(self, data: Any, *, now: datetime) -> None:
        if not isinstance(data, dict):
            return
        restored = deque(maxlen=MAX_SAMPLES)
        rows = data.get("samples", [])
        if not isinstance(rows, list):
            rows = []
        for row in rows[-MAX_SAMPLES:]:
            # Compatible with the original four-column v0.12.0 layout.
            if not isinstance(row, list) or len(row) not in (4, 5):
                continue
            try:
                when = datetime.fromisoformat(row[0])
            except (ValueError, TypeError):
                continue
            if when.tzinfo is None or when > now or now - when > MAX_SAMPLE_AGE:
                continue
            c, h, temp = (_value(v) for v in row[1:4])
            if c is not None and not (250 <= c <= 10000):
                c = None
            if h is not None and not (0 <= h <= 100):
                h = None
            if temp is not None and not (-40 <= temp <= 60):
                temp = None
            particle_values = _pollutants(row[4]) if len(row) == 5 else {}
            if all(value is None for value in (c, h, temp)) and not particle_values:
                continue
            if restored and when <= restored[-1][0]:
                continue
            restored.append((when, c, h, temp, particle_values))
        self._samples = restored
        source = data.get("source_stamp")
        try:
            stamp = datetime.fromisoformat(source) if isinstance(source, str) else None
        except ValueError:
            stamp = None
        self._source_stamp = stamp if stamp is not None and stamp.tzinfo is not None and stamp <= now else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "samples": [[t.isoformat(), c, h, temp, particles]
                        for t, c, h, temp, particles in self._samples],
            "source_stamp": self._source_stamp.isoformat() if self._source_stamp else None,
        }

    def observe(self, *, now: datetime, source_stamp: datetime | None,
                co2: Any, humidity: Any, temperature: Any, window_open: bool,
                pollutants: Any = None) -> bool:
        """Require an actual sensor update; no coordinator-tick observations."""
        c, h, temp = _value(co2), _value(humidity), _value(temperature)
        particle_values = _pollutants(pollutants)
        if source_stamp is None or source_stamp.tzinfo is None or source_stamp > now:
            return False
        if self._source_stamp is not None and source_stamp <= self._source_stamp:
            return False
        self._source_stamp = source_stamp
        if c is not None and not (250 <= c <= 10000):
            c = None
        if h is not None and not (0 <= h <= 100):
            h = None
        if temp is not None and not (-40 <= temp <= 60):
            temp = None
        if all(v is None for v in (c, h, temp)) and not particle_values:
            return False
        if window_open:
            return self.invalidate_for_open_window()
        if self._samples and now - self._samples[-1][0] < MIN_SAMPLE_INTERVAL:
            return False
        prior = self._samples[-1] if self._samples else None
        if prior is not None and now - prior[0] > timedelta(hours=2):
            self._last_observation = "none"
        self._samples.append((now, c, h, temp, particle_values))
        while self._samples and now - self._samples[0][0] > MAX_SAMPLE_AGE:
            self._samples.popleft()
        if prior is not None and timedelta(0) < now - prior[0] <= timedelta(hours=2):
            hours = (now - prior[0]).total_seconds() / 3600
            history = self._recent_slopes()
            baseline = median(abs(v) for v in history) if history else 0.0
            slope = (c - prior[1]) / hours if c is not None and prior[1] is not None else None
            particulate_improved = any(
                value < prior[4][key]
                for key, value in particle_values.items() if key in prior[4]
            )
            if slope is not None and slope < -max(25.0, baseline * 2.8):
                self._last_observation = "exchange_suspected"
            elif ((c is not None and prior[1] is not None and c < prior[1])
                  or (h is not None and prior[2] is not None and h < prior[2])
                  or particulate_improved):
                self._last_observation = "air_improved"
            else:
                self._last_observation = "none"
        return True

    def _recent_slopes(self) -> list[float]:
        values = list(self._samples)[-20:]
        slopes = []
        for old, new in zip(values, values[1:]):
            hours = (new[0] - old[0]).total_seconds() / 3600
            if 0.1 <= hours <= 2 and old[1] is not None and new[1] is not None:
                slopes.append((new[1] - old[1]) / hours)
        return slopes[:-1]  # latest drop must not inflate its own baseline

    def stable_good(self, *, now: datetime, passive_hint: bool = False, co2_fresh: bool = True) -> bool:
        """Sustained *stable* measurements can defer routine-only reminders.

        A configured passive inlet reduces required observation from 12h to 8h,
        but never overrides sensor proof or safety/other ventilation needs.
        Without CO2 readings we cannot establish that the entire air is good.
        """
        if not co2_fresh or len(self._samples) < 20 or now - self._samples[-1][0] > timedelta(minutes=45):
            return False
        samples = [s for s in self._samples if now - s[0] <= timedelta(hours=14)]
        required = timedelta(hours=8 if passive_hint else 12)
        if (len(samples) < (20 if passive_hint else 28)
                or samples[-1][0] - samples[0][0] < required):
            return False
        if any(s[1] is None or not (350 <= s[1] < GOOD_CO2)
               or s[2] is None or not (35 <= s[2] <= 60)
               for s in samples):
            return False
        co2 = [s[1] for s in samples]
        if max(co2) - min(co2) > MAX_STABLE_CO2_SPREAD:
            return False
        if any(abs(a - b) > MAX_STABLE_CO2_STEP for a, b in zip(co2, co2[1:])):
            return False
        # Missing an entire stretch of measurements is not "stable" evidence.
        if any(new[0] - old[0] > timedelta(minutes=70)
               for old, new in zip(samples, samples[1:])):
            return False
        return True

    def next_observation_check(self, *, now: datetime) -> float | None:
        """One-shot expiry deadline for an observed event, not another poll."""
        if self._last_observation not in {"air_improved", "exchange_suspected"} or not self._samples:
            return None
        remaining = (self._samples[-1][0] + MAX_OBSERVATION_AGE - now).total_seconds()
        return max(0.0, remaining) if remaining >= 0 else None

    def summary(self, *, now: datetime, contact_open: bool, passive_hint: bool,
                co2_fresh: bool = True) -> dict[str, Any]:
        # Sample history is kept for learning, but a *displayed event* is only
        # meaningful while its most recent sensor observation is still fresh.
        # Never expire the independent real-time window-contact indication.
        observation_fresh = bool(
            self._samples
            and timedelta(0) <= now - self._samples[-1][0] <= MAX_OBSERVATION_AGE
        )
        status = (
            "contact_confirmed" if contact_open else
            self._last_observation if observation_fresh
            and self._last_observation != "contact_confirmed" else "none"
        )
        return {
            "status": status,
            "proven_window_airing": bool(contact_open),
            "passive_ventilation_configured": bool(passive_hint),
            "stable_good_air": self.stable_good(
                now=now, passive_hint=passive_hint, co2_fresh=co2_fresh
            ),
            "samples": len(self._samples),
            "mode": "observation",
        }

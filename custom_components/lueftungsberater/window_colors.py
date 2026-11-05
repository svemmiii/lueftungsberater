"""Window-contact colour boundary protections for the *room-air* perspective.

The native ventilation action and official safety decisions are never modified.
A short airing is always unconfirmed; an exceptional green close only describes
independently good measured room air, not a successfully completed session.
"""
from __future__ import annotations

from typing import Any


def _numeric(value: Any) -> float | None:
    try:
        number = float(value)
        from math import isfinite
        return number if isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _fresh_worsening(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """A real independent deterioration is allowed to worsen the colour."""
    # Even a small real change may cross an independently actionable engine
    # threshold. Do not mask that escalation merely because it is smaller than
    # the normal sensor-noise allowance.
    for key, tolerance, boundaries in (
        ("co2_ppm", 15.0, (1000.0, 1400.0, 2000.0)),
        ("humidity_inside", 0.8, (60.0, 65.0, 75.0)),
    ):
        old, new = _numeric(before.get(key)), _numeric(after.get(key))
        if old is not None and new is not None and new > old:
            if new > old + tolerance or any(old < edge <= new for edge in boundaries):
                return True
    old_h, new_h = _numeric(before.get("humidity_inside")), _numeric(after.get("humidity_inside"))
    if old_h is not None and new_h is not None and old_h >= 40 > new_h:
        return True
    old_t, new_t = _numeric(before.get("temperature_inside")), _numeric(after.get("temperature_inside"))
    target = _numeric(after.get("target_temperature"))
    if old_t is not None and new_t is not None and target is not None:
        if abs(new_t - target) > abs(old_t - target) + 0.25:
            return True
    if (after.get("mold_risk") and not before.get("mold_risk")) or (
        after.get("mold_persistent") and not before.get("mold_persistent")
    ):
        return True
    quality_rank = {"very_good": 0, "good": 0, "moderate": 1, "poor": 2, "very_poor": 3}
    old_quality = quality_rank.get(str(before.get("indoor_air_quality")), -1)
    new_quality = quality_rank.get(str(after.get("indoor_air_quality")), -1)
    if new_quality > old_quality and new_quality >= 1:
        return True
    return False


def exceptional_short_airing_good(
    previous: Any, current: Any, *, original_reasons: tuple[str, ...] | None = None
) -> bool:
    """15% reserve *inside* the measurable good interval, not 15% of U.

    CO2: 400–1000 ppm reference good interval -> <=910 ppm.
    Humidity: 40–60% engine good interval -> 43–57%.
    Temperature: room target +/-1 C -> within +/-0.85 C.
    Other reasons must be independently cleared by the ordinary engine.
    """
    result = current.result
    old_result = previous.result
    if result is None or old_result is None or result.safety_lock:
        return False
    if result.room_status_color != "green":
        return False
    if result.active_reasons or result.mold_risk or result.mold_persistent:
        return False
    # Do not turn unquantified, medical/PM, stale, safety, routine or unknown
    # reasons into a fictitious successful window session.
    eligible = {"co2_elevated", "co2_high", "co2_critical", "humidity", "humidity_urgent", "temperature"}
    reasons = set(old_result.active_reasons if original_reasons is None else original_reasons)
    if not reasons.issubset(eligible):
        return False
    v = current.values
    co2 = _numeric(v.get("co2_ppm"))
    co2_was_trigger = bool(reasons & {"co2_elevated", "co2_high", "co2_critical"})
    if co2_was_trigger and not v.get("has_co2"):
        return False
    if (v.get("has_co2") or co2_was_trigger) and (co2 is None or co2 > 910):
        return False
    humidity = _numeric(v.get("humidity_inside"))
    # Absent optional sensors do not make their made-up reading "good"; only
    # configured, available values can be verified. If humidity was a trigger
    # for this very attempt, it is mandatory evidence of recovery.
    if "humidity" in (original_reasons if original_reasons is not None else old_result.active_reasons) or "humidity_urgent" in (original_reasons if original_reasons is not None else old_result.active_reasons):
        if humidity is None:
            return False
    if humidity is not None and not (43 <= humidity <= 57):
        return False
    temp = _numeric(v.get("temperature_inside"))
    target = _numeric(v.get("target_temperature"))
    if "temperature" in (original_reasons if original_reasons is not None else old_result.active_reasons):
        if temp is None or target is None:
            return False
    if temp is not None and target is not None and abs(temp - target) > 0.85:
        return False
    if v.get("indoor_air_quality") in {"moderate", "poor", "very_poor"}:
        return False
    if v.get("window_data_status") == "unavailable":
        return False
    return True


def protect_room_color(
    previous: Any, current: Any, *, short_close: bool, opening: bool,
    closing: bool = False, hold_after_abort: bool = False,
    independent_recovery: bool = False,
    original_reasons: tuple[str, ...] | None = None,
) -> bool:
    """Protect green/non-green on contact transitions and below five minutes.

    Return whether the room presentation was stabilized. No intervention at a
    real safety lock, and worsening raw readings are never concealed.
    """
    if previous is None or previous.result is None or current.result is None:
        return False
    before, after = previous.result, current.result
    if before.safety_lock or after.safety_lock:
        return False
    old_green = before.room_status_color == "green"
    new_green = after.room_status_color == "green"
    if old_green == new_green:
        return False
    if not current.values.get("has_window_contacts") or current.values.get("window_data_status") == "unavailable":
        return False
    window_now_open = bool(current.values.get("window_open"))
    minutes = _numeric(current.values.get("open_minutes"))
    early_open = window_now_open and minutes is not None and minutes < 5
    if not (opening or closing or early_open or hold_after_abort):
        return False
    if (short_close or (hold_after_abort and independent_recovery)) and not old_green and new_green and exceptional_short_airing_good(
        previous, current, original_reasons=original_reasons
    ):
        return False
    if old_green and not new_green and (
        _fresh_worsening(previous.values, current.values)
        or (after.mold_risk and not before.mold_risk)
        or (after.mold_persistent and not before.mold_persistent)
    ):
        return False
    if old_green and not new_green and after.mode in {
        "wetter_vorsicht", "wetter_stark_nachteilig", "nina_vorsicht",
    } and after.mode != before.mode:
        return False
    # Keep measured data + the native action as-is; only room-facing advice is
    # stabilized. A closing/finishing action is not proof that air is good.
    after.room_status_color = before.room_status_color
    after.room_recommendation_key = (
        "room_good" if old_green and not window_now_open else
        "can_close" if old_green else
        "room_keep_brief" if window_now_open else "room_need"
    )
    if not old_green:
        after.room_reason_key = "room_perspective"
        args = dict(after.room_reason_args)
        args.update({"need": before.primary_need, "room_color": before.room_status_color})
        after.room_reason_args = args
    return True

# Persist only the handful of raw measurements needed to distinguish a genuine
# later improvement from an otherwise identical recalculation after an abort.
_GUARD_INPUTS = (
    "co2_ppm", "humidity_inside", "temperature_inside", "target_temperature",
    "indoor_air_quality", "indoor_air_quality_values", "mold_risk",
    "mold_persistent", "surface_temperature", "air_quality_unusual",
)


class ShortAiringColorGuard:
    """Remember unresolved closes across coordinator ticks and restarts.

    A short aborted session needs the special 15% release. A time-confirmed
    but unfinished humidity session uses its normal completion criteria.
    Neither guard changes the factual ventilation/session history.
    """

    def __init__(self) -> None:
        self.baseline: dict[str, Any] | None = None
        self.reasons: tuple[str, ...] = ()
        self.color = "orange"
        self.humidity_unresolved = False

    def clear(self) -> None:
        self.baseline = None
        self.reasons = ()
        self.humidity_unresolved = False

    def as_dict(self) -> dict[str, Any] | None:
        if self.baseline is None:
            return None
        return {"baseline": self.baseline, "reasons": list(self.reasons),
                "color": self.color, "humidity_unresolved": self.humidity_unresolved}

    def restore(self, data: Any) -> None:
        self.clear()
        if not isinstance(data, dict) or not isinstance(data.get("baseline"), dict):
            return
        baseline = data["baseline"]
        if any(key not in _GUARD_INPUTS for key in baseline):
            return
        self.baseline = {key: baseline.get(key) for key in _GUARD_INPUTS}
        reasons = data.get("reasons")
        self.reasons = tuple(v for v in reasons if isinstance(v, str)) if isinstance(reasons, list) else ()
        color = data.get("color")
        self.color = color if color in {"yellow", "orange", "red"} else "orange"
        self.humidity_unresolved = bool(data.get("humidity_unresolved", False))

    def apply(self, previous: Any, current: Any, *, short_close: bool,
              opening: bool, closing: bool,
              unresolved_humidity_close: bool = False,
              unresolved_humidity_active: bool = False) -> bool:
        result = current.result
        if result is None:
            return False
        if current.values.get("window_open") and (_numeric(current.values.get("open_minutes")) or 0) >= 5:
            self.clear()
        if (short_close or unresolved_humidity_close) and previous is not None and previous.result is not None:
            prior = previous.result
            if prior.room_status_color != "green" and (
                unresolved_humidity_close or not exceptional_short_airing_good(previous, current)
            ):
                self.baseline = {key: current.values.get(key) for key in _GUARD_INPUTS}
                self.reasons = tuple(prior.active_reasons)
                self.color = prior.room_status_color
                self.humidity_unresolved = bool(unresolved_humidity_close)
            else:
                self.clear()

        if self.baseline is not None and self.humidity_unresolved:
            # A completed five-minute duration is not a completed humidity
            # reason. The colour may clear only once the source readings have
            # improved and the *normal* humidity rules release the need.
            current_rh = _numeric(current.values.get("humidity_inside"))
            closing_rh = _numeric(self.baseline.get("humidity_inside"))
            real_resolution = (
                not unresolved_humidity_active
                and current_rh is not None and closing_rh is not None
                and current_rh < 60 and current_rh < closing_rh
                and not ({"humidity", "humidity_urgent"} & set(result.active_reasons))
            )
            if real_resolution:
                self.clear()

        if (self.baseline is not None and not self.humidity_unresolved
                and result.room_status_color == "green"):
            # A second refresh with identical data is NOT new evidence. Even
            # on actual recovery, the ordinary engine and 15% reserve must
            # independently agree and original nonnumeric reasons must clear.
            changed = any(current.values.get(k) != v for k, v in self.baseline.items())
            if (changed and previous is not None and previous.result is not None
                    and exceptional_short_airing_good(
                        previous, current, original_reasons=self.reasons
                    )):
                self.clear()

        if previous is None:
            if (self.baseline is not None and result.room_status_color == "green"
                    and not result.safety_lock and current.values.get("has_window_contacts")):
                result.room_status_color = self.color
                result.room_recommendation_key = (
                    "room_keep_brief" if current.values.get("window_open") else "room_need"
                )
                result.room_reason_key = "room_perspective"
                result.room_reason_args = {
                    **result.room_reason_args, "room_color": self.color,
                }
                return True
            return False
        return protect_room_color(
            previous, current, short_close=short_close, opening=opening,
            closing=closing, hold_after_abort=self.baseline is not None,
            original_reasons=self.reasons,
        )

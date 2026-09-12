"""Small timestamp-safety helpers shared by persisted state restorers."""
from __future__ import annotations

from datetime import datetime, timedelta


def timestamp_age(now: datetime, stamp: datetime | None) -> timedelta | None:
    """Return a non-negative age, or None for missing/future timestamps."""
    if stamp is None:
        return None
    age = now - stamp
    if age < timedelta(0):
        return None
    return age


def timestamp_is_fresh(
    now: datetime,
    stamp: datetime | None,
    max_age: timedelta,
    *,
    inclusive: bool = True,
) -> bool:
    """Return whether a persisted timestamp is present, not future, and fresh."""
    age = timestamp_age(now, stamp)
    if age is None:
        return False
    return age <= max_age if inclusive else age < max_age


def clamp_not_future(now: datetime, stamp: datetime | None) -> datetime | None:
    """Discard a persisted timestamp that lies in the future."""
    if stamp is None or stamp > now:
        return None
    return stamp


def utc_timeline(value: datetime) -> datetime:
    """Normalize an aware datetime to its absolute UTC timeline."""
    # All integration persistence helpers normalize naive datetimes to UTC before
    # reaching this function. datetime.astimezone() therefore also handles DST
    # folds correctly because the fold is resolved by the timezone object.
    from homeassistant.util import dt as dt_util

    if value.tzinfo is None:
        value = value.replace(tzinfo=dt_util.UTC)
    return value.astimezone(dt_util.UTC)

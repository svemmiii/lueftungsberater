from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from custom_components.lueftungsberater.time_utils import (
    clamp_not_future,
    timestamp_is_fresh,
    utc_timeline,
)


def test_future_persisted_timestamp_is_never_fresh() -> None:
    now = datetime(2026, 9, 11, 20, 0, tzinfo=timezone.utc)
    future = now + timedelta(hours=1)
    assert timestamp_is_fresh(now, future, timedelta(days=1)) is False
    assert clamp_not_future(now, future) is None


def test_utc_timeline_distinguishes_both_dst_fold_hours() -> None:
    berlin = ZoneInfo("Europe/Berlin")
    first = datetime(2026, 10, 25, 2, 30, tzinfo=berlin, fold=0)
    second = datetime(2026, 10, 25, 2, 30, tzinfo=berlin, fold=1)

    assert utc_timeline(first) < utc_timeline(second)
    assert utc_timeline(second) - utc_timeline(first) == timedelta(hours=1)

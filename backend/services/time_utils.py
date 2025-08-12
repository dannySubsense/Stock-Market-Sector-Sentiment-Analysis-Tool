"""
Time utilities for consistent UTC↔ET conversion and metadata formatting.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any


NEW_YORK_TZ = ZoneInfo("America/New_York")


def utc_to_et_fields(ts_utc: datetime) -> Dict[str, Any]:
    """
    Given a UTC datetime (aware or naive), return ET string and tz metadata.
    """
    if ts_utc.tzinfo is None:
        ts_utc = ts_utc.replace(tzinfo=timezone.utc)

    ts_et = ts_utc.astimezone(NEW_YORK_TZ)
    offset_minutes = int(ts_et.utcoffset().total_seconds() // 60) if ts_et.utcoffset() else 0
    is_dst = bool(ts_et.dst() and ts_et.dst().total_seconds() != 0)

    return {
        "timestamp_utc": ts_utc.isoformat(),
        "timestamp_et": ts_et.isoformat(),
        "tz": "America/New_York",
        "tz_offset_minutes": offset_minutes,
        "is_dst": is_dst,
    }




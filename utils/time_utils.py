from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_stale(ts_epoch_ms: int, max_age_ms: int, now: datetime | None = None) -> bool:
    ref = now or utc_now()
    age_ms = int(ref.timestamp() * 1000) - ts_epoch_ms
    return age_ms > max_age_ms

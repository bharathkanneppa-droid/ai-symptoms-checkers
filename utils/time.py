"""Timezone helpers."""
from datetime import datetime, timezone


def utcnow():
    """Naive-UTC datetime (tzinfo stripped) — avoids the deprecated
    ``datetime.utcnow()`` while keeping naive-UTC column semantics."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

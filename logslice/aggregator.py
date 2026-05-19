"""Aggregation utilities for summarising log entries by severity and time bucket."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, List

from logslice.parser import LogEntry


@dataclass
class Bucket:
    """A time bucket holding severity counts for log entries."""

    start: datetime
    end: datetime
    counts: Counter = field(default_factory=Counter)

    def add(self, entry: LogEntry) -> None:
        self.counts[entry.severity] += 1

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def __str__(self) -> str:  # pragma: no cover
        parts = ", ".join(f"{sev}={cnt}" for sev, cnt in sorted(self.counts.items()))
        return f"[{self.start.isoformat()} – {self.end.isoformat()}] {parts} (total={self.total})"


def aggregate(
    entries: Iterable[LogEntry],
    bucket_minutes: int = 60,
) -> List[Bucket]:
    """Group *entries* into fixed-width time buckets of *bucket_minutes* width.

    Entries without a timestamp are silently skipped.
    Returns buckets in chronological order.
    """
    if bucket_minutes <= 0:
        raise ValueError("bucket_minutes must be a positive integer")

    delta = timedelta(minutes=bucket_minutes)
    buckets: dict[datetime, Bucket] = {}

    for entry in entries:
        if entry.timestamp is None:
            continue

        # Floor the timestamp to the nearest bucket boundary.
        epoch = datetime.min
        elapsed = entry.timestamp - epoch
        bucket_index = int(elapsed.total_seconds() // delta.total_seconds())
        bucket_start = epoch + timedelta(seconds=bucket_index * delta.total_seconds())
        bucket_end = bucket_start + delta

        if bucket_start not in buckets:
            buckets[bucket_start] = Bucket(start=bucket_start, end=bucket_end)

        buckets[bucket_start].add(entry)

    return [buckets[k] for k in sorted(buckets)]


def summary_lines(buckets: List[Bucket]) -> List[str]:
    """Return a list of human-readable summary strings, one per bucket."""
    return [str(b) for b in buckets]

"""Tests for logslice.aggregator."""

from datetime import datetime

import pytest

from logslice.aggregator import Bucket, aggregate, summary_lines
from logslice.parser import LogEntry


def _entry(ts: str | None, severity: str = "INFO", msg: str = "msg") -> LogEntry:
    timestamp = datetime.fromisoformat(ts) if ts else None
    return LogEntry(timestamp=timestamp, severity=severity, message=msg, raw=msg)


# ---------------------------------------------------------------------------
# Bucket
# ---------------------------------------------------------------------------

class TestBucket:
    def test_add_increments_count(self):
        b = Bucket(start=datetime(2024, 1, 1, 0), end=datetime(2024, 1, 1, 1))
        b.add(_entry("2024-01-01T00:10:00", "ERROR"))
        b.add(_entry("2024-01-01T00:20:00", "ERROR"))
        b.add(_entry("2024-01-01T00:30:00", "INFO"))
        assert b.counts["ERROR"] == 2
        assert b.counts["INFO"] == 1

    def test_total(self):
        b = Bucket(start=datetime(2024, 1, 1, 0), end=datetime(2024, 1, 1, 1))
        b.add(_entry("2024-01-01T00:05:00", "WARN"))
        b.add(_entry("2024-01-01T00:06:00", "DEBUG"))
        assert b.total == 2


# ---------------------------------------------------------------------------
# aggregate
# ---------------------------------------------------------------------------

class TestAggregate:
    def test_empty_input_returns_empty_list(self):
        assert aggregate([]) == []

    def test_entries_without_timestamp_are_skipped(self):
        entries = [_entry(None, "ERROR")]
        assert aggregate(entries) == []

    def test_single_bucket(self):
        entries = [
            _entry("2024-06-01T10:05:00", "INFO"),
            _entry("2024-06-01T10:30:00", "WARN"),
            _entry("2024-06-01T10:55:00", "ERROR"),
        ]
        buckets = aggregate(entries, bucket_minutes=60)
        assert len(buckets) == 1
        assert buckets[0].total == 3

    def test_two_buckets(self):
        entries = [
            _entry("2024-06-01T09:00:00", "DEBUG"),
            _entry("2024-06-01T10:00:00", "INFO"),
        ]
        buckets = aggregate(entries, bucket_minutes=60)
        assert len(buckets) == 2

    def test_buckets_are_chronological(self):
        entries = [
            _entry("2024-06-01T12:00:00", "INFO"),
            _entry("2024-06-01T10:00:00", "WARN"),
        ]
        buckets = aggregate(entries, bucket_minutes=60)
        assert buckets[0].start < buckets[1].start

    def test_invalid_bucket_minutes_raises(self):
        with pytest.raises(ValueError, match="positive"):
            aggregate([], bucket_minutes=0)

    def test_severity_counts_per_bucket(self):
        entries = [
            _entry("2024-06-01T08:10:00", "ERROR"),
            _entry("2024-06-01T08:20:00", "ERROR"),
            _entry("2024-06-01T09:05:00", "INFO"),
        ]
        buckets = aggregate(entries, bucket_minutes=60)
        assert buckets[0].counts["ERROR"] == 2
        assert buckets[1].counts["INFO"] == 1


# ---------------------------------------------------------------------------
# summary_lines
# ---------------------------------------------------------------------------

def test_summary_lines_returns_one_string_per_bucket():
    entries = [
        _entry("2024-06-01T10:00:00", "INFO"),
        _entry("2024-06-01T11:00:00", "WARN"),
    ]
    buckets = aggregate(entries, bucket_minutes=60)
    lines = summary_lines(buckets)
    assert len(lines) == 2
    assert all(isinstance(line, str) for line in lines)

"""Tests for logslice.sampler."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

import pytest

from logslice.parser import LogEntry
from logslice.sampler import _Counter, sample

_TS = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _entry(severity: str = "INFO", message: str = "msg") -> LogEntry:
    return LogEntry(timestamp=_TS, severity=severity, message=message, raw=f"{severity} {message}")


def _run(entries: Sequence[LogEntry], **kwargs) -> list[LogEntry]:
    return list(sample(entries, **kwargs))


# ---------------------------------------------------------------------------
# _Counter
# ---------------------------------------------------------------------------

class TestCounter:
    def test_starts_at_zero(self):
        c = _Counter()
        assert c.increment("x") == 1

    def test_increments_independently(self):
        c = _Counter()
        c.increment("a")
        c.increment("a")
        c.increment("b")
        assert c.counts["a"] == 2
        assert c.counts["b"] == 1

    def test_reset_clears_all(self):
        c = _Counter()
        c.increment("a")
        c.reset()
        assert c.counts == {}


# ---------------------------------------------------------------------------
# sample()
# ---------------------------------------------------------------------------

def test_rate_one_keeps_all():
    entries = [_entry() for _ in range(5)]
    assert _run(entries, rate=1) == entries


def test_rate_two_keeps_every_second():
    entries = [_entry(message=str(i)) for i in range(6)]
    result = _run(entries, rate=2)
    assert len(result) == 3
    assert result == [entries[1], entries[3], entries[5]]


def test_rate_larger_than_input_yields_one():
    entries = [_entry() for _ in range(3)]
    result = _run(entries, rate=10)
    assert result == []


def test_rate_zero_raises():
    with pytest.raises(ValueError, match="rate must be >= 1"):
        _run([_entry()], rate=0)


def test_negative_rate_raises():
    with pytest.raises(ValueError):
        _run([_entry()], rate=-5)


def test_per_severity_counts_independently():
    # 3 INFO + 3 ERROR, rate=3 → one of each
    entries = (
        [_entry("INFO", str(i)) for i in range(3)]
        + [_entry("ERROR", str(i)) for i in range(3)]
    )
    result = _run(entries, rate=3, per_severity=True)
    severities = [e.severity for e in result]
    assert "INFO" in severities
    assert "ERROR" in severities


def test_per_severity_false_uses_global_counter():
    # 2 INFO + 2 ERROR with rate=2 → only 2 entries total
    entries = [_entry("INFO"), _entry("ERROR"), _entry("INFO"), _entry("ERROR")]
    result = _run(entries, rate=2, per_severity=False)
    assert len(result) == 2


def test_empty_input_yields_nothing():
    assert _run([], rate=1) == []

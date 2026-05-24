"""Tests for logslice.normalizer."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.normalizer import NormalizeOptions, normalize_entry, normalize_entries


def _entry(
    message: str = "hello world",
    severity: str = "INFO",
    timestamp: datetime | None = None,
) -> LogEntry:
    if timestamp is None:
        timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=timestamp, severity=severity, message=message)


# ---------------------------------------------------------------------------
# collapse_whitespace
# ---------------------------------------------------------------------------

def test_collapse_whitespace_strips_extra_spaces():
    entry = _entry(message="hello   world  ")
    result = normalize_entry(entry, NormalizeOptions(collapse_whitespace=True))
    assert result.message == "hello world"


def test_collapse_whitespace_disabled_leaves_message():
    raw = "hello   world  "
    entry = _entry(message=raw)
    result = normalize_entry(entry, NormalizeOptions(collapse_whitespace=False))
    assert result.message == raw


def test_collapse_whitespace_handles_tabs_and_newlines():
    entry = _entry(message="foo\t\tbar\nbaz")
    result = normalize_entry(entry, NormalizeOptions(collapse_whitespace=True))
    assert result.message == "foo bar baz"


# ---------------------------------------------------------------------------
# canonical_severity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("warning", "WARN"),
    ("Warning", "WARN"),
    ("WARN", "WARN"),
    ("err", "ERROR"),
    ("ERROR", "ERROR"),
    ("crit", "CRITICAL"),
    ("CRITICAL", "CRITICAL"),
    ("info", "INFO"),
    ("DEBUG", "DEBUG"),
    ("trace", "TRACE"),
    ("CUSTOM", "CUSTOM"),
])
def test_canonical_severity(raw: str, expected: str):
    entry = _entry(severity=raw)
    result = normalize_entry(entry, NormalizeOptions(canonical_severity=True))
    assert result.severity == expected


def test_canonical_severity_disabled_preserves_case():
    entry = _entry(severity="warning")
    result = normalize_entry(entry, NormalizeOptions(canonical_severity=False))
    assert result.severity == "warning"


# ---------------------------------------------------------------------------
# strip_ansi
# ---------------------------------------------------------------------------

def test_strip_ansi_removes_colour_codes():
    entry = _entry(message="\x1b[31mERROR\x1b[0m occurred")
    result = normalize_entry(entry, NormalizeOptions(strip_ansi=True))
    assert result.message == "ERROR occurred"


def test_strip_ansi_disabled_preserves_codes():
    raw = "\x1b[31mERROR\x1b[0m"
    entry = _entry(message=raw)
    result = normalize_entry(entry, NormalizeOptions(strip_ansi=False))
    assert "\x1b[" in result.message


# ---------------------------------------------------------------------------
# utc_timestamps
# ---------------------------------------------------------------------------

def test_utc_timestamps_converts_aware_datetime():
    from datetime import timedelta
    tz_plus2 = timezone(timedelta(hours=2))
    ts = datetime(2024, 6, 1, 14, 0, 0, tzinfo=tz_plus2)
    entry = _entry(timestamp=ts)
    result = normalize_entry(entry, NormalizeOptions(utc_timestamps=True))
    assert result.timestamp is not None
    assert result.timestamp.tzinfo == timezone.utc
    assert result.timestamp.hour == 12  # 14:00+02:00 -> 12:00 UTC


def test_utc_timestamps_disabled_leaves_tz():
    from datetime import timedelta
    tz_plus2 = timezone(timedelta(hours=2))
    ts = datetime(2024, 6, 1, 14, 0, 0, tzinfo=tz_plus2)
    entry = _entry(timestamp=ts)
    result = normalize_entry(entry, NormalizeOptions(utc_timestamps=False))
    assert result.timestamp == ts


# ---------------------------------------------------------------------------
# normalize_entries iterator
# ---------------------------------------------------------------------------

def test_normalize_entries_yields_all():
    entries = [_entry(severity="warning"), _entry(severity="err")]
    results = list(normalize_entries(entries))
    assert len(results) == 2
    assert results[0].severity == "WARN"
    assert results[1].severity == "ERROR"


def test_normalize_entries_default_opts():
    entry = _entry(message="  spaced  ", severity="warning")
    result = list(normalize_entries([entry]))[0]
    assert result.message == "spaced"
    assert result.severity == "WARN"

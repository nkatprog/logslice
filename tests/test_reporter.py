"""Tests for logslice.reporter."""

from __future__ import annotations

from datetime import datetime
from io import StringIO

import pytest

from logslice.parser import LogEntry
from logslice.reporter import (
    _severity_bar,
    format_summary,
    severity_summary,
    write_summary,
)


def _entry(severity: str, message: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01 12:00:00 {severity} {message}",
    )


# ---------------------------------------------------------------------------
# _severity_bar
# ---------------------------------------------------------------------------

class TestSeverityBar:
    def test_full_bar(self):
        bar = _severity_bar(10, 10, width=10)
        assert bar == "[##########]"

    def test_empty_bar(self):
        bar = _severity_bar(0, 10, width=10)
        assert bar == "[----------]"

    def test_half_bar(self):
        bar = _severity_bar(5, 10, width=10)
        assert bar == "[#####-----]"

    def test_zero_max_returns_empty(self):
        bar = _severity_bar(0, 0, width=8)
        assert bar == "[--------]"


# ---------------------------------------------------------------------------
# severity_summary
# ---------------------------------------------------------------------------

class TestSeveritySummary:
    def test_counts_known_severities(self):
        entries = [
            _entry("INFO"),
            _entry("INFO"),
            _entry("ERROR"),
            _entry("WARN"),
        ]
        counts = severity_summary(entries)
        assert counts["INFO"] == 2
        assert counts["ERROR"] == 1
        assert counts["WARN"] == 1
        assert counts["DEBUG"] == 0

    def test_empty_entries_all_zero(self):
        counts = severity_summary([])
        assert all(v == 0 for v in counts.values())

    def test_unknown_severity_counted(self):
        entries = [_entry("TRACE")]
        counts = severity_summary(entries)
        assert counts.get("TRACE", 0) == 1


# ---------------------------------------------------------------------------
# format_summary
# ---------------------------------------------------------------------------

def test_format_summary_contains_title():
    counts = {"INFO": 5, "ERROR": 2, "WARN": 1, "DEBUG": 0, "CRITICAL": 0}
    result = format_summary(counts, title="My Report")
    assert "My Report" in result


def test_format_summary_contains_total():
    counts = {"INFO": 3, "ERROR": 1, "WARN": 0, "DEBUG": 0, "CRITICAL": 0}
    result = format_summary(counts)
    assert "4" in result  # total = 3 + 1


def test_format_summary_lists_all_severities():
    counts = {sev: 0 for sev in ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]}
    result = format_summary(counts)
    for sev in ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]:
        assert sev in result


# ---------------------------------------------------------------------------
# write_summary
# ---------------------------------------------------------------------------

def test_write_summary_writes_to_stream():
    entries = [_entry("INFO"), _entry("ERROR"), _entry("INFO")]
    buf = StringIO()
    write_summary(entries, buf, title="Stream Test")
    output = buf.getvalue()
    assert "Stream Test" in output
    assert "INFO" in output
    assert "ERROR" in output

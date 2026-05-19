"""Tests for logslice.parser and logslice.filter."""

import io
from datetime import datetime
from unittest.mock import patch, mock_open

import pytest

from logslice.parser import parse_line, LogEntry
from logslice.filter import filter_entries, filter_file


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestParseLine:
    def test_iso_timestamp_error(self):
        line = "2024-03-10T08:15:00.000Z [ERROR] Disk full"
        entry = parse_line(line)
        assert entry.timestamp == datetime(2024, 3, 10, 8, 15, 0)
        assert entry.severity == "ERROR"
        assert entry.message == "Disk full"

    def test_space_timestamp_info(self):
        line = "2024-03-10 08:15:00,123 [INFO] Server started"
        entry = parse_line(line)
        assert entry.timestamp == datetime(2024, 3, 10, 8, 15, 0, 123000)
        assert entry.severity == "INFO"

    def test_warning_normalised_to_warn(self):
        line = "2024-03-10T09:00:00Z [WARNING] Low memory"
        entry = parse_line(line)
        assert entry.severity == "WARN"

    def test_unparsed_line(self):
        line = "This is a plain text line with no structure"
        entry = parse_line(line)
        assert entry.timestamp is None
        assert entry.severity is None
        assert entry.raw == line

    def test_severity_level_ordering(self):
        levels = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
        entries = [
            parse_line(f"2024-01-01T00:00:00Z [{s}] msg") for s in levels
        ]
        numeric = [e.severity_level for e in entries]
        assert numeric == sorted(numeric)


# ---------------------------------------------------------------------------
# Filter tests
# ---------------------------------------------------------------------------

def _make_entry(ts_str, severity, message="msg"):
    from logslice.parser import parse_line
    line = f"{ts_str} [{severity}] {message}"
    return parse_line(line)


class TestFilterEntries:
    ENTRIES = [
        _make_entry("2024-05-01T10:00:00Z", "DEBUG"),
        _make_entry("2024-05-01T11:00:00Z", "INFO"),
        _make_entry("2024-05-01T12:00:00Z", "WARN"),
        _make_entry("2024-05-01T13:00:00Z", "ERROR"),
    ]

    def test_no_filters_returns_all(self):
        result = list(filter_entries(self.ENTRIES))
        assert len(result) == 4

    def test_start_filter(self):
        start = datetime(2024, 5, 1, 11, 30)
        result = list(filter_entries(self.ENTRIES, start=start))
        assert all(e.timestamp >= start for e in result)
        assert len(result) == 2  # WARN + ERROR

    def test_end_filter(self):
        end = datetime(2024, 5, 1, 11, 30)
        result = list(filter_entries(self.ENTRIES, end=end))
        assert len(result) == 2  # DEBUG + INFO

    def test_min_severity_warn(self):
        result = list(filter_entries(self.ENTRIES, min_severity="WARN"))
        severities = {e.severity for e in result}
        assert severities == {"WARN", "ERROR"}

    def test_unparsed_included_by_default(self):
        unparsed = LogEntry(raw="raw line", timestamp=None, severity=None, message="raw line")
        result = list(filter_entries([unparsed]))
        assert len(result) == 1

    def test_unparsed_excluded_when_flag_false(self):
        unparsed = LogEntry(raw="raw line", timestamp=None, severity=None, message="raw line")
        result = list(filter_entries([unparsed], include_unparsed=False))
        assert len(result) == 0

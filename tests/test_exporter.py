"""Tests for logslice.exporter."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

import pytest

from logslice.exporter import entries_to_csv, entries_to_json, export_entries
from logslice.parser import LogEntry


def _entry(
    msg: str = "hello",
    severity: str = "INFO",
    ts: datetime | None = None,
) -> LogEntry:
    ts = ts or datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message=msg, raw=f"{ts} {severity} {msg}")


# ---------------------------------------------------------------------------
# entries_to_json
# ---------------------------------------------------------------------------

class TestEntriesToJson:
    def test_returns_valid_json(self):
        data = entries_to_json([_entry()])
        parsed = json.loads(data)
        assert isinstance(parsed, list)

    def test_contains_expected_keys(self):
        data = json.loads(entries_to_json([_entry()]))
        assert set(data[0].keys()) == {"timestamp", "severity", "message", "raw"}

    def test_severity_preserved(self):
        data = json.loads(entries_to_json([_entry(severity="ERROR")]))
        assert data[0]["severity"] == "ERROR"

    def test_message_preserved(self):
        data = json.loads(entries_to_json([_entry(msg="disk full")]))
        assert data[0]["message"] == "disk full"

    def test_null_timestamp_serialised(self):
        entry = LogEntry(timestamp=None, severity="INFO", message="x", raw="x")
        data = json.loads(entries_to_json([entry]))
        assert data[0]["timestamp"] is None

    def test_compact_output_with_none_indent(self):
        data = entries_to_json([_entry()], indent=None)
        assert "\n" not in data

    def test_empty_list(self):
        assert json.loads(entries_to_json([])) == []


# ---------------------------------------------------------------------------
# entries_to_csv
# ---------------------------------------------------------------------------

class TestEntriesToCsv:
    def test_has_header_row(self):
        data = entries_to_csv([_entry()])
        reader = csv.reader(io.StringIO(data))
        header = next(reader)
        assert "severity" in header
        assert "message" in header

    def test_row_count_matches_entries(self):
        entries = [_entry("a"), _entry("b"), _entry("c")]
        data = entries_to_csv(entries)
        rows = list(csv.DictReader(io.StringIO(data)))
        assert len(rows) == 3

    def test_message_in_row(self):
        data = entries_to_csv([_entry(msg="timeout")])
        rows = list(csv.DictReader(io.StringIO(data)))
        assert rows[0]["message"] == "timeout"


# ---------------------------------------------------------------------------
# export_entries
# ---------------------------------------------------------------------------

def test_export_json_returns_string():
    result = export_entries([_entry()], fmt="json")
    assert isinstance(result, str)
    json.loads(result)  # must be valid JSON


def test_export_csv_returns_string():
    result = export_entries([_entry()], fmt="csv")
    assert "severity" in result


def test_export_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_entries([_entry()], fmt="xml")  # type: ignore[arg-type]


def test_export_writes_file(tmp_path):
    out = tmp_path / "out.json"
    export_entries([_entry()], fmt="json", output_path=str(out))
    assert out.exists()
    assert json.loads(out.read_text())

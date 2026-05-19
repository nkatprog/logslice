"""Tests for logslice.output and logslice.cli."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.output import format_entry, write_entries
from logslice.cli import build_parser, main


# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------

def _entry(severity="INFO", message="hello", ts=None) -> LogEntry:
    return LogEntry(
        timestamp=ts or datetime(2024, 3, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw="raw line",
    )


def test_format_entry_contains_timestamp():
    entry = _entry(ts=datetime(2024, 3, 1, 8, 5, 3))
    result = format_entry(entry)
    assert "2024-03-01" in result
    assert "08:05:03" in result


def test_format_entry_contains_severity():
    assert "[ERROR   ]" in format_entry(_entry(severity="ERROR"))


def test_format_entry_contains_message():
    assert "something happened" in format_entry(_entry(message="something happened"))


def test_format_entry_colour_wraps_ansi():
    result = format_entry(_entry(severity="ERROR"), colour=True)
    assert "\033[" in result
    assert "\033[0m" in result


def test_format_entry_no_colour_no_ansi():
    result = format_entry(_entry(severity="ERROR"), colour=False)
    assert "\033[" not in result


def test_write_entries_returns_count():
    entries = [_entry(), _entry(), _entry()]
    buf = io.StringIO()
    count = write_entries(entries, dest=buf)
    assert count == 3


def test_write_entries_output_has_newlines():
    buf = io.StringIO()
    write_entries([_entry(message="line1"), _entry(message="line2")], dest=buf)
    lines = buf.getvalue().splitlines()
    assert len(lines) == 2


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def test_cli_parse_from_iso():
    parser = build_parser()
    args = parser.parse_args(["myfile.log", "--from", "2024-01-15T08:30:00"])
    assert args.from_dt == datetime(2024, 1, 15, 8, 30, 0)


def test_cli_parse_bad_datetime():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["myfile.log", "--from", "not-a-date"])


def test_cli_missing_file_returns_nonzero(tmp_path):
    result = main([str(tmp_path / "nonexistent.log")])
    assert result != 0


def test_cli_processes_real_file(tmp_path):
    log = tmp_path / "app.log"
    log.write_text(
        "2024-03-01 10:00:00 INFO  server started\n"
        "2024-03-01 10:01:00 ERROR disk full\n"
    )
    buf = io.StringIO()
    with patch("logslice.cli.sys.stdout", buf):
        rc = main([str(log), "--min-severity", "ERROR"])
    assert rc == 0
    output = buf.getvalue()
    assert "disk full" in output
    assert "server started" not in output

"""Tests for logslice.truncator and logslice.truncate_cmd."""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.truncator import (
    TruncateOptions,
    _effective_limit,
    truncate_entries,
    truncate_entry,
    truncate_message,
)
from logslice.truncate_cmd import build_truncate_parser, truncate_main

_TS = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    raw = f"2024-01-01T12:00:00Z {severity} {message}"
    return LogEntry(timestamp=_TS, severity=severity, message=message, raw=raw)


# ---------------------------------------------------------------------------
# truncate_message
# ---------------------------------------------------------------------------

def test_short_message_unchanged():
    assert truncate_message("hello", 20) == "hello"


def test_exact_length_unchanged():
    msg = "a" * 10
    assert truncate_message(msg, 10) == msg


def test_long_message_is_cut():
    result = truncate_message("a" * 50, 10)
    assert len(result) == 10
    assert result.endswith("...")


def test_custom_ellipsis_used():
    result = truncate_message("hello world", 8, ellipsis="--")
    assert result == "hello w--"
    assert len(result) == 8


# ---------------------------------------------------------------------------
# TruncateOptions
# ---------------------------------------------------------------------------

def test_options_defaults():
    opts = TruncateOptions()
    assert opts.max_length == 200
    assert opts.ellipsis == "..."


def test_options_invalid_max_length_raises():
    with pytest.raises(ValueError):
        TruncateOptions(max_length=2, ellipsis="...")


# ---------------------------------------------------------------------------
# _effective_limit
# ---------------------------------------------------------------------------

def test_effective_limit_uses_default_when_no_override():
    opts = TruncateOptions(max_length=100)
    assert _effective_limit("INFO", opts) == 100


def test_effective_limit_uses_per_severity_override():
    opts = TruncateOptions(max_length=100, per_severity={"ERROR": 40})
    assert _effective_limit("ERROR", opts) == 40
    assert _effective_limit("INFO", opts) == 100


# ---------------------------------------------------------------------------
# truncate_entry / truncate_entries
# ---------------------------------------------------------------------------

def test_truncate_entry_shortens_message():
    entry = _entry("x" * 300)
    result = truncate_entry(entry, TruncateOptions(max_length=50))
    assert len(result.message) == 50
    assert result.timestamp == entry.timestamp
    assert result.severity == entry.severity


def test_truncate_entry_preserves_short_message():
    entry = _entry("short")
    result = truncate_entry(entry, TruncateOptions(max_length=50))
    assert result.message == "short"


def test_truncate_entries_yields_all():
    entries = [_entry("a" * 300), _entry("b" * 10)]
    results = list(truncate_entries(entries, TruncateOptions(max_length=20)))
    assert len(results) == 2
    assert len(results[0].message) == 20
    assert results[1].message == "b" * 10


def test_truncate_entries_default_opts():
    entries = [_entry("c" * 300)]
    results = list(truncate_entries(entries))
    assert len(results[0].message) == 200


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_build_truncate_parser_defaults():
    p = build_truncate_parser()
    args = p.parse_args([])
    assert args.max_length == 200
    assert args.ellipsis == "..."
    assert args.file == "-"


def test_truncate_main_reads_stdin(capsys):
    log_line = "2024-01-01T12:00:00Z INFO " + "word " * 60 + "\n"
    with patch("sys.stdin", StringIO(log_line)):
        truncate_main(["--max-length", "50"])
    out, _ = capsys.readouterr()
    # message part should be truncated
    lines = [l for l in out.splitlines() if l.strip()]
    assert lines, "expected at least one output line"

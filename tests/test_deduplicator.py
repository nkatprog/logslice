"""Tests for logslice.deduplicator."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.deduplicator import deduplicate


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01 12:00:00 {severity} {message}",
    )


def _run(entries: List[LogEntry], **kwargs) -> List[LogEntry]:
    return list(deduplicate(entries, **kwargs))


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_empty_input_yields_nothing():
    assert _run([]) == []


def test_single_entry_passes_through():
    e = _entry("hello")
    result = _run([e])
    assert len(result) == 1
    assert result[0].message == "hello"


def test_distinct_entries_all_pass_through():
    entries = [_entry("a"), _entry("b"), _entry("c")]
    result = _run(entries)
    assert [r.message for r in result] == ["a", "b", "c"]


def test_two_consecutive_duplicates_collapsed():
    entries = [_entry("same"), _entry("same")]
    result = _run(entries)
    assert len(result) == 1
    assert "repeated 2x" in result[0].message


def test_five_consecutive_duplicates_collapsed():
    entries = [_entry("boom")] * 5
    result = _run(entries)
    assert len(result) == 1
    assert "repeated 5x" in result[0].message


def test_duplicate_run_then_different_entry():
    entries = [_entry("x"), _entry("x"), _entry("y")]
    result = _run(entries)
    assert len(result) == 2
    assert "repeated 2x" in result[0].message
    assert result[1].message == "y"


def test_non_duplicate_between_duplicates():
    entries = [_entry("a"), _entry("b"), _entry("a")]
    result = _run(entries)
    # Each 'a' is in its own run; no collapsing across the 'b'
    assert len(result) == 3


# ---------------------------------------------------------------------------
# max_gap option
# ---------------------------------------------------------------------------

def test_max_gap_breaks_long_run():
    entries = [_entry("loop")] * 6
    result = _run(entries, max_gap=3)
    # First 3 collapsed, next 3 collapsed → 2 output entries
    assert len(result) == 2
    assert "repeated 3x" in result[0].message
    assert "repeated 3x" in result[1].message


def test_max_gap_one_means_no_collapsing():
    entries = [_entry("x"), _entry("x"), _entry("x")]
    result = _run(entries, max_gap=1)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# key option
# ---------------------------------------------------------------------------

def test_key_severity_collapses_same_severity():
    entries = [_entry("msg1", "WARN"), _entry("msg2", "WARN"), _entry("msg3", "ERROR")]
    result = _run(entries, key="severity")
    assert len(result) == 2


def test_original_entry_preserved_when_no_repeat():
    e = _entry("unique")
    result = _run([e])
    assert result[0] is e

"""Tests for logslice.highlighter."""
from __future__ import annotations

import datetime
import pytest

from logslice.parser import LogEntry
from logslice.highlighter import (
    HighlightRule,
    highlight_message,
    highlight_entry,
    rules_from_strings,
)


def _entry(message: str = "hello world") -> LogEntry:
    return LogEntry(
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        severity="INFO",
        message=message,
        raw=f"2024-01-01T12:00:00 INFO {message}",
    )


# ---------------------------------------------------------------------------
# HighlightRule
# ---------------------------------------------------------------------------

class TestHighlightRule:
    def test_wraps_matching_word(self):
        rule = HighlightRule(pattern="error", colour="red")
        result = rule.apply("an error occurred")
        assert "\033[31merror\033[0m" in result

    def test_does_not_alter_non_matching_text(self):
        rule = HighlightRule(pattern="error", colour="red")
        result = rule.apply("everything is fine")
        assert result == "everything is fine"

    def test_case_insensitive_by_default(self):
        rule = HighlightRule(pattern="error", colour="red")
        result = rule.apply("ERROR detected")
        assert "\033[31m" in result

    def test_case_sensitive_skips_wrong_case(self):
        rule = HighlightRule(pattern="error", colour="red", case_sensitive=True)
        result = rule.apply("ERROR detected")
        assert "\033[31m" not in result

    def test_multiple_occurrences_all_wrapped(self):
        rule = HighlightRule(pattern="ok", colour="green")
        result = rule.apply("ok and ok again")
        assert result.count("\033[32m") == 2


# ---------------------------------------------------------------------------
# highlight_message
# ---------------------------------------------------------------------------

def test_highlight_message_applies_all_rules():
    rules = [
        HighlightRule(pattern="error", colour="red"),
        HighlightRule(pattern="warn", colour="yellow"),
    ]
    result = highlight_message("error and warn", rules)
    assert "\033[31m" in result
    assert "\033[33m" in result


def test_highlight_message_empty_rules_returns_original():
    msg = "unchanged message"
    assert highlight_message(msg, []) == msg


# ---------------------------------------------------------------------------
# highlight_entry
# ---------------------------------------------------------------------------

def test_highlight_entry_preserves_metadata():
    entry = _entry("connection timeout")
    rules = [HighlightRule(pattern="timeout", colour="cyan")]
    result = highlight_entry(entry, rules)
    assert result.timestamp == entry.timestamp
    assert result.severity == entry.severity


def test_highlight_entry_modifies_message():
    entry = _entry("connection timeout")
    rules = [HighlightRule(pattern="timeout", colour="cyan")]
    result = highlight_entry(entry, rules)
    assert "\033[36m" in result.message
    assert "timeout" in result.message


def test_highlight_entry_original_unchanged():
    entry = _entry("connection timeout")
    rules = [HighlightRule(pattern="timeout", colour="cyan")]
    highlight_entry(entry, rules)
    assert "\033[" not in entry.message


# ---------------------------------------------------------------------------
# rules_from_strings
# ---------------------------------------------------------------------------

def test_rules_from_strings_count():
    rules = rules_from_strings(["foo", "bar", "baz"])
    assert len(rules) == 3


def test_rules_from_strings_colour_applied():
    rules = rules_from_strings(["hello"], colour="magenta")
    result = rules[0].apply("say hello")
    assert "\033[35m" in result


def test_rules_from_strings_empty_list():
    assert rules_from_strings([]) == []

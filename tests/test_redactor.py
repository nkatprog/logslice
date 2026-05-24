"""Tests for logslice.redactor and logslice.redact_cmd."""
from __future__ import annotations

import io
from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.redactor import (
    RedactOptions,
    _BUILTIN_PATTERNS,
    redact_entries,
    redact_entry,
    redact_message,
)

_TS = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(timestamp=_TS, severity=severity, message=message, raw=message)


# ---------------------------------------------------------------------------
# RedactOptions
# ---------------------------------------------------------------------------

class TestRedactOptions:
    def test_empty_options_compile_to_no_patterns(self):
        opts = RedactOptions()
        assert opts.compiled() == []

    def test_unknown_builtin_raises(self):
        with pytest.raises(ValueError, match="Unknown built-in"):
            RedactOptions(builtins=["ssn"])

    def test_builtin_compiles_correctly(self):
        opts = RedactOptions(builtins=["ipv4"])
        compiled = opts.compiled()
        assert len(compiled) == 1
        assert compiled[0].search("addr 192.168.1.1 here")

    def test_custom_pattern_included(self):
        opts = RedactOptions(patterns=[r"\d{4}-\d{4}-\d{4}-\d{4}"])
        assert len(opts.compiled()) == 1


# ---------------------------------------------------------------------------
# redact_message
# ---------------------------------------------------------------------------

def test_ipv4_redacted():
    opts = RedactOptions(builtins=["ipv4"])
    result = redact_message("request from 10.0.0.1", opts)
    assert "10.0.0.1" not in result
    assert "[REDACTED]" in result


def test_email_redacted():
    opts = RedactOptions(builtins=["email"])
    result = redact_message("user alice@example.com logged in", opts)
    assert "alice@example.com" not in result


def test_token_redacted():
    opts = RedactOptions(builtins=["token"])
    result = redact_message("auth token=abc123secret", opts)
    assert "abc123secret" not in result


def test_custom_replacement_string():
    opts = RedactOptions(builtins=["ipv4"], replacement="***")
    result = redact_message("ip 1.2.3.4", opts)
    assert "***" in result


def test_no_match_leaves_message_unchanged():
    opts = RedactOptions(builtins=["email"])
    original = "nothing sensitive here"
    assert redact_message(original, opts) == original


def test_multiple_occurrences_all_redacted():
    opts = RedactOptions(builtins=["ipv4"])
    result = redact_message("from 1.1.1.1 to 2.2.2.2", opts)
    assert "1.1.1.1" not in result
    assert "2.2.2.2" not in result


# ---------------------------------------------------------------------------
# redact_entry / redact_entries
# ---------------------------------------------------------------------------

def test_redact_entry_returns_new_entry():
    opts = RedactOptions(builtins=["ipv4"])
    original = _entry("client 192.168.0.5")
    result = redact_entry(original, opts)
    assert result is not original
    assert "192.168.0.5" not in result.message


def test_redact_entry_preserves_timestamp_and_severity():
    opts = RedactOptions(builtins=["ipv4"])
    original = _entry("ip 10.0.0.1", severity="ERROR")
    result = redact_entry(original, opts)
    assert result.timestamp == _TS
    assert result.severity == "ERROR"


def test_redact_entries_yields_all():
    opts = RedactOptions(builtins=["email"])
    entries = [_entry("user a@b.com"), _entry("no email here"), _entry("c@d.org")]
    results = list(redact_entries(entries, opts))
    assert len(results) == 3
    assert "a@b.com" not in results[0].message
    assert results[1].message == "no email here"
    assert "c@d.org" not in results[2].message

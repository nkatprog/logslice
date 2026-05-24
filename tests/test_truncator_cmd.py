"""Tests for the truncate_cmd CLI entry point."""

import io
import sys
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.truncate_cmd import build_truncate_parser, truncate_main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(
    message: str = "hello world",
    severity: str = "INFO",
    ts: datetime | None = None,
) -> LogEntry:
    return LogEntry(
        timestamp=ts or datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        severity=severity,
        message=message,
        raw=f"2024-01-15T10:00:00Z [{severity}] {message}",
    )


def _stdin(*entries: LogEntry) -> io.TextIOWrapper:
    """Return a StringIO whose lines are the raw text of *entries*."""
    text = "".join(e.raw + "\n" for e in entries)
    return io.StringIO(text)


# ---------------------------------------------------------------------------
# build_truncate_parser
# ---------------------------------------------------------------------------

class TestBuildTruncateParser:
    def setup_method(self):
        self.parser = build_truncate_parser()

    def test_default_limit(self):
        args = self.parser.parse_args([])
        assert args.limit == 120

    def test_custom_limit(self):
        args = self.parser.parse_args(["--limit", "50"])
        assert args.limit == 50

    def test_default_ellipsis(self):
        args = self.parser.parse_args([])
        assert args.ellipsis == "..."

    def test_custom_ellipsis(self):
        args = self.parser.parse_args(["--ellipsis", "[…]"])
        assert args.ellipsis == "[…]"

    def test_per_severity_flag_absent_by_default(self):
        args = self.parser.parse_args([])
        assert args.per_severity is False

    def test_per_severity_flag_present(self):
        args = self.parser.parse_args(["--per-severity"])
        assert args.per_severity is True

    def test_short_limit_alias(self):
        args = self.parser.parse_args(["-l", "80"])
        assert args.limit == 80


# ---------------------------------------------------------------------------
# truncate_main integration
# ---------------------------------------------------------------------------

class TestTruncateMain:
    """End-to-end tests that exercise truncate_main via patched stdin/stdout."""

    def _run(self, argv: list[str], *entries: LogEntry) -> str:
        stdin = _stdin(*entries)
        stdout = io.StringIO()
        with (
            patch("logslice.truncate_cmd.sys.stdin", stdin),
            patch("logslice.truncate_cmd.sys.stdout", stdout),
            patch("sys.argv", ["logslice-truncate"] + argv),
        ):
            truncate_main()
        return stdout.getvalue()

    def test_short_message_passes_through_unchanged(self):
        entry = _entry(message="short")
        output = self._run(["--limit", "120"], entry)
        assert "short" in output

    def test_long_message_is_truncated(self):
        long_msg = "x" * 200
        entry = _entry(message=long_msg)
        output = self._run(["--limit", "50"], entry)
        # The raw output line should NOT contain the full 200-char message
        assert long_msg not in output
        assert "..." in output

    def test_custom_ellipsis_appears_in_output(self):
        long_msg = "a" * 100
        entry = _entry(message=long_msg)
        output = self._run(["--limit", "20", "--ellipsis", "[cut]"], entry)
        assert "[cut]" in output

    def test_multiple_entries_all_written(self):
        entries = [_entry(message=f"msg{i}") for i in range(5)]
        output = self._run(["--limit", "120"], *entries)
        for i in range(5):
            assert f"msg{i}" in output

    def test_per_severity_does_not_crash(self):
        """Smoke-test: --per-severity flag should run without error."""
        entries = [
            _entry(message="x" * 200, severity="DEBUG"),
            _entry(message="y" * 200, severity="ERROR"),
        ]
        # Should not raise
        output = self._run(["--per-severity", "--limit", "60"], *entries)
        assert len(output) > 0

    def test_empty_input_produces_no_output(self):
        output = self._run(["--limit", "120"])
        assert output == ""

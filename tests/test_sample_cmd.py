"""Integration-level tests for logslice.sample_cmd."""
from __future__ import annotations

import io
import sys
from unittest.mock import patch

import pytest

from logslice.sample_cmd import build_sample_parser, sample_main


_LOG_LINES = [
    "2024-01-01T00:00:00Z INFO  message one\n",
    "2024-01-01T00:00:01Z INFO  message two\n",
    "2024-01-01T00:00:02Z ERROR something broke\n",
    "2024-01-01T00:00:03Z WARN  watch out\n",
    "2024-01-01T00:00:04Z INFO  message five\n",
    "2024-01-01T00:00:05Z DEBUG verbose\n",
]


def _stdin(lines):
    return io.StringIO("".join(lines))


class TestBuildSampleParser:
    def test_default_rate(self):
        parser = build_sample_parser()
        args = parser.parse_args([])
        assert args.rate == 10

    def test_custom_rate(self):
        parser = build_sample_parser()
        args = parser.parse_args(["-n", "3"])
        assert args.rate == 3

    def test_per_severity_flag(self):
        parser = build_sample_parser()
        args = parser.parse_args(["--per-severity"])
        assert args.per_severity is True

    def test_colour_flag(self):
        parser = build_sample_parser()
        args = parser.parse_args(["--colour"])
        assert args.colour is True


class TestSampleMain:
    def test_rate_one_outputs_all_parseable(self, capsys):
        with patch("sys.stdin", _stdin(_LOG_LINES)):
            sample_main(["-n", "1"])
        out = capsys.readouterr().out
        # All 6 lines are parseable; all should appear
        assert out.count("\n") == 6

    def test_rate_two_halves_output(self, capsys):
        with patch("sys.stdin", _stdin(_LOG_LINES)):
            sample_main(["-n", "2"])
        out = capsys.readouterr().out
        assert out.count("\n") == 3

    def test_reads_from_file(self, tmp_path, capsys):
        log_file = tmp_path / "test.log"
        log_file.write_text("".join(_LOG_LINES))
        sample_main(["-n", "1", str(log_file)])
        out = capsys.readouterr().out
        assert out.count("\n") == 6

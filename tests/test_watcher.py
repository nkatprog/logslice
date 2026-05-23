"""Tests for logslice.watcher."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from logslice.parser import LogEntry
from logslice.watcher import watch, _tail_lines


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_lines(path: Path, lines: list[str], delay: float = 0.05) -> None:
    """Append *lines* to *path* with a small delay between each."""
    for line in lines:
        time.sleep(delay)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


_SAMPLE_LINES = [
    "2024-01-15T10:00:00 INFO  service started",
    "2024-01-15T10:00:01 DEBUG checking config",
    "2024-01-15T10:00:02 ERROR disk full",
    "2024-01-15T10:00:03 WARN  retrying connection",
]


# ---------------------------------------------------------------------------
# _tail_lines
# ---------------------------------------------------------------------------

class TestTailLines:
    def test_yields_existing_lines_from_start(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("line1\nline2\n", encoding="utf-8")
        gen = _tail_lines(log, from_end=False)
        assert next(gen) == "line1"
        assert next(gen) == "line2"

    def test_yields_empty_string_when_no_data(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("", encoding="utf-8")
        gen = _tail_lines(log, from_end=False)
        assert next(gen) == ""


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------

class TestWatch:
    def _run_watch(self, tmp_path, *, min_severity=None, timeout=2.0):
        log = tmp_path / "app.log"
        log.write_text("", encoding="utf-8")
        collected: list[LogEntry] = []
        stop = threading.Event()

        def _callback(entry: LogEntry) -> None:
            collected.append(entry)
            if len(collected) >= 2:
                stop.set()

        def _watch_thread():
            watch(
                log,
                min_severity=min_severity,
                callback=_callback,
                poll_interval=0.05,
                from_end=False,
            )

        t = threading.Thread(target=_watch_thread, daemon=True)
        t.start()
        _write_lines(log, _SAMPLE_LINES, delay=0.05)
        stop.wait(timeout=timeout)
        return collected

    def test_callback_receives_log_entries(self, tmp_path):
        entries = self._run_watch(tmp_path)
        assert len(entries) >= 2
        assert all(isinstance(e, LogEntry) for e in entries)

    def test_min_severity_filters_debug(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("", encoding="utf-8")
        collected: list[LogEntry] = []
        stop = threading.Event()

        def _callback(entry):
            collected.append(entry)
            if len(collected) >= 1:
                stop.set()

        t = threading.Thread(
            target=watch,
            kwargs=dict(
                path=log,
                min_severity="ERROR",
                callback=_callback,
                poll_interval=0.05,
                from_end=False,
            ),
            daemon=True,
        )
        t.start()
        _write_lines(log, _SAMPLE_LINES, delay=0.05)
        stop.wait(timeout=2.0)

        assert all(e.severity in ("ERROR", "CRITICAL") for e in collected)

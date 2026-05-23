"""Output formatting for logslice results."""

from __future__ import annotations

import sys
from typing import Iterable, TextIO

from logslice.parser import LogEntry

# ANSI colour codes
_COLOURS = {
    "DEBUG": "\033[36m",    # cyan
    "INFO": "\033[32m",     # green
    "WARN": "\033[33m",     # yellow
    "WARNING": "\033[33m",  # yellow (alias)
    "ERROR": "\033[31m",    # red
    "CRITICAL": "\033[35m", # magenta
}
_RESET = "\033[0m"


def _colourise(entry: LogEntry, text: str) -> str:
    """Wrap *text* in ANSI colour for the entry's severity, if known."""
    colour = _COLOURS.get(entry.severity or "", "")
    if not colour:
        return text
    return f"{colour}{text}{_RESET}"


def format_entry(entry: LogEntry, *, colour: bool = False) -> str:
    """Return a single-line string representation of *entry*."""
    ts = entry.timestamp.isoformat(sep=" ") if entry.timestamp else "(no timestamp)"
    severity = entry.severity or "UNKNOWN"
    line = f"{ts}  [{severity:<8}]  {entry.message}"
    if colour:
        line = _colourise(entry, line)
    return line


def write_entries(
    entries: Iterable[LogEntry],
    dest: TextIO = sys.stdout,
    *,
    colour: bool = False,
) -> int:
    """Write *entries* to *dest*, one per line.  Returns the count written."""
    count = 0
    for entry in entries:
        dest.write(format_entry(entry, colour=colour))
        dest.write("\n")
        count += 1
    return count


def write_summary(
    entries: Iterable[LogEntry],
    dest: TextIO = sys.stdout,
) -> None:
    """Write a severity-count summary table to *dest*.

    Iterates over *entries* once and prints the number of log lines
    observed for each severity level, sorted from most to least frequent.
    """
    counts: dict[str, int] = {}
    for entry in entries:
        key = entry.severity or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1

    if not counts:
        dest.write("No entries.\n")
        return

    dest.write(f"{'Severity':<12}  {'Count':>6}\n")
    dest.write(f"{'-' * 12}  {'-' * 6}\n")
    for severity, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        dest.write(f"{severity:<12}  {count:>6}\n")

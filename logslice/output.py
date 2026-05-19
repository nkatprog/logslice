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

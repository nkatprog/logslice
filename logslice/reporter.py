"""Summary reporter: produce human-readable statistics from aggregated buckets."""

from __future__ import annotations

from io import StringIO
from typing import Iterable, TextIO
import sys

from logslice.aggregator import Bucket, aggregate
from logslice.filter import filter_entries
from logslice.parser import LogEntry

_SEVERITY_ORDER = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]


def _severity_bar(count: int, max_count: int, width: int = 20) -> str:
    """Return an ASCII bar proportional to *count* / *max_count*."""
    if max_count == 0:
        filled = 0
    else:
        filled = round(width * count / max_count)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def severity_summary(entries: Iterable[LogEntry]) -> dict[str, int]:
    """Count occurrences of each severity level across *entries*."""
    counts: dict[str, int] = {sev: 0 for sev in _SEVERITY_ORDER}
    for entry in entries:
        key = entry.severity.upper()
        if key not in counts:
            counts[key] = 0
        counts[key] = counts.get(key, 0) + 1
    return counts


def format_summary(
    counts: dict[str, int],
    *,
    title: str = "Log Summary",
    bar_width: int = 20,
) -> str:
    """Return a formatted multi-line summary string."""
    buf = StringIO()
    total = sum(counts.values())
    buf.write(f"{title}\n")
    buf.write("-" * (bar_width + 30) + "\n")
    max_count = max(counts.values(), default=0)
    for sev in _SEVERITY_ORDER:
        count = counts.get(sev, 0)
        bar = _severity_bar(count, max_count, bar_width)
        buf.write(f"  {sev:<10} {bar}  {count:>6}\n")
    buf.write("-" * (bar_width + 30) + "\n")
    buf.write(f"  {'TOTAL':<10} {'':>{bar_width + 2}}  {total:>6}\n")
    return buf.getvalue()


def write_summary(
    entries: Iterable[LogEntry],
    out: TextIO = sys.stdout,
    *,
    title: str = "Log Summary",
    bar_width: int = 20,
) -> None:
    """Compute severity counts from *entries* and write the summary to *out*."""
    counts = severity_summary(entries)
    out.write(format_summary(counts, title=title, bar_width=bar_width))

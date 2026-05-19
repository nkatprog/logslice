"""Filtering logic: apply time-range and severity constraints to log entries."""

from datetime import datetime
from typing import Iterable, Iterator, Optional

from logslice.parser import LogEntry, SEVERITY_LEVELS


def _min_severity_level(min_severity: Optional[str]) -> int:
    """Return the numeric level for the given severity string, defaulting to 0."""
    if min_severity is None:
        return 0
    return SEVERITY_LEVELS.get(min_severity.upper(), 0)


def filter_entries(
    entries: Iterable[LogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_severity: Optional[str] = None,
    include_unparsed: bool = True,
) -> Iterator[LogEntry]:
    """Yield log entries that match the given time range and minimum severity.

    Args:
        entries: Iterable of LogEntry objects.
        start: Only include entries at or after this timestamp.
        end: Only include entries at or before this timestamp.
        min_severity: Minimum severity level (DEBUG/INFO/WARN/ERROR/CRITICAL).
        include_unparsed: If True, lines without a recognised timestamp or
                          severity are passed through unchanged.
    """
    min_level = _min_severity_level(min_severity)

    for entry in entries:
        # Handle lines that could not be parsed
        if entry.timestamp is None or entry.severity is None:
            if include_unparsed:
                yield entry
            continue

        # Time-range filter
        if start is not None and entry.timestamp < start:
            continue
        if end is not None and entry.timestamp > end:
            continue

        # Severity filter
        if entry.severity_level < min_level:
            continue

        yield entry


def filter_file(
    path: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_severity: Optional[str] = None,
    include_unparsed: bool = True,
) -> Iterator[LogEntry]:
    """Open a log file and yield filtered LogEntry objects."""
    from logslice.parser import parse_line

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        entries = (parse_line(line) for line in fh)
        yield from filter_entries(
            entries,
            start=start,
            end=end,
            min_severity=min_severity,
            include_unparsed=include_unparsed,
        )

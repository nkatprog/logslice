"""Truncate long log messages to a configurable maximum length."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from logslice.parser import LogEntry

_DEFAULT_MAX_LENGTH = 200
_ELLIPSIS = "..."


@dataclass
class TruncateOptions:
    max_length: int = _DEFAULT_MAX_LENGTH
    ellipsis: str = _ELLIPSIS
    per_severity: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.max_length < len(self.ellipsis):
            raise ValueError(
                f"max_length ({self.max_length}) must be >= "
                f"len(ellipsis) ({len(self.ellipsis)})"
            )


def _effective_limit(severity: str, opts: TruncateOptions) -> int:
    """Return the max length for the given severity, respecting per-severity overrides."""
    if opts.per_severity:
        return opts.per_severity.get(severity.upper(), opts.max_length)
    return opts.max_length


def truncate_message(message: str, max_length: int, ellipsis: str = _ELLIPSIS) -> str:
    """Truncate *message* to *max_length* characters, appending *ellipsis* if cut."""
    if len(message) <= max_length:
        return message
    cut = max_length - len(ellipsis)
    return message[:cut] + ellipsis


def truncate_entry(entry: LogEntry, opts: TruncateOptions) -> LogEntry:
    """Return a new LogEntry with its message truncated according to *opts*."""
    limit = _effective_limit(entry.severity, opts)
    new_message = truncate_message(entry.message, limit, opts.ellipsis)
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=new_message,
        raw=entry.raw,
    )


def truncate_entries(
    entries: Iterable[LogEntry],
    opts: TruncateOptions | None = None,
) -> Iterator[LogEntry]:
    """Yield entries with messages truncated according to *opts*."""
    if opts is None:
        opts = TruncateOptions()
    for entry in entries:
        yield truncate_entry(entry, opts)

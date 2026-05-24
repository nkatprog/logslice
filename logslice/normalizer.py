"""Normalise log entry fields: strip whitespace, unify severity casing,
and optionally reformat timestamps to a canonical ISO-8601 string."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import timezone
from typing import Iterable, Iterator

from logslice.parser import LogEntry, severity_level

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizeOptions:
    """Controls which normalisation steps are applied."""

    collapse_whitespace: bool = True
    canonical_severity: bool = True
    utc_timestamps: bool = False
    strip_ansi: bool = True

    def __post_init__(self) -> None:
        # validate — nothing to validate currently, kept for future guards
        pass


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

_SEVERITY_CANONICAL: dict[str, str] = {
    "warning": "WARN",
    "warn": "WARN",
    "error": "ERROR",
    "err": "ERROR",
    "critical": "CRITICAL",
    "crit": "CRITICAL",
    "info": "INFO",
    "debug": "DEBUG",
    "trace": "TRACE",
}


def _canonical_severity(raw: str) -> str:
    """Return the canonical upper-case severity token."""
    return _SEVERITY_CANONICAL.get(raw.lower(), raw.upper())


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def normalize_entry(entry: LogEntry, opts: NormalizeOptions) -> LogEntry:
    """Return a new *LogEntry* with normalised fields."""
    message = entry.message

    if opts.strip_ansi:
        message = _strip_ansi(message)

    if opts.collapse_whitespace:
        message = _WHITESPACE_RE.sub(" ", message).strip()

    severity = entry.severity
    if opts.canonical_severity:
        severity = _canonical_severity(severity)

    timestamp = entry.timestamp
    if opts.utc_timestamps and timestamp is not None:
        timestamp = timestamp.astimezone(timezone.utc)

    return LogEntry(timestamp=timestamp, severity=severity, message=message)


def normalize_entries(
    entries: Iterable[LogEntry],
    opts: NormalizeOptions | None = None,
) -> Iterator[LogEntry]:
    """Yield normalised copies of each entry in *entries*."""
    if opts is None:
        opts = NormalizeOptions()
    for entry in entries:
        yield normalize_entry(entry, opts)

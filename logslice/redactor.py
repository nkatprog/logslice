"""Redact sensitive patterns from log entry messages."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogEntry

_BUILTIN_PATTERNS: dict[str, str] = {
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "email": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "token": r"(?i)(?:token|key|secret|password)=[^\s&]+",
}


@dataclass
class RedactOptions:
    replacement: str = "[REDACTED]"
    patterns: list[str] = field(default_factory=list)
    builtins: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        unknown = set(self.builtins) - set(_BUILTIN_PATTERNS)
        if unknown:
            raise ValueError(f"Unknown built-in patterns: {', '.join(sorted(unknown))}")

    def compiled(self) -> list[re.Pattern[str]]:
        """Return all active patterns as compiled regexes."""
        active: list[str] = [_BUILTIN_PATTERNS[b] for b in self.builtins]
        active.extend(self.patterns)
        return [re.compile(p) for p in active]


def redact_message(message: str, opts: RedactOptions) -> str:
    """Return *message* with all matching spans replaced by *opts.replacement*."""
    for pattern in opts.compiled():
        message = pattern.sub(opts.replacement, message)
    return message


def redact_entry(entry: LogEntry, opts: RedactOptions) -> LogEntry:
    """Return a new *LogEntry* with the message redacted."""
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=redact_message(entry.message, opts),
        raw=entry.raw,
    )


def redact_entries(
    entries: Iterable[LogEntry], opts: RedactOptions
) -> Iterator[LogEntry]:
    """Yield redacted copies of every entry in *entries*."""
    for entry in entries:
        yield redact_entry(entry, opts)

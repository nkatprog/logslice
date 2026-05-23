"""Keyword highlighting for log entry messages."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry

# ANSI colour codes
_RESET = "\033[0m"
_COLOURS = {
    "red": "\033[31m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "bold": "\033[1m",
}


@dataclass
class HighlightRule:
    """A keyword pattern and the colour to apply when it matches."""

    pattern: str
    colour: str = "yellow"
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(f"({re.escape(self.pattern)})", flags)

    def apply(self, text: str) -> str:
        """Wrap all occurrences of *pattern* in *text* with ANSI colour codes."""
        colour_code = _COLOURS.get(self.colour, _COLOURS["yellow"])
        return self._regex.sub(rf"{colour_code}\1{_RESET}", text)


def highlight_message(
    message: str,
    rules: List[HighlightRule],
) -> str:
    """Apply every rule in *rules* to *message* in order."""
    for rule in rules:
        message = rule.apply(message)
    return message


def highlight_entry(
    entry: LogEntry,
    rules: List[HighlightRule],
) -> LogEntry:
    """Return a copy of *entry* with its message highlighted according to *rules*."""
    highlighted = highlight_message(entry.message, rules)
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=highlighted,
        raw=entry.raw,
    )


def rules_from_strings(
    patterns: List[str],
    colour: str = "yellow",
    case_sensitive: bool = False,
) -> List[HighlightRule]:
    """Convenience factory: build a list of :class:`HighlightRule` from plain strings."""
    return [
        HighlightRule(pattern=p, colour=colour, case_sensitive=case_sensitive)
        for p in patterns
    ]

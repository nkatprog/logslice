"""Deduplication of repeated log entries within a stream."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogEntry


@dataclass
class _State:
    entry: LogEntry
    count: int = 1


def _make_collapsed(state: _State) -> LogEntry:
    """Return a (possibly annotated) entry representing *state*."""
    if state.count == 1:
        return state.entry
    original = state.entry
    new_message = f"{original.message} [repeated {state.count}x]"
    return LogEntry(
        timestamp=original.timestamp,
        severity=original.severity,
        message=new_message,
        raw=original.raw,
    )


def deduplicate(
    entries: Iterable[LogEntry],
    *,
    key: str = "message",
    max_gap: Optional[int] = None,
) -> Iterator[LogEntry]:
    """Collapse consecutive duplicate log entries.

    Parameters
    ----------
    entries:
        Source entries to process.
    key:
        Attribute of :class:`LogEntry` used to decide equality.
        Defaults to ``"message"``.
    max_gap:
        If given, a run of duplicates is broken after this many repetitions
        and a new run begins.  ``None`` means no limit.
    """
    state: Optional[_State] = None

    for entry in entries:
        entry_key = getattr(entry, key)
        if state is None:
            state = _State(entry=entry)
            continue

        prev_key = getattr(state.entry, key)
        at_limit = max_gap is not None and state.count >= max_gap

        if entry_key == prev_key and not at_limit:
            state.count += 1
        else:
            yield _make_collapsed(state)
            state = _State(entry=entry)

    if state is not None:
        yield _make_collapsed(state)

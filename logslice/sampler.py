"""Rate-based log sampler: keep every N-th entry per severity bucket."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogEntry


@dataclass
class _Counter:
    counts: dict[str, int] = field(default_factory=dict)

    def increment(self, key: str) -> int:
        """Increment counter for *key* and return the new value."""
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def reset(self) -> None:
        self.counts.clear()


def sample(
    entries: Iterable[LogEntry],
    rate: int,
    per_severity: bool = False,
) -> Iterator[LogEntry]:
    """Yield every *rate*-th log entry.

    Parameters
    ----------
    entries:
        Source entries to sample.
    rate:
        Keep one entry for every *rate* entries seen.  A rate of 1 keeps
        everything; a rate of 0 raises ``ValueError``.
    per_severity:
        When *True* the counter is maintained independently for each
        severity level so that rare severities are not starved.
    """
    if rate < 1:
        raise ValueError(f"rate must be >= 1, got {rate!r}")

    counter = _Counter()
    for entry in entries:
        key = entry.severity if per_severity else "_all"
        n = counter.increment(key)
        if n % rate == 0:
            yield entry

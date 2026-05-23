"""Tail and watch a log file, emitting new entries in real time."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterator, Optional

from logslice.parser import LogEntry, parse_line
from logslice.filter import _min_severity_level

_DEFAULT_POLL_INTERVAL = 0.25  # seconds


def _tail_lines(path: Path, from_end: bool = True) -> Iterator[str]:
    """Open *path* and yield new lines as they are appended.

    If *from_end* is True the file pointer starts at EOF so only
    lines written after the watch begins are returned.
    """
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        if from_end:
            fh.seek(0, 2)  # seek to end
        while True:
            line = fh.readline()
            if line:
                yield line.rstrip("\n")
            else:
                yield ""  # sentinel: no new data


def watch(
    path: str | Path,
    *,
    min_severity: Optional[str] = None,
    callback: Callable[[LogEntry], None],
    poll_interval: float = _DEFAULT_POLL_INTERVAL,
    from_end: bool = True,
) -> None:
    """Continuously watch *path* and invoke *callback* for each matching entry.

    Parameters
    ----------
    path:
        Log file to monitor.
    min_severity:
        If given, only entries at or above this severity are forwarded.
    callback:
        Callable that receives each matching :class:`~logslice.parser.LogEntry`.
    poll_interval:
        Seconds to sleep when no new data is available.
    from_end:
        When True (default) skip existing content and watch only new lines.
    """
    path = Path(path)
    min_level = _min_severity_level(min_severity) if min_severity else None

    for raw in _tail_lines(path, from_end=from_end):
        if not raw:
            time.sleep(poll_interval)
            continue

        entry = parse_line(raw)
        if entry is None:
            continue

        if min_level is not None and entry.level < min_level:
            continue

        callback(entry)

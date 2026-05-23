"""Export filtered log entries to alternate formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import Iterable, Literal

from logslice.parser import LogEntry

ExportFormat = Literal["json", "csv"]


def _entry_to_dict(entry: LogEntry) -> dict:
    """Convert a LogEntry to a plain dictionary."""
    return {
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "severity": entry.severity,
        "message": entry.message,
        "raw": entry.raw,
    }


def entries_to_json(
    entries: Iterable[LogEntry],
    *,
    indent: int | None = 2,
) -> str:
    """Serialise *entries* to a JSON string.

    Parameters
    ----------
    entries:
        Iterable of parsed log entries.
    indent:
        Pretty-print indentation level; pass ``None`` for compact output.
    """
    records = [_entry_to_dict(e) for e in entries]
    return json.dumps(records, indent=indent, default=str)


def entries_to_csv(entries: Iterable[LogEntry]) -> str:
    """Serialise *entries* to a CSV string with a header row."""
    buf = io.StringIO()
    fieldnames = ["timestamp", "severity", "message", "raw"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for entry in entries:
        writer.writerow(_entry_to_dict(entry))
    return buf.getvalue()


def export_entries(
    entries: Iterable[LogEntry],
    fmt: ExportFormat,
    output_path: str | None = None,
) -> str:
    """Export *entries* in *fmt* format, optionally writing to *output_path*.

    Returns the serialised string regardless of whether a file was written.

    Raises
    ------
    ValueError
        If *fmt* is not a supported export format.
    """
    if fmt == "json":
        data = entries_to_json(entries)
    elif fmt == "csv":
        data = entries_to_csv(entries)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")

    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(data)

    return data

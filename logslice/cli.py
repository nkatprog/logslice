"""Command-line interface for logslice."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from logslice.filter import filter_file
from logslice.output import write_entries


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string supplied on the command line."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime {value!r}. "
        "Expected ISO-8601, e.g. 2024-01-15T08:30:00"
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Extract and filter log segments by time range and severity.",
    )
    p.add_argument("file", nargs="+", type=Path, help="Log file(s) to process.")
    p.add_argument(
        "--from", dest="from_dt", metavar="DATETIME", type=_parse_dt,
        help="Include entries at or after this datetime.",
    )
    p.add_argument(
        "--to", dest="to_dt", metavar="DATETIME", type=_parse_dt,
        help="Include entries at or before this datetime.",
    )
    p.add_argument(
        "--min-severity", "-s", metavar="LEVEL", default=None,
        help="Minimum severity level (DEBUG, INFO, WARN, ERROR, CRITICAL).",
    )
    p.add_argument(
        "--colour", "--color", action="store_true",
        help="Colourise output by severity level.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    total = 0
    for path in args.file:
        if not path.exists():
            print(f"logslice: {path}: file not found", file=sys.stderr)
            return 1
        entries = filter_file(
            path,
            from_dt=args.from_dt,
            to_dt=args.to_dt,
            min_severity=args.min_severity,
        )
        total += write_entries(entries, colour=args.colour)

    return 0 if total >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())

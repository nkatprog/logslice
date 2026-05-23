"""CLI sub-command: truncate long log messages."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from logslice.filter import filter_file
from logslice.output import write_entries
from logslice.truncator import TruncateOptions, truncate_entries


def build_truncate_parser(
    parser: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="logslice-truncate",
            description="Truncate long log messages to a maximum length.",
        )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Log file to read (default: stdin).",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=200,
        metavar="N",
        help="Maximum message length in characters (default: 200).",
    )
    parser.add_argument(
        "--ellipsis",
        default="...",
        help="String appended to truncated messages (default: '...').",
    )
    parser.add_argument(
        "--severity",
        nargs=2,
        action="append",
        metavar=("LEVEL", "N"),
        dest="per_severity",
        help="Per-severity override, e.g. --severity ERROR 80.",
    )
    parser.add_argument(
        "--colour",
        action="store_true",
        default=False,
        help="Colourise output by severity.",
    )
    return parser


def truncate_main(argv: Sequence[str] | None = None) -> None:
    parser = build_truncate_parser()
    args = parser.parse_args(argv)

    per_severity: dict[str, int] | None = None
    if args.per_severity:
        try:
            per_severity = {sev.upper(): int(n) for sev, n in args.per_severity}
        except ValueError:
            parser.error("--severity N must be an integer.")

    try:
        opts = TruncateOptions(
            max_length=args.max_length,
            ellipsis=args.ellipsis,
            per_severity=per_severity,
        )
    except ValueError as exc:
        parser.error(str(exc))

    source = sys.stdin if args.file == "-" else open(args.file)
    try:
        entries = filter_file(source)
        truncated = truncate_entries(entries, opts)
        write_entries(truncated, sys.stdout, colour=args.colour)
    finally:
        if source is not sys.stdin:
            source.close()


if __name__ == "__main__":  # pragma: no cover
    truncate_main()

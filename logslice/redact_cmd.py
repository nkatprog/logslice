"""CLI sub-command: redact sensitive data from a log stream."""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

from logslice.filter import filter_file
from logslice.output import format_entry, write_entries
from logslice.redactor import RedactOptions, redact_entries

_BUILTIN_CHOICES = ["ipv4", "email", "token"]


def build_redact_parser(
    parent: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="logslice redact",
        description="Redact sensitive patterns from log lines.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Log file to read (default: stdin).",
    )
    parser.add_argument(
        "--builtin",
        dest="builtins",
        metavar="NAME",
        action="append",
        default=[],
        choices=_BUILTIN_CHOICES,
        help="Enable a built-in redaction pattern (ipv4, email, token).",
    )
    parser.add_argument(
        "--pattern",
        dest="patterns",
        metavar="REGEX",
        action="append",
        default=[],
        help="Custom regex pattern to redact (may be repeated).",
    )
    parser.add_argument(
        "--replacement",
        default="[REDACTED]",
        help="Replacement string (default: [REDACTED]).",
    )
    parser.add_argument(
        "--colour",
        action="store_true",
        default=False,
        help="Colourise output by severity.",
    )
    return parser


def redact_main(argv: Sequence[str] | None = None) -> None:
    parser = build_redact_parser()
    args = parser.parse_args(argv)

    opts = RedactOptions(
        replacement=args.replacement,
        patterns=args.patterns,
        builtins=args.builtins,
    )

    src = sys.stdin if args.file == "-" else open(args.file)
    try:
        entries = filter_file(src)
        redacted = redact_entries(entries, opts)
        write_entries(redacted, sys.stdout, colour=args.colour)
    finally:
        if src is not sys.stdin:
            src.close()


if __name__ == "__main__":  # pragma: no cover
    redact_main()

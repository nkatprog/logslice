"""CLI sub-command: highlight keywords in a log file."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.filter import filter_file
from logslice.highlighter import rules_from_strings, highlight_entry
from logslice.output import format_entry, write_entries


def build_highlight_parser(
    parent: Optional[argparse._SubParsersAction] = None,
) -> argparse.ArgumentParser:
    """Build (or register) the *highlight* argument parser."""
    kwargs = dict(
        description="Print log lines with keywords highlighted in colour.",
    )
    if parent is not None:
        parser = parent.add_parser("highlight", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="logslice-highlight", **kwargs)

    parser.add_argument("file", help="Path to the log file (use '-' for stdin).")
    parser.add_argument(
        "-k",
        "--keyword",
        dest="keywords",
        action="append",
        default=[],
        metavar="WORD",
        help="Keyword to highlight (repeatable).",
    )
    parser.add_argument(
        "--colour",
        default="yellow",
        choices=["red", "yellow", "green", "cyan", "magenta", "bold"],
        help="ANSI colour to use for all keywords (default: yellow).",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Match keywords case-sensitively.",
    )
    parser.add_argument(
        "--min-severity",
        default=None,
        metavar="LEVEL",
        help="Only show entries at or above this severity.",
    )
    parser.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable ANSI colour in output entirely.",
    )
    return parser


def highlight_main(argv: Optional[List[str]] = None) -> None:
    """Entry point for the *highlight* sub-command."""
    parser = build_highlight_parser()
    args = parser.parse_args(argv)

    source = sys.stdin if args.file == "-" else open(args.file)
    try:
        entries = list(filter_file(source, min_severity=args.min_severity))
    finally:
        if source is not sys.stdin:
            source.close()

    rules = rules_from_strings(
        args.keywords,
        colour=args.colour,
        case_sensitive=args.case_sensitive,
    )

    highlighted = [
        highlight_entry(e, rules) if rules else e
        for e in entries
    ]

    write_entries(highlighted, colour=not args.no_colour)


if __name__ == "__main__":  # pragma: no cover
    highlight_main()

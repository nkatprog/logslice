"""CLI entry point for the ``logslice tail`` sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from logslice.parser import LogEntry
from logslice.output import format_entry, _colourise
from logslice.watcher import watch


def _make_callback(colour: bool, fmt: str) -> "Callable[[LogEntry], None]":
    """Return a callback that prints each entry according to *fmt*."""

    def _cb(entry: LogEntry) -> None:
        line = format_entry(entry, colour=colour)
        print(line, flush=True)

    return _cb


def build_tail_parser(parent: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    """Build (or populate) the argument parser for the *tail* sub-command."""
    if parent is None:
        parent = argparse.ArgumentParser(
            prog="logslice tail",
            description="Watch a log file and stream new entries to stdout.",
        )

    parent.add_argument("file", help="Log file to watch.")
    parent.add_argument(
        "--severity",
        metavar="LEVEL",
        default=None,
        help="Minimum severity to display (DEBUG/INFO/WARN/ERROR/CRITICAL).",
    )
    parent.add_argument(
        "--no-colour",
        dest="no_colour",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    parent.add_argument(
        "--from-start",
        dest="from_start",
        action="store_true",
        default=False,
        help="Read from the beginning of the file instead of the end.",
    )
    return parent


def tail_main(argv: Optional[list[str]] = None) -> None:
    """Entry point for ``logslice tail``."""
    parser = build_tail_parser()
    args = parser.parse_args(argv)

    colour = not args.no_colour
    callback = _make_callback(colour=colour, fmt="default")

    try:
        watch(
            args.file,
            min_severity=args.severity,
            callback=callback,
            from_end=not args.from_start,
        )
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass  # clean exit on Ctrl-C


if __name__ == "__main__":  # pragma: no cover
    tail_main()

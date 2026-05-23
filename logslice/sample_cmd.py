"""CLI sub-command: sample — thin out a log stream by a given rate."""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

from logslice.filter import filter_file
from logslice.output import write_entries
from logslice.sampler import sample


def build_sample_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs: dict = dict(
        description="Sample log entries, keeping every N-th line.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("sample", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="logslice-sample", **kwargs)

    parser.add_argument("file", nargs="?", default="-", help="Log file (default: stdin)")
    parser.add_argument(
        "-n", "--rate",
        type=int, default=10, metavar="N",
        help="Keep one entry per N entries.",
    )
    parser.add_argument(
        "--per-severity",
        action="store_true",
        help="Apply the rate counter independently for each severity level.",
    )
    parser.add_argument(
        "--colour",
        action="store_true",
        help="Colourise output by severity.",
    )
    return parser


def sample_main(argv: Sequence[str] | None = None) -> None:
    parser = build_sample_parser()
    args = parser.parse_args(argv)

    src = sys.stdin if args.file == "-" else open(args.file)  # noqa: SIM115
    try:
        entries = list(filter_file(src))
        sampled = sample(entries, rate=args.rate, per_severity=args.per_severity)
        write_entries(sampled, colour=args.colour)
    finally:
        if src is not sys.stdin:
            src.close()


if __name__ == "__main__":  # pragma: no cover
    sample_main()

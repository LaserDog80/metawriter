"""CLI entry point for Nametag."""

import argparse
import sys

from .stamper import UnsupportedFormatError, VideoToolMissingError, stamp_previous_name


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="nametag",
        description=(
            "Stamp a file's previous filename into its metadata. "
            "Modifies the file in-place."
        ),
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the file to stamp.",
    )
    parser.add_argument(
        "old_name",
        type=str,
        help="The previous filename to record (name only, not full path).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        stamp_previous_name(args.file, args.old_name)
        print(f"Stamped: {args.old_name} -> {args.file}")
        return 0
    except (
        FileNotFoundError,
        ValueError,
        TypeError,
        UnsupportedFormatError,
        VideoToolMissingError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

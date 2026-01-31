"""CLI entry point for MetaWriter."""

import argparse
import json
import sys
from pathlib import Path

from . import append_metadata, read_metadata
from .exceptions import MetaWriterError


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="metawriter",
        description="Append AI-provenance metadata to image and video files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- append ---
    append_parser = subparsers.add_parser(
        "append",
        help="Append metadata entries to a media file (outputs a new copy).",
    )
    append_parser.add_argument("file", type=str, help="Source media file path.")
    append_parser.add_argument("--prompt", type=str, help="AI prompt used to generate the file.")
    append_parser.add_argument("--model", type=str, help="AI model name.")
    append_parser.add_argument("--provider", type=str, help="AI provider name.")
    append_parser.add_argument("--source-url", type=str, help="Source URL.")
    append_parser.add_argument(
        "--set",
        action="append",
        metavar="KEY=VALUE",
        dest="extra",
        help="Arbitrary key=value metadata entry (repeatable).",
    )
    append_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Custom output file path (default: <name>_mwrite.<ext>).",
    )

    # --- read ---
    read_parser = subparsers.add_parser(
        "read",
        help="Read metadata from a media file.",
    )
    read_parser.add_argument("file", type=str, help="Media file path to read.")
    read_parser.add_argument(
        "--only-mwrite",
        action="store_true",
        help="Show only MetaWriter entries (keys ending in _mwrite).",
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
        if args.command == "append":
            return _handle_append(args)
        else:
            return _handle_read(args)
    except MetaWriterError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (FileNotFoundError, FileExistsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _handle_append(args: argparse.Namespace) -> int:
    """Handle the 'append' subcommand."""
    entries: dict[str, str] = {}

    if args.prompt:
        entries["prompt"] = args.prompt
    if args.model:
        entries["model"] = args.model
    if args.provider:
        entries["provider"] = args.provider
    if args.source_url:
        entries["source_url"] = args.source_url

    if args.extra:
        for item in args.extra:
            if "=" not in item:
                print(f"Error: --set value must be KEY=VALUE, got: {item!r}", file=sys.stderr)
                return 1
            key, _, value = item.partition("=")
            entries[key] = value

    if not entries:
        print("Error: No metadata entries provided. Use --prompt, --model, etc.", file=sys.stderr)
        return 1

    output = append_metadata(
        args.file,
        entries,
        output_path=args.output,
    )
    print(f"Written: {output}")
    return 0


def _handle_read(args: argparse.Namespace) -> int:
    """Handle the 'read' subcommand."""
    metadata = read_metadata(args.file, only_mwrite=args.only_mwrite)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

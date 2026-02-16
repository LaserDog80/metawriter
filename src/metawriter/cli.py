"""CLI entry point for MetaWriter."""

import argparse
import json
import sys
from pathlib import Path

from .engine import tag_file, tag_files
from .exceptions import MetaWriterError
from .reader import read_metadata


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="metawriter",
        description="Preserve file identity through renames — stamp metadata into media files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- tag ---
    tag_parser = subparsers.add_parser(
        "tag",
        help="Tag files in-place with filename, timestamps, and optional provenance.",
    )
    tag_parser.add_argument(
        "paths",
        nargs="+",
        type=str,
        help="File or directory paths to tag.",
    )
    tag_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recurse into subdirectories.",
    )
    tag_parser.add_argument("--model", type=str, help="AI model name.")
    tag_parser.add_argument("--source-url", type=str, help="Source URL where file was downloaded.")
    tag_parser.add_argument("--prompt", type=str, help="AI prompt used to generate the file.")
    tag_parser.add_argument(
        "--set",
        action="append",
        metavar="KEY=VALUE",
        dest="extra",
        help="Arbitrary key=value metadata entry (repeatable).",
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

    # --- gui ---
    subparsers.add_parser(
        "gui",
        help="Launch the graphical interface.",
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
        if args.command == "tag":
            return _handle_tag(args)
        elif args.command == "read":
            return _handle_read(args)
        elif args.command == "gui":
            return _handle_gui()
        else:
            parser.print_help()
            return 1
    except MetaWriterError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (FileNotFoundError, FileExistsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _handle_tag(args: argparse.Namespace) -> int:
    """Handle the 'tag' subcommand."""
    extra: dict[str, str] | None = None
    if args.extra:
        extra = {}
        for item in args.extra:
            if "=" not in item:
                print(f"Error: --set value must be KEY=VALUE, got: {item!r}", file=sys.stderr)
                return 1
            key, _, value = item.partition("=")
            extra[key] = value

    paths = [Path(p) for p in args.paths]

    # Validate that paths exist
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"Path not found: {p}")

    # Single file — use tag_file for simpler output
    if len(paths) == 1 and paths[0].is_file():
        result = tag_file(
            paths[0],
            model=args.model,
            source_url=args.source_url,
            prompt=args.prompt,
            extra=extra,
        )
        print(f"Tagged: {paths[0].name}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # Multiple paths or directories
    def on_progress(path: Path, status: str) -> None:
        if status == "done":
            print(f"  Tagged: {path}")

    def on_error(path: Path, exc: Exception) -> None:
        print(f"  Error: {path} — {exc}", file=sys.stderr)

    tagged = tag_files(
        paths,
        recursive=args.recursive,
        model=args.model,
        source_url=args.source_url,
        prompt=args.prompt,
        extra=extra,
        on_progress=on_progress,
        on_error=on_error,
    )
    print(f"\n{len(tagged)} file(s) tagged.")
    return 0


def _handle_read(args: argparse.Namespace) -> int:
    """Handle the 'read' subcommand."""
    metadata = read_metadata(args.file, only_mwrite=args.only_mwrite)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    return 0


def _handle_gui() -> int:
    """Handle the 'gui' subcommand."""
    from .gui import MetaWriterApp
    app = MetaWriterApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

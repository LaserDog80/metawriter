"""Unified tagging engine for MetaWriter.

Combines filename stamping, birthtime capture, and optional provenance
fields into a single in-place tagging operation.
"""

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .birthtime import get_birthtime
from .formats import get_handler
from .models import MWRITE_SUFFIX
from .scanner import scan_paths


def tag_file(
    file_path: str | Path,
    *,
    model: str | None = None,
    source_url: str | None = None,
    prompt: str | None = None,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    """Tag a file in-place with metadata.

    Always stamps:
        - previous_name_mwrite: current filename
        - download_timestamp_mwrite: filesystem birthtime
        - timestamp_mwrite: current UTC time

    Optional (only written if provided):
        - model_mwrite
        - source_url_mwrite
        - prompt_mwrite

    Args:
        file_path: Path to the media file.
        model: AI model name (optional).
        source_url: Source URL where file was downloaded (optional).
        prompt: AI prompt used to generate the file (optional).
        extra: Additional key-value pairs (optional). Keys get _mwrite suffix
            if they don't already have it.

    Returns:
        Dict of all metadata that was written.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnsupportedFormatError: If the format is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    handler = get_handler(path)

    # Read existing _mwrite metadata to preserve optional fields
    existing = handler.read_metadata(path)
    existing_mwrite = {k: v for k, v in existing.items() if k.endswith(MWRITE_SUFFIX)}

    # Build new metadata — start with preserved values
    metadata: dict[str, str] = dict(existing_mwrite)

    # Always overwrite: filename and timestamps
    metadata["previous_name_mwrite"] = path.name
    metadata["timestamp_mwrite"] = datetime.now(timezone.utc).isoformat()

    # Preserve download_timestamp if already set, otherwise capture birthtime
    if "download_timestamp_mwrite" not in metadata:
        metadata["download_timestamp_mwrite"] = get_birthtime(path)

    # Optional fields — only overwrite if user provides a new value
    if model is not None:
        metadata["model_mwrite"] = model
    if source_url is not None:
        metadata["source_url_mwrite"] = source_url
    if prompt is not None:
        metadata["prompt_mwrite"] = prompt

    # Extra arbitrary entries
    if extra:
        for key, value in extra.items():
            suffixed = key if key.endswith(MWRITE_SUFFIX) else f"{key}{MWRITE_SUFFIX}"
            metadata[suffixed] = value

    handler.write_metadata_inplace(path, metadata)
    return metadata


def tag_files(
    paths: list[str | Path],
    *,
    recursive: bool = False,
    model: str | None = None,
    source_url: str | None = None,
    prompt: str | None = None,
    extra: dict[str, str] | None = None,
    on_progress: Callable[[Path, str], None] | None = None,
    on_error: Callable[[Path, Exception], None] | None = None,
) -> list[Path]:
    """Tag multiple files in-place, expanding directories.

    Args:
        paths: List of file or directory paths.
        recursive: If True, recurse into subdirectories.
        model: AI model name (optional, applied to all files).
        source_url: Source URL (optional, applied to all files).
        prompt: AI prompt (optional, applied to all files).
        extra: Additional key-value pairs (optional).
        on_progress: Callback(path, status_message) for each file processed.
        on_error: Callback(path, exception) for files that fail.

    Returns:
        List of successfully tagged file paths.
    """
    resolved = [Path(p) for p in paths]
    files = scan_paths(resolved, recursive=recursive)
    tagged: list[Path] = []

    for file_path in files:
        try:
            if on_progress:
                on_progress(file_path, "tagging")
            tag_file(
                file_path,
                model=model,
                source_url=source_url,
                prompt=prompt,
                extra=extra,
            )
            tagged.append(file_path)
            if on_progress:
                on_progress(file_path, "done")
        except Exception as exc:
            if on_error:
                on_error(file_path, exc)
            elif on_progress:
                on_progress(file_path, f"error: {exc}")

    return tagged

"""File discovery for MetaWriter — scan paths and expand directories."""

from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp",
    ".mp4", ".mov", ".mkv",
})


def scan_paths(
    paths: list[Path],
    *,
    recursive: bool = False,
) -> list[Path]:
    """Expand a list of paths into supported media files.

    Files are returned in sorted order. Directories are expanded to include
    all supported files within them.

    Args:
        paths: List of file or directory paths.
        recursive: If True, recurse into subdirectories.

    Returns:
        Sorted list of supported media file paths.
    """
    result: list[Path] = []
    for p in paths:
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            result.append(p)
        elif p.is_dir():
            glob_fn = p.rglob if recursive else p.glob
            for child in sorted(glob_fn("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS:
                    result.append(child)
    return sorted(set(result))

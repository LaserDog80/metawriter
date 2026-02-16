"""Video metadata handler for MP4, MOV, and MKV via ffmpeg subprocess."""

import json
import shutil
import subprocess
from pathlib import Path

from ..exceptions import VideoToolMissingError
from .base import BaseFormatHandler


def _check_tool(name: str) -> str:
    """Return the full path to a tool, or raise if not found."""
    path = shutil.which(name)
    if path is None:
        raise VideoToolMissingError(name)
    return path


class VideoHandler(BaseFormatHandler):
    """Read and write metadata for MP4, MOV, and MKV containers."""

    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read metadata from a video file using ffprobe.

        Args:
            path: Path to the video file.

        Returns:
            Dict of metadata key-value pairs.
        """
        ffprobe = _check_tool("ffprobe")

        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        tags = data.get("format", {}).get("tags", {})
        # Normalise keys to lowercase — ffprobe returns MKV tags in UPPERCASE.
        return {str(k).lower(): str(v) for k, v in tags.items()}

    def write_metadata(
        self,
        source_path: Path,
        output_path: Path,
        metadata: dict[str, str],
    ) -> None:
        """Copy a video file with metadata appended via ffmpeg.

        Uses ``ffmpeg -c copy`` to avoid re-encoding. Existing metadata is
        carried forward automatically by ffmpeg, and new entries are appended
        via ``-metadata`` flags.

        Args:
            source_path: Original video file.
            output_path: Destination path for new copy.
            metadata: New key-value entries to append.
        """
        ffmpeg = _check_tool("ffmpeg")

        # -movflags use_metadata_tags enables custom key names in MP4/MOV.
        ext = source_path.suffix.lower()
        movflags = ["-movflags", "use_metadata_tags"] if ext in (".mp4", ".mov") else []

        cmd = [
            ffmpeg,
            "-i", str(source_path),
            "-c", "copy",
            "-map_metadata", "0",  # carry forward all existing metadata
        ]

        for key, value in metadata.items():
            cmd.extend(["-metadata", f"{key}={value}"])

        cmd.extend(movflags)
        cmd.append(str(output_path))

        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

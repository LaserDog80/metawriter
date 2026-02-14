"""Video in-place stamper for MP4, MOV, and MKV via ffmpeg subprocess."""

import shutil
import subprocess
from pathlib import Path

from ..stamper import VideoToolMissingError


def _check_tool(name: str) -> str:
    """Return the full path to a tool, or raise if not found."""
    path = shutil.which(name)
    if path is None:
        raise VideoToolMissingError(name)
    return path


class VideoStamper:
    """Stamp metadata into video files via ffmpeg."""

    def stamp(self, file_path: Path, key: str, value: str) -> None:
        """Write a key-value pair into a video file's metadata in-place.

        Uses ffmpeg with -c copy to avoid re-encoding. Writes to a temp
        file then atomically replaces the original.

        Args:
            file_path: Path to the video file.
            key: Metadata key.
            value: Metadata value.
        """
        ffmpeg = _check_tool("ffmpeg")
        tmp_path = file_path.with_name(file_path.stem + "_nametag_tmp" + file_path.suffix)

        try:
            # -movflags use_metadata_tags enables custom key names in MP4/MOV.
            ext = file_path.suffix.lower()
            movflags = ["-movflags", "use_metadata_tags"] if ext in (".mp4", ".mov") else []

            cmd = [
                ffmpeg, "-y",
                "-i", str(file_path),
                "-c", "copy",
                "-map_metadata", "0",
                "-metadata", f"{key}={value}",
                *movflags,
                str(tmp_path),
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            tmp_path.replace(file_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

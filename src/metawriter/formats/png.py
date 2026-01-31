"""PNG metadata handler using Pillow tEXt/iTXt chunks."""

from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from .base import BaseFormatHandler


class PngHandler(BaseFormatHandler):
    """Read and write metadata via PNG text chunks."""

    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read all tEXt/iTXt/zTXt metadata from a PNG file.

        Args:
            path: Path to the PNG file.

        Returns:
            Dict of metadata key-value pairs.
        """
        with Image.open(path) as img:
            return dict(img.info) if img.info else {}

    def write_metadata(
        self,
        source_path: Path,
        output_path: Path,
        metadata: dict[str, str],
    ) -> None:
        """Copy a PNG file with merged metadata written as text chunks.

        Args:
            source_path: Original PNG file.
            output_path: Destination path for new copy.
            metadata: New key-value entries to append.
        """
        with Image.open(source_path) as img:
            existing = dict(img.info) if img.info else {}

            png_info = PngInfo()
            # Carry forward existing text chunks
            for key, value in existing.items():
                png_info.add_text(key, str(value))
            # Append new entries
            for key, value in metadata.items():
                png_info.add_text(key, value)

            img.save(str(output_path), pnginfo=png_info)

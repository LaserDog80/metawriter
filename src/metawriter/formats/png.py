"""PNG metadata handler using Pillow tEXt/iTXt chunks."""

from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from .base import BaseFormatHandler


class PngHandler(BaseFormatHandler):
    """Read and write metadata via PNG text chunks."""

    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read all tEXt/iTXt/zTXt metadata from a PNG file.

        Only returns text-chunk entries (string values). Non-text metadata
        like gamma, DPI, and ICC profiles are excluded.

        Args:
            path: Path to the PNG file.

        Returns:
            Dict of metadata key-value pairs.
        """
        with Image.open(path) as img:
            # img.text contains only text chunks; img.info also contains
            # non-text data (gamma as float, dpi as tuple, etc.)
            if hasattr(img, "text") and img.text:
                return {k: str(v) for k, v in img.text.items()}
            return {}

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
            # Read only text chunks from the source
            existing = {}
            if hasattr(img, "text") and img.text:
                existing = dict(img.text)

            png_info = PngInfo()
            for key, value in existing.items():
                png_info.add_text(key, str(value))
            for key, value in metadata.items():
                png_info.add_text(key, value)

            # Preserve ICC profile if present
            save_kwargs: dict = {"pnginfo": png_info}
            icc = img.info.get("icc_profile")
            if icc:
                save_kwargs["icc_profile"] = icc

            img.save(str(output_path), **save_kwargs)

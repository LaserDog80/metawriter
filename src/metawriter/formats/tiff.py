"""TIFF metadata handler using Pillow and piexif."""

from pathlib import Path

from PIL import Image
from PIL.TiffImagePlugin import ImageFileDirectory_v2

from ..xmp import build_xmp, parse_xmp
from .base import BaseFormatHandler

# TIFF tag 700 is the standard XMP tag.
_XMP_TAG = 700


class TiffHandler(BaseFormatHandler):
    """Read and write TIFF metadata via TIFF tags and XMP."""

    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read TIFF tags and embedded XMP metadata from a TIFF file.

        Args:
            path: Path to the TIFF file.

        Returns:
            Dict of metadata key-value pairs.
        """
        result: dict[str, str] = {}

        with Image.open(path) as img:
            if hasattr(img, "tag_v2") and img.tag_v2:
                for tag_id, value in img.tag_v2.items():
                    if isinstance(value, bytes):
                        if tag_id == _XMP_TAG:
                            result.update(parse_xmp(value))
                            continue
                        try:
                            value = value.decode("utf-8", errors="replace")
                        except Exception:
                            value = repr(value)
                    elif isinstance(value, tuple):
                        value = str(value)
                    result[f"tiff:{tag_id}"] = str(value)

        return result

    def write_metadata(
        self,
        source_path: Path,
        output_path: Path,
        metadata: dict[str, str],
    ) -> None:
        """Copy a TIFF file with metadata appended as XMP in tag 700.

        Args:
            source_path: Original TIFF file.
            output_path: Destination path for new copy.
            metadata: New key-value entries to append.
        """
        with Image.open(source_path) as img:
            # Read existing XMP from tag 700 if present
            existing_xmp: dict[str, str] = {}
            tiff_info = img.tag_v2 if hasattr(img, "tag_v2") and img.tag_v2 else ImageFileDirectory_v2()

            xmp_raw = tiff_info.get(_XMP_TAG, b"")
            if isinstance(xmp_raw, bytes) and xmp_raw:
                existing_xmp = parse_xmp(xmp_raw)

            merged = {**existing_xmp, **metadata}
            xmp_packet = build_xmp(merged)

            # Build new tiffinfo with the XMP tag set
            new_tiff_info = ImageFileDirectory_v2()
            for tag_id in tiff_info:
                if tag_id != _XMP_TAG:
                    try:
                        new_tiff_info[tag_id] = tiff_info[tag_id]
                    except Exception:
                        pass
            new_tiff_info[_XMP_TAG] = xmp_packet

            img.save(str(output_path), tiffinfo=new_tiff_info)

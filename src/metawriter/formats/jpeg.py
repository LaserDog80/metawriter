"""JPEG metadata handler using XMP sidecar blocks and EXIF via piexif."""

from pathlib import Path

import piexif
from PIL import Image

from ..xmp import build_xmp, parse_xmp
from .base import BaseFormatHandler


class JpegHandler(BaseFormatHandler):
    """Read and write JPEG metadata via XMP blocks and EXIF."""

    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read EXIF and XMP metadata from a JPEG file.

        Args:
            path: Path to the JPEG file.

        Returns:
            Dict of metadata key-value pairs.
        """
        result: dict[str, str] = {}

        with Image.open(path) as img:
            # Read EXIF data via piexif
            exif_data = img.info.get("exif", b"")
            if exif_data:
                try:
                    exif_dict = piexif.load(exif_data)
                    for ifd_name in exif_dict:
                        if ifd_name == "thumbnail":
                            continue
                        ifd = exif_dict[ifd_name]
                        if isinstance(ifd, dict):
                            for tag, val in ifd.items():
                                tag_name = piexif.TAGS.get(ifd_name, {}).get(
                                    tag, {}
                                ).get("name", str(tag))
                                if isinstance(val, bytes):
                                    try:
                                        val = val.decode("utf-8", errors="replace")
                                    except Exception:
                                        val = repr(val)
                                result[f"exif:{tag_name}"] = str(val)
                except Exception:
                    pass

            # Read XMP data
            xmp_data = img.info.get("xmp", b"")
            if isinstance(xmp_data, bytes) and xmp_data:
                result.update(parse_xmp(xmp_data))

        return result

    def write_metadata(
        self,
        source_path: Path,
        output_path: Path,
        metadata: dict[str, str],
    ) -> None:
        """Copy a JPEG file with metadata appended via XMP.

        EXIF data from the source is carried forward. New MetaWriter entries
        are stored in an XMP block.

        Args:
            source_path: Original JPEG file.
            output_path: Destination path for new copy.
            metadata: New key-value entries to append.
        """
        with Image.open(source_path) as img:
            # Preserve existing EXIF
            exif_bytes = img.info.get("exif", b"")

            # Read existing XMP entries and merge with new
            existing_xmp = img.info.get("xmp", b"")
            merged: dict[str, str] = {}
            if isinstance(existing_xmp, bytes) and existing_xmp:
                merged.update(parse_xmp(existing_xmp))
            merged.update(metadata)

            xmp_packet = build_xmp(merged)

            save_kwargs: dict = {"format": "JPEG"}
            if exif_bytes:
                save_kwargs["exif"] = exif_bytes
            save_kwargs["xmp"] = xmp_packet

            img.save(str(output_path), **save_kwargs)

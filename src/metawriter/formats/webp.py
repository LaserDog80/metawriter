"""WebP metadata handler using Pillow and piexif."""

from pathlib import Path

import piexif
from PIL import Image

from ..xmp import build_xmp, parse_xmp
from .base import BaseFormatHandler


class WebpHandler(BaseFormatHandler):
    """Read and write WebP metadata via EXIF and XMP."""

    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read EXIF and XMP metadata from a WebP file.

        Args:
            path: Path to the WebP file.

        Returns:
            Dict of metadata key-value pairs.
        """
        result: dict[str, str] = {}

        with Image.open(path) as img:
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
                                    # Check for embedded XMP in UserComment
                                    if tag == piexif.ExifIFD.UserComment:
                                        if val.startswith(b"XMP:"):
                                            result.update(parse_xmp(val[4:]))
                                            continue
                                    try:
                                        val = val.decode("utf-8", errors="replace")
                                    except Exception:
                                        val = repr(val)
                                result[f"exif:{tag_name}"] = str(val)
                except Exception:
                    pass

            # Also check for XMP info key
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
        """Copy a WebP file with metadata appended via EXIF XMP.

        Args:
            source_path: Original WebP file.
            output_path: Destination path for new copy.
            metadata: New key-value entries to append.
        """
        with Image.open(source_path) as img:
            # Read existing metadata
            existing_xmp: dict[str, str] = {}
            exif_data = img.info.get("exif", b"")
            if exif_data:
                try:
                    exif_dict = piexif.load(exif_data)
                    user_comment = exif_dict.get("Exif", {}).get(
                        piexif.ExifIFD.UserComment, b""
                    )
                    if isinstance(user_comment, bytes) and user_comment.startswith(b"XMP:"):
                        existing_xmp = parse_xmp(user_comment[4:])
                except Exception:
                    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
            else:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

            # Also check xmp info key
            xmp_raw = img.info.get("xmp", b"")
            if isinstance(xmp_raw, bytes) and xmp_raw:
                existing_xmp.update(parse_xmp(xmp_raw))

            merged = {**existing_xmp, **metadata}
            xmp_packet = build_xmp(merged)

            exif_dict.setdefault("Exif", {})
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = b"XMP:" + xmp_packet
            new_exif = piexif.dump(exif_dict)

            img.save(str(output_path), format="WEBP", exif=new_exif)

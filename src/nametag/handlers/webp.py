"""WebP in-place stamper using XMP in EXIF UserComment."""

from pathlib import Path

import piexif
from PIL import Image

from ..xmp import build_xmp, parse_xmp


class WebpStamper:
    """Stamp metadata into WebP files via EXIF XMP."""

    def stamp(self, file_path: Path, key: str, value: str) -> None:
        """Write a key-value pair into a WebP file's metadata in-place.

        Preserves existing EXIF data and merges into existing XMP.

        Args:
            file_path: Path to the WebP file.
            key: Metadata key.
            value: Metadata value.
        """
        tmp_path = file_path.with_name(file_path.stem + "_nametag_tmp" + file_path.suffix)

        try:
            with Image.open(file_path) as img:
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

                existing_xmp[key] = value
                xmp_packet = build_xmp(existing_xmp)

                exif_dict.setdefault("Exif", {})
                exif_dict["Exif"][piexif.ExifIFD.UserComment] = b"XMP:" + xmp_packet
                new_exif = piexif.dump(exif_dict)

                img.save(str(tmp_path), format="WEBP", exif=new_exif)

            tmp_path.replace(file_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

"""JPEG in-place stamper using XMP blocks."""

from pathlib import Path

from PIL import Image

from ..xmp import build_xmp, parse_xmp


class JpegStamper:
    """Stamp metadata into JPEG files via XMP blocks."""

    def stamp(self, file_path: Path, key: str, value: str) -> None:
        """Write a key-value pair into a JPEG file's metadata in-place.

        Preserves existing EXIF data and merges into existing XMP.

        Args:
            file_path: Path to the JPEG file.
            key: Metadata key.
            value: Metadata value.
        """
        tmp_path = file_path.with_name(file_path.stem + "_nametag_tmp" + file_path.suffix)

        try:
            with Image.open(file_path) as img:
                exif_bytes = img.info.get("exif", b"")

                existing_xmp: dict[str, str] = {}
                xmp_data = img.info.get("xmp", b"")
                if isinstance(xmp_data, bytes) and xmp_data:
                    existing_xmp = parse_xmp(xmp_data)

                existing_xmp[key] = value
                xmp_packet = build_xmp(existing_xmp)

                save_kwargs: dict = {"format": "JPEG", "xmp": xmp_packet}
                if exif_bytes:
                    save_kwargs["exif"] = exif_bytes

                img.save(str(tmp_path), **save_kwargs)

            tmp_path.replace(file_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

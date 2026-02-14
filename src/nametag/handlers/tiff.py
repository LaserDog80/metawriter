"""TIFF in-place stamper using XMP in tag 700."""

from pathlib import Path

from PIL import Image
from PIL.TiffImagePlugin import ImageFileDirectory_v2

from ..xmp import build_xmp, parse_xmp

# TIFF tag 700 is the standard XMP tag.
_XMP_TAG = 700


class TiffStamper:
    """Stamp metadata into TIFF files via XMP in TIFF tag 700."""

    def stamp(self, file_path: Path, key: str, value: str) -> None:
        """Write a key-value pair into a TIFF file's metadata in-place.

        Preserves existing TIFF tags and merges into existing XMP.

        Args:
            file_path: Path to the TIFF file.
            key: Metadata key.
            value: Metadata value.
        """
        tmp_path = file_path.with_name(file_path.stem + "_nametag_tmp" + file_path.suffix)

        try:
            with Image.open(file_path) as img:
                existing_xmp: dict[str, str] = {}
                tiff_info = (
                    img.tag_v2
                    if hasattr(img, "tag_v2") and img.tag_v2
                    else ImageFileDirectory_v2()
                )

                xmp_raw = tiff_info.get(_XMP_TAG, b"")
                if isinstance(xmp_raw, bytes) and xmp_raw:
                    existing_xmp = parse_xmp(xmp_raw)

                existing_xmp[key] = value
                xmp_packet = build_xmp(existing_xmp)

                new_tiff_info = ImageFileDirectory_v2()
                for tag_id in tiff_info:
                    if tag_id != _XMP_TAG:
                        try:
                            new_tiff_info[tag_id] = tiff_info[tag_id]
                        except Exception:
                            pass
                new_tiff_info[_XMP_TAG] = xmp_packet

                # Remove old XMP from the image's own tags to prevent
                # Pillow from merging stale data during save.
                if hasattr(img, "tag_v2") and _XMP_TAG in img.tag_v2:
                    del img.tag_v2[_XMP_TAG]

                img.save(str(tmp_path), tiffinfo=new_tiff_info)

            tmp_path.replace(file_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

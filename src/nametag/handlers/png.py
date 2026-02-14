"""PNG in-place stamper using Pillow tEXt chunks."""

from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo


class PngStamper:
    """Stamp metadata into PNG files via text chunks."""

    def stamp(self, file_path: Path, key: str, value: str) -> None:
        """Write a key-value pair into a PNG file's metadata in-place.

        Preserves existing text chunks and ICC profile.

        Args:
            file_path: Path to the PNG file.
            key: Metadata key.
            value: Metadata value.
        """
        tmp_path = file_path.with_name(file_path.stem + "_nametag_tmp" + file_path.suffix)

        try:
            with Image.open(file_path) as img:
                existing: dict[str, str] = {}
                if hasattr(img, "text") and img.text:
                    existing = {k: str(v) for k, v in img.text.items()}

                existing[key] = value

                png_info = PngInfo()
                for k, v in existing.items():
                    png_info.add_text(k, v)

                save_kwargs: dict = {"pnginfo": png_info}
                icc = img.info.get("icc_profile")
                if icc:
                    save_kwargs["icc_profile"] = icc

                img.save(str(tmp_path), **save_kwargs)

            tmp_path.replace(file_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

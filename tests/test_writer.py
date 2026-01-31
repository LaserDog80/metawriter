"""Tests for metawriter.writer — core append_metadata logic."""

from pathlib import Path
from unittest.mock import patch

import pytest

from metawriter.exceptions import MetadataIntegrityError, UnsupportedFormatError
from metawriter.writer import _default_output_path, append_metadata


# ---------------------------------------------------------------------------
# Default output path naming
# ---------------------------------------------------------------------------

class TestDefaultOutputPath:
    """Tests for _default_output_path()."""

    def test_default_name(self) -> None:
        assert _default_output_path(Path("photo.png")) == Path("photo_mwrite.png")

    def test_preserves_directory(self) -> None:
        result = _default_output_path(Path("/some/dir/image.jpg"))
        assert result == Path("/some/dir/image_mwrite.jpg")

    def test_preserves_extension(self) -> None:
        result = _default_output_path(Path("video.mp4"))
        assert result == Path("video_mwrite.mp4")


# ---------------------------------------------------------------------------
# append_metadata() — happy path
# ---------------------------------------------------------------------------

class TestAppendMetadataHappyPath:
    """Tests for append_metadata() with valid inputs."""

    def test_creates_output_file(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        result = append_metadata(str(sample_png), {"prompt": "test"}, output_path=str(out))
        assert Path(result).exists()

    def test_returns_output_path_string(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        result = append_metadata(str(sample_png), {"prompt": "test"}, output_path=str(out))
        assert result == str(out)

    def test_default_output_naming(self, sample_png: Path) -> None:
        result = append_metadata(str(sample_png), {"prompt": "test"})
        expected = sample_png.with_name("sample_mwrite.png")
        assert result == str(expected)
        assert expected.exists()

    def test_custom_output_path(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "custom" / "output.png"
        out.parent.mkdir(parents=True)
        result = append_metadata(str(sample_png), {"prompt": "test"}, output_path=str(out))
        assert Path(result) == out

    def test_original_file_untouched(self, sample_png: Path, tmp_path: Path) -> None:
        original_bytes = sample_png.read_bytes()
        out = tmp_path / "out.png"
        append_metadata(str(sample_png), {"prompt": "test"}, output_path=str(out))
        assert sample_png.read_bytes() == original_bytes

    def test_accepts_path_object(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        result = append_metadata(sample_png, {"prompt": "test"}, output_path=out)
        assert Path(result).exists()


# ---------------------------------------------------------------------------
# append_metadata() — error handling
# ---------------------------------------------------------------------------

class TestAppendMetadataErrors:
    """Tests for append_metadata() error conditions."""

    def test_source_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Source file not found"):
            append_metadata(str(tmp_path / "nonexistent.png"), {"prompt": "test"})

    def test_output_directory_not_found(self, sample_png: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Output directory"):
            append_metadata(
                str(sample_png),
                {"prompt": "test"},
                output_path="/nonexistent/dir/out.png",
            )

    def test_output_already_exists(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "existing.png"
        out.write_bytes(b"existing")
        with pytest.raises(FileExistsError, match="already exists"):
            append_metadata(str(sample_png), {"prompt": "test"}, output_path=str(out))

    def test_unsupported_format(self, tmp_path: Path) -> None:
        unsupported = tmp_path / "file.bmp"
        unsupported.write_bytes(b"BM" + b"\x00" * 50)
        with pytest.raises(UnsupportedFormatError):
            append_metadata(str(unsupported), {"prompt": "test"})

    def test_empty_key_rejected(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        with pytest.raises(ValueError):
            append_metadata(str(sample_png), {"": "value"}, output_path=str(out))

    def test_non_string_value_rejected(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        with pytest.raises(TypeError):
            append_metadata(str(sample_png), {"key": 123}, output_path=str(out))  # type: ignore[dict-item]


# ---------------------------------------------------------------------------
# Post-write integrity verification
# ---------------------------------------------------------------------------

class TestIntegrityVerification:
    """Tests for the post-write integrity check."""

    def test_integrity_passes_on_valid_write(self, sample_png_with_metadata: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        # Should not raise
        append_metadata(
            str(sample_png_with_metadata),
            {"prompt": "test"},
            output_path=str(out),
        )
        assert out.exists()

    def test_integrity_error_on_simulated_corruption(
        self, sample_png_with_metadata: Path, tmp_path: Path
    ) -> None:
        """Simulate a handler that drops metadata during write."""
        from metawriter.formats.png import PngHandler

        original_write = PngHandler.write_metadata

        def corrupted_write(self_handler, source_path, output_path, metadata):
            # Write a blank PNG with NO metadata at all
            from PIL import Image
            img = Image.new("RGB", (4, 4), color="black")
            img.save(str(output_path))

        out = tmp_path / "out.png"
        with patch.object(PngHandler, "write_metadata", corrupted_write):
            with pytest.raises(MetadataIntegrityError):
                append_metadata(
                    str(sample_png_with_metadata),
                    {"prompt": "test"},
                    output_path=str(out),
                )

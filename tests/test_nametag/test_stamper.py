"""Tests for nametag core stamper logic."""

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from nametag import stamp_previous_name, METADATA_KEY
from nametag.stamper import UnsupportedFormatError, _validate_old_name


class TestValidateOldName:
    """Tests for _validate_old_name."""

    def test_valid_name(self):
        assert _validate_old_name("photo.jpg") == "photo.jpg"

    def test_strips_whitespace(self):
        assert _validate_old_name("  photo.jpg  ") == "photo.jpg"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _validate_old_name("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _validate_old_name("   ")

    def test_non_string_raises(self):
        with pytest.raises(TypeError, match="string"):
            _validate_old_name(123)  # type: ignore[arg-type]


class TestStampPreviousName:
    """Tests for the public stamp_previous_name function."""

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            stamp_previous_name(tmp_path / "nonexistent.png", "old.png")

    def test_empty_old_name(self, sample_png):
        with pytest.raises(ValueError, match="empty"):
            stamp_previous_name(sample_png, "")

    def test_non_string_old_name(self, sample_png):
        with pytest.raises(TypeError, match="string"):
            stamp_previous_name(sample_png, 42)  # type: ignore[arg-type]

    def test_unsupported_format(self, tmp_path):
        p = tmp_path / "file.bmp"
        Image.new("RGB", (4, 4)).save(str(p), format="BMP")
        with pytest.raises(UnsupportedFormatError, match="Unsupported"):
            stamp_previous_name(p, "old.bmp")

    def test_stamps_png(self, sample_png):
        stamp_previous_name(sample_png, "old_photo.png")
        with Image.open(sample_png) as img:
            assert img.text[METADATA_KEY] == "old_photo.png"

    def test_file_modified_in_place(self, sample_png):
        """The original file path still exists after stamping."""
        stamp_previous_name(sample_png, "old.png")
        assert sample_png.exists()
        # Verify it's a valid image
        with Image.open(sample_png) as img:
            assert img.size == (4, 4)

    def test_preserves_existing_metadata(self, sample_png_with_metadata):
        stamp_previous_name(sample_png_with_metadata, "old.png")
        with Image.open(sample_png_with_metadata) as img:
            assert img.text["Author"] == "Test User"
            assert img.text["Description"] == "A test image"
            assert img.text[METADATA_KEY] == "old.png"

    def test_overwrites_previous_stamp(self, sample_png):
        stamp_previous_name(sample_png, "first_name.png")
        stamp_previous_name(sample_png, "second_name.png")
        with Image.open(sample_png) as img:
            assert img.text[METADATA_KEY] == "second_name.png"

    def test_unicode_old_name(self, sample_png):
        stamp_previous_name(sample_png, "写真.png")
        with Image.open(sample_png) as img:
            assert img.text[METADATA_KEY] == "写真.png"

    def test_special_chars_in_name(self, sample_png):
        stamp_previous_name(sample_png, "photo (1) [copy].png")
        with Image.open(sample_png) as img:
            assert img.text[METADATA_KEY] == "photo (1) [copy].png"

    def test_no_temp_file_left_behind(self, sample_png):
        stamp_previous_name(sample_png, "old.png")
        tmp_files = list(sample_png.parent.glob("*_nametag_tmp*"))
        assert len(tmp_files) == 0

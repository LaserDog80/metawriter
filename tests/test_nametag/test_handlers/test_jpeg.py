"""Tests for JPEG in-place stamper."""

import piexif
import pytest
from PIL import Image

from nametag.handlers.jpeg import JpegStamper
from nametag.xmp import parse_xmp


class TestJpegStamper:
    """Tests for JpegStamper.stamp()."""

    def test_stamp_basic(self, sample_jpeg):
        JpegStamper().stamp(sample_jpeg, "previous_name_mwrite", "old.jpg")
        with Image.open(sample_jpeg) as img:
            xmp = img.info.get("xmp", b"")
            entries = parse_xmp(xmp)
            assert entries["previous_name_mwrite"] == "old.jpg"

    def test_preserves_exif(self, sample_jpeg_with_exif):
        JpegStamper().stamp(sample_jpeg_with_exif, "previous_name_mwrite", "old.jpg")
        with Image.open(sample_jpeg_with_exif) as img:
            exif_data = img.info.get("exif", b"")
            assert exif_data  # EXIF should still be present
            exif_dict = piexif.load(exif_data)
            assert exif_dict["0th"][piexif.ImageIFD.Make] == b"TestCamera"

    def test_updates_existing_stamp(self, sample_jpeg):
        stamper = JpegStamper()
        stamper.stamp(sample_jpeg, "previous_name_mwrite", "first.jpg")
        stamper.stamp(sample_jpeg, "previous_name_mwrite", "second.jpg")
        with Image.open(sample_jpeg) as img:
            xmp = img.info.get("xmp", b"")
            entries = parse_xmp(xmp)
            assert entries["previous_name_mwrite"] == "second.jpg"

    def test_unicode_value(self, sample_jpeg):
        JpegStamper().stamp(sample_jpeg, "previous_name_mwrite", "写真.jpg")
        with Image.open(sample_jpeg) as img:
            xmp = img.info.get("xmp", b"")
            entries = parse_xmp(xmp)
            assert entries["previous_name_mwrite"] == "写真.jpg"

    def test_image_remains_valid(self, sample_jpeg):
        JpegStamper().stamp(sample_jpeg, "previous_name_mwrite", "old.jpg")
        with Image.open(sample_jpeg) as img:
            assert img.format == "JPEG"
            assert img.size == (4, 4)

    def test_no_temp_file_left(self, sample_jpeg):
        JpegStamper().stamp(sample_jpeg, "previous_name_mwrite", "old.jpg")
        tmp_files = list(sample_jpeg.parent.glob("*_nametag_tmp*"))
        assert len(tmp_files) == 0

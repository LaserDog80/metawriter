"""Tests for WebP in-place stamper."""

import piexif
import pytest
from PIL import Image

from nametag.handlers.webp import WebpStamper
from nametag.xmp import parse_xmp


class TestWebpStamper:
    """Tests for WebpStamper.stamp()."""

    def test_stamp_basic(self, sample_webp):
        WebpStamper().stamp(sample_webp, "previous_name_mwrite", "old.webp")
        with Image.open(sample_webp) as img:
            exif_data = img.info.get("exif", b"")
            assert exif_data
            exif_dict = piexif.load(exif_data)
            user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, b"")
            assert user_comment.startswith(b"XMP:")
            entries = parse_xmp(user_comment[4:])
            assert entries["previous_name_mwrite"] == "old.webp"

    def test_updates_existing_stamp(self, sample_webp):
        stamper = WebpStamper()
        stamper.stamp(sample_webp, "previous_name_mwrite", "first.webp")
        stamper.stamp(sample_webp, "previous_name_mwrite", "second.webp")
        with Image.open(sample_webp) as img:
            exif_data = img.info.get("exif", b"")
            exif_dict = piexif.load(exif_data)
            user_comment = exif_dict["Exif"][piexif.ExifIFD.UserComment]
            entries = parse_xmp(user_comment[4:])
            assert entries["previous_name_mwrite"] == "second.webp"

    def test_unicode_value(self, sample_webp):
        WebpStamper().stamp(sample_webp, "previous_name_mwrite", "写真.webp")
        with Image.open(sample_webp) as img:
            exif_data = img.info.get("exif", b"")
            exif_dict = piexif.load(exif_data)
            user_comment = exif_dict["Exif"][piexif.ExifIFD.UserComment]
            entries = parse_xmp(user_comment[4:])
            assert entries["previous_name_mwrite"] == "写真.webp"

    def test_image_remains_valid(self, sample_webp):
        WebpStamper().stamp(sample_webp, "previous_name_mwrite", "old.webp")
        with Image.open(sample_webp) as img:
            assert img.format == "WEBP"
            assert img.size == (4, 4)

    def test_no_temp_file_left(self, sample_webp):
        WebpStamper().stamp(sample_webp, "previous_name_mwrite", "old.webp")
        tmp_files = list(sample_webp.parent.glob("*_nametag_tmp*"))
        assert len(tmp_files) == 0

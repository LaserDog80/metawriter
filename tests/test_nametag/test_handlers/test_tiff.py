"""Tests for TIFF in-place stamper."""

import pytest
from PIL import Image

from nametag.handlers.tiff import TiffStamper
from nametag.xmp import parse_xmp

# TIFF tag 700 is the standard XMP tag.
_XMP_TAG = 700


class TestTiffStamper:
    """Tests for TiffStamper.stamp()."""

    def test_stamp_basic(self, sample_tiff):
        TiffStamper().stamp(sample_tiff, "previous_name_mwrite", "old.tiff")
        with Image.open(sample_tiff) as img:
            xmp_raw = img.tag_v2.get(_XMP_TAG, b"")
            entries = parse_xmp(xmp_raw)
            assert entries["previous_name_mwrite"] == "old.tiff"

    def test_updates_existing_stamp(self, sample_tiff):
        stamper = TiffStamper()
        stamper.stamp(sample_tiff, "previous_name_mwrite", "first.tiff")
        stamper.stamp(sample_tiff, "previous_name_mwrite", "second.tiff")
        with Image.open(sample_tiff) as img:
            xmp_raw = img.tag_v2.get(_XMP_TAG, b"")
            entries = parse_xmp(xmp_raw)
            assert entries["previous_name_mwrite"] == "second.tiff"

    def test_unicode_value(self, sample_tiff):
        TiffStamper().stamp(sample_tiff, "previous_name_mwrite", "画像.tiff")
        with Image.open(sample_tiff) as img:
            xmp_raw = img.tag_v2.get(_XMP_TAG, b"")
            entries = parse_xmp(xmp_raw)
            assert entries["previous_name_mwrite"] == "画像.tiff"

    def test_image_remains_valid(self, sample_tiff):
        TiffStamper().stamp(sample_tiff, "previous_name_mwrite", "old.tiff")
        with Image.open(sample_tiff) as img:
            assert img.format == "TIFF"
            assert img.size == (4, 4)

    def test_no_temp_file_left(self, sample_tiff):
        TiffStamper().stamp(sample_tiff, "previous_name_mwrite", "old.tiff")
        tmp_files = list(sample_tiff.parent.glob("*_nametag_tmp*"))
        assert len(tmp_files) == 0

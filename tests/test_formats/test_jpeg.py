"""Tests for the JPEG format handler — round-trip and edge cases."""

from pathlib import Path

import pytest

from metawriter.formats.jpeg import (
    JpegHandler,
    _build_xmp,
    _escape_xml,
    _parse_xmp,
    _sanitize_xml_name,
)
from metawriter.reader import read_metadata
from metawriter.writer import append_metadata

handler = JpegHandler()


# ---------------------------------------------------------------------------
# XMP helper functions
# ---------------------------------------------------------------------------

class TestXmpHelpers:
    """Tests for XMP building and parsing utilities."""

    def test_escape_xml_ampersand(self) -> None:
        assert _escape_xml("a & b") == "a &amp; b"

    def test_escape_xml_angle_brackets(self) -> None:
        assert _escape_xml("<tag>") == "&lt;tag&gt;"

    def test_escape_xml_quotes(self) -> None:
        assert _escape_xml('"hello"') == "&quot;hello&quot;"

    def test_sanitize_xml_name_valid(self) -> None:
        assert _sanitize_xml_name("prompt_mwrite") == "prompt_mwrite"

    def test_sanitize_xml_name_starts_with_digit(self) -> None:
        result = _sanitize_xml_name("1invalid")
        assert result[0] in ("_", *"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def test_sanitize_xml_name_special_chars(self) -> None:
        result = _sanitize_xml_name("key with spaces!")
        assert " " not in result
        assert "!" not in result

    def test_sanitize_xml_name_empty(self) -> None:
        result = _sanitize_xml_name("")
        assert result == "_"

    def test_build_and_parse_roundtrip(self) -> None:
        entries = {"prompt_mwrite": "sunset", "model_mwrite": "DALL-E"}
        xmp = _build_xmp(entries)
        parsed = _parse_xmp(xmp)
        assert parsed["prompt_mwrite"] == "sunset"
        assert parsed["model_mwrite"] == "DALL-E"

    def test_parse_empty_xmp(self) -> None:
        result = _parse_xmp(b"")
        assert result == {}

    def test_parse_invalid_xmp(self) -> None:
        result = _parse_xmp(b"not valid xml at all")
        assert result == {}


# ---------------------------------------------------------------------------
# Round-trip: write → read → verify
# ---------------------------------------------------------------------------

class TestJpegRoundTrip:
    """JPEG write/read round-trip tests."""

    def test_basic_roundtrip(self, sample_jpeg: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.jpg"
        append_metadata(str(sample_jpeg), {"prompt": "test"}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "test"
        assert "timestamp_mwrite" in meta

    def test_preserves_existing_exif(
        self, sample_jpeg_with_exif: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "out.jpg"
        append_metadata(
            str(sample_jpeg_with_exif),
            {"prompt": "test"},
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        # EXIF data should be preserved (prefixed with exif:)
        exif_keys = [k for k in meta if k.startswith("exif:")]
        assert len(exif_keys) > 0
        # New metadata present
        assert meta["prompt_mwrite"] == "test"

    def test_multiple_entries(self, sample_jpeg: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.jpg"
        append_metadata(
            str(sample_jpeg),
            {
                "prompt": "A sunset",
                "model": "DALL-E 3",
                "provider": "OpenAI",
            },
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "A sunset"
        assert meta["model_mwrite"] == "DALL-E 3"
        assert meta["provider_mwrite"] == "OpenAI"

    def test_original_untouched(self, sample_jpeg: Path, tmp_path: Path) -> None:
        original_bytes = sample_jpeg.read_bytes()
        out = tmp_path / "out.jpg"
        append_metadata(str(sample_jpeg), {"prompt": "test"}, output_path=str(out))
        assert sample_jpeg.read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestJpegEdgeCases:
    """Edge case tests for the JPEG handler."""

    def test_unicode_metadata(self, sample_jpeg: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.jpg"
        append_metadata(
            str(sample_jpeg),
            {"prompt": "日本語テスト", "model": "Ünïcödé"},
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "日本語テスト"
        assert meta["model_mwrite"] == "Ünïcödé"

    def test_large_metadata_value(self, sample_jpeg: Path, tmp_path: Path) -> None:
        large_value = "y" * 10_000
        out = tmp_path / "out.jpg"
        append_metadata(str(sample_jpeg), {"prompt": large_value}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == large_value

    def test_xml_special_chars_in_value(self, sample_jpeg: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.jpg"
        special = '<script>alert("xss")</script> & more'
        append_metadata(str(sample_jpeg), {"prompt": special}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == special

    def test_read_empty_jpeg(self, sample_jpeg: Path) -> None:
        meta = handler.read_metadata(sample_jpeg)
        assert isinstance(meta, dict)

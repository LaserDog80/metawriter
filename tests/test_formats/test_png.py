"""Tests for the PNG format handler — round-trip and edge cases."""

from pathlib import Path

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from metawriter.formats.png import PngHandler
from metawriter.reader import read_metadata
from metawriter.writer import append_metadata


handler = PngHandler()


# ---------------------------------------------------------------------------
# Round-trip: write → read back → verify
# ---------------------------------------------------------------------------

class TestPngRoundTrip:
    """PNG write/read round-trip tests."""

    def test_basic_roundtrip(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        append_metadata(str(sample_png), {"prompt": "sunset"}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "sunset"
        assert "timestamp_mwrite" in meta

    def test_preserves_existing_metadata(
        self, sample_png_with_metadata: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "out.png"
        append_metadata(
            str(sample_png_with_metadata),
            {"prompt": "test"},
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        # Original metadata preserved
        assert meta["Author"] == "Test User"
        assert meta["Description"] == "A test image"
        # New metadata present
        assert meta["prompt_mwrite"] == "test"

    def test_multiple_entries(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        append_metadata(
            str(sample_png),
            {
                "prompt": "A sunset over mountains",
                "model": "DALL-E 3",
                "provider": "OpenAI",
                "source_url": "https://example.com",
            },
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "A sunset over mountains"
        assert meta["model_mwrite"] == "DALL-E 3"
        assert meta["provider_mwrite"] == "OpenAI"
        assert meta["source_url_mwrite"] == "https://example.com"

    def test_original_file_byte_identical(self, sample_png: Path, tmp_path: Path) -> None:
        original_bytes = sample_png.read_bytes()
        out = tmp_path / "out.png"
        append_metadata(str(sample_png), {"prompt": "test"}, output_path=str(out))
        assert sample_png.read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestPngEdgeCases:
    """Edge case tests for the PNG handler."""

    def test_unicode_metadata(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        append_metadata(
            str(sample_png),
            {"prompt": "日本語テスト 🌅", "model": "Ünïcödé™"},
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "日本語テスト 🌅"
        assert meta["model_mwrite"] == "Ünïcödé™"

    def test_large_metadata_value(self, sample_png: Path, tmp_path: Path) -> None:
        large_value = "x" * 10_000  # 10 KB text
        out = tmp_path / "out.png"
        append_metadata(
            str(sample_png), {"prompt": large_value}, output_path=str(out)
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == large_value

    def test_special_characters_in_value(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        special = 'Quotes "here" & <there> and \'single\''
        append_metadata(str(sample_png), {"prompt": special}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == special

    def test_empty_file_no_metadata(self, sample_png: Path) -> None:
        meta = handler.read_metadata(sample_png)
        assert isinstance(meta, dict)

    def test_handler_read_with_existing_metadata(self, sample_png_with_metadata: Path) -> None:
        meta = handler.read_metadata(sample_png_with_metadata)
        assert "Author" in meta
        assert "Description" in meta

"""Tests for the WebP format handler — round-trip and edge cases."""

from pathlib import Path

import pytest

from metawriter.formats.webp import WebpHandler
from metawriter.reader import read_metadata
from metawriter.writer import append_metadata

handler = WebpHandler()


# ---------------------------------------------------------------------------
# Round-trip: write → read → verify
# ---------------------------------------------------------------------------

class TestWebpRoundTrip:
    """WebP write/read round-trip tests."""

    def test_basic_roundtrip(self, sample_webp: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.webp"
        append_metadata(str(sample_webp), {"prompt": "test"}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "test"
        assert "timestamp_mwrite" in meta

    def test_multiple_entries(self, sample_webp: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.webp"
        append_metadata(
            str(sample_webp),
            {
                "prompt": "ocean waves",
                "model": "Midjourney v5",
                "provider": "Midjourney",
            },
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "ocean waves"
        assert meta["model_mwrite"] == "Midjourney v5"
        assert meta["provider_mwrite"] == "Midjourney"

    def test_original_untouched(self, sample_webp: Path, tmp_path: Path) -> None:
        original_bytes = sample_webp.read_bytes()
        out = tmp_path / "out.webp"
        append_metadata(str(sample_webp), {"prompt": "test"}, output_path=str(out))
        assert sample_webp.read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestWebpEdgeCases:
    """Edge case tests for the WebP handler."""

    def test_unicode_metadata(self, sample_webp: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.webp"
        append_metadata(
            str(sample_webp),
            {"prompt": "日本語 テスト"},
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "日本語 テスト"

    def test_large_metadata_value(self, sample_webp: Path, tmp_path: Path) -> None:
        large_value = "w" * 10_000
        out = tmp_path / "out.webp"
        append_metadata(str(sample_webp), {"prompt": large_value}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == large_value

    def test_read_empty_webp(self, sample_webp: Path) -> None:
        meta = handler.read_metadata(sample_webp)
        assert isinstance(meta, dict)

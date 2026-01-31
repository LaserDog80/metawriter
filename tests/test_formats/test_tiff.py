"""Tests for the TIFF format handler — round-trip and edge cases."""

from pathlib import Path

import pytest

from metawriter.formats.tiff import TiffHandler
from metawriter.reader import read_metadata
from metawriter.writer import append_metadata

handler = TiffHandler()


# ---------------------------------------------------------------------------
# Round-trip: write → read → verify
# ---------------------------------------------------------------------------

class TestTiffRoundTrip:
    """TIFF write/read round-trip tests."""

    def test_basic_roundtrip(self, sample_tiff: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.tiff"
        append_metadata(str(sample_tiff), {"prompt": "test"}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "test"
        assert "timestamp_mwrite" in meta

    def test_multiple_entries(self, sample_tiff: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.tiff"
        append_metadata(
            str(sample_tiff),
            {
                "prompt": "mountain scene",
                "model": "Stable Diffusion",
                "provider": "StabilityAI",
            },
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "mountain scene"
        assert meta["model_mwrite"] == "Stable Diffusion"
        assert meta["provider_mwrite"] == "StabilityAI"

    def test_original_untouched(self, sample_tiff: Path, tmp_path: Path) -> None:
        original_bytes = sample_tiff.read_bytes()
        out = tmp_path / "out.tiff"
        append_metadata(str(sample_tiff), {"prompt": "test"}, output_path=str(out))
        assert sample_tiff.read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestTiffEdgeCases:
    """Edge case tests for the TIFF handler."""

    def test_unicode_metadata(self, sample_tiff: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.tiff"
        append_metadata(
            str(sample_tiff),
            {"prompt": "Ünïcödé テスト"},
            output_path=str(out),
        )
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "Ünïcödé テスト"

    def test_large_metadata_value(self, sample_tiff: Path, tmp_path: Path) -> None:
        large_value = "z" * 10_000
        out = tmp_path / "out.tiff"
        append_metadata(str(sample_tiff), {"prompt": large_value}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == large_value

    def test_read_empty_tiff(self, sample_tiff: Path) -> None:
        meta = handler.read_metadata(sample_tiff)
        assert isinstance(meta, dict)

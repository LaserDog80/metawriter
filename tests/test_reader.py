"""Tests for metawriter.reader — read_metadata functionality."""

from pathlib import Path

import pytest

from metawriter.exceptions import UnsupportedFormatError
from metawriter.reader import read_metadata
from metawriter.writer import append_metadata


# ---------------------------------------------------------------------------
# Basic read functionality
# ---------------------------------------------------------------------------

class TestReadMetadata:
    """Tests for read_metadata()."""

    def test_read_empty_png_returns_dict(self, sample_png: Path) -> None:
        result = read_metadata(str(sample_png))
        assert isinstance(result, dict)

    def test_read_png_with_metadata(self, sample_png_with_metadata: Path) -> None:
        result = read_metadata(str(sample_png_with_metadata))
        assert "Author" in result
        assert result["Author"] == "Test User"
        assert "Description" in result

    def test_read_after_write_roundtrip(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        append_metadata(str(sample_png), {"prompt": "sunset"}, output_path=str(out))
        result = read_metadata(str(out))
        assert "prompt_mwrite" in result
        assert result["prompt_mwrite"] == "sunset"
        assert "timestamp_mwrite" in result


# ---------------------------------------------------------------------------
# only_mwrite filter
# ---------------------------------------------------------------------------

class TestOnlyMwrite:
    """Tests for the only_mwrite filter."""

    def test_only_mwrite_filters_non_mwrite(
        self, sample_png_with_metadata: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "out.png"
        append_metadata(
            str(sample_png_with_metadata),
            {"prompt": "test"},
            output_path=str(out),
        )
        all_meta = read_metadata(str(out))
        mwrite_only = read_metadata(str(out), only_mwrite=True)
        # mwrite_only should be a subset
        assert len(mwrite_only) <= len(all_meta)
        for key in mwrite_only:
            assert key.endswith("_mwrite")

    def test_only_mwrite_includes_all_mwrite_keys(
        self, sample_png: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "out.png"
        append_metadata(
            str(sample_png),
            {"prompt": "sunset", "model": "DALL-E 3"},
            output_path=str(out),
        )
        result = read_metadata(str(out), only_mwrite=True)
        assert "prompt_mwrite" in result
        assert "model_mwrite" in result
        assert "timestamp_mwrite" in result


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestReadErrors:
    """Tests for read_metadata() error conditions."""

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_metadata(str(tmp_path / "nonexistent.png"))

    def test_unsupported_format(self, tmp_path: Path) -> None:
        f = tmp_path / "file.bmp"
        f.write_bytes(b"BM" + b"\x00" * 50)
        with pytest.raises(UnsupportedFormatError):
            read_metadata(str(f))

    def test_accepts_path_object(self, sample_png: Path) -> None:
        result = read_metadata(sample_png)
        assert isinstance(result, dict)

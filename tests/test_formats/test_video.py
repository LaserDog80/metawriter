"""Tests for the video format handler — MP4/MOV/MKV via ffmpeg."""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from metawriter.exceptions import VideoToolMissingError
from metawriter.formats.video import VideoHandler, _check_tool

has_ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
skip_no_ffmpeg = pytest.mark.skipif(not has_ffmpeg, reason="ffmpeg/ffprobe not available")

handler = VideoHandler()


# ---------------------------------------------------------------------------
# Tool availability check
# ---------------------------------------------------------------------------

class TestCheckTool:
    """Tests for _check_tool() utility."""

    def test_raises_when_tool_missing(self) -> None:
        with patch("shutil.which", return_value=None):
            with pytest.raises(VideoToolMissingError, match="ffprobe"):
                _check_tool("ffprobe")

    def test_returns_path_when_tool_exists(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/ffprobe"):
            result = _check_tool("ffprobe")
            assert result == "/usr/bin/ffprobe"


# ---------------------------------------------------------------------------
# Missing ffmpeg error handling
# ---------------------------------------------------------------------------

class TestMissingFfmpeg:
    """Tests that video operations fail gracefully without ffmpeg."""

    def test_read_raises_without_ffprobe(self, sample_mp4: Path) -> None:
        with patch("metawriter.formats.video.shutil.which", return_value=None):
            with pytest.raises(VideoToolMissingError, match="ffprobe"):
                handler.read_metadata(sample_mp4)

    def test_write_raises_without_ffmpeg(
        self, sample_mp4: Path, tmp_path: Path
    ) -> None:
        with patch("metawriter.formats.video.shutil.which", return_value=None):
            with pytest.raises(VideoToolMissingError, match="ffmpeg"):
                handler.write_metadata(
                    sample_mp4, tmp_path / "out.mp4", {"key": "val"}
                )


# ---------------------------------------------------------------------------
# Round-trip tests (require ffmpeg)
# ---------------------------------------------------------------------------

@skip_no_ffmpeg
class TestVideoRoundTrip:
    """Video write/read round-trip tests (require ffmpeg on PATH)."""

    def test_mp4_roundtrip(self, sample_mp4: Path, tmp_path: Path) -> None:
        from metawriter.writer import append_metadata
        from metawriter.reader import read_metadata

        out = tmp_path / "out.mp4"
        append_metadata(str(sample_mp4), {"prompt": "test"}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta.get("prompt_mwrite") == "test"

    def test_mov_roundtrip(self, sample_mov: Path, tmp_path: Path) -> None:
        from metawriter.writer import append_metadata
        from metawriter.reader import read_metadata

        out = tmp_path / "out.mov"
        append_metadata(str(sample_mov), {"prompt": "test"}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta.get("prompt_mwrite") == "test"

    def test_mkv_roundtrip(self, sample_mkv: Path, tmp_path: Path) -> None:
        from metawriter.writer import append_metadata
        from metawriter.reader import read_metadata

        out = tmp_path / "out.mkv"
        append_metadata(str(sample_mkv), {"prompt": "test"}, output_path=str(out))
        meta = read_metadata(str(out))
        assert meta.get("prompt_mwrite") == "test"


# ---------------------------------------------------------------------------
# Magic byte detection for video formats
# ---------------------------------------------------------------------------

class TestVideoMagicBytes:
    """Tests for video format detection via magic bytes."""

    def test_mp4_detected(self, sample_mp4: Path) -> None:
        from metawriter.formats.base import BaseFormatHandler
        assert BaseFormatHandler.detect_magic(sample_mp4) == "mp4"

    def test_mov_detected(self, sample_mov: Path) -> None:
        from metawriter.formats.base import BaseFormatHandler
        assert BaseFormatHandler.detect_magic(sample_mov) == "mov"

    def test_mkv_detected(self, sample_mkv: Path) -> None:
        from metawriter.formats.base import BaseFormatHandler
        assert BaseFormatHandler.detect_magic(sample_mkv) == "mkv"

"""Tests for Video in-place stamper."""

import json
import shutil
import subprocess

import pytest

from nametag.handlers.video import VideoStamper
from nametag.stamper import VideoToolMissingError

has_ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
skip_no_ffmpeg = pytest.mark.skipif(not has_ffmpeg, reason="ffmpeg/ffprobe not available")


def _read_video_metadata(path) -> dict[str, str]:
    """Read metadata from a video file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return data.get("format", {}).get("tags", {})


@skip_no_ffmpeg
class TestVideoStamper:
    """Tests for VideoStamper.stamp()."""

    def test_stamp_mp4(self, sample_mp4):
        VideoStamper().stamp(sample_mp4, "previous_name_mwrite", "old.mp4")
        tags = _read_video_metadata(sample_mp4)
        assert tags.get("previous_name_mwrite") == "old.mp4"

    def test_stamp_mov(self, sample_mov):
        VideoStamper().stamp(sample_mov, "previous_name_mwrite", "old.mov")
        tags = _read_video_metadata(sample_mov)
        assert tags.get("previous_name_mwrite") == "old.mov"

    def test_updates_existing_stamp(self, sample_mp4):
        stamper = VideoStamper()
        stamper.stamp(sample_mp4, "previous_name_mwrite", "first.mp4")
        stamper.stamp(sample_mp4, "previous_name_mwrite", "second.mp4")
        tags = _read_video_metadata(sample_mp4)
        assert tags.get("previous_name_mwrite") == "second.mp4"

    def test_no_temp_file_left(self, sample_mp4):
        VideoStamper().stamp(sample_mp4, "previous_name_mwrite", "old.mp4")
        tmp_files = list(sample_mp4.parent.glob("*_nametag_tmp*"))
        assert len(tmp_files) == 0


class TestVideoToolMissing:
    """Tests for missing ffmpeg."""

    def test_missing_ffmpeg_raises(self, sample_mp4, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        with pytest.raises(VideoToolMissingError, match="ffmpeg"):
            VideoStamper().stamp(sample_mp4, "previous_name_mwrite", "old.mp4")

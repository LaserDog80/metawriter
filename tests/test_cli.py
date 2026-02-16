"""Tests for metawriter.cli — CLI integration tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from metawriter.cli import main
from metawriter.reader import read_metadata


# ---------------------------------------------------------------------------
# tag subcommand
# ---------------------------------------------------------------------------

class TestCliTag:
    """Tests for the 'tag' CLI subcommand."""

    def test_tag_single_file(
        self, sample_png: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["tag", str(sample_png)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Tagged" in captured.out
        meta = read_metadata(str(sample_png), only_mwrite=True)
        assert meta["previous_name_mwrite"] == sample_png.name

    def test_tag_with_model(self, sample_png: Path) -> None:
        exit_code = main(["tag", str(sample_png), "--model", "DALL-E 3"])
        assert exit_code == 0
        meta = read_metadata(str(sample_png), only_mwrite=True)
        assert meta["model_mwrite"] == "DALL-E 3"

    def test_tag_with_all_optional_fields(self, sample_png: Path) -> None:
        exit_code = main([
            "tag", str(sample_png),
            "--model", "DALL-E 3",
            "--source-url", "https://example.com",
            "--prompt", "a sunset",
        ])
        assert exit_code == 0
        meta = read_metadata(str(sample_png), only_mwrite=True)
        assert meta["model_mwrite"] == "DALL-E 3"
        assert meta["source_url_mwrite"] == "https://example.com"
        assert meta["prompt_mwrite"] == "a sunset"

    def test_tag_with_set_key_value(self, sample_png: Path) -> None:
        exit_code = main([
            "tag", str(sample_png),
            "--set", "artist=Bob",
            "--set", "license=CC-BY",
        ])
        assert exit_code == 0
        meta = read_metadata(str(sample_png), only_mwrite=True)
        assert meta["artist_mwrite"] == "Bob"
        assert meta["license_mwrite"] == "CC-BY"

    def test_tag_invalid_set_format(
        self, sample_png: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["tag", str(sample_png), "--set", "no_equals_sign"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "KEY=VALUE" in captured.err

    def test_tag_source_not_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["tag", str(tmp_path / "no.png")])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_tag_directory(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        for name in ("a.png", "b.png"):
            p = tmp_path / name
            Image.new("RGB", (4, 4)).save(str(p))

        exit_code = main(["tag", str(tmp_path)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "2 file(s) tagged" in captured.out

    def test_tag_recursive(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        Image.new("RGB", (4, 4)).save(str(sub / "deep.png"))

        exit_code = main(["tag", str(tmp_path), "--recursive"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "1 file(s) tagged" in captured.out


# ---------------------------------------------------------------------------
# read subcommand
# ---------------------------------------------------------------------------

class TestCliRead:
    """Tests for the 'read' CLI subcommand."""

    def test_read_outputs_json(
        self, sample_png_with_metadata: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["read", str(sample_png_with_metadata)])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "Author" in data

    def test_read_only_mwrite(
        self, sample_png: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Tag the file first
        main(["tag", str(sample_png), "--model", "test"])
        capsys.readouterr()  # clear output
        exit_code = main(["read", str(sample_png), "--only-mwrite"])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        for key in data:
            assert key.endswith("_mwrite")

    def test_read_source_not_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["read", str(tmp_path / "no.png")])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err


# ---------------------------------------------------------------------------
# Missing ffmpeg via CLI
# ---------------------------------------------------------------------------

class TestCliVideoErrors:
    """Tests that video operations via CLI report clear errors."""

    def test_tag_video_without_ffmpeg(
        self, sample_mp4: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("metawriter.formats.video.shutil.which", return_value=None):
            exit_code = main(["tag", str(sample_mp4)])
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "ffmpeg" in captured.err.lower() or "ffprobe" in captured.err.lower()

"""Tests for metawriter.cli — CLI integration tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from metawriter.cli import main
from metawriter.reader import read_metadata


# ---------------------------------------------------------------------------
# append subcommand
# ---------------------------------------------------------------------------

class TestCliAppend:
    """Tests for the 'append' CLI subcommand."""

    def test_append_with_prompt(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        exit_code = main(["append", str(sample_png), "--prompt", "sunset", "-o", str(out)])
        assert exit_code == 0
        assert out.exists()
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "sunset"

    def test_append_with_all_provenance_fields(
        self, sample_png: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "out.png"
        exit_code = main([
            "append", str(sample_png),
            "--prompt", "test prompt",
            "--model", "DALL-E 3",
            "--provider", "OpenAI",
            "--source-url", "https://example.com",
            "-o", str(out),
        ])
        assert exit_code == 0
        meta = read_metadata(str(out))
        assert meta["prompt_mwrite"] == "test prompt"
        assert meta["model_mwrite"] == "DALL-E 3"
        assert meta["provider_mwrite"] == "OpenAI"
        assert meta["source_url_mwrite"] == "https://example.com"

    def test_append_with_set_key_value(self, sample_png: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.png"
        exit_code = main([
            "append", str(sample_png),
            "--set", "artist=Bob",
            "--set", "license=CC-BY",
            "-o", str(out),
        ])
        assert exit_code == 0
        meta = read_metadata(str(out))
        assert meta["artist_mwrite"] == "Bob"
        assert meta["license_mwrite"] == "CC-BY"

    def test_append_no_entries_returns_error(
        self, sample_png: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["append", str(sample_png)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "No metadata entries" in captured.err

    def test_append_invalid_set_format(
        self, sample_png: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["append", str(sample_png), "--set", "no_equals_sign"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "KEY=VALUE" in captured.err

    def test_append_default_output_naming(self, sample_png: Path) -> None:
        exit_code = main(["append", str(sample_png), "--prompt", "test"])
        expected = sample_png.with_name("sample_mwrite.png")
        assert exit_code == 0
        assert expected.exists()
        # Clean up
        expected.unlink()

    def test_append_source_not_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["append", str(tmp_path / "no.png"), "--prompt", "test"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_append_output_already_exists(
        self, sample_png: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = tmp_path / "existing.png"
        out.write_bytes(b"data")
        exit_code = main([
            "append", str(sample_png), "--prompt", "test", "-o", str(out)
        ])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err


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
        self, sample_png: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = tmp_path / "out.png"
        main(["append", str(sample_png), "--prompt", "test", "-o", str(out)])
        # Clear captured output from append before calling read
        capsys.readouterr()
        exit_code = main(["read", str(out), "--only-mwrite"])
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

    def test_append_video_without_ffmpeg(
        self, sample_mp4: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("metawriter.formats.video.shutil.which", return_value=None):
            out = tmp_path / "out.mp4"
            exit_code = main([
                "append", str(sample_mp4), "--prompt", "test", "-o", str(out)
            ])
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "ffmpeg" in captured.err.lower() or "ffprobe" in captured.err.lower()

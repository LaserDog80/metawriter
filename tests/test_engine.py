"""Tests for the unified tagging engine."""

from pathlib import Path

import pytest
from PIL import Image

from metawriter.engine import tag_file, tag_files
from metawriter.reader import read_metadata


class TestTagFile:
    """Tests for the tag_file() function."""

    def test_stamps_filename(self, sample_png: Path) -> None:
        result = tag_file(sample_png)
        assert result["previous_name_mwrite"] == sample_png.name

    def test_stamps_download_timestamp(self, sample_png: Path) -> None:
        result = tag_file(sample_png)
        assert "download_timestamp_mwrite" in result

    def test_stamps_tag_timestamp(self, sample_png: Path) -> None:
        result = tag_file(sample_png)
        assert "timestamp_mwrite" in result

    def test_metadata_readable_after_tag(self, sample_png: Path) -> None:
        tag_file(sample_png)
        meta = read_metadata(str(sample_png), only_mwrite=True)
        assert meta["previous_name_mwrite"] == sample_png.name
        assert "timestamp_mwrite" in meta
        assert "download_timestamp_mwrite" in meta

    def test_optional_model(self, sample_png: Path) -> None:
        result = tag_file(sample_png, model="DALL-E 3")
        assert result["model_mwrite"] == "DALL-E 3"

    def test_optional_source_url(self, sample_png: Path) -> None:
        result = tag_file(sample_png, source_url="https://example.com")
        assert result["source_url_mwrite"] == "https://example.com"

    def test_optional_prompt(self, sample_png: Path) -> None:
        result = tag_file(sample_png, prompt="a sunset over the ocean")
        assert result["prompt_mwrite"] == "a sunset over the ocean"

    def test_extra_fields(self, sample_png: Path) -> None:
        result = tag_file(sample_png, extra={"custom": "value"})
        assert result["custom_mwrite"] == "value"

    def test_preserves_optional_on_retag(self, sample_png: Path) -> None:
        tag_file(sample_png, model="DALL-E 3", prompt="sunset")
        # Re-tag without providing model — should be preserved
        result = tag_file(sample_png)
        assert result["model_mwrite"] == "DALL-E 3"
        assert result["prompt_mwrite"] == "sunset"

    def test_overwrites_filename_on_retag(self, sample_png: Path, tmp_path: Path) -> None:
        tag_file(sample_png)
        # Simulate rename
        renamed = tmp_path / "renamed.png"
        sample_png.rename(renamed)
        result = tag_file(renamed)
        assert result["previous_name_mwrite"] == "renamed.png"

    def test_preserves_download_timestamp_on_retag(self, sample_png: Path) -> None:
        first = tag_file(sample_png)
        second = tag_file(sample_png)
        assert first["download_timestamp_mwrite"] == second["download_timestamp_mwrite"]

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            tag_file("/nonexistent/file.png")

    def test_unicode_values(self, sample_png: Path) -> None:
        result = tag_file(sample_png, prompt="日本語テスト", model="Ünïcödé")
        meta = read_metadata(str(sample_png), only_mwrite=True)
        assert meta["prompt_mwrite"] == "日本語テスト"
        assert meta["model_mwrite"] == "Ünïcödé"

    def test_no_temp_file_left_behind(self, sample_png: Path) -> None:
        parent = sample_png.parent
        tag_file(sample_png)
        leftovers = list(parent.glob("*_mwrite_tmp*"))
        assert leftovers == []

    def test_all_image_formats(
        self,
        sample_png: Path,
        sample_jpeg: Path,
        sample_tiff: Path,
        sample_webp: Path,
    ) -> None:
        for path in [sample_png, sample_jpeg, sample_tiff, sample_webp]:
            result = tag_file(path, model="test")
            assert result["previous_name_mwrite"] == path.name
            assert result["model_mwrite"] == "test"


class TestTagFiles:
    """Tests for the tag_files() batch function."""

    def test_batch_tag(self, tmp_path: Path) -> None:
        files = []
        for name in ("a.png", "b.png", "c.png"):
            p = tmp_path / name
            Image.new("RGB", (4, 4), color="red").save(str(p))
            files.append(p)

        tagged = tag_files(files)
        assert len(tagged) == 3
        for p in tagged:
            meta = read_metadata(str(p), only_mwrite=True)
            assert "previous_name_mwrite" in meta

    def test_batch_with_directory(self, tmp_path: Path) -> None:
        for name in ("x.png", "y.jpg"):
            p = tmp_path / name
            fmt = "JPEG" if name.endswith(".jpg") else "PNG"
            Image.new("RGB", (4, 4)).save(str(p), format=fmt)

        tagged = tag_files([tmp_path], recursive=False)
        assert len(tagged) == 2

    def test_progress_callback(self, sample_png: Path) -> None:
        events: list[tuple[Path, str]] = []

        def on_progress(path: Path, status: str) -> None:
            events.append((path, status))

        tag_files([sample_png], on_progress=on_progress)
        statuses = [s for _, s in events]
        assert "tagging" in statuses
        assert "done" in statuses

    def test_error_callback(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.png"
        bad.write_text("not a real image")  # Invalid file

        errors: list[tuple[Path, Exception]] = []

        def on_error(path: Path, exc: Exception) -> None:
            errors.append((path, exc))

        tag_files([bad], on_error=on_error)
        assert len(errors) == 1
        assert errors[0][0] == bad

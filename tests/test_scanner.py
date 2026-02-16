"""Tests for the file scanner utility."""

from pathlib import Path

from PIL import Image

from metawriter.scanner import SUPPORTED_EXTENSIONS, scan_paths


class TestScanPaths:
    """Tests for scan_paths() file discovery."""

    def test_single_file(self, sample_png: Path) -> None:
        result = scan_paths([sample_png])
        assert result == [sample_png]

    def test_unsupported_extension_skipped(self, tmp_path: Path) -> None:
        txt = tmp_path / "notes.txt"
        txt.write_text("hello")
        result = scan_paths([txt])
        assert result == []

    def test_directory_flat(self, tmp_path: Path) -> None:
        img1 = tmp_path / "a.png"
        img2 = tmp_path / "b.jpg"
        txt = tmp_path / "c.txt"
        Image.new("RGB", (2, 2)).save(str(img1))
        Image.new("RGB", (2, 2)).save(str(img2), format="JPEG")
        txt.write_text("not an image")

        result = scan_paths([tmp_path])
        assert img1 in result
        assert img2 in result
        assert txt not in result

    def test_directory_recursive(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        img = sub / "deep.png"
        Image.new("RGB", (2, 2)).save(str(img))

        # Non-recursive should NOT find it
        flat = scan_paths([tmp_path])
        assert img not in flat

        # Recursive should find it
        deep = scan_paths([tmp_path], recursive=True)
        assert img in deep

    def test_deduplicates(self, sample_png: Path) -> None:
        result = scan_paths([sample_png, sample_png])
        assert len(result) == 1

    def test_supported_extensions_constant(self) -> None:
        assert ".png" in SUPPORTED_EXTENSIONS
        assert ".jpg" in SUPPORTED_EXTENSIONS
        assert ".mp4" in SUPPORTED_EXTENSIONS
        assert ".txt" not in SUPPORTED_EXTENSIONS

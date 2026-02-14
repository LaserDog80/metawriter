"""Tests for Nametag CLI."""

import pytest
from PIL import Image

from nametag.cli import main
from nametag import METADATA_KEY


class TestCli:
    """Tests for the nametag CLI."""

    def test_stamps_file(self, sample_png, capsys):
        result = main([str(sample_png), "old_photo.png"])
        assert result == 0
        with Image.open(sample_png) as img:
            assert img.text[METADATA_KEY] == "old_photo.png"

    def test_prints_success_message(self, sample_png, capsys):
        main([str(sample_png), "old.png"])
        captured = capsys.readouterr()
        assert "Stamped:" in captured.out
        assert "old.png" in captured.out

    def test_file_not_found(self, tmp_path, capsys):
        result = main([str(tmp_path / "nope.png"), "old.png"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_missing_arguments(self):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 2

    def test_unsupported_format(self, tmp_path, capsys):
        p = tmp_path / "file.bmp"
        Image.new("RGB", (4, 4)).save(str(p), format="BMP")
        result = main([str(p), "old.bmp"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Unsupported" in captured.err

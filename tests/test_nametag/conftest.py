"""Shared fixtures for Nametag tests.

Generates minimal sample files programmatically — no committed binary fixtures.
"""

import shutil
import subprocess
import struct
import sys
from pathlib import Path

import piexif
import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


# ---------------------------------------------------------------------------
# PNG fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_png(tmp_path: Path) -> Path:
    """Create a minimal 4x4 red PNG with no metadata."""
    p = tmp_path / "sample.png"
    img = Image.new("RGB", (4, 4), color="red")
    img.save(str(p))
    return p


@pytest.fixture()
def sample_png_with_metadata(tmp_path: Path) -> Path:
    """Create a minimal PNG with pre-existing text chunk metadata."""
    p = tmp_path / "sample_with_meta.png"
    img = Image.new("RGB", (4, 4), color="blue")
    info = PngInfo()
    info.add_text("Author", "Test User")
    info.add_text("Description", "A test image")
    img.save(str(p), pnginfo=info)
    return p


# ---------------------------------------------------------------------------
# JPEG fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_jpeg(tmp_path: Path) -> Path:
    """Create a minimal JPEG with no metadata."""
    p = tmp_path / "sample.jpg"
    img = Image.new("RGB", (4, 4), color="green")
    img.save(str(p), format="JPEG")
    return p


@pytest.fixture()
def sample_jpeg_with_exif(tmp_path: Path) -> Path:
    """Create a minimal JPEG with pre-existing EXIF data."""
    p = tmp_path / "sample_exif.jpg"
    img = Image.new("RGB", (4, 4), color="yellow")
    exif_dict = {
        "0th": {piexif.ImageIFD.Make: b"TestCamera"},
        "Exif": {},
        "GPS": {},
        "1st": {},
    }
    exif_bytes = piexif.dump(exif_dict)
    img.save(str(p), format="JPEG", exif=exif_bytes)
    return p


# ---------------------------------------------------------------------------
# TIFF fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_tiff(tmp_path: Path) -> Path:
    """Create a minimal TIFF with no extra metadata."""
    p = tmp_path / "sample.tiff"
    img = Image.new("RGB", (4, 4), color="purple")
    img.save(str(p), format="TIFF")
    return p


# ---------------------------------------------------------------------------
# WebP fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_webp(tmp_path: Path) -> Path:
    """Create a minimal WebP with no metadata."""
    p = tmp_path / "sample.webp"
    img = Image.new("RGB", (4, 4), color="orange")
    img.save(str(p), format="WEBP")
    return p


# ---------------------------------------------------------------------------
# Video fixtures (generated via ffmpeg for valid containers)
# ---------------------------------------------------------------------------

def _make_video_with_ffmpeg(path: Path, fmt: str = "mp4") -> Path:
    """Generate a minimal valid video file using ffmpeg.

    Creates a 1-frame, 1x1 pixel video that ffmpeg can read and write.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg not available")

    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=c=black:s=2x2:d=0.1:r=1",
        "-c:v", "libx264" if fmt != "mkv" else "libx264",
        "-frames:v", "1",
        str(path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return path


@pytest.fixture()
def sample_mp4(tmp_path: Path) -> Path:
    """Create a minimal valid MP4 via ffmpeg."""
    return _make_video_with_ffmpeg(tmp_path / "sample.mp4")


@pytest.fixture()
def sample_mov(tmp_path: Path) -> Path:
    """Create a minimal valid MOV via ffmpeg."""
    return _make_video_with_ffmpeg(tmp_path / "sample.mov")


@pytest.fixture()
def sample_mkv(tmp_path: Path) -> Path:
    """Create a minimal valid MKV via ffmpeg."""
    return _make_video_with_ffmpeg(tmp_path / "sample.mkv", fmt="mkv")


# ---------------------------------------------------------------------------
# Helper: check whether ffmpeg / ffprobe are available
# ---------------------------------------------------------------------------

has_ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
skip_no_ffmpeg = pytest.mark.skipif(not has_ffmpeg, reason="ffmpeg/ffprobe not available")

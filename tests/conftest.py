"""Shared fixtures for MetaWriter tests.

Generates minimal sample image files programmatically so tests are
self-contained and don't depend on committed binary fixtures.
"""

import shutil
import struct
import sys
from pathlib import Path

import piexif
import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


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
# Video fixtures (minimal valid containers)
# ---------------------------------------------------------------------------

def _make_minimal_mp4(path: Path) -> Path:
    """Write a minimal valid MP4 container (ftyp + moov boxes only).

    This is the smallest technically valid MP4 that ffprobe can read.
    """
    ftyp_brand = b"isom"
    ftyp_body = ftyp_brand + struct.pack(">I", 0) + ftyp_brand
    ftyp_size = 8 + len(ftyp_body)
    ftyp_box = struct.pack(">I", ftyp_size) + b"ftyp" + ftyp_body

    # Minimal moov box with an mvhd atom
    mvhd_body = b"\x00" * 108  # version 0 mvhd is 108 bytes
    mvhd_size = 8 + len(mvhd_body)
    mvhd_box = struct.pack(">I", mvhd_size) + b"mvhd" + mvhd_body
    moov_size = 8 + len(mvhd_box)
    moov_box = struct.pack(">I", moov_size) + b"moov" + mvhd_box

    path.write_bytes(ftyp_box + moov_box)
    return path


def _make_minimal_mov(path: Path) -> Path:
    """Write a minimal MOV container (ftyp brand = qt)."""
    ftyp_brand = b"qt  "
    ftyp_body = ftyp_brand + struct.pack(">I", 0) + ftyp_brand
    ftyp_size = 8 + len(ftyp_body)
    ftyp_box = struct.pack(">I", ftyp_size) + b"ftyp" + ftyp_body

    mvhd_body = b"\x00" * 108
    mvhd_size = 8 + len(mvhd_body)
    mvhd_box = struct.pack(">I", mvhd_size) + b"mvhd" + mvhd_body
    moov_size = 8 + len(mvhd_box)
    moov_box = struct.pack(">I", moov_size) + b"moov" + mvhd_box

    path.write_bytes(ftyp_box + moov_box)
    return path


def _make_minimal_mkv(path: Path) -> Path:
    """Write the MKV/WebM magic bytes header (EBML element)."""
    # Minimal EBML header that identifies the file as Matroska
    path.write_bytes(
        b"\x1a\x45\xdf\xa3"  # EBML element ID
        b"\x93"               # Size (19 bytes)
        b"\x42\x86\x81\x01"  # EBMLVersion: 1
        b"\x42\xf7\x81\x01"  # EBMLReadVersion: 1
        b"\x42\xf2\x81\x04"  # EBMLMaxIDLength: 4
        b"\x42\xf3\x81\x08"  # EBMLMaxSizeLength: 8
        b"\x42\x82\x84\x6d\x61\x74\x72"  # DocType partial
    )
    return path


@pytest.fixture()
def sample_mp4(tmp_path: Path) -> Path:
    """Create a minimal MP4 container."""
    return _make_minimal_mp4(tmp_path / "sample.mp4")


@pytest.fixture()
def sample_mov(tmp_path: Path) -> Path:
    """Create a minimal MOV container."""
    return _make_minimal_mov(tmp_path / "sample.mov")


@pytest.fixture()
def sample_mkv(tmp_path: Path) -> Path:
    """Create a minimal MKV container."""
    return _make_minimal_mkv(tmp_path / "sample.mkv")


# ---------------------------------------------------------------------------
# Helper: check whether ffmpeg / ffprobe are available
# ---------------------------------------------------------------------------

has_ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
skip_no_ffmpeg = pytest.mark.skipif(not has_ffmpeg, reason="ffmpeg/ffprobe not available")

# MetaWriter — Implementation Plan

## Goal

Build an append-only metadata utility that writes AI-provenance entries (prompts, models, providers, source sites) to image and video files without modifying or removing any pre-existing metadata.

---

## Requirements

1. **Append metadata entries** to supported image formats: PNG, JPEG, TIFF, WebP.
2. **Append metadata entries** to supported video containers: MP4, MOV, MKV.
3. **Never modify the original file.** Output a new copy with metadata appended. The source file is always left untouched.
4. **Read existing metadata** from the source file and carry it forward into the output copy.
5. **Support structured provenance fields** at minimum: `prompt`, `model`, `provider`, `source_url`, and a `timestamp` (auto-generated on write).
6. **Allow arbitrary key-value text entries** beyond the built-in provenance fields.
7. **Validate inputs** — reject empty keys, non-text values, and unsupported file formats with clear errors.
8. **Expose a Python API** (importable module) as the primary interface.
9. **Provide a CLI wrapper** for scripting and one-off use.
10. **Overwrite-in-place mode** deferred to a future version (not in v1).

---

## Inputs and Outputs

| Operation | Input | Output |
|-----------|-------|--------|
| Append metadata | Source file path + dict of key-value entries + optional output path | **New file** (copy of source) with metadata appended. Original untouched. |
| Read metadata | File path | Dict of all metadata entries currently stored |
| Verify integrity | Source file path + output file path | Boolean — confirms pre-existing metadata from source survived into output |

---

## Technical Approach

### Metadata storage strategy per format

| Format | Storage mechanism | Library |
|--------|-------------------|---------|
| **PNG** | `tEXt` / `iTXt` text chunks (native key-value support) | Pillow |
| **JPEG** | XMP sidecar block (arbitrary XML key-value, survives re-encoding) | Pillow + `defusedxml` for XMP parsing; `piexif` as fallback for EXIF fields |
| **TIFF** | XMP or EXIF `ImageDescription` / `UserComment` fields | Pillow + `piexif` |
| **WebP** | XMP or EXIF block | Pillow + `piexif` |
| **MP4 / MOV** | QuickTime/MPEG-4 metadata atoms | `ffmpeg` via subprocess (ffprobe to read, ffmpeg to write) |
| **MKV** | Matroska tags | `mkvpropedit` (from mkvtoolnix) or `ffmpeg` via subprocess |

**Naming convention:** All MetaWriter entries use the suffix `_mwrite` (e.g. `prompt_mwrite`, `model_mwrite`) to avoid collisions with existing metadata fields while keeping keys readable.

### File structure

```
metawriter/
├── src/
│   └── metawriter/
│       ├── __init__.py          # Public API surface
│       ├── writer.py            # Core MetadataWriter class (append + output new copy)
│       ├── reader.py            # Read-only metadata extraction
│       ├── models.py            # Entry dataclass, validation logic
│       ├── exceptions.py        # Custom exception hierarchy
│       ├── formats/
│       │   ├── __init__.py      # Format registry / dispatch
│       │   ├── base.py          # Abstract base handler
│       │   ├── png.py           # PNG text-chunk handler
│       │   ├── jpeg.py          # JPEG XMP/EXIF handler
│       │   ├── tiff.py          # TIFF handler
│       │   ├── webp.py          # WebP handler
│       │   └── video.py         # MP4/MOV/MKV handler (ffmpeg-based)
│       └── cli.py               # CLI entry point (argparse)
├── tests/
│   ├── conftest.py              # Shared fixtures (sample files)
│   ├── test_writer.py           # Writer append + save tests
│   ├── test_reader.py           # Reader round-trip tests
│   ├── test_models.py           # Validation / data model tests
│   ├── test_formats/
│   │   ├── test_png.py
│   │   ├── test_jpeg.py
│   │   ├── test_tiff.py
│   │   ├── test_webp.py
│   │   └── test_video.py
│   ├── test_cli.py              # CLI integration tests
│   └── fixtures/                # Minimal sample files per format
│       ├── sample.png
│       ├── sample.jpg
│       ├── sample.tiff
│       ├── sample.webp
│       ├── sample.mp4
│       ├── sample.mov
│       └── sample.mkv
├── requirements.txt
├── plan.md
├── CLAUDE.md
├── LEARNINGS.md
└── README.md
```

### Core flow

```
User calls: append_metadata("photo.png", {"prompt": "sunset", "model": "DALL-E 3"})
  │
  ├─ 1. Detect format from extension + magic bytes
  ├─ 2. Dispatch to format-specific handler
  ├─ 3. Handler reads ALL existing metadata from source → snapshot
  ├─ 4. Validate new entries (non-empty keys, text values)
  ├─ 5. Merge: existing metadata + new entries (append, never replace)
  ├─ 6. Write merged result to a NEW output file (original untouched)
  └─ 7. Post-write verification: re-read output and confirm snapshot fields still present
```

### Key design decisions

- **New-copy output** — the original file is never modified. Every write produces a new output file. Default output path is `<name>_mwrite.<ext>` alongside the original. An overwrite-in-place mode may be added in a future version, but is out of scope for v1.
- **Post-write verification** — after every write, re-read the output file and assert that all metadata keys from the original source are still present. Raise `MetadataIntegrityError` if anything is missing.
- **Duplicate keys** — since the original is never touched, running the tool multiple times on the same source is safe (produces a fresh copy each time). If the user runs the tool on an already-processed copy, new entries are appended alongside existing `_mwrite` entries without conflict.
- **Video format dependency** — video support requires `ffmpeg` and optionally `mkvtoolnix` installed on the system. The module should raise a clear error if these are missing, and image support should work without them.

### Public API sketch

```python
from metawriter import append_metadata, read_metadata

# Append entries — produces "photo_mwrite.png" (original untouched)
output = append_metadata("photo.png", {
    "prompt": "A sunset over mountains",
    "model": "DALL-E 3",
    "provider": "OpenAI",
    "source_url": "https://example.com/gallery",
})
# output == "photo_mwrite.png"

# Custom output path
output = append_metadata("photo.png", {...}, output_path="tagged/photo.png")

# Read all metadata (including non-MetaWriter fields)
meta = read_metadata("photo_mwrite.png")
# Returns: {"prompt_mwrite": "A sunset...", "exif:Make": "Canon", ...}
```

### CLI sketch

```bash
# Append metadata — outputs photo_mwrite.png (original untouched)
metawriter append photo.png --prompt "A sunset" --model "DALL-E 3"

# Custom output path
metawriter append photo.png --prompt "A sunset" -o tagged/photo.png

# Append arbitrary key-value
metawriter append photo.png --set key=value --set another=value2

# Read metadata
metawriter read photo.png

# Read only MetaWriter entries (keys ending in _mwrite)
metawriter read photo.png --only-mwrite
```

---

## Test Cases

### Unit tests

1. **Append to empty file** — file with no metadata receives new entries in output copy correctly.
2. **Append preserves existing** — file with pre-existing EXIF/text chunks retains all original fields in the output copy.
3. **Original untouched** — source file is byte-identical before and after the operation.
4. **Validation rejects bad input** — empty key → `ValueError`; non-string value → `TypeError`; unsupported format → `UnsupportedFormatError`.
5. **Post-write integrity check** — simulated corruption triggers `MetadataIntegrityError`.
6. **Timestamp auto-populated** — every entry gets a `timestamp_mwrite` field with ISO-8601 time.
7. **Default output naming** — `photo.png` → `photo_mwrite.png`; custom output path also works.

### Integration tests (per format)

7. **PNG round-trip** — write entries → read back → all entries present and correct.
8. **JPEG round-trip** — same, verifying XMP/EXIF survival.
9. **TIFF round-trip** — same.
10. **WebP round-trip** — same.
11. **MP4 round-trip** — same (requires ffmpeg in test environment).
12. **MOV round-trip** — same.
13. **MKV round-trip** — same.

### Edge cases

15. **Source file not found** — raises `FileNotFoundError`.
16. **Output directory doesn't exist** — raises `FileNotFoundError` with helpful message.
17. **Output path already exists** — raises error rather than silently overwriting (user must delete or choose different path).
18. **Extension/content mismatch** — `.png` file that is actually a JPEG → detected via magic bytes, raises `FormatMismatchError`.
19. **Very large metadata value** — 10 KB text string as a value → handled gracefully per format limits.
20. **Unicode metadata** — non-ASCII characters in keys and values preserved correctly.

### CLI tests

21. **`append` subcommand** — end-to-end: CLI writes output file, `read_metadata()` confirms entries.
22. **`read` subcommand** — outputs JSON to stdout.
23. **Missing ffmpeg** — video operation without ffmpeg prints actionable error message.

---

## Dependencies

```
Pillow>=10.0.0        # Image metadata read/write
piexif>=1.1.3         # EXIF manipulation for JPEG/TIFF/WebP
defusedxml>=0.7.1     # Safe XML parsing for XMP blocks
pytest>=7.0.0         # Testing
```

System dependencies (for video support):
- `ffmpeg` / `ffprobe`
- `mkvtoolnix` (optional, for MKV tag editing via `mkvpropedit`)

---

## Phases

| Phase | Scope | Deliverable |
|-------|-------|-------------|
| **1 — Core + PNG** | Data models, writer/reader core, PNG handler, tests | Working append/read for PNG files |
| **2 — Remaining images** | JPEG, TIFF, WebP handlers + tests | Full image format coverage |
| **3 — Video** | MP4/MOV/MKV handler via ffmpeg + tests | Full format coverage |
| **4 — CLI** | argparse-based CLI + integration tests | `metawriter` command available |
| **5 — Companion UI** | Desktop GUI (tkinter) for viewing, adding, editing, and removing metadata (not bound by core module's append-only constraint) | Standalone desktop application |

---

## Decisions (resolved)

1. **No in-place writes** — output a new copy; original is never touched. Overwrite mode deferred to future version.
2. **Duplicate keys** — resolved by #1. Running the tool on the same source is always safe since the original is untouched. Re-running on an already-processed copy appends new entries alongside existing ones.
3. **ffmpeg on system path** — accepted. Video support requires ffmpeg/ffprobe installed. Image support works independently.
4. **Desktop GUI** — companion UI will use tkinter for a native desktop application.
5. **`_mwrite` suffix** — all custom metadata keys end with `_mwrite` (e.g. `prompt_mwrite`, `model_mwrite`).
6. **Extension fields deferred** — version stamping, workflow attribution, and chain-of-custody are out of scope for v1. Will be added in a later phase.

## Open Questions

None — all resolved.

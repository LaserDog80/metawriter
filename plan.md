# MetaWriter — Implementation Plan

## Goal

Build an append-only metadata utility that writes AI-provenance entries (prompts, models, providers, source sites) to image and video files without modifying or removing any pre-existing metadata.

---

## Requirements

1. **Append metadata entries** to supported image formats: PNG, JPEG, TIFF, WebP.
2. **Append metadata entries** to supported video containers: MP4, MOV, MKV.
3. **Never overwrite, delete, or alter** existing metadata fields — additive only.
4. **Read existing metadata** before writing, to verify nothing is lost.
5. **Support structured provenance fields** at minimum: `prompt`, `model`, `provider`, `source_url`, and a `timestamp` (auto-generated on write).
6. **Allow arbitrary key-value text entries** beyond the built-in provenance fields.
7. **Validate inputs** — reject empty keys, non-text values, and unsupported file formats with clear errors.
8. **Expose a Python API** (importable module) as the primary interface.
9. **Provide a CLI wrapper** for scripting and one-off use.

---

## Inputs and Outputs

| Operation | Input | Output |
|-----------|-------|--------|
| Append metadata | File path + dict of key-value entries | Modified file (in-place) with new metadata appended |
| Read metadata | File path | Dict of all metadata entries currently stored |
| Verify integrity | File path | Boolean — confirms pre-existing metadata survived a write |

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

**Namespace convention:** All MetaWriter entries use the prefix `metawriter:` (e.g. `metawriter:prompt`, `metawriter:model`) to avoid collisions with existing metadata fields.

### File structure

```
metawriter/
├── src/
│   └── metawriter/
│       ├── __init__.py          # Public API surface
│       ├── writer.py            # Core MetadataWriter class (append + save)
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
  ├─ 3. Handler reads ALL existing metadata → snapshot
  ├─ 4. Validate new entries (non-empty keys, text values, no collisions with protected fields)
  ├─ 5. Merge: existing metadata + new entries (append, never replace)
  ├─ 6. Write merged metadata back to file
  └─ 7. Post-write verification: re-read and confirm snapshot fields still present
```

### Key design decisions

- **In-place writes** — modifies the original file. Users should keep backups or use version control on assets. We can optionally support a `backup=True` parameter that creates a `.bak` copy before writing.
- **Post-write verification** — after every write, re-read the file and assert that all previously-existing metadata keys are still present. Raise `MetadataIntegrityError` if anything is missing.
- **Duplicate keys** — if the user appends a key that already exists, we append a new entry with a numeric suffix (e.g. `metawriter:prompt`, `metawriter:prompt:2`) rather than overwriting. Formats that don't support duplicate keys use this suffixing strategy.
- **Video format dependency** — video support requires `ffmpeg` and optionally `mkvtoolnix` installed on the system. The module should raise a clear error if these are missing, and image support should work without them.

### Public API sketch

```python
from metawriter import append_metadata, read_metadata

# Append entries (core use case)
append_metadata("photo.png", {
    "prompt": "A sunset over mountains",
    "model": "DALL-E 3",
    "provider": "OpenAI",
    "source_url": "https://example.com/gallery",
})

# Read all metadata (including non-MetaWriter fields)
meta = read_metadata("photo.png")
# Returns: {"metawriter:prompt": "A sunset...", "exif:Make": "Canon", ...}
```

### CLI sketch

```bash
# Append metadata
metawriter append photo.png --prompt "A sunset" --model "DALL-E 3"

# Append arbitrary key-value
metawriter append photo.png --set key=value --set another=value2

# Read metadata
metawriter read photo.png

# Read only MetaWriter-namespaced entries
metawriter read photo.png --only-metawriter
```

---

## Test Cases

### Unit tests

1. **Append to empty file** — file with no metadata receives new entries correctly.
2. **Append preserves existing** — file with pre-existing EXIF/text chunks retains all original fields after append.
3. **Duplicate key handling** — appending the same key twice produces suffixed entries, not an overwrite.
4. **Validation rejects bad input** — empty key → `ValueError`; non-string value → `TypeError`; unsupported format → `UnsupportedFormatError`.
5. **Post-write integrity check** — simulated corruption triggers `MetadataIntegrityError`.
6. **Timestamp auto-populated** — every entry gets a `metawriter:timestamp` field with ISO-8601 time.

### Integration tests (per format)

7. **PNG round-trip** — write entries → read back → all entries present and correct.
8. **JPEG round-trip** — same, verifying XMP/EXIF survival.
9. **TIFF round-trip** — same.
10. **WebP round-trip** — same.
11. **MP4 round-trip** — same (requires ffmpeg in test environment).
12. **MOV round-trip** — same.
13. **MKV round-trip** — same.

### Edge cases

14. **Read-only file** — raises `PermissionError` with helpful message.
15. **File not found** — raises `FileNotFoundError`.
16. **Extension/content mismatch** — `.png` file that is actually a JPEG → detected via magic bytes, raises `FormatMismatchError`.
17. **Very large metadata value** — 10 KB text string as a value → handled gracefully per format limits.
18. **Unicode metadata** — non-ASCII characters in keys and values preserved correctly.
19. **Concurrent writes** — two processes appending to the same file → documented as unsupported (no file locking in v1).

### CLI tests

20. **`append` subcommand** — end-to-end: CLI writes entries, `read_metadata()` confirms them.
21. **`read` subcommand** — outputs JSON to stdout.
22. **Missing ffmpeg** — video operation without ffmpeg prints actionable error message.

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
| **5 — Companion UI** | Separate lightweight viewer/editor (not bound by append-only) | Standalone tool for metadata management |

---

## Open Questions

1. **Backup behavior** — should `append_metadata` create a `.bak` file by default, or only on opt-in? In-place writes are destructive if something goes wrong.
2. **Duplicate key strategy** — is numeric suffixing (`prompt:2`, `prompt:3`) acceptable, or would you prefer a different approach (e.g. JSON array values, or reject duplicate keys entirely)?
3. **Video system dependencies** — is requiring `ffmpeg` on the system path acceptable, or should we bundle/vendor a solution? This also affects CI/CD setup.
4. **Companion UI scope** — should the viewer be a terminal TUI (e.g. `textual`/`rich`), a desktop GUI (e.g. `tkinter`), or a local web app (e.g. Flask)? This affects the tech stack significantly.
5. **Namespace prefix** — is `metawriter:` the right prefix for our custom fields, or would you prefer something different (e.g. `ai:`, `provenance:`)?
6. **Extension fields** — for version stamping and chain-of-custody, should those be part of the core module from the start, or deferred to a later phase?

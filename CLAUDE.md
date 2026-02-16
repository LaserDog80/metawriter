# CLAUDE.md

> **Purpose:** Persistent instructions for Claude when working in this project.  
> **Rule:** Edit specific sections. Never rewrite this file entirely.

---

## Project Overview

MetaWriter — Preserve file identity through renames. Stamps filenames, download
timestamps, and AI-provenance metadata into media files in-place. Supports PNG,
JPEG, TIFF, WebP, MP4, MOV, MKV. Has both CLI and ttkbootstrap GUI.

---

## Tech Stack

- **Language:** Python 3.x
- **GUI:** ttkbootstrap + tkinterdnd2
- **Testing:** pytest
- **Package manager:** pip (use requirements.txt)

---

## Development Workflow

```bash
# 1. Create virtual environment (first time only)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests
pytest

# 4. Run the GUI
PYTHONPATH=src python -m metawriter gui

# 5. Before committing
pytest && git add -A && git commit -m "message"
```

---

## Code Standards

- Use type hints for function signatures
- Docstrings for public functions
- Keep functions under 30 lines where possible
- Prefer explicit over clever

---

## File Structure Conventions

```
src/metawriter/
├── __init__.py       # Public API exports
├── __main__.py       # python -m metawriter entry point
├── engine.py         # Core tag_file() / tag_files() logic
├── scanner.py        # File discovery (scan_paths)
├── birthtime.py      # Filesystem creation date utility
├── reader.py         # Read metadata from files
├── writer.py         # Legacy append_metadata (copy-based)
├── models.py         # MetadataEntry, validation
├── exceptions.py     # Error hierarchy
├── xmp.py            # Shared XMP build/parse utilities
├── cli.py            # CLI (tag/read/gui subcommands)
├── gui.py            # ttkbootstrap GUI application
└── formats/          # Per-format handlers (png, jpeg, tiff, webp, video)
```

---

## Known Issues & Workarounds

<!-- Append new issues here as they're discovered -->

- None yet

---

## Do NOT Do

<!-- Append items here when Claude makes mistakes -->

- Do not rewrite CLAUDE.md or LEARNINGS.md entirely—edit sections only
- Do not delete test files without explicit approval
- Do not change the directory structure without discussing first

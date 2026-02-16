# Unified MetaWriter: Reshape into GUI-Driven File Tagging Tool

## Context

The tool's core purpose is **preserving file identity through renames** — when you download an AI-generated image and rename it, the original filename, download timestamp, and provenance info (model, source URL, prompt) should survive in the file's metadata forever.

Currently, two separate modules exist doing overlapping work:
- `nametag` — stamps filenames in-place (simple, works)
- `metawriter` — appends AI metadata as new copies (more features, wrong workflow)

These need to merge into **one unified in-place tool with a ttkbootstrap GUI**.

---

## What the Tool Does (After Reshape)

**Always automatic:**
- `previous_name_mwrite` = current filename at time of tagging
- `download_timestamp_mwrite` = file's filesystem creation date (birthtime)
- `timestamp_mwrite` = when the tagging happened

**Optional (user fills in):**
- `model_mwrite` — e.g. "DALL-E 3", "Midjourney v6"
- `source_url_mwrite` — e.g. "https://chatgpt.com/..."
- `prompt_mwrite` — the AI prompt used

**All in-place** — original file is modified, no copies produced.

---

## Implementation Phases

### Phase 1: Extract Shared XMP Utilities
Eliminate ~100 lines of duplication between the two modules.

- **Create** `src/metawriter/xmp.py` — move `build_xmp()`, `parse_xmp()`, escaping/sanitizing from `src/nametag/xmp.py`
- **Update** `src/metawriter/formats/jpeg.py` — import from `metawriter.xmp` instead of defining its own `_build_xmp`/`_parse_xmp`
- **Update** `src/metawriter/formats/tiff.py` and `webp.py` — import from `metawriter.xmp` instead of `from .jpeg`
- **Add** `tests/test_xmp.py`
- Run tests — all 154 must still pass.

### Phase 2: Add In-Place Writing to Handlers
Extend the handler base class so every format can write in-place.

- **Edit** `src/metawriter/formats/base.py` — add `write_metadata_inplace()`:
  ```python
  def write_metadata_inplace(self, path, metadata):
      tmp = path.with_name(path.stem + "_mwrite_tmp" + path.suffix)
      try:
          self.write_metadata(path, tmp, metadata)
          tmp.replace(path)
      except Exception:
          if tmp.exists(): tmp.unlink()
          raise
  ```
- This reuses existing `write_metadata()` — no per-handler changes needed.
- Add in-place round-trip tests for each format.

### Phase 3: Build Unified Engine
Replace both `stamp_previous_name()` and `append_metadata()` with one function.

- **Create** `src/metawriter/birthtime.py` — `get_birthtime(path) -> str` using `os.stat().st_birthtime` on macOS
- **Create** `src/metawriter/scanner.py` — `scan_paths(paths, recursive) -> list[Path]` walking folder trees for supported extensions (png, jpg, jpeg, tiff, tif, webp, mp4, mov, mkv)
- **Create** `src/metawriter/engine.py` — core `tag_file()` function:
  1. Get handler, read existing metadata
  2. Build metadata dict (filename + birthtime + timestamp + optional fields)
  3. Merge with existing (preserves old optional values unless user provides new ones)
  4. `handler.write_metadata_inplace(path, merged)`
- **Create** `tag_files()` — batch wrapper with progress/error callbacks (used by CLI and GUI)
- **Update** `src/metawriter/__init__.py` — export `tag_file`, `tag_files`, `read_metadata`, `scan_paths`
- **Add** `tests/test_engine.py`, `tests/test_scanner.py`, `tests/test_birthtime.py`

### Phase 4: Rewrite CLI
Single `metawriter` command with three subcommands.

```bash
metawriter tag photo.jpg                          # auto-stamp filename + birthtime
metawriter tag photo.jpg --model "DALL-E 3"       # + optional fields
metawriter tag ./folder/ --recursive              # batch process a folder tree
metawriter read photo.jpg [--only-mwrite]         # read metadata as JSON
metawriter gui                                    # launch the GUI
```

- **Rewrite** `src/metawriter/cli.py`
- **Rewrite** `tests/test_cli.py`
- **Create/update** `src/metawriter/__main__.py`

### Phase 5: Build GUI
ttkbootstrap desktop app with drag-and-drop.

- **Create** `src/metawriter/gui.py`
- **Add** `ttkbootstrap>=1.10.0` and `tkinterdnd2>=0.3.0` to `requirements.txt`

**Layout (top to bottom):**
1. **Drop zone + Browse button** — drag files/folders or click to pick. Checkbox for "Include subfolders"
2. **File list** — treeview with columns: filename, path, status. Click a row to preview existing metadata
3. **Metadata fields** — Model (text), Source URL (text), Prompt (multiline). All optional
4. **Action bar** — "Tag" button, progress bar, status label

**Technical notes:**
- Root window: `TkinterDnD.Tk` with ttkbootstrap `Style` applied (avoids inheritance conflict)
- Processing runs in a `threading.Thread`, updates GUI via `root.after()`
- Callbacks from `tag_files()` update each file's status in the treeview

### Phase 6: Delete Nametag & Consolidate
- **Delete** `src/nametag/` entirely
- **Delete** `tests/test_nametag/` entirely
- **Delete** `tests/test_writer.py` (replaced by `test_engine.py`)
- Migrate key nametag test cases (overwrite, unicode, special chars, no temp file left behind) into `tests/test_engine.py`
- **Update** `README.md`, `CLAUDE.md`

---

## Metadata Merge Rules (Re-tagging)

| Key | On re-tag |
|-----|-----------|
| `previous_name_mwrite` | Always overwritten (current filename) |
| `download_timestamp_mwrite` | Preserved if exists, set from birthtime if missing |
| `timestamp_mwrite` | Always overwritten (current time) |
| `model_mwrite` | Preserved unless user provides new value |
| `source_url_mwrite` | Preserved unless user provides new value |
| `prompt_mwrite` | Preserved unless user provides new value |

---

## Key Files (modify/create)

| Action | File |
|--------|------|
| Create | `src/metawriter/xmp.py` |
| Create | `src/metawriter/engine.py` |
| Create | `src/metawriter/scanner.py` |
| Create | `src/metawriter/birthtime.py` |
| Create | `src/metawriter/gui.py` |
| Create | `src/metawriter/__main__.py` |
| Modify | `src/metawriter/formats/base.py` (add `write_metadata_inplace`) |
| Modify | `src/metawriter/formats/jpeg.py` (use shared xmp) |
| Modify | `src/metawriter/formats/tiff.py` (use shared xmp) |
| Modify | `src/metawriter/formats/webp.py` (use shared xmp) |
| Rewrite | `src/metawriter/cli.py` |
| Rewrite | `src/metawriter/__init__.py` |
| Delete | `src/nametag/` (entire directory) |
| Delete | `tests/test_nametag/` (entire directory) |
| Delete | `tests/test_writer.py` |

---

## Verification

After each phase, run `pytest` to confirm no regressions. After Phase 5:
1. `metawriter tag /path/to/image.png` — verify metadata stamped with `metawriter read`
2. `metawriter tag /path/to/folder/ --recursive` — verify all supported files tagged
3. `metawriter gui` — launch GUI, drag files, fill optional fields, click Tag, verify results
4. Full `pytest` suite passes

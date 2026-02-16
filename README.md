# MetaWriter

Preserve file identity through renames. Stamps filenames, download timestamps, and AI-provenance metadata into media files so the information survives no matter how many times you rename them.

## Quick Start

```bash
# Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Tag a file (stamps filename + download timestamp automatically)
python -m metawriter tag photo.png

# Tag with optional provenance info
python -m metawriter tag photo.png --model "DALL-E 3" --source-url "https://chatgpt.com" --prompt "a sunset"

# Tag an entire folder
python -m metawriter tag ./downloads/ --recursive

# Read metadata back
python -m metawriter read photo.png --only-mwrite

# Launch the GUI
python -m metawriter gui
```

## What Gets Stamped

**Always automatic:**
- `previous_name_mwrite` — current filename at time of tagging
- `download_timestamp_mwrite` — file's filesystem creation date
- `timestamp_mwrite` — when the tagging happened

**Optional (you provide):**
- `model_mwrite` — AI model name (e.g. "DALL-E 3", "Midjourney v6")
- `source_url_mwrite` — where the file was downloaded from
- `prompt_mwrite` — the AI prompt used to generate it

## Supported Formats

PNG, JPEG, TIFF, WebP, MP4, MOV, MKV

Video formats require `ffmpeg` and `ffprobe` on your PATH.

## Development

```bash
pytest  # Run tests
```

See `CLAUDE.md` for development conventions.

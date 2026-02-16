"""Cross-platform filesystem birthtime (creation date) utility."""

import platform
from datetime import datetime, timezone
from pathlib import Path


def get_birthtime(path: Path) -> str:
    """Return the filesystem creation time as an ISO-8601 UTC string.

    Args:
        path: Path to the file.

    Returns:
        ISO-8601 formatted timestamp string.
    """
    stat = path.stat()
    system = platform.system()
    if system == "Darwin":
        ts = stat.st_birthtime
    elif system == "Windows":
        ts = stat.st_ctime  # On Windows, st_ctime is creation time
    else:
        # Linux: st_ctime is metadata change time, not creation.
        # Use st_birthtime if available (Python 3.12+ on some systems),
        # otherwise fall back to st_mtime.
        ts = getattr(stat, "st_birthtime", stat.st_mtime)
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

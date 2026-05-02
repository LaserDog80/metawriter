"""ComfyUI custom node package for MetaWriter.

Drop this folder (or symlink the parent project) into ``ComfyUI/custom_nodes/``
and ComfyUI will pick up the nodes via ``NODE_CLASS_MAPPINGS``.

The metawriter package itself lives in ``../src/metawriter`` in the source
repo. This file ensures it is importable regardless of how the folder is
deployed.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# Locate the metawriter package. Two supported layouts:
#   1. Dev / repo:  <project>/src/metawriter      (sibling of this folder's parent)
#   2. Bundled:     <this folder>/_vendor/metawriter
for _candidate in (_HERE.parent / "src", _HERE / "_vendor"):
    if (_candidate / "metawriter" / "__init__.py").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS  # noqa: E402

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

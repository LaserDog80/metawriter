"""ComfyUI custom nodes for MetaWriter."""

from __future__ import annotations

import logging
from pathlib import Path

# These imports only resolve when this module is loaded inside ComfyUI.
# We tolerate ImportError so the module can still be imported for
# unit-testing the pure helpers.
try:
    import folder_paths  # type: ignore[import-not-found]
    from nodes import SaveImage  # type: ignore[import-not-found]

    _COMFY_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only outside ComfyUI
    folder_paths = None  # type: ignore[assignment]
    SaveImage = object  # type: ignore[assignment,misc]
    _COMFY_AVAILABLE = False

from metawriter import tag_file

LOGGER = logging.getLogger(__name__)


def _parse_extras(text: str) -> dict[str, str]:
    """Parse a multiline ``key=value`` string into a dict.

    Skips blank lines and lines starting with ``#``. Malformed lines
    (no ``=``, empty key) are dropped with a warning so the workflow
    keeps running rather than aborting on a typo.
    """
    result: dict[str, str] = {}
    if not text:
        return result
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            LOGGER.warning("MetaWriter: skipping extras line (no '='): %r", line)
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            LOGGER.warning("MetaWriter: skipping extras line with empty key: %r", line)
            continue
        result[key] = value
    return result


# Common image-input field names on ComfyUI nodes; we follow these upstream
# while looking for a LoadImage source.
_IMAGE_INPUT_KEYS = ("images", "image", "pixels")


def _trace_source_filename(
    workflow: dict, start_node_id: str, max_hops: int = 8
) -> str | None:
    """Walk upstream from ``start_node_id`` looking for a ``LoadImage`` source.

    Follows the first IMAGE-shaped input on each node (``images`` / ``image``
    / ``pixels``). If a ``LoadImage`` is reached within ``max_hops``, returns
    its widget value (the source filename). Otherwise returns ``None``.

    The workflow dict is the value ComfyUI passes as its hidden ``prompt``
    input — a flat ``{node_id: {class_type, inputs, ...}}`` map.
    """
    seen: set[str] = set()
    current = str(start_node_id)
    for _ in range(max_hops):
        if current in seen:
            return None  # cycle guard
        seen.add(current)
        node = workflow.get(current)
        if not isinstance(node, dict):
            return None
        if node.get("class_type") == "LoadImage":
            value = node.get("inputs", {}).get("image")
            return value if isinstance(value, str) else None
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            return None
        upstream: str | None = None
        for key in _IMAGE_INPUT_KEYS:
            ref = inputs.get(key)
            # IMAGE links are encoded as [upstream_node_id, output_index]
            if isinstance(ref, list) and len(ref) >= 1:
                upstream = str(ref[0])
                break
        if upstream is None:
            return None
        current = upstream
    return None


class MetaWriterSaveImage(SaveImage):  # type: ignore[misc]
    """Save an image and stamp MetaWriter metadata into it.

    Behaves identically to the stock ``SaveImage`` node (including embedding
    the workflow JSON via ComfyUI's hidden ``prompt`` / ``extra_pnginfo``
    inputs), then tags each saved file in place with any user-supplied
    fields. Empty fields are skipped — only populated metadata is written.

    The ``mw_`` prefix on widget names is required so they do not collide
    with ComfyUI's hidden ``prompt`` kwarg (which carries the workflow JSON).
    """

    CATEGORY = "MetaWriter"

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802 - ComfyUI naming convention
        base = super().INPUT_TYPES()
        # Request our own node id so we can locate ourselves in the workflow
        # graph (delivered via the existing hidden `prompt` input) and trace
        # back to a LoadImage source filename.
        base.setdefault("hidden", {})
        base["hidden"].setdefault("unique_id", "UNIQUE_ID")
        base.setdefault("required", {})
        base["required"]["mw_model"] = (
            "STRING",
            {"default": "", "placeholder": "e.g. flux-dev, sdxl-1.0"},
        )
        base["required"]["mw_prompt"] = (
            "STRING",
            {"default": "", "multiline": True, "placeholder": "Prompt used to generate the image"},
        )
        base["required"]["mw_platform"] = (
            "STRING",
            {"default": "", "placeholder": "e.g. ComfyUI, Midjourney, local"},
        )
        base["required"]["mw_extras"] = (
            "STRING",
            {
                "default": "",
                "multiline": True,
                "placeholder": "Extra fields, one per line:\nkey=value\nseed=12345",
            },
        )
        return base

    def save_images(self, images, **kwargs):
        # Pull out our fields before delegating; everything else (filename_prefix,
        # the hidden prompt + extra_pnginfo) flows through to stock SaveImage.
        mw_model = kwargs.pop("mw_model", "") or ""
        mw_prompt = kwargs.pop("mw_prompt", "") or ""
        mw_platform = kwargs.pop("mw_platform", "") or ""
        mw_extras = kwargs.pop("mw_extras", "") or ""

        # `unique_id` is ours alone — strip it before super() so SaveImage
        # doesn't choke on the unexpected kwarg. `prompt` (the workflow graph)
        # we leave intact: super needs it to embed the workflow JSON.
        unique_id = kwargs.pop("unique_id", None)
        workflow = kwargs.get("prompt")  # the flat node-id dict

        result = super().save_images(images, **kwargs)

        if not _COMFY_AVAILABLE or folder_paths is None:
            return result  # pragma: no cover

        ui_images = []
        if isinstance(result, dict):
            ui_images = result.get("ui", {}).get("images", []) or []

        model = mw_model.strip() or None
        prompt_text = mw_prompt.strip() or None
        platform = mw_platform.strip()

        extras = _parse_extras(mw_extras)
        if platform:
            extras.setdefault("platform", platform)

        # Attempt to recover the source filename if this image was loaded
        # from disk via LoadImage. Without this we would only record the
        # newly-generated ComfyUI filename, losing the file's prior identity.
        if unique_id is not None and isinstance(workflow, dict):
            self_node = workflow.get(str(unique_id))
            if isinstance(self_node, dict):
                self_inputs = self_node.get("inputs", {})
                ref = self_inputs.get("images") if isinstance(self_inputs, dict) else None
                if isinstance(ref, list) and ref:
                    source_name = _trace_source_filename(workflow, str(ref[0]))
                    if source_name:
                        extras.setdefault("source_filename", source_name)

        # self.output_dir is set by SaveImage.__init__; honour it so this node
        # remains correct if someone ever subclasses it the way PreviewImage does.
        output_dir = Path(getattr(self, "output_dir", folder_paths.get_output_directory()))
        for entry in ui_images:
            filename = entry.get("filename") if isinstance(entry, dict) else None
            if not filename:
                continue
            subfolder = entry.get("subfolder", "") or ""
            file_path = output_dir / subfolder / filename
            try:
                tag_file(
                    file_path,
                    model=model,
                    prompt=prompt_text,
                    extra=extras or None,
                )
            except Exception as exc:  # noqa: BLE001 - never crash the workflow
                LOGGER.warning("MetaWriter: failed to tag %s: %s", file_path, exc)

        return result


NODE_CLASS_MAPPINGS = {
    "MetaWriterSaveImage": MetaWriterSaveImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MetaWriterSaveImage": "MetaWriter Save Image",
}

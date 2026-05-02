"""Tests for the ComfyUI node's extras-string parser.

The full node depends on ComfyUI, but ``_parse_extras`` is pure Python
and worth covering since it's the only place we accept free-form user
input on the node.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the comfyui_metawriter folder importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comfyui_metawriter.nodes import _parse_extras, _trace_source_filename  # noqa: E402


def test_parses_simple_lines():
    out = _parse_extras("seed=12345\nsteps=20")
    assert out == {"seed": "12345", "steps": "20"}


def test_strips_whitespace_around_key_and_value():
    out = _parse_extras("  seed   =   12345  ")
    assert out == {"seed": "12345"}


def test_skips_blank_lines_and_comments():
    text = "\n# a comment\nseed=1\n\n  # indented comment\nsteps=2\n"
    assert _parse_extras(text) == {"seed": "1", "steps": "2"}


def test_skips_lines_without_equals():
    out = _parse_extras("seed=1\nthis is malformed\nsteps=2")
    assert out == {"seed": "1", "steps": "2"}


def test_skips_lines_with_empty_key():
    out = _parse_extras("=novalue\nseed=1")
    assert out == {"seed": "1"}


def test_value_can_contain_equals_signs():
    # Only the first '=' splits; the rest of the value is preserved.
    out = _parse_extras("equation=a=b+c")
    assert out == {"equation": "a=b+c"}


def test_empty_value_is_allowed():
    assert _parse_extras("note=") == {"note": ""}


def test_empty_input_returns_empty_dict():
    assert _parse_extras("") == {}
    assert _parse_extras("   \n\n   ") == {}


def test_later_duplicate_key_wins():
    assert _parse_extras("k=1\nk=2") == {"k": "2"}


# ---------------------------------------------------------------------------
# _trace_source_filename — walks the ComfyUI workflow graph upstream
# ---------------------------------------------------------------------------


def test_trace_finds_loadimage_directly_upstream():
    workflow = {
        "30": {"class_type": "LoadImage", "inputs": {"image": "Grungy Philosopher.jpeg"}},
        "31": {"class_type": "MetaWriterSaveImage", "inputs": {"images": ["30", 0]}},
    }
    assert _trace_source_filename(workflow, "30") == "Grungy Philosopher.jpeg"


def test_trace_walks_through_passthrough_node():
    workflow = {
        "10": {"class_type": "LoadImage", "inputs": {"image": "src.png"}},
        "11": {"class_type": "ImageScale", "inputs": {"image": ["10", 0], "scale_by": 2.0}},
        "12": {"class_type": "MetaWriterSaveImage", "inputs": {"images": ["11", 0]}},
    }
    assert _trace_source_filename(workflow, "11") == "src.png"


def test_trace_returns_none_for_pure_generation():
    # KSampler output → VAEDecode → MetaWriterSave; no LoadImage in lineage
    workflow = {
        "1": {"class_type": "KSampler", "inputs": {"seed": 42}},
        "2": {"class_type": "VAEDecode", "inputs": {"samples": ["1", 0]}},
        "3": {"class_type": "MetaWriterSaveImage", "inputs": {"images": ["2", 0]}},
    }
    assert _trace_source_filename(workflow, "2") is None


def test_trace_returns_none_when_node_missing():
    assert _trace_source_filename({}, "99") is None


def test_trace_handles_cycles():
    # Pathological self-loop — must not infinite-loop
    workflow = {
        "1": {"class_type": "Frob", "inputs": {"image": ["1", 0]}},
    }
    assert _trace_source_filename(workflow, "1") is None


def test_trace_respects_max_hops():
    # Build a long chain with no LoadImage
    chain = {
        str(i): {"class_type": "Passthrough", "inputs": {"image": [str(i + 1), 0]}}
        for i in range(20)
    }
    chain["20"] = {"class_type": "Sampler", "inputs": {}}
    assert _trace_source_filename(chain, "0", max_hops=5) is None


def test_trace_loadimage_with_non_string_value_returns_none():
    # Defensive: malformed workflow shouldn't crash the save
    workflow = {"5": {"class_type": "LoadImage", "inputs": {"image": 12345}}}
    assert _trace_source_filename(workflow, "5") is None

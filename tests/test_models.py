"""Tests for metawriter.models — validation and data model logic."""

from datetime import datetime, timezone

import pytest

from metawriter.models import (
    MWRITE_SUFFIX,
    PROVENANCE_FIELDS,
    MetadataEntry,
    entries_to_dict,
    validate_entries,
)


# ---------------------------------------------------------------------------
# MetadataEntry dataclass
# ---------------------------------------------------------------------------

class TestMetadataEntry:
    """Tests for the MetadataEntry dataclass."""

    def test_entry_stores_key_value(self) -> None:
        entry = MetadataEntry(key="prompt_mwrite", value="a sunset")
        assert entry.key == "prompt_mwrite"
        assert entry.value == "a sunset"

    def test_entry_is_frozen(self) -> None:
        entry = MetadataEntry(key="k", value="v")
        with pytest.raises(AttributeError):
            entry.key = "other"  # type: ignore[misc]

    def test_entry_auto_generates_timestamp(self) -> None:
        before = datetime.now(timezone.utc).isoformat()
        entry = MetadataEntry(key="k", value="v")
        after = datetime.now(timezone.utc).isoformat()
        assert before <= entry.timestamp <= after


# ---------------------------------------------------------------------------
# validate_entries()
# ---------------------------------------------------------------------------

class TestValidateEntries:
    """Tests for validate_entries()."""

    def test_valid_entries_returns_list(self) -> None:
        result = validate_entries({"prompt": "test", "model": "dall-e"})
        assert isinstance(result, list)
        assert len(result) == 2

    def test_suffix_appended_to_keys(self) -> None:
        result = validate_entries({"prompt": "test"})
        assert result[0].key == "prompt_mwrite"

    def test_suffix_not_doubled(self) -> None:
        result = validate_entries({"prompt_mwrite": "test"})
        assert result[0].key == "prompt_mwrite"

    def test_empty_key_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_entries({"": "value"})

    def test_whitespace_only_key_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_entries({"   ": "value"})

    def test_non_string_key_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="key must be a string"):
            validate_entries({123: "value"})  # type: ignore[dict-item]

    def test_non_string_value_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="value.*must be a string"):
            validate_entries({"prompt": 42})  # type: ignore[dict-item]

    def test_non_dict_entries_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="entries must be a dict"):
            validate_entries([("prompt", "test")])  # type: ignore[arg-type]

    def test_entries_share_same_timestamp(self) -> None:
        result = validate_entries({"a": "1", "b": "2", "c": "3"})
        timestamps = {e.timestamp for e in result}
        assert len(timestamps) == 1

    def test_empty_dict_returns_empty_list(self) -> None:
        result = validate_entries({})
        assert result == []

    def test_arbitrary_keys_are_accepted(self) -> None:
        result = validate_entries({"custom_field": "value"})
        assert result[0].key == "custom_field_mwrite"

    def test_provenance_fields_all_accepted(self) -> None:
        entries = {field: f"val_{field}" for field in PROVENANCE_FIELDS}
        result = validate_entries(entries)
        assert len(result) == len(PROVENANCE_FIELDS)
        for entry in result:
            assert entry.key.endswith(MWRITE_SUFFIX)


# ---------------------------------------------------------------------------
# entries_to_dict()
# ---------------------------------------------------------------------------

class TestEntriesToDict:
    """Tests for entries_to_dict()."""

    def test_converts_entries_to_flat_dict(self) -> None:
        entries = validate_entries({"prompt": "sunset"})
        d = entries_to_dict(entries)
        assert "prompt_mwrite" in d
        assert d["prompt_mwrite"] == "sunset"

    def test_includes_timestamp_key(self) -> None:
        entries = validate_entries({"prompt": "sunset"})
        d = entries_to_dict(entries)
        assert "timestamp_mwrite" in d
        # Validate ISO-8601 format
        datetime.fromisoformat(d["timestamp_mwrite"])

    def test_empty_entries_returns_empty_dict(self) -> None:
        d = entries_to_dict([])
        assert d == {}

    def test_multiple_entries_all_present(self) -> None:
        entries = validate_entries({"a": "1", "b": "2"})
        d = entries_to_dict(entries)
        assert d["a_mwrite"] == "1"
        assert d["b_mwrite"] == "2"
        assert "timestamp_mwrite" in d

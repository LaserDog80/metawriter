"""Data models and validation logic for MetaWriter metadata entries."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


# Built-in provenance field names (before _mwrite suffix is applied).
PROVENANCE_FIELDS: tuple[str, ...] = (
    "prompt",
    "model",
    "provider",
    "source_url",
)

MWRITE_SUFFIX: str = "_mwrite"


@dataclass(frozen=True)
class MetadataEntry:
    """A single validated metadata key-value pair.

    Keys are stored *with* the ``_mwrite`` suffix already applied.
    """

    key: str
    value: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def validate_entries(entries: dict[str, str]) -> list[MetadataEntry]:
    """Validate a user-supplied dict and return a list of MetadataEntry objects.

    Validation rules:
    - Keys must be non-empty strings.
    - Values must be strings (non-empty).
    - The ``_mwrite`` suffix is appended to every key automatically.

    Args:
        entries: Mapping of field names to text values.

    Returns:
        List of validated MetadataEntry instances with suffixed keys.

    Raises:
        ValueError: If a key is empty.
        TypeError: If a key or value is not a string.
    """
    if not isinstance(entries, dict):
        raise TypeError(f"entries must be a dict, got {type(entries).__name__}")

    results: list[MetadataEntry] = []
    ts = datetime.now(timezone.utc).isoformat()

    for key, value in entries.items():
        if not isinstance(key, str):
            raise TypeError(f"Metadata key must be a string, got {type(key).__name__}")
        if not isinstance(value, str):
            raise TypeError(
                f"Metadata value for key '{key}' must be a string, "
                f"got {type(value).__name__}"
            )
        if not key.strip():
            raise ValueError("Metadata key must not be empty or whitespace-only")

        suffixed_key = key if key.endswith(MWRITE_SUFFIX) else f"{key}{MWRITE_SUFFIX}"
        results.append(MetadataEntry(key=suffixed_key, value=value, timestamp=ts))

    return results


def entries_to_dict(entries: list[MetadataEntry]) -> dict[str, str]:
    """Convert a list of MetadataEntry objects to a flat dict for writing.

    The timestamp is stored under a dedicated ``timestamp_mwrite`` key.
    """
    result: dict[str, str] = {}
    for entry in entries:
        result[entry.key] = entry.value
    if entries:
        result["timestamp_mwrite"] = entries[0].timestamp
    return result

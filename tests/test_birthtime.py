"""Tests for the birthtime utility."""

from datetime import datetime, timezone
from pathlib import Path

from metawriter.birthtime import get_birthtime


class TestGetBirthtime:
    """Tests for filesystem birthtime extraction."""

    def test_returns_iso_string(self, sample_png: Path) -> None:
        result = get_birthtime(sample_png)
        # Should be a valid ISO-8601 string
        dt = datetime.fromisoformat(result)
        assert dt.tzinfo is not None

    def test_timestamp_is_in_the_past(self, sample_png: Path) -> None:
        result = get_birthtime(sample_png)
        dt = datetime.fromisoformat(result)
        assert dt <= datetime.now(timezone.utc)

    def test_returns_string(self, sample_png: Path) -> None:
        result = get_birthtime(sample_png)
        assert isinstance(result, str)

"""Unit tests for birthday service."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jeff.services.birthday import (
    BIRTHDAY_MESSAGE,
    find_birthdays,
    record_birthday_exchange,
)


def _make_contact(tmp_path: Path, slug: str, birthday: str) -> None:
    """Write a minimal contact .md with a birthday."""
    (tmp_path / f"{slug}.md").write_text(
        f"---\nname: {slug}\nslug: {slug}\nbirthday: {birthday}\n---\n",
        encoding="utf-8",
    )


class TestFindBirthdays:
    """Tests for birthday detection."""

    def test_finds_today(self, tmp_path: Path) -> None:
        """Finds contacts whose birthday is today."""
        today = date.today()
        bday = f"1985-{today.month:02d}-{today.day:02d}"
        _make_contact(tmp_path, "jean", bday)
        _make_contact(tmp_path, "marie", "1990-01-01")
        result = find_birthdays(tmp_path)
        assert len(result) == 1
        assert result[0]["slug"] == "jean"

    def test_finds_target_date(self, tmp_path: Path) -> None:
        """Finds contacts for a specific date."""
        _make_contact(tmp_path, "jean", "1985-03-15")
        result = find_birthdays(tmp_path, target_date=date(2026, 3, 15))
        assert len(result) == 1

    def test_no_match(self, tmp_path: Path) -> None:
        """Returns empty when no birthdays match."""
        _make_contact(tmp_path, "jean", "1985-12-25")
        result = find_birthdays(tmp_path, target_date=date(2026, 6, 1))
        assert result == []

    def test_empty_dir(self, tmp_path: Path) -> None:
        """Returns empty for nonexistent dir."""
        result = find_birthdays(tmp_path / "nope")
        assert result == []


class TestRecordBirthdayExchange:
    """Tests for birthday exchange recording."""

    def test_records_exchange(self, tmp_path: Path) -> None:
        """Writes an exchange line in the frontmatter."""
        _make_contact(tmp_path, "jean", "1985-03-15")
        from jeff.services.triage import load_contact

        data = load_contact(tmp_path / "jean.md")
        assert data is not None
        result = record_birthday_exchange(data, target_date=date(2026, 3, 15))
        assert result is True
        text = (tmp_path / "jean.md").read_text()
        assert "2026-03-15" in text

    def test_idempotent(self, tmp_path: Path) -> None:
        """Does not record twice for the same date."""
        _make_contact(tmp_path, "jean", "1985-03-15")
        from jeff.services.triage import load_contact

        data = load_contact(tmp_path / "jean.md")
        assert data is not None
        record_birthday_exchange(data, target_date=date(2026, 3, 15))
        result = record_birthday_exchange(data, target_date=date(2026, 3, 15))
        assert result is False

    def test_message_defined(self) -> None:
        """Birthday message is a non-empty string."""
        assert len(BIRTHDAY_MESSAGE) > 10

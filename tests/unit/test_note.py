"""Unit tests for note/interaction service."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jeff.services.note import (
    INTERACTION_TYPES,
    create_interaction,
    find_contact_dir,
    list_interactions,
)


def _make_contact_dir(tmp_path: Path, slug: str, name: str) -> Path:
    """Create a contact directory with a .md file."""
    d = tmp_path / slug
    d.mkdir()
    (d / f"{slug}.md").write_text(
        f"---\nname: {name}\nslug: {slug}\n---\n",
        encoding="utf-8",
    )
    return d


class TestFindContactDir:
    """Tests for contact directory lookup."""

    def test_finds_by_slug(self, tmp_path: Path) -> None:
        """Finds contact by slug substring."""
        _make_contact_dir(tmp_path, "antoine-martin", "Antoine Martin")
        result = find_contact_dir(tmp_path, "antoine")
        assert result is not None
        assert result.name == "antoine-martin"

    def test_finds_by_name(self, tmp_path: Path) -> None:
        """Finds contact by name substring."""
        _make_contact_dir(tmp_path, "antoine-martin", "Antoine Martin")
        result = find_contact_dir(tmp_path, "martin")
        assert result is not None

    def test_not_found(self, tmp_path: Path) -> None:
        """Returns None when no match."""
        _make_contact_dir(tmp_path, "jean", "Jean")
        assert find_contact_dir(tmp_path, "xyz") is None


class TestCreateInteraction:
    """Tests for interaction file creation."""

    def test_creates_file(self, tmp_path: Path) -> None:
        """Creates a dated .md file."""
        d = _make_contact_dir(tmp_path, "jean", "Jean")
        path = create_interaction(d, "whatsapp", "Hello", date(2025, 5, 6))
        assert path.exists()
        assert path.name == "2025-05-06.md"
        text = path.read_text()
        assert "type: whatsapp" in text
        assert "Hello" in text

    def test_handles_duplicate_date(self, tmp_path: Path) -> None:
        """Creates numbered file on same date."""
        d = _make_contact_dir(tmp_path, "jean", "Jean")
        create_interaction(d, "tel", "First", date(2025, 5, 6))
        path2 = create_interaction(d, "mail", "Second", date(2025, 5, 6))
        assert path2.name == "2025-05-06-2.md"

    def test_default_today(self, tmp_path: Path) -> None:
        """Uses today's date by default."""
        d = _make_contact_dir(tmp_path, "jean", "Jean")
        path = create_interaction(d, "note", "A note")
        assert date.today().isoformat() in path.name


class TestListInteractions:
    """Tests for interaction listing."""

    def test_lists_interactions(self, tmp_path: Path) -> None:
        """Lists interaction files, newest first."""
        d = _make_contact_dir(tmp_path, "jean", "Jean")
        create_interaction(d, "tel", "Old", date(2025, 1, 1))
        create_interaction(d, "whatsapp", "New", date(2025, 5, 6))
        interactions = list_interactions(d)
        assert len(interactions) == 2
        assert str(interactions[0].get("date")) == "2025-05-06"

    def test_empty(self, tmp_path: Path) -> None:
        """Returns empty for contact with no interactions."""
        d = _make_contact_dir(tmp_path, "jean", "Jean")
        assert list_interactions(d) == []


class TestInteractionTypes:
    """Tests for type mapping."""

    def test_types_defined(self) -> None:
        """All expected types exist."""
        assert "w" in INTERACTION_TYPES
        assert "t" in INTERACTION_TYPES
        assert "m" in INTERACTION_TYPES
        assert "v" in INTERACTION_TYPES
        assert "n" in INTERACTION_TYPES

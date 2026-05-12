"""Unit tests for duplicate detection service."""

from __future__ import annotations

import time
from pathlib import Path

from jeff.services.duplicates import find_duplicates, remove_duplicate


def _make_contact(tmp_path: Path, filename: str, uid: str, name: str) -> Path:
    """Write a minimal contact .md file in folder layout."""
    slug = filename.replace(".md", "")
    slug_dir = tmp_path / slug
    slug_dir.mkdir(exist_ok=True)
    md = slug_dir / filename
    md.write_text(
        f"---\nuid: {uid}\nname: {name}\nslug: {slug}\n---\n",
        encoding="utf-8",
    )
    return md


class TestFindDuplicates:
    """Tests for duplicate UID detection."""

    def test_no_duplicates(self, tmp_path: Path) -> None:
        """No duplicates when UIDs are unique."""
        _make_contact(tmp_path, "jean.md", "uid-1", "Jean")
        _make_contact(tmp_path, "marie.md", "uid-2", "Marie")
        assert find_duplicates(tmp_path) == []

    def test_finds_duplicate(self, tmp_path: Path) -> None:
        """Detects two files with same UID."""
        _make_contact(tmp_path, "jean-old.md", "uid-1", "Jean Old")
        time.sleep(0.05)
        _make_contact(tmp_path, "jean-new.md", "uid-1", "Jean New")
        dupes = find_duplicates(tmp_path)
        assert len(dupes) == 1
        assert dupes[0].uid == "uid-1"
        assert dupes[0].recommended.get("name") == "Jean New"
        assert len(dupes[0].to_remove) == 1
        assert dupes[0].to_remove[0].get("name") == "Jean Old"

    def test_three_duplicates(self, tmp_path: Path) -> None:
        """Handles three files with same UID."""
        _make_contact(tmp_path, "a.md", "uid-1", "A")
        time.sleep(0.05)
        _make_contact(tmp_path, "b.md", "uid-1", "B")
        time.sleep(0.05)
        _make_contact(tmp_path, "c.md", "uid-1", "C")
        dupes = find_duplicates(tmp_path)
        assert len(dupes) == 1
        assert dupes[0].recommended.get("name") == "C"
        assert len(dupes[0].to_remove) == 2


class TestRemoveDuplicate:
    """Tests for duplicate removal."""

    def test_removes_file(self, tmp_path: Path) -> None:
        """Deletes the .md file."""
        md = _make_contact(tmp_path, "old.md", "uid-1", "Old")
        from jeff.services.triage import load_contact

        data = load_contact(md)
        assert data is not None
        assert remove_duplicate(data)
        assert not md.exists()

"""Unit tests for archive service."""

from __future__ import annotations

from pathlib import Path

from jeff.services.archive import run_archive


def _make_contact(base: Path, slug: str, status: str = "actif") -> None:
    """Create a contact in folder layout."""
    d = base / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.md").write_text(
        f"---\nname: {slug}\nslug: {slug}\nstatus: {status}\n---\n",
        encoding="utf-8",
    )


class TestRunArchive:
    """Tests for archive sorting."""

    def test_archives_contact(self, tmp_path: Path) -> None:
        """Moves archivé contact to archive dir."""
        content = tmp_path / "contacts"
        archive = tmp_path / "archive"
        _make_contact(content, "jean", status="archivé")
        result = run_archive(content, archive)
        assert len(result.archived) == 1
        assert (archive / "jean" / "jean.md").exists()
        assert not (content / "jean").exists()

    def test_restores_contact(self, tmp_path: Path) -> None:
        """Moves non-archivé contact back to contacts dir."""
        content = tmp_path / "contacts"
        archive = tmp_path / "archive"
        content.mkdir()
        _make_contact(archive, "jean", status="actif")
        result = run_archive(content, archive)
        assert len(result.restored) == 1
        assert (content / "jean" / "jean.md").exists()
        assert not (archive / "jean").exists()

    def test_no_changes(self, tmp_path: Path) -> None:
        """No moves when everything is in the right place."""
        content = tmp_path / "contacts"
        archive = tmp_path / "archive"
        _make_contact(content, "jean", status="actif")
        _make_contact(archive, "marie", status="archivé")
        result = run_archive(content, archive)
        assert result.archived == []
        assert result.restored == []

    def test_empty_dirs(self, tmp_path: Path) -> None:
        """Works with empty directories."""
        content = tmp_path / "contacts"
        archive = tmp_path / "archive"
        content.mkdir()
        result = run_archive(content, archive)
        assert result.archived == []
        assert result.restored == []

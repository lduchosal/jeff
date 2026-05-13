"""Unit tests for migration service."""

from __future__ import annotations

from pathlib import Path

from jeff.services.migrate import is_migrated, migrate_to_folders


class TestMigrateToFolders:
    """Tests for flat-to-folder migration."""

    def test_migrates_flat_files(self, tmp_path: Path) -> None:
        """Moves .md files into slug directories."""
        (tmp_path / "jean.md").write_text(
            "---\nname: Jean\nslug: jean\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "marie.md").write_text(
            "---\nname: Marie\nslug: marie\n---\n",
            encoding="utf-8",
        )
        migrated, already = migrate_to_folders(tmp_path)
        assert migrated == 2
        assert already == 0
        assert (tmp_path / "jean" / "jean.md").exists()
        assert (tmp_path / "marie" / "marie.md").exists()
        assert not (tmp_path / "jean.md").exists()

    def test_skips_already_migrated(self, tmp_path: Path) -> None:
        """Skips contacts already in folders."""
        slug_dir = tmp_path / "jean"
        slug_dir.mkdir()
        (slug_dir / "jean.md").write_text(
            "---\nname: Jean\nslug: jean\n---\n",
            encoding="utf-8",
        )
        migrated, already = migrate_to_folders(tmp_path)
        assert migrated == 0
        assert already == 1

    def test_empty_dir(self, tmp_path: Path) -> None:
        """Returns 0,0 for empty dir."""
        migrated, already = migrate_to_folders(tmp_path)
        assert migrated == 0
        assert already == 0


class TestIsMigrated:
    """Tests for migration detection."""

    def test_flat_layout(self, tmp_path: Path) -> None:
        """Detects flat layout as not migrated."""
        (tmp_path / "jean.md").write_text("---\nname: Jean\n---\n")
        assert not is_migrated(tmp_path)

    def test_folder_layout(self, tmp_path: Path) -> None:
        """Detects folder layout as migrated."""
        (tmp_path / "jean").mkdir()
        (tmp_path / "jean" / "jean.md").write_text("---\nname: Jean\n---\n")
        assert is_migrated(tmp_path)

    def test_empty_dir(self, tmp_path: Path) -> None:
        """Empty dir counts as migrated (no flat files)."""
        assert is_migrated(tmp_path)

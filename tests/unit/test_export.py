"""Unit tests for export service."""

from __future__ import annotations

from pathlib import Path

from jeff.services.export import export_squirrelmail


def _make_contact(
    tmp_path: Path,
    slug: str,
    name: str,
    email: str,
    status: str = "actif",
) -> None:
    """Write a contact .md file."""
    slug_dir = tmp_path / slug
    slug_dir.mkdir(exist_ok=True)
    (slug_dir / f"{slug}.md").write_text(
        f"---\nname: {name}\nslug: {slug}\nemail: {email}\n"
        f"name_given: {name.split()[0]}\nname_family: {name.split()[-1]}\n"
        f"status: {status}\nnote: A note\n---\n",
        encoding="utf-8",
    )


class TestExportSquirrelmail:
    """Tests for SquirrelMail export."""

    def test_exports_active(self, tmp_path: Path) -> None:
        """Exports active contacts with email."""
        out = tmp_path / "out.abook"
        _make_contact(tmp_path, "jean", "Jean Dupont", "jean@example.com")
        count = export_squirrelmail(tmp_path, out)
        assert count == 1
        content = out.read_text()
        assert "jean|Jean|Dupont|jean@example.com|" in content

    def test_skips_archived(self, tmp_path: Path) -> None:
        """Does not export archived contacts."""
        out = tmp_path / "out.abook"
        _make_contact(
            tmp_path, "jean", "Jean Dupont", "jean@example.com", status="archivé"
        )
        count = export_squirrelmail(tmp_path, out)
        assert count == 0

    def test_empty_dir(self, tmp_path: Path) -> None:
        """Exports 0 from empty dir."""
        out = tmp_path / "out.abook"
        count = export_squirrelmail(tmp_path, out)
        assert count == 0
        assert out.read_text().strip() == ""

    def test_pipe_in_note(self, tmp_path: Path) -> None:
        """Pipes in notes are replaced."""
        out = tmp_path / "out.abook"
        (tmp_path / "test").mkdir(exist_ok=True)
        (tmp_path / "test" / "test.md").write_text(
            "---\nname: Test\nslug: test\nemail: t@t.com\n"
            'status: actif\nnote: "a|b"\n---\n',
            encoding="utf-8",
        )
        export_squirrelmail(tmp_path, out)
        content = out.read_text()
        assert "|" not in content.split("|", 4)[-1].split("\n")[0] or "a/b" in content

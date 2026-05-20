"""Unit tests for export service."""

from __future__ import annotations

from pathlib import Path

import json

from jeff.services.export import export_json, export_squirrelmail
from jeff.services.import_contacts import import_from_json


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


class TestExportJson:
    """Tests for JSON export (inverse of ``jeff import``)."""

    def test_exports_schema_fields(self, tmp_path: Path) -> None:
        """Includes schema fields; ignores frontmatter-only extras."""
        (tmp_path / "jean").mkdir()
        (tmp_path / "jean" / "jean.md").write_text(
            "---\n"
            "uid: u1\n"
            "name: Jean Dupont\n"
            "slug: jean\n"
            "name_family: Dupont\n"
            "name_given: Jean\n"
            "email: jean@example.com\n"
            "phone: '+41791234567'\n"
            "birthday: 1985-03-15\n"
            "status: actif\n"
            "relation: ami\n"
            "tags: [tech, ami]\n"
            "photo: photos/jean.jpg\n"
            "rev: '2026-01-01'\n"
            "---\n",
            encoding="utf-8",
        )
        out = tmp_path / "contacts.json"
        count = export_json(tmp_path, out)
        assert count == 1
        data = json.loads(out.read_text())
        assert len(data) == 1
        c = data[0]
        assert c["name"] == "Jean Dupont"
        assert c["name_family"] == "Dupont"
        assert c["email"] == "jean@example.com"
        assert c["birthday"] == "1985-03-15"  # date serialised as ISO string
        assert c["tags"] == ["tech", "ami"]
        # Non-schema fields are dropped.
        assert "slug" not in c
        assert "photo" not in c
        assert "rev" not in c

    def test_skips_contacts_without_name(self, tmp_path: Path) -> None:
        """A frontmatter without ``name`` is ignored."""
        (tmp_path / "x").mkdir()
        (tmp_path / "x" / "x.md").write_text(
            "---\nuid: u\nemail: x@x.com\n---\n", encoding="utf-8"
        )
        out = tmp_path / "contacts.json"
        assert export_json(tmp_path, out) == 0
        assert json.loads(out.read_text()) == []

    def test_round_trip_import_export(self, tmp_path: Path) -> None:
        """Re-importing the exported JSON reproduces the same schema payload."""
        source = tmp_path / "in.json"
        original = [
            {
                "uid": "u1",
                "name": "Marie Curie",
                "name_family": "Curie",
                "name_given": "Marie",
                "email": "marie@example.com",
                "phones": [{"number": "+41790000001", "type": "cell"}],
                "tags": ["science"],
                "status": "actif",
                "relation": "ami",
            }
        ]
        source.write_text(json.dumps(original), encoding="utf-8")
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        imported, _ = import_from_json(source, content_dir)
        assert imported == 1

        out = tmp_path / "out.json"
        export_json(content_dir, out)
        round_tripped = json.loads(out.read_text())
        assert round_tripped[0]["name"] == "Marie Curie"
        assert round_tripped[0]["name_family"] == "Curie"
        assert round_tripped[0]["email"] == "marie@example.com"
        assert round_tripped[0]["phones"][0]["number"] == "+41790000001"
        assert round_tripped[0]["tags"] == ["science"]

    def test_empty_dir_writes_empty_array(self, tmp_path: Path) -> None:
        """An empty content dir produces ``[]``."""
        out = tmp_path / "out.json"
        assert export_json(tmp_path, out) == 0
        assert json.loads(out.read_text()) == []

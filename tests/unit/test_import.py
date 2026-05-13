"""Unit tests for import service."""

from __future__ import annotations

import json
from pathlib import Path

from jeff.services.import_contacts import import_from_json


class TestImportFromJson:
    """Tests for JSON contact import."""

    def test_imports_contacts(self, tmp_path: Path) -> None:
        """Creates contact folders from JSON array."""
        content = tmp_path / "contacts"
        content.mkdir()
        json_file = tmp_path / "data.json"
        json_file.write_text(
            json.dumps(
                [
                    {"name": "Jean Dupont", "email": "jean@example.com"},
                    {"name": "Marie Martin", "phone": "+41790000000"},
                ]
            ),
            encoding="utf-8",
        )
        imported, skipped = import_from_json(json_file, content)
        assert imported == 2
        assert skipped == 0
        assert (content / "jean-dupont" / "jean-dupont.md").exists()
        assert (content / "marie-martin" / "marie-martin.md").exists()
        text = (content / "jean-dupont" / "jean-dupont.md").read_text()
        assert "name: Jean Dupont" in text
        assert "jean@example.com" in text

    def test_skips_existing(self, tmp_path: Path) -> None:
        """Skips contacts whose slug directory already exists."""
        content = tmp_path / "contacts"
        (content / "jean-dupont").mkdir(parents=True)
        (content / "jean-dupont" / "jean-dupont.md").write_text("existing")
        json_file = tmp_path / "data.json"
        json_file.write_text(
            json.dumps([{"name": "Jean Dupont"}]),
            encoding="utf-8",
        )
        imported, skipped = import_from_json(json_file, content)
        assert imported == 0
        assert skipped == 1
        assert (content / "jean-dupont" / "jean-dupont.md").read_text() == "existing"

    def test_skips_nameless(self, tmp_path: Path) -> None:
        """Skips entries without a name."""
        content = tmp_path / "contacts"
        content.mkdir()
        json_file = tmp_path / "data.json"
        json_file.write_text(
            json.dumps([{"email": "no-name@test.com"}]),
            encoding="utf-8",
        )
        imported, skipped = import_from_json(json_file, content)
        assert imported == 0
        assert skipped == 1

    def test_single_object(self, tmp_path: Path) -> None:
        """Accepts a single object (not array)."""
        content = tmp_path / "contacts"
        content.mkdir()
        json_file = tmp_path / "data.json"
        json_file.write_text(
            json.dumps({"name": "Solo Contact"}),
            encoding="utf-8",
        )
        imported, skipped = import_from_json(json_file, content)
        assert imported == 1

    def test_generates_uid(self, tmp_path: Path) -> None:
        """Generates UUID when uid is missing."""
        content = tmp_path / "contacts"
        content.mkdir()
        json_file = tmp_path / "data.json"
        json_file.write_text(
            json.dumps([{"name": "Test"}]),
            encoding="utf-8",
        )
        import_from_json(json_file, content)
        text = (content / "test" / "test.md").read_text()
        assert "uid:" in text

    def test_full_contact(self, tmp_path: Path) -> None:
        """Imports a contact with all fields."""
        content = tmp_path / "contacts"
        content.mkdir()
        json_file = tmp_path / "data.json"
        json_file.write_text(
            json.dumps(
                [
                    {
                        "name": "Jean Dupont",
                        "name_family": "Dupont",
                        "name_given": "Jean",
                        "email": "jean@test.com",
                        "phone": "+41791234567",
                        "phones": [{"number": "+41791234567", "type": "cell"}],
                        "birthday": "1985-03-15",
                        "genre": "homme",
                        "tags": ["ami", "tech"],
                        "note": "A note",
                        "status": "actif",
                        "relation": "ami",
                    }
                ]
            ),
            encoding="utf-8",
        )
        imported, _ = import_from_json(json_file, content)
        assert imported == 1
        text = (content / "jean-dupont" / "jean-dupont.md").read_text()
        assert "name_family: Dupont" in text
        assert "genre: homme" in text
        assert "tags:" in text

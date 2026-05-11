"""Unit tests for birthday mail service."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jeff.services.birthday_mail import build_birthday_html


def _make_contact(tmp_path: Path, slug: str, birthday: str, phone: str = "") -> None:
    """Write a contact .md with birthday."""
    (tmp_path / f"{slug}.md").write_text(
        f"---\nname: {slug}\nslug: {slug}\nbirthday: {birthday}\n"
        f"phone: \"{phone}\"\nphone_cell: \"{phone}\"\n---\n",
        encoding="utf-8",
    )


class TestBuildBirthdayHtml:
    """Tests for HTML email generation."""

    def test_generates_html(self) -> None:
        """Generates HTML with contact names."""
        contacts = [
            {"name": "Jean", "birthday": "1985-03-15", "phone": "+41790000000"},
        ]
        html = build_birthday_html(contacts, "Anniversaires aujourd'hui")
        assert "Jean" in html
        assert "1985-03-15" in html
        assert "WhatsApp" in html
        assert "api.whatsapp.com" in html

    def test_empty_contacts(self) -> None:
        """Returns empty string for no contacts."""
        assert build_birthday_html([], "Test") == ""

    def test_no_phone(self) -> None:
        """Handles contacts without phone."""
        contacts = [{"name": "Marie", "birthday": "1990-01-01"}]
        html = build_birthday_html(contacts, "Test")
        assert "Marie" in html
        assert "WhatsApp" not in html

    def test_with_signe(self) -> None:
        """Includes zodiac sign if present."""
        contacts = [
            {"name": "Jean", "birthday": "1985-03-15", "signe": "Poissons"},
        ]
        html = build_birthday_html(contacts, "Test")
        assert "Poissons" in html

"""Unit tests for the static site builder."""

from __future__ import annotations

from pathlib import Path

from jeff.services.publish import (
    _normalize_markdown,
    _parse_frontmatter,
    build_site,
    display_name,
)

SAMPLE_MD = """\
---
uid: "urn:uuid:test-001"
name: Jean Dupont
slug: jean-dupont
name_given: Jean
name_family: Dupont
email: "jean@example.com"
phone: "+41791234567"
birthday: 1985-03-15
note: Un ami fidele.
tags: [ami, tech]
emails:
  - address: "jean@example.com"
    type: work
phones:
  - number: "+41791234567"
    type: cell
---
"""

SAMPLE_MD_MINIMAL = """\
---
name: Marie
slug: marie
---
"""

SAMPLE_MD_WITH_BODY_DASHES = """\
---
name: Pierre Martin
slug: pierre-martin
email: "pierre@example.com"
note: "Contact via réseau---rencontre au salon"
addresses:
  - street: Chemin du Viaduc 1
    city: Prilly
    postal_code: "1008"
    country: Switzerland
---

Some body text.

---

More text after a horizontal rule.
"""


class TestParseFrontmatter:
    """Tests for frontmatter parsing."""

    def test_parses_yaml(self, tmp_path: Path) -> None:
        """Extracts YAML frontmatter from a .md file."""
        f = tmp_path / "test.md"
        f.write_text(SAMPLE_MD)
        data = _parse_frontmatter(f)
        assert data["name"] == "Jean Dupont"
        assert data["slug"] == "jean-dupont"
        assert data["tags"] == ["ami", "tech"]

    def test_body_with_dashes(self, tmp_path: Path) -> None:
        """Ignores --- horizontal rules in the body."""
        f = tmp_path / "test.md"
        f.write_text(SAMPLE_MD_WITH_BODY_DASHES)
        data = _parse_frontmatter(f)
        assert data["name"] == "Pierre Martin"
        assert data["slug"] == "pierre-martin"
        assert data["addresses"][0]["street"] == "Chemin du Viaduc 1"

    def test_handles_no_frontmatter(self, tmp_path: Path) -> None:
        """Returns empty dict when no frontmatter."""
        f = tmp_path / "test.md"
        f.write_text("Just some text")
        data = _parse_frontmatter(f)
        assert data == {}


class TestMarkdownFilter:
    """Tests for the Markdown-to-HTML conversion used in notes."""

    def _render(self, text: str) -> str:
        import markdown as _md

        from jeff.services.publish import _MD_EXTENSIONS

        return _md.markdown(_normalize_markdown(text), extensions=_MD_EXTENSIONS)

    def test_heading_without_blank_line(self) -> None:
        """## headings render even when the previous line is non-empty."""
        html = self._render("Intro\n## Titre 2\nSuite")
        assert "<h2>Titre 2</h2>" in html

    def test_list_with_bold_item(self) -> None:
        """- **bold** list items render as <ul><li><strong>."""
        html = self._render("Texte avant\n- **tiret et gras**\n- normal\n")
        assert "<ul>" in html
        assert "<strong>tiret et gras</strong>" in html
        assert "<li>normal</li>" in html

    def test_inline_bold(self) -> None:
        """**bold** renders inside a paragraph."""
        html = self._render("Du **gras** au milieu.")
        assert "<strong>gras</strong>" in html

    def test_tight_list_no_paragraph_wrap(self) -> None:
        """Consecutive list items stay tight (no <p> inside <li>)."""
        html = self._render("Avant\n- un\n- deux\n- trois\n")
        assert "<li>un</li>" in html
        assert "<li><p>" not in html


class TestDisplayName:
    """Family name is uppercased; given name keeps its case."""

    def test_uppercases_family(self) -> None:
        assert display_name({"name_given": "Jean", "name_family": "Dupont"}) == (
            "Jean DUPONT"
        )

    def test_family_only(self) -> None:
        assert display_name({"name_family": "Madonna"}) == "MADONNA"

    def test_falls_back_to_name(self) -> None:
        assert display_name({"name": "Cher"}) == "Cher"

    def test_preserves_already_uppercased_family(self) -> None:
        assert display_name({"name_given": "Luc", "name_family": "DUCHOSAL"}) == (
            "Luc DUCHOSAL"
        )

    def test_empty(self) -> None:
        assert display_name({}) == ""


class TestBuildSite:
    """Tests for the full build pipeline."""

    def test_builds_contact_and_index(self, tmp_path: Path) -> None:
        """Generates HTML files for contacts and an index."""
        content_dir = tmp_path / "content" / "contacts"
        content_dir.mkdir(parents=True)
        (content_dir / "jean-dupont").mkdir(exist_ok=True)

        (content_dir / "jean-dupont" / "jean-dupont.md").write_text(SAMPLE_MD)
        (content_dir / "marie").mkdir(exist_ok=True)

        (content_dir / "marie" / "marie.md").write_text(SAMPLE_MD_MINIMAL)

        output_dir = tmp_path / "public"
        count = build_site(content_dir, output_dir)

        assert count == 2
        assert (output_dir / "index.html").exists()
        assert (output_dir / "contacts" / "jean-dupont.html").exists()
        assert (output_dir / "contacts" / "marie.html").exists()

        # Check content.
        index = (output_dir / "index.html").read_text()
        assert "Jean DUPONT" in index  # family name uppercased
        assert "Marie" in index
        assert "2 contacts" in index

        contact = (output_dir / "contacts" / "jean-dupont.html").read_text()
        assert "Jean DUPONT" in contact  # family name uppercased
        assert "jean@example.com" in contact
        assert "ami" in contact

    def test_copies_css(self, tmp_path: Path) -> None:
        """Copies CSS file to output."""
        content_dir = tmp_path / "content" / "contacts"
        content_dir.mkdir(parents=True)
        (content_dir / "marie").mkdir(exist_ok=True)

        (content_dir / "marie" / "marie.md").write_text(SAMPLE_MD_MINIMAL)

        css = tmp_path / "contact.css"
        css.write_text("body { color: red; }")

        output_dir = tmp_path / "public"
        build_site(content_dir, output_dir, css_path=css)

        assert (output_dir / "css" / "contact.css").exists()
        assert "color: red" in (output_dir / "css" / "contact.css").read_text()

    def test_copies_photos(self, tmp_path: Path) -> None:
        """Copies photo files to output."""
        content_dir = tmp_path / "content" / "contacts"
        content_dir.mkdir(parents=True)
        (content_dir / "marie").mkdir(exist_ok=True)

        (content_dir / "marie" / "marie.md").write_text(SAMPLE_MD_MINIMAL)

        photo_dir = tmp_path / "photos"
        photo_dir.mkdir()
        (photo_dir / "marie.png").write_bytes(b"fakepng")

        output_dir = tmp_path / "public"
        build_site(content_dir, output_dir, photo_dir=photo_dir)

        assert (output_dir / "photos" / "marie.png").exists()

    def test_empty_content_dir(self, tmp_path: Path) -> None:
        """Builds an empty site when no contacts exist."""
        content_dir = tmp_path / "content" / "contacts"
        output_dir = tmp_path / "public"
        count = build_site(content_dir, output_dir)
        assert count == 0
        assert (output_dir / "index.html").exists()
        assert "0 contact" in (output_dir / "index.html").read_text()

    def test_recency_dot_recent(self, tmp_path: Path) -> None:
        """Shows green recency dot for contact with recent interaction."""
        from datetime import date

        content_dir = tmp_path / "content" / "contacts"
        contact_dir = content_dir / "jean-dupont"
        contact_dir.mkdir(parents=True)
        (contact_dir / "jean-dupont.md").write_text(SAMPLE_MD)

        # Create a recent interaction (today).
        today = date.today().isoformat()
        (contact_dir / f"{today}.md").write_text(
            f"---\ndate: {today}\ntype: tel\n---\n\nAppel rapide.\n"
        )

        output_dir = tmp_path / "public"
        build_site(content_dir, output_dir)

        index = (output_dir / "index.html").read_text()
        assert "recency-dot--recent" in index

    def test_recency_dot_old(self, tmp_path: Path) -> None:
        """Shows red recency dot for contact with old interaction (< 6 months)."""
        from datetime import date, timedelta

        content_dir = tmp_path / "content" / "contacts"
        contact_dir = content_dir / "jean-dupont"
        contact_dir.mkdir(parents=True)
        (contact_dir / "jean-dupont.md").write_text(SAMPLE_MD)

        # Create an interaction 100 days ago (within 6 months).
        old_date = (date.today() - timedelta(days=100)).isoformat()
        (contact_dir / f"{old_date}.md").write_text(
            f"---\ndate: {old_date}\ntype: tel\n---\n\nVieux appel.\n"
        )

        output_dir = tmp_path / "public"
        build_site(content_dir, output_dir)

        index = (output_dir / "index.html").read_text()
        assert "recency-dot--old" in index

    def test_no_recency_dot_without_interactions(self, tmp_path: Path) -> None:
        """No recency dot when contact has no interactions."""
        content_dir = tmp_path / "content" / "contacts"
        contact_dir = content_dir / "jean-dupont"
        contact_dir.mkdir(parents=True)
        (contact_dir / "jean-dupont.md").write_text(SAMPLE_MD)

        output_dir = tmp_path / "public"
        build_site(content_dir, output_dir)

        index = (output_dir / "index.html").read_text()
        assert "recency-dot" not in index

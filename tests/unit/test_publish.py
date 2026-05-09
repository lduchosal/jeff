"""Unit tests for the static site builder."""

from __future__ import annotations

from pathlib import Path

from jeff.publish import _parse_frontmatter, build_site

SAMPLE_MD = """\
---
uid: "urn:uuid:test-001"
name: Jean Dupont
slug: jean-dupont
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


class TestBuildSite:
    """Tests for the full build pipeline."""

    def test_builds_contact_and_index(self, tmp_path: Path) -> None:
        """Generates HTML files for contacts and an index."""
        content_dir = tmp_path / "content" / "contacts"
        content_dir.mkdir(parents=True)
        (content_dir / "jean-dupont.md").write_text(SAMPLE_MD)
        (content_dir / "marie.md").write_text(SAMPLE_MD_MINIMAL)

        output_dir = tmp_path / "public"
        count = build_site(content_dir, output_dir)

        assert count == 2
        assert (output_dir / "index.html").exists()
        assert (output_dir / "contacts" / "jean-dupont.html").exists()
        assert (output_dir / "contacts" / "marie.html").exists()

        # Check content.
        index = (output_dir / "index.html").read_text()
        assert "Jean Dupont" in index
        assert "Marie" in index
        assert "2 contacts" in index

        contact = (output_dir / "contacts" / "jean-dupont.html").read_text()
        assert "Jean Dupont" in contact
        assert "jean@example.com" in contact
        assert "ami" in contact

    def test_copies_css(self, tmp_path: Path) -> None:
        """Copies CSS file to output."""
        content_dir = tmp_path / "content" / "contacts"
        content_dir.mkdir(parents=True)
        (content_dir / "marie.md").write_text(SAMPLE_MD_MINIMAL)

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
        (content_dir / "marie.md").write_text(SAMPLE_MD_MINIMAL)

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

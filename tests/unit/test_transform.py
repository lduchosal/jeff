"""Unit tests for vCard to Markdown transformation."""

from __future__ import annotations

from pathlib import Path

from jeff.domain.carddav import Contact
from jeff.domain.transform import (
    contact_to_markdown,
    parse_vcard,
    render_frontmatter,
    slugify,
)

# -- Sample vCards -------------------------------------------------------------

VCARD_FULL = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:f47ac10b-58cc-4372-a567-0e02b2c3d479
FN:Jean Dupont
N:Dupont;Jean;;;
EMAIL;TYPE=WORK;TYPE=PREF:jean@work.com
EMAIL;TYPE=HOME:jean@home.com
TEL;TYPE=CELL;TYPE=PREF:+41791234567
TEL;TYPE=WORK:+41221234567
ADR;TYPE=WORK:;;Rue du Marche 12;Geneve;GE;1204;Switzerland
ORG:Acme Corp
TITLE:CTO
BDAY:1985-03-15
CATEGORIES:friend,a-list
URL;TYPE=WORK:https://acme-corp.ch
NOTE:Met at FOSDEM 2024.
REV:2026-05-08T14:30:00Z
END:VCARD"""

VCARD_MINIMAL = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:aaa-bbb
FN:Marie
N:;Marie;;;
END:VCARD"""

VCARD_MULTILINE_ADR = (
    "BEGIN:VCARD\r\n"
    "VERSION:3.0\r\n"
    "UID:urn:uuid:multiline-adr\r\n"
    "FN:Cinetoile\r\n"
    "N:;Cinetoile;;;\r\n"
    "ADR;TYPE=HOME:;;Centre Malley Lumières\\nChemin du Viaduc 1;Prilly;;1008;Switzerland\r\n"
    "END:VCARD"
)

VCARD_MULTI_ORG = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:multi-org
FN:Pierre Blanc
N:Blanc;Pierre;;;
ORG:Alpha SA
TITLE:CEO
ORG:Beta GmbH
TITLE:Advisor
END:VCARD"""


# -- slugify tests -------------------------------------------------------------


class TestSlugify:
    """Tests for slug generation."""

    def test_basic(self) -> None:
        """Simple name slugification."""
        assert slugify("Jean Dupont") == "jean-dupont"

    def test_accents(self) -> None:
        """Handles French accents."""
        assert slugify("René Müller") == "rene-muller"

    def test_special_chars(self) -> None:
        """Strips special characters."""
        assert slugify("O'Brien (Jr.)") == "o-brien-jr"

    def test_empty(self) -> None:
        """Returns 'contact' for empty input."""
        assert slugify("") == "contact"
        assert slugify("!!!") == "contact"


# -- parse_vcard tests ---------------------------------------------------------


class TestParseVcard:
    """Tests for vCard parsing."""

    def test_full_vcard(self) -> None:
        """Extracts all fields from a complete vCard."""
        data = parse_vcard(VCARD_FULL)
        assert data["uid"] == "urn:uuid:f47ac10b-58cc-4372-a567-0e02b2c3d479"
        assert data["name"] == "Jean Dupont"
        assert data["slug"] == "jean-dupont"
        assert data["name_family"] == "Dupont"
        assert data["name_given"] == "Jean"
        assert data["email"] == "jean@work.com"
        assert data["phone"] == "+41791234567"
        assert len(data["emails"]) == 2
        assert data["emails"][0]["pref"] is True
        assert len(data["phones"]) == 2
        assert data["addresses"][0]["city"] == "Geneve"
        assert data["positions"][0]["org"] == "Acme Corp"
        assert data["positions"][0]["title"] == "CTO"
        assert data["birthday"] == "1985-03-15"
        assert data["tags"] == ["friend", "a-list"]
        assert data["urls"][0]["url"] == "https://acme-corp.ch"
        assert data["note"] == "Met at FOSDEM 2024."

    def test_minimal_vcard(self) -> None:
        """Handles a vCard with only required fields."""
        data = parse_vcard(VCARD_MINIMAL)
        assert data["uid"] == "urn:uuid:aaa-bbb"
        assert data["name"] == "Marie"
        assert data["slug"] == "marie"
        assert "emails" not in data
        assert "phones" not in data
        assert "addresses" not in data

    def test_multi_org(self) -> None:
        """Parses multiple ORG/TITLE pairs."""
        data = parse_vcard(VCARD_MULTI_ORG)
        assert len(data["positions"]) == 2
        assert data["positions"][0]["org"] == "Alpha SA"
        assert data["positions"][0]["title"] == "CEO"
        assert data["positions"][1]["org"] == "Beta GmbH"
        assert data["positions"][1]["title"] == "Advisor"

    def test_multiline_address(self) -> None:
        """Multi-line street in ADR produces valid YAML frontmatter."""
        import yaml

        data = parse_vcard(VCARD_MULTILINE_ADR)
        data.pop("_photo_data", None)
        fm = render_frontmatter(data)
        # The frontmatter must be valid YAML.
        yaml_text = fm.strip().removeprefix("---").removesuffix("---").strip()
        parsed = yaml.safe_load(yaml_text)
        street = parsed["addresses"][0]["street"]
        assert "Centre Malley" in street
        assert "Chemin du Viaduc" in street


# -- render_frontmatter tests --------------------------------------------------


class TestRenderFrontmatter:
    """Tests for YAML frontmatter rendering."""

    def test_renders_scalars(self) -> None:
        """Renders scalar fields in frontmatter."""
        data = parse_vcard(VCARD_MINIMAL)
        data.pop("_photo_data", None)
        fm = render_frontmatter(data)
        assert "---" in fm
        assert '"urn:uuid:aaa-bbb"' in fm
        assert "name: Marie" in fm
        assert "slug: marie" in fm

    def test_renders_lists(self) -> None:
        """Renders list fields in frontmatter."""
        data = parse_vcard(VCARD_FULL)
        data.pop("_photo_data", None)
        fm = render_frontmatter(data)
        assert "emails:" in fm
        assert '"jean@work.com"' in fm
        assert "phones:" in fm
        assert "positions:" in fm
        assert "- org: Acme Corp" in fm
        assert "tags: [friend, a-list]" in fm

    def test_quotes_phone_numbers(self) -> None:
        """Phone numbers with + are quoted."""
        data = parse_vcard(VCARD_FULL)
        data.pop("_photo_data", None)
        fm = render_frontmatter(data)
        assert 'phone: "+41791234567"' in fm


# -- contact_to_markdown tests -------------------------------------------------


class TestContactToMarkdown:
    """Tests for the full transform pipeline."""

    def test_writes_markdown_file(self, tmp_path: Path) -> None:
        """Creates a .md file with frontmatter."""
        contact = Contact(
            href="/contact.vcf",
            etag="etag-1",
            vcard_raw=VCARD_FULL,
        )
        content_dir = tmp_path / "content" / "contacts"
        photo_dir = tmp_path / "static" / "photos"
        path = contact_to_markdown(contact, content_dir, photo_dir)
        assert path.name == "jean-dupont.md"
        assert path.exists()
        text = path.read_text()
        assert text.startswith("---")
        assert "name: Jean Dupont" in text
        assert '"jean@work.com"' in text

    def test_minimal_contact(self, tmp_path: Path) -> None:
        """Handles minimal vCards without crashing."""
        contact = Contact(
            href="/min.vcf",
            etag="etag-2",
            vcard_raw=VCARD_MINIMAL,
        )
        content_dir = tmp_path / "content" / "contacts"
        photo_dir = tmp_path / "static" / "photos"
        path = contact_to_markdown(contact, content_dir, photo_dir)
        assert path.name == "marie.md"
        text = path.read_text()
        assert "name: Marie" in text
        assert "emails:" not in text

    def test_resync_preserves_triage_fields(self, tmp_path: Path) -> None:
        """Triage fields survive a re-sync (sync → triage → sync)."""
        from jeff.services.triage import save_triage

        contact = Contact(
            href="/contact.vcf",
            etag="etag-1",
            vcard_raw=VCARD_FULL,
        )
        content_dir = tmp_path / "content" / "contacts"
        photo_dir = tmp_path / "static" / "photos"

        # 1. First sync — creates the .md with empty triage fields.
        path = contact_to_markdown(contact, content_dir, photo_dir)
        text = path.read_text()
        assert "status:" in text
        assert "status: actif" not in text

        # 2. Simulate triage — user sets fields by hand.
        save_triage(
            path,
            {
                "status": "actif",
                "relation": "ami",
                "frequence": "mensuel",
                "priorite": "haute",
            },
        )
        text = path.read_text()
        assert "status: actif" in text
        assert "relation: ami" in text

        # 3. Re-sync — same contact, new etag (simulating a server update).
        contact_v2 = Contact(
            href="/contact.vcf",
            etag="etag-2",
            vcard_raw=VCARD_FULL,
        )
        path = contact_to_markdown(contact_v2, content_dir, photo_dir)

        # 4. Triage fields must be preserved.
        text = path.read_text()
        assert "status: actif" in text
        assert "relation: ami" in text
        assert "frequence: mensuel" in text
        assert "priorite: haute" in text

    def test_resync_preserves_family_links(self, tmp_path: Path) -> None:
        """Family link fields survive a re-sync."""
        from jeff.services.triage import save_triage

        contact = Contact(
            href="/contact.vcf",
            etag="etag-1",
            vcard_raw=VCARD_FULL,
        )
        content_dir = tmp_path / "content" / "contacts"
        photo_dir = tmp_path / "static" / "photos"

        # 1. First sync.
        path = contact_to_markdown(contact, content_dir, photo_dir)
        assert "pere:" in path.read_text()

        # 2. Edit family links by hand.
        save_triage(
            path,
            {
                "pere": "jacques-dupont",
                "conjoint": "marie-dupont",
            },
        )

        # 3. Re-sync.
        contact_v2 = Contact(
            href="/contact.vcf",
            etag="etag-2",
            vcard_raw=VCARD_FULL,
        )
        path = contact_to_markdown(contact_v2, content_dir, photo_dir)

        # 4. Family links must be preserved.
        text = path.read_text()
        assert "pere: jacques-dupont" in text
        assert "conjoint: marie-dupont" in text

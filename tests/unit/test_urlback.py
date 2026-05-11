"""Unit tests for CRM URL writeback."""

from __future__ import annotations

from jeff.domain.urlback import (
    build_profile_url,
    inject_crm_url,
    inject_gender,
    inject_related,
)

SAMPLE_VCARD = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:test-001
FN:Jean Dupont
N:Dupont;Jean;;;
EMAIL:jean@example.com
END:VCARD"""

SAMPLE_VCARD_WITH_URL = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:test-001
FN:Jean Dupont
N:Dupont;Jean;;;
EMAIL:jean@example.com
item99.URL:https://crm.example.com/contacts/jean-dupont.html
item99.X-ABLabel:Profil CRM
END:VCARD"""


class TestInjectCrmUrl:
    """Tests for URL injection into vCard."""

    def test_injects_url(self) -> None:
        """Adds item99.URL and X-ABLabel before END:VCARD."""
        result = inject_crm_url(
            SAMPLE_VCARD, "https://crm.example.com/contacts/jean-dupont.html"
        )
        assert result is not None
        assert "item99.URL:https://crm.example.com/contacts/jean-dupont.html" in result
        assert "item99.X-ABLabel:Profil CRM" in result
        assert result.endswith("END:VCARD")

    def test_skips_if_url_present(self) -> None:
        """Returns None when URL is already in the vCard."""
        result = inject_crm_url(
            SAMPLE_VCARD_WITH_URL,
            "https://crm.example.com/contacts/jean-dupont.html",
        )
        assert result is None

    def test_replaces_stale_item99(self) -> None:
        """Removes old item99 lines before injecting new URL."""
        vcard_with_old = SAMPLE_VCARD.replace(
            "END:VCARD",
            "item99.URL:https://old.example.com/old\nitem99.X-ABLabel:Old\nEND:VCARD",
        )
        result = inject_crm_url(
            vcard_with_old, "https://new.example.com/contacts/jean.html"
        )
        assert result is not None
        assert "old.example.com" not in result
        assert "https://new.example.com/contacts/jean.html" in result


class TestInjectGender:
    """Tests for gender injection into vCard."""

    def test_injects_male(self) -> None:
        """Adds X-GENDER:M for homme."""
        result = inject_gender(SAMPLE_VCARD, "homme")
        assert result is not None
        assert "X-GENDER:M" in result
        assert result.endswith("END:VCARD")

    def test_injects_female(self) -> None:
        """Adds X-GENDER:F for femme."""
        result = inject_gender(SAMPLE_VCARD, "femme")
        assert result is not None
        assert "X-GENDER:F" in result

    def test_skips_if_same(self) -> None:
        """Returns None when gender is already set to the same value."""
        vcard = SAMPLE_VCARD.replace("END:VCARD", "X-GENDER:M\nEND:VCARD")
        result = inject_gender(vcard, "homme")
        assert result is None

    def test_replaces_different(self) -> None:
        """Replaces existing X-GENDER when changing."""
        vcard = SAMPLE_VCARD.replace("END:VCARD", "X-GENDER:M\nEND:VCARD")
        result = inject_gender(vcard, "femme")
        assert result is not None
        assert "X-GENDER:F" in result
        assert "X-GENDER:M" not in result


class TestInjectRelated:
    """Tests for RELATED property injection."""

    def test_injects_related(self) -> None:
        """Adds RELATED lines before END:VCARD."""
        result = inject_related(SAMPLE_VCARD, [("spouse", "uid-marie")])
        assert result is not None
        assert "RELATED;TYPE=spouse:urn:uuid:uid-marie" in result

    def test_skips_if_same(self) -> None:
        """Returns None when RELATED already present."""
        vcard = SAMPLE_VCARD.replace(
            "END:VCARD",
            "RELATED;TYPE=spouse:urn:uuid:uid-marie\nEND:VCARD",
        )
        result = inject_related(vcard, [("spouse", "uid-marie")])
        assert result is None

    def test_replaces_old(self) -> None:
        """Replaces existing RELATED with new set."""
        vcard = SAMPLE_VCARD.replace(
            "END:VCARD",
            "RELATED;TYPE=spouse:urn:uuid:old\nEND:VCARD",
        )
        result = inject_related(vcard, [("spouse", "uid-new")])
        assert result is not None
        assert "uid-new" in result
        assert "old" not in result

    def test_multiple_relations(self) -> None:
        """Handles multiple RELATED entries."""
        result = inject_related(
            SAMPLE_VCARD,
            [("parent", "uid-pere"), ("spouse", "uid-marie"), ("child", "uid-luc")],
        )
        assert result is not None
        assert "TYPE=parent" in result
        assert "TYPE=spouse" in result
        assert "TYPE=child" in result

    def test_empty_relations(self) -> None:
        """Returns None for empty relations list."""
        assert inject_related(SAMPLE_VCARD, []) is None


class TestBuildProfileUrl:
    """Tests for profile URL construction."""

    def test_basic(self) -> None:
        """Builds URL from base and slug."""
        url = build_profile_url("https://crm.example.com", "jean-dupont")
        assert url == "https://crm.example.com/contacts/jean-dupont.html"

    def test_trailing_slash(self) -> None:
        """Strips trailing slash from base URL."""
        url = build_profile_url("https://crm.example.com/", "jean-dupont")
        assert url == "https://crm.example.com/contacts/jean-dupont.html"

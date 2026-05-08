"""Unit tests for CRM URL writeback."""

from __future__ import annotations

from jeff.urlback import build_profile_url, inject_crm_url


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
        result = inject_crm_url(SAMPLE_VCARD, "https://crm.example.com/contacts/jean-dupont.html")
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
        result = inject_crm_url(vcard_with_old, "https://new.example.com/contacts/jean.html")
        assert result is not None
        assert "old.example.com" not in result
        assert "https://new.example.com/contacts/jean.html" in result


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

"""Unit tests for the CardDAV client.

HTTP is mocked at the ``requests.Session.request`` boundary so no real server is needed.
Tests verify XML parsing, change detection, and sync state management.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from jeff.carddav import CardDAVClient, CardDAVConfig, SyncState

# -- Fixtures ----------------------------------------------------------------

SAMPLE_VCARD = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:f47ac10b-58cc-4372-a567-0e02b2c3d479
FN:Jean Dupont
N:Dupont;Jean;;;
EMAIL:jean@example.com
TEL:+41791234567
END:VCARD"""

SAMPLE_VCARD_2 = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:a1b2c3d4-0000-0000-0000-000000000001
FN:Marie Laurent
N:Laurent;Marie;;;
EMAIL:marie@example.com
END:VCARD"""


def _make_client() -> CardDAVClient:
    """Create a client with dummy config."""
    config = CardDAVConfig(
        url="https://dav.example.com/dav.php/addressbooks/user/default/",
        username="user",
        password="pass",
    )
    return CardDAVClient(config)


def _mock_response(content: str, status_code: int = 207) -> MagicMock:
    """Build a fake requests.Response."""
    resp = MagicMock()
    resp.content = content.encode("utf-8")
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


# -- XML response templates ---------------------------------------------------

PROPFIND_ADDRESSBOOKS = """\
<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/dav.php/addressbooks/user/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype><d:collection/></d:resourcetype>
        <d:displayname>user</d:displayname>
      </d:prop>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype>
          <d:collection/>
          <card:addressbook/>
        </d:resourcetype>
        <d:displayname>Contacts</d:displayname>
      </d:prop>
    </d:propstat>
  </d:response>
</d:multistatus>"""

PROPFIND_CTAG = """\
<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:cs="http://calendarserver.org/ns/">
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/</d:href>
    <d:propstat>
      <d:prop>
        <cs:getctag>ctag-abc-123</cs:getctag>
      </d:prop>
    </d:propstat>
  </d:response>
</d:multistatus>"""

PROPFIND_CONTACTS = """\
<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/</d:href>
    <d:propstat>
      <d:prop>
        <d:getetag>"collection-etag"</d:getetag>
        <d:resourcetype>
          <d:collection/>
          <card:addressbook/>
        </d:resourcetype>
      </d:prop>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/contact1.vcf</d:href>
    <d:propstat>
      <d:prop>
        <d:getetag>"etag-111"</d:getetag>
        <d:resourcetype/>
      </d:prop>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/contact2.vcf</d:href>
    <d:propstat>
      <d:prop>
        <d:getetag>"etag-222"</d:getetag>
        <d:resourcetype/>
      </d:prop>
    </d:propstat>
  </d:response>
</d:multistatus>"""

MULTIGET_RESPONSE = """\
<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/contact1.vcf</d:href>
    <d:propstat>
      <d:prop>
        <d:getetag>"etag-111"</d:getetag>
        <card:address-data>{vcard1}</card:address-data>
      </d:prop>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/contact2.vcf</d:href>
    <d:propstat>
      <d:prop>
        <d:getetag>"etag-222"</d:getetag>
        <card:address-data>{vcard2}</card:address-data>
      </d:prop>
    </d:propstat>
  </d:response>
</d:multistatus>""".format(vcard1=SAMPLE_VCARD, vcard2=SAMPLE_VCARD_2)


# -- SyncState tests ----------------------------------------------------------


class TestSyncState:
    """Tests for SyncState persistence."""

    def test_save_and_load(self, tmp_path: object) -> None:
        """State round-trips through JSON."""
        path = tmp_path / ".sync-state.json"  # type: ignore[operator]
        state = SyncState(
            ctag="ctag-1",
            contacts={"/contact1.vcf": {"etag": "e1"}},
        )
        state.save(path)
        loaded = SyncState.load(path)
        assert loaded.ctag == "ctag-1"
        assert loaded.contacts["/contact1.vcf"]["etag"] == "e1"

    def test_load_missing_file(self, tmp_path: object) -> None:
        """Loading from a missing file returns empty state."""
        path = tmp_path / "nope.json"  # type: ignore[operator]
        state = SyncState.load(path)
        assert state.ctag is None
        assert state.contacts == {}


# -- Client tests --------------------------------------------------------------


class TestDiscoverAddressbooks:
    """Tests for addressbook discovery."""

    def test_finds_addressbook(self) -> None:
        """Discovers addressbooks from a PROPFIND response."""
        client = _make_client()
        with patch.object(
            client._session,
            "request",
            return_value=_mock_response(PROPFIND_ADDRESSBOOKS),
        ):
            books = client.discover_addressbooks()
        assert len(books) == 1
        assert books[0]["href"] == "/dav.php/addressbooks/user/default/"
        assert books[0]["displayname"] == "Contacts"


class TestGetCtag:
    """Tests for CTag retrieval."""

    def test_returns_ctag(self) -> None:
        """Parses ctag from XML response."""
        client = _make_client()
        with patch.object(
            client._session,
            "request",
            return_value=_mock_response(PROPFIND_CTAG),
        ):
            ctag = client.get_ctag("/dav.php/addressbooks/user/default/")
        assert ctag == "ctag-abc-123"


class TestListContacts:
    """Tests for listing contact hrefs and etags."""

    def test_lists_contacts_skipping_collection(self) -> None:
        """Lists .vcf hrefs, skips the addressbook itself."""
        client = _make_client()
        with patch.object(
            client._session,
            "request",
            return_value=_mock_response(PROPFIND_CONTACTS),
        ):
            contacts = client.list_contacts("/dav.php/addressbooks/user/default/")
        assert len(contacts) == 2
        assert contacts["/dav.php/addressbooks/user/default/contact1.vcf"] == "etag-111"
        assert contacts["/dav.php/addressbooks/user/default/contact2.vcf"] == "etag-222"


class TestFetchContacts:
    """Tests for batch fetching vCard data."""

    def test_multiget_returns_contacts(self) -> None:
        """Parses contacts from an addressbook-multiget response."""
        client = _make_client()
        with patch.object(
            client._session,
            "request",
            return_value=_mock_response(MULTIGET_RESPONSE),
        ):
            contacts = client.fetch_contacts(
                "/dav.php/addressbooks/user/default/",
                [
                    "/dav.php/addressbooks/user/default/contact1.vcf",
                    "/dav.php/addressbooks/user/default/contact2.vcf",
                ],
            )
        assert len(contacts) == 2
        assert "Jean Dupont" in contacts[0].vcard_raw
        assert "Marie Laurent" in contacts[1].vcard_raw
        assert contacts[0].etag == "etag-111"

    def test_empty_hrefs_returns_empty(self) -> None:
        """No HTTP call when hrefs list is empty."""
        client = _make_client()
        result = client.fetch_contacts("/dav.php/addressbooks/user/default/", [])
        assert result == []


class TestSync:
    """Tests for incremental sync logic."""

    def test_no_change_when_ctag_matches(self) -> None:
        """Returns empty results when ctag has not changed."""
        client = _make_client()
        state = SyncState(ctag="ctag-abc-123")
        with patch.object(
            client._session,
            "request",
            return_value=_mock_response(PROPFIND_CTAG),
        ):
            updated, deleted, new_state = client.sync(
                "/dav.php/addressbooks/user/default/", state
            )
        assert updated == []
        assert deleted == []
        assert new_state.ctag == "ctag-abc-123"

    def test_detects_new_contacts(self) -> None:
        """Fetches contacts that were not in previous state."""
        client = _make_client()
        state = SyncState(ctag="old-ctag", contacts={})
        responses = [
            _mock_response(PROPFIND_CTAG),
            _mock_response(PROPFIND_CONTACTS),
            _mock_response(MULTIGET_RESPONSE),
        ]
        with patch.object(client._session, "request", side_effect=responses):
            updated, deleted, new_state = client.sync(
                "/dav.php/addressbooks/user/default/", state
            )
        assert len(updated) == 2
        assert deleted == []
        assert new_state.ctag == "ctag-abc-123"
        assert len(new_state.contacts) == 2

    def test_detects_deleted_contacts(self) -> None:
        """Detects contacts that are gone from the server."""
        client = _make_client()
        state = SyncState(
            ctag="old-ctag",
            contacts={
                "/dav.php/addressbooks/user/default/contact1.vcf": {"etag": "etag-111"},
                "/dav.php/addressbooks/user/default/contact2.vcf": {"etag": "etag-222"},
                "/dav.php/addressbooks/user/default/gone.vcf": {"etag": "etag-old"},
            },
        )
        responses = [
            _mock_response(PROPFIND_CTAG),
            _mock_response(PROPFIND_CONTACTS),
            # No changed hrefs since etags match.
        ]
        with patch.object(client._session, "request", side_effect=responses):
            updated, deleted, new_state = client.sync(
                "/dav.php/addressbooks/user/default/", state
            )
        assert updated == []
        assert "/dav.php/addressbooks/user/default/gone.vcf" in deleted
        assert len(new_state.contacts) == 2

    def test_detects_updated_contacts(self) -> None:
        """Fetches contacts whose etag changed."""
        client = _make_client()
        state = SyncState(
            ctag="old-ctag",
            contacts={
                "/dav.php/addressbooks/user/default/contact1.vcf": {"etag": "etag-111"},
                "/dav.php/addressbooks/user/default/contact2.vcf": {"etag": "old-etag"},
            },
        )
        # contact2 has a new etag, so it should be fetched.
        multiget_single = """\
<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/dav.php/addressbooks/user/default/contact2.vcf</d:href>
    <d:propstat>
      <d:prop>
        <d:getetag>"etag-222"</d:getetag>
        <card:address-data>{vcard}</card:address-data>
      </d:prop>
    </d:propstat>
  </d:response>
</d:multistatus>""".format(vcard=SAMPLE_VCARD_2)
        responses = [
            _mock_response(PROPFIND_CTAG),
            _mock_response(PROPFIND_CONTACTS),
            _mock_response(multiget_single),
        ]
        with patch.object(client._session, "request", side_effect=responses):
            updated, deleted, _ = client.sync(
                "/dav.php/addressbooks/user/default/", state
            )
        assert len(updated) == 1
        assert "Marie Laurent" in updated[0].vcard_raw
        assert deleted == []

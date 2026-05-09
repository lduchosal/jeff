"""CardDAV client for Baikal.

Minimal, no-bloat CardDAV client using ``requests`` + ``lxml``. Supports discovery,
contact listing, batch fetch, and change detection via sync-token / ctag / etags.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
from lxml import etree

from jeff.log import get_logger

_log = get_logger("carddav")

# XML namespaces used in CardDAV / WebDAV.
DAV = "DAV:"
CARDDAV = "urn:ietf:params:xml:ns:carddav"
CS = "http://calendarserver.org/ns/"

_NS = {"d": DAV, "card": CARDDAV, "cs": CS}


@dataclass
class Contact:
    """A single contact fetched from the server."""

    href: str
    etag: str
    vcard_raw: str


@dataclass
class SyncState:
    """Persistent sync state stored on disk as JSON."""

    sync_token: str | None = None
    ctag: str | None = None
    contacts: dict[str, dict[str, str]] = field(default_factory=dict)

    def save(self, path: Path) -> None:
        """Write state to a JSON file."""
        data = {
            "sync_token": self.sync_token,
            "ctag": self.ctag,
            "contacts": self.contacts,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SyncState:
        """Load state from a JSON file, or return empty state."""
        if not path.is_file():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            sync_token=data.get("sync_token"),
            ctag=data.get("ctag"),
            contacts=data.get("contacts", {}),
        )


@dataclass
class CardDAVConfig:
    """Connection parameters for a CardDAV server."""

    url: str
    username: str
    password: str

    @property
    def base_url(self) -> str:
        """Return the URL without a trailing slash."""
        return self.url.rstrip("/")


class CardDAVClient:
    """Minimal CardDAV client for Baikal.

    Talks to the server using raw WebDAV/CardDAV XML requests. No dependency on
    vdirsyncer internals.
    """

    def __init__(self, config: CardDAVConfig) -> None:
        """Initialize the CardDAV client."""
        self._config = config
        self._session = requests.Session()
        self._session.auth = (config.username, config.password)
        self._session.headers["Content-Type"] = "application/xml; charset=utf-8"

    def discover_addressbooks(self) -> list[dict[str, str]]:
        """Find all addressbooks for the authenticated user.

        Returns a list of dicts with ``href`` and ``displayname`` keys.
        """
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<d:propfind xmlns:d="DAV:">'
            "<d:prop>"
            "<d:resourcetype/>"
            "<d:displayname/>"
            "</d:prop>"
            "</d:propfind>"
        )
        _log.debug("PROPFIND %s (discover addressbooks)", self._config.base_url)
        resp = self._request("PROPFIND", self._config.base_url, body, depth="1")
        tree = etree.fromstring(resp.content)
        books: list[dict[str, str]] = []
        for response in tree.findall("d:response", _NS):
            restype = response.find(".//d:resourcetype/card:addressbook", _NS)
            if restype is not None:
                href = response.findtext("d:href", "", _NS)
                name = response.findtext(".//d:displayname", "", _NS)
                books.append({"href": href, "displayname": name})
        return books

    def get_ctag(self, addressbook_href: str) -> str | None:
        """Fetch the CTag for an addressbook (collection-level change tag)."""
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">'
            "<d:prop>"
            "<cs:getctag/>"
            "</d:prop>"
            "</d:propfind>"
        )
        url = self._absolute(addressbook_href)
        resp = self._request("PROPFIND", url, body, depth="0")
        tree = etree.fromstring(resp.content)
        ctag: str | None = tree.findtext(".//cs:getctag", None, _NS)  # noqa: FURB184
        return ctag

    def list_contacts(self, addressbook_href: str) -> dict[str, str]:
        """List all contact hrefs and their etags in an addressbook.

        Returns a dict mapping ``href -> etag``.
        """
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<d:propfind xmlns:d="DAV:">'
            "<d:prop>"
            "<d:getetag/>"
            "<d:resourcetype/>"
            "</d:prop>"
            "</d:propfind>"
        )
        url = self._absolute(addressbook_href)
        resp = self._request("PROPFIND", url, body, depth="1")
        tree = etree.fromstring(resp.content)
        contacts: dict[str, str] = {}
        for response in tree.findall("d:response", _NS):
            # Skip the addressbook itself (it has a resourcetype).
            restype = response.find(".//d:resourcetype/card:addressbook", _NS)
            if restype is not None:
                continue
            href = response.findtext("d:href", "", _NS)
            etag = response.findtext(".//d:getetag", "", _NS).strip('"')
            if href and href.endswith(".vcf"):
                contacts[href] = etag
        return contacts

    def fetch_contacts(self, addressbook_href: str, hrefs: list[str]) -> list[Contact]:
        """Fetch multiple contacts in a single request (multiget REPORT).

        Returns a list of ``Contact`` objects with raw vCard data.
        """
        if not hrefs:
            return []
        _log.debug("Multiget %d contact(s)", len(hrefs))
        href_xml = "".join(f"<d:href>{h}</d:href>" for h in hrefs)
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<card:addressbook-multiget xmlns:d="DAV:" '
            'xmlns:card="urn:ietf:params:xml:ns:carddav">'
            "<d:prop>"
            "<d:getetag/>"
            "<card:address-data/>"
            "</d:prop>"
            f"{href_xml}"
            "</card:addressbook-multiget>"
        )
        url = self._absolute(addressbook_href)
        resp = self._request("REPORT", url, body, depth="1")
        tree = etree.fromstring(resp.content)
        result: list[Contact] = []
        for response in tree.findall("d:response", _NS):
            href = response.findtext("d:href", "", _NS)
            etag = response.findtext(".//d:getetag", "", _NS).strip('"')
            vcard_raw = response.findtext(".//card:address-data", "", _NS)
            if href and vcard_raw:
                result.append(Contact(href=href, etag=etag, vcard_raw=vcard_raw))
        return result

    def fetch_all_contacts(self, addressbook_href: str) -> list[Contact]:
        """Fetch all contacts in an addressbook."""
        hrefs = list(self.list_contacts(addressbook_href).keys())
        return self.fetch_contacts(addressbook_href, hrefs)

    def sync(
        self,
        addressbook_href: str,
        state: SyncState,
    ) -> tuple[list[Contact], list[str], SyncState]:
        """Incremental sync: fetch only changed contacts.

        Returns ``(new_or_updated, deleted_hrefs, new_state)``. Uses ctag for
        collection-level change detection, then diffs etags to find individual changes.
        """
        ctag = self.get_ctag(addressbook_href)
        if ctag is not None and ctag == state.ctag:
            _log.debug("CTag unchanged (%s), skipping sync", ctag)
            return [], [], state
        _log.debug("CTag changed: %s → %s", state.ctag, ctag)

        current = self.list_contacts(addressbook_href)
        old = state.contacts

        # Find new or updated contacts.
        changed_hrefs: list[str] = []
        for href, etag in current.items():
            old_etag = old.get(href, {}).get("etag")
            if old_etag != etag:
                changed_hrefs.append(href)

        # Find deleted contacts.
        deleted = [h for h in old if h not in current]

        # Fetch changed contacts.
        updated = self.fetch_contacts(addressbook_href, changed_hrefs)

        # Build new state.
        new_contacts: dict[str, dict[str, str]] = {}
        for href, etag in current.items():
            new_contacts[href] = {"etag": etag}

        new_state = SyncState(
            sync_token=state.sync_token,
            ctag=ctag,
            contacts=new_contacts,
        )
        return updated, deleted, new_state

    def put_contact(self, href: str, vcard_raw: str, etag: str) -> str | None:
        """Update a contact on the server via PUT.

        Uses ``If-Match`` with the given etag for optimistic locking. Returns the new
        etag on success, or None on conflict (412).
        """
        url = self._absolute(href)
        _log.debug("PUT %s (If-Match: %s)", href, etag)
        headers = {
            "Content-Type": "text/vcard",
            "If-Match": f'"{etag}"',
        }
        resp = self._session.put(url, data=vcard_raw.encode("utf-8"), headers=headers)
        if resp.status_code == 412:
            return None
        resp.raise_for_status()
        # Baikal returns the new etag in the ETag header.
        new_etag = resp.headers.get("ETag", "").strip('"')
        return new_etag or None

    def _absolute(self, href: str) -> str:
        """Resolve a relative href to an absolute URL."""
        if href.startswith("http"):
            return href
        # Strip the path from the config URL, keep scheme+host.
        from urllib.parse import urljoin

        return urljoin(self._config.base_url + "/", href)

    def _request(
        self,
        method: str,
        url: str,
        body: str,
        depth: str = "0",
    ) -> Any:
        """Send a WebDAV request and return the response."""
        headers = {"Depth": depth}
        resp = self._session.request(
            method, url, data=body.encode("utf-8"), headers=headers
        )
        resp.raise_for_status()
        return resp

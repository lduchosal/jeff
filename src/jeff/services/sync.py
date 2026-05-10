"""Sync service — orchestrates CardDAV sync, transform, and writeback."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests

from jeff.domain.carddav import CardDAVClient, CardDAVConfig, Contact, SyncState
from jeff.domain.config import JeffConfig
from jeff.domain.transform import contact_to_markdown, parse_vcard
from jeff.domain.urlback import (
    build_profile_url,
    inject_crm_url,
    inject_gender,
    inject_related,
)
from jeff.services.triage import load_contact

# Progress callback type: (message: str) -> None
ProgressFn = Callable[[str], None]


def _noop(msg: str) -> None:
    """No-op progress callback."""


@dataclass
class SyncResult:
    """Result of a sync operation."""

    written: list[str]
    removed: list[str]
    deleted_remote: list[str]
    url_count: int
    gender_count: int
    famille_count: int = 0
    error: str = ""


def run_sync(
    cfg: JeffConfig,
    full: bool = False,
    progress: ProgressFn | None = None,
    writeback_gender: bool = False,
    writeback_famille: bool = False,
) -> SyncResult:
    """Run a full sync cycle: fetch, transform, writeback."""
    log = progress or _noop
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    state_path = base / cfg.sync_state_path
    content_dir = base / cfg.content_dir
    photo_dir = base / cfg.photo_dir

    client = CardDAVClient(
        CardDAVConfig(
            url=cfg.carddav_url,
            username=cfg.carddav_username,
            password=cfg.carddav_password,
        )
    )

    # Discover addressbook.
    log("Discovering addressbooks...")
    try:
        books = client.discover_addressbooks()
    except requests.ConnectionError:
        log("Error: no internet connection. Sync skipped.")
        return SyncResult([], [], [], 0, 0, error="no connection")
    if not books:
        return SyncResult([], [], [], 0, 0)
    addressbook_href = books[0]["href"]
    log(f"Addressbook: {books[0]['displayname']}")

    # Load or reset state.
    state = SyncState() if full else SyncState.load(state_path)

    # Sync.
    log("Fetching changes...")
    updated, deleted, new_state = client.sync(addressbook_href, state)
    log(f"Found {len(updated)} updated, {len(deleted)} deleted")

    # Transform updated contacts.
    written: list[str] = []
    for i, contact in enumerate(updated, 1):
        data = parse_vcard(contact.vcard_raw)
        log(f"Transform [{i}/{len(updated)}] {data.get('name', '?')}")
        path = contact_to_markdown(contact, content_dir, photo_dir)
        written.append(path.name)

    # Handle deleted contacts.
    removed: list[str] = []
    for href in deleted:
        old_info = state.contacts.get(href, {})
        slug = old_info.get("slug")
        if slug:
            md_path = content_dir / f"{slug}.md"
            if md_path.exists():
                md_path.unlink()
                removed.append(md_path.name)

    # Enrich state with slugs.
    for contact in updated:
        data = parse_vcard(contact.vcard_raw)
        slug = data.get("slug", "")
        if contact.href in new_state.contacts:
            new_state.contacts[contact.href]["slug"] = slug

    # Writeback: CRM URL.
    if cfg.publish_url and updated:
        log("Writing back URLs...")
    url_count = _writeback_urls(cfg, client, updated, new_state, content_dir, log)

    # Writeback: gender (only when explicitly requested — slow operation).
    gender_count = 0
    if writeback_gender:
        log("Writing back gender...")
        gender_count = _writeback_gender(client, new_state, content_dir, log)

    # Writeback: family links (only when explicitly requested — slow operation).
    famille_count = 0
    if writeback_famille:
        log("Writing back family links...")
        famille_count = _writeback_famille(client, new_state, content_dir, log)

    # Delete contacts marked as 'supprimé' from CardDAV.
    deleted_remote: list[str] = []
    slug_to_href: dict[str, str] = {}
    for href, info in new_state.contacts.items():
        s = info.get("slug", "")
        if s:
            slug_to_href[s] = href
    for md_path in sorted(content_dir.glob("*.md")):
        md_data = load_contact(md_path)
        if not md_data or md_data.get("status") != "supprimé":
            continue
        slug = md_data.get("slug", "")
        name = md_data.get("name", slug)
        del_href = slug_to_href.get(slug)
        if not del_href:
            continue
        etag = new_state.contacts[del_href].get("etag", "")
        if not etag:
            continue
        log(f"  Deleting {name} from CardDAV...")
        if client.delete_contact(del_href, etag):
            deleted_remote.append(name)
            del new_state.contacts[del_href]
            md_path.unlink()

    # Save state.
    new_state.save(state_path)

    return SyncResult(
        written=written,
        removed=removed,
        deleted_remote=deleted_remote,
        url_count=url_count,
        gender_count=gender_count,
        famille_count=famille_count,
    )


def _writeback_urls(
    cfg: JeffConfig,
    client: CardDAVClient,
    updated: list[Contact],
    new_state: SyncState,
    content_dir: Path,
    log: ProgressFn = _noop,
) -> int:
    """Write CRM profile URLs back to CardDAV."""
    if not cfg.publish_url or not updated:
        return 0
    count = 0
    for i, contact in enumerate(updated, 1):
        data = parse_vcard(contact.vcard_raw)
        slug = data.get("slug", "")
        if not slug:
            continue
        profile_url = build_profile_url(cfg.publish_url, slug)
        new_vcard = inject_crm_url(contact.vcard_raw, profile_url)
        if new_vcard is None:
            continue
        log(f"  URL [{i}/{len(updated)}] {data.get('name', '?')}")
        new_etag = client.put_contact(contact.href, new_vcard, contact.etag)
        if new_etag:
            count += 1
            if contact.href in new_state.contacts:
                new_state.contacts[contact.href]["etag"] = new_etag
    return count


def _writeback_gender(
    client: CardDAVClient,
    new_state: SyncState,
    content_dir: Path,
    log: ProgressFn = _noop,
) -> int:
    """Write gender back to CardDAV for all contacts that have it set locally.

    Iterates over all local .md files (not just updated contacts) so that running ``jeff
    genre`` followed by ``jeff sync`` pushes the gender even when no contact changed on
    the server.
    """
    if not content_dir.is_dir():
        return 0
    count = 0
    # Build href→etag lookup from state.
    slug_to_href: dict[str, str] = {}
    for href, info in new_state.contacts.items():
        s = info.get("slug", "")
        if s:
            slug_to_href[s] = href

    md_files = sorted(content_dir.glob("*.md"))
    for i, md_path in enumerate(md_files, 1):
        md_data = load_contact(md_path)
        if not md_data or not md_data.get("genre"):
            continue
        slug = md_data.get("slug", "")
        contact_href = slug_to_href.get(slug)
        if not contact_href:
            continue
        etag = new_state.contacts[contact_href].get("etag", "")
        if not etag:
            continue
        # Fetch current vCard to check if gender already set.
        contacts = client.fetch_contacts(
            contact_href.rsplit("/", 1)[0] + "/", [contact_href]
        )
        if not contacts:
            continue
        current_vcard = contacts[0].vcard_raw
        new_vcard = inject_gender(current_vcard, md_data["genre"])
        if new_vcard is None:
            continue  # Already correct.
        log(f"  Gender [{i}/{len(md_files)}] {md_data.get('name', '?')}")
        new_etag = client.put_contact(contact_href, new_vcard, contacts[0].etag)
        if new_etag:
            count += 1
            new_state.contacts[contact_href]["etag"] = new_etag
    return count


def _writeback_famille(
    client: CardDAVClient,
    new_state: SyncState,
    content_dir: Path,
    log: ProgressFn = _noop,
) -> int:
    """Write family RELATED properties back to CardDAV."""
    if not content_dir.is_dir():
        return 0
    # Build slug→href and slug→uid lookups.
    slug_to_href: dict[str, str] = {}
    slug_to_uid: dict[str, str] = {}
    for href, info in new_state.contacts.items():
        s = info.get("slug", "")
        if s:
            slug_to_href[s] = href

    # First pass: collect UIDs from all contacts.
    from jeff.services.famille import _parse_slug_list

    for md_path in sorted(content_dir.glob("*.md")):
        md_data = load_contact(md_path)
        if md_data and md_data.get("uid") and md_data.get("slug"):
            uid = str(md_data["uid"])
            if uid.startswith("urn:uuid:"):
                uid = uid[len("urn:uuid:"):]
            slug_to_uid[md_data["slug"]] = uid

    count = 0
    md_files = sorted(content_dir.glob("*.md"))
    for i, md_path in enumerate(md_files, 1):
        md_data = load_contact(md_path)
        if not md_data or md_data.get("relation") != "famille":
            continue
        slug = md_data.get("slug", "")
        contact_href = slug_to_href.get(slug)
        if not contact_href:
            continue

        # Build RELATED list from frontmatter fields.
        relations: list[tuple[str, str]] = []
        for field, rtype in [
            ("pere", "parent"), ("mere", "parent"),
            ("conjoint", "spouse"),
        ]:
            target_slug = md_data.get(field, "")
            if target_slug and target_slug in slug_to_uid:
                relations.append((rtype, slug_to_uid[target_slug]))
        for field, rtype in [
            ("enfants", "child"), ("freres_soeurs", "sibling"),
        ]:
            for target_slug in _parse_slug_list(md_data.get(field)):
                if target_slug in slug_to_uid:
                    relations.append((rtype, slug_to_uid[target_slug]))

        if not relations:
            continue

        # Fetch current vCard.
        contacts = client.fetch_contacts(
            contact_href.rsplit("/", 1)[0] + "/", [contact_href]
        )
        if not contacts:
            continue
        new_vcard = inject_related(contacts[0].vcard_raw, relations)
        if new_vcard is None:
            continue
        log(f"  Family [{i}/{len(md_files)}] {md_data.get('name', '?')}")
        new_etag = client.put_contact(
            contact_href, new_vcard, contacts[0].etag
        )
        if new_etag:
            count += 1
            new_state.contacts[contact_href]["etag"] = new_etag
    return count

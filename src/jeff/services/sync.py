"""Sync service — orchestrates CardDAV sync, transform, and writeback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jeff.carddav import CardDAVClient, CardDAVConfig, Contact, SyncState
from jeff.config import JeffConfig
from jeff.triage import load_contact
from jeff.transform import contact_to_markdown, parse_vcard
from jeff.urlback import build_profile_url, inject_crm_url, inject_gender


@dataclass
class SyncResult:
    """Result of a sync operation."""

    written: list[str]
    removed: list[str]
    url_count: int
    gender_count: int


def run_sync(cfg: JeffConfig, full: bool = False) -> SyncResult:
    """Run a full sync cycle: fetch, transform, writeback."""
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
    books = client.discover_addressbooks()
    if not books:
        return SyncResult([], [], 0, 0)
    addressbook_href = books[0]["href"]

    # Load or reset state.
    state = SyncState() if full else SyncState.load(state_path)

    # Sync.
    updated, deleted, new_state = client.sync(addressbook_href, state)

    # Transform updated contacts.
    written: list[str] = []
    for contact in updated:
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
    url_count = _writeback_urls(cfg, client, updated, new_state, content_dir)

    # Writeback: gender.
    gender_count = _writeback_gender(client, updated, new_state, content_dir)

    # Save state.
    new_state.save(state_path)

    return SyncResult(
        written=written,
        removed=removed,
        url_count=url_count,
        gender_count=gender_count,
    )


def _writeback_urls(
    cfg: JeffConfig,
    client: CardDAVClient,
    updated: list[Contact],
    new_state: SyncState,
    content_dir: Path,
) -> int:
    """Write CRM profile URLs back to CardDAV."""
    if not cfg.publish_url or not updated:
        return 0
    count = 0
    for contact in updated:
        data = parse_vcard(contact.vcard_raw)
        slug = data.get("slug", "")
        if not slug:
            continue
        profile_url = build_profile_url(cfg.publish_url, slug)
        new_vcard = inject_crm_url(contact.vcard_raw, profile_url)
        if new_vcard is None:
            continue
        new_etag = client.put_contact(contact.href, new_vcard, contact.etag)
        if new_etag:
            count += 1
            if contact.href in new_state.contacts:
                new_state.contacts[contact.href]["etag"] = new_etag
    return count


def _writeback_gender(
    client: CardDAVClient,
    updated: list[Contact],
    new_state: SyncState,
    content_dir: Path,
) -> int:
    """Write gender back to CardDAV for contacts that have it set locally."""
    if not updated:
        return 0
    count = 0
    for contact in updated:
        data = parse_vcard(contact.vcard_raw)
        slug = data.get("slug", "")
        if not slug:
            continue
        md_path = content_dir / f"{slug}.md"
        if not md_path.exists():
            continue
        md_data = load_contact(md_path)
        if not md_data or not md_data.get("genre"):
            continue
        if contact.href in new_state.contacts:
            etag = new_state.contacts[contact.href].get("etag", contact.etag)
        else:
            etag = contact.etag
        new_vcard = inject_gender(contact.vcard_raw, md_data["genre"])
        if new_vcard is None:
            continue
        new_etag = client.put_contact(contact.href, new_vcard, etag)
        if new_etag:
            count += 1
            if contact.href in new_state.contacts:
                new_state.contacts[contact.href]["etag"] = new_etag
    return count

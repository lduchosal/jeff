"""Jeff CLI — sync CardDAV contacts to Markdown and publish HTML.

Usage::

    jeff sync          # incremental sync
    jeff sync --full   # force full sync
    jeff publish       # build static HTML site
"""

from __future__ import annotations

import sys

import click

from jeff import __version__
from jeff.carddav import CardDAVClient, CardDAVConfig, SyncState
from jeff.config import load_config
from jeff.transform import contact_to_markdown, parse_vcard

from pathlib import Path


@click.group()
@click.option("--config", "config_file", help="Path to a .jeff config file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
@click.version_option(__version__, prog_name="jeff")
@click.pass_context
def cli(ctx: click.Context, config_file: str | None, verbose: bool) -> None:
    """Jeff — sync CardDAV contacts to Markdown."""
    from jeff.log import setup

    setup(verbose=verbose)
    ctx.ensure_object(dict)
    cfg = load_config(config_file)
    errors = cfg.validate()
    if errors:
        click.echo(
            f"Error: missing config fields: {', '.join(errors)}. "
            f"Create a .jeff file or set JEFF_* env vars.",
            err=True,
        )
        sys.exit(1)
    ctx.obj["cfg"] = cfg


@cli.command()
@click.option("--full", is_flag=True, help="Force full sync (ignore cached state).")
@click.pass_context
def sync(ctx: click.Context, full: bool) -> None:
    """Sync contacts from CardDAV to Markdown files."""
    cfg = ctx.obj["cfg"]

    # Resolve paths relative to .jeff file or cwd.
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
        click.echo("Error: no addressbooks found.", err=True)
        sys.exit(1)
    addressbook_href = books[0]["href"]
    click.echo(f"Addressbook: {books[0]['displayname']} ({addressbook_href})")

    # Load or reset state.
    state = SyncState() if full else SyncState.load(state_path)

    # Sync.
    updated, deleted, new_state = client.sync(addressbook_href, state)

    # Transform updated contacts.
    written: list[str] = []
    for contact in updated:
        path = contact_to_markdown(contact, content_dir, photo_dir)
        written.append(path.name)

    # Handle deleted contacts (archive by removing the .md file).
    removed: list[str] = []
    for href in deleted:
        # Try to find the slug from old state.
        old_info = state.contacts.get(href, {})
        slug = old_info.get("slug")
        if slug:
            md_path = content_dir / f"{slug}.md"
            if md_path.exists():
                md_path.unlink()
                removed.append(md_path.name)

    # Enrich state with slugs for future delete detection.
    for contact in updated:
        data = parse_vcard(contact.vcard_raw)
        slug = data.get("slug", "")
        if contact.href in new_state.contacts:
            new_state.contacts[contact.href]["slug"] = slug

    # Write CRM URL back to Baikal (if publish_url is configured).
    url_count = 0
    if cfg.publish_url and updated:
        from jeff.urlback import build_profile_url, inject_crm_url

        for contact in updated:
            data = parse_vcard(contact.vcard_raw)
            slug = data.get("slug", "")
            if not slug:
                continue
            profile_url = build_profile_url(cfg.publish_url, slug)
            new_vcard = inject_crm_url(contact.vcard_raw, profile_url)
            if new_vcard is None:
                continue  # URL already present.
            new_etag = client.put_contact(
                contact.href, new_vcard, contact.etag
            )
            if new_etag:
                url_count += 1
                # Update state with new etag (PUT changes it).
                if contact.href in new_state.contacts:
                    new_state.contacts[contact.href]["etag"] = new_etag

    # Save state.
    new_state.save(state_path)

    # Report.
    if not updated and not deleted:
        click.echo("Already up to date.")
    else:
        if written:
            click.echo(f"Written: {len(written)} contact(s)")
            for name in sorted(written):
                click.echo(f"  + {name}")
        if removed:
            click.echo(f"Removed: {len(removed)} contact(s)")
            for name in sorted(removed):
                click.echo(f"  - {name}")
        if url_count:
            click.echo(f"URL written back: {url_count} contact(s)")


@cli.command()
@click.option(
    "--output", "-o", default="public", help="Output directory (default: public)."
)
@click.pass_context
def publish(ctx: click.Context, output: str) -> None:
    """Build a static HTML site from synced Markdown contacts."""
    from jeff.publish import build_site

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    content_dir = base / cfg.content_dir
    photo_dir = base / cfg.photo_dir
    output_dir = base / output

    # Look for contact.css in doc/ui or bundled.
    css_path = base / "doc" / "ui" / "contact.css"
    if not css_path.is_file():
        css_path = None

    count = build_site(content_dir, output_dir, photo_dir, css_path)
    click.echo(f"Published {count} contact(s) to {output_dir}")

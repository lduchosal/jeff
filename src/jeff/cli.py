"""Jeff CLI — sync CardDAV contacts to Markdown and publish HTML.

Usage::

    jeff sync          # incremental sync
    jeff sync --full   # force full sync
    jeff publish       # build static HTML site
    jeff triage        # interactive contact triage
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from jeff import __version__
from jeff.carddav import CardDAVClient, CardDAVConfig, SyncState
from jeff.config import load_config
from jeff.transform import contact_to_markdown, parse_vcard


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
            new_etag = client.put_contact(contact.href, new_vcard, contact.etag)
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


@cli.command()
@click.option("--all", "show_all", is_flag=True, help="Show all contacts, including already triaged.")
@click.pass_context
def triage(ctx: click.Context, show_all: bool) -> None:
    """Interactive triage of contacts."""
    from jeff.triage import format_summary, load_contact, needs_triage, save_triage

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    content_dir = base / cfg.content_dir

    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    files = sorted(content_dir.glob("*.md"))
    contacts = []
    for f in files:
        data = load_contact(f)
        if data and data.get("name"):
            if show_all or needs_triage(data):
                contacts.append(data)

    total = len(list(content_dir.glob("*.md")))
    done = total - len([1 for f in files if (d := load_contact(f)) and needs_triage(d)])

    if not contacts:
        click.echo(f"All {total} contacts have been triaged.")
        return

    click.echo(f"\n{len(contacts)} contacts to triage ({done}/{total} done)\n")
    click.echo("Commands: a=actif  r=archivé  s=skip  q=quit")
    click.echo("After status, enter relation (a/c/f/k) and priority (h/m/b):")
    click.echo("  relation: a=ami  c=collegue  f=famille  k=connaissance")
    click.echo("  priority: h=haute  m=moyenne  b=basse")
    click.echo("Example: 'a a h' = actif, ami, haute priorité")
    click.echo("         'r' = archivé (no relation/priority needed)")
    click.echo("         's' = skip for now\n")

    relation_map = {"a": "ami", "c": "collegue", "f": "famille", "k": "connaissance"}
    priority_map = {"h": "haute", "m": "moyenne", "b": "basse"}

    triaged = 0
    for i, data in enumerate(contacts, 1):
        path = data["_path"]
        click.echo(f"── [{i}/{len(contacts)}] {'─' * 50}")
        click.echo(format_summary(data))
        click.echo()

        while True:
            raw = click.prompt("  >", default="s").strip().lower()
            if raw == "q":
                click.echo(f"\nTriaged {triaged} contact(s) this session.")
                return
            if raw == "s":
                break

            parts = raw.split()
            cmd = parts[0] if parts else ""

            if cmd == "a":
                updates = {"status": "actif"}
                if len(parts) >= 2 and parts[1] in relation_map:
                    updates["relation"] = relation_map[parts[1]]
                if len(parts) >= 3 and parts[2] in priority_map:
                    updates["priorite"] = priority_map[parts[2]]
                save_triage(path, updates)
                triaged += 1
                click.echo(f"  ✓ {data['name']} → actif")
                break
            elif cmd == "r":
                save_triage(path, {"status": "archivé"})
                triaged += 1
                click.echo(f"  ✗ {data['name']} → archivé")
                break
            else:
                click.echo("  ? a/r/s/q (ex: 'a a h', 'r', 's')")

    click.echo(f"\nTriaged {triaged} contact(s) this session.")


@cli.command()
@click.pass_context
def famille(ctx: click.Context) -> None:
    """Batch-edit family links for all famille contacts.

    Shows same-surname contacts numbered, then type e.g. '1f 2m 3w 4c 5b':
    f=father m=mother w=wife/husband c=child b=brother/sister
    """
    from jeff.triage import load_contact, save_triage

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    content_dir = base / cfg.content_dir

    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    # Load all contacts.
    all_contacts: list[dict] = []
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name"):
            all_contacts.append(data)

    # Filter famille contacts that need editing.
    famille_contacts = [
        c for c in all_contacts
        if c.get("relation") == "famille"
        and not c.get("pere") and not c.get("mere")
        and not c.get("conjoint") and not c.get("enfants")
        and not c.get("freres_soeurs")
    ]

    if not famille_contacts:
        click.echo("All famille contacts have links set.")
        return

    # Build surname index.
    by_surname: dict[str, list[dict]] = {}
    for c in all_contacts:
        surname = (c.get("name_family") or "").strip().lower()
        if surname:
            by_surname.setdefault(surname, []).append(c)

    role_map = {
        "f": "pere", "m": "mere", "w": "conjoint",
        "c": "enfants", "b": "freres_soeurs",
    }

    click.echo(f"\n{len(famille_contacts)} famille contacts to edit")
    click.echo("Codes: f=father m=mother w=wife/husband c=child b=brother/sister")
    click.echo("Example: 1f 2m 3w 4c    Enter=skip  q=quit\n")

    edited = 0
    for idx, contact in enumerate(famille_contacts, 1):
        surname = (contact.get("name_family") or "").strip().lower()
        slug = contact.get("slug", "")
        same_family = [
            c for c in by_surname.get(surname, [])
            if c.get("slug") != slug
        ]

        click.echo(f"── [{idx}/{len(famille_contacts)}] {contact.get('name')} ──")
        if same_family:
            for n, c in enumerate(same_family, 1):
                click.echo(f"    {n}. {c.get('name')}")
        else:
            click.echo("    (no same-surname contacts found)")
        click.echo()

        raw = click.prompt("  >", default="").strip().lower()
        if raw == "q":
            break
        if not raw:
            continue

        # Parse tokens like "1f 2m 3w 4c 5b"
        updates: dict[str, str] = {}
        children: list[str] = []
        siblings: list[str] = []
        for token in raw.split():
            if len(token) < 2:
                continue
            num_str = token[:-1]
            code = token[-1]
            if not num_str.isdigit() or code not in role_map:
                click.echo(f"    ? invalid: {token}")
                continue
            n = int(num_str)
            if n < 1 or n > len(same_family):
                click.echo(f"    ? out of range: {token}")
                continue
            target_slug = same_family[n - 1].get("slug", "")
            role = role_map[code]
            if role == "enfants":
                children.append(target_slug)
            elif role == "freres_soeurs":
                siblings.append(target_slug)
            else:
                updates[role] = target_slug

        if children:
            updates["enfants"] = f"[{', '.join(children)}]"
        if siblings:
            updates["freres_soeurs"] = f"[{', '.join(siblings)}]"

        if updates:
            save_triage(contact["_path"], updates)
            summary = " ".join(f"{k}={v}" for k, v in updates.items())
            click.echo(f"  ✓ {summary}")
            edited += 1

    click.echo(f"\nEdited {edited} contact(s).")

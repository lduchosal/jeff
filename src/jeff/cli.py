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
    click.echo("After status: relation (a/c/f/k), priority (h/m/b), genre (H/F):")
    click.echo("  relation: a=ami  c=collegue  f=famille  k=connaissance")
    click.echo("  priority: h=haute  m=moyenne  b=basse")
    click.echo("  genre:    H=homme  F=femme")
    click.echo("Example: 'a f h H' = actif, famille, haute, homme")
    click.echo("         'r' = archivé")
    click.echo("         's' = skip\n")

    relation_map = {"a": "ami", "c": "collegue", "f": "famille", "k": "connaissance"}
    genre_map = {"h": "homme", "f": "femme"}
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
                if len(parts) >= 4 and parts[3].lower() in genre_map:
                    updates["genre"] = genre_map[parts[3].lower()]
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


def _reciprocal_updates(
    role: str, source_slug: str, source: dict, target: dict,
) -> dict[str, str]:
    """Compute the reciprocal family link update for the target contact.

    Uses source genre to pick pere vs mere when the reciprocal of 'enfants'
    is needed (i.e. source says target is their child, so target gets
    pere or mere pointing back to source).
    """
    reciprocal: dict[str, str] = {
        "pere": "enfants",
        "mere": "enfants",
        "conjoint": "conjoint",
        "freres_soeurs": "freres_soeurs",
    }
    if role == "enfants":
        # Source is the parent — use source genre to decide pere/mere.
        genre = (source.get("genre") or "").lower()
        rev = "mere" if genre == "femme" else "pere"
    else:
        rev = reciprocal.get(role, "")
    if not rev:
        return {}
    if rev in ("enfants", "freres_soeurs"):
        existing = target.get(rev) or []
        if isinstance(existing, str):
            # Parse "[slug1, slug2]" string back to list.
            stripped = existing.strip("[] ")
            existing = [s.strip() for s in stripped.split(",") if s.strip()]
        if source_slug not in existing:
            existing.append(source_slug)
        return {rev: f"[{', '.join(existing)}]"}
    return {rev: source_slug}


def _show_existing_links(data: dict) -> None:
    """Display current family links for a contact."""
    links = []
    if data.get("pere"):
        links.append(f"père: {data['pere']}")
    if data.get("mere"):
        links.append(f"mère: {data['mere']}")
    if data.get("conjoint"):
        links.append(f"conjoint: {data['conjoint']}")
    if data.get("freres_soeurs"):
        fs = data["freres_soeurs"]
        if isinstance(fs, list):
            links.append(f"frères/sœurs: {', '.join(fs)}")
    if data.get("enfants"):
        enf = data["enfants"]
        if isinstance(enf, list):
            links.append(f"enfants: {', '.join(enf)}")
    if links:
        for lnk in links:
            click.echo(f"    ↳ {lnk}")
    else:
        click.echo("    ↳ (aucun lien)")


@cli.command()
@click.pass_context
def famille(ctx: click.Context) -> None:
    """Batch-edit family links for all famille contacts."""
    from jeff.triage import load_contact, save_triage

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    content_dir = base / cfg.content_dir

    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    # Load all contacts, indexed by slug for reciprocal writes.
    all_contacts: list[dict] = []
    by_slug: dict[str, dict] = {}
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name"):
            all_contacts.append(data)
            by_slug[data.get("slug", "")] = data

    # Filter famille contacts. Show all that have relation=famille,
    # even if they already received reciprocal links.
    famille_contacts = [
        c for c in all_contacts if c.get("relation") == "famille"
    ]

    if not famille_contacts:
        click.echo("No famille contacts found.")
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

    click.echo(f"\n{len(famille_contacts)} famille contacts to edit\n")

    edited = 0
    for idx, contact in enumerate(famille_contacts, 1):
        surname = (contact.get("name_family") or "").strip().lower()
        slug = contact.get("slug", "")
        candidates = [
            c for c in by_surname.get(surname, [])
            if c.get("slug") != slug
        ]

        genre_label = f" ({contact.get('genre')})" if contact.get("genre") else ""
        click.echo(f"── [{idx}/{len(famille_contacts)}] {contact.get('name')}{genre_label} ──")
        _show_existing_links(contact)
        click.echo()
        if candidates:
            for n, c in enumerate(candidates, 1):
                g = f" ({c.get('genre')})" if c.get("genre") else ""
                click.echo(f"    {n}. {c.get('name')}{g}")
        else:
            click.echo("    (aucun contact même nom)")
        click.echo()
        click.echo("    f=père m=mère w=conjoint c=enfant b=frère/sœur")
        click.echo("    ?texte=chercher  Enter=skip  q=quit")
        click.echo()

        while True:
            raw = click.prompt("  >", default="").strip()
            if raw.lower() == "q":
                click.echo(f"\nEdited {edited} contact(s).")
                return
            if not raw:
                break

            # Search mode: ?query
            if raw.startswith("?"):
                query = raw[1:].strip().lower()
                if not query:
                    continue
                candidates = [
                    c for c in all_contacts
                    if c.get("slug") != slug
                    and query in (c.get("name") or "").lower()
                ]
                if candidates:
                    for n, c in enumerate(candidates, 1):
                        click.echo(f"    {n}. {c.get('name')}")
                else:
                    click.echo(f"    aucun résultat pour '{query}'")
                click.echo()
                continue

            # Parse tokens like "1f 2m 3w 4c 5b"
            updates: dict[str, str] = {}
            children: list[str] = []
            siblings: list[str] = []
            reciprocals: list[tuple[dict, dict[str, str]]] = []
            ok = True
            for token in raw.lower().split():
                if len(token) < 2:
                    ok = False
                    continue
                num_str = token[:-1]
                code = token[-1]
                if not num_str.isdigit() or code not in role_map:
                    click.echo(f"    ? invalide: {token}")
                    ok = False
                    continue
                n = int(num_str)
                if n < 1 or n > len(candidates):
                    click.echo(f"    ? hors limite: {token}")
                    ok = False
                    continue
                target = candidates[n - 1]
                target_slug = target.get("slug", "")
                role = role_map[code]
                if role == "enfants":
                    children.append(target_slug)
                elif role == "freres_soeurs":
                    siblings.append(target_slug)
                else:
                    updates[role] = target_slug
                # Prepare reciprocal update.
                rev = _reciprocal_updates(role, slug, contact, target)
                if rev:
                    reciprocals.append((target, rev))

            if not ok and not updates and not children and not siblings:
                continue

            if children:
                existing_c = contact.get("enfants") or []
                if isinstance(existing_c, str):
                    existing_c = [s.strip() for s in existing_c.strip("[] ").split(",") if s.strip()]
                for c in children:
                    if c not in existing_c:
                        existing_c.append(c)
                updates["enfants"] = f"[{', '.join(existing_c)}]"
            if siblings:
                existing_s = contact.get("freres_soeurs") or []
                if isinstance(existing_s, str):
                    existing_s = [s.strip() for s in existing_s.strip("[] ").split(",") if s.strip()]
                for s in siblings:
                    if s not in existing_s:
                        existing_s.append(s)
                updates["freres_soeurs"] = f"[{', '.join(existing_s)}]"

            if updates:
                # Save on current contact and update in-memory data.
                save_triage(contact["_path"], updates)
                for k, v in updates.items():
                    contact[k] = v
                summary = " ".join(f"{k}={v}" for k, v in updates.items())
                click.echo(f"  ✓ {contact.get('name')}: {summary}")
                # Save reciprocals and update in-memory data.
                for target, rev_updates in reciprocals:
                    target_path = target.get("_path")
                    if target_path:
                        save_triage(target_path, rev_updates)
                        for k, v in rev_updates.items():
                            target[k] = v
                        rev_summary = " ".join(
                            f"{k}={v}" for k, v in rev_updates.items()
                        )
                        click.echo(
                            f"  ↔ {target.get('name')}: {rev_summary}"
                        )
                edited += 1
            break

    click.echo(f"\nEdited {edited} contact(s).")

"""Jeff CLI — sync CardDAV contacts to Markdown and publish HTML.

Usage::

    jeff sync          # incremental sync
    jeff sync --full   # force full sync
    jeff publish       # build static HTML site
    jeff triage        # interactive contact triage
    jeff genre         # set gender on contacts
    jeff famille       # batch-edit family links
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from jeff import __version__
from jeff.config import load_config


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
    from jeff.services.sync import run_sync

    cfg = ctx.obj["cfg"]
    result = run_sync(cfg, full=full)

    if not result.written and not result.removed:
        click.echo("Already up to date.")
    else:
        if result.written:
            click.echo(f"Written: {len(result.written)} contact(s)")
            for name in sorted(result.written):
                click.echo(f"  + {name}")
        if result.removed:
            click.echo(f"Removed: {len(result.removed)} contact(s)")
            for name in sorted(result.removed):
                click.echo(f"  - {name}")
        if result.url_count:
            click.echo(f"URL written back: {result.url_count} contact(s)")
        if result.gender_count:
            click.echo(f"Gender written back: {result.gender_count} contact(s)")


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
    priority_map = {"h": "haute", "m": "moyenne", "b": "basse"}
    genre_map = {"h": "homme", "f": "femme"}

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
                click.echo("  ? a/r/s/q (ex: 'a f h H', 'r', 's')")

    click.echo(f"\nTriaged {triaged} contact(s) this session.")


@cli.command()
@click.pass_context
def genre(ctx: click.Context) -> None:
    """Assign gender (H/F) on all contacts that don't have one yet."""
    from jeff.triage import load_contact, save_triage

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    content_dir = base / cfg.content_dir

    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    contacts = []
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name") and not data.get("genre"):
            contacts.append(data)

    if not contacts:
        click.echo("All contacts have a genre set.")
        return

    click.echo(f"\n{len(contacts)} contacts without genre")
    click.echo("H=homme  F=femme  Enter=skip  q=quit\n")

    edited = 0
    for i, data in enumerate(contacts, 1):
        raw = click.prompt(
            f"  [{i}/{len(contacts)}] {data.get('name')}",
            default="",
            show_default=False,
        ).strip().lower()
        if raw == "q":
            break
        if raw == "h":
            save_triage(data["_path"], {"genre": "homme"})
            edited += 1
        elif raw == "f":
            save_triage(data["_path"], {"genre": "femme"})
            edited += 1

    click.echo(f"\nSet genre on {edited} contact(s).")


@cli.command()
@click.pass_context
def famille(ctx: click.Context) -> None:
    """Batch-edit family links for all famille contacts."""
    from jeff.services.famille import (
        format_existing_links,
        merge_list_field,
        reciprocal_updates,
    )
    from jeff.triage import load_contact, save_triage

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    content_dir = base / cfg.content_dir

    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    # Load all contacts.
    all_contacts: list[dict] = []
    by_slug: dict[str, dict] = {}
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name"):
            all_contacts.append(data)
            by_slug[data.get("slug", "")] = data

    # All famille contacts.
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

    click.echo(f"\n{len(famille_contacts)} famille contacts\n")

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
        links = format_existing_links(contact)
        if links:
            for lnk in links:
                click.echo(f"    ↳ {lnk}")
        else:
            click.echo("    ↳ (aucun lien)")
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

            # Search mode.
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
                        g = f" ({c.get('genre')})" if c.get("genre") else ""
                        click.echo(f"    {n}. {c.get('name')}{g}")
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
                rev = reciprocal_updates(role, slug, contact, target)
                if rev:
                    reciprocals.append((target, rev))

            if not ok and not updates and not children and not siblings:
                continue

            if children:
                updates["enfants"] = merge_list_field(contact, "enfants", children)
            if siblings:
                updates["freres_soeurs"] = merge_list_field(contact, "freres_soeurs", siblings)

            if updates:
                save_triage(contact["_path"], updates)
                for k, v in updates.items():
                    contact[k] = v
                summary = " ".join(f"{k}={v}" for k, v in updates.items())
                click.echo(f"  ✓ {contact.get('name')}: {summary}")
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

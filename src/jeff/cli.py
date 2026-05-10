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
from jeff.domain.config import load_config


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


def _content_dir(ctx: click.Context) -> Path:
    """Resolve the content directory from config."""
    cfg = ctx.obj["cfg"]
    base: Path = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    result: Path = base / cfg.content_dir
    return result


@cli.command()
@click.option("--full", is_flag=True, help="Force full sync (ignore cached state).")
@click.option("--writeback-gender", is_flag=True, help="Push gender to CardDAV (slow).")
@click.option("--writeback-famille", is_flag=True, help="Push family links to CardDAV (slow).")
@click.pass_context
def sync(ctx: click.Context, full: bool, writeback_gender: bool, writeback_famille: bool) -> None:
    """Sync contacts from CardDAV to Markdown files."""
    from jeff.services.sync import run_sync

    result = run_sync(
        ctx.obj["cfg"],
        full=full,
        progress=click.echo,
        writeback_gender=writeback_gender,
        writeback_famille=writeback_famille,
    )
    if result.error:
        sys.exit(1)
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
        if result.famille_count:
            click.echo(f"Family links written back: {result.famille_count} contact(s)")
        if result.deleted_remote:
            click.echo(f"Deleted from CardDAV: {len(result.deleted_remote)} contact(s)")
            for name in sorted(result.deleted_remote):
                click.echo(f"  ✗ {name}")


@cli.command()
@click.option(
    "--output", "-o", default="public", help="Output directory (default: public)."
)
@click.pass_context
def publish(ctx: click.Context, output: str) -> None:
    """Build a static HTML site from synced Markdown contacts."""
    from jeff.services.publish import build_site

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    output_dir = base / output
    photo_dir = base / cfg.photo_dir
    css_path = base / "doc" / "ui" / "contact.css"
    if not css_path.is_file():
        css_path = None
    count = build_site(_content_dir(ctx), output_dir, photo_dir, css_path)
    click.echo(f"Published {count} contact(s) to {output_dir}")


@cli.command()
@click.pass_context
def check(ctx: click.Context) -> None:
    """Check for duplicate contacts (same UID) and propose cleanup."""
    from jeff.services.duplicates import find_duplicates, remove_duplicate

    content_dir = _content_dir(ctx)
    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    dupes = find_duplicates(content_dir)
    if not dupes:
        click.echo("No duplicates found.")
        return

    click.echo(f"\n{len(dupes)} duplicate UID(s) found\n")
    click.echo("f=fix (keep newest, delete others)  s=skip  q=quit\n")
    fixed = 0
    for i, dupe in enumerate(dupes, 1):
        click.echo(f"── [{i}/{len(dupes)}] UID: {dupe.uid} ──")
        click.echo(f"  Keep: {dupe.recommended.get('name')} ({dupe.recommended['_path'].name})")
        for old in dupe.to_remove:
            click.echo(f"  Delete: {old.get('name')} ({old['_path'].name})")
        click.echo()
        raw = click.prompt("  >", default="f").strip().lower()
        if raw == "q":
            break
        if raw == "f":
            for old in dupe.to_remove:
                remove_duplicate(old)
                click.echo(f"    ✗ deleted {old['_path'].name}")
            fixed += 1
    click.echo(f"\nFixed {fixed} duplicate(s).")


@cli.command()
@click.option("--full", is_flag=True, help="Force full sync.")
@click.option(
    "--output", "-o", default="public", help="Output directory (default: public)."
)
@click.pass_context
def cron(ctx: click.Context, full: bool, output: str) -> None:
    """Daily cron job: sync + birthdays + publish."""
    from jeff.services.birthday import find_birthdays, record_birthday_exchange
    from jeff.services.publish import build_site
    from jeff.services.sync import run_sync

    cfg = ctx.obj["cfg"]
    base = cfg.jeff_file.parent if cfg.jeff_file else Path.cwd()
    content_dir = _content_dir(ctx)

    # 1. Sync (continues on network error — local data still valid).
    click.echo("── Sync ──")
    result = run_sync(cfg, full=full, progress=click.echo)
    if not result.error:
        if result.written:
            click.echo(f"Written: {len(result.written)} contact(s)")
        if result.removed:
            click.echo(f"Removed: {len(result.removed)} contact(s)")
        if not result.written and not result.removed:
            click.echo("Already up to date.")

    # 2. Birthdays.
    click.echo("\n── Birthdays ──")
    birthdays = find_birthdays(content_dir)
    if birthdays:
        for data in birthdays:
            recorded = record_birthday_exchange(data)
            status = "recorded" if recorded else "already sent"
            click.echo(f"  🎂 {data.get('name')} ({status})")
    else:
        click.echo("  No birthdays today.")

    # 3. Publish.
    click.echo("\n── Publish ──")
    output_dir = base / output
    photo_dir = base / cfg.photo_dir
    css_path = base / "doc" / "ui" / "contact.css"
    if not css_path.is_file():
        css_path = None
    count = build_site(content_dir, output_dir, photo_dir, css_path)
    click.echo(f"Published {count} contact(s) to {output_dir}")


@cli.command()
@click.option("--all", "show_all", is_flag=True, help="Include already triaged.")
@click.pass_context
def triage(ctx: click.Context, show_all: bool) -> None:
    """Interactive triage of contacts."""
    from jeff.services.triage import (
        format_summary,
        load_contact,
        needs_triage,
        save_triage,
    )

    content_dir = _content_dir(ctx)
    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    files = sorted(content_dir.glob("*.md"))
    contacts = [
        d
        for f in files
        if (d := load_contact(f)) and d.get("name") and (show_all or needs_triage(d))
    ]
    total = len(files)
    done = total - sum(1 for f in files if (d := load_contact(f)) and needs_triage(d))

    if not contacts:
        click.echo(f"All {total} contacts have been triaged.")
        return

    click.echo(f"\n{len(contacts)} to triage ({done}/{total} done)\n")
    click.echo("  a=actif r=archivé s=skip q=quit")
    click.echo("  Format: a <relation> <priority> <genre>")
    click.echo("  relation: a=ami c=collegue f=famille k=connaissance")
    click.echo("  priority: h=haute m=moyenne b=basse")
    click.echo("  genre: H=homme F=femme N=none")
    click.echo("  Ex: 'a f h H'  'r'  's'\n")

    rel = {"a": "ami", "c": "collegue", "f": "famille", "k": "connaissance"}
    pri = {"h": "haute", "m": "moyenne", "b": "basse"}
    gen = {"h": "homme", "f": "femme"}
    triaged = 0

    for i, data in enumerate(contacts, 1):
        click.echo(f"── [{i}/{len(contacts)}] {'─' * 50}")
        click.echo(format_summary(data))
        click.echo()
        while True:
            raw = click.prompt("  >", default="s").strip().lower()
            if raw == "q":
                click.echo(f"\nTriaged {triaged} contact(s).")
                return
            if raw == "s":
                break
            parts = raw.split()
            if parts[0] == "a":
                updates: dict[str, str] = {"status": "actif", "delete": "false"}
                if len(parts) >= 2 and parts[1] in rel:
                    updates["relation"] = rel[parts[1]]
                if len(parts) >= 3 and parts[2] in pri:
                    updates["priorite"] = pri[parts[2]]
                if len(parts) >= 4 and parts[3] in gen:
                    updates["genre"] = gen[parts[3]]
                save_triage(data["_path"], updates)
                triaged += 1
                click.echo(f"  ✓ {data['name']} → actif")
                break
            if parts[0] == "r":
                save_triage(data["_path"], {"status": "archivé"})
                triaged += 1
                click.echo(f"  ✗ {data['name']} → archivé")
                break
            click.echo("  ? a/r/s/q")
    click.echo(f"\nTriaged {triaged} contact(s).")


@cli.command()
@click.pass_context
def genre(ctx: click.Context) -> None:
    """Assign gender (H/F) on contacts without one."""
    from jeff.services.genre import apply_genre, load_contacts_without_genre

    content_dir = _content_dir(ctx)
    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    contacts = load_contacts_without_genre(content_dir)
    if not contacts:
        click.echo("All contacts have a genre set.")
        return

    click.echo(f"\n{len(contacts)} contacts without genre")
    click.echo("H=homme  F=femme  N=none (entreprise)  Enter=skip  q=quit\n")
    edited = 0
    for i, data in enumerate(contacts, 1):
        raw = (
            click.prompt(
                f"  [{i}/{len(contacts)}] {data.get('name')}",
                default="",
                show_default=False,
            )
            .strip()
            .lower()
        )
        if raw == "q":
            break
        if apply_genre(data, raw):
            edited += 1
    click.echo(f"\nSet genre on {edited} contact(s).")


@cli.command(name="delete")
@click.pass_context
def delete_cmd(ctx: click.Context) -> None:
    """Mark contacts for deletion, then confirm."""
    from jeff.services.triage import format_summary, load_contact, save_triage

    content_dir = _content_dir(ctx)
    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    # Load contacts with delete field empty (not yet decided).
    contacts = []
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name") and not data.get("delete"):
            contacts.append(data)

    if not contacts:
        click.echo("No contacts to review for deletion.")
        return

    click.echo(f"\n{len(contacts)} contacts to review")
    click.echo("d=delete  Enter=skip  q=quit\n")

    marked: list[dict] = []
    for i, data in enumerate(contacts, 1):
        click.echo(f"── [{i}/{len(contacts)}] {'─' * 50}")
        click.echo(format_summary(data))
        click.echo()
        raw = click.prompt("  d=delete  Enter=skip  q=quit >", default="", show_default=False).strip().lower()
        if raw == "q":
            break
        if raw == "d":
            marked.append(data)
            click.echo("    ✗ marked for deletion")
        else:
            # Skip = keep, mark as delete: false so we don't ask again.
            save_triage(data["_path"], {"delete": "false"})

    if not marked:
        click.echo("\nNo contacts marked.")
        return

    # Confirmation.
    click.echo(f"\n{len(marked)} contacts marked for deletion:")
    for data in marked:
        click.echo(f"  ✗ {data.get('name')}")
    confirm = click.prompt("\nConfirm? (y/n)", default="n").strip().lower()
    if confirm != "y":
        click.echo("Cancelled.")
        return

    for data in marked:
        save_triage(data["_path"], {"delete": "true"})
    click.echo(f"\n{len(marked)} contact(s) marked for deletion.")
    click.echo("Next jeff sync will delete them from CardDAV.")


@cli.command()
@click.option("--check", is_flag=True, help="Check & fix bidirectional consistency.")
@click.argument("query", required=False, default=None)
@click.pass_context
def famille(ctx: click.Context, check: bool, query: str | None) -> None:
    """Batch-edit family links, or --check consistency.

    Optionally pass a name to filter: jeff famille edmond
    """
    from jeff.services.famille import (
        apply_famille_updates,
        apply_fix,
        check_family_consistency,
        format_existing_links,
        load_famille_context,
        parse_tokens,
        same_surname_candidates,
        search_contacts,
    )

    content_dir = _content_dir(ctx)
    if not content_dir.is_dir():
        click.echo("No contacts found.", err=True)
        sys.exit(1)

    fctx = load_famille_context(content_dir)

    # Filter by query if provided — search ALL contacts, not just famille.
    if query:
        q = query.lower()
        fctx.famille_contacts = [
            c for c in fctx.all_contacts
            if q in (c.get("name") or "").lower() or q in (c.get("slug") or "").lower()
        ]

    if not fctx.famille_contacts:
        click.echo("No famille contacts found." if not query else f"No match for '{query}'.")
        return

    # --check mode: verify and fix consistency.
    if check:
        issues = check_family_consistency(fctx)
        if not issues:
            click.echo("All family links are consistent.")
            return
        by_slug = {c.get("slug", ""): c for c in fctx.all_contacts}
        click.echo(f"\n{len(issues)} inconsistencies found\n")
        click.echo("f=fix  s=skip  q=quit\n")
        fixed = 0
        for i, issue in enumerate(issues, 1):
            click.echo(f"  [{i}/{len(issues)}] {issue.message}")
            click.echo(
                f"    fix: {issue.fix_contact} → {issue.fix_field}={issue.fix_value}"
            )
            raw = click.prompt("    >", default="f").strip().lower()
            if raw == "q":
                break
            if raw == "f":
                result = apply_fix(issue, by_slug)
                if result:
                    click.echo(f"    {result}")
                    fixed += 1
        click.echo(f"\nFixed {fixed} inconsistencies.")
        return

    click.echo(f"\n{len(fctx.famille_contacts)} famille contacts\n")
    edited = 0

    for idx, contact in enumerate(fctx.famille_contacts, 1):
        candidates = same_surname_candidates(fctx, contact)
        g = f" ({contact.get('genre')})" if contact.get("genre") else ""
        click.echo(
            f"── [{idx}/{len(fctx.famille_contacts)}] {contact.get('name')}{g} ──"
        )
        links = format_existing_links(contact)
        for lnk in links or ["(aucun lien)"]:
            click.echo(f"    ↳ {lnk}")
        click.echo()
        if candidates:
            for n, c in enumerate(candidates, 1):
                cg = f" ({c.get('genre')})" if c.get("genre") else ""
                click.echo(f"    {n}. {c.get('name')}{cg}")
        else:
            click.echo("    (aucun contact même nom)")
        click.echo("    f=père m=mère w=conjoint c=enfant b=frère/sœur")
        click.echo("    ?texte=chercher  Enter=skip  q=quit\n")

        while True:
            raw = click.prompt("  >", default="").strip()
            if raw.lower() == "q":
                click.echo(f"\nEdited {edited} contact(s).")
                return
            if not raw:
                break
            if raw.startswith("?"):
                query = raw[1:].strip()
                if not query:
                    continue
                candidates = search_contacts(fctx, query, contact.get("slug", ""))
                for n, c in enumerate(candidates, 1):
                    cg = f" ({c.get('genre')})" if c.get("genre") else ""
                    click.echo(f"    {n}. {c.get('name')}{cg}")
                if not candidates:
                    click.echo(f"    aucun résultat pour '{query}'")
                click.echo()
                continue

            parsed = parse_tokens(raw, candidates, contact)
            for err in parsed.errors:
                click.echo(f"    ? {err}")
            if not parsed.updates and parsed.errors:
                continue
            lines = apply_famille_updates(contact, parsed)
            for line in lines:
                click.echo(f"  {line}")
            if lines:
                edited += 1
            break

    click.echo(f"\nEdited {edited} contact(s).")

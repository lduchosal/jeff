"""Build static HTML site from Markdown contact files.

Reads ``.md`` files with YAML frontmatter from ``content_dir``, renders them through
Jinja2 templates, and writes the result to ``output_dir``.
"""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader

from jeff.log import get_logger
from jeff.services.triage import iter_contact_files

_log = get_logger("publish")


def _parse_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a Markdown file.

    Returns the frontmatter as a dict. Ignores body content after the closing ``---``.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    # Find the closing --- on its own line.
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            yaml_text = "\n".join(lines[1:i])
            try:
                return yaml.safe_load(yaml_text) or {}
            except yaml.YAMLError:
                _log.warning("Corrupt frontmatter in %s, skipping", path.name)
                return {}
    return {}


_PRIORITY_ORDER = {"haute": 0, "moyenne": 1, "basse": 2, "": 3}


def _load_contacts(content_dir: Path) -> list[dict[str, Any]]:
    """Load active contact .md files, sorted by priority then name."""
    contacts: list[dict[str, Any]] = []
    if not content_dir.is_dir():
        return contacts
    for md in iter_contact_files(content_dir):
        data = _parse_frontmatter(md)
        if not data.get("name"):
            continue
        # Skip archived contacts.
        if data.get("status") == "archivé":
            continue
        contacts.append(data)
    contacts.sort(
        key=lambda c: (
            _PRIORITY_ORDER.get(c.get("priorite", ""), 3),
            c.get("name", ""),
        )
    )
    return contacts


def build_site(
    content_dir: Path,
    output_dir: Path,
    photo_dir: Path | None = None,
    css_path: Path | None = None,
) -> int:
    """Build the static HTML site.

    Parameters
    ----------
    content_dir:
        Directory containing ``.md`` contact files.
    output_dir:
        Directory to write the HTML output to.
    photo_dir:
        Directory containing contact photos. Copied to output.
    css_path:
        Path to ``contact.css``. If None, uses the bundled one.

    Returns
    -------
    int
        Number of contact pages generated.
    """
    contacts = _load_contacts(content_dir)
    _log.debug("Loaded %d contact(s) from %s", len(contacts), content_dir)

    # Set up Jinja2 with bundled templates.
    from urllib.parse import quote

    template_dir = resources.files("jeff").joinpath("templates")
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
    )
    env.filters["whatsapp_encode"] = lambda s: quote(str(s), safe="")
    contact_tpl = env.get_template("contact.html")
    index_tpl = env.get_template("index.html")

    # Create output dirs.
    output_dir.mkdir(parents=True, exist_ok=True)
    contacts_out = output_dir / "contacts"
    contacts_out.mkdir(exist_ok=True)
    css_out = output_dir / "css"
    css_out.mkdir(exist_ok=True)

    # Copy CSS: user-provided > bundled in package > empty placeholder.
    if css_path and css_path.is_file():
        shutil.copy2(css_path, css_out / "contact.css")
    else:
        bundled_css = resources.files("jeff").joinpath("static", "contact.css")
        if hasattr(bundled_css, "is_file") and bundled_css.is_file():
            shutil.copy2(str(bundled_css), css_out / "contact.css")
        else:
            (css_out / "contact.css").write_text("/* no css found */", encoding="utf-8")

    # Copy bundled fonts CSS and font files.
    static_dir = resources.files("jeff").joinpath("static")
    fonts_css = static_dir.joinpath("fonts.css")
    if hasattr(fonts_css, "is_file") and fonts_css.is_file():
        shutil.copy2(str(fonts_css), css_out / "fonts.css")
    fonts_src = static_dir.joinpath("fonts")
    if hasattr(fonts_src, "is_dir") and fonts_src.is_dir():
        fonts_out = css_out / "fonts"
        if fonts_out.exists():
            shutil.rmtree(fonts_out)
        shutil.copytree(str(fonts_src), fonts_out)

    # Copy photos.
    photos_out = output_dir / "photos"
    if photo_dir and photo_dir.is_dir():
        if photos_out.exists():
            shutil.rmtree(photos_out)
        shutil.copytree(photo_dir, photos_out)

    # Detect today's birthdays (before rendering so contact pages know).
    from datetime import date

    today = date.today()
    today_str = f"{today.month:02d}-{today.day:02d}"
    birthdays: list[_DotDict] = []
    for c in contacts:
        bday = c.get("birthday")
        if not bday:
            continue
        bday_s = str(bday)
        if len(bday_s) >= 10:
            bday_md = bday_s[5:10]
        elif len(bday_s) == 5:
            bday_md = bday_s
        else:
            continue
        if bday_md == today_str:
            birthdays.append(_DotDict(c))

    bday_msg = (
        "Je vois que c'est une journ\u00e9e sp\u00e9ciale pour toi, "
        "je te souhaite un joyeux anniversaire et une journ\u00e9e "
        "remplie de joies et de belles attentions. "
        "\U0001f618\U0001f389\U0001f38a\U0001f381\U0001f382\U0001f308"
    )
    birthday_slugs = {c.get("slug") for c in birthdays}

    # Render contact pages (and enrich with computed fields).
    enriched: list[_DotDict] = []
    for contact in contacts:
        dc = _DotDict(contact)
        dc["is_birthday"] = dc.get("slug") in birthday_slugs
        dc["birthday_message"] = bday_msg if dc["is_birthday"] else ""
        # Compute phone_cell at render time from phones list if not in frontmatter.
        if not dc.get("phone_cell") and dc.get("phones"):
            phones = dc["phones"]
            cell = next((p for p in phones if p.get("type") == "cell"), None)
            pref = next((p for p in phones if p.get("pref")), phones[0])
            dc["phone_cell"] = (cell or pref).get("number", "")
        # Compute zodiac sign if not in frontmatter.
        if not dc.get("signe") and dc.get("birthday"):
            from contextlib import suppress

            from jeff.domain.transform import zodiac_sign

            bday_s = str(dc["birthday"])
            with suppress(IndexError, ValueError):
                parts = bday_s.split("-")
                name, _ = zodiac_sign(int(parts[1]), int(parts[2]))
                dc["signe"] = name
        # Load interactions from the contact's folder.
        slug = contact.get("slug", "contact")
        contact_dir = content_dir / slug
        interactions: list[_DotDict] = []
        if contact_dir.is_dir():
            from jeff.services.note import list_interactions

            for inter in list_interactions(contact_dir):
                interactions.append(_DotDict(inter))
        dc["interactions"] = interactions

        # Compute recent contact indicator from interactions.
        dc["contact_recency"] = ""
        if interactions:
            latest = interactions[0].get("date")
            if latest:
                latest_str = str(latest)
                from contextlib import suppress

                with suppress(ValueError):
                    latest_date = today.__class__.fromisoformat(latest_str)
                    days = (today - latest_date).days
                    if days <= 10:
                        dc["contact_recency"] = "recent"
                    elif days <= 60:
                        dc["contact_recency"] = "medium"
                    elif days <= 180:
                        dc["contact_recency"] = "old"
                    # > 1 year: no dot

        html = contact_tpl.render(contact=dc)
        _log.debug("Render %s.html", slug)
        (contacts_out / f"{slug}.html").write_text(html, encoding="utf-8")
        enriched.append(dc)

    # Group enriched contacts by relation for the dashboard.
    groups: dict[str, list[_DotDict]] = {}
    for c in enriched:
        rel = c.get("relation") or "autre"
        groups.setdefault(rel, []).append(c)

    # Stats for the dashboard.
    by_priority: dict[str, int] = {}
    for c in contacts:
        p = c.get("priorite") or "non définie"
        by_priority[p] = by_priority.get(p, 0) + 1
    stats = {
        "total": len(contacts),
        "by_relation": {rel: len(lst) for rel, lst in groups.items()},
        "by_priority": by_priority,
    }

    # Relation display order.
    relation_order = ["famille", "ami", "collegue", "connaissance", "autre"]
    sorted_groups = [(rel, groups[rel]) for rel in relation_order if rel in groups]

    # Render index.
    index_html = index_tpl.render(
        contacts=enriched,
        groups=sorted_groups,
        stats=stats,
        birthdays=birthdays,
        today=today.strftime("%d/%m/%Y"),
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Render genealogy page.
    from markupsafe import Markup

    from jeff.services.genealogy import build_family_trees, tree_to_svg

    trees = build_family_trees(content_dir)
    if trees:
        genealogy_tpl = env.get_template("genealogie.html")
        trees_html = [Markup(tree_to_svg(t)) for t in trees]
        gen_html = genealogy_tpl.render(
            trees_html=trees_html,
            tree_count=len(trees),
        )
        (output_dir / "genealogie.html").write_text(gen_html, encoding="utf-8")
        _log.debug("Rendered genealogie.html with %d tree(s)", len(trees))

    return len(contacts)


class _DotDict(dict):
    """Dict subclass that allows attribute access for Jinja2 templates."""

    def __getattr__(self, key: str) -> Any:
        """Return value for key, or None if missing."""
        try:
            value = self[key]
        except KeyError:
            return None
        if isinstance(value, dict):
            return _DotDict(value)
        if isinstance(value, list):
            return [_DotDict(v) if isinstance(v, dict) else v for v in value]
        return value

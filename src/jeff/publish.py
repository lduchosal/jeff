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
            return yaml.safe_load(yaml_text) or {}
    return {}


_PRIORITY_ORDER = {"haute": 0, "moyenne": 1, "basse": 2, "": 3}


def _load_contacts(content_dir: Path) -> list[dict[str, Any]]:
    """Load active contact .md files, sorted by priority then name."""
    contacts: list[dict[str, Any]] = []
    if not content_dir.is_dir():
        return contacts
    for md in sorted(content_dir.glob("*.md")):
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
    template_dir = resources.files("jeff").joinpath("templates")
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
    )
    contact_tpl = env.get_template("contact.html")
    index_tpl = env.get_template("index.html")

    # Create output dirs.
    output_dir.mkdir(parents=True, exist_ok=True)
    contacts_out = output_dir / "contacts"
    contacts_out.mkdir(exist_ok=True)
    css_out = output_dir / "css"
    css_out.mkdir(exist_ok=True)

    # Copy CSS.
    if css_path and css_path.is_file():
        shutil.copy2(css_path, css_out / "contact.css")
    else:
        # Fallback: just create an empty placeholder.
        (css_out / "contact.css").write_text("/* no css found */", encoding="utf-8")

    # Copy photos.
    photos_out = output_dir / "photos"
    if photo_dir and photo_dir.is_dir():
        if photos_out.exists():
            shutil.rmtree(photos_out)
        shutil.copytree(photo_dir, photos_out)

    # Render contact pages.
    for contact in contacts:
        # Wrap dict in a SimpleNamespace-like object for template dot access.
        html = contact_tpl.render(contact=_DotDict(contact))
        slug = contact.get("slug", "contact")
        _log.debug("Render %s.html", slug)
        (contacts_out / f"{slug}.html").write_text(html, encoding="utf-8")

    # Render index.
    index_html = index_tpl.render(
        contacts=[_DotDict(c) for c in contacts],
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

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

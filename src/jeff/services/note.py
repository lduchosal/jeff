"""Note/interaction service — create dated interaction files."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from jeff.services.triage import load_contact

INTERACTION_TYPES = {
    "w": "whatsapp",
    "t": "tel",
    "m": "mail",
    "v": "visite",
    "n": "note",
}


def find_contact_dir(content_dir: Path, query: str) -> Path | None:
    """Find a contact directory by partial name or slug match."""
    q = query.lower()
    for d in sorted(content_dir.iterdir()):
        if not d.is_dir():
            continue
        # Check slug match.
        if q in d.name:
            return d
        # Check name match in the .md file.
        md = d / f"{d.name}.md"
        if md.exists():
            data = load_contact(md)
            if data and q in (data.get("name") or "").lower():
                return d
    return None


def list_interactions(contact_dir: Path) -> list[dict[str, Any]]:
    """List all interaction files in a contact directory, newest first."""
    interactions: list[dict[str, Any]] = []
    slug = contact_dir.name
    for md in sorted(contact_dir.glob("*.md"), reverse=True):
        if md.name == f"{slug}.md":
            continue  # Skip the contact file itself.
        data = load_contact(md)
        if data:
            interactions.append(data)
        else:
            # Simple .md without frontmatter — read as plain text.
            text = md.read_text(encoding="utf-8").strip()
            interactions.append({
                "date": md.stem,
                "note": text,
                "_path": md,
            })
    return interactions


def create_interaction(
    contact_dir: Path,
    interaction_type: str,
    note: str,
    target_date: date | None = None,
) -> Path:
    """Create an interaction .md file in the contact directory."""
    d = target_date or date.today()
    date_str = d.isoformat()

    # Handle multiple interactions on the same day.
    filename = f"{date_str}.md"
    path = contact_dir / filename
    counter = 2
    while path.exists():
        filename = f"{date_str}-{counter}.md"
        path = contact_dir / filename
        counter += 1

    content = (
        f"---\n"
        f"date: {date_str}\n"
        f"type: {interaction_type}\n"
        f"---\n\n"
        f"{note}\n"
    )
    path.write_text(content, encoding="utf-8")
    return path

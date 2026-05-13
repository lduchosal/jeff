"""Import service — create contacts from JSON file."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from jeff.domain.transform import render_frontmatter, slugify


def import_from_json(json_path: Path, content_dir: Path) -> tuple[int, int]:
    """Import contacts from a JSON file into content_dir.

    Returns (imported_count, skipped_count).
    Skips contacts whose slug directory already exists.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        data = [data]

    imported = 0
    skipped = 0

    for entry in data:
        if not entry.get("name"):
            skipped += 1
            continue

        contact = _normalize(entry)
        slug = contact.get("slug", "contact")
        contact_dir = content_dir / slug

        if contact_dir.exists():
            skipped += 1
            continue

        contact_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = render_frontmatter(contact)
        (contact_dir / f"{slug}.md").write_text(
            f"{frontmatter}\n", encoding="utf-8",
        )
        imported += 1

    return imported, skipped


def _normalize(entry: dict[str, Any]) -> dict[str, Any]:
    """Normalize a JSON contact entry to jeff frontmatter fields."""
    contact: dict[str, Any] = {}

    # UID — generate if missing.
    contact["uid"] = entry.get("uid") or str(uuid.uuid4())

    # Name fields.
    contact["name"] = entry["name"]
    contact["slug"] = slugify(entry["name"])
    for field in ("name_family", "name_given", "name_prefix"):
        if entry.get(field):
            contact[field] = entry[field]

    # Email.
    if entry.get("email"):
        contact["email"] = entry["email"]
    if entry.get("emails"):
        contact["emails"] = entry["emails"]
        if not contact.get("email"):
            contact["email"] = entry["emails"][0].get("address", "")

    # Phone.
    if entry.get("phone"):
        contact["phone"] = entry["phone"]
    if entry.get("phones"):
        contact["phones"] = entry["phones"]
        if not contact.get("phone"):
            contact["phone"] = entry["phones"][0].get("number", "")
        # Compute phone_cell.
        cell = next(
            (p for p in entry["phones"] if p.get("type") == "cell"), None,
        )
        pref = next(
            (p for p in entry["phones"] if p.get("pref")),
            entry["phones"][0],
        )
        contact["phone_cell"] = (cell or pref).get("number", "")

    # Other fields — pass through.
    for field in (
        "birthday", "signe", "note", "tags", "addresses", "positions",
        "urls", "genre", "status", "relation", "priorite", "frequence",
    ):
        if entry.get(field):
            contact[field] = entry[field]

    return contact

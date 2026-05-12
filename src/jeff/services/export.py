"""Export service — generate address books in various formats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jeff.services.triage import iter_contact_files, load_contact


def export_squirrelmail(content_dir: Path, output_path: Path) -> int:
    """Export active contacts to SquirrelMail .abook format.

    Format: nickname|firstname|lastname|email|info
    Returns the number of contacts exported.
    """
    contacts = _load_active_contacts(content_dir)
    lines: list[str] = []
    for c in contacts:
        email = c.get("email", "")
        if not email:
            continue
        nickname = c.get("slug", "")
        firstname = c.get("name_given", "")
        lastname = c.get("name_family", "")
        note = (c.get("note") or "").replace("\n", " ").replace("|", "/")
        lines.append(f"{nickname}|{firstname}|{lastname}|{email}|{note}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def _load_active_contacts(content_dir: Path) -> list[dict[str, Any]]:
    """Load contacts with status=actif."""
    contacts: list[dict[str, Any]] = []
    if not content_dir.is_dir():
        return contacts
    for md in iter_contact_files(content_dir):
        data = load_contact(md)
        if not data or not data.get("name"):
            continue
        status = data.get("status", "")
        if status == "actif":
            contacts.append(data)
    return contacts

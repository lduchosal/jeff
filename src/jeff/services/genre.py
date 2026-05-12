"""Genre assignment service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jeff.services.triage import iter_contact_files, load_contact, save_triage

GENRE_MAP = {"h": "homme", "f": "femme", "n": "none"}


def load_contacts_without_genre(content_dir: Path) -> list[dict[str, Any]]:
    """Load contacts that don't have a genre set yet."""
    contacts = []
    for md in iter_contact_files(content_dir):
        data = load_contact(md)
        if data and data.get("name") and not data.get("genre"):
            contacts.append(data)
    return contacts


def apply_genre(data: dict[str, Any], code: str) -> bool:
    """Apply a genre code (h/f) to a contact.

    Return True if applied.
    """
    genre = GENRE_MAP.get(code)
    if not genre:
        return False
    save_triage(data["_path"], {"genre": genre})
    return True

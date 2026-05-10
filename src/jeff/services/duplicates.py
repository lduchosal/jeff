"""Duplicate detection service — find contacts with same UID."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jeff.services.triage import load_contact


@dataclass
class Duplicate:
    """A set of files sharing the same UID."""

    uid: str
    files: list[dict[str, Any]]
    recommended: dict[str, Any]  # The one to keep.
    to_remove: list[dict[str, Any]]  # The ones to delete.


def find_duplicates(content_dir: Path) -> list[Duplicate]:
    """Find contacts with duplicate UIDs."""
    by_uid: dict[str, list[dict[str, Any]]] = {}
    if not content_dir.is_dir():
        return []
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if not data or not data.get("uid"):
            continue
        uid = str(data["uid"])
        by_uid.setdefault(uid, []).append(data)

    duplicates: list[Duplicate] = []
    for uid, files in by_uid.items():
        if len(files) < 2:
            continue
        # Recommend the most recently modified file.
        files.sort(key=lambda d: d["_path"].stat().st_mtime, reverse=True)
        duplicates.append(
            Duplicate(
                uid=uid,
                files=files,
                recommended=files[0],
                to_remove=files[1:],
            )
        )
    return duplicates


def remove_duplicate(contact: dict[str, Any]) -> bool:
    """Delete a duplicate .md file.

    Return True if deleted.
    """
    path = contact.get("_path")
    if path and path.exists():
        path.unlink()
        return True
    return False

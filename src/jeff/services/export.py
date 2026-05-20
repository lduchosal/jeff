"""Export service — generate address books in various formats."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from jeff.services.triage import iter_contact_files, load_contact

_SCHEMA_FIELDS = (
    "uid",
    "name",
    "name_family",
    "name_given",
    "name_prefix",
    "email",
    "emails",
    "phone",
    "phones",
    "birthday",
    "genre",
    "note",
    "tags",
    "addresses",
    "positions",
    "urls",
    "status",
    "relation",
    "priorite",
    "frequence",
)


def export_json(content_dir: Path, output_path: Path) -> int:
    """Export every contact to a JSON array matching ``contact.schema.json``.

    Mirrors ``jeff import``: the output of this function can be re-imported without data
    loss for fields covered by the schema. Non-schema fields (slug, photo,
    pere/mere/conjoint, ...) are intentionally omitted because the schema does not
    describe them.

    Returns the number of contacts written.
    """
    contacts: list[dict[str, Any]] = []
    if content_dir.is_dir():
        for md in iter_contact_files(content_dir):
            data = load_contact(md)
            if not data or not data.get("name"):
                continue
            contacts.append(_to_schema(data))

    output_path.write_text(
        json.dumps(contacts, ensure_ascii=False, indent=2, default=_json_default)
        + "\n",
        encoding="utf-8",
    )
    return len(contacts)


def _to_schema(data: dict[str, Any]) -> dict[str, Any]:
    """Project a frontmatter dict onto the JSON schema fields, dropping the rest."""
    return {k: data[k] for k in _SCHEMA_FIELDS if data.get(k) not in (None, "", [])}


def _json_default(value: Any) -> str:
    """Serialise non-JSON-native values (e.g. ``date``) as ISO strings."""
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


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

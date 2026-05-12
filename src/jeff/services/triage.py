"""Interactive triage of contact Markdown files.

Walks through each untriaged contact, displays a summary, and prompts for status /
relation / frequence / priorite.  Saves to the frontmatter immediately so progress is
never lost.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_TRIAGE_KEYS = ("status", "relation", "frequence", "priorite")


def iter_contact_files(content_dir: Path) -> list[Path]:
    """List all contact .md files (folder-per-contact layout).

    Contact file = ``<content_dir>/<slug>/<slug>.md``
    (file name matches parent directory name).
    """
    results: list[Path] = []
    if not content_dir.is_dir():
        return results
    for d in sorted(content_dir.iterdir()):
        if not d.is_dir():
            continue
        md = d / f"{d.name}.md"
        if md.is_file():
            results.append(md)
    return results


def load_contact(path: Path) -> dict[str, Any] | None:
    """Parse frontmatter from a contact .md file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            try:
                data = yaml.safe_load("\n".join(lines[1:i])) or {}
            except yaml.YAMLError:
                return None
            data["_path"] = path
            return data
    return None


def _sanitize_filename(name: str) -> str:
    """Strip path separators to prevent directory traversal."""
    return name.replace("/", "").replace("\\", "").replace("..", "")


def save_triage(path: Path, updates: dict[str, str]) -> None:
    """Update triage fields in a contact .md file.

    Rebuilds a safe path from the parent directory and sanitized filename to prevent
    path-traversal attacks (SonarCloud S2083).
    """
    parent = path.resolve().parent
    safe_name = _sanitize_filename(path.name)
    if not safe_name.endswith(".md"):
        return
    safe_path = parent / safe_name
    if not safe_path.is_file():
        return
    lines = safe_path.read_text(encoding="utf-8").splitlines()

    # Find frontmatter boundaries.
    if not lines or lines[0].strip() != "---":
        return
    close_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close_idx = i
            break
    if close_idx is None:
        return

    # Update or insert triage keys in frontmatter.
    new_fm_lines = []
    seen: set[str] = set()
    for line in lines[1:close_idx]:
        key = line.split(":")[0].strip() if ":" in line else ""
        if key in updates:
            new_fm_lines.append(f"{key}: {updates[key]}")
            seen.add(key)
        else:
            new_fm_lines.append(line)
    for k, v in updates.items():
        if k not in seen:
            new_fm_lines.append(f"{k}: {v}")

    result = [lines[0]] + new_fm_lines + lines[close_idx:]
    safe_path.write_text("\n".join(result), encoding="utf-8")


def needs_triage(data: dict[str, Any]) -> bool:
    """Return True if the contact has not been triaged yet."""
    return not data.get("status")


def format_summary(data: dict[str, Any]) -> str:
    """Format a one-screen summary of a contact for the terminal."""
    parts = []
    parts.append(data.get("name", "?"))
    if data.get("tags"):
        parts.append(f"  tags: {', '.join(data['tags'])}")
    if data.get("note"):
        parts.append(f"  note: {data['note']}")
    if data.get("addresses"):
        for addr in data["addresses"]:
            city = addr.get("city", "")
            country = addr.get("country", "")
            street = addr.get("street", "")
            loc = ", ".join(p for p in (street, city, country) if p)
            if loc:
                parts.append(f"  addr: {loc}")
    if data.get("email"):
        parts.append(f"  email: {data['email']}")
    if data.get("phone"):
        parts.append(f"  phone: {data['phone']}")
    if data.get("positions"):
        for pos in data["positions"]:
            org = pos.get("org", "")
            title = pos.get("title", "")
            parts.append(f"  org: {', '.join(p for p in (title, org) if p)}")
    return "\n".join(parts)

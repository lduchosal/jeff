"""Birthday service — detect and record birthday exchanges in frontmatter."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from jeff.services.triage import load_contact

BIRTHDAY_MESSAGE = (
    "Je vois que c'est une journ\u00e9e sp\u00e9ciale pour toi, "
    "je te souhaite un joyeux anniversaire et une journ\u00e9e "
    "remplie de joies et de belles attentions. "
    "\U0001f618\U0001f389\U0001f38a\U0001f381\U0001f382\U0001f308"
)


def find_birthdays(
    content_dir: Path, target_date: date | None = None,
) -> list[dict[str, Any]]:
    """Find contacts whose birthday is today (or target_date)."""
    d = target_date or date.today()
    today_str = f"{d.month:02d}-{d.day:02d}"
    results: list[dict[str, Any]] = []
    if not content_dir.is_dir():
        return results
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if not data or not data.get("name"):
            continue
        bday = data.get("birthday")
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
            results.append(data)
    return results


def record_birthday_exchange(
    contact: dict[str, Any], target_date: date | None = None,
) -> bool:
    """Write a birthday exchange entry in the contact's frontmatter.

    Returns True if an exchange was written, False if already recorded today.
    """
    d = target_date or date.today()
    date_str = d.isoformat()

    path = contact.get("_path")
    if not path:
        return False

    # Read file, check if already recorded today.
    text = path.read_text(encoding="utf-8")
    if f"- {date_str} anniversaire" in text:
        return False

    # Append to echanges list before the closing ---.
    lines = text.splitlines()
    new_lines: list[str] = []
    inserted = False
    for line in lines:
        # Insert before the last ---.
        if line.strip() == "---" and new_lines and not inserted:
            # If echanges section doesn't exist yet, add it.
            if "echanges:" not in text:
                new_lines.append("echanges:")
            new_lines.append(f"  - {date_str} anniversaire")
            inserted = True
        new_lines.append(line)
    path.write_text("\n".join(new_lines), encoding="utf-8")
    return True

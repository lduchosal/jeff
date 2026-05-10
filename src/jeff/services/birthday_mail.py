"""Birthday reminder mail service."""

from __future__ import annotations

import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from jeff.services.birthday import BIRTHDAY_MESSAGE, find_birthdays


def build_birthday_html(
    contacts: list[dict[str, Any]],
    label: str,
) -> str:
    """Build an HTML email body for birthday reminders."""
    if not contacts:
        return ""
    lines = [
        "<html><body>",
        f"<h2>{label}</h2>",
        "<ul>",
    ]
    for c in contacts:
        name = c.get("name", "?")
        phone = c.get("phone_cell") or c.get("phone", "")
        phone_clean = phone.replace("+", "").replace(" ", "")
        wa_text = quote(BIRTHDAY_MESSAGE, safe="")
        wa_url = (
            f"https://api.whatsapp.com/send?phone={phone_clean}&text={wa_text}"
            if phone_clean
            else ""
        )
        lines.append(f"<li><strong>{name}</strong>")
        if c.get("birthday"):
            lines.append(f" — {c['birthday']}")
        if c.get("signe"):
            lines.append(f" ({c['signe']})")
        if wa_url:
            lines.append(f' — <a href="{wa_url}">WhatsApp</a>')
        lines.append("</li>")
    lines.extend(["</ul>", "</body></html>"])
    return "\n".join(lines)


def send_birthday_mail(
    content_dir: Path,
    mail_to: str,
    mail_from: str = "jeff@localhost",
    tomorrow: bool = False,
) -> int:
    """Send birthday reminder via sendmail. Return number of contacts."""
    target_date = date.today() + timedelta(days=1) if tomorrow else date.today()
    label = "Anniversaires demain" if tomorrow else "Anniversaires aujourd'hui"
    contacts = find_birthdays(content_dir, target_date)
    if not contacts:
        return 0

    html = build_birthday_html(contacts, label)
    subject = f"{label} ({target_date.strftime('%d/%m/%Y')})"

    # Build raw email.
    msg = (
        f"From: {mail_from}\r\n"
        f"To: {mail_to}\r\n"
        f"Subject: {subject}\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n"
        f"MIME-Version: 1.0\r\n"
        f"\r\n"
        f"{html}"
    )

    # Send via sendmail/msmtp.
    proc = subprocess.run(
        ["sendmail", "-t"],
        input=msg.encode("utf-8"),
        capture_output=True,
    )
    return len(contacts) if proc.returncode == 0 else 0

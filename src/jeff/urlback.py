"""Write CRM profile URL back into vCard on CardDAV server.

Adds an ``item99.URL`` + ``item99.X-ABLabel:Profil CRM`` pair to the vCard so the link
is visible and clickable in Apple Contacts / iOS. See task #273 for the design decision.
"""

from __future__ import annotations


def inject_crm_url(vcard_raw: str, profile_url: str) -> str | None:
    """Inject a CRM profile URL into a vCard string.

    Returns the modified vCard, or None if the URL is already present. Uses the
    ``item99`` property group with ``X-ABLabel:Profil CRM`` so it appears as a labeled
    link in Apple Contacts.
    """
    # Check if the URL is already there.
    if profile_url in vcard_raw:
        return None

    # Remove any existing item99 group (in case of a stale URL).
    lines = vcard_raw.splitlines()
    lines = [line for line in lines if not line.startswith("item99.")]

    # Insert before END:VCARD.
    new_lines: list[str] = []
    for line in lines:
        if line.strip().upper() == "END:VCARD":
            new_lines.extend(
                (f"item99.URL:{profile_url}", "item99.X-ABLabel:Profil CRM")
            )
        new_lines.append(line)

    return "\n".join(new_lines)


def build_profile_url(publish_url: str, slug: str) -> str:
    """Build the full profile URL for a contact.

    Parameters
    ----------
    publish_url:
        Base URL of the published site (e.g. ``https://crm.example.com``).
    slug:
        Contact slug (e.g. ``jean-dupont``).

    Returns
    -------
    str
        Full URL (e.g. ``https://crm.example.com/contacts/jean-dupont.html``).
    """
    base = publish_url.rstrip("/")
    return f"{base}/contacts/{slug}.html"

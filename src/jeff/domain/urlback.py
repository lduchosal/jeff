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


def inject_gender(vcard_raw: str, genre: str) -> str | None:
    """Inject an X-GENDER property into a vCard string.

    Returns the modified vCard, or None if the gender is already set to the same value.
    Uses ``X-GENDER`` (widely supported by CardDAV clients).
    """
    gender_value = "M" if genre == "homme" else "F"
    existing_line = f"X-GENDER:{gender_value}"

    # Already present with the same value.
    if existing_line in vcard_raw:
        return None

    # Remove any existing X-GENDER line.
    lines = [
        line for line in vcard_raw.splitlines() if not line.startswith("X-GENDER:")
    ]

    # Insert before END:VCARD.
    new_lines: list[str] = []
    for line in lines:
        if line.strip().upper() == "END:VCARD":
            new_lines.append(existing_line)
        new_lines.append(line)

    return "\n".join(new_lines)


def inject_related(
    vcard_raw: str,
    relations: list[tuple[str, str]],
) -> str | None:
    """Inject RELATED properties into a vCard string.

    ``relations`` is a list of ``(type, uid)`` tuples where type is one of
    ``parent``, ``spouse``, ``child``, ``sibling``.

    Returns the modified vCard, or None if nothing changed.
    """
    # Build the target set of RELATED lines.
    target_lines = sorted(
        f"RELATED;TYPE={rtype}:urn:uuid:{uid}" for rtype, uid in relations
    )
    if not target_lines:
        return None

    # Parse existing RELATED lines.
    existing_related = set()
    other_lines: list[str] = []
    for line in vcard_raw.splitlines():
        if line.startswith("RELATED;"):
            existing_related.add(line)
        else:
            other_lines.append(line)

    # Check if already up to date.
    if existing_related == set(target_lines):
        return None

    # Insert new RELATED lines before END:VCARD.
    new_lines: list[str] = []
    for line in other_lines:
        if line.strip().upper() == "END:VCARD":
            new_lines.extend(target_lines)
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

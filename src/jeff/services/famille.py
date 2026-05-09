"""Family link service — reciprocal link logic and display helpers."""

from __future__ import annotations

from typing import Any


def reciprocal_updates(
    role: str, source_slug: str, source: dict, target: dict,
) -> dict[str, str]:
    """Compute the reciprocal family link update for the target contact.

    Uses source genre to pick pere vs mere when the reciprocal of 'enfants'
    is needed (i.e. source says target is their child, so target gets
    pere or mere pointing back to source).
    """
    reciprocal_map: dict[str, str] = {
        "pere": "enfants",
        "mere": "enfants",
        "conjoint": "conjoint",
        "freres_soeurs": "freres_soeurs",
    }
    if role == "enfants":
        genre = (source.get("genre") or "").lower()
        rev = "mere" if genre == "femme" else "pere"
    else:
        rev = reciprocal_map.get(role, "")
    if not rev:
        return {}
    if rev in ("enfants", "freres_soeurs"):
        existing = _parse_slug_list(target.get(rev))
        if source_slug not in existing:
            existing.append(source_slug)
        return {rev: f"[{', '.join(existing)}]"}
    return {rev: source_slug}


def merge_list_field(contact: dict, field: str, new_slugs: list[str]) -> str:
    """Merge new slugs into an existing list field, return YAML string."""
    existing = _parse_slug_list(contact.get(field))
    for s in new_slugs:
        if s not in existing:
            existing.append(s)
    return f"[{', '.join(existing)}]"


def format_existing_links(data: dict[str, Any]) -> list[str]:
    """Return human-readable lines for existing family links."""
    links = []
    if data.get("pere"):
        links.append(f"père: {data['pere']}")
    if data.get("mere"):
        links.append(f"mère: {data['mere']}")
    if data.get("conjoint"):
        links.append(f"conjoint: {data['conjoint']}")
    if data.get("freres_soeurs"):
        fs = _parse_slug_list(data["freres_soeurs"])
        if fs:
            links.append(f"frères/sœurs: {', '.join(fs)}")
    if data.get("enfants"):
        enf = _parse_slug_list(data["enfants"])
        if enf:
            links.append(f"enfants: {', '.join(enf)}")
    return links


def _parse_slug_list(value: Any) -> list[str]:
    """Parse a list field that may be a list or a '[slug1, slug2]' string."""
    if not value:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, str):
        return [s.strip() for s in value.strip("[] ").split(",") if s.strip()]
    return []

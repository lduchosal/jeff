"""Family link service — reciprocal link logic and display helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jeff.services.triage import load_contact, save_triage

ROLE_MAP = {
    "f": "pere",
    "m": "mere",
    "w": "conjoint",
    "c": "enfants",
    "b": "freres_soeurs",
}


def reciprocal_updates(
    role: str,
    source_slug: str,
    source: dict,
    target: dict,
) -> dict[str, str]:
    """Compute the reciprocal family link update for the target contact.

    Uses source genre to pick pere vs mere when the reciprocal of 'enfants' is needed
    (i.e. source says target is their child, so target gets pere or mere pointing back
    to source).
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


@dataclass
class FamilleContext:
    """Loaded state for the famille editing session."""

    all_contacts: list[dict] = field(default_factory=list)
    famille_contacts: list[dict] = field(default_factory=list)
    by_surname: dict[str, list[dict]] = field(default_factory=dict)


def load_famille_context(content_dir: Path) -> FamilleContext:
    """Load all contacts and prepare famille editing context."""
    ctx = FamilleContext()
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name"):
            ctx.all_contacts.append(data)
            surname = (data.get("name_family") or "").strip().lower()
            if surname:
                ctx.by_surname.setdefault(surname, []).append(data)
    ctx.famille_contacts = [
        c for c in ctx.all_contacts if c.get("relation") == "famille"
    ]
    return ctx


def same_surname_candidates(ctx: FamilleContext, contact: dict) -> list[dict]:
    """Return contacts with the same surname, excluding self."""
    surname = (contact.get("name_family") or "").strip().lower()
    slug = contact.get("slug", "")
    return [c for c in ctx.by_surname.get(surname, []) if c.get("slug") != slug]


def search_contacts(ctx: FamilleContext, query: str, exclude_slug: str) -> list[dict]:
    """Search contacts by name substring."""
    q = query.lower()
    return [
        c
        for c in ctx.all_contacts
        if c.get("slug") != exclude_slug and q in (c.get("name") or "").lower()
    ]


@dataclass
class ParsedTokens:
    """Result of parsing family assignment tokens."""

    updates: dict[str, str] = field(default_factory=dict)
    reciprocals: list[tuple[dict, dict[str, str]]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_tokens(
    raw: str,
    candidates: list[dict],
    contact: dict,
) -> ParsedTokens:
    """Parse tokens like '1f 2m 3w 4c 5b' into updates and reciprocals."""
    result = ParsedTokens()
    slug = contact.get("slug", "")
    children: list[str] = []
    siblings: list[str] = []

    for token in raw.lower().split():
        if len(token) < 2:
            result.errors.append(f"invalide: {token}")
            continue
        num_str = token[:-1]
        code = token[-1]
        if not num_str.isdigit() or code not in ROLE_MAP:
            result.errors.append(f"invalide: {token}")
            continue
        n = int(num_str)
        if n < 1 or n > len(candidates):
            result.errors.append(f"hors limite: {token}")
            continue
        target = candidates[n - 1]
        target_slug = target.get("slug", "")
        role = ROLE_MAP[code]
        if role == "enfants":
            children.append(target_slug)
        elif role == "freres_soeurs":
            siblings.append(target_slug)
        else:
            result.updates[role] = target_slug
        rev = reciprocal_updates(role, slug, contact, target)
        if rev:
            result.reciprocals.append((target, rev))

    if children:
        result.updates["enfants"] = merge_list_field(contact, "enfants", children)
    if siblings:
        result.updates["freres_soeurs"] = merge_list_field(
            contact, "freres_soeurs", siblings
        )
    return result


def apply_famille_updates(
    contact: dict,
    parsed: ParsedTokens,
) -> list[str]:
    """Apply parsed tokens to contact and targets.

    Return summary lines.
    """
    lines: list[str] = []
    if not parsed.updates:
        return lines
    save_triage(contact["_path"], parsed.updates)
    for k, v in parsed.updates.items():
        contact[k] = v
    summary = " ".join(f"{k}={v}" for k, v in parsed.updates.items())
    lines.append(f"✓ {contact.get('name')}: {summary}")
    for target, rev_updates in parsed.reciprocals:
        target_path = target.get("_path")
        if target_path:
            save_triage(target_path, rev_updates)
            for k, v in rev_updates.items():
                target[k] = v
            rev_summary = " ".join(f"{k}={v}" for k, v in rev_updates.items())
            lines.append(f"↔ {target.get('name')}: {rev_summary}")
    return lines


@dataclass
class Inconsistency:
    """A detected family link inconsistency."""

    contact_name: str
    contact_slug: str
    target_slug: str
    target_name: str
    message: str
    fix_contact: str  # slug of contact to fix
    fix_field: str
    fix_value: str


def check_family_consistency(ctx: FamilleContext) -> list[Inconsistency]:
    """Check all family links for bidirectional consistency."""
    by_slug: dict[str, dict] = {}
    for c in ctx.all_contacts:
        s = c.get("slug", "")
        if s:
            by_slug[s] = c

    issues: list[Inconsistency] = []

    for contact in ctx.famille_contacts:
        slug = contact.get("slug", "")
        name = contact.get("name", "?")
        genre = (contact.get("genre") or "").lower()

        # pere → target.enfants should contain slug
        if contact.get("pere"):
            _check_in_list(
                issues,
                by_slug,
                slug,
                name,
                contact["pere"],
                "pere",
                "enfants",
            )

        # mere → target.enfants should contain slug
        if contact.get("mere"):
            _check_in_list(
                issues,
                by_slug,
                slug,
                name,
                contact["mere"],
                "mere",
                "enfants",
            )

        # conjoint → target.conjoint should be slug
        if contact.get("conjoint"):
            target_slug = contact["conjoint"]
            target = by_slug.get(target_slug)
            if target and target.get("conjoint") != slug:
                issues.append(
                    Inconsistency(
                        contact_name=name,
                        contact_slug=slug,
                        target_slug=target_slug,
                        target_name=target.get("name", "?"),
                        message=(
                            f"{name} a conjoint={target_slug} mais "
                            f"{target.get('name', '?')} a conjoint={target.get('conjoint', '')}"
                        ),
                        fix_contact=target_slug,
                        fix_field="conjoint",
                        fix_value=slug,
                    )
                )

        # enfants → each child should have pere/mere = slug
        for child_slug in _parse_slug_list(contact.get("enfants")):
            child = by_slug.get(child_slug)
            if not child:
                continue
            expected_field = "mere" if genre == "femme" else "pere"
            if child.get(expected_field) != slug:
                issues.append(
                    Inconsistency(
                        contact_name=name,
                        contact_slug=slug,
                        target_slug=child_slug,
                        target_name=child.get("name", "?"),
                        message=(
                            f"{name} a {child_slug} dans enfants mais "
                            f"{child.get('name', '?')} a {expected_field}={child.get(expected_field, '')}"
                        ),
                        fix_contact=child_slug,
                        fix_field=expected_field,
                        fix_value=slug,
                    )
                )

        # freres_soeurs → each sibling should have slug in freres_soeurs
        for sib_slug in _parse_slug_list(contact.get("freres_soeurs")):
            sib = by_slug.get(sib_slug)
            if not sib:
                continue
            sib_list = _parse_slug_list(sib.get("freres_soeurs"))
            if slug not in sib_list:
                issues.append(
                    Inconsistency(
                        contact_name=name,
                        contact_slug=slug,
                        target_slug=sib_slug,
                        target_name=sib.get("name", "?"),
                        message=(
                            f"{name} a {sib_slug} dans freres_soeurs mais "
                            f"{sib.get('name', '?')} n'a pas {slug}"
                        ),
                        fix_contact=sib_slug,
                        fix_field="freres_soeurs",
                        fix_value=slug,
                    )
                )

    return issues


def _check_in_list(
    issues: list[Inconsistency],
    by_slug: dict[str, dict],
    slug: str,
    name: str,
    target_slug: str,
    relation: str,
    expected_list: str,
) -> None:
    """Check that slug is in target's expected_list."""
    target = by_slug.get(target_slug)
    if not target:
        return
    existing = _parse_slug_list(target.get(expected_list))
    if slug not in existing:
        issues.append(
            Inconsistency(
                contact_name=name,
                contact_slug=slug,
                target_slug=target_slug,
                target_name=target.get("name", "?"),
                message=(
                    f"{name} a {relation}={target_slug} mais "
                    f"{target.get('name', '?')} n'a pas {slug} dans {expected_list}"
                ),
                fix_contact=target_slug,
                fix_field=expected_list,
                fix_value=slug,
            )
        )


def apply_fix(inconsistency: Inconsistency, by_slug: dict[str, dict]) -> str | None:
    """Apply a fix for an inconsistency.

    Return summary or None.
    """
    target = by_slug.get(inconsistency.fix_contact)
    if not target or not target.get("_path"):
        return None
    field = inconsistency.fix_field
    value = inconsistency.fix_value
    if field in ("enfants", "freres_soeurs"):
        new_val = merge_list_field(target, field, [value])
        save_triage(target["_path"], {field: new_val})
        target[field] = new_val
    else:
        save_triage(target["_path"], {field: value})
        target[field] = value
    return f"✓ {target.get('name')}: {field}={target[field]}"

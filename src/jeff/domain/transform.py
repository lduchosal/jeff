"""Transform vCard data to Markdown with YAML frontmatter.

Parses vCard strings via ``vobject``, extracts fields into a dict, and renders Hugo-
compatible Markdown files.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any

import vobject

from jeff.domain.carddav import Contact
from jeff.log import get_logger

_log = get_logger("transform")


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[àáâãäå]", "a", slug)
    slug = re.sub(r"[èéêë]", "e", slug)
    slug = re.sub(r"[ìíîï]", "i", slug)
    slug = re.sub(r"[òóôõö]", "o", slug)
    slug = re.sub(r"[ùúûü]", "u", slug)
    slug = re.sub(r"[ýÿ]", "y", slug)
    slug = re.sub(r"ñ", "n", slug)
    slug = re.sub(r"[çć]", "c", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "contact"


def parse_vcard(vcard_raw: str) -> dict[str, Any]:
    """Parse a vCard string into a flat dict for YAML frontmatter.

    Extracts all standard fields. Missing fields are omitted (not set to None) so the
    frontmatter stays clean.
    """
    vc = vobject.readOne(vcard_raw)
    data: dict[str, Any] = {}

    # UID
    if hasattr(vc, "uid"):
        data["uid"] = vc.uid.value

    # Name
    if hasattr(vc, "fn"):
        data["name"] = vc.fn.value
        data["slug"] = slugify(vc.fn.value)

    if hasattr(vc, "n"):
        n = vc.n.value
        if n.family:
            data["name_family"] = n.family
        if n.given:
            data["name_given"] = n.given
        if n.prefix:
            data["name_prefix"] = n.prefix
        if n.suffix:
            data["name_suffix"] = n.suffix

    # Emails
    emails = vc.contents.get("email", [])
    if emails:
        email_list = []
        for em in emails:
            entry: dict[str, Any] = {"address": em.value}
            types = em.params.get("TYPE", [])
            etype = next(
                (t.lower() for t in types if t.lower() in ("home", "work")),
                None,
            )
            if etype:
                entry["type"] = etype
            if "PREF" in types:
                entry["pref"] = True
            email_list.append(entry)
        data["emails"] = email_list
        # Convenience scalar: pref or first.
        pref = next((e for e in email_list if e.get("pref")), email_list[0])
        data["email"] = pref["address"]

    # Phones
    tels = vc.contents.get("tel", [])
    if tels:
        phone_list = []
        for tel in tels:
            entry = {"number": tel.value}
            types = tel.params.get("TYPE", [])
            ptype = next(
                (
                    t.lower()
                    for t in types
                    if t.lower() in ("home", "work", "cell", "fax")
                ),
                None,
            )
            if ptype:
                entry["type"] = ptype
            if "PREF" in types:
                entry["pref"] = True
            phone_list.append(entry)
        data["phones"] = phone_list
        pref = next((p for p in phone_list if p.get("pref")), phone_list[0])
        data["phone"] = pref["number"]

    # Addresses
    adrs = vc.contents.get("adr", [])
    if adrs:
        addr_list = []
        for adr in adrs:
            a = adr.value
            entry = {}
            types = adr.params.get("TYPE", [])
            atype = next(
                (t.lower() for t in types if t.lower() in ("home", "work")),
                None,
            )
            if atype:
                entry["type"] = atype
            if a.street:
                entry["street"] = _collapse_newlines(a.street) if "\n" in a.street else a.street
            if a.city:
                entry["city"] = a.city
            if a.region:
                entry["region"] = a.region
            if a.code:
                entry["postal_code"] = a.code
            if a.country:
                entry["country"] = a.country
            if entry:
                addr_list.append(entry)
        if addr_list:
            data["addresses"] = addr_list

    # Org + Title
    orgs = vc.contents.get("org", [])
    titles = vc.contents.get("title", [])
    if orgs:
        positions = []
        for i, org in enumerate(orgs):
            org_name = org.value[0] if isinstance(org.value, list) else org.value
            pos: dict[str, str] = {"org": org_name}
            if i < len(titles):
                pos["title"] = titles[i].value
            positions.append(pos)
        data["positions"] = positions

    # Birthday
    if hasattr(vc, "bday"):
        data["birthday"] = vc.bday.value

    # Categories -> tags
    cats = vc.contents.get("categories", [])
    if cats:
        tags: list[str] = []
        for cat in cats:
            if isinstance(cat.value, list):
                tags.extend(cat.value)
            else:
                tags.extend(cat.value.split(","))
        data["tags"] = [t.strip() for t in tags if t.strip()]

    # URLs
    urls = vc.contents.get("url", [])
    if urls:
        url_list = []
        for u in urls:
            entry = {"url": u.value}
            types = u.params.get("TYPE", [])
            utype = next(
                (t.lower() for t in types if t.lower() in ("home", "work")),
                None,
            )
            if utype:
                entry["type"] = utype
            url_list.append(entry)
        data["urls"] = url_list

    # Note
    if hasattr(vc, "note"):
        data["note"] = vc.note.value

    # Photo (returns the raw bytes + extension, or None)
    photo = vc.contents.get("photo", [None])[0]
    if photo and photo.value:
        data["_photo_data"] = photo

    # REV
    if hasattr(vc, "rev"):
        data["rev"] = vc.rev.value

    # Gender (X-GENDER property).
    x_gender = vc.contents.get("x-gender", [None])[0]
    if x_gender and x_gender.value:
        val = x_gender.value.strip().upper()
        if val == "M":
            data["genre"] = "homme"
        elif val == "F":
            data["genre"] = "femme"

    return data


def _collapse_newlines(value: str) -> str:
    """Collapse multi-line strings into a single line joined by ', '."""
    return ", ".join(line.strip() for line in value.splitlines() if line.strip())


def _yaml_value(value: Any) -> str:
    """Format a value for YAML output."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        s: str = value
        # Quote strings containing special chars.
        if any(c in s for c in ":{}[]#&*!|>'\",@`"):
            return f'"{s}"'
        if s.startswith("+"):
            return f'"{s}"'
        return s
    return str(value)


def _yaml_list_of_dicts(items: list[dict[str, Any]], indent: int = 2) -> str:
    """Render a list of dicts as YAML."""
    lines: list[str] = []
    prefix = " " * indent
    for item in items:
        first = True
        for k, v in item.items():
            if first:
                lines.append(f"{prefix}- {k}: {_yaml_value(v)}")
                first = False
            else:
                lines.append(f"{prefix}  {k}: {_yaml_value(v)}")
    return "\n".join(lines)


def render_frontmatter(data: dict[str, Any]) -> str:
    """Render a parsed vCard dict as YAML frontmatter string."""
    lines: list[str] = ["---"]

    # Scalar fields in order.
    scalars = [
        "uid",
        "name",
        "slug",
        "name_family",
        "name_given",
        "name_prefix",
        "name_suffix",
        "email",
        "phone",
        "birthday",
        "note",
        "photo",
        "rev",
    ]
    for key in scalars:
        if key not in data:
            continue
        val = data[key]
        # Notes with newlines use YAML block scalar to preserve formatting.
        if key == "note" and isinstance(val, str) and "\n" in val:
            lines.append("note: |")
            for note_line in val.splitlines():
                lines.append(f"  {note_line}")
        else:
            lines.append(f"{key}: {_yaml_value(val)}")

    # Tags
    if "tags" in data:
        tags_str = ", ".join(data["tags"])
        lines.append(f"tags: [{tags_str}]")

    # Sorting/triage fields (preserved from existing frontmatter if present).
    for key in ("status", "relation", "frequence", "priorite", "genre"):
        lines.append(f"{key}: {_yaml_value(data[key]) if data.get(key) else ''}")

    # Family link fields (preserved from existing frontmatter).
    for key in ("pere", "mere", "conjoint"):
        val = data.get(key, "")
        lines.append(f"{key}: {_yaml_value(val) if val else ''}")
    for key in ("freres_soeurs", "enfants"):
        val = data.get(key)
        if val:
            lines.append(f"{key}: [{', '.join(val)}]")
        else:
            lines.append(f"{key}: []")

    # List-of-dict fields.
    list_fields = [
        ("emails", "emails"),
        ("phones", "phones"),
        ("addresses", "addresses"),
        ("positions", "positions"),
        ("urls", "urls"),
    ]
    for key, label in list_fields:
        if key in data:
            lines.extend((f"{label}:", _yaml_list_of_dicts(data[key])))

    lines.append("---")
    return "\n".join(lines)


def extract_photo(
    data: dict[str, Any],
    slug: str,
    photo_dir: Path,
) -> str | None:
    """Extract a base64 photo from vCard data to a file.

    Returns the relative path (for frontmatter) or None.
    """
    photo_prop = data.get("_photo_data")
    if photo_prop is None:
        return None

    # Determine extension from TYPE param.
    types = photo_prop.params.get("TYPE", [])
    ext_map = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "gif": "gif"}
    ext = "jpg"
    for t in types:
        mapped = ext_map.get(t.lower())
        if mapped:
            ext = mapped
            break

    # Get binary data. vobject may already decode base64 to bytes.
    value = photo_prop.value
    if isinstance(value, bytes):
        photo_bytes = value
    elif isinstance(value, str):
        if value.startswith("data:"):
            _, encoded = value.split(",", 1)
            photo_bytes = base64.b64decode(encoded)
        elif value.startswith("http"):
            # External URL — skip extraction.
            return None
        else:
            # Try base64 decode (raw base64 string).
            try:
                photo_bytes = base64.b64decode(value)
            except Exception:
                return None
    else:
        return None

    photo_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{slug}.{ext}"
    (photo_dir / filename).write_bytes(photo_bytes)
    return f"photos/{filename}"


def contact_to_markdown(
    contact: Contact,
    content_dir: Path,
    photo_dir: Path,
) -> Path:
    """Transform a CardDAV contact into a Markdown file.

    Returns the path to the written file.
    """
    data = parse_vcard(contact.vcard_raw)
    slug = data.get("slug", "contact")
    _log.debug("Transform %s → %s.md", data.get("name", "?"), slug)

    # Preserve hand-edited triage fields from existing frontmatter.
    content_dir.mkdir(parents=True, exist_ok=True)
    md_path = content_dir / f"{slug}.md"
    _triage_keys = (
        "status",
        "relation",
        "frequence",
        "priorite",
        "genre",
        "pere",
        "mere",
        "conjoint",
        "freres_soeurs",
        "enfants",
    )
    if md_path.exists():
        import yaml

        existing = md_path.read_text(encoding="utf-8")
        lines_ex = existing.split("\n")
        if lines_ex and lines_ex[0].strip() == "---":
            for idx, line in enumerate(lines_ex[1:], start=1):
                if line.strip() == "---":
                    try:
                        old = yaml.safe_load("\n".join(lines_ex[1:idx])) or {}
                    except yaml.YAMLError:
                        _log.warning("Corrupt frontmatter in %s, skipping preservation", md_path.name)
                        break
                    for k in _triage_keys:
                        if old.get(k):
                            data[k] = old[k]
                    break

    # Extract photo if present.
    photo_path = extract_photo(data, slug, photo_dir)
    if photo_path:
        data["photo"] = photo_path
    # Remove internal photo data.
    data.pop("_photo_data", None)

    frontmatter = render_frontmatter(data)
    md_path.write_text(f"{frontmatter}\n", encoding="utf-8")
    return md_path

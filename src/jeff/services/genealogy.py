"""Genealogy service — build family tree structure for HTML rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jeff.services.famille import _parse_slug_list
from jeff.services.triage import load_contact


@dataclass
class TreeNode:
    """A node in the family tree."""

    slug: str
    name: str
    genre: str
    birthday: str
    conjoint: TreeNode | None = None
    children: list[TreeNode] = field(default_factory=list)
    depth: int = 0


def build_family_trees(content_dir: Path) -> list[TreeNode]:
    """Build all family trees from contact .md files.

    Returns a list of root nodes (ancestors with no parents in the dataset).
    """
    # Load all famille contacts.
    by_slug: dict[str, dict[str, Any]] = {}
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name") and data.get("relation") == "famille":
            by_slug[data.get("slug", "")] = data

    # Find roots: contacts with no pere/mere in the dataset.
    roots: list[str] = []
    for slug, data in by_slug.items():
        pere = data.get("pere", "")
        mere = data.get("mere", "")
        has_parent = (pere and pere in by_slug) or (mere and mere in by_slug)
        if not has_parent:
            roots.append(slug)

    # Deduplicate: if both spouses are roots, keep only one.
    deduped: list[str] = []
    seen_couples: set[str] = set()
    for slug in roots:
        data = by_slug[slug]
        conjoint = data.get("conjoint", "")
        couple_key = tuple(sorted([slug, conjoint])) if conjoint else (slug,)
        key = str(couple_key)
        if key in seen_couples:
            continue
        seen_couples.add(key)
        deduped.append(slug)

    # Build tree recursively.
    visited: set[str] = set()
    trees: list[TreeNode] = []
    for slug in deduped:
        node = _build_node(slug, by_slug, visited, depth=0)
        if node:
            trees.append(node)

    return trees


def _build_node(
    slug: str,
    by_slug: dict[str, dict[str, Any]],
    visited: set[str],
    depth: int,
) -> TreeNode | None:
    """Recursively build a tree node."""
    if slug in visited or slug not in by_slug:
        return None
    visited.add(slug)

    data = by_slug[slug]
    node = TreeNode(
        slug=slug,
        name=data.get("name", slug),
        genre=(data.get("genre") or ""),
        birthday=str(data.get("birthday", "")),
        depth=depth,
    )

    # Attach conjoint (not recursive — just info).
    conjoint_slug = data.get("conjoint", "")
    if conjoint_slug and conjoint_slug in by_slug and conjoint_slug not in visited:
        visited.add(conjoint_slug)
        cdata = by_slug[conjoint_slug]
        node.conjoint = TreeNode(
            slug=conjoint_slug,
            name=cdata.get("name", conjoint_slug),
            genre=(cdata.get("genre") or ""),
            birthday=str(cdata.get("birthday", "")),
            depth=depth,
        )

    # Attach children.
    child_slugs = _parse_slug_list(data.get("enfants"))
    # Also check conjoint's children.
    if node.conjoint and conjoint_slug:
        cdata = by_slug.get(conjoint_slug, {})
        for cs in _parse_slug_list(cdata.get("enfants")):
            if cs not in child_slugs:
                child_slugs.append(cs)

    for child_slug in child_slugs:
        child_node = _build_node(child_slug, by_slug, visited, depth + 1)
        if child_node:
            node.children.append(child_node)

    return node


def tree_to_html(node: TreeNode) -> str:
    """Render a tree node as nested HTML for CSS-based tree display."""
    parts: list[str] = []
    parts.append('<li>')
    parts.append('<div class="tree-couple">')
    parts.append(_person_html(node))
    if node.conjoint:
        parts.append('<span class="tree-link">+</span>')
        parts.append(_person_html(node.conjoint))
    parts.append('</div>')
    if node.children:
        parts.append('<ul>')
        for child in node.children:
            parts.append(tree_to_html(child))
        parts.append('</ul>')
    parts.append('</li>')
    return "\n".join(parts)


def _person_html(node: TreeNode) -> str:
    """Render a single person card."""
    gender = "♂️" if node.genre == "homme" else "♀️" if node.genre == "femme" else ""
    return (
        f'<a class="tree-person tree-person--{node.genre or "unknown"}" '
        f'href="contacts/{node.slug}.html">'
        f'{gender} {node.name}'
        f'</a>'
    )

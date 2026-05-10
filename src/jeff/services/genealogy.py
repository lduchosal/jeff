"""Genealogy service — build family tree structure and render as SVG."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from jeff.services.famille import _parse_slug_list
from jeff.services.triage import load_contact

# Layout constants.
NODE_W = 160
NODE_H = 40
COUPLE_GAP = 24
H_GAP = 32
V_GAP = 80
PADDING = 20


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
    # Computed layout positions.
    x: float = 0
    y: float = 0
    width: float = 0  # Total subtree width.


def build_family_trees(content_dir: Path) -> list[TreeNode]:
    """Build all family trees from contact .md files."""
    by_slug: dict[str, dict[str, Any]] = {}
    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if data and data.get("name") and data.get("relation") == "famille":
            by_slug[data.get("slug", "")] = data

    roots: list[str] = []
    for slug, data in by_slug.items():
        pere = data.get("pere", "")
        mere = data.get("mere", "")
        has_parent = (pere and pere in by_slug) or (mere and mere in by_slug)
        if not has_parent:
            roots.append(slug)

    # Deduplicate couples.
    deduped: list[str] = []
    seen_couples: set[str] = set()
    for slug in roots:
        data = by_slug[slug]
        conjoint = data.get("conjoint", "")
        couple_key = str(tuple(sorted([slug, conjoint])) if conjoint else (slug,))
        if couple_key in seen_couples:
            continue
        seen_couples.add(couple_key)
        deduped.append(slug)

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
    child_slugs = _parse_slug_list(data.get("enfants"))
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


def _couple_width(node: TreeNode) -> float:
    """Width of the couple box (one or two person cards + gap)."""
    if node.conjoint:
        return NODE_W * 2 + COUPLE_GAP
    return NODE_W


def _compute_layout(node: TreeNode, x: float, y: float) -> None:
    """Compute x, y positions for the entire subtree."""
    node.y = y

    if not node.children:
        node.width = _couple_width(node)
        node.x = x
        return

    # Layout children first to know total width.
    children_width = 0.0
    for i, child in enumerate(node.children):
        _compute_layout(child, x + children_width, y + V_GAP)
        children_width += child.width
        if i < len(node.children) - 1:
            children_width += H_GAP

    node.width = max(_couple_width(node), children_width)

    # Center this node over its children.
    first_child = node.children[0]
    last_child = node.children[-1]
    children_center = (
        first_child.x + _couple_width(first_child) / 2
        + last_child.x + _couple_width(last_child) / 2
    ) / 2
    node.x = children_center - _couple_width(node) / 2


def tree_to_svg(root: TreeNode) -> str:
    """Render a family tree as an SVG string."""
    _compute_layout(root, PADDING, PADDING)

    # Collect all elements.
    svg_parts: list[str] = []
    max_x = 0.0
    max_y = 0.0
    _render_node(root, svg_parts)
    _find_bounds(root, bounds := [0.0, 0.0])
    max_x, max_y = bounds

    w = max_x + PADDING
    h = max_y + PADDING
    header = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {w:.0f} {h:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}" '
        f'style="font-family: Inter, sans-serif;">'
    )
    return header + "\n".join(svg_parts) + "</svg>"


def _find_bounds(node: TreeNode, bounds: list[float]) -> None:
    """Find max x and y in the tree."""
    right = node.x + _couple_width(node)
    bottom = node.y + NODE_H
    if right > bounds[0]:
        bounds[0] = right
    if bottom > bounds[1]:
        bounds[1] = bottom
    if node.conjoint:
        pass  # conjoint is at same y, already counted in couple_width
    for child in node.children:
        _find_bounds(child, bounds)


def _render_node(node: TreeNode, parts: list[str]) -> None:
    """Render a node and its descendants as SVG elements."""
    cx = node.x + _couple_width(node) / 2

    # Draw person box(es).
    _render_person(node, node.x, node.y, parts)
    if node.conjoint:
        conj_x = node.x + NODE_W + COUPLE_GAP
        _render_person(node.conjoint, conj_x, node.y, parts)
        # Couple connector line.
        parts.append(
            f'<line x1="{node.x + NODE_W}" y1="{node.y + NODE_H / 2}" '
            f'x2="{conj_x}" y2="{node.y + NODE_H / 2}" '
            f'stroke="#cbd5e1" stroke-width="2"/>'
        )
        # Heart/link symbol.
        mid_x = node.x + NODE_W + COUPLE_GAP / 2
        parts.append(
            f'<text x="{mid_x}" y="{node.y + NODE_H / 2 + 4}" '
            f'text-anchor="middle" font-size="10" fill="#94a3b8">'
            f"&#9829;</text>"
        )

    # Lines to children.
    if node.children:
        # Vertical line down from couple center.
        child_y = node.y + V_GAP
        mid_y = node.y + NODE_H + (V_GAP - NODE_H) / 2
        parts.append(
            f'<line x1="{cx}" y1="{node.y + NODE_H}" '
            f'x2="{cx}" y2="{mid_y}" '
            f'stroke="#cbd5e1" stroke-width="2"/>'
        )

        # Horizontal bar across children.
        first_cx = node.children[0].x + _couple_width(node.children[0]) / 2
        last_cx = node.children[-1].x + _couple_width(node.children[-1]) / 2
        if len(node.children) > 1:
            parts.append(
                f'<line x1="{first_cx}" y1="{mid_y}" '
                f'x2="{last_cx}" y2="{mid_y}" '
                f'stroke="#cbd5e1" stroke-width="2"/>'
            )

        # Vertical drops to each child.
        for child in node.children:
            child_cx = child.x + _couple_width(child) / 2
            parts.append(
                f'<line x1="{child_cx}" y1="{mid_y}" '
                f'x2="{child_cx}" y2="{child_y}" '
                f'stroke="#cbd5e1" stroke-width="2"/>'
            )
            _render_node(child, parts)


def _render_person(node: TreeNode, x: float, y: float, parts: list[str]) -> None:
    """Render a single person as an SVG rect + text with link."""
    fill = "#eff6ff" if node.genre == "homme" else "#fdf2f8" if node.genre == "femme" else "#f9fafb"
    stroke = "#93c5fd" if node.genre == "homme" else "#f9a8d4" if node.genre == "femme" else "#e5e7eb"
    icon = "\u2642" if node.genre == "homme" else "\u2640" if node.genre == "femme" else ""
    name = escape(node.name)

    parts.append(f'<a href="contacts/{node.slug}.html">')
    parts.append(
        f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" '
        f'rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    )
    parts.append(
        f'<text x="{x + NODE_W / 2}" y="{y + NODE_H / 2 + 5}" '
        f'text-anchor="middle" font-size="12" font-weight="500" '
        f'fill="#1e293b">{icon} {name}</text>'
    )
    parts.append("</a>")

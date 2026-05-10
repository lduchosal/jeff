"""Genealogy service — build family tree and render via Graphviz."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import graphviz

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


def _gender_icon(genre: str) -> str:
    """Return gender symbol."""
    if genre == "homme":
        return "\u2642"
    if genre == "femme":
        return "\u2640"
    return ""


def _node_color(genre: str) -> tuple[str, str]:
    """Return (fillcolor, bordercolor) for a genre."""
    if genre == "homme":
        return "#dbeafe", "#3b82f6"
    if genre == "femme":
        return "#fce7f3", "#ec4899"
    return "#f3f4f6", "#9ca3af"


def tree_to_svg(root: TreeNode) -> str:
    """Render a family tree as SVG using Graphviz."""
    dot = graphviz.Digraph(
        format="svg",
        engine="dot",
        graph_attr={
            "rankdir": "TB",
            "splines": "polyline",
            "nodesep": "0.5",
            "ranksep": "0.7",
            "bgcolor": "transparent",
            "margin": "0.2",
        },
        node_attr={
            "fontname": "Helvetica, Arial, sans-serif",
            "fontsize": "11",
            "penwidth": "1.5",
        },
        edge_attr={
            "color": "#94a3b8",
            "arrowhead": "none",
            "penwidth": "1.2",
        },
    )

    _render_tree(dot, root)

    svg: str = dot.pipe().decode("utf-8")
    idx = svg.find("<svg")
    if idx >= 0:
        svg = svg[idx:]
    return svg


def _couple_node_id(node: TreeNode) -> str:
    """Unique ID for a couple join point."""
    if node.conjoint:
        return f"c_{node.slug}_{node.conjoint.slug}"
    return node.slug


def _render_tree(dot: graphviz.Digraph, node: TreeNode) -> None:
    """Render a node, its conjoint, and children recursively."""
    # Person node.
    fill, border = _node_color(node.genre)
    icon = _gender_icon(node.genre)
    label = f"{icon} {node.name}"
    dot.node(
        node.slug,
        label,
        shape="box",
        style="rounded,filled",
        fillcolor=fill,
        color=border,
        href=f"contacts/{node.slug}.html",
        target="_top",
    )

    if node.conjoint:
        c = node.conjoint
        cfill, cborder = _node_color(c.genre)
        cicon = _gender_icon(c.genre)
        dot.node(
            c.slug,
            f"{cicon} {c.name}",
            shape="box",
            style="rounded,filled",
            fillcolor=cfill,
            color=cborder,
            href=f"contacts/{c.slug}.html",
            target="_top",
        )

        # Couple join point (invisible).
        couple_id = _couple_node_id(node)
        dot.node(couple_id, "", shape="point", width="0.01", height="0.01")

        # Force same rank.
        with dot.subgraph() as s:
            s.attr(rank="same")
            s.node(node.slug)
            s.node(couple_id)
            s.node(c.slug)

        # Spouse edges (thicker, no arrow).
        dot.edge(node.slug, couple_id, penwidth="2", color="#64748b", minlen="1")
        dot.edge(couple_id, c.slug, penwidth="2", color="#64748b", minlen="1")

        parent_id = couple_id
    else:
        parent_id = node.slug

    # Children.
    for child in node.children:
        _render_tree(dot, child)
        child_target = child.slug
        dot.edge(parent_id, child_target)

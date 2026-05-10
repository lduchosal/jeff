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


def tree_to_svg(root: TreeNode) -> str:
    """Render a family tree as SVG using Graphviz."""
    dot = graphviz.Digraph(
        format="svg",
        graph_attr={
            "rankdir": "TB",
            "splines": "ortho",
            "nodesep": "0.6",
            "ranksep": "0.8",
            "bgcolor": "transparent",
        },
        node_attr={
            "shape": "box",
            "style": "rounded,filled",
            "fontname": "Inter, Helvetica, Arial, sans-serif",
            "fontsize": "11",
            "height": "0.4",
            "width": "1.8",
            "penwidth": "2",
        },
        edge_attr={
            "color": "#cbd5e1",
            "arrowhead": "none",
            "penwidth": "1.5",
        },
    )

    _add_nodes(dot, root)
    _add_edges(dot, root)

    # Render to SVG string.
    svg_bytes: bytes = dot.pipe()
    svg: str = svg_bytes.decode("utf-8")
    # Strip XML header and doctype, keep just the <svg> tag.
    idx = svg.find("<svg")
    if idx >= 0:
        svg = svg[idx:]
    return svg


def _person_label(node: TreeNode) -> str:
    """Build the display label for a person node."""
    icon = "\u2642" if node.genre == "homme" else "\u2640" if node.genre == "femme" else ""
    return f"{icon} {node.name}"


def _person_style(node: TreeNode) -> dict[str, str]:
    """Return Graphviz node attributes for a person."""
    if node.genre == "homme":
        return {"fillcolor": "#eff6ff", "color": "#93c5fd"}
    if node.genre == "femme":
        return {"fillcolor": "#fdf2f8", "color": "#f9a8d4"}
    return {"fillcolor": "#f9fafb", "color": "#e5e7eb"}


def _add_nodes(dot: graphviz.Digraph, node: TreeNode) -> None:
    """Add person nodes and couple connectors to the graph."""
    attrs = _person_style(node)
    attrs["href"] = f"contacts/{node.slug}.html"
    dot.node(node.slug, _person_label(node), **attrs)

    if node.conjoint:
        c = node.conjoint
        cattrs = _person_style(c)
        cattrs["href"] = f"contacts/{c.slug}.html"
        dot.node(c.slug, _person_label(c), **cattrs)

        # Invisible couple node to join spouses.
        couple_id = f"couple_{node.slug}_{c.slug}"
        dot.node(couple_id, "", shape="point", width="0", height="0")

        # Same rank for couple.
        with dot.subgraph() as s:
            s.attr(rank="same")
            s.node(node.slug)
            s.node(c.slug)
            s.node(couple_id)

    for child in node.children:
        _add_nodes(dot, child)


def _add_edges(dot: graphviz.Digraph, node: TreeNode) -> None:
    """Add edges between parents and children."""
    if node.conjoint:
        couple_id = f"couple_{node.slug}_{node.conjoint.slug}"
        dot.edge(node.slug, couple_id)
        dot.edge(node.conjoint.slug, couple_id)
        # Children connect from the couple point.
        parent_id = couple_id
    else:
        parent_id = node.slug

    for child in node.children:
        child_id = child.slug
        dot.edge(parent_id, child_id)
        _add_edges(dot, child)

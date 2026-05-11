"""Unit tests for genealogy service."""

from __future__ import annotations

from pathlib import Path

from jeff.services.genealogy import TreeNode, build_family_trees


def _make_contact(tmp_path: Path, slug: str, **fields: str) -> None:
    """Write a contact .md."""
    lines = ["---", f"name: {fields.get('name', slug)}", f"slug: {slug}"]
    for k, v in fields.items():
        if k != "name":
            lines.append(f"{k}: {v}")
    lines.append("---")
    (tmp_path / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")


class TestBuildFamilyTrees:
    """Tests for tree construction."""

    def test_single_person(self, tmp_path: Path) -> None:
        """Single famille contact becomes a root."""
        _make_contact(tmp_path, "jean", name="Jean", relation="famille", genre="homme")
        trees = build_family_trees(tmp_path)
        assert len(trees) == 1
        assert trees[0].name == "Jean"

    def test_couple(self, tmp_path: Path) -> None:
        """Couple detected and deduplicated."""
        _make_contact(
            tmp_path, "jean",
            name="Jean", relation="famille", genre="homme", conjoint="marie",
        )
        _make_contact(
            tmp_path, "marie",
            name="Marie", relation="famille", genre="femme", conjoint="jean",
        )
        trees = build_family_trees(tmp_path)
        assert len(trees) == 1
        assert trees[0].conjoint is not None

    def test_parent_child(self, tmp_path: Path) -> None:
        """Parent-child link creates tree with depth."""
        _make_contact(
            tmp_path, "jacques",
            name="Jacques", relation="famille", genre="homme", enfants="[jean]",
        )
        _make_contact(
            tmp_path, "jean",
            name="Jean", relation="famille", genre="homme", pere="jacques",
        )
        trees = build_family_trees(tmp_path)
        assert len(trees) == 1
        assert len(trees[0].children) == 1
        assert trees[0].children[0].name == "Jean"

    def test_ignores_non_famille(self, tmp_path: Path) -> None:
        """Non-famille contacts are excluded."""
        _make_contact(tmp_path, "jean", name="Jean", relation="ami", genre="homme")
        trees = build_family_trees(tmp_path)
        assert trees == []

    def test_three_generations(self, tmp_path: Path) -> None:
        """Three-generation tree works."""
        _make_contact(
            tmp_path, "grand",
            name="Grand", relation="famille", genre="homme", enfants="[pere]",
        )
        _make_contact(
            tmp_path, "pere",
            name="Pere", relation="famille", genre="homme",
            pere="grand", enfants="[enfant]",
        )
        _make_contact(
            tmp_path, "enfant",
            name="Enfant", relation="famille", genre="homme", pere="pere",
        )
        trees = build_family_trees(tmp_path)
        assert len(trees) == 1
        assert len(trees[0].children) == 1
        assert len(trees[0].children[0].children) == 1

"""Unit tests for the family link service."""

from __future__ import annotations

from pathlib import Path

from jeff.services.famille import (
    check_family_consistency,
    format_existing_links,
    load_famille_context,
    merge_list_field,
    reciprocal_updates,
)


class TestReciprocalUpdates:
    """Tests for reciprocal family link computation."""

    def test_pere_adds_enfants(self) -> None:
        """Setting pere on child adds child to parent's enfants."""
        target: dict = {"slug": "jacques"}
        result = reciprocal_updates("pere", "jean", {}, target)
        assert result == {"enfants": "[jean]"}

    def test_mere_adds_enfants(self) -> None:
        """Setting mere on child adds child to mother's enfants."""
        target: dict = {"slug": "anne"}
        result = reciprocal_updates("mere", "jean", {}, target)
        assert result == {"enfants": "[jean]"}

    def test_conjoint_reciprocal(self) -> None:
        """Setting conjoint is symmetric."""
        target: dict = {"slug": "marie"}
        result = reciprocal_updates("conjoint", "jean", {}, target)
        assert result == {"conjoint": "jean"}

    def test_enfant_uses_genre_homme(self) -> None:
        """Setting enfant on a homme source sets pere on target."""
        source: dict = {"genre": "homme"}
        target: dict = {"slug": "luc"}
        result = reciprocal_updates("enfants", "jean", source, target)
        assert result == {"pere": "jean"}

    def test_enfant_uses_genre_femme(self) -> None:
        """Setting enfant on a femme source sets mere on target."""
        source: dict = {"genre": "femme"}
        target: dict = {"slug": "luc"}
        result = reciprocal_updates("enfants", "anne", source, target)
        assert result == {"mere": "anne"}

    def test_frere_soeur_reciprocal(self) -> None:
        """Setting frere/soeur adds to target's freres_soeurs."""
        target: dict = {"slug": "paul"}
        result = reciprocal_updates("freres_soeurs", "jean", {}, target)
        assert result == {"freres_soeurs": "[jean]"}

    def test_enfants_merges_existing(self) -> None:
        """Existing enfants list is preserved when adding."""
        target: dict = {"enfants": ["luc"]}
        result = reciprocal_updates("pere", "lea", {}, target)
        assert result == {"enfants": "[luc, lea]"}

    def test_enfants_merges_string_format(self) -> None:
        """Handles '[slug1, slug2]' string format."""
        target: dict = {"enfants": "[luc, lea]"}
        result = reciprocal_updates("pere", "paul", {}, target)
        assert "luc" in result["enfants"]
        assert "lea" in result["enfants"]
        assert "paul" in result["enfants"]

    def test_no_duplicate_in_list(self) -> None:
        """Does not add duplicate slugs."""
        target: dict = {"enfants": ["jean"]}
        result = reciprocal_updates("pere", "jean", {}, target)
        assert result == {"enfants": "[jean]"}


class TestMergeListField:
    """Tests for list field merging."""

    def test_empty_existing(self) -> None:
        """Merges into empty field."""
        contact: dict = {}
        result = merge_list_field(contact, "enfants", ["luc"])
        assert result == "[luc]"

    def test_existing_list(self) -> None:
        """Merges with existing list."""
        contact: dict = {"enfants": ["luc"]}
        result = merge_list_field(contact, "enfants", ["lea"])
        assert result == "[luc, lea]"

    def test_existing_string(self) -> None:
        """Merges with existing string format."""
        contact: dict = {"enfants": "[luc]"}
        result = merge_list_field(contact, "enfants", ["lea"])
        assert result == "[luc, lea]"

    def test_no_duplicates(self) -> None:
        """Does not add duplicates."""
        contact: dict = {"enfants": ["luc"]}
        result = merge_list_field(contact, "enfants", ["luc", "lea"])
        assert result == "[luc, lea]"


class TestFormatExistingLinks:
    """Tests for link display formatting."""

    def test_empty(self) -> None:
        """Returns empty list for no links."""
        assert format_existing_links({}) == []

    def test_all_fields(self) -> None:
        """Formats all family link types."""
        data = {
            "pere": "jacques",
            "mere": "anne",
            "conjoint": "marie",
            "freres_soeurs": ["paul"],
            "enfants": ["luc", "lea"],
        }
        links = format_existing_links(data)
        assert len(links) == 5
        assert "père: jacques" in links[0]
        assert "enfants: luc, lea" in links[4]

    def test_string_list_format(self) -> None:
        """Handles '[slug1, slug2]' string format."""
        data = {"enfants": "[luc, lea]"}
        links = format_existing_links(data)
        assert len(links) == 1
        assert "luc" in links[0]
        assert "lea" in links[0]


def _make_contact(tmp_path: Path, slug: str, **fields: str) -> None:
    """Write a minimal contact .md file."""
    lines = ["---", f"name: {fields.get('name', slug)}", f"slug: {slug}"]
    for k, v in fields.items():
        if k != "name":
            lines.append(f"{k}: {v}")
    lines.append("---")
    slug_dir = tmp_path / slug
    slug_dir.mkdir(exist_ok=True)
    (slug_dir / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")


class TestCheckFamilyConsistency:
    """Tests for bidirectional family link verification."""

    def test_no_issues_when_consistent(self, tmp_path: Path) -> None:
        """No issues when links are bidirectional."""
        _make_contact(
            tmp_path,
            "jacques",
            name="Jacques Dupont",
            relation="famille",
            genre="homme",
            enfants="[jean]",
        )
        _make_contact(
            tmp_path,
            "jean",
            name="Jean Dupont",
            relation="famille",
            genre="homme",
            pere="jacques",
        )
        ctx = load_famille_context(tmp_path)
        issues = check_family_consistency(ctx)
        assert len(issues) == 0

    def test_parent_missing_child(self, tmp_path: Path) -> None:
        """Detects when a child has pere but parent has no enfants."""
        _make_contact(
            tmp_path,
            "jacques",
            name="Jacques Dupont",
            relation="famille",
            genre="homme",
        )
        _make_contact(
            tmp_path,
            "jean",
            name="Jean Dupont",
            relation="famille",
            genre="homme",
            pere="jacques",
        )
        ctx = load_famille_context(tmp_path)
        issues = check_family_consistency(ctx)
        assert len(issues) == 1
        assert issues[0].fix_contact == "jacques"
        assert issues[0].fix_field == "enfants"
        assert issues[0].fix_value == "jean"

    def test_child_missing_parent(self, tmp_path: Path) -> None:
        """Detects when parent has enfant but child has no pere/mere."""
        _make_contact(
            tmp_path,
            "jacques",
            name="Jacques Dupont",
            relation="famille",
            genre="homme",
            enfants="[jean]",
        )
        _make_contact(
            tmp_path,
            "jean",
            name="Jean Dupont",
            relation="famille",
            genre="homme",
        )
        ctx = load_famille_context(tmp_path)
        issues = check_family_consistency(ctx)
        assert len(issues) == 1
        assert issues[0].fix_contact == "jean"
        assert issues[0].fix_field == "pere"
        assert issues[0].fix_value == "jacques"

    def test_conjoint_not_reciprocal(self, tmp_path: Path) -> None:
        """Detects when conjoint is one-way."""
        _make_contact(
            tmp_path,
            "jean",
            name="Jean",
            relation="famille",
            conjoint="marie",
        )
        _make_contact(
            tmp_path,
            "marie",
            name="Marie",
            relation="famille",
        )
        ctx = load_famille_context(tmp_path)
        issues = check_family_consistency(ctx)
        assert len(issues) == 1
        assert issues[0].fix_contact == "marie"
        assert issues[0].fix_field == "conjoint"

    def test_sibling_not_reciprocal(self, tmp_path: Path) -> None:
        """Detects when freres_soeurs is one-way."""
        _make_contact(
            tmp_path,
            "jean",
            name="Jean",
            relation="famille",
            freres_soeurs="[paul]",
        )
        _make_contact(
            tmp_path,
            "paul",
            name="Paul",
            relation="famille",
        )
        ctx = load_famille_context(tmp_path)
        issues = check_family_consistency(ctx)
        assert len(issues) == 1
        assert issues[0].fix_contact == "paul"
        assert issues[0].fix_field == "freres_soeurs"

    def test_mere_missing_child(self, tmp_path: Path) -> None:
        """Detects when a child has mere but mother has no enfants."""
        _make_contact(
            tmp_path,
            "anne",
            name="Anne Dupont",
            relation="famille",
            genre="femme",
        )
        _make_contact(
            tmp_path,
            "jean",
            name="Jean Dupont",
            relation="famille",
            mere="anne",
        )
        ctx = load_famille_context(tmp_path)
        issues = check_family_consistency(ctx)
        assert len(issues) == 1
        assert issues[0].fix_contact == "anne"
        assert issues[0].fix_field == "enfants"
        assert issues[0].fix_value == "jean"

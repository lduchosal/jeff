"""Unit tests for the family link service."""

from __future__ import annotations

from jeff.services.famille import (
    format_existing_links,
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

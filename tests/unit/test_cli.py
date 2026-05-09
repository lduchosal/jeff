"""Unit tests for the jeff CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from jeff.cli import cli
from jeff.domain.carddav import Contact, SyncState

SAMPLE_VCARD = """\
BEGIN:VCARD
VERSION:3.0
UID:urn:uuid:test-uid-001
FN:Test User
N:User;Test;;;
EMAIL:test@example.com
TEL:+41790000000
END:VCARD"""


@pytest.fixture()
def runner() -> CliRunner:
    """Click test runner."""
    return CliRunner()


@pytest.fixture()
def jeff_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temp dir with a .jeff config file."""
    monkeypatch.chdir(tmp_path)
    jeff_file = tmp_path / ".jeff"
    jeff_file.write_text(
        "carddav_url=https://dav.example.com/dav.php/addressbooks/u/default/\n"
        "carddav_username=user\n"
        "carddav_password=pass\n"
    )
    return tmp_path


class TestSyncCommand:
    """Tests for the sync command."""

    def test_sync_up_to_date(self, runner: CliRunner, jeff_env: Path) -> None:
        """Reports 'up to date' when nothing changed."""
        books = [
            {"href": "/dav.php/addressbooks/u/default/", "displayname": "Contacts"}
        ]
        with (
            patch(
                "jeff.services.sync.CardDAVClient.discover_addressbooks",
                return_value=books,
            ),
            patch(
                "jeff.services.sync.CardDAVClient.sync",
                return_value=([], [], SyncState(ctag="c1")),
            ),
        ):
            result = runner.invoke(cli, ["sync"])
        assert result.exit_code == 0
        assert "Already up to date" in result.output

    def test_sync_writes_contacts(self, runner: CliRunner, jeff_env: Path) -> None:
        """Creates markdown files for new contacts."""
        books = [
            {"href": "/dav.php/addressbooks/u/default/", "displayname": "Contacts"}
        ]
        contact = Contact(
            href="/dav.php/addressbooks/u/default/test.vcf",
            etag="etag-1",
            vcard_raw=SAMPLE_VCARD,
        )
        new_state = SyncState(
            ctag="c2",
            contacts={"/dav.php/addressbooks/u/default/test.vcf": {"etag": "etag-1"}},
        )
        with (
            patch(
                "jeff.services.sync.CardDAVClient.discover_addressbooks",
                return_value=books,
            ),
            patch(
                "jeff.services.sync.CardDAVClient.sync",
                return_value=([contact], [], new_state),
            ),
        ):
            result = runner.invoke(cli, ["sync"])
        assert result.exit_code == 0
        assert "Written: 1 contact(s)" in result.output
        assert "test-user.md" in result.output
        # Check file was actually created.
        md = jeff_env / "content" / "contacts" / "test-user.md"
        assert md.exists()
        assert "Test User" in md.read_text()

    def test_sync_no_config_fails(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exits with error when no .jeff config exists."""
        monkeypatch.chdir(tmp_path)
        for key in (
            "JEFF_CARDDAV_URL",
            "JEFF_CARDDAV_USERNAME",
            "JEFF_CARDDAV_PASSWORD",
        ):
            monkeypatch.delenv(key, raising=False)
        result = runner.invoke(cli, ["sync"])
        assert result.exit_code != 0
        assert "missing config" in result.output

    def test_version(self, runner: CliRunner) -> None:
        """Displays version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "jeff" in result.output


class TestPublishCommand:
    """Tests for the publish command."""

    def test_publish_empty(self, runner: CliRunner, jeff_env: Path) -> None:
        """Publishes 0 contacts from empty content dir."""
        result = runner.invoke(cli, ["publish"])
        assert result.exit_code == 0
        assert "0 contact" in result.output

    def test_publish_with_contact(self, runner: CliRunner, jeff_env: Path) -> None:
        """Publishes a contact from a .md file."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text("---\nname: Test User\nslug: test\n---\n")
        result = runner.invoke(cli, ["publish"])
        assert result.exit_code == 0
        assert "1 contact" in result.output


class TestTriageCommand:
    """Tests for the triage command."""

    def test_triage_no_contacts(self, runner: CliRunner, jeff_env: Path) -> None:
        """Reports all triaged when content dir has no untriaged contacts."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        result = runner.invoke(cli, ["triage"])
        assert result.exit_code == 0

    def test_triage_skips(self, runner: CliRunner, jeff_env: Path) -> None:
        """Can skip a contact with Enter."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text(
            "---\nname: Test User\nslug: test\nstatus:\n---\n"
        )
        result = runner.invoke(cli, ["triage"], input="s\n")
        assert result.exit_code == 0
        assert (
            "0" in result.output
            or "skip" in result.output.lower()
            or "Triaged" in result.output
        )

    def test_triage_actif(self, runner: CliRunner, jeff_env: Path) -> None:
        """Can mark a contact as actif with relation and priority."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text(
            "---\nname: Test User\nslug: test\nstatus:\nrelation:\n"
            "priorite:\ngenre:\n---\n"
        )
        result = runner.invoke(cli, ["triage"], input="a f h H\n")
        assert result.exit_code == 0
        assert "actif" in result.output
        text = (content / "test.md").read_text()
        assert "status: actif" in text
        assert "relation: famille" in text
        assert "priorite: haute" in text
        assert "genre: homme" in text

    def test_triage_archive(self, runner: CliRunner, jeff_env: Path) -> None:
        """Can archive a contact."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text(
            "---\nname: Test User\nslug: test\nstatus:\n---\n"
        )
        result = runner.invoke(cli, ["triage"], input="r\n")
        assert result.exit_code == 0
        assert "archivé" in result.output

    def test_triage_quit(self, runner: CliRunner, jeff_env: Path) -> None:
        """Can quit early."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text(
            "---\nname: Test User\nslug: test\nstatus:\n---\n"
        )
        result = runner.invoke(cli, ["triage"], input="q\n")
        assert result.exit_code == 0
        assert "Triaged" in result.output


class TestGenreCommand:
    """Tests for the genre command."""

    def test_genre_no_contacts(self, runner: CliRunner, jeff_env: Path) -> None:
        """Reports all set when no contacts need genre."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        result = runner.invoke(cli, ["genre"])
        assert result.exit_code == 0

    def test_genre_set_homme(self, runner: CliRunner, jeff_env: Path) -> None:
        """Sets genre to homme."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text(
            "---\nname: Jean Test\nslug: jean-test\ngenre:\n---\n"
        )
        result = runner.invoke(cli, ["genre"], input="h\n")
        assert result.exit_code == 0
        assert "1" in result.output
        text = (content / "test.md").read_text()
        assert "genre: homme" in text

    def test_genre_set_femme(self, runner: CliRunner, jeff_env: Path) -> None:
        """Sets genre to femme."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text(
            "---\nname: Marie Test\nslug: marie-test\ngenre:\n---\n"
        )
        result = runner.invoke(cli, ["genre"], input="f\n")
        assert result.exit_code == 0
        text = (content / "test.md").read_text()
        assert "genre: femme" in text

    def test_genre_quit(self, runner: CliRunner, jeff_env: Path) -> None:
        """Can quit early."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "test.md").write_text("---\nname: Test\nslug: test\ngenre:\n---\n")
        result = runner.invoke(cli, ["genre"], input="q\n")
        assert result.exit_code == 0


class TestFamilleCommand:
    """Tests for the famille command."""

    def test_famille_no_contacts(self, runner: CliRunner, jeff_env: Path) -> None:
        """Reports no famille contacts when none exist."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        result = runner.invoke(cli, ["famille"])
        assert result.exit_code == 0

    def test_famille_assigns_link(self, runner: CliRunner, jeff_env: Path) -> None:
        """Assigns a family link and writes reciprocal."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "jean-dupont.md").write_text(
            "---\nname: Jean Dupont\nslug: jean-dupont\nname_family: Dupont\n"
            "relation: famille\ngenre: homme\npere:\nmere:\nconjoint:\n"
            "freres_soeurs: []\nenfants: []\n---\n"
        )
        (content / "luc-dupont.md").write_text(
            "---\nname: Luc Dupont\nslug: luc-dupont\nname_family: Dupont\n"
            "relation: famille\ngenre: homme\npere:\nmere:\nconjoint:\n"
            "freres_soeurs: []\nenfants: []\n---\n"
        )
        # 1c = Luc is child of Jean
        result = runner.invoke(cli, ["famille"], input="1c\n\n")
        assert result.exit_code == 0
        jean = (content / "jean-dupont.md").read_text()
        luc = (content / "luc-dupont.md").read_text()
        assert "enfants" in jean and "luc-dupont" in jean
        assert "pere: jean-dupont" in luc

    def test_famille_search(self, runner: CliRunner, jeff_env: Path) -> None:
        """Search mode with ?query works."""
        content = jeff_env / "content" / "contacts"
        content.mkdir(parents=True)
        (content / "jean-dupont.md").write_text(
            "---\nname: Jean Dupont\nslug: jean-dupont\nname_family: Dupont\n"
            "relation: famille\npere:\nmere:\nconjoint:\n"
            "freres_soeurs: []\nenfants: []\n---\n"
        )
        (content / "marie-martin.md").write_text(
            "---\nname: Marie Martin\nslug: marie-martin\nname_family: Martin\n"
            "genre: femme\npere:\nmere:\nconjoint:\n"
            "freres_soeurs: []\nenfants: []\n---\n"
        )
        # Search for Marie, then assign as wife
        result = runner.invoke(cli, ["famille"], input="?marie\n1w\n")
        assert result.exit_code == 0
        assert "Marie Martin" in result.output

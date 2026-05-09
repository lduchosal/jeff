"""Unit tests for the jeff CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from jeff.carddav import Contact, SyncState
from jeff.cli import cli

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
            patch("jeff.services.sync.CardDAVClient.discover_addressbooks", return_value=books),
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
            patch("jeff.services.sync.CardDAVClient.discover_addressbooks", return_value=books),
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

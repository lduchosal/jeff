"""Unit tests for jeff configuration loading."""

from __future__ import annotations

from pathlib import Path

from jeff.config import JeffConfig, _parse_jeff_file, load_config


class TestParseJeffFile:
    """Tests for .jeff file parsing."""

    def test_parses_key_value(self, tmp_path: Path) -> None:
        """Reads simple key=value lines."""
        f = tmp_path / ".jeff"
        f.write_text("carddav_url=https://dav.example.com\ncarddav_username=user\n")
        result = _parse_jeff_file(f)
        assert result["carddav_url"] == "https://dav.example.com"
        assert result["carddav_username"] == "user"

    def test_skips_comments_and_blanks(self, tmp_path: Path) -> None:
        """Ignores comment lines and empty lines."""
        f = tmp_path / ".jeff"
        f.write_text("# comment\n\ncarddav_url=https://x\n  # another\n")
        result = _parse_jeff_file(f)
        assert len(result) == 1
        assert result["carddav_url"] == "https://x"

    def test_handles_equals_in_value(self, tmp_path: Path) -> None:
        """Values containing = are preserved."""
        f = tmp_path / ".jeff"
        f.write_text("carddav_password=p@ss=word\n")
        result = _parse_jeff_file(f)
        assert result["carddav_password"] == "p@ss=word"


class TestLoadConfig:
    """Tests for full config loading with env/file resolution."""

    def test_loads_from_file(self, tmp_path: Path, monkeypatch: object) -> None:
        """Loads config from a .jeff file."""
        monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]
        for key in (
            "JEFF_CARDDAV_URL",
            "JEFF_CARDDAV_USERNAME",
            "JEFF_CARDDAV_PASSWORD",
        ):
            monkeypatch.delenv(key, raising=False)  # type: ignore[attr-defined]
        f = tmp_path / ".jeff"
        f.write_text(
            "carddav_url=https://dav.example.com/dav.php/\n"
            "carddav_username=alice\n"
            "carddav_password=secret\n"
        )
        cfg = load_config()
        assert cfg.carddav_url == "https://dav.example.com/dav.php/"
        assert cfg.carddav_username == "alice"
        assert cfg.carddav_password == "secret"

    def test_env_overrides_file(self, tmp_path: Path, monkeypatch: object) -> None:
        """Env vars take precedence over .jeff file."""
        monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]
        f = tmp_path / ".jeff"
        f.write_text("carddav_url=https://file.example.com\n")
        monkeypatch.setenv("JEFF_CARDDAV_URL", "https://env.example.com")  # type: ignore[attr-defined]
        monkeypatch.delenv("JEFF_CARDDAV_USERNAME", raising=False)  # type: ignore[attr-defined]
        monkeypatch.delenv("JEFF_CARDDAV_PASSWORD", raising=False)  # type: ignore[attr-defined]
        cfg = load_config()
        assert cfg.carddav_url == "https://env.example.com"

    def test_defaults_when_no_file(self, tmp_path: Path, monkeypatch: object) -> None:
        """Returns defaults when no .jeff file and no env vars."""
        monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]
        for key in (
            "JEFF_CARDDAV_URL",
            "JEFF_CARDDAV_USERNAME",
            "JEFF_CARDDAV_PASSWORD",
        ):
            monkeypatch.delenv(key, raising=False)  # type: ignore[attr-defined]
        cfg = load_config()
        assert cfg.carddav_url == ""
        assert cfg.content_dir == "content/contacts"

    def test_explicit_path(self, tmp_path: Path, monkeypatch: object) -> None:
        """Loads from an explicit config file path."""
        for key in (
            "JEFF_CARDDAV_URL",
            "JEFF_CARDDAV_USERNAME",
            "JEFF_CARDDAV_PASSWORD",
        ):
            monkeypatch.delenv(key, raising=False)  # type: ignore[attr-defined]
        f = tmp_path / "custom.jeff"
        f.write_text("carddav_url=https://custom.example.com\n")
        cfg = load_config(config_path=str(f))
        assert cfg.carddav_url == "https://custom.example.com"


class TestValidate:
    """Tests for config validation."""

    def test_valid_config(self) -> None:
        """No errors when all required fields are set."""
        cfg = JeffConfig(
            carddav_url="https://x",
            carddav_username="u",
            carddav_password="p",
        )
        assert cfg.validate() == []

    def test_missing_fields(self) -> None:
        """Reports all missing required fields."""
        cfg = JeffConfig(carddav_url="", carddav_username="", carddav_password="")
        errors = cfg.validate()
        assert "carddav_url" in errors
        assert "carddav_username" in errors
        assert "carddav_password" in errors

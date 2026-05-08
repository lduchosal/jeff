"""Verify package version is set."""

from jeff import __version__


def test_version_is_string() -> None:
    """Version should be a non-empty string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0

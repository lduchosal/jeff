"""Jeff configuration.

Resolves config in this order: env vars (JEFF_*) > ``.jeff`` file (searched upwards from
cwd) > defaults. The ``.jeff`` file uses the same ``key=value`` format as kenboard's
``.ken``.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

JEFF_FILE = ".jeff"


@dataclass
class JeffConfig:
    """Resolved configuration for the jeff sync tool."""

    carddav_url: str
    carddav_username: str
    carddav_password: str
    sync_state_path: str = ".sync-state.json"
    content_dir: str = "content/contacts"
    photo_dir: str = "static/photos"
    publish_url: str = ""
    jeff_file: Path | None = None

    def validate(self) -> list[str]:
        """Return a list of missing required fields."""
        errors: list[str] = []
        if not self.carddav_url:
            errors.append("carddav_url")
        if not self.carddav_username:
            errors.append("carddav_username")
        if not self.carddav_password:
            errors.append("carddav_password")
        return errors


def _find_file_upwards(start: Path, name: str) -> Path | None:
    """Walk up from ``start`` looking for a file named ``name``."""
    cur = start.resolve()
    while True:
        candidate = cur / name
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent


def _parse_jeff_file(path: Path) -> dict[str, str]:
    """Parse a ``.jeff`` file (key=value lines, ``#`` comments allowed)."""
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _check_permissions(path: Path) -> str | None:
    """Return a warning message if file is group/other readable."""
    if sys.platform == "win32":
        return None
    try:
        mode = path.stat().st_mode & 0o777
    except OSError:
        return None
    if mode & 0o077:
        return (
            f"Warning: {path} has mode {mode:o}, expected 600 (user only). "
            f"It contains credentials — fix with: chmod 600 {path}"
        )
    return None


def load_config(config_path: str | None = None) -> JeffConfig:
    """Load config from env vars > .jeff file > defaults.

    Parameters
    ----------
    config_path:
        Explicit path to a ``.jeff`` file. If ``None``, searches
        upwards from cwd.
    """
    jeff_path: Path | None
    if config_path:
        jeff_path = Path(config_path).resolve()
    else:
        jeff_path = _find_file_upwards(Path.cwd(), JEFF_FILE)

    file_data: dict[str, str] = {}
    if jeff_path is not None and jeff_path.is_file():
        warning = _check_permissions(jeff_path)
        if warning:
            print(warning, file=sys.stderr)
        file_data = _parse_jeff_file(jeff_path)

    return JeffConfig(
        carddav_url=(
            os.environ.get("JEFF_CARDDAV_URL") or file_data.get("carddav_url", "")
        ),
        carddav_username=(
            os.environ.get("JEFF_CARDDAV_USERNAME")
            or file_data.get("carddav_username", "")
        ),
        carddav_password=(
            os.environ.get("JEFF_CARDDAV_PASSWORD")
            or file_data.get("carddav_password", "")
        ),
        sync_state_path=(
            os.environ.get("JEFF_SYNC_STATE_PATH")
            or file_data.get("sync_state_path", ".sync-state.json")
        ),
        content_dir=(
            os.environ.get("JEFF_CONTENT_DIR")
            or file_data.get("content_dir", "content/contacts")
        ),
        photo_dir=(
            os.environ.get("JEFF_PHOTO_DIR")
            or file_data.get("photo_dir", "static/photos")
        ),
        publish_url=(
            os.environ.get("JEFF_PUBLISH_URL") or file_data.get("publish_url", "")
        ),
        jeff_file=jeff_path,
    )

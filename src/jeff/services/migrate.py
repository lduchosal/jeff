"""Migration service — move flat contacts to per-contact directories."""

from __future__ import annotations

import shutil
from pathlib import Path

from jeff.services.triage import load_contact


def migrate_to_folders(content_dir: Path) -> tuple[int, int]:
    """Migrate content/contacts/*.md to content/contacts/<slug>/<slug>.md.

    Returns (migrated_count, already_count).
    """
    if not content_dir.is_dir():
        return 0, 0

    migrated = 0
    already = 0

    for md in sorted(content_dir.glob("*.md")):
        data = load_contact(md)
        if not data:
            continue
        slug = data.get("slug", md.stem)
        target_dir = content_dir / slug

        if target_dir.is_dir() and (target_dir / md.name).exists():
            already += 1
            continue

        target_dir.mkdir(exist_ok=True)
        shutil.move(str(md), str(target_dir / md.name))
        migrated += 1

    return migrated, already


def is_migrated(content_dir: Path) -> bool:
    """Check if the content dir uses the folder-per-contact layout."""
    if not content_dir.is_dir():
        return False
    # If there are .md files directly in content_dir, not migrated yet.
    flat_mds = list(content_dir.glob("*.md"))
    return len(flat_mds) == 0

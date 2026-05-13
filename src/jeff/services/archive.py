"""Archive service — move contacts between contacts/ and archive/ by status."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from jeff.services.triage import iter_contact_files, load_contact


@dataclass
class ArchiveResult:
    """Result of an archive operation."""

    archived: list[str]
    restored: list[str]


def run_archive(content_dir: Path, archive_dir: Path) -> ArchiveResult:
    """Move contacts between content_dir and archive_dir based on status.

    - status=archivé in content_dir → move to archive_dir
    - status!=archivé in archive_dir → move back to content_dir
    """
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived: list[str] = []
    restored: list[str] = []

    # Scan content_dir: move archivé contacts to archive_dir.
    for md in iter_contact_files(content_dir):
        data = load_contact(md)
        if not data:
            continue
        if data.get("status") == "archivé":
            slug = data.get("slug", md.parent.name)
            name = data.get("name", slug)
            src_dir = md.parent
            dst_dir = archive_dir / slug
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.move(str(src_dir), str(dst_dir))
            archived.append(name)

    # Scan archive_dir: restore non-archivé contacts to content_dir.
    for md in iter_contact_files(archive_dir):
        data = load_contact(md)
        if not data:
            continue
        if data.get("status") != "archivé":
            slug = data.get("slug", md.parent.name)
            name = data.get("name", slug)
            src_dir = md.parent
            dst_dir = content_dir / slug
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.move(str(src_dir), str(dst_dir))
            restored.append(name)

    return ArchiveResult(archived=archived, restored=restored)

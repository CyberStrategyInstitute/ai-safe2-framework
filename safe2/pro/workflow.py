"""Orchestrate manifest collection, validation, and local writing for `assess --pro`."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from safe2.configuration import resolve_configuration
from safe2.pro.collect import (
    collect_manifest,
    render_manifest,
    render_notes,
    validate_manifest,
)
from safe2.secure_io import write_new_atomic

MANIFEST_FILENAME = "aisafe2-project-manifest-1.json"
NOTES_FILENAME = "pro-collection-notes.json"


@dataclass(frozen=True)
class ProManifest:
    manifest: dict[str, Any]
    path: Path
    sha256: str
    notes_path: Path


def build_and_write(
    root: Path,
    *,
    bundle_dir: Path,
    config_path: Path | None,
    manifest_out: Path | None,
) -> ProManifest:
    """Collect, validate against the vendored schema, then write. Nothing is sent anywhere.

    Validation happens before any manifest byte is written. The local notes explaining
    every unfavourable default or omitted key go in the evidence bundle, never the manifest.
    """
    config, _ = resolve_configuration(explicit=config_path, start=root.absolute())
    collection = collect_manifest(
        root,
        project_name=config["project"].get("name", root.name),
        max_files=config["limits"]["max_files"],
        max_file_bytes=config["limits"]["max_file_bytes"],
    )
    validate_manifest(collection.manifest)
    body = render_manifest(collection.manifest)
    digest = hashlib.sha256(body).hexdigest()
    manifest_path = manifest_out.absolute() if manifest_out is not None else bundle_dir / MANIFEST_FILENAME
    notes_path = bundle_dir / NOTES_FILENAME
    write_new_atomic(manifest_path, body)
    write_new_atomic(notes_path, render_notes(collection.notes, digest))
    return ProManifest(collection.manifest, manifest_path, digest, notes_path)

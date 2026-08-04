"""Contain database and request-controlled paths inside approved directories."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ApprovedPathError(ValueError):
    """Raised when a path escapes its configured trust boundary."""


def configured_dataset_roots() -> tuple[Path, ...]:
    configured = os.getenv("DATASET_ROOTS")
    values = configured.split(os.pathsep) if configured else [str(PROJECT_ROOT / "datasets")]
    return tuple(Path(value).expanduser().resolve() for value in values if value.strip())


def resolve_approved_path(
    candidate: str | Path,
    *,
    roots: Iterable[Path],
    allowed_suffixes: set[str] | None = None,
    must_be_file: bool = False,
) -> Path:
    raw = Path(candidate).expanduser()
    if not raw.is_absolute():
        raw = PROJECT_ROOT / raw
    try:
        resolved = raw.resolve(strict=True)
    except OSError:
        raise ApprovedPathError("Requested path does not exist") from None

    approved = tuple(Path(root).expanduser().resolve() for root in roots)
    if not approved or not any(resolved == root or root in resolved.parents for root in approved):
        raise ApprovedPathError("Requested path is outside the approved directory")
    if must_be_file and not resolved.is_file():
        raise ApprovedPathError("Requested path must be a file")
    if allowed_suffixes is not None and resolved.suffix.lower() not in allowed_suffixes:
        raise ApprovedPathError("Requested file type is not allowed")
    return resolved


def validate_dataset_yaml(candidate: str | Path) -> Path:
    return resolve_approved_path(
        candidate,
        roots=configured_dataset_roots(),
        allowed_suffixes={".yaml", ".yml"},
        must_be_file=True,
    )

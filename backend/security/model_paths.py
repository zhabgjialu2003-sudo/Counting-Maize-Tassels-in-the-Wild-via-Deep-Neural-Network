"""Validation for model artifacts selected through database-controlled paths."""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_MODEL_SUFFIXES = {".pt", ".pth"}


class ModelArtifactError(ValueError):
    """Raised when a model artifact is outside the deployment trust boundary."""


@dataclass(frozen=True)
class ValidatedModelArtifact:
    path: Path
    sha256: str
    byte_size: int


def configured_model_roots() -> tuple[Path, ...]:
    configured = os.getenv("MODEL_ROOTS")
    values = configured.split(os.pathsep) if configured else [str(PROJECT_ROOT / "models")]
    return tuple(Path(value).expanduser().resolve() for value in values if value.strip())


def _inside(path: Path, roots: Iterable[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def validate_model_artifact(
    candidate: str | Path,
    *,
    roots: Iterable[Path] | None = None,
    expected_sha256: str | None = None,
) -> ValidatedModelArtifact:
    raw = Path(candidate).expanduser()
    if not raw.is_absolute():
        raw = PROJECT_ROOT / raw
    try:
        resolved = raw.resolve(strict=True)
    except OSError:
        raise ModelArtifactError("Model artifact does not exist") from None

    approved_roots = tuple(Path(root).expanduser().resolve() for root in (roots or configured_model_roots()))
    if not approved_roots or not _inside(resolved, approved_roots):
        raise ModelArtifactError("Model artifact is outside the approved model directory")
    if not resolved.is_file() or resolved.suffix.lower() not in ALLOWED_MODEL_SUFFIXES:
        raise ModelArtifactError("Model artifact type is not allowed")

    byte_size = resolved.stat().st_size
    if byte_size < 1024:
        prefix = resolved.read_bytes()[:128]
        if prefix.startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise ModelArtifactError("Model artifact is a Git LFS pointer")
        raise ModelArtifactError("Model artifact is too small to be deployable")

    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual_sha256 = digest.hexdigest()
    if expected_sha256 and not hmac.compare_digest(expected_sha256.lower(), actual_sha256):
        raise ModelArtifactError("Model artifact integrity check failed")
    return ValidatedModelArtifact(resolved, actual_sha256, byte_size)

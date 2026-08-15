"""Materialise and verify the two deployment models for cloud builds."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GITHUB_MEDIA_ROOT = (
    "https://media.githubusercontent.com/media/"
    "zhabgjialu2003-sudo/"
    "Counting-Maize-Tassels-in-the-Wild-via-Deep-Neural-Network/main"
)


@dataclass(frozen=True)
class ModelArtifact:
    relative_path: str
    sha256: str

    @property
    def path(self) -> Path:
        return PROJECT_ROOT / self.relative_path

    @property
    def download_url(self) -> str:
        return f"{GITHUB_MEDIA_ROOT}/{self.relative_path}"


ARTIFACTS = (
    ModelArtifact(
        "models/deployment/tassel-best.pt",
        "37bca6b8e817d911424dbd22f720f9cbe00248036e0fc6305ef853f8b38d9913",
    ),
    ModelArtifact(
        "models/deployment/maize-disease.torchscript.pt",
        "4f48a440e2eb35bef220107f9e777f9a3a10dc8fa0b79e0296a022cba700ef17",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_lfs_pointer(path: Path) -> bool:
    return path.is_file() and path.stat().st_size < 1024 and path.read_bytes().startswith(
        b"version https://git-lfs.github.com/spec/v1"
    )


def download_artifact(artifact: ModelArtifact, destination: Path) -> None:
    request = Request(
        artifact.download_url,
        headers={"User-Agent": "maize-detector-render-build/1.0"},
    )
    timeout = int(os.getenv("MODEL_DOWNLOAD_TIMEOUT_SECONDS", "300"))
    with urlopen(request, timeout=timeout) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)


def materialize_artifact(
    artifact: ModelArtifact,
    *,
    downloader=download_artifact,
) -> str:
    path = artifact.path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and not is_lfs_pointer(path):
        actual = sha256_file(path)
        if actual == artifact.sha256:
            return "verified"
        raise RuntimeError(f"Model checksum mismatch: {artifact.relative_path}")

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f"{path.name}.", suffix=".download", dir=path.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        downloader(artifact, temporary)
        actual = sha256_file(temporary)
        if actual != artifact.sha256:
            raise RuntimeError(f"Downloaded model checksum mismatch: {artifact.relative_path}")
        temporary.replace(path)
        temporary = None
        return "downloaded"
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    for artifact in ARTIFACTS:
        result = materialize_artifact(artifact)
        print(f"{result}: {artifact.relative_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

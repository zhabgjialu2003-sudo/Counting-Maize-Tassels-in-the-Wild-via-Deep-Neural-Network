"""Reproducible dependency and model preparation for Render."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from backend.scripts.materialize_deployment_models import main as materialize_models


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run(*arguments: str) -> None:
    subprocess.run([sys.executable, *arguments], cwd=PROJECT_ROOT, check=True)


def main() -> int:
    materialize_models()
    run("-m", "pip", "install", "--upgrade", "pip")
    run(
        "-m",
        "pip",
        "install",
        "--index-url",
        "https://download.pytorch.org/whl/cpu",
        "torch>=2.2,<3",
        "torchvision>=0.17,<1",
    )
    run("-m", "pip", "install", "-r", "backend/requirements.txt")
    # Ultralytics declares the desktop OpenCV distribution. Replace it after
    # dependency resolution so the headless Render host never needs libGL/X11.
    run("-m", "pip", "uninstall", "--yes", "opencv-python")
    run(
        "-m",
        "pip",
        "install",
        "--force-reinstall",
        "--no-deps",
        "opencv-python-headless>=4.8.0",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

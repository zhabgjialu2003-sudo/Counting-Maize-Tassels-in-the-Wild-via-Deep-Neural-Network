"""Training and evaluation controls used by the E.2/E.3 system workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def train_model(
    weights_path: str | Path,
    dataset_yaml: str | Path,
    *,
    epochs: int = 100,
    image_size: int = 640,
    batch: int = 16,
    project: str | Path = "runs/train",
    name: str = "maize-tassel",
) -> dict[str, Any]:
    """Run the BCE training loop through Ultralytics and return its best checkpoint."""
    from ultralytics import YOLO

    model = YOLO(str(weights_path))
    result = model.train(
        data=str(dataset_yaml),
        epochs=epochs,
        imgsz=image_size,
        batch=batch,
        project=str(project),
        name=name,
    )
    save_dir = Path(result.save_dir)
    best = save_dir / "weights" / "best.pt"
    return {
        "save_dir": str(save_dir),
        "best_weights": str(best),
        "completed": best.exists(),
    }


def evaluate_model(
    weights_path: str | Path,
    dataset_yaml: str | Path,
    *,
    image_size: int = 640,
) -> dict[str, float]:
    """Run validation and return the Model entity's BCE evaluation metrics."""
    from ultralytics import YOLO

    metrics = YOLO(str(weights_path)).val(data=str(dataset_yaml), imgsz=image_size)
    return {
        "map50": float(metrics.box.map50),
        "map50_95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
    }

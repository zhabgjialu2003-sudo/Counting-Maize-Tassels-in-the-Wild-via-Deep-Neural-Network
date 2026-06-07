"""YOLO inference module for Maize Tassel Detection.

Loads the trained YOLO model and provides a detect() function
that returns results in the same format as the existing mock data,
so the /api/predict endpoint can swap between mock and real seamlessly.

Usage:
    from inference import get_predictor
    predictor = get_predictor()          # loads model once at startup
    result  = predictor.detect(image_path)  # runs inference
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Path to trained model weights (relative to backend/ or absolute)
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "best.pt"

# Fall back to project root if not in backend/models/
if not DEFAULT_MODEL_PATH.exists():
    DEFAULT_MODEL_PATH = (
        Path(__file__).resolve().parents[1] / "models" / "best.pt"
    )


def _load_yolo(model_path: Path) -> Any:
    """Lazy-load ultralytics YOLO.  Returns None if not installed or model missing."""
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.warning("ultralytics not installed — real inference unavailable")
        return None

    if not model_path.exists():
        logger.warning("Model weights not found at %s — real inference unavailable", model_path)
        return None

    logger.info("Loading YOLO model from %s ...", model_path)
    model = YOLO(str(model_path))
    logger.info("Model loaded successfully")
    return model


class YOLOPredictor:
    """Thin wrapper around a YOLO model that normalises output for the API."""

    def __init__(self, model_path: Path | None = None):
        self._model_path = model_path or DEFAULT_MODEL_PATH
        self._model: Any = None  # ultralytics.YOLO or None
        self._available: bool | None = None  # tri-state check

    @property
    def available(self) -> bool:
        if self._available is None:
            self._model = _load_yolo(self._model_path)
            self._available = self._model is not None
        return self._available

    def detect(self, image_path: Path | str) -> dict[str, Any]:
        """Run inference on a single image.

        Returns a dict matching the existing API response contract:
            {
                "tassel_count": int,
                "confidence_score": float,
                "bbox_data": {"model": str, "boxes": [...], "image_width": int, "image_height": int},
                "processing_time": float,   # seconds
            }
        """
        if not self.available:
            raise RuntimeError("YOLO model is not available for inference")

        t0 = time.perf_counter()

        results = self._model(str(image_path), verbose=False)
        result = results[0]  # first (only) image

        boxes_data = []
        if result.boxes is not None and len(result.boxes) > 0:
            xyxy = result.boxes.xyxy.cpu().numpy() if result.boxes.xyxy is not None else np.array([])
            conf = result.boxes.conf.cpu().numpy() if result.boxes.conf is not None else np.array([])

            for i in range(len(xyxy)):
                x1, y1, x2, y2 = xyxy[i].tolist()
                boxes_data.append({
                    "x": int(x1),
                    "y": int(y1),
                    "width": int(x2 - x1),
                    "height": int(y2 - y1),
                    "confidence": round(float(conf[i]), 4),
                })

        processing_time = round(time.perf_counter() - t0, 3)
        avg_conf = round(float(np.mean(conf)) if len(boxes_data) > 0 else 0.0, 4)

        return {
            "tassel_count": len(boxes_data),
            "confidence_score": avg_conf,
            "bbox_data": {
                "model": "YOLO26s",
                "boxes": boxes_data,
                "image_width": result.orig_shape[1] if result.orig_shape else 0,
                "image_height": result.orig_shape[0] if result.orig_shape else 0,
            },
            "processing_time": processing_time,
        }


# Singleton — initialised once per process
_predictor: YOLOPredictor | None = None


def get_predictor(model_path: Path | None = None) -> YOLOPredictor:
    global _predictor
    if _predictor is None:
        _predictor = YOLOPredictor(model_path)
    return _predictor

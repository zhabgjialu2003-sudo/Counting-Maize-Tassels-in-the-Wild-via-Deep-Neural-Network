"""YOLO inference module for Maize Tassel Detection.

Loads the trained YOLO model and provides a detect() function
that returns a stable response format for the `/api/predict` endpoint.

Supports SAHI-style tiling: large images are split into overlapping
640x640 tiles, inference runs on each tile, and results are merged
with IoU-based NMS to produce full-image detections.

Usage:
    from inference import get_predictor
    predictor = get_predictor()          # loads model once at startup
    result  = predictor.detect(image_path)  # runs inference (with tiling)
"""

from __future__ import annotations

import json
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _configured_model_path() -> Path:
    configured = Path(
        os.getenv("TASSEL_MODEL_PATH", "models/deployment/tassel-best.pt")
    ).expanduser()
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


DEFAULT_MODEL_PATH = _configured_model_path()

# SAHI tiling parameters
TILE_SIZE = 640
TILE_OVERLAP = 0.30   # 30% overlap between tiles
CONF_THRESHOLD = 0.25
IOU_NMS = 0.4


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
    if model_path.stat().st_size < 1024 and model_path.read_bytes().startswith(
        b"version https://git-lfs.github.com/spec/v1"
    ):
        logger.warning("Model path contains a Git LFS pointer, not model weights: %s", model_path)
        return None

    logger.info("Loading YOLO model from %s ...", model_path)
    model = YOLO(str(model_path))
    logger.info("Model loaded successfully")
    return model


def _nms_boxes(boxes_xyxy, scores, iou_thr):
    """Pure-numpy NMS.  boxes: (N,4) xyxy, scores: (N,).  Returns kept indices."""
    if len(boxes_xyxy) == 0:
        return np.array([], dtype=int)
    x1, y1, x2, y2 = boxes_xyxy[:, 0], boxes_xyxy[:, 1], boxes_xyxy[:, 2], boxes_xyxy[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size:
        i = order[0]
        keep.append(i)
        order = order[1:]
        if order.size == 0:
            break
        xx1 = np.maximum(x1[i], x1[order])
        yy1 = np.maximum(y1[i], y1[order])
        xx2 = np.minimum(x2[i], x2[order])
        yy2 = np.minimum(y2[i], y2[order])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        union = areas[i] + areas[order] - inter
        iou = np.where(union > 0, inter / union, 0)
        order = order[iou <= iou_thr]
    return np.array(keep, dtype=int)


class YOLOPredictor:
    """YOLO predictor with automatic SAHI tiling for large images."""

    def __init__(self, model_path: Path | None = None):
        self._model_path = model_path or DEFAULT_MODEL_PATH
        self._model: Any = None  # ultralytics.YOLO or None
        self._available: bool | None = None
        self._cache: dict[str, dict[str, Any]] = {}

    @property
    def model_path(self) -> Path:
        return self._model_path

    @property
    def available(self) -> bool:
        if self._available is None:
            self._model = _load_yolo(self._model_path)
            self._available = self._model is not None
        return self._available

    def _detect_single(
        self,
        image: np.ndarray,
        image_size: int = 640,
        confidence_threshold: float = CONF_THRESHOLD,
    ) -> list[dict]:
        """Run inference on a single image array (no tiling)."""
        from PIL import Image as PILImage
        tmp = PILImage.fromarray(image)
        try:
            import torch
            device = 0 if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
        results = self._model.predict(
            tmp,
            verbose=False,
            conf=confidence_threshold,
            device=device,
            imgsz=image_size,
        )
        result = results[0]

        boxes = []
        if result.boxes is not None and len(result.boxes) > 0:
            xyxy = result.boxes.xyxy.cpu().numpy()
            conf = result.boxes.conf.cpu().numpy()
            for i in range(len(xyxy)):
                x1, y1, x2, y2 = xyxy[i].tolist()
                boxes.append({
                    "x": int(x1), "y": int(y1),
                    "width": int(x2 - x1), "height": int(y2 - y1),
                    "confidence": round(float(conf[i]), 4),
                })
        return boxes

    def detect(self, image_path: Path | str, mode: str = "fast") -> dict[str, Any]:
        """Run fast web inference or accurate SAHI research inference."""
        if not self.available:
            raise RuntimeError("YOLO model is not available for inference")

        image_path = Path(image_path)
        # Use filename + mode as cache key (fast lookup without reading entire file)
        cache_key = f"{image_path.name}:{mode}"
        if cache_key in self._cache:
            cached = dict(self._cache[cache_key])
            cached["cache_hit"] = True
            return cached

        t0 = time.perf_counter()

        img = np.array(Image.open(str(image_path)).convert("RGB"))
        H, W = img.shape[:2]

        if mode == "fast":
            all_boxes = self._detect_single(
                img,
                image_size=2560,
                confidence_threshold=0.15,
            )
        # If image is small enough, run single inference
        elif W <= TILE_SIZE * 1.5 and H <= TILE_SIZE * 1.5:
            all_boxes = self._detect_single(img)
        else:
            # SAHI tiling
            stride = int(TILE_SIZE * (1 - TILE_OVERLAP))
            all_boxes = []
            tile_count = 0

            for y0 in range(0, H, stride):
                for x0 in range(0, W, stride):
                    tile = img[y0:y0 + TILE_SIZE, x0:x0 + TILE_SIZE]
                    th, tw = tile.shape[:2]

                    # Skip tiny edge tiles
                    if th < TILE_SIZE * 0.3 or tw < TILE_SIZE * 0.3:
                        continue

                    tile_boxes = self._detect_single(tile)
                    tile_count += 1

                    # Shift boxes to full-image coordinates
                    for box in tile_boxes:
                        box["x"] += x0
                        box["y"] += y0
                        all_boxes.append(box)

            logger.info("SAHI: %d tiles, %d raw detections", tile_count, len(all_boxes))

            # Merge overlapping detections with NMS
            if len(all_boxes) > 1:
                xyxy = np.array([[b["x"], b["y"],
                                  b["x"] + b["width"], b["y"] + b["height"]]
                                 for b in all_boxes], dtype=float)
                scores = np.array([b["confidence"] for b in all_boxes], dtype=float)
                keep = _nms_boxes(xyxy, scores, IOU_NMS)
                all_boxes = [all_boxes[i] for i in keep]
                logger.info("After NMS: %d boxes", len(all_boxes))

        processing_time = round(time.perf_counter() - t0, 3)
        avg_conf = round(float(np.mean([b["confidence"] for b in all_boxes]))
                         if all_boxes else 0.0, 4)

        output = {
            "tassel_count": len(all_boxes),
            "confidence_score": avg_conf,
            "bbox_data": {
                "model": "YOLO26s",
                "boxes": all_boxes,
                "image_width": W,
                "image_height": H,
            },
            "processing_time": processing_time,
            "cache_hit": False,
            "inference_mode": mode,
        }
        self._cache[cache_key] = dict(output)
        return output


# Singleton — initialised once per process
_predictor: YOLOPredictor | None = None


def get_predictor(model_path: Path | None = None) -> YOLOPredictor:
    global _predictor
    if _predictor is None:
        _predictor = YOLOPredictor(model_path)
    return _predictor


def activate_predictor(model_path: Path | str) -> YOLOPredictor:
    """Load and activate a model only after its weights pass a health check."""
    global _predictor
    candidate = YOLOPredictor(Path(model_path))
    if not candidate.available:
        raise RuntimeError(f"Model could not be loaded from {model_path}")
    _predictor = candidate
    return candidate

"""Lazy TorchScript inference for maize leaf-disease assistance."""

from __future__ import annotations

import io
import json
import logging
import math
import os
import threading
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _configured_path(environment_name: str, default: str) -> Path:
    configured = Path(os.getenv(environment_name, default)).expanduser()
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


DEFAULT_METADATA_DIR = PROJECT_ROOT / "models" / "disease"
DEFAULT_MODEL_PATH = _configured_path(
    "DISEASE_MODEL_PATH",
    "models/deployment/maize-disease.torchscript.pt",
)
REQUIRED_CLASSES = (
    "healthy",
    "common_rust",
    "gray_leaf_spot",
    "northern_leaf_blight",
)
MAX_DECODED_PIXELS = 36_000_000


class DiseaseModelUnavailable(RuntimeError):
    """Raised when a safe disease artifact cannot be activated."""


class InvalidDiseaseImage(ValueError):
    """Raised when uploaded bytes are not a safe decodable image."""


def load_rgb_image(data: bytes) -> Image.Image:
    if not data:
        raise InvalidDiseaseImage("The uploaded image is empty")
    try:
        with Image.open(io.BytesIO(data)) as opened:
            opened.verify()
        with Image.open(io.BytesIO(data)) as opened:
            width, height = opened.size
            if width <= 0 or height <= 0 or width * height > MAX_DECODED_PIXELS:
                raise InvalidDiseaseImage("The decoded image dimensions are not allowed")
            return ImageOps.exif_transpose(opened).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidDiseaseImage("The uploaded file is not a valid JPG or PNG image") from exc


def assess_image_quality(image: Image.Image) -> dict[str, Any]:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    gray_u8 = np.asarray(image.convert("L"), dtype=np.uint8)
    gray = gray_u8.astype(np.float32)
    height, width = gray.shape
    brightness = float(gray.mean())
    contrast = float(gray.std())

    try:
        import cv2

        blur_score = float(cv2.Laplacian(gray_u8, cv2.CV_64F).var())
    except ImportError:
        horizontal = np.abs(np.diff(gray, axis=1)).mean() if width > 1 else 0.0
        vertical = np.abs(np.diff(gray, axis=0)).mean() if height > 1 else 0.0
        blur_score = float((horizontal + vertical) * 4.0)

    issues: list[str] = []
    if min(width, height) < 224:
        issues.append("too_small")
    if brightness < 38:
        issues.append("too_dark")
    elif brightness > 224:
        issues.append("too_bright")
    if contrast < 22:
        issues.append("low_contrast")
    if blur_score < 35:
        issues.append("blurry")

    severe = {"too_small", "too_dark", "too_bright", "blurry"}
    return {
        "status": "retake" if severe.intersection(issues) else "pass",
        "issues": issues,
        "measurements": {
            "width": int(width),
            "height": int(height),
            "brightness": round(brightness, 2),
            "contrast": round(contrast, 2),
            "blur_score": round(blur_score, 2),
            "mean_rgb": [round(float(value), 2) for value in rgb.mean(axis=(0, 1))],
        },
    }


def validate_metadata(metadata: dict[str, Any], allow_candidate: bool = False) -> None:
    if metadata.get("artifact_schema_version") != "1.0":
        raise DiseaseModelUnavailable("Unsupported disease artifact schema")
    if tuple(metadata.get("classes", ())) != REQUIRED_CLASSES:
        raise DiseaseModelUnavailable("Disease class order does not match the backend contract")
    if not metadata.get("deployment_ready", False) and not allow_candidate:
        raise DiseaseModelUnavailable(
            "The disease artifact is a candidate and has not passed deployment gates"
        )
    for key in ("image_size", "normalization", "temperature", "thresholds", "model_version"):
        if key not in metadata:
            raise DiseaseModelUnavailable(f"Disease metadata is missing {key}")


class DiseasePredictor:
    def __init__(
        self,
        artifact_dir: Path | str | None = None,
        model_path: Path | str | None = None,
        allow_candidate: bool | None = None,
    ):
        self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else DEFAULT_METADATA_DIR
        self.allow_candidate = (
            os.getenv("DISEASE_ALLOW_CANDIDATE", "false").lower() == "true"
            if allow_candidate is None
            else allow_candidate
        )
        self.metadata_path = self.artifact_dir / "metadata.json"
        if model_path is not None:
            self.model_path = Path(model_path)
        elif artifact_dir is not None:
            self.model_path = self.artifact_dir / "maize_disease.torchscript.pt"
        else:
            self.model_path = DEFAULT_MODEL_PATH
        self._metadata: dict[str, Any] | None = None
        self._model: Any = None
        self._load_error: str | None = None
        self._lock = threading.RLock()

    @property
    def metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            if not self.metadata_path.exists():
                raise DiseaseModelUnavailable(
                    f"Disease metadata was not found at {self.metadata_path}"
                )
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            validate_metadata(metadata, self.allow_candidate)
            self._metadata = metadata
        return self._metadata

    @property
    def available(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except Exception as exc:
            self._load_error = str(exc)
            return False

    def health(self) -> dict[str, Any]:
        available = self.available
        metadata = self._metadata or {}
        if not available and self._load_error:
            logger.info("Disease model health check failed: %s", self._load_error)
        return {
            "available": available,
            "status": "ready" if available else "unavailable",
            "model_version": metadata.get("model_version"),
            "deployment_ready": metadata.get("deployment_ready", False),
            "error": None if available else "Disease artifact unavailable",
        }

    def _ensure_loaded(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            metadata = self.metadata
            if not self.model_path.exists():
                raise DiseaseModelUnavailable(
                    f"Disease TorchScript model was not found at {self.model_path}"
                )
            if self.model_path.stat().st_size < 1024 and self.model_path.read_bytes().startswith(
                b"version https://git-lfs.github.com/spec/v1"
            ):
                raise DiseaseModelUnavailable(
                    f"Disease model path contains a Git LFS pointer: {self.model_path}"
                )
            try:
                import torch
            except ImportError as exc:
                raise DiseaseModelUnavailable("PyTorch is not installed") from exc
        # The Windows C++ path overload may reject valid non-ASCII user or
        # workspace names. A Python-owned file handle is Unicode-safe.
        with self.model_path.open("rb") as model_file:
            model = torch.jit.load(model_file, map_location="cpu")
            model.eval()
            self._model = model
            logger.info(
                "Loaded disease model %s (%s)",
                metadata["model_version"],
                self.model_path,
            )

    def _tensor(self, image: Image.Image):
        import torch

        metadata = self.metadata
        size = int(metadata["image_size"])
        resize_size = int(metadata.get("resize_size", round(size * 256 / 224)))
        width, height = image.size
        scale = resize_size / min(width, height)
        resized = image.resize(
            (round(width * scale), round(height * scale)),
            Image.Resampling.BILINEAR,
        )
        left = max((resized.width - size) // 2, 0)
        top = max((resized.height - size) // 2, 0)
        image = resized.crop((left, top, left + size, top + size))
        array = np.asarray(image, dtype=np.float32) / 255.0
        mean = np.asarray(metadata["normalization"]["mean"], dtype=np.float32)
        std = np.asarray(metadata["normalization"]["std"], dtype=np.float32)
        array = (array - mean) / std
        return torch.from_numpy(array.transpose(2, 0, 1)).unsqueeze(0)

    def predict_bytes(self, data: bytes) -> dict[str, Any]:
        image = load_rgb_image(data)
        quality = assess_image_quality(image)
        if quality["status"] == "retake":
            return {
                "status": "retake_required",
                "condition_code": None,
                "quality": quality,
                "technical": {"model_version": self.metadata.get("model_version")},
            }

        self._ensure_loaded()
        import torch

        with self._lock, torch.inference_mode():
            logits = self._model(self._tensor(image))
            if isinstance(logits, (tuple, list)):
                logits = logits[0]
            logits = logits.float().reshape(1, -1)
            temperature = max(float(self.metadata["temperature"]), 1e-4)
            probabilities = torch.softmax(logits / temperature, dim=1)[0].cpu().numpy()

        confidence = float(probabilities.max())
        order = probabilities.argsort()[::-1]
        predicted_index = int(order[0])
        margin = float(probabilities[order[0]] - probabilities[order[1]])
        entropy = float(
            -sum(float(p) * math.log(max(float(p), 1e-12)) for p in probabilities)
            / math.log(len(probabilities))
        )
        thresholds = self.metadata["thresholds"]
        accepted = (
            confidence >= float(thresholds["min_confidence"])
            and margin >= float(thresholds["min_margin"])
            and entropy <= float(thresholds["max_normalized_entropy"])
        )
        condition_code = self.metadata["classes"][predicted_index]
        strongly_outside = (
            confidence < float(thresholds.get("unknown_max_confidence", 0.40))
            or entropy > float(thresholds.get("unknown_min_normalized_entropy", 0.95))
        )
        status = "supported" if accepted else ("unsupported" if strongly_outside else "uncertain")

        return {
            "status": status,
            "condition_code": condition_code,
            "quality": quality,
            "technical": {
                "probabilities": {
                    name: round(float(probabilities[index]), 6)
                    for index, name in enumerate(self.metadata["classes"])
                },
                "confidence": round(confidence, 6),
                "margin": round(margin, 6),
                "entropy": round(entropy, 6),
                "thresholds": thresholds,
                "model_version": self.metadata["model_version"],
            },
        }


_predictor: DiseasePredictor | None = None


def get_disease_predictor(
    artifact_dir: Path | str | None = None,
) -> DiseasePredictor:
    global _predictor
    if _predictor is None or artifact_dir is not None:
        _predictor = DiseasePredictor(artifact_dir)
    return _predictor

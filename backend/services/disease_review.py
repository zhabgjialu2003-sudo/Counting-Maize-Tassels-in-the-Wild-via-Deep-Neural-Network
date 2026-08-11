"""Shared policy for recommending professional review of leaf screenings."""

from __future__ import annotations

import os
from typing import Any


DEFAULT_REVIEW_CONFIDENCE_THRESHOLD = 0.70


def review_confidence_threshold() -> float:
    """Return a bounded confidence threshold from configuration."""
    raw = os.getenv(
        "DISEASE_REVIEW_CONFIDENCE_THRESHOLD",
        str(DEFAULT_REVIEW_CONFIDENCE_THRESHOLD),
    )
    try:
        threshold = float(raw)
    except (TypeError, ValueError):
        threshold = DEFAULT_REVIEW_CONFIDENCE_THRESHOLD
    return min(max(threshold, 0.0), 1.0)


def build_review_recommendation(response: dict[str, Any]) -> dict[str, Any]:
    """Explain whether a saved AI screening should receive human review."""
    reasons: list[str] = []
    status = str(response.get("status") or "").strip().lower()
    if status != "supported":
        reasons.append("screening_uncertain")

    quality = response.get("quality") or {}
    if str(quality.get("status") or "").strip().lower() != "pass":
        reasons.append("image_quality")

    condition = response.get("possible_condition") or {}
    condition_code = str(condition.get("code") or "").strip().lower()
    if condition_code and condition_code != "healthy":
        reasons.append("possible_disease")

    technical = response.get("technical") or {}
    threshold = review_confidence_threshold()
    try:
        confidence = float(technical.get("confidence"))
    except (TypeError, ValueError):
        confidence = None
    if confidence is None or confidence < threshold:
        reasons.append("low_confidence")

    return {
        "recommended": bool(reasons),
        "reasons": list(dict.fromkeys(reasons)),
        "confidence_threshold": threshold,
    }

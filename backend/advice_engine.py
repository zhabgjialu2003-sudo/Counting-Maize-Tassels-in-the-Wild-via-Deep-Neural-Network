"""Bilingual, rule-based agronomy response formatter.

The classifier supplies structured evidence. This module turns that evidence
into calm, actionable language without inventing agronomic facts.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_KNOWLEDGE_PATH = Path(__file__).with_name("agronomy_knowledge.json")
SUPPORTED_LANGUAGES = {"en", "zh-CN"}


@lru_cache(maxsize=4)
def load_knowledge(path: str | Path = DEFAULT_KNOWLEDGE_PATH) -> dict[str, Any]:
    knowledge_path = Path(path)
    data = json.loads(knowledge_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0":
        raise ValueError("Unsupported agronomy knowledge schema")
    return data


def normalize_language(language: str | None) -> str:
    text = str(language or "en").strip().lower()
    return "zh-CN" if text.startswith("zh") else "en"


def _localized(value: dict[str, Any], language: str) -> Any:
    return value.get(language, value.get("en"))


def confidence_band(confidence: float, status: str) -> str:
    if status != "supported":
        return "needs_confirmation"
    if confidence >= 0.90:
        return "strong_match"
    if confidence >= 0.75:
        return "moderate_match"
    return "needs_confirmation"


def _headline(
    status: str,
    condition_name: str | None,
    language: str,
) -> str:
    if status == "supported" and condition_name:
        if language == "zh-CN":
            return f"图片中的特征与{condition_name}较为相似，但仍建议结合田间情况确认。"
        return (
            f"The visible signs are similar to {condition_name}, "
            "but the field context should still be checked."
        )
    if status == "uncertain":
        return (
            "图片里有一些相似迹象，但证据还不够，先补充信息会更稳妥。"
            if language == "zh-CN"
            else "There are some matching signs, but more evidence is needed for a reliable result."
        )
    if status == "retake_required":
        return (
            "这张照片暂时看不清关键细节，重新拍一张就能继续。"
            if language == "zh-CN"
            else "Key details are not clear enough in this photo. A new photo will help."
        )
    return (
        "目前无法把这张图片可靠地归入已支持的玉米叶片情况。"
        if language == "zh-CN"
        else "I cannot reliably match this image to the supported maize leaf conditions."
    )


def build_advice(
    prediction: dict[str, Any],
    language: str | None = None,
    context: dict[str, Any] | None = None,
    knowledge_path: str | Path = DEFAULT_KNOWLEDGE_PATH,
) -> dict[str, Any]:
    """Return the stable API response for a structured model prediction."""
    language = normalize_language(language)
    context = context or {}
    knowledge = load_knowledge(knowledge_path)
    status = prediction.get("status", "unsupported")
    condition_code = prediction.get("condition_code")
    condition = knowledge["conditions"].get(condition_code or "")
    condition_name = _localized(condition["name"], language) if condition else None

    quality_issues = []
    for issue in prediction.get("quality", {}).get("issues", []):
        entry = knowledge["quality_issues"].get(issue)
        if entry:
            quality_issues.append(
                {"code": issue, "message": _localized(entry, language)}
            )

    if status == "retake_required":
        observation = [item["message"] for item in quality_issues]
        follow_up_questions: list[str] = []
        next_steps = observation[:]
    elif status in {"unsupported", "uncertain"}:
        state = knowledge["states"][status]
        observation = [_localized(state, language)]
        follow_up_questions = (
            _localized(condition["questions"], language)[:3] if condition else []
        )
        next_steps = (
            _localized(condition["next_steps"], language)[:3]
            if condition
            else [
                (
                    "请补拍叶片正反面近照，并拍一张包含整株及周围植株的照片。"
                    if language == "zh-CN"
                    else "Take close photos of both leaf surfaces and one wider photo of the whole plant."
                )
            ]
        )
    else:
        # Knowledge is cached and shared between requests. Copy localized lists
        # before adding request-specific context to prevent cross-user leakage.
        observation = (
            list(_localized(condition["supported_observations"], language))
            if condition
            else []
        )
        follow_up_questions = (
            _localized(condition["questions"], language)[:3] if condition else []
        )
        next_steps = (
            _localized(condition["next_steps"], language)[:3] if condition else []
        )

    if context.get("symptom_spread") and status != "retake_required":
        spread_note = (
            f"用户补充的扩散情况：{context['symptom_spread']}"
            if language == "zh-CN"
            else f"Reported spread: {context['symptom_spread']}"
        )
        observation.append(spread_note)

    confidence = float(prediction.get("technical", {}).get("confidence", 0.0))
    return {
        "status": status,
        "language": language,
        "headline": _headline(status, condition_name, language),
        "observation": observation,
        "possible_condition": (
            {
                "code": condition_code,
                "display_name": condition_name,
                "confidence_band": confidence_band(confidence, status),
            }
            if condition
            else None
        ),
        "follow_up_questions": follow_up_questions,
        "next_steps": next_steps,
        "quality": {
            "status": prediction.get("quality", {}).get("status", "unknown"),
            "issues": quality_issues,
            "measurements": prediction.get("quality", {}).get("measurements", {}),
        },
        "technical": prediction.get("technical", {}),
        "context_received": {
            key: value for key, value in context.items() if value not in (None, "")
        },
        "safety_note": _localized(knowledge["safety"], language),
        "knowledge_version": knowledge["knowledge_version"],
    }

import io
import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from PIL import Image

import backend.app as backend
from backend.advice_engine import build_advice, normalize_language
from backend.disease_inference import (
    DiseaseModelUnavailable,
    DiseasePredictor,
    InvalidDiseaseImage,
    assess_image_quality,
    load_rgb_image,
    validate_metadata,
)


class DiseaseAssistantUnitTests(unittest.TestCase):
    def test_chinese_language_normalization(self):
        self.assertEqual(normalize_language("zh"), "zh-CN")
        self.assertEqual(normalize_language("zh-Hans"), "zh-CN")
        self.assertEqual(normalize_language("en-GB"), "en")

    def test_human_centred_chinese_supported_response(self):
        response = build_advice(
            {
                "status": "supported",
                "condition_code": "gray_leaf_spot",
                "quality": {"status": "pass", "issues": [], "measurements": {}},
                "technical": {"confidence": 0.91, "model_version": "test-v1"},
            },
            language="zh-CN",
        )
        self.assertIn("灰斑病", response["headline"])
        self.assertNotIn("确诊", response["headline"])
        self.assertEqual(
            response["possible_condition"]["confidence_band"], "strong_match"
        )
        self.assertGreaterEqual(len(response["next_steps"]), 2)
        self.assertIn("并非确诊", response["safety_note"])

    def test_uncertain_response_always_offers_a_next_step(self):
        response = build_advice(
            {
                "status": "uncertain",
                "condition_code": "common_rust",
                "quality": {"status": "pass", "issues": [], "measurements": {}},
                "technical": {"confidence": 0.57, "model_version": "test-v1"},
            },
            language="en",
        )
        self.assertTrue(response["next_steps"])
        self.assertTrue(response["follow_up_questions"])
        self.assertEqual(
            response["possible_condition"]["confidence_band"], "needs_confirmation"
        )

    def test_request_context_does_not_leak_into_later_advice(self):
        prediction = {
            "status": "supported",
            "condition_code": "gray_leaf_spot",
            "quality": {"status": "pass", "issues": [], "measurements": {}},
            "technical": {"confidence": 0.99, "model_version": "test-v1"},
        }

        first = build_advice(
            prediction,
            language="en",
            context={"symptom_spread": "first request only"},
        )
        second = build_advice(
            prediction,
            language="en",
            context={"symptom_spread": "second request only"},
        )

        self.assertTrue(
            any("first request only" in item for item in first["observation"])
        )
        self.assertFalse(
            any("first request only" in item for item in second["observation"])
        )
        self.assertTrue(
            any("second request only" in item for item in second["observation"])
        )

    def test_small_dark_image_requests_a_retake(self):
        image = Image.new("RGB", (120, 100), color=(5, 5, 5))
        result = assess_image_quality(image)
        self.assertEqual(result["status"], "retake")
        self.assertIn("too_small", result["issues"])
        self.assertIn("too_dark", result["issues"])

    def test_invalid_image_bytes_are_rejected(self):
        with self.assertRaises(InvalidDiseaseImage):
            load_rgb_image(b"this is not an image")

    def test_candidate_metadata_is_not_production_ready(self):
        metadata = {
            "artifact_schema_version": "1.0",
            "deployment_ready": False,
            "classes": [
                "healthy",
                "common_rust",
                "gray_leaf_spot",
                "northern_leaf_blight",
            ],
            "image_size": 224,
            "normalization": {"mean": [0, 0, 0], "std": [1, 1, 1]},
            "temperature": 1.0,
            "thresholds": {},
            "model_version": "candidate",
        }
        with self.assertRaises(DiseaseModelUnavailable):
            validate_metadata(metadata)
        validate_metadata(metadata, allow_candidate=True)

    def test_model_health_does_not_expose_an_internal_path(self):
        with tempfile.TemporaryDirectory() as directory:
            health = DiseasePredictor(directory).health()
            self.assertFalse(health["available"])
            self.assertEqual(health["error"], "Disease artifact unavailable")
            self.assertNotIn(directory, health["error"])

    def test_torchscript_artifact_runs_through_backend_contract(self):
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch is not installed")

        class ConstantModel(torch.nn.Module):
            def forward(self, inputs):
                logits = torch.tensor(
                    [[8.0, 0.0, 0.0, 0.0]],
                    dtype=inputs.dtype,
                    device=inputs.device,
                )
                return logits.repeat(inputs.shape[0], 1)

        metadata = {
            "artifact_schema_version": "1.0",
            "deployment_ready": True,
            "classes": [
                "healthy",
                "common_rust",
                "gray_leaf_spot",
                "northern_leaf_blight",
            ],
            "image_size": 224,
            "resize_size": 256,
            "normalization": {
                "mean": [0.485, 0.456, 0.406],
                "std": [0.229, 0.224, 0.225],
            },
            "temperature": 1.0,
            "thresholds": {
                "min_confidence": 0.7,
                "min_margin": 0.2,
                "max_normalized_entropy": 0.7,
                "unknown_max_confidence": 0.4,
                "unknown_min_normalized_entropy": 0.95,
            },
            "model_version": "test-runtime",
        }
        checker = np.zeros((320, 320, 3), dtype=np.uint8)
        checker[::2, ::2] = (70, 190, 80)
        checker[1::2, 1::2] = (230, 245, 180)
        image = Image.fromarray(checker, mode="RGB")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")

        with tempfile.TemporaryDirectory() as directory:
            artifact_dir = Path(directory)
            (artifact_dir / "metadata.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            traced = torch.jit.trace(
                ConstantModel().eval(),
                torch.randn(1, 3, 224, 224),
            )
            traced.save(str(artifact_dir / "maize_disease.torchscript.pt"))
            result = DiseasePredictor(artifact_dir).predict_bytes(
                image_bytes.getvalue()
            )

        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["condition_code"], "healthy")
        self.assertEqual(result["technical"]["model_version"], "test-runtime")


class DiseaseAssistantApiContractTests(unittest.TestCase):
    def setUp(self):
        backend.app.config["TESTING"] = True
        self.client = backend.app.test_client()

    def token(self, role="Agronomist", user_id=3):
        return backend.issue_access_token(
            {
                "user_id": user_id,
                "name": "Disease Assistant Test",
                "email": "disease@example.com",
                "role": role,
                "status": "active",
            }
        )

    def headers(self):
        return {"Authorization": f"Bearer {self.token()}"}

    def test_diagnosis_requires_authentication(self):
        response = self.client.post("/api/agronomy/diagnose")
        self.assertEqual(response.status_code, 401)

    def test_diagnosis_requires_an_image(self):
        response = self.client.post(
            "/api/agronomy/diagnose",
            headers=self.headers(),
            json={"language": "zh-CN"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("image_id", response.get_json()["message"])

    def test_existing_tassel_route_is_still_registered(self):
        rules = {rule.rule for rule in backend.app.url_map.iter_rules()}
        self.assertIn("/api/predict", rules)
        self.assertIn("/api/agronomy/diagnose", rules)

    def test_review_rejects_an_invalid_decision_before_database_access(self):
        response = self.client.post(
            "/api/agronomy/diagnoses/1/review",
            headers=self.headers(),
            json={"decision": "maybe", "note": "Field review"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("confirmed", response.get_json()["message"])

    def test_bilingual_diagnosis_survives_a_persistence_failure(self):
        class FakePredictor:
            def predict_bytes(self, _data):
                return {
                    "status": "supported",
                    "condition_code": "common_rust",
                    "quality": {
                        "status": "pass",
                        "issues": [],
                        "measurements": {"width": 320, "height": 320},
                    },
                    "technical": {
                        "confidence": 0.93,
                        "entropy": 0.12,
                        "model_version": "fake-contract-model",
                    },
                }

        old_factory = backend.get_disease_predictor
        old_db_connection = backend.db_connection

        connection_count = 0

        @contextmanager
        def persistence_failure_database():
            nonlocal connection_count
            connection_count += 1
            if connection_count > 1:
                raise RuntimeError("simulated persistence failure")
            with old_db_connection() as conn:
                yield conn

        backend.get_disease_predictor = lambda: FakePredictor()
        backend.db_connection = persistence_failure_database
        try:
            image = Image.new("RGB", (320, 320), color=(80, 160, 60))
            content = io.BytesIO()
            image.save(content, format="PNG")
            content.seek(0)
            response = self.client.post(
                "/api/agronomy/diagnose",
                headers=self.headers(),
                data={
                    "language": "zh-CN",
                    "image": (content, "leaf.png"),
                },
                content_type="multipart/form-data",
            )
        finally:
            backend.get_disease_predictor = old_factory
            backend.db_connection = old_db_connection

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "supported")
        self.assertIn("普通锈病", payload["headline"])
        self.assertEqual(payload["persistence"]["status"], "failed")

    def test_frontend_contains_bilingual_diagnosis_flow(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend/pages/agronomist.html").read_text(encoding="utf-8")
        api = (root / "frontend/js/api.js").read_text(encoding="utf-8")
        self.assertIn("Leaf Assistant (C.1+)", html)
        self.assertIn("叶片助手（C.1+）", html)
        self.assertIn("apiDiagnoseDisease", api)


if __name__ == "__main__":
    unittest.main()

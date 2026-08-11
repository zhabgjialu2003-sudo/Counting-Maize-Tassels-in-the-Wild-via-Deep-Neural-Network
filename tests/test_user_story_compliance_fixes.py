import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from PIL import Image

import backend.app as backend
from backend.database import db_connection
from backend.security.model_paths import ModelArtifactError
from backend.security.path_controls import ApprovedPathError


def png_bytes(colour=(35, 135, 55)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (48, 32), colour).save(output, format="PNG")
    return output.getvalue()


class FakePredictor:
    available = True
    model_path = Path("models/deployment/tassel-best.pt")

    def detect(self, _image_path, mode="fast"):
        return {
            "tassel_count": 2,
            "confidence_score": 0.91,
            "processing_time": 0.02,
            "bbox_data": {
                "image_width": 48,
                "image_height": 32,
                "boxes": [
                    {"x": 4, "y": 4, "width": 8, "height": 10, "confidence": 0.92},
                    {"x": 24, "y": 5, "width": 9, "height": 11, "confidence": 0.90},
                ],
            },
            "inference_mode": mode,
            "cache_hit": False,
        }


class UserStoryComplianceFixTests(unittest.TestCase):
    def setUp(self):
        backend.app.config["TESTING"] = True
        self.client = backend.app.test_client()
        self.old_upload_dir = backend.UPLOAD_DIR
        self.temp_uploads = tempfile.TemporaryDirectory()
        backend.UPLOAD_DIR = Path(self.temp_uploads.name)
        self.image_ids = []
        with db_connection() as conn:
            rows = conn.execute(
                "SELECT model_id, map50, precision_score, recall_score "
                "FROM models WHERE model_id IN (1, 2) ORDER BY model_id"
            ).fetchall()
        self.original_metrics = [dict(row) for row in rows]

    def tearDown(self):
        with db_connection() as conn:
            if self.image_ids:
                conn.execute(
                    "DELETE FROM detection_results WHERE image_id = ANY(%s)",
                    (list(set(self.image_ids)),),
                )
                conn.execute(
                    "DELETE FROM images WHERE image_id = ANY(%s)",
                    (list(set(self.image_ids)),),
                )
            for model in self.original_metrics:
                conn.execute(
                    "UPDATE models SET map50 = %s, precision_score = %s, recall_score = %s "
                    "WHERE model_id = %s",
                    (
                        model["map50"],
                        model["precision_score"],
                        model["recall_score"],
                        model["model_id"],
                    ),
                )
        backend.UPLOAD_DIR = self.old_upload_dir
        self.temp_uploads.cleanup()

    def headers(self, role="Farmer", user_id=1, *, idempotency_key=None):
        with db_connection() as conn:
            row = conn.execute(
                "SELECT session_version FROM users WHERE user_id = %s", (user_id,)
            ).fetchone()
        token = backend.issue_access_token(
            {"user_id": user_id, "session_version": row["session_version"]}
        )
        headers = {"Authorization": f"Bearer {token}"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def upload(self, user_id, key, *, image_data=None):
        return self.client.post(
            "/api/upload",
            headers=self.headers("Farmer", user_id, idempotency_key=key),
            data={"image": (io.BytesIO(image_data or png_bytes()), "field.png")},
            content_type="multipart/form-data",
        )

    def test_upload_retry_reuses_one_record_and_one_encrypted_blob(self):
        key = f"field-upload-{uuid4()}"
        first = self.upload(1, key)
        second = self.upload(1, key)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        first_payload = first.get_json()
        second_payload = second.get_json()
        self.assertEqual(first_payload["image_id"], second_payload["image_id"])
        self.assertFalse(first_payload["idempotent_replay"])
        self.assertTrue(second_payload["idempotent_replay"])
        self.image_ids.append(first_payload["image_id"])

        with db_connection() as conn:
            image_count = conn.execute(
                "SELECT COUNT(*) AS count FROM images "
                "WHERE user_id = %s AND upload_idempotency_key = %s",
                (1, key),
            ).fetchone()["count"]
            file_count = conn.execute(
                "SELECT COUNT(*) AS count FROM image_files WHERE image_id = %s",
                (first_payload["image_id"],),
            ).fetchone()["count"]
        self.assertEqual(image_count, 1)
        self.assertEqual(file_count, 1)
        self.assertEqual(len(list(backend.UPLOAD_DIR.glob("*.enc"))), 1)

    def test_reusing_a_key_for_different_image_bytes_is_rejected(self):
        key = f"field-upload-{uuid4()}"
        first = self.upload(1, key)
        mismatched = self.upload(1, key, image_data=png_bytes((140, 45, 35)))

        self.assertEqual(first.status_code, 201)
        self.assertEqual(mismatched.status_code, 409)
        self.assertIn("different image", mismatched.get_json()["message"])
        self.image_ids.append(first.get_json()["image_id"])

    def test_idempotency_key_is_scoped_to_user_and_new_keys_create_new_records(self):
        shared_key = f"field-upload-{uuid4()}"
        with db_connection() as conn:
            conn.execute("UPDATE users SET status = 'active' WHERE user_id = %s", (9,))
        try:
            first = self.upload(1, shared_key)
            second_user = self.upload(9, shared_key)
            new_intent = self.upload(1, f"field-upload-{uuid4()}")
        finally:
            with db_connection() as conn:
                conn.execute("UPDATE users SET status = 'disabled' WHERE user_id = %s", (9,))

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second_user.status_code, 201)
        self.assertEqual(new_intent.status_code, 201)
        ids = {
            first.get_json()["image_id"],
            second_user.get_json()["image_id"],
            new_intent.get_json()["image_id"],
        }
        self.assertEqual(len(ids), 3)
        self.image_ids.extend(ids)

    def test_failed_first_upload_does_not_consume_the_idempotency_key(self):
        key = f"field-upload-{uuid4()}"
        with patch.object(
            backend, "secure_store_bytes", side_effect=OSError("simulated storage failure")
        ):
            failed = self.upload(1, key)
        self.assertEqual(failed.status_code, 500)

        retry = self.upload(1, key)
        self.assertEqual(retry.status_code, 201)
        self.assertFalse(retry.get_json()["idempotent_replay"])
        self.image_ids.append(retry.get_json()["image_id"])

        with db_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) AS count FROM images "
                "WHERE user_id = %s AND upload_idempotency_key = %s",
                (1, key),
            ).fetchone()["count"]
        self.assertEqual(count, 1)

    def test_model_listing_never_discloses_registered_weight_paths(self):
        response = self.client.get(
            "/api/models", headers=self.headers("Researcher", 2)
        )
        self.assertEqual(response.status_code, 200)
        for model in response.get_json()["models"]:
            self.assertNotIn("weights_path", model)
            self.assertIn("artifact_registered", model)

    def test_prediction_and_result_return_safe_auditable_provenance(self):
        upload = self.upload(1, f"field-upload-{uuid4()}")
        self.assertEqual(upload.status_code, 201)
        image_id = upload.get_json()["image_id"]
        self.image_ids.append(image_id)

        with patch.object(backend, "get_predictor", return_value=FakePredictor()):
            prediction = self.client.post(
                "/api/predict",
                headers=self.headers(),
                json={"image_id": image_id, "mode": "fast"},
            )
        self.assertEqual(prediction.status_code, 201)
        prediction_payload = prediction.get_json()
        result_id = prediction_payload["result_id"]

        result = self.client.get(
            f"/api/results/{result_id}", headers=self.headers()
        )
        self.assertEqual(result.status_code, 200)
        payload = result.get_json()
        for forbidden in (
            "image_path",
            "original_image_path",
            "annotated_image_path",
            "weights_path",
        ):
            self.assertNotIn(forbidden, prediction_payload)
            self.assertNotIn(forbidden, payload)
        self.assertEqual(payload["original_asset_url"], f"/api/images/{image_id}/file/original")
        self.assertEqual(payload["inference_mode"], "fast")
        self.assertTrue(payload["model_version"])
        self.assertIn("model_id", payload)
        self.assertEqual(payload["quality_status"], "unreviewed")

        protected_image = self.client.get(
            payload["original_asset_url"], headers=self.headers()
        )
        self.assertEqual(protected_image.status_code, 200)
        self.assertEqual(protected_image.mimetype, "image/png")

    def test_compare_rejects_untrusted_or_integrity_failed_model_before_evaluation(self):
        for diagnostic in (
            "Model artifact is outside C:/private/models",
            "Model artifact integrity check failed for C:/private/model.pt",
        ):
            with self.subTest(diagnostic=diagnostic), patch.object(
                backend, "validate_model_artifact", side_effect=ModelArtifactError(diagnostic)
            ), patch.object(backend, "evaluate_model") as evaluate:
                response = self.client.post(
                    "/api/models/compare",
                    headers=self.headers("Researcher", 2),
                    json={"model_ids": [1, 2], "dataset_yaml": "datasets/maize.yaml"},
                )
                self.assertEqual(response.status_code, 409)
                self.assertNotIn("C:/private", response.get_json()["message"])
                evaluate.assert_not_called()

    def test_compare_rejects_unapproved_dataset_before_evaluation(self):
        artifact = SimpleNamespace(path=Path("approved-model.pt"))
        with patch.object(
            backend, "validate_model_artifact", return_value=artifact
        ), patch.object(
            backend,
            "validate_dataset_yaml",
            side_effect=ApprovedPathError("C:/private/dataset.yaml is outside the approved directory"),
        ), patch.object(backend, "evaluate_model") as evaluate:
            response = self.client.post(
                "/api/models/compare",
                headers=self.headers("Researcher", 2),
                json={"model_ids": [1, 2], "dataset_yaml": "C:/private/dataset.yaml"},
            )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("C:/private", response.get_json()["message"])
        evaluate.assert_not_called()

    def test_compare_validates_all_resources_then_evaluates_both_models(self):
        artifacts = [
            SimpleNamespace(path=Path("approved-one.pt")),
            SimpleNamespace(path=Path("approved-two.pt")),
        ]
        metrics = {"map50": 0.8, "precision": 0.81, "recall": 0.79}
        with patch.object(
            backend, "validate_model_artifact", side_effect=artifacts
        ) as validate_artifact, patch.object(
            backend, "validate_dataset_yaml", return_value=Path("approved.yaml")
        ) as validate_yaml, patch.object(
            backend, "evaluate_model", return_value=metrics
        ) as evaluate:
            response = self.client.post(
                "/api/models/compare",
                headers=self.headers("Researcher", 2),
                json={"model_ids": [1, 2], "dataset_yaml": "datasets/approved.yaml"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["comparison_source"], "shared-validation-run")
        self.assertEqual(validate_artifact.call_count, 2)
        validate_yaml.assert_called_once()
        self.assertEqual(evaluate.call_count, 2)
        for model in response.get_json()["models"]:
            self.assertNotIn("weights_path", model)


if __name__ == "__main__":
    unittest.main()

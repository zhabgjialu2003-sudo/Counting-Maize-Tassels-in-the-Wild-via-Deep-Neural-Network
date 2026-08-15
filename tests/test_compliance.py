import io
import json
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import backend.app as backend


class ComplianceApiTests(unittest.TestCase):
    def setUp(self):
        backend.app.config["TESTING"] = True
        self.client = backend.app.test_client()

    def token(self, role, user_id=1):
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT session_version FROM users WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
        return backend.issue_access_token(
            {
                "user_id": user_id,
                "session_version": row["session_version"],
                "name": f"{role} Test",
                "email": f"{role.lower()}@example.com",
                "role": role,
                "status": "active",
            }
        )

    def headers(self, role, user_id=1):
        return {"Authorization": f"Bearer {self.token(role, user_id)}"}

    def test_admin_endpoint_rejects_unauthenticated_request(self):
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 401)

    def test_security_headers_are_applied_to_api_responses(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_admin_endpoint_rejects_farmer(self):
        response = self.client.get("/api/users", headers=self.headers("Farmer"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_database_users(self):
        response = self.client.get("/api/users", headers=self.headers("Admin", 4))
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.get_json())

    def test_researcher_can_compare_registered_model_metrics(self):
        response = self.client.post(
            "/api/models/compare",
            headers=self.headers("Researcher", 2),
            json={"model_ids": [1, 2]},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload["models"]), 2)
        self.assertIn(payload["winner_model_id"], [1, 2])

    def test_researcher_can_download_metadata_only_dataset_manifest(self):
        response = self.client.get(
            "/api/datasets/1/download?format=zip",
            headers=self.headers("Researcher", 2),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")
        with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {"dataset-manifest.json", "README.txt"},
            )
            manifest = json.loads(archive.read("dataset-manifest.json"))
            notice = archive.read("README.txt").decode("utf-8")
        self.assertEqual(manifest["dataset_id"], 1)
        self.assertEqual(manifest["export"]["content_mode"], "manifest_only")
        self.assertFalse(manifest["export"]["files_included"])
        self.assertIn("metadata only", notice)

    def test_researcher_dataset_page_surfaces_download_errors(self):
        source = (Path(__file__).resolve().parents[1] / "frontend" / "pages" / "researcher.html").read_text("utf-8")
        self.assertIn('id="datasetDownloadStatus"', source)
        self.assertIn("payload.message || payload.error", source)
        self.assertIn("Cannot reach the server", source)
        self.assertNotIn("alert('Dataset download failed.')", source)

    def test_dataset_download_still_rejects_an_unapproved_nonempty_path(self):
        with patch.object(
            backend,
            "resolve_approved_path",
            side_effect=backend.ApprovedPathError("outside approved storage"),
        ):
            response = self.client.get(
                "/api/datasets/4/download?format=zip",
                headers=self.headers("Researcher", 2),
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn("approved storage", response.get_json()["message"])

    def test_admin_can_list_stored_images_for_preprocessing(self):
        response = self.client.get(
            "/api/system/images?limit=5",
            headers=self.headers("Admin", 4),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertLessEqual(len(payload["images"]), 5)
        self.assertEqual(payload["total"], len(payload["images"]))
        if payload["images"]:
            self.assertIn("image_id", payload["images"][0])
            self.assertIn("original_filename", payload["images"][0])
        source = (Path(__file__).resolve().parents[1] / "frontend" / "pages" / "system.html").read_text("utf-8")
        self.assertIn('<select id="preprocessImageId" disabled>', source)
        self.assertIn("apiGet('/api/system/images?limit=50')", source)
        self.assertNotIn('id="preprocessImageId" type="number" value="1"', source)

    def test_non_admin_cannot_list_preprocessing_images(self):
        response = self.client.get(
            "/api/system/images",
            headers=self.headers("Researcher", 2),
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_preprocesses_an_encrypted_database_original(self):
        raw = io.BytesIO()
        Image.new("RGB", (900, 700), (24, 120, 40)).save(raw, format="PNG")
        original = raw.getvalue()
        image_name = f"preprocess-{uuid.uuid4().hex}.png"
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO images (
                        user_id, image_name, image_path, status, file_size,
                        original_filename, mime_type, image_width, image_height, validated
                    ) VALUES (%s, %s, %s, 'pending', %s, %s, 'image/png', 900, 700, TRUE)
                    RETURNING image_id
                    """,
                    (1, image_name, f"database://images/{image_name}", len(original), "field-test.png"),
                )
                image_id = cur.fetchone()["image_id"]
            backend.store_image_blob(
                conn,
                image_id,
                "original",
                image_name,
                "image/png",
                backend.encryption_cipher().encrypt(original),
                encrypted=True,
            )

        old_upload_dir = backend.UPLOAD_DIR
        try:
            with tempfile.TemporaryDirectory() as directory:
                backend.UPLOAD_DIR = Path(directory)
                response = self.client.post(
                    f"/api/system/preprocess/{image_id}",
                    headers=self.headers("Admin", 4),
                    json={"augment": True},
                )
                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertTrue(payload["preprocessed"])
                self.assertIn("horizontal augmentation", payload["steps"])
                with Image.open(io.BytesIO(backend.secure_read_bytes(payload["preprocessed_name"]))) as processed:
                    self.assertLessEqual(max(processed.size), 640)
                with backend.db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT preprocessed, preprocessed_path FROM images WHERE image_id = %s",
                            (image_id,),
                        )
                        row = cur.fetchone()
                self.assertTrue(row["preprocessed"])
                self.assertTrue(row["preprocessed_path"])
        finally:
            backend.UPLOAD_DIR = old_upload_dir
            with backend.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM system_logs WHERE action = 'image_preprocessed' AND details LIKE %s",
                        (f"image_id={image_id},%",),
                    )
                    cur.execute("DELETE FROM images WHERE image_id = %s", (image_id,))

    def test_farmer_cannot_compare_models(self):
        response = self.client.post(
            "/api/models/compare",
            headers=self.headers("Farmer"),
            json={"model_ids": [1, 2]},
        )
        self.assertEqual(response.status_code, 403)

    def test_agronomist_can_read_fields_and_insights(self):
        fields = self.client.get("/api/fields", headers=self.headers("Agronomist", 3))
        insights = self.client.get("/api/fields/insights", headers=self.headers("Agronomist", 3))
        self.assertEqual(fields.status_code, 200)
        self.assertEqual(insights.status_code, 200)
        self.assertGreaterEqual(len(fields.get_json()["fields"]), 3)
        self.assertIn("recommendation", insights.get_json())

    def test_farmer_can_read_own_leaf_screening_history(self):
        response = self.client.get(
            "/api/agronomy/diagnoses?limit=5",
            headers=self.headers("Farmer", 1),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json()["records"], list)

    def test_secure_image_storage_round_trip(self):
        old_upload_dir = backend.UPLOAD_DIR
        with tempfile.TemporaryDirectory() as directory:
            backend.UPLOAD_DIR = Path(directory)
            content = b"example-image-bytes"
            backend.secure_store_bytes("sample.jpg", content)
            encrypted = backend.encrypted_path("sample.jpg").read_bytes()
            self.assertNotEqual(encrypted, content)
            self.assertEqual(backend.secure_read_bytes("sample.jpg"), content)
        backend.UPLOAD_DIR = old_upload_dir

    def test_invalid_upload_type_is_rejected(self):
        response = self.client.post(
            "/api/upload",
            headers=self.headers("Farmer"),
            json={"image_name": "report.pdf"},
        )
        self.assertEqual(response.status_code, 400)

    def test_prediction_requires_a_persisted_image_id(self):
        response = self.client.post(
            "/api/predict",
            headers=self.headers("Farmer"),
            json={"image_name": "untrusted-client-name.jpg"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("image_id is required", response.get_json()["message"])

    def test_a8_signed_session_can_be_validated(self):
        response = self.client.get("/api/auth/me", headers=self.headers("Farmer", 1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["user_id"], 1)

    def test_b6_report_requires_valid_ordered_date_range(self):
        response = self.client.post(
            "/api/reports",
            headers=self.headers("Researcher", 2),
            json={"date_from": "2026-06-10", "date_to": "2026-06-01", "field_ids": []},
        )
        self.assertEqual(response.status_code, 400)

    def test_c3_anomaly_review_requires_reason(self):
        response = self.client.post(
            "/api/fields/1/anomaly",
            headers=self.headers("Agronomist", 3),
            json={"reason": ""},
        )
        self.assertEqual(response.status_code, 400)

    def test_e2_local_training_requires_dataset_yaml(self):
        response = self.client.post(
            "/api/training-runs",
            headers=self.headers("Admin", 4),
            json={"model_id": 1, "dataset_id": 1, "execute_local": True},
        )
        self.assertEqual(response.status_code, 400)

    def test_boundary_tabs_follow_bce_order(self):
        root = Path(__file__).resolve().parents[1]
        agronomist = (root / "frontend/pages/agronomist.html").read_text(encoding="utf-8")
        admin = (root / "frontend/pages/admin.html").read_text(encoding="utf-8")
        researcher = (root / "frontend/pages/researcher.html").read_text(encoding="utf-8")
        system = (root / "frontend/pages/system.html").read_text(encoding="utf-8")
        self.assertLess(researcher.index("B.1"), researcher.index("B.2"))
        self.assertLess(researcher.index("B.2"), researcher.index("B.3"))
        self.assertLess(researcher.index("B.3"), researcher.index("B.4"))
        self.assertLess(researcher.index("B.4"), researcher.index("B.5"))
        self.assertLess(researcher.index("B.5"), researcher.index("B.6"))
        self.assertLess(agronomist.index("C.1"), agronomist.index("C.2"))
        self.assertLess(agronomist.index("C.2"), agronomist.index("C.3"))
        self.assertLess(agronomist.index("C.3"), agronomist.index("C.4"))
        self.assertLess(agronomist.index("C.4"), agronomist.index("C.5"))
        self.assertLess(admin.index("D.1"), admin.index("D.2"))
        self.assertLess(admin.index("D.2"), admin.index("D.3"))
        self.assertLess(admin.index("D.3"), admin.index("D.4"))
        self.assertLess(admin.index("D.4"), admin.index("D.5"))
        self.assertLess(admin.index("D.5"), admin.index("D.6"))
        self.assertLess(system.index("E.1"), system.index("E.2"))
        self.assertLess(system.index("E.2"), system.index("E.3"))
        self.assertLess(system.index("E.3"), system.index("E.4"))
        self.assertLess(system.index("E.4"), system.index("E.5"))

    def test_production_code_contains_no_mock_fallbacks(self):
        root = Path(__file__).resolve().parents[1]
        files = [
            root / "backend/app.py",
            root / "backend/server.py",
            root / "frontend/js/api.js",
            root / "frontend/js/auth.js",
            *sorted((root / "frontend/pages").glob("*.html")),
        ]
        forbidden = (
            "MockData",
            "mock fallback",
            "mock mode",
            'source="mock"',
            '"source": "mock"',
        )
        for path in files:
            content = path.read_text(encoding="utf-8").lower()
            for marker in forbidden:
                self.assertNotIn(marker.lower(), content, f"{marker!r} found in {path}")


if __name__ == "__main__":
    unittest.main()

import json
import unittest
import uuid

import backend.app as backend
from backend.services.disease_review import build_review_recommendation


class DiseaseReviewPolicyTests(unittest.TestCase):
    def test_possible_disease_recommends_human_review(self):
        recommendation = build_review_recommendation(
            {
                "status": "supported",
                "quality": {"status": "pass"},
                "possible_condition": {"code": "common_rust"},
                "technical": {"confidence": 0.93},
            }
        )
        self.assertTrue(recommendation["recommended"])
        self.assertIn("possible_disease", recommendation["reasons"])

    def test_clear_healthy_result_does_not_force_review(self):
        recommendation = build_review_recommendation(
            {
                "status": "supported",
                "quality": {"status": "pass"},
                "possible_condition": {"code": "healthy"},
                "technical": {"confidence": 0.91},
            }
        )
        self.assertFalse(recommendation["recommended"])
        self.assertEqual(recommendation["reasons"], [])


class FarmerLeafReviewApiTests(unittest.TestCase):
    def setUp(self):
        backend.app.config["TESTING"] = True
        self.client = backend.app.test_client()
        suffix = uuid.uuid4().hex
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role_id, role_name FROM roles")
                roles = {row["role_name"]: row["role_id"] for row in cur.fetchall()}
                self.user_ids = {}
                for key, role in (
                    ("farmer", "Farmer"),
                    ("other_farmer", "Farmer"),
                    ("agronomist", "Agronomist"),
                    ("other_agronomist", "Agronomist"),
                ):
                    cur.execute(
                        """
                        INSERT INTO users (name, email, password_hash, role_id, status)
                        VALUES (%s, %s, %s, %s, 'active')
                        RETURNING user_id, session_version
                        """,
                        (
                            f"Leaf Review {key}",
                            f"leaf-review-{key}-{suffix}@example.com",
                            backend.hash_password("leaf-review-safe-123"),
                            roles[role],
                        ),
                    )
                    row = cur.fetchone()
                    self.user_ids[key] = row["user_id"]

                cur.execute(
                    """
                    INSERT INTO fields (field_name, location, owner_user_id)
                    VALUES (%s, 'Test Region', %s), (%s, 'Test Region', %s),
                           (%s, 'Test Region', %s)
                    RETURNING field_id
                    """,
                    (
                        f"Owned Field {suffix}",
                        self.user_ids["farmer"],
                        f"Unassigned Field {suffix}",
                        self.user_ids["farmer"],
                        f"Other Field {suffix}",
                        self.user_ids["other_farmer"],
                    ),
                )
                field_rows = cur.fetchall()
                self.owned_field_id = field_rows[0]["field_id"]
                self.unassigned_field_id = field_rows[1]["field_id"]
                self.other_field_id = field_rows[2]["field_id"]
                cur.execute(
                    """
                    INSERT INTO field_assignments (field_id, agronomist_user_id)
                    VALUES (%s, %s)
                    """,
                    (self.owned_field_id, self.user_ids["agronomist"]),
                )
                self.diagnosis_id = self.insert_diagnosis(
                    cur, self.user_ids["farmer"], None
                )
                self.other_diagnosis_id = self.insert_diagnosis(
                    cur, self.user_ids["other_farmer"], self.other_field_id
                )

        self.headers = {
            key: {
                "Authorization": "Bearer "
                + backend.issue_access_token({"user_id": user_id, "session_version": 1})
            }
            for key, user_id in self.user_ids.items()
        }

    @staticmethod
    def insert_diagnosis(cur, user_id, field_id):
        response = {
            "headline": "Possible common rust",
            "possible_condition": {"code": "common_rust", "display_name": "Common rust"},
            "review": {"recommended": True, "reasons": ["possible_disease"]},
        }
        cur.execute(
            """
            INSERT INTO disease_diagnoses
                (user_id, field_id, knowledge_version, status,
                 predicted_condition, confidence, quality_findings,
                 context_data, response_data)
            VALUES (%s, %s, 'test-knowledge', 'supported', 'common_rust', 0.91,
                    '{}'::jsonb, '{}'::jsonb, %s::jsonb)
            RETURNING diagnosis_id
            """,
            (user_id, field_id, json.dumps(response)),
        )
        return cur.fetchone()["diagnosis_id"]

    def tearDown(self):
        user_ids = list(self.user_ids.values())
        field_ids = [self.owned_field_id, self.unassigned_field_id, self.other_field_id]
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM system_logs WHERE user_id = ANY(%s)", (user_ids,))
                cur.execute(
                    "DELETE FROM disease_diagnoses WHERE user_id = ANY(%s)",
                    (user_ids,),
                )
                cur.execute(
                    "DELETE FROM field_assignments WHERE field_id = ANY(%s)",
                    (field_ids,),
                )
                cur.execute("DELETE FROM fields WHERE field_id = ANY(%s)", (field_ids,))
                cur.execute("DELETE FROM users WHERE user_id = ANY(%s)", (user_ids,))

    def request_review(self, diagnosis_id=None, field_id=None):
        return self.client.post(
            f"/api/agronomy/diagnoses/{diagnosis_id or self.diagnosis_id}/review-request",
            headers=self.headers["farmer"],
            json={
                "field_id": field_id or self.owned_field_id,
                "reason": "The symptoms are spreading across the lower leaves.",
            },
        )

    def test_farmer_field_list_is_owner_scoped(self):
        response = self.client.get("/api/fields", headers=self.headers["farmer"])
        self.assertEqual(response.status_code, 200)
        returned = {row["field_id"] for row in response.get_json()["fields"]}
        self.assertEqual(returned, {self.owned_field_id, self.unassigned_field_id})

    def test_review_request_is_idempotent(self):
        first = self.request_review()
        second = self.request_review()
        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.get_json()["idempotent_replay"])
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.get_json()["idempotent_replay"])
        self.assertEqual(second.get_json()["review_status"], "requested")

    def test_farmer_cannot_request_review_for_another_users_diagnosis(self):
        response = self.request_review(
            diagnosis_id=self.other_diagnosis_id,
            field_id=self.other_field_id,
        )
        self.assertEqual(response.status_code, 404)

    def test_review_request_requires_an_assigned_agronomist(self):
        response = self.request_review(field_id=self.unassigned_field_id)
        self.assertEqual(response.status_code, 409)
        self.assertIn("assigned", response.get_json()["message"])

    def test_assigned_agronomist_can_complete_review(self):
        self.assertEqual(self.request_review().status_code, 200)
        denied = self.client.patch(
            f"/api/agronomy/diagnoses/{self.diagnosis_id}/review-status",
            headers=self.headers["other_agronomist"],
            json={"status": "in_review"},
        )
        self.assertEqual(denied.status_code, 404)

        started = self.client.patch(
            f"/api/agronomy/diagnoses/{self.diagnosis_id}/review-status",
            headers=self.headers["agronomist"],
            json={"status": "in_review"},
        )
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.get_json()["review_status"], "in_review")

        reviewed = self.client.post(
            f"/api/agronomy/diagnoses/{self.diagnosis_id}/review",
            headers=self.headers["agronomist"],
            json={"decision": "confirmed", "note": "Rust symptoms confirmed in the field."},
        )
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(reviewed.get_json()["review"]["review_status"], "reviewed")

        history = self.client.get(
            "/api/agronomy/diagnoses", headers=self.headers["farmer"]
        )
        self.assertEqual(history.status_code, 200)
        record = next(
            row
            for row in history.get_json()["records"]
            if row["diagnosis_id"] == self.diagnosis_id
        )
        self.assertEqual(record["review_status"], "reviewed")
        self.assertEqual(record["reviewer_decision"], "confirmed")
        self.assertIn("Rust symptoms", record["reviewer_note"])


if __name__ == "__main__":
    unittest.main()

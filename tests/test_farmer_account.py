import io
import unittest
import uuid
from pathlib import Path

from PIL import Image

import backend.app as backend


ROOT = Path(__file__).resolve().parents[1]


class FarmerAccountApiTests(unittest.TestCase):
    def setUp(self):
        backend.app.config["TESTING"] = True
        self.client = backend.app.test_client()
        self.password = "field-safe-123"
        self.email = f"farmer-profile-{uuid.uuid4().hex}@example.com"
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role_id FROM roles WHERE role_name = 'Farmer'")
                role = cur.fetchone()
                self.assertIsNotNone(role, "Farmer role must exist")
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role_id, status)
                    VALUES (%s, %s, %s, %s, 'active')
                    RETURNING user_id
                    """,
                    ("Profile Test Farmer", self.email, backend.hash_password(self.password), role["role_id"]),
                )
                self.user_id = cur.fetchone()["user_id"]
        self.headers = {
            "Authorization": "Bearer " + backend.issue_access_token({
                "user_id": self.user_id,
                "name": "Profile Test Farmer",
                "email": self.email,
                "role": "Farmer",
                "status": "active",
            })
        }
        self.created_image_ids = []

    def tearDown(self):
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                if self.created_image_ids:
                    cur.execute(
                        "DELETE FROM image_files WHERE image_id = ANY(%s)",
                        (self.created_image_ids,),
                    )
                    cur.execute(
                        "DELETE FROM disease_diagnoses WHERE image_id = ANY(%s)",
                        (self.created_image_ids,),
                    )
                    cur.execute(
                        "DELETE FROM detection_results WHERE image_id = ANY(%s)",
                        (self.created_image_ids,),
                    )
                    cur.execute(
                        "DELETE FROM images WHERE image_id = ANY(%s)",
                        (self.created_image_ids,),
                    )
                cur.execute("DELETE FROM system_logs WHERE user_id = %s", (self.user_id,))
                cur.execute("DELETE FROM users WHERE user_id = %s", (self.user_id,))
                cur.execute("DELETE FROM users WHERE email LIKE 'occupied-profile-%@example.com'")

    def test_account_routes_require_authentication(self):
        profile = self.client.patch("/api/auth/profile", json={})
        password = self.client.post("/api/auth/change-password", json={})
        self.assertEqual(profile.status_code, 401)
        self.assertEqual(password.status_code, 401)

    def test_query_string_access_token_is_rejected(self):
        token = self.headers["Authorization"].removeprefix("Bearer ")
        response = self.client.get(f"/api/auth/me?access_token={token}")
        self.assertEqual(response.status_code, 401)

    def test_farmer_can_update_own_name_and_email(self):
        new_email = f"updated-{uuid.uuid4().hex}@example.com"
        response = self.client.patch(
            "/api/auth/profile",
            headers=self.headers,
            json={
                "name": "Updated Farmer",
                "email": new_email.upper(),
                "current_password": self.password,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["user"]["name"], "Updated Farmer")
        self.assertEqual(payload["user"]["email"], new_email)
        self.assertTrue(payload["access_token"])
        stale = self.client.get("/api/auth/me", headers=self.headers)
        fresh = self.client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer " + payload["access_token"]},
        )
        self.assertEqual(stale.status_code, 401)
        self.assertEqual(fresh.status_code, 200)
        with backend.db_connection() as conn:
            user = backend.fetch_user(conn, self.user_id)
        self.assertEqual(user["email"], new_email)

    def test_wrong_current_password_preserves_profile(self):
        response = self.client.patch(
            "/api/auth/profile",
            headers=self.headers,
            json={
                "name": "Should Not Save",
                "email": self.email,
                "current_password": "wrong-password",
            },
        )
        self.assertEqual(response.status_code, 401)
        with backend.db_connection() as conn:
            user = backend.fetch_user(conn, self.user_id)
        self.assertEqual(user["name"], "Profile Test Farmer")

    def test_duplicate_email_is_rejected(self):
        occupied = f"occupied-profile-{uuid.uuid4().hex}@example.com"
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role_id, status)
                    SELECT 'Occupied', %s, %s, role_id, 'active' FROM roles WHERE role_name = 'Farmer'
                    """,
                    (occupied, backend.hash_password("occupied-password")),
                )
        response = self.client.patch(
            "/api/auth/profile",
            headers=self.headers,
            json={"name": "Profile Test Farmer", "email": occupied, "current_password": self.password},
        )
        self.assertEqual(response.status_code, 409)

    def test_farmer_can_change_password_and_old_password_stops_working(self):
        new_password = "new-field-safe-456"
        response = self.client.post(
            "/api/auth/change-password",
            headers=self.headers,
            json={
                "current_password": self.password,
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )
        self.assertEqual(response.status_code, 200)
        old_login = self.client.post("/api/auth/login", json={"email": self.email, "password": self.password})
        new_login = self.client.post("/api/auth/login", json={"email": self.email, "password": new_password})
        self.assertEqual(old_login.status_code, 401)
        self.assertEqual(new_login.status_code, 200)
        stale_session = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(stale_session.status_code, 401)

    def test_disabled_account_cannot_reuse_an_existing_token(self):
        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET status = 'disabled', session_version = session_version + 1
                    WHERE user_id = %s
                    """,
                    (self.user_id,),
                )
        response = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(response.status_code, 401)

    @staticmethod
    def png_bytes(colour):
        output = io.BytesIO()
        Image.new("RGB", (64, 64), colour).save(output, format="PNG")
        return output.getvalue()

    def upload_png(self, data, filename="same-field-name.png"):
        response = self.client.post(
            "/api/upload",
            headers=self.headers,
            data={"image": (io.BytesIO(data), filename)},
            content_type="multipart/form-data",
        )
        if response.status_code == 201:
            self.created_image_ids.append(response.get_json()["image_id"])
        return response

    def test_same_original_filename_creates_isolated_encrypted_records(self):
        first_bytes = self.png_bytes((10, 90, 20))
        second_bytes = self.png_bytes((90, 10, 20))
        first = self.upload_png(first_bytes)
        second = self.upload_png(second_bytes)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(first.get_json()["image_name"], second.get_json()["image_name"])

        with backend.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT i.image_id, i.original_filename, i.content_sha256, i.validated,
                           f.image_data, f.encrypted
                    FROM images i
                    JOIN image_files f ON f.image_id = i.image_id AND f.file_type = 'original'
                    WHERE i.image_id = ANY(%s)
                    ORDER BY i.image_id
                    """,
                    (self.created_image_ids,),
                )
                rows = cur.fetchall()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["original_filename"] == "same-field-name.png" for row in rows))
        self.assertTrue(all(row["validated"] and row["encrypted"] for row in rows))
        self.assertNotEqual(rows[0]["content_sha256"], rows[1]["content_sha256"])
        plaintext = [backend.encryption_cipher().decrypt(bytes(row["image_data"])) for row in rows]
        self.assertEqual(plaintext, [first_bytes, second_bytes])


class FarmerAccountFrontendTests(unittest.TestCase):
    def test_mobile_my_account_links_never_call_logout(self):
        for name in ("mobile.html", "history.html", "upload.html", "leaf.html", "result.html"):
            source = (ROOT / "frontend" / "pages" / name).read_text("utf-8")
            self.assertIn('href="profile.html"', source, name)
            my_account_lines = [line for line in source.splitlines() if "profile.html" in line]
            self.assertTrue(my_account_lines, name)
            self.assertTrue(all("logout()" not in line for line in my_account_lines), name)

        profile = (ROOT / "frontend" / "pages" / "profile.html").read_text("utf-8")
        self.assertIn('/api/auth/profile', profile)
        self.assertIn('/api/auth/change-password', profile)
        self.assertIn('confirmLogout', profile)


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import backend.app as backend


ROOT = Path(__file__).resolve().parents[1]


class DemoAccessApiTests(unittest.TestCase):
    def setUp(self):
        backend.app.config["TESTING"] = True
        self.client = backend.app.test_client()

    def test_demo_access_is_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DEMO_ACCESS_ENABLED", None)
            os.environ.pop("DEMO_ACCESS_ALLOW_PRIVATE_NETWORK", None)
            os.environ.pop("DEMO_ACCESS_ALLOW_PUBLIC", None)
            os.environ.pop("DEMO_ACCOUNT_PASSWORD", None)
            response = self.client.get("/api/demo-access", headers={"Host": "localhost:5000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"enabled": False})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_enabled_demo_access_is_rejected_for_public_and_lan_hosts(self):
        configured = {
            "DEMO_ACCESS_ENABLED": "true",
            "DEMO_ACCESS_ALLOW_PRIVATE_NETWORK": "false",
            "DEMO_ACCESS_ALLOW_PUBLIC": "false",
            "DEMO_ACCOUNT_PASSWORD": "local-demo-pass",
        }
        with patch.dict(os.environ, configured, clear=False):
            for host in ("example.com", "demo.example.com:443", "192.168.1.20:5000"):
                response = self.client.get("/api/demo-access", headers={"Host": host})
                self.assertEqual(response.get_json(), {"enabled": False}, host)

    def test_private_network_mobile_access_requires_explicit_opt_in(self):
        configured = {
            "DEMO_ACCESS_ENABLED": "true",
            "DEMO_ACCESS_ALLOW_PRIVATE_NETWORK": "true",
            "DEMO_ACCESS_ALLOW_PUBLIC": "false",
            "DEMO_ACCOUNT_PASSWORD": "local-demo-pass",
        }
        with patch.dict(os.environ, configured, clear=False):
            response = self.client.get(
                "/api/demo-access", headers={"Host": "192.168.1.20:5001"}
            )
        self.assertTrue(response.get_json()["enabled"])

    def test_enabled_demo_access_returns_four_roles_only_on_loopback(self):
        configured = {
            "DEMO_ACCESS_ENABLED": "true",
            "DEMO_ACCESS_ALLOW_PUBLIC": "false",
            "DEMO_ACCOUNT_PASSWORD": "local-demo-pass",
        }
        with patch.dict(os.environ, configured, clear=False):
            for host in ("localhost:5000", "127.0.0.1:5000", "[::1]:5000"):
                response = self.client.get("/api/demo-access", headers={"Host": host})
                data = response.get_json()
                self.assertTrue(data["enabled"], host)
                self.assertEqual(data["shared_password"], "local-demo-pass")
                self.assertEqual(
                    [account["role"] for account in data["accounts"]],
                    ["Farmer", "Researcher", "Agronomist", "Admin"],
                )

    def test_public_demo_access_requires_explicit_opt_in(self):
        configured = {
            "DEMO_ACCESS_ENABLED": "true",
            "DEMO_ACCESS_ALLOW_PUBLIC": "true",
            "DEMO_ACCOUNT_PASSWORD": "public-demo-pass",
        }
        with patch.dict(os.environ, configured, clear=False):
            response = self.client.get(
                "/api/demo-access", headers={"Host": "maize-detector.onrender.com"}
            )
        data = response.get_json()
        self.assertTrue(data["enabled"])
        self.assertEqual(data["shared_password"], "public-demo-pass")
        self.assertEqual(
            [account["role"] for account in data["accounts"]],
            ["Farmer", "Researcher", "Agronomist", "Admin"],
        )
        self.assertEqual(response.headers["Cache-Control"], "no-store")


class DemoAccessFrontendTests(unittest.TestCase):
    def test_login_page_uses_manual_submit_demo_role_controls(self):
        source = (ROOT / "frontend/pages/login.html").read_text(encoding="utf-8")
        self.assertIn("Quick Demo Access", source)
        self.assertIn("apiGet('/api/demo-access')", source)
        self.assertIn("fillDemoAccount(account, password)", source)
        self.assertIn("document.getElementById('loginBtn').focus()", source)
        fill_function = source.split("function fillDemoAccount", 1)[1].split("async function", 1)[0]
        self.assertNotIn("handleLogin()", fill_function)

    def test_tracked_configuration_has_safe_demo_defaults(self):
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("DEMO_ACCESS_ENABLED=false", example)
        self.assertIn("DEMO_ACCESS_ALLOW_PRIVATE_NETWORK=false", example)
        self.assertIn("DEMO_ACCESS_ALLOW_PUBLIC=false", example)
        self.assertIn("DEMO_ACCOUNT_PASSWORD=", example)


if __name__ == "__main__":
    unittest.main()

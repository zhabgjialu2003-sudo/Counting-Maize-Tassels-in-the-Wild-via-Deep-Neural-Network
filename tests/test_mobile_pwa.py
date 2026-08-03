import json
import re
import unittest
from pathlib import Path

from PIL import Image

import backend.app as backend


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


class MobilePwaStaticTests(unittest.TestCase):
    @staticmethod
    def contrast_ratio(foreground, background):
        def luminance(hex_color):
            channels = [
                int(hex_color[index : index + 2], 16) / 255
                for index in (1, 3, 5)
            ]
            linear = [
                value / 12.92
                if value <= 0.04045
                else ((value + 0.055) / 1.055) ** 2.4
                for value in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        first = luminance(foreground)
        second = luminance(background)
        lighter, darker = max(first, second), min(first, second)
        return (lighter + 0.05) / (darker + 0.05)

    def test_manifest_has_installable_png_icons(self):
        manifest = json.loads((FRONTEND / "manifest.webmanifest").read_text("utf-8"))
        self.assertEqual(manifest["display"], "standalone")
        self.assertTrue(manifest["start_url"].endswith("pages/login.html?source=pwa"))
        sizes = {icon["sizes"]: icon for icon in manifest["icons"]}
        self.assertIn("192x192", sizes)
        self.assertIn("512x512", sizes)
        for expected in (192, 512):
            path = FRONTEND / sizes[f"{expected}x{expected}"]["src"].removeprefix("./")
            self.assertTrue(path.is_file())
            with Image.open(path) as image:
                self.assertEqual(image.size, (expected, expected))

    def test_service_worker_never_lists_sensitive_resources(self):
        source = (FRONTEND / "sw.js").read_text("utf-8")
        shell_match = re.search(r"const SHELL_ASSETS = \[(.*?)\];", source, re.S)
        self.assertIsNotNone(shell_match)
        shell_assets = shell_match.group(1)
        for forbidden in ("/api/", "/uploads/", "/storage/", "access_token"):
            self.assertNotIn(forbidden, shell_assets)
        self.assertIn("isSensitiveRequest", source)
        self.assertIn("request.method !== 'GET'", source)

    def test_status_text_colors_meet_wcag_aa(self):
        pairs = [
            ("#142018", "#e3f1df"),
            ("#2c2100", "#fff0c4"),
            ("#36150b", "#f9ded3"),
            ("#ffffff", "#1f5136"),
        ]
        for foreground, background in pairs:
            self.assertGreaterEqual(
                self.contrast_ratio(foreground, background),
                4.5,
                f"{foreground} on {background} must meet WCAG AA",
            )

    def test_mobile_pages_connect_to_real_api_and_pwa_shell(self):
        for name in ("mobile.html", "upload.html", "leaf.html", "result.html", "profile.html"):
            source = (FRONTEND / "pages" / name).read_text("utf-8")
            self.assertIn("../manifest.webmanifest", source)
            self.assertIn("../js/api.js", source)
            self.assertIn("../js/pwa.js", source)
            self.assertNotIn("mock", source.lower())

    def test_farmer_mobile_routes_are_authorized(self):
        source = (FRONTEND / "js" / "auth.js").read_text("utf-8")
        farmer_pages = re.search(r"Farmer:\s*\[(.*?)\]", source, re.S)
        self.assertIsNotNone(farmer_pages)
        for page in ("mobile.html", "upload.html", "leaf.html", "result.html", "history.html", "profile.html"):
            self.assertIn(page, farmer_pages.group(1))

    def test_cloud_api_defaults_to_same_origin(self):
        source = (FRONTEND / "js" / "api.js").read_text("utf-8")
        self.assertIn("window.MAIZE_API_BASE", source)
        self.assertIn("return ''", source)
        self.assertIn("apiMultipartWithProgress", source)

    def test_frontend_is_served_by_backend_for_https_single_origin(self):
        client = backend.app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/frontend/pages/login.html")
        page = client.get("/frontend/pages/mobile.html")
        try:
            self.assertEqual(page.status_code, 200)
            self.assertIn("Maize Field Assistant", page.get_data(as_text=True))
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FarmerLeafFrontendTests(unittest.TestCase):
    def test_farmer_desktop_navigation_exposes_leaf_health(self):
        auth = (ROOT / "frontend/js/auth.js").read_text(encoding="utf-8")
        self.assertIn("['dashboard.html', 'upload.html', 'leaf.html', 'result.html']", auth)
        self.assertIn("'leaf.html': 'Leaf Health'", auth)

    def test_dashboard_separates_tassel_and_leaf_tasks(self):
        dashboard = (ROOT / "frontend/pages/dashboard.html").read_text(encoding="utf-8")
        self.assertIn('href="upload.html"', dashboard)
        self.assertIn('href="leaf.html"', dashboard)
        self.assertIn("Count Maize Tassels", dashboard)
        self.assertIn("Check Leaf Health", dashboard)

    def test_leaf_page_uses_external_safe_renderer(self):
        page = (ROOT / "frontend/pages/leaf.html").read_text(encoding="utf-8")
        script = (ROOT / "frontend/js/leaf.js").read_text(encoding="utf-8")
        self.assertIn('../js/leaf.js', page)
        self.assertNotIn('<script>\n', page)
        self.assertNotIn('.innerHTML', script)
        self.assertIn('textContent', script)
        self.assertIn('apiRequestDiseaseReview', script)

    def test_service_worker_precaches_leaf_controller(self):
        worker = (ROOT / "frontend/sw.js").read_text(encoding="utf-8")
        self.assertIn("'./js/leaf.js'", worker)

    def test_leaf_upload_offers_camera_and_gallery_separately(self):
        page = (ROOT / "frontend/pages/leaf.html").read_text(encoding="utf-8")
        script = (ROOT / "frontend/js/leaf.js").read_text(encoding="utf-8")
        camera = re.search(r'<input[^>]+id="leafCameraPhoto"[^>]*>', page)
        gallery = re.search(r'<input[^>]+id="leafGalleryPhoto"[^>]*>', page)
        self.assertIsNotNone(camera)
        self.assertIsNotNone(gallery)
        self.assertIn('capture="environment"', camera.group(0))
        self.assertNotIn("capture=", gallery.group(0))
        self.assertIn("'leafDesktopPhoto', 'leafCameraPhoto', 'leafGalleryPhoto'", script)
        self.assertIn("从相册选择", script)


if __name__ == "__main__":
    unittest.main()

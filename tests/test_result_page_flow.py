import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ResultPageFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result_page = (ROOT / "frontend/pages/result.html").read_text(encoding="utf-8")
        cls.upload_page = (ROOT / "frontend/pages/upload.html").read_text(encoding="utf-8")
        cls.dashboard_page = (ROOT / "frontend/pages/dashboard.html").read_text(encoding="utf-8")
        cls.dashboard_script = (ROOT / "frontend/js/dashboard.js").read_text(encoding="utf-8")

    def test_upload_redirects_with_the_persisted_result_id(self):
        self.assertIn("function resultPageUrl(result)", self.upload_page)
        self.assertIn("result.html?id=${encodeURIComponent(resultId)}", self.upload_page)
        self.assertIn("resultPageUrl(lastResult)", self.upload_page)
        self.assertIn("resultPageUrl(result)", self.upload_page)

    def test_result_page_recovers_the_latest_database_result(self):
        self.assertIn("apiGet('/api/history?limit=1')", self.result_page)
        self.assertIn("requestedResultId || (storedResult && storedResult.resultId)", self.result_page)
        self.assertIn("history.replaceState(null, '', url)", self.result_page)
        self.assertNotIn("age > 15000", self.result_page)
        self.assertNotIn("resultTimestamp", self.result_page)

    def test_dashboard_latest_result_card_receives_a_real_result_id(self):
        self.assertIn('id="latestResultLink"', self.dashboard_page)
        self.assertIn("records[0].resultId", self.dashboard_script)
        self.assertIn("result.html?id=${encodeURIComponent(records[0].resultId)}", self.dashboard_script)


if __name__ == "__main__":
    unittest.main()

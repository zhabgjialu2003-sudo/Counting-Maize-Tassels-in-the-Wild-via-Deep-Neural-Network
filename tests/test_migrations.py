import tempfile
import unittest
from pathlib import Path

from backend.migrations import _transaction_body, discover_migrations


class MigrationDiscoveryTests(unittest.TestCase):
    def test_transaction_markers_are_removed_for_runner_control(self):
        self.assertEqual(_transaction_body("BEGIN;\nSELECT 1;\nCOMMIT;"), "SELECT 1;")

    def test_migrations_are_discovered_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
            (root / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
            migrations = discover_migrations(root)
            self.assertEqual([item.name for item in migrations], ["001_first.sql", "002_second.sql"])
            self.assertTrue(all(len(item.sha256) == 64 for item in migrations))

    def test_leaf_review_migration_defines_idempotent_review_workflow(self):
        root = Path(__file__).resolve().parents[1]
        source = (
            root / "database" / "migrations" / "007_farmer_leaf_review_workflow.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("ADD COLUMN IF NOT EXISTS review_status", source)
        self.assertIn("disease_diagnoses_review_status_check", source)
        self.assertIn("'not_requested'", source)
        self.assertIn("'requested'", source)
        self.assertIn("'in_review'", source)
        self.assertIn("'reviewed'", source)
        self.assertIn("WHERE reviewed_at IS NOT NULL", source)
        self.assertIn("idx_disease_diagnoses_review_queue", source)


if __name__ == "__main__":
    unittest.main()

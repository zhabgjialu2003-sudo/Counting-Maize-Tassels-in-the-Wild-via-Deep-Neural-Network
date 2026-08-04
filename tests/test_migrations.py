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


if __name__ == "__main__":
    unittest.main()

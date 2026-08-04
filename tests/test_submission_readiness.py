import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


class SubmissionReadinessTests(unittest.TestCase):
    def test_assessor_facing_markdown_links_resolve(self):
        for relative in ("README.md", "docs/ASSESSMENT_INDEX.md"):
            document = ROOT / relative
            content = document.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                target = target.strip().strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path_text = unquote(target.split("#", 1)[0])
                resolved = (document.parent / path_text).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"Broken link in {relative}: {target}",
                )

    def test_repository_has_submission_governance_and_automation(self):
        required = (
            "CONTRIBUTING.md",
            "SECURITY.md",
            ".github/pull_request_template.md",
            ".github/workflows/quality.yml",
            "docs/ASSESSMENT_INDEX.md",
            "docs/testing/TEST_RESULTS.md",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_readme_exposes_current_assessment_entry_points(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for marker in (
            "Farmer",
            "Researcher",
            "Agronomist",
            "Admin",
            "System",
            "Assessment Evidence Index",
            "91 automated tests with zero failures",
            "models/deployment/tassel-best.pt",
            "models/deployment/maize-disease.torchscript.pt",
        ):
            self.assertIn(marker, readme)
        self.assertNotIn("The current baseline is 78", readme)

    def test_runtime_and_secret_files_are_not_tracked(self):
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        tracked = [line.replace("\\", "/") for line in completed.stdout.splitlines()]
        forbidden = []
        for path in tracked:
            name = Path(path).name
            if name == ".env" or path.endswith((".dump", ".bak", ".sqlite", ".sqlite3")):
                forbidden.append(path)
            if path.startswith(("backend/uploads/", "backend/backups/")):
                forbidden.append(path)
        self.assertEqual(forbidden, [])

        login = (ROOT / "frontend/pages/login.html").read_text(encoding="utf-8")
        schema = (ROOT / "database/schema/schema_postgresql.sql").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("fillDemo(", login)
        self.assertNotIn("Password: 123456", login)
        self.assertNotIn("sha256$8d969eef6eca", schema)
        self.assertTrue((ROOT / "backend/scripts/bootstrap_admin.py").is_file())


if __name__ == "__main__":
    unittest.main()

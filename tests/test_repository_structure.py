import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MODEL_HASHES = {
    "models/deployment/tassel-best.pt":
        "37bca6b8e817d911424dbd22f720f9cbe00248036e0fc6305ef853f8b38d9913",
    "models/deployment/maize-disease.torchscript.pt":
        "4f48a440e2eb35bef220107f9e777f9a3a10dc8fa0b79e0296a022cba700ef17",
}
CURRENT_GUIDANCE = (
    "README.md",
    "backend/README.md",
    "datasets/README.md",
    "training/README.md",
    "examples/README.md",
    "docs/ASSESSMENT_INDEX.md",
    "docs/requirements/PROJECT_DELIVERABLES.md",
    "docs/design/architecture/system-architecture.md",
    "docs/design/ai/ai-logic-design.md",
    "docs/manuals/USER_MANUAL.md",
    "docs/manuals/TECHNICAL_MANUAL.md",
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def markdown_targets(path):
    text = path.read_text(encoding="utf-8")
    pattern = r"!?\[[^\]]*\]\((<[^>]+>|(?:[^()]|\([^)]*\))*)\)"
    for match in re.finditer(pattern, text):
        target = match.group(1).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        yield target.split("#", 1)[0]


class RepositoryStructureTests(unittest.TestCase):
    def test_assessment_directories_exist(self):
        required = (
            "backend", "frontend", "database/schema", "database/migrations",
            "database/seeds", "models/deployment", "training/notebooks/tassel",
            "training/notebooks/disease", "examples", "tests", "docs/manuals",
            "docs/testing", "coursework",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_dir(), relative)

    def test_obsolete_mixed_locations_are_absent(self):
        forbidden = (
            "ai", "docs/other", "docs/diagrams", "docs/screenshots",
            "README_CODE_ONLY.md", "maize_yolo26_final (4).ipynb",
        )
        for relative in forbidden:
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_database_directory_contains_only_sql_and_markdown(self):
        allowed = {".sql", ".md"}
        files = [path for path in (ROOT / "database").rglob("*") if path.is_file()]
        self.assertTrue(files)
        for path in files:
            self.assertIn(path.suffix.lower(), allowed, str(path.relative_to(ROOT)))

    def test_deployment_models_are_materialized_and_verified(self):
        for relative, expected_hash in MODEL_HASHES.items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(path.stat().st_size, 1_000_000, relative)
            with path.open("rb") as stream:
                self.assertNotEqual(
                    stream.read(42), b"version https://git-lfs.github.com/spec/v1",
                    f"Run git lfs pull for {relative}",
                )
            self.assertEqual(sha256(path), expected_hash, relative)

    def test_executed_disease_notebook_is_error_free(self):
        path = ROOT / "training/notebooks/disease/maize_disease_agronomist_training.executed.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        executed = [
            cell for cell in notebook["cells"]
            if cell.get("cell_type") == "code" and cell.get("execution_count") is not None
        ]
        errors = [
            output for cell in notebook["cells"] for output in cell.get("outputs", [])
            if output.get("output_type") == "error"
        ]
        self.assertEqual(len(executed), 16)
        self.assertEqual(errors, [])

    def test_entry_point_markdown_links_resolve(self):
        for relative in ("README.md", "docs/ASSESSMENT_INDEX.md"):
            source = ROOT / relative
            for target in markdown_targets(source):
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = source.parent / unquote(target)
                self.assertTrue(
                    resolved.exists(),
                    f"Broken link in {relative}: {target}",
                )

    def test_current_repository_guidance_is_english_only(self):
        chinese = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
        for relative in CURRENT_GUIDANCE:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIsNone(chinese.search(text), relative)

    def test_vscode_configuration_is_valid_json(self):
        for path in (ROOT / ".vscode").glob("*.json"):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8-sig"))

    def test_sensitive_and_generated_files_are_not_tracked(self):
        result = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
        tracked = [line.replace("\\", "/") for line in result.stdout.splitlines()]
        for path in tracked:
            normalized = f"/{path}"
            self.assertFalse(normalized.endswith("/.env"), path)
            self.assertNotIn("/__pycache__/", normalized, path)
            self.assertFalse(normalized.endswith(".pyc"), path)
            self.assertFalse(normalized.endswith("/server.stdout.log"), path)
            self.assertFalse(Path(path).name.startswith("SPP-FYP"), path)

    def test_assessment_entry_points_exist(self):
        required = (
            "README.md", "docs/ASSESSMENT_INDEX.md",
            "docs/manuals/USER_MANUAL.md", "docs/manuals/TECHNICAL_MANUAL.md",
            "docs/design/architecture/system-architecture.md",
            "docs/design/ai/ai-logic-design.md",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from backend.scripts import initialize_render
from backend.scripts import materialize_deployment_models as models
from backend.scripts import render_build


class ModelMaterialisationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.root_patch = patch.object(models, "PROJECT_ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temporary.cleanup()

    def artifact(self, payload: bytes) -> models.ModelArtifact:
        return models.ModelArtifact(
            "models/deployment/test-model.pt",
            hashlib.sha256(payload).hexdigest(),
        )

    def test_existing_materialised_model_is_verified_without_download(self):
        payload = b"materialised-model" * 100
        artifact = self.artifact(payload)
        artifact.path.parent.mkdir(parents=True)
        artifact.path.write_bytes(payload)
        downloader = MagicMock()

        result = models.materialize_artifact(artifact, downloader=downloader)

        self.assertEqual(result, "verified")
        downloader.assert_not_called()

    def test_lfs_pointer_is_replaced_only_by_a_valid_download(self):
        payload = b"downloaded-model" * 100
        artifact = self.artifact(payload)
        artifact.path.parent.mkdir(parents=True)
        artifact.path.write_text(
            "version https://git-lfs.github.com/spec/v1\n"
            f"oid sha256:{artifact.sha256}\nsize {len(payload)}\n",
            encoding="ascii",
        )

        def downloader(_artifact, destination):
            destination.write_bytes(payload)

        result = models.materialize_artifact(artifact, downloader=downloader)

        self.assertEqual(result, "downloaded")
        self.assertEqual(artifact.path.read_bytes(), payload)

    def test_invalid_download_does_not_replace_the_lfs_pointer(self):
        payload = b"expected-model" * 100
        artifact = self.artifact(payload)
        artifact.path.parent.mkdir(parents=True)
        pointer = "version https://git-lfs.github.com/spec/v1\n"
        artifact.path.write_text(pointer, encoding="ascii")

        def downloader(_artifact, destination):
            destination.write_bytes(b"wrong")

        with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
            models.materialize_artifact(artifact, downloader=downloader)

        self.assertEqual(artifact.path.read_text(encoding="ascii"), pointer)


class RenderDatabaseInitialisationTests(unittest.TestCase):
    def connection(self, users_present: bool, application_tables_present: bool = False):
        connection = MagicMock()
        lookup = MagicMock()
        lookup.fetchone.return_value = (users_present, application_tables_present)
        connection.execute.side_effect = [lookup, MagicMock()]
        return connection

    def test_existing_database_skips_the_destructive_base_schema(self):
        connection = self.connection(True)

        applied = initialize_render.ensure_base_schema(connection)

        self.assertFalse(applied)
        self.assertEqual(connection.execute.call_count, 1)

    def test_empty_database_receives_the_base_schema_once(self):
        connection = self.connection(False)
        with tempfile.TemporaryDirectory() as directory:
            schema = Path(directory) / "schema.sql"
            schema.write_text("CREATE TABLE users (user_id INTEGER);", encoding="utf-8")

            applied = initialize_render.ensure_base_schema(connection, schema)

        self.assertTrue(applied)
        self.assertEqual(connection.execute.call_count, 2)
        connection.execute.assert_called_with("CREATE TABLE users (user_id INTEGER);")

    def test_partial_database_stops_before_destructive_schema_execution(self):
        connection = self.connection(False, True)

        with self.assertRaisesRegex(RuntimeError, "partial application schema"):
            initialize_render.ensure_base_schema(connection)

        self.assertEqual(connection.execute.call_count, 1)


class RenderBlueprintTests(unittest.TestCase):
    def test_blueprint_uses_paid_singapore_resources_without_plaintext_secrets(self):
        blueprint = (Path(__file__).resolve().parents[1] / "render.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("plan: standard", blueprint)
        self.assertIn("plan: basic-256mb", blueprint)
        self.assertEqual(blueprint.count("region: singapore"), 2)
        self.assertIn("healthCheckPath: /api/health", blueprint)
        self.assertIn("key: DEMO_ACCOUNT_PASSWORD\n        sync: false", blueprint)
        self.assertNotIn("MaizeDemo!2026", blueprint)
        self.assertNotIn("PGPASSWORD=", blueprint)

    def test_render_build_selects_cpu_torch_and_headless_opencv(self):
        with (
            patch.object(render_build, "run") as run,
            patch.object(render_build, "materialize_models") as materialize,
        ):
            render_build.main()

        materialize.assert_called_once_with()
        commands = [" ".join(call.args) for call in run.call_args_list]
        self.assertTrue(any("download.pytorch.org/whl/cpu" in item for item in commands))
        self.assertTrue(any("uninstall --yes opencv-python" in item for item in commands))
        self.assertTrue(any("opencv-python-headless>=4.8.0" in item for item in commands))


class HostedRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_module = importlib.import_module("backend.app")

    def test_strict_health_rejects_an_unavailable_deployment_model(self):
        tassel = SimpleNamespace(available=True, model_path=Path("tassel-best.pt"))
        disease = MagicMock()
        disease.health.return_value = {
            "available": False,
            "status": "unavailable",
            "model_version": None,
            "deployment_ready": False,
            "error": "Disease artifact unavailable",
        }
        with (
            patch.dict(os.environ, {"REQUIRE_MODELS_HEALTHY": "true"}),
            patch.object(self.app_module, "db_ready", return_value=(True, None)),
            patch.object(self.app_module, "get_predictor", return_value=tassel),
            patch.object(self.app_module, "get_disease_predictor", return_value=disease),
        ):
            response = self.app_module.app.test_client().get("/api/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["status"], "degraded")

    def test_hosted_runtime_can_disable_filesystem_backup_scheduler(self):
        with (
            patch.dict(os.environ, {"AUTO_BACKUP_ENABLED": "false"}),
            patch.object(self.app_module.threading, "Thread") as thread,
        ):
            self.app_module.start_backup_scheduler()

        thread.assert_not_called()


if __name__ == "__main__":
    unittest.main()

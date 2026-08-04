import tempfile
import unittest
from pathlib import Path

from backend.security.model_paths import ModelArtifactError, validate_model_artifact
from backend.security.passwords import password_policy_error
from backend.security.path_controls import ApprovedPathError, resolve_approved_path
from backend.security.rate_limits import InMemoryRateLimiter
from backend.services.training_jobs import BoundedJobExecutor


class RateLimiterTests(unittest.TestCase):
    def test_sliding_window_rejects_and_then_recovers(self):
        limiter = InMemoryRateLimiter()
        self.assertTrue(limiter.check("login", "client", limit=2, window_seconds=60, now=0).allowed)
        self.assertTrue(limiter.check("login", "client", limit=2, window_seconds=60, now=1).allowed)
        rejected = limiter.check("login", "client", limit=2, window_seconds=60, now=2)
        self.assertFalse(rejected.allowed)
        self.assertGreater(rejected.retry_after, 0)
        self.assertTrue(limiter.check("login", "client", limit=2, window_seconds=60, now=61).allowed)


class ModelArtifactValidationTests(unittest.TestCase):
    def test_artifact_must_remain_inside_an_approved_root(self):
        with tempfile.TemporaryDirectory() as approved, tempfile.TemporaryDirectory() as outside:
            candidate = Path(outside) / "model.pt"
            candidate.write_bytes(b"model" * 300)
            with self.assertRaises(ModelArtifactError):
                validate_model_artifact(candidate, roots=[Path(approved)])

    def test_artifact_digest_is_verified(self):
        with tempfile.TemporaryDirectory() as approved:
            candidate = Path(approved) / "model.pt"
            candidate.write_bytes(b"model" * 300)
            artifact = validate_model_artifact(candidate, roots=[Path(approved)])
            self.assertEqual(len(artifact.sha256), 64)
            with self.assertRaises(ModelArtifactError):
                validate_model_artifact(candidate, roots=[Path(approved)], expected_sha256="0" * 64)


class ApprovedPathTests(unittest.TestCase):
    def test_directory_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "datasets"
            root.mkdir()
            outside = Path(directory) / "secret.yaml"
            outside.write_text("names: []", encoding="utf-8")
            with self.assertRaises(ApprovedPathError):
                resolve_approved_path(outside, roots=[root], must_be_file=True)

    def test_expected_file_inside_root_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "maize.yaml"
            dataset.write_text("names: [tassel]", encoding="utf-8")
            resolved = resolve_approved_path(
                dataset,
                roots=[root],
                allowed_suffixes={".yaml"},
                must_be_file=True,
            )
            self.assertEqual(resolved, dataset.resolve())


class PasswordPolicyTests(unittest.TestCase):
    def test_short_and_common_passwords_are_rejected(self):
        self.assertIsNotNone(password_policy_error("short"))
        self.assertIsNotNone(password_policy_error("password123"))
        self.assertIsNone(password_policy_error("field-safe-2026"))


class BoundedTrainingExecutorTests(unittest.TestCase):
    def test_pending_capacity_is_bounded(self):
        import threading

        gate = threading.Event()
        executor = BoundedJobExecutor(max_workers=1, max_pending=1)
        try:
            first = executor.submit(gate.wait, 1)
            second = executor.submit(lambda: None)
            self.assertIsNotNone(first)
            self.assertIsNone(second)
            gate.set()
            first.result(timeout=2)
        finally:
            gate.set()
            executor.shutdown()


if __name__ == "__main__":
    unittest.main()

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from backend.image_security import (
    InvalidImageUpload,
    read_limited,
    validate_image_bytes,
)
from backend.inference import YOLOPredictor


def image_bytes(colour: tuple[int, int, int], image_format: str = "PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (32, 32), colour).save(output, format=image_format)
    return output.getvalue()


class ImageUploadSecurityTests(unittest.TestCase):
    def test_valid_images_receive_unique_server_names(self):
        data = image_bytes((20, 120, 40))
        first = validate_image_bytes(data, "field.png", "image/png")
        second = validate_image_bytes(data, "field.png", "image/png")
        self.assertNotEqual(first.stored_name, second.stored_name)
        self.assertEqual(first.original_name, "field.png")
        self.assertEqual(first.sha256, second.sha256)

    def test_extension_cannot_disguise_non_image_bytes(self):
        with self.assertRaises(InvalidImageUpload):
            validate_image_bytes(b"not an image", "field.jpg", "image/jpeg")

    def test_declared_mime_must_match_decoded_image(self):
        with self.assertRaises(InvalidImageUpload):
            validate_image_bytes(image_bytes((1, 2, 3)), "field.png", "image/jpeg")

    def test_stream_read_stops_at_configured_limit(self):
        with self.assertRaises(InvalidImageUpload):
            read_limited(io.BytesIO(b"12345"), max_bytes=4)


class InferenceCacheTests(unittest.TestCase):
    def predictor(self, capacity: int = 4) -> YOLOPredictor:
        predictor = YOLOPredictor(Path("test-model.pt"), max_cache_entries=capacity)
        predictor._available = True
        predictor._model = object()
        return predictor

    def test_same_filename_with_different_bytes_is_not_a_cache_hit(self):
        predictor = self.predictor()
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            left_path = Path(left) / "field.png"
            right_path = Path(right) / "field.png"
            left_path.write_bytes(image_bytes((255, 0, 0)))
            right_path.write_bytes(image_bytes((0, 255, 0)))
            with patch.object(predictor, "_detect_single", return_value=[]) as detect:
                first = predictor.detect(left_path)
                second = predictor.detect(right_path)
            self.assertFalse(first["cache_hit"])
            self.assertFalse(second["cache_hit"])
            self.assertEqual(detect.call_count, 2)

    def test_identical_content_reuses_cached_result(self):
        predictor = self.predictor()
        data = image_bytes((10, 20, 30))
        with tempfile.TemporaryDirectory() as directory:
            first_path = Path(directory) / "first.png"
            second_path = Path(directory) / "second.png"
            first_path.write_bytes(data)
            second_path.write_bytes(data)
            with patch.object(predictor, "_detect_single", return_value=[]) as detect:
                predictor.detect(first_path)
                second = predictor.detect(second_path)
            self.assertTrue(second["cache_hit"])
            self.assertEqual(detect.call_count, 1)

    def test_cache_capacity_is_bounded(self):
        predictor = self.predictor(capacity=1)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(predictor, "_detect_single", return_value=[]):
                for index, colour in enumerate(((1, 2, 3), (4, 5, 6))):
                    path = Path(directory) / f"{index}.png"
                    path.write_bytes(image_bytes(colour))
                    predictor.detect(path)
        self.assertEqual(predictor.cache_info(), {"size": 1, "capacity": 1})

    def test_fast_image_size_can_be_reduced_for_hosted_inference(self):
        with patch.dict("os.environ", {"INFERENCE_FAST_IMAGE_SIZE": "1024"}):
            predictor = YOLOPredictor(Path("test-model.pt"))
        predictor._available = True
        predictor._model = object()
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "field.png"
            image_path.write_bytes(image_bytes((20, 120, 40)))
            with patch.object(predictor, "_detect_single", return_value=[]) as detect:
                predictor.detect(image_path, mode="fast")
        self.assertEqual(detect.call_args.kwargs["image_size"], 1024)


if __name__ == "__main__":
    unittest.main()

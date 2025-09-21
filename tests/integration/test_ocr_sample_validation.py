"""Integration tests for OCR engines using stratified test samples.

This test suite validates OCR engine performance across different image quality
scenarios using samples from the test bundle created by create_test_sample_bundle.py.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engines import dispatch


class OCRValidationConfig:
    """Configuration for OCR validation expectations."""

    # Confidence thresholds for each category
    CONFIDENCE_THRESHOLDS = {
        "readable_labels": 0.80,    # Should achieve high confidence
        "minimal_text": 0.30,       # May have lower confidence but should extract something
        "unlabeled": 0.20,          # Should not produce false positives
        "poor_quality": 0.10        # Should fail gracefully
    }

    # Minimum text length expectations (characters)
    MIN_TEXT_LENGTH = {
        "readable_labels": 10,      # Should extract meaningful text
        "minimal_text": 3,          # May extract partial text
        "unlabeled": 0,             # May extract nothing
        "poor_quality": 0           # May extract nothing
    }

    # Maximum allowed processing time (seconds)
    MAX_PROCESSING_TIME = {
        "readable_labels": 30,
        "minimal_text": 30,
        "unlabeled": 30,
        "poor_quality": 45  # May take longer due to poor quality
    }


class TestSampleValidator:
    """Validator for OCR performance on test samples."""

    def __init__(self, bundle_path: Path):
        self.bundle_path = bundle_path
        self.manifest = self._load_manifest()
        self.categories = self._load_categories()

    def _load_manifest(self) -> Dict:
        """Load the test sample manifest."""
        manifest_path = self.bundle_path / "manifest.json"
        if not manifest_path.exists():
            pytest.skip(f"Test sample manifest not found: {manifest_path}")

        with manifest_path.open() as f:
            return json.load(f)

    def _load_categories(self) -> Dict:
        """Load category descriptions."""
        categories_path = self.bundle_path / "test_categories.json"
        if categories_path.exists():
            with categories_path.open() as f:
                return json.load(f)
        return {}

    def get_images_by_category(self, category: str) -> List[Path]:
        """Get all images for a specific category."""
        images = []
        for img_metadata in self.manifest["images"]:
            if img_metadata["category"] == category:
                img_path = self.bundle_path / img_metadata["local_path"]
                if img_path.exists():
                    images.append(img_path)
        return images

    def validate_ocr_result(
        self,
        image_path: Path,
        text: str,
        confidences: List[float],
        category: str,
        processing_time: float
    ) -> Dict[str, bool]:
        """Validate OCR result against category expectations."""
        results = {}

        # Check confidence threshold
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        expected_confidence = OCRValidationConfig.CONFIDENCE_THRESHOLDS[category]
        results["confidence_met"] = avg_confidence >= expected_confidence

        # Check text length
        min_length = OCRValidationConfig.MIN_TEXT_LENGTH[category]
        results["text_length_adequate"] = len(text.strip()) >= min_length

        # Check processing time
        max_time = OCRValidationConfig.MAX_PROCESSING_TIME[category]
        results["processing_time_acceptable"] = processing_time <= max_time

        # Category-specific validations
        if category == "unlabeled":
            # Should not produce too much false positive text
            results["low_false_positives"] = len(text.strip()) < 50
        elif category == "poor_quality":
            # Should not crash or produce garbage
            results["graceful_handling"] = text is not None and isinstance(text, str)
        elif category == "readable_labels":
            # Should extract meaningful content
            results["meaningful_content"] = len(text.strip()) >= 20 and avg_confidence >= 0.7

        return results


@pytest.fixture(scope="session")
def test_bundle_path():
    """Locate the test sample bundle."""
    possible_paths = [
        Path("./test_sample_bundle"),
        Path("./test_sample_bundle.zip"),
        Path("../test_sample_bundle"),
        Path("../../test_sample_bundle")
    ]

    for path in possible_paths:
        if path.exists():
            if path.suffix == ".zip":
                # Extract if it's a ZIP file
                import zipfile
                extract_path = path.parent / path.stem
                if not extract_path.exists():
                    with zipfile.ZipFile(path, 'r') as zipf:
                        zipf.extractall(extract_path)
                return extract_path
            return path

    pytest.skip("Test sample bundle not found. Run create_test_sample_bundle.py first.")


@pytest.fixture(scope="session")
def validator(test_bundle_path):
    """Create validator for the test bundle."""
    return TestSampleValidator(test_bundle_path)


@pytest.fixture(params=["tesseract", "vision_swift", "multilingual"])
def ocr_engine(request):
    """Parameterized fixture for testing multiple OCR engines."""
    return request.param


class TestOCRSampleValidation:
    """Test suite for OCR validation using stratified samples."""

    def test_readable_labels_quality(self, validator, ocr_engine):
        """Test OCR performance on images with readable labels."""
        images = validator.get_images_by_category("readable_labels")
        if not images:
            pytest.skip("No readable_labels samples found")

        successes = 0
        total_images = len(images)

        for image_path in images[:5]:  # Test subset for speed
            try:
                import time
                start_time = time.time()

                text, confidences = dispatch(
                    "image_to_text",
                    image=image_path,
                    engine=ocr_engine
                )

                processing_time = time.time() - start_time

                results = validator.validate_ocr_result(
                    image_path, text, confidences, "readable_labels", processing_time
                )

                # For readable labels, we expect high success rate
                if results.get("confidence_met", False) and results.get("meaningful_content", False):
                    successes += 1

            except Exception as e:
                pytest.fail(f"OCR failed on readable label {image_path}: {e}")

        # At least 70% of readable labels should be processed successfully
        success_rate = successes / min(5, total_images)
        assert success_rate >= 0.7, f"Only {success_rate:.1%} of readable labels processed successfully"

    def test_minimal_text_robustness(self, validator, ocr_engine):
        """Test OCR robustness on images with minimal text."""
        images = validator.get_images_by_category("minimal_text")
        if not images:
            pytest.skip("No minimal_text samples found")

        for image_path in images[:3]:  # Test subset
            try:
                import time
                start_time = time.time()

                text, confidences = dispatch(
                    "image_to_text",
                    image=image_path,
                    engine=ocr_engine
                )

                processing_time = time.time() - start_time

                results = validator.validate_ocr_result(
                    image_path, text, confidences, "minimal_text", processing_time
                )

                # Should process without crashing and within time limit
                assert results.get("processing_time_acceptable", False), \
                    f"Processing took too long: {processing_time}s"

            except Exception as e:
                pytest.fail(f"OCR failed on minimal text image {image_path}: {e}")

    def test_unlabeled_specimens_handling(self, validator, ocr_engine):
        """Test OCR behavior on unlabeled specimens (should minimize false positives)."""
        images = validator.get_images_by_category("unlabeled")
        if not images:
            pytest.skip("No unlabeled samples found")

        false_positive_count = 0

        for image_path in images[:3]:  # Test subset
            try:
                text, confidences = dispatch(
                    "image_to_text",
                    image=image_path,
                    engine=ocr_engine
                )

                results = validator.validate_ocr_result(
                    image_path, text, confidences, "unlabeled", 0
                )

                # Count potential false positives
                if not results.get("low_false_positives", True):
                    false_positive_count += 1

            except Exception as e:
                pytest.fail(f"OCR failed on unlabeled specimen {image_path}: {e}")

        # Should have minimal false positives
        assert false_positive_count <= 1, f"Too many false positives: {false_positive_count}"

    def test_poor_quality_graceful_failure(self, validator, ocr_engine):
        """Test that OCR handles poor quality images gracefully."""
        images = validator.get_images_by_category("poor_quality")
        if not images:
            pytest.skip("No poor_quality samples found")

        for image_path in images[:3]:  # Test subset
            try:
                text, confidences = dispatch(
                    "image_to_text",
                    image=image_path,
                    engine=ocr_engine
                )

                results = validator.validate_ocr_result(
                    image_path, text, confidences, "poor_quality", 0
                )

                # Should handle gracefully (not crash)
                assert results.get("graceful_handling", False), \
                    f"OCR did not handle poor quality image gracefully: {image_path}"

            except Exception as e:
                # Some failures are acceptable for poor quality images
                # but should not be crashes due to code errors
                if "EngineError" not in str(type(e)):
                    pytest.fail(f"Unexpected error type on poor quality image {image_path}: {e}")

    def test_engine_performance_comparison(self, validator):
        """Compare performance across different OCR engines."""
        if not hasattr(self, "_engine_results"):
            pytest.skip("Run with multiple engines to compare")

        # This would collect results across engine runs and compare
        # Implementation depends on how pytest parameterization stores results
        pass

    def test_sample_bundle_integrity(self, validator):
        """Validate the integrity of the test sample bundle."""
        manifest = validator.manifest

        # Check required fields
        assert "total_images" in manifest
        assert "categories" in manifest
        assert "images" in manifest

        # Check that all referenced images exist
        missing_images = []
        for img_metadata in manifest["images"]:
            img_path = validator.bundle_path / img_metadata["local_path"]
            if not img_path.exists():
                missing_images.append(img_metadata["local_path"])

        assert not missing_images, f"Missing images: {missing_images}"

        # Check category distribution
        total_expected = sum(manifest["categories"].values())
        assert total_expected == manifest["total_images"], \
            "Category counts don't match total"


class TestOCRRegression:
    """Regression tests to detect OCR quality degradation."""

    def test_known_good_samples(self, validator, ocr_engine):
        """Test OCR on samples that should always work well."""
        # This would test against a curated set of "golden" samples
        # with known expected outputs
        pytest.skip("Implement with curated golden samples")

    def test_performance_benchmarks(self, validator, ocr_engine):
        """Benchmark OCR processing speed."""
        images = validator.get_images_by_category("readable_labels")
        if not images:
            pytest.skip("No samples for benchmarking")

        import time
        processing_times = []

        for image_path in images[:3]:
            start_time = time.time()
            try:
                dispatch("image_to_text", image=image_path, engine=ocr_engine)
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
            except Exception:
                pass  # Skip failed images for benchmark

        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            # Assert reasonable processing time (adjust based on your requirements)
            assert avg_time < 30, f"Average processing time too slow: {avg_time:.2f}s"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
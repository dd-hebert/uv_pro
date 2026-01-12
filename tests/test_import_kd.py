"""Tests for import_kd module."""

import warnings
from pathlib import Path

import pytest

from uv_pro.io.import_kd import KDFile


TEST_DATA_DIR = Path(__file__).parent.parent / "test data"


class TestKDFileCorruptionDetection:
    """Test detection of corrupted .KD files with non-monotonic time values."""

    def test_valid_multi_cuvette_file_no_warning(self):
        """Test that valid multi-cuvette file does not generate a warning."""
        file_path = TEST_DATA_DIR / "multi_cuvette_test_data.KD"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            kd = KDFile(file_path)

            # Filter for UserWarnings about corruption
            corruption_warnings = [
                warning for warning in w
                if issubclass(warning.category, UserWarning)
                and "corrupted" in str(warning.message).lower()
            ]

            assert len(corruption_warnings) == 0, (
                f"Expected no corruption warnings for valid file, "
                f"but got: {[str(w.message) for w in corruption_warnings]}"
            )

    def test_corrupted_multi_cuvette_file_generates_warning(self):
        """Test that corrupted multi-cuvette file generates a warning."""
        file_path = TEST_DATA_DIR / "multi_cuvette_test_data_corrupted.KD"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            kd = KDFile(file_path)

            # Filter for UserWarnings about corruption
            corruption_warnings = [
                warning for warning in w
                if issubclass(warning.category, UserWarning)
                and "corrupted" in str(warning.message).lower()
            ]

            assert len(corruption_warnings) >= 1, (
                "Expected at least one corruption warning for corrupted file"
            )

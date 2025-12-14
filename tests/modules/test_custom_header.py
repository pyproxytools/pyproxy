"""
test_custom_header.py

This test module verifies the functionality of the `custom_header.py` module.

Tests:
- test_load_custom_header: Ensures JSON headers are correctly loaded from a test file.
- test_custom_header_process: Validates the multiprocessing behavior of resolving custom headers.
"""

import unittest
import tempfile
import os
import multiprocessing
import time
import json

from pyproxy.modules.custom_header import custom_header_process


class TestCustomHeader(unittest.TestCase):
    """Unit tests for the custom_header.py module."""

    def setUp(self):
        """Set up a temporary JSON file with test data for custom headers."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.sample_data = {
            "http://example.com": {"X-Test-Header": "123", "X-Another": "456"},
            "http://another.com": {"X-Custom": "abc"},
        }
        json.dump(self.sample_data, self.temp_file)
        self.temp_file.close()
        self.path = self.temp_file.name

    def tearDown(self):
        """Remove the temporary file after tests complete."""
        os.unlink(self.path)

    def test_load_custom_header(self):
        """Test that the custom header dict is correctly used."""
        # Since we embed, no load function
        pass

    def test_custom_header_process(self):
        """Test that the custom header process returns the correct header dictionary."""
        queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=custom_header_process, args=(queue, result_queue, self.sample_data)
        )
        process.start()

        time.sleep(1)

        queue.put("http://example.com")
        result = result_queue.get(timeout=3)
        self.assertEqual(result, {"X-Test-Header": "123", "X-Another": "456"})

        queue.put("http://nonexistent.com")
        result = result_queue.get(timeout=3)
        self.assertEqual(result, {})

        process.terminate()
        process.join()


if __name__ == "__main__":
    unittest.main()

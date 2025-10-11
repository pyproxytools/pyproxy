"""
test_filter.py

This module contains unit tests for the `filter.py` module.
It verifies the correct functionality of loading blacklists and filtering domains/URLs.

Tested Functions:
- load_blacklist: Ensures that the blacklist is correctly loaded from the file.
- filter_process: Ensures that domains/URLs are correctly filtered based on the blacklist.

Test Cases:
- TestLoadBlacklist: Checks the correct loading of blocked sites and URLs from the file.
- TestFilterProcess: Verifies that domains/URLs are correctly identified as blocked or allowed.
- TestLoadBlacklistFileNotFound: Verifies that a FileNotFoundError is
                raised when the blacklist file is missing.
- TestLoadBlacklistHttpError: Verifies that an HTTP error is handled
                correctly when loading blacklists.
- TestLoadBlacklistEmptyFile: Verifies that an empty file returns empty
                sets for blocked sites and URLs.
- TestFilterProcessWithPathAndPort: Verifies that URLs with paths or ports are correctly filtered.
"""

import unittest
import multiprocessing
from unittest.mock import patch, mock_open
import requests
from pyproxy.modules.filter import load_blacklist, filter_process


class TestFilter(unittest.TestCase):
    """
    Test suite for the filter module.
    """

    def setUp(self):
        """Sets up the common resources for tests."""
        self.queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()

    def tearDown(self):
        """Cleans up after each test."""
        while not self.queue.empty():
            self.queue.get_nowait()
        while not self.result_queue.empty():
            self.result_queue.get_nowait()

    def test_load_blacklist(self):
        """Tests if the blacklist is correctly loaded from the file."""
        with patch(
            "builtins.open",
            new_callable=mock_open,
            read_data="blocked.com\nallowed.com/blocked",
        ):
            blocked_sites, blocked_urls = load_blacklist(
                "blocked_sites.txt", "blocked_urls.txt", "local"
            )
            self.assertIn("blocked.com", blocked_sites)
            self.assertIn("allowed.com/blocked", blocked_sites)
            self.assertIsInstance(blocked_sites, set)
            self.assertIsInstance(blocked_urls, set)

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_load_blacklist_file_not_found(self, _mock_file):
        """Tests that a FileNotFoundError is raised when the blacklist file is missing."""
        with self.assertRaises(FileNotFoundError):
            load_blacklist("invalid_file.txt", "blocked_urls.txt", "local")

    @patch(
        "requests.get",
        side_effect=requests.exceptions.RequestException("Failed to load"),
    )
    def test_load_blacklist_http_error(self, _mock_request):
        """Tests that an HTTP error is handled correctly when loading blacklists."""
        with self.assertRaises(requests.exceptions.RequestException):
            load_blacklist(
                "http://example.com/blocked_sites",
                "http://example.com/blocked_urls",
                "http",
            )

    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_load_blacklist_empty_file(self, _mock_file):
        """Tests that an empty file returns empty sets for blocked sites and URLs."""
        blocked_sites, blocked_urls = load_blacklist("empty_sites.txt", "empty_urls.txt", "local")
        self.assertEqual(len(blocked_sites), 0)
        self.assertEqual(len(blocked_urls), 0)

    def _test_filter_process_helper(
        self,
        input_urls,
        expected_results,
        patch_data="blocked.com\nallowed.com/blocked",
    ):
        """Helper method to test filter_process with different inputs."""
        with patch("builtins.open", new_callable=mock_open, read_data=patch_data):
            process = multiprocessing.Process(
                target=filter_process,
                args=(
                    self.queue,
                    self.result_queue,
                    "local",
                    "blocked_sites.txt",
                    "blocked_urls.txt",
                ),
            )
            process.start()

            for url in input_urls:
                self.queue.put(url)

            results = []
            for _ in expected_results:
                results.append(self.result_queue.get(timeout=2))

            self.assertEqual(results, expected_results)
            process.terminate()
            process.join()

    def test_filter_process(self):
        """Tests if domains/URLs are correctly identified as blocked or allowed."""
        input_urls = [
            "http://blocked.com/",
            "http://allowed.com/",
            "http://allowed.com/blocked",
            "http://allowed.com/allowed",
        ]
        expected_results = [
            ("blocked.com", "Blocked"),
            ("allowed.com", "Allowed"),
            ("allowed.com/blocked", "Blocked"),
            ("allowed.com", "Allowed"),
        ]
        self._test_filter_process_helper(input_urls, expected_results)

    def test_filter_process_with_query_string(self):
        """Tests if URLs with query strings are correctly filtered."""
        input_urls = [
            "http://blocked.com?tracking=123",
            "http://example.com/secret?auth=false",
            "http://safe.com/page?debug=true",
        ]
        expected_results = [
            ("blocked.com", "Blocked"),
            ("example.com/secret", "Blocked"),
            ("safe.com", "Allowed"),
        ]
        self._test_filter_process_helper(
            input_urls, expected_results, patch_data="blocked.com\nexample.com/secret"
        )

    def test_filter_process_subdomain_not_blocked(self):
        """
        Tests if subdomains are correctly handled and not blocked if the main domain is not blocked.
        """
        input_urls = ["http://sub.blocked.com/"]
        expected_results = [("sub.blocked.com", "Allowed")]
        self._test_filter_process_helper(input_urls, expected_results, patch_data="blocked.com\n")

    def test_filter_process_special_characters(self):
        """Tests if URLs with special characters are correctly handled."""
        input_urls = ["http://weird-site.com/"]
        expected_results = [("weird-site.com", "Blocked")]
        self._test_filter_process_helper(
            input_urls, expected_results, patch_data="weird-site.com\n"
        )

    def test_filter_process_with_path_and_port(self):
        """Tests if URLs with paths and ports are correctly filtered."""
        input_urls = [
            "http://blocked.com:8080/path/to/resource",
            "http://allowed.com/blocked/resource",
        ]
        expected_results = [
            ("blocked.com", "Blocked"),
            ("allowed.com/blocked/resource", "Blocked"),
        ]
        self._test_filter_process_helper(input_urls, expected_results)


if __name__ == "__main__":
    unittest.main()

"""
pyproxy.modules.custom_header.py

This module contains functions and a process to load and monitor custom header entries.
It uses custom header data from the configuration and checks if specific entries exist in it.

Functions:
- custom_header_process: Process that listens for header-like entries and checks
  if they exist in the custom header list.
"""

import multiprocessing


def custom_header_process(
    queue: multiprocessing.Queue,
    result_queue: multiprocessing.Queue,
    custom_header: dict[str, dict[str, str]],
) -> None:
    """
    Process that checks if received entries exist in the custom header dict.

    Args:
        queue (multiprocessing.Queue): A queue to receive header-like entries to check.
        result_queue (multiprocessing.Queue): A queue to send back the headers.
        custom_header (dict[str, dict[str, str]]): The dict of custom headers.
    """
    while True:
        try:
            url = queue.get()
            headers = custom_header.get(url, {})
            result_queue.put(headers)

        except KeyboardInterrupt:
            break

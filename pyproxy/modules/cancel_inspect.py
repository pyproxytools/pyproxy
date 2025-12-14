"""
pyproxy.modules.cancel_inspect.py

This module contains functions and a process to load and monitor cancel inspection entries.
It uses cancel inspection data from the configuration and checks whether specific entries exist
in that list.

Functions:
- cancel_inspect_process: Process that listens for URL-like entries and checks
  if they exist in the cancel inspection list.
"""

import multiprocessing


def load_cancel_inspect(cancel_inspect_path: str) -> dict:
    """
    Loads cancel inspection entries from a file into a list.

    Args:
        cancel_inspect_path (str): The path to the file containing the entries.

    Returns:
        list: A list containing each line (entry) from the file.
    """
    cancel_inspect = []

    with open(cancel_inspect_path, "r", encoding="utf-8") as f:
        for line in f:
            cancel_inspect.append(line)

    return cancel_inspect


def cancel_inspect_process(
    queue: multiprocessing.Queue,
    result_queue: multiprocessing.Queue,
    cancel_inspect: list[str],
) -> None:
    """
    Process that checks if received entries exist in the cancel inspection list.

    Args:
        queue (multiprocessing.Queue): A queue to receive entries to check.
        result_queue (multiprocessing.Queue): A queue to send back True/False depending on match.
        cancel_inspect (list[str]): The list of cancel inspection entries.
    """
    while True:
        try:
            url = queue.get()
            if url in cancel_inspect:
                result_queue.put(True)
            else:
                result_queue.put(False)

        except KeyboardInterrupt:
            break

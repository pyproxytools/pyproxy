"""
pyproxy.modules.shortcuts.py

This module contains functions and a process to load and manage URL shortcuts.
It loads shortcuts (alias to URL mappings) from a specified file, and provides
a process that listens for requests to resolve an alias to its corresponding URL.

Functions:
- shortcuts_process: The process that listens for alias requests and resolves them to URLs.
"""

import multiprocessing


def load_shortcuts(shortcuts_path: str) -> dict:
    """
    Loads URL alias mappings from a file into a dictionary for fast lookup.

    Args:
        shortcuts_path (str): The path to the file containing alias=URL mappings.

    Returns:
        dict: A dictionary mapping aliases to URLs.
    """
    shortcuts = {}

    with open(shortcuts_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                alias, url = line.split("=", 1)
                shortcuts[alias.strip()] = url.strip()

    return shortcuts


def shortcuts_process(
    queue: multiprocessing.Queue,
    result_queue: multiprocessing.Queue,
    shortcuts: dict[str, str],
) -> None:
    """
    Process that listens for alias requests and resolves them to URLs.

    Args:
        queue (multiprocessing.Queue): A queue to receive alias for URL resolution.
        result_queue (multiprocessing.Queue): A queue to send back the resolved URL.
        shortcuts (dict[str, str]): The dictionary of alias to URL mappings.
    """
    while True:
        try:
            alias = queue.get()
            url = shortcuts.get(alias)
            result_queue.put(url)

        except KeyboardInterrupt:
            break

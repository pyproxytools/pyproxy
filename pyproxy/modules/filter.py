"""
pyproxy.modules.filter.py

This module contains functions and a process to filter and block domains and URLs.
It loads blocked domain names and URLs from specified files, then listens for
incoming requests to check if the domain or URL should be blocked.

Functions:
- load_blacklist: Loads blocked FQDNs and URLs from files into sets for fast lookup.
- filter_process: The process that checks whether a domain or URL is blocked.
"""

import multiprocessing
import time
import sys
import threading
from urllib.parse import urlparse
import requests


def load_blacklist(blocked_sites_path: str, blocked_url_path: str, filter_mode: str) -> set:
    """
    Loads blocked FQDNs or URLs from a file or URL into a set for fast lookup.

    Args:
        blocked_sites_path (str): The path or URL to the file containing blocked FQDNs.
        blocked_url_path (str): The path or URL to the file containing blocked URLs.
        filter_mode (str): Mode to determine if we load from local file or HTTP URL.

    Returns:
        set: A set of blocked domains/URLs.
    """
    blocked_sites = set()
    blocked_url = set()

    def load_from_file(file_path: str) -> set:
        data = set()
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                data.add(line.strip())
        return data

    def load_from_http(url: str) -> set:
        data = set()
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            for line in response.text.splitlines():
                data.add(line.strip())
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Failed to load data from {url}: {e}")
        return data

    if filter_mode == "local":
        blocked_sites = load_from_file(blocked_sites_path)
        blocked_url = load_from_file(blocked_url_path)
    elif filter_mode == "http":
        blocked_sites = load_from_http(blocked_sites_path)
        blocked_url = load_from_http(blocked_url_path)

    return blocked_sites, blocked_url


def filter_process(
    queue: multiprocessing.Queue,
    result_queue: multiprocessing.Queue,
    filter_mode: str,
    blocked_sites_path: str,
    blocked_url_path: str,
    refresh_interval=5,
) -> None:
    """
    Process that listens for requests and checks if the domain/URL should be blocked.

    Args:
        queue (multiprocessing.Queue): A queue to receive URL/domain for checking.
        result_queue (multiprocessing.Queue): A queue to send back the result of
                the filtering (blocked or allowed).
        filter_mode (str): Filter list mode (local or http).
        blocked_sites_path (str): The path to the file containing blocked FQDNs.
        blocked_url_path (str): The path to the file containing blocked URLs.
        refresh_interval (int): Interval in seconds to reload the blacklist files.
    """
    manager = multiprocessing.Manager()
    blocked_data = manager.dict(
        {
            "sites": load_blacklist(blocked_sites_path, blocked_url_path, filter_mode)[0],
            "urls": load_blacklist(blocked_sites_path, blocked_url_path, filter_mode)[1],
        }
    )

    error_event = threading.Event()

    def file_monitor() -> None:
        try:
            while True:
                new_blocked_sites, new_blocked_url = load_blacklist(
                    blocked_sites_path, blocked_url_path, filter_mode
                )

                blocked_data["sites"] = new_blocked_sites
                blocked_data["urls"] = new_blocked_url

                time.sleep(refresh_interval)
        except (IOError, ValueError) as e:
            print(f"File monitor error: {e}")
            error_event.set()

    monitor_thread = threading.Thread(target=file_monitor, daemon=True)
    monitor_thread.start()

    while True:
        if error_event.is_set():
            print("Error detected in file monitor thread, terminating process.")
            sys.exit(1)

        try:
            request = queue.get()

            if "://" in request:
                parsed = urlparse(request)
                server_host = parsed.hostname
                url_path = parsed.path if parsed.path else "/"
                full_url = (server_host or "") + url_path
            else:
                parts = request.split(":")
                server_host = parts[0] if parts else None
                full_url = server_host

            if "*" in blocked_data["sites"] or any(
                server_host.startswith(blocked_host) for blocked_host in blocked_data["sites"]
            ):
                result_queue.put((server_host, "Blocked"))
            elif any(full_url.startswith(blocked_url) for blocked_url in blocked_data["urls"]):
                result_queue.put((full_url, "Blocked"))
            else:
                result_queue.put((server_host, "Allowed"))

        except KeyboardInterrupt:
            break

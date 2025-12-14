"""
pyproxy.modules.filter.py

This module contains functions and a process to filter and block domains and URLs.
It uses blocked domain names and URLs from the configuration, then listens for
incoming requests to check if the domain or URL should be blocked.

Functions:
- load_blacklist: Loads blocked FQDNs and URLs from lists into sets for fast lookup.
- filter_process: The process that checks whether a domain or URL is blocked.
"""

import multiprocessing
from urllib.parse import urlparse


def load_blacklist(blocked_sites: list[str], blocked_url: list[str]) -> tuple[set, set]:
    """
    Loads blocked FQDNs and URLs from lists into sets for fast lookup.

    Args:
        blocked_sites (list[str]): The list of blocked FQDNs.
        blocked_url (list[str]): The list of blocked URLs.

    Returns:
        tuple[set, set]: A tuple of sets of blocked domains and URLs.
    """
    return set(blocked_sites), set(blocked_url)


def filter_process(
    queue: multiprocessing.Queue,
    result_queue: multiprocessing.Queue,
    blocked_sites: list[str],
    blocked_url: list[str],
) -> None:
    """
    Process that listens for requests and checks if the domain/URL should be blocked.

    Args:
        queue (multiprocessing.Queue): A queue to receive URL/domain for checking.
        result_queue (multiprocessing.Queue): A queue to send back the result of
                the filtering (blocked or allowed).
        blocked_sites (list[str]): The list of blocked FQDNs.
        blocked_url (list[str]): The list of blocked URLs.
    """
    blocked_sites_set, blocked_url_set = load_blacklist(blocked_sites, blocked_url)

    while True:
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

            if "*" in blocked_sites_set or any(
                server_host.startswith(blocked_host) for blocked_host in blocked_sites_set
            ):
                result_queue.put((server_host, "Blocked"))
            elif any(full_url.startswith(blocked_url) for blocked_url in blocked_url_set):
                result_queue.put((full_url, "Blocked"))
            else:
                result_queue.put((server_host, "Allowed"))

        except KeyboardInterrupt:
            break

"""
pyproxy.handlers.http.py

This module defines the HttpHandler class used by the proxy server to process
HTTP client connections. It handles request forwarding, blocking, and custom headers.
"""

import socket
import os
import threading
from urllib.parse import urlparse

from pyproxy.utils.http_req import extract_headers


class HttpHandler:
    """
    HttpHandler manages client HTTP connections for a proxy server,
    handling request forwarding, filtering, blocking, and custom header modification
    based on configuration settings.
    """

    def __init__(
        self,
        html_403,
        logger_config,
        filter_config,
        filter_queue,
        filter_result_queue,
        shortcuts_queue,
        shortcuts_result_queue,
        custom_header_queue,
        custom_header_result_queue,
        console_logger,
        shortcuts,
        custom_header,
        active_connections,
        proxy_config,
    ):
        self.html_403 = html_403
        self.logger_config = logger_config
        self.filter_config = filter_config
        self.filter_queue = filter_queue
        self.filter_result_queue = filter_result_queue
        self.shortcuts_queue = shortcuts_queue
        self.shortcuts_result_queue = shortcuts_result_queue
        self.custom_header_queue = custom_header_queue
        self.custom_header_result_queue = custom_header_result_queue
        self.console_logger = console_logger
        self.config_shortcuts = shortcuts
        self.config_custom_header = custom_header
        self.proxy_config = proxy_config
        self.active_connections = active_connections

    def _get_modified_headers(self, url, request_text):
        """
        Extract headers from a request
        """
        headers = extract_headers(request_text)
        self.custom_header_queue.put(url)
        try:
            new_headers = self.custom_header_result_queue.get(timeout=5)
            headers.update(new_headers)
        except Exception:
            self.console_logger.warning("Timeout while getting custom headers for %s", url)
        return headers

    def _rebuild_http_request(self, request_line, headers, body=""):
        """
        Reconstructs an HTTP request with the new headers.
        """
        header_lines = [f"{key}: {value}" for key, value in headers.items()]
        reconstructed_headers = "\r\n".join(header_lines)
        return f"{request_line}\r\n{reconstructed_headers}\r\n\r\n{body}".encode()

    def _apply_shortcut(self, url: str) -> str | None:
        """
        Checks if a shortcut is defined for the given domain.
        """
        if self.config_shortcuts and os.path.isfile(self.config_shortcuts):
            parsed_url = urlparse(url)
            domain = parsed_url.hostname
            self.shortcuts_queue.put(domain)
            try:
                return self.shortcuts_result_queue.get(timeout=5)
            except Exception:
                self.console_logger.warning("Timeout while getting shortcut for %s", url)
        return None

    def _is_blocked(self, url: str) -> bool:
        """
        Checks if a URL is blocked by the configuration filter.
        """
        if not self.filter_config.no_filter:
            self.filter_queue.put(url)
            try:
                result = self.filter_result_queue.get(timeout=5)
                return result[1] == "Blocked"
            except Exception:
                self.console_logger.warning("Timeout while filtering %s", url)
        return False

    def _send_403(self, client_socket, url, first_line):
        """
        Sends an HTTP 403 Forbidden response to the client.
        """
        if not self.logger_config.no_logging_block:
            method, domain_port, protocol = first_line.split(" ")
            domain, port = domain_port.split(":")
            self.logger_config.block_logger.info(
                "",
                extra={
                    "ip_src": client_socket.getpeername()[0],
                    "url": url,
                    "method": method,
                    "domain": domain,
                    "port": port,
                    "protocol": protocol,
                },
            )
        with open(self.html_403, "r", encoding="utf-8") as f:
            custom_403_page = f.read()
        response = (
            f"HTTP/1.1 403 Forbidden\r\n"
            f"Content-Length: {len(custom_403_page)}\r\n"
            f"\r\n"
            f"{custom_403_page}"
        )
        client_socket.sendall(response.encode())
        client_socket.close()
        self.active_connections.pop(threading.get_ident(), None)

    def handle_http_request(self, client_socket, request):
        """
        Processes an HTTP request, checks for URL filtering, applies shortcuts,
        and forwards the request to the target server if not blocked.

        Args:
            client_socket (socket): The socket object for the client connection.
            request (bytes): The raw HTTP request sent by the client.
        """
        first_line = request.decode(errors="ignore").split("\n")[0]
        url = first_line.split(" ")[1]

        if self.config_shortcuts and os.path.isfile(self.config_shortcuts):
            shortcut_url = self._apply_shortcut(url)
            if shortcut_url:
                response = (
                    f"HTTP/1.1 302 Found\r\nLocation: {shortcut_url}\r\nContent-Length: 0\r\n\r\n"
                )

                client_socket.sendall(response.encode())
                client_socket.close()
                self.active_connections.pop(threading.get_ident(), None)
                return

        if self._is_blocked(url):
            self._send_403(client_socket, url, first_line)
            return

        if self.config_custom_header and os.path.isfile(self.config_custom_header):
            request_text = request.decode(errors="ignore")
            request_lines = request_text.split("\r\n")
            headers = self._get_modified_headers(url, request_text)
            request_line = request_lines[0]
            body = request_text.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in request_text else ""
            modified_request = self._rebuild_http_request(request_line, headers, body)

            self.forward_request_to_server(client_socket, modified_request, url, first_line)

        else:
            self.forward_request_to_server(client_socket, request, url, first_line)

    def forward_request_to_server(self, client_socket, request, url, first_line):
        """
        Forwards the HTTP request to the target server and sends the response back to the client.

        Args:
            client_socket (socket): The socket object for the client connection.
            request (bytes): The raw HTTP request sent by the client.
            url (str): The target URL from the HTTP request.
            first_line (str): The first line of the HTTP request (e.g., "GET / HTTP/1.1").
        """
        if self.proxy_config.enable:
            server_host, server_port = self.proxy_config.host, self.proxy_config.port
        else:
            parsed_url = urlparse(url)
            server_host = parsed_url.hostname
            server_port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

        try:
            ip_address = socket.gethostbyname(server_host)
        except socket.gaierror:
            ip_address = server_host

        thread_id = threading.get_ident()

        if thread_id in self.active_connections:
            self.active_connections[thread_id].update(
                {
                    "target_ip": ip_address,
                    "target_domain": server_host,
                    "target_port": server_port,
                    "bytes_sent": 0,
                    "bytes_received": 0,
                }
            )

        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((server_host, server_port))
            server_socket.sendall(request)
            server_socket.settimeout(5)
            self.active_connections[thread_id]["bytes_sent"] += len(request)

            while True:
                try:
                    response = server_socket.recv(4096)
                    if response:
                        client_socket.send(response)
                        self.active_connections[thread_id]["bytes_received"] += len(response)
                    else:
                        break
                except socket.timeout:
                    break
        except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
            self.console_logger.error("Error connecting to the server %s : %s", server_host, e)
            response = (
                f"HTTP/1.1 502 Bad Gateway\r\n"
                f"Content-Length: {len('Bad Gateway')} \r\n"
                "\r\n"
                f"Bad Gateway"
            )
            client_socket.sendall(response.encode())
            client_socket.close()
            self.active_connections.pop(thread_id, None)
        finally:
            if not self.logger_config.no_logging_access:
                method, url, protocol = first_line.split(" ")

                conn_data = self.active_connections.get(thread_id, {})
                self.logger_config.access_logger.info(
                    "",
                    extra={
                        "ip_src": client_socket.getpeername()[0],
                        "url": f"http://{server_host}",
                        "method": method,
                        "domain": parsed_url.hostname,
                        "port": parsed_url.port,
                        "protocol": protocol,
                        "bytes_sent": conn_data.get("bytes_sent", 0),
                        "bytes_received": conn_data.get("bytes_received", 0),
                    },
                )
            client_socket.close()
            server_socket.close()
            self.active_connections.pop(thread_id, None)

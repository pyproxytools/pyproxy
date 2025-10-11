"""
pyproxy.handlers.https.py

This class handles HTTPS CONNECT requests, applies filtering rules, supports SSL inspection,
generates certificates dynamically, and logs access and blocked attempts. It can also
relay raw data when SSL inspection is disabled.
"""

import socket
import select
import os
import ssl
import threading

from pyproxy.utils.crypto import generate_certificate


class HttpsHandler:
    """
    Handles HTTPS client connections for a proxy server.

    Supports SSL interception, filtering of targets, and custom logging. This handler
    processes HTTPS `CONNECT` requests and either tunnels them directly to the destination
    or performs SSL interception for inspection and filtering.
    """

    def __init__(
        self,
        html_403,
        logger_config,
        filter_config,
        ssl_config,
        filter_queue,
        filter_result_queue,
        shortcuts_queue,
        shortcuts_result_queue,
        cancel_inspect_queue,
        cancel_inspect_result_queue,
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
        self.ssl_config = ssl_config
        self.filter_queue = filter_queue
        self.filter_result_queue = filter_result_queue
        self.shortcuts_queue = shortcuts_queue
        self.shortcuts_result_queue = shortcuts_result_queue
        self.cancel_inspect_queue = cancel_inspect_queue
        self.cancel_inspect_result_queue = cancel_inspect_result_queue
        self.custom_header_queue = custom_header_queue
        self.custom_header_result_queue = custom_header_result_queue
        self.console_logger = console_logger
        self.config_shortcuts = shortcuts
        self.config_custom_header = custom_header
        self.proxy_config = proxy_config
        self.active_connections = active_connections

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

    def _should_skip_inspection(self, server_host: str) -> bool:
        """
        Determine if SSL inspection should be skipped for the given host.
        """
        if (
            self.ssl_config.ssl_inspect
            and self.ssl_config.cancel_inspect
            and os.path.isfile(self.ssl_config.cancel_inspect)
        ):
            self.cancel_inspect_queue.put(server_host)
            return self.cancel_inspect_result_queue.get(timeout=5)
        return False

    def _establish_server_connection(self, server_host, server_port):
        """
        Create and return a socket connected to the target server.
        """
        if self.proxy_config.enable:
            next_proxy_socket = socket.create_connection(
                (self.proxy_config.host, self.proxy_config.port)
            )
            connect_command = (
                f"CONNECT {server_host}:{server_port} HTTP/1.1\r\n"
                f"Host: {server_host}:{server_port}\r\n\r\n"
            )
            next_proxy_socket.sendall(connect_command.encode())

            response = b""
            while b"\r\n\r\n" not in response:
                chunk = next_proxy_socket.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection to next proxy failed")
                response += chunk

            if b"200 Connection Established" not in response:
                raise ConnectionRefusedError("Next proxy refused CONNECT")

            return next_proxy_socket
        else:
            return socket.create_connection((server_host, server_port))

    def _wrap_client_socket_with_ssl(self, client_socket, cert_path, key_path):
        """
        Wrap the client socket with an SSL context for interception.
        """
        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        client_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        client_context.options |= (
            ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        )
        client_context.load_verify_locations(self.ssl_config.inspect_ca_cert)

        ssl_client_socket = client_context.wrap_socket(
            client_socket, server_side=True, do_handshake_on_connect=False
        )
        try:
            ssl_client_socket.do_handshake()
        except ssl.SSLError as e:
            if "TLSV1_ALERT_UNKNOWN_CA" in str(e):
                self.console_logger.debug("Client refused cert: %s", e)
                ssl_client_socket.close()
                raise ConnectionAbortedError("Client refused SSL cert")
            else:
                raise
        return ssl_client_socket

    def _wrap_server_socket_with_ssl(self, server_socket, server_host):
        """
        Wrap the server socket with an SSL context to enable encrypted communication.
        """
        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if self.proxy_config.enable:
            server_context.check_hostname = False
            server_context.verify_mode = ssl.CERT_NONE
        else:
            server_context.load_default_certs()

        ssl_server_socket = server_context.wrap_socket(
            server_socket,
            server_hostname=server_host,
            do_handshake_on_connect=True,
        )
        return ssl_server_socket

    def _process_first_ssl_request(self, ssl_client_socket, server_host, first_line):
        """
        Reads and processes the first SSL client request, extracts the method and full URL.
        """
        try:
            first_request = ssl_client_socket.recv(4096).decode(errors="ignore")
            if not first_request:
                raise ConnectionError("Empty request received")

            request_line = first_request.split("\r\n")[0]
            method, path, _ = request_line.split(" ")

            full_url = f"https://{server_host}{path}"

            if self._is_blocked(f"{server_host}{path}"):
                return None, full_url, True

            if not self.logger_config.no_logging_access:
                method, domain_port, protocol = first_line.split(" ")
                domain, port = domain_port.split(":")
                self.logger_config.access_logger.info(
                    "",
                    extra={
                        "ip_src": ssl_client_socket.getpeername()[0],
                        "url": full_url,
                        "method": method,
                        "domain": server_host,
                        "port": port,
                        "protocol": protocol,
                    },
                )

            return first_request, full_url, False
        except Exception as e:
            self.logger_config.error_logger.error(f"SSL request processing error : {e}")
            return None, None, False

    def handle_https_connection(self, client_socket, first_line):
        """
        Handles HTTPS connections by establishing a connection with the target server
        and relaying data between the client and server.

        Args:
            client_socket (socket): The socket object for the client connection.
            first_line (str): The first line of the CONNECT request from the client.
        """
        target = first_line.split(" ")[1]
        server_host, server_port = target.split(":")
        server_port = int(server_port)

        if self._is_blocked(target):
            self._send_403(client_socket, target, first_line)
            return

        not_inspect = self._should_skip_inspection(server_host)

        thread_id = threading.get_ident()
        self.active_connections[thread_id].update(
            {
                "target_domain": server_host,
                "bytes_sent": 0,
                "bytes_received": 0,
            }
        )

        if self.ssl_config.ssl_inspect and not not_inspect:
            try:
                cert_path, key_path = generate_certificate(
                    server_host,
                    self.ssl_config.inspect_certs_folder,
                    self.ssl_config.inspect_ca_cert,
                    self.ssl_config.inspect_ca_key,
                )

                client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

                ssl_client_socket = self._wrap_client_socket_with_ssl(
                    client_socket, cert_path, key_path
                )

                tls_version = ssl_client_socket.version() or "unknown"

                server_socket = self._establish_server_connection(server_host, server_port)
                ssl_server_socket = self._wrap_server_socket_with_ssl(server_socket, server_host)

                first_request, full_url, is_blocked = self._process_first_ssl_request(
                    ssl_client_socket, server_host, first_line
                )
                if is_blocked:
                    self._send_403(ssl_client_socket, target, first_line)
                    return
                if first_request is None:
                    ssl_client_socket.close()
                    return

                ssl_server_socket.sendall(first_request.encode())
                client_ip = ssl_client_socket.getpeername()[0]
                bytes_sent, bytes_received = self.transfer_data_between_sockets(
                    ssl_client_socket, ssl_server_socket
                )

                if not self.logger_config.no_logging_access:
                    method, _, protocol = first_line.split(" ")
                    self.logger_config.access_logger.info(
                        "",
                        extra={
                            "ip_src": client_ip,
                            "url": target,
                            "method": method,
                            "domain": server_host,
                            "port": server_port,
                            "protocol": protocol,
                            "bytes_sent": bytes_sent,
                            "bytes_received": bytes_received,
                            "tls_version": tls_version,
                        },
                    )

            except ConnectionAbortedError:
                self.active_connections.pop(threading.get_ident(), None)
                return
            except ssl.SSLError as e:
                self.console_logger.error("SSL error: %s", str(e))
            except socket.error as e:
                self.console_logger.error("Socket error: %s", str(e))
            finally:
                client_socket.close()
                self.active_connections.pop(threading.get_ident(), None)

        else:
            try:
                server_socket = self._establish_server_connection(server_host, server_port)
                client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

                client_ip = client_socket.getpeername()[0]
                bytes_sent, bytes_received = self.transfer_data_between_sockets(
                    client_socket, server_socket
                )

                if not self.logger_config.no_logging_access:
                    method, _, protocol = first_line.split(" ")
                    self.logger_config.access_logger.info(
                        "",
                        extra={
                            "ip_src": client_ip,
                            "url": target,
                            "method": method,
                            "domain": server_host,
                            "port": server_port,
                            "protocol": protocol,
                            "bytes_sent": bytes_sent,
                            "bytes_received": bytes_received,
                        },
                    )
            except (
                socket.timeout,
                socket.gaierror,
                ConnectionRefusedError,
                OSError,
            ) as e:
                self.console_logger.error("Error connecting to the server %s: %s", server_host, e)
                response = (
                    f"HTTP/1.1 502 Bad Gateway\r\n"
                    f"Content-Length: {len('Bad Gateway')} \r\n"
                    f"\r\n"
                    f"Bad Gateway"
                )
                client_socket.sendall(response.encode())
                client_socket.close()
            finally:
                self.active_connections.pop(thread_id, None)

    def transfer_data_between_sockets(self, client_socket, server_socket):
        """
        Transfers data between the client socket and server socket.

        Args:
            client_socket (socket): The socket object for the client connection.
            server_socket (socket): The socket object for the server connection.
        """
        sockets = [client_socket, server_socket]
        thread_id = threading.get_ident()

        if (
            thread_id in self.active_connections
            and "target_ip" not in self.active_connections[thread_id]
        ):
            try:
                target_ip, target_port = server_socket.getpeername()
                self.active_connections[thread_id]["target_ip"] = target_ip
                self.active_connections[thread_id]["target_port"] = target_port
            except OSError as e:
                self.console_logger.debug("Could not get peer name: %s", e)

        try:
            while True:
                readable, _, _ = select.select(sockets, [], [], 1)
                for sock in readable:
                    data = sock.recv(4096)
                    if len(data) == 0:
                        self.console_logger.debug("Closing connection.")
                        client_socket.close()
                        server_socket.close()
                        bytes_sent = self.active_connections[thread_id]["bytes_sent"]
                        bytes_received = self.active_connections[thread_id]["bytes_received"]
                        self.active_connections.pop(threading.get_ident(), None)
                        return bytes_sent, bytes_received
                    if sock is client_socket:
                        server_socket.sendall(data)
                        self.active_connections[thread_id]["bytes_sent"] += len(data)
                    else:
                        client_socket.sendall(data)
                        self.active_connections[thread_id]["bytes_received"] += len(data)
        except (socket.error, OSError):
            client_socket.close()
            server_socket.close()
            self.active_connections.pop(threading.get_ident(), None)

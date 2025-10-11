"""
server.py

This module defines a Python-based proxy server capable of handling both HTTP
and HTTPS requests. It forwards client requests to target servers, applies
filtering, serves custom 403 pages for blocked content, and logs access and
block events.
"""

import socket
import threading
import logging
import multiprocessing
import os
import ssl
import time
import ipaddress

from pyproxy import __slim__
from pyproxy.utils.logger import configure_file_logger, configure_console_logger
from pyproxy.handlers.client import ProxyHandlers
from pyproxy.modules.filter import filter_process
from pyproxy.modules.cancel_inspect import cancel_inspect_process

if not __slim__:
    from pyproxy.modules.shortcuts import shortcuts_process
if not __slim__:
    from pyproxy.modules.custom_header import custom_header_process
if not __slim__:
    from pyproxy.monitoring import start_flask_server


class ProxyServer:
    """
    A proxy server that forwards HTTP and HTTPS requests, blocks based on rules,
    injects headers, and logs events.
    """

    _EXCLUDE_DEBUG_KEYS = {
        "filter_proc",
        "filter_queue",
        "filter_result_queue",
        "shortcuts_proc",
        "shortcuts_queue",
        "shortcuts_result_queue",
        "cancel_inspect_proc",
        "cancel_inspect_queue",
        "cancel_inspect_result_queue",
        "custom_header_proc",
        "custom_header_queue",
        "custom_header_result_queue",
        "console_logger",
        "access_logger",
        "block_logger",
        "authorized_ips",
        "active_connections",
    }

    def __init__(
        self,
        main_config,
        logger_config,
        filter_config,
        ssl_config,
        monitoring_config,
        proxy_config,
    ):
        """
        Initialize the ProxyServer with configuration parameters.
        """
        self.host_port = (main_config.host, main_config.port)
        self.debug = main_config.debug
        self.html_403 = main_config.html_403
        self.active_connections = {}

        self.logger_config = logger_config
        self.filter_config = filter_config
        self.ssl_config = ssl_config

        # Monitoring
        self.monitoring_config = monitoring_config

        # Proxy
        self.proxy_config = proxy_config

        # Authorized IPS
        self.authorized_ips = main_config.authorized_ips
        self.allowed_subnets = None

        # Process communication queues
        self.filter_proc = None
        self.filter_queue = multiprocessing.Queue()
        self.filter_result_queue = multiprocessing.Queue()
        self.shortcuts_proc = None
        self.shortcuts_queue = multiprocessing.Queue()
        self.shortcuts_result_queue = multiprocessing.Queue()
        self.cancel_inspect_proc = None
        self.cancel_inspect_queue = multiprocessing.Queue()
        self.cancel_inspect_result_queue = multiprocessing.Queue()
        self.custom_header_proc = None
        self.custom_header_queue = multiprocessing.Queue()
        self.custom_header_result_queue = multiprocessing.Queue()

        # Logging
        self.console_logger = configure_console_logger(self.logger_config)
        if not self.logger_config.no_logging_access:
            self.logger_config.access_logger = configure_file_logger(
                self.logger_config.access_log,
                "AccessLogger",
                self.logger_config.access_log_format,
                self.logger_config.datefmt,
            )
        if not self.logger_config.no_logging_block:
            self.logger_config.block_logger = configure_file_logger(
                self.logger_config.block_log,
                "BlockLogger",
                self.logger_config.block_log_format,
                self.logger_config.datefmt,
            )

        # Configuration files
        self.config_shortcuts = main_config.shortcuts
        self.config_custom_header = main_config.custom_header

    def _initialize_processes(self):
        """
        Initializes and starts multiple processes for various tasks if their
        respective configurations and conditions are met.
        """
        if not self.filter_config.no_filter:
            self.filter_proc = multiprocessing.Process(
                target=filter_process,
                args=(
                    self.filter_queue,
                    self.filter_result_queue,
                    self.filter_config.filter_mode,
                    self.filter_config.blocked_sites,
                    self.filter_config.blocked_url,
                ),
            )
            self.filter_proc.start()
            self.console_logger.debug("[*] Starting the filter process...")

        if not __slim__ and self.config_shortcuts and os.path.isfile(self.config_shortcuts):
            self.shortcuts_proc = multiprocessing.Process(
                target=shortcuts_process,
                args=(
                    self.shortcuts_queue,
                    self.shortcuts_result_queue,
                    self.config_shortcuts,
                ),
            )
            self.shortcuts_proc.start()
            self.console_logger.debug("[*] Starting the shortcuts process...")

        if self.ssl_config.cancel_inspect and os.path.isfile(self.ssl_config.cancel_inspect):
            self.cancel_inspect_proc = multiprocessing.Process(
                target=cancel_inspect_process,
                args=(
                    self.cancel_inspect_queue,
                    self.cancel_inspect_result_queue,
                    self.ssl_config.cancel_inspect,
                ),
            )
            self.cancel_inspect_proc.start()
            self.console_logger.debug("[*] Starting the cancel inspection process...")

        if not __slim__ and self.config_custom_header and os.path.isfile(self.config_custom_header):
            self.custom_header_proc = multiprocessing.Process(
                target=custom_header_process,
                args=(
                    self.custom_header_queue,
                    self.custom_header_result_queue,
                    self.config_custom_header,
                ),
            )
            self.custom_header_proc.start()
            self.console_logger.debug("[*] Starting the custom header process...")

    def _clean_inspection_folder(self):
        """
        Delete old inspection cert/key files if they exist.
        """
        for file in os.listdir(self.ssl_config.inspect_certs_folder):
            if file.endswith((".key", ".pem")):
                file_path = os.path.join(self.ssl_config.inspect_certs_folder, file)
                try:
                    os.remove(file_path)
                except (FileNotFoundError, PermissionError, OSError) as e:
                    self.console_logger.debug("Error deleting %s: %s", file_path, e)

    def _load_authorized_ips(self):
        """
        Load authorized IPs/subnets from the file.
        """
        self.allowed_subnets = None

        if self.authorized_ips and os.path.isfile(self.authorized_ips):
            with open(self.authorized_ips, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            try:
                self.allowed_subnets = [ipaddress.ip_network(line, strict=False) for line in lines]
                self.console_logger.debug(
                    "[*] Loaded %d authorized IPs/subnets", len(self.allowed_subnets)
                )
            except ValueError as e:
                self.console_logger.error("[*] Invalid IP/subnet in %s: %s", self.authorized_ips, e)
                self.allowed_subnets = None

    def _validate_ssl_inspection_files(self):
        """
        Validate SSL Inspection cert/key.
        """
        required_files = [
            self.ssl_config.inspect_ca_cert,
            self.ssl_config.inspect_ca_key,
        ]

        for file_path in required_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"SSL file not found: {file_path}")
            if not os.path.isfile(file_path):
                raise ValueError(f"Invalid SSL file: {file_path} is not a file")

        try:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(
                certfile=self.ssl_config.inspect_ca_cert,
                keyfile=self.ssl_config.inspect_ca_key,
            )
        except ssl.SSLError as e:
            raise ssl.SSLError(f"SSL certificate/key validation failed: {e}")

    def _start_monitoring_server(self):
        """
        Start monitoring flask server.
        """
        flask_thread = threading.Thread(
            target=start_flask_server,
            args=(
                self,
                self.monitoring_config.flask_port,
                self.monitoring_config.flask_pass,
                self.debug,
            ),
            daemon=True,
        )
        flask_thread.start()

    def start(self):
        """
        Start the proxy server and listen for incoming client connections.
        Logs configuration if debug is enabled.
        """
        self.console_logger.setLevel(logging.DEBUG if self.debug else logging.INFO)

        if self.debug:
            self.console_logger.debug("Configuration used:")
            for key in sorted(vars(self)):
                if key not in self._EXCLUDE_DEBUG_KEYS:
                    self.console_logger.debug("[*] %s = %s", key, getattr(self, key))

        if self.ssl_config.ssl_inspect:
            os.makedirs(self.ssl_config.inspect_certs_folder, exist_ok=True)
            self._validate_ssl_inspection_files()
            self._clean_inspection_folder()

        if self.filter_config.filter_mode == "local":
            for file in [
                self.filter_config.blocked_sites,
                self.filter_config.blocked_url,
            ]:
                if not os.path.exists(file):
                    with open(file, "w", encoding="utf-8"):
                        pass

        self._initialize_processes()
        self._load_authorized_ips()

        if not __slim__:
            self._start_monitoring_server()
            self.console_logger.debug("[*] Starting the monitoring process...")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.host_port)
        server.listen(10)
        self.console_logger.info("Proxy server started on %s...", self.host_port)

        try:
            while True:
                client_socket, addr = server.accept()
                client_ip, client_port = addr

                if self.allowed_subnets:
                    ip_obj = ipaddress.ip_address(client_ip)
                    if not any(ip_obj in net for net in self.allowed_subnets):
                        self.console_logger.debug("Unauthorized IP blocked: %s", client_ip)
                        with open(self.html_403, "r", encoding="utf-8") as f:
                            custom_403_page = f.read()
                        response = (
                            "HTTP/1.1 403 Forbidden\r\n"
                            "Content-Type: text/html; charset=utf-8\r\n"
                            "Connection: close\r\n\r\n"
                            f"{custom_403_page}"
                        )

                        try:
                            client_socket.sendall(response.encode("utf-8"))
                        except Exception as e:
                            self.console_logger.error("Error sending 403 response: %s", e)
                        finally:
                            client_socket.close()
                        continue

                self.console_logger.debug("Connection from %s", addr)
                client = ProxyHandlers(
                    html_403=self.html_403,
                    logger_config=self.logger_config,
                    filter_config=self.filter_config,
                    ssl_config=self.ssl_config,
                    filter_queue=self.filter_queue,
                    filter_result_queue=self.filter_result_queue,
                    shortcuts_queue=self.shortcuts_queue,
                    shortcuts_result_queue=self.shortcuts_result_queue,
                    cancel_inspect_queue=self.cancel_inspect_queue,
                    cancel_inspect_result_queue=self.cancel_inspect_result_queue,
                    custom_header_queue=self.custom_header_queue,
                    custom_header_result_queue=self.custom_header_result_queue,
                    console_logger=self.console_logger,
                    shortcuts=self.config_shortcuts,
                    custom_header=self.config_custom_header,
                    proxy_config=self.proxy_config,
                    active_connections=self.active_connections,
                )
                client_handler = threading.Thread(
                    target=client.handle_client, args=(client_socket,), daemon=True
                )
                client_handler.start()
                self.active_connections[client_handler.ident] = {
                    "client_ip": client_ip,
                    "client_port": client_port,
                    "start_time": time.time(),
                    "bytes_sent": 0,
                    "bytes_received": 0,
                    "thread_name": client_handler.name,
                }
        except KeyboardInterrupt:
            self.console_logger.info("Proxy interrupted, shutting down.")

"""
pyproxy.utils.config.py

This module defines configuration classes used by the HTTP/HTTPS proxy.
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ProxyConfigMain:
    """
    Handles main configuration for the proxy.
    """

    host: str
    port: int
    debug: bool
    html_403: str
    shortcuts: dict[str, str]
    custom_header: dict[str, dict[str, str]]
    authorized_ips: list[str]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ProxyConfigProxy:
    """
    Handles proxy configuration for the proxy.
    """

    enable: bool
    host: str
    port: int

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ProxyConfigMonitoring:
    """
    Handles monitoring configuration for the proxy.
    """

    flask_port: int
    flask_pass: str

    def to_dict(self):
        return asdict(self)


@dataclass()
class ProxyConfigLogger:
    """
    Handles logging configuration for the proxy.
    """

    access_log: str
    block_log: str
    no_logging_access: bool
    no_logging_block: bool
    console_format: str
    access_log_format: str
    block_log_format: str
    datefmt: str

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ProxyConfigFilter:
    """
    Manages filtering configuration for the proxy.
    """

    no_filter: bool
    filter_mode: str
    blocked_sites: list[str]
    blocked_url: list[str]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ProxyConfigSSL:
    """
    Handles SSL/TLS inspection configuration.
    """

    ssl_inspect: bool
    inspect_ca_cert: str
    inspect_ca_key: str
    inspect_certs_folder: str
    cancel_inspect: list[str]

    def to_dict(self):
        return asdict(self)

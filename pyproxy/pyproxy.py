"""
This script implements a lightweight and fast Python-based proxy server.
It listens for client requests, filters URLs based on a list, and allows or blocks access
to those URLs. The proxy can handle both HTTP and HTTPS requests, and logs access and block events.
"""

from .server import ProxyServer
from .utils.args import parse_args, load_config, get_config_value, str_to_bool
from .utils.config import (
    ProxyConfigLogger,
    ProxyConfigFilter,
    ProxyConfigSSL,
    ProxyConfigMonitoring,
    ProxyConfigProxy,
    ProxyConfigMain,
)


def main():
    """
    Main entry point of the proxy server. It parses command-line arguments,
    loads the configuration file, retrieves configuration values, and starts the proxy server.
    """
    args = parse_args()
    config = load_config(args.config_file)

    main_config = ProxyConfigMain(
        host=get_config_value(args, config, "host", "Server", "0.0.0.0"),  # noqa: S104
        port=int(get_config_value(args, config, "port", "Server", 8080)),
        debug=str_to_bool(get_config_value(args, config, "debug", "Logging", False)),
        html_403=get_config_value(args, config, "html_403", "Files", "assets/403.html"),
        shortcuts=get_config_value(args, config, "shortcuts", "Options", "config/shortcuts.txt"),
        custom_header=get_config_value(
            args, config, "custom_header", "Options", "config/custom_header.json"
        ),
        authorized_ips=get_config_value(
            args, config, "authorized_ips", "Options", "config/authorized_ips.txt"
        ),
    )

    monitoring_config = ProxyConfigMonitoring(
        flask_port=get_config_value(args, config, "flask_port", "Monitoring", 5000),
        flask_pass=get_config_value(args, config, "flask_pass", "Monitoring", "password"),
    )

    proxy_config = ProxyConfigProxy(
        enable=str_to_bool(get_config_value(args, config, "proxy_enable", "Proxy", False)),
        host=get_config_value(args, config, "proxy_host", "Proxy", "127.0.0.1"),
        port=get_config_value(args, config, "proxy_port", "Proxy", 8081),
    )

    console_format = config.get("Logging", "console_format", fallback=None)
    access_log_format = config.get("Logging", "access_log_format", fallback=None)
    block_log_format = config.get("Logging", "block_log_format", fallback=None)
    datefmt = config.get("Logging", "datefmt", fallback=None)

    logger_config = ProxyConfigLogger(
        access_log=get_config_value(args, config, "access_log", "Logging", "logs/access.log"),
        block_log=get_config_value(args, config, "block_log", "Logging", "logs/block.log"),
        no_logging_access=str_to_bool(
            get_config_value(args, config, "no_logging_access", "Logging", False)
        ),
        no_logging_block=str_to_bool(
            get_config_value(args, config, "no_logging_block", "Logging", False)
        ),
        console_format=(
            console_format
            if console_format is not None
            else (
                "date=%(asctime)s "
                "level=%(levelname)s "
                "file=%(filename)s "
                "function=%(funcName)s "
                "message=%(message)s"
            )
        ),
        access_log_format=(
            access_log_format
            if access_log_format is not None
            else (
                "date=%(asctime)s "
                "ip_src=%(ip_src)s "
                "url=%(url)s "
                "method=%(method)s "
                "domain=%(domain)s "
                "port=%(port)s "
                "protocol=%(protocol)s "
                "bytes_sent=%(bytes_sent)s "
                "bytes_received=%(bytes_received)s "
                "tls_version=%(tls_version)s"
            )
        ),
        block_log_format=(
            block_log_format
            if block_log_format is not None
            else (
                "date=%(asctime)s "
                "ip_src=%(ip_src)s "
                "url=%(url)s "
                "method=%(method)s "
                "domain=%(domain)s "
                "port=%(port)s "
                "protocol=%(protocol)s"
            )
        ),
        datefmt=datefmt if datefmt is not None else "%Y-%m-%d %H:%M:%S",
    )

    filter_config = ProxyConfigFilter(
        no_filter=str_to_bool(get_config_value(args, config, "no_filter", "Filtering", False)),
        filter_mode=get_config_value(args, config, "filter_mode", "Filtering", "local"),
        blocked_sites=get_config_value(
            args, config, "blocked_sites", "Filtering", "config/blocked_sites.txt"
        ),
        blocked_url=get_config_value(
            args, config, "blocked_url", "Filtering", "config/blocked_url.txt"
        ),
    )

    ssl_config = ProxyConfigSSL(
        ssl_inspect=str_to_bool(get_config_value(args, config, "ssl_inspect", "Security", False)),
        inspect_ca_cert=get_config_value(
            args, config, "inspect_ca_cert", "Security", "certs/ca/cert.pem"
        ),
        inspect_ca_key=get_config_value(
            args, config, "inspect_ca_key", "Security", "certs/ca/key.pem"
        ),
        inspect_certs_folder=get_config_value(
            args, config, "inspect_certs_folder", "Security", "certs/"
        ),
        cancel_inspect=get_config_value(
            args, config, "cancel_inspect", "Security", "config/cancel_inspect.txt"
        ),
    )

    proxy = ProxyServer(
        main_config=main_config,
        logger_config=logger_config,
        filter_config=filter_config,
        ssl_config=ssl_config,
        monitoring_config=monitoring_config,
        proxy_config=proxy_config,
    )

    proxy.start()

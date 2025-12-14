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
        host=get_config_value(args, config, "host", "server", "0.0.0.0"),  # noqa: S104
        port=int(get_config_value(args, config, "port", "server", 8080)),
        debug=str_to_bool(get_config_value(args, config, "debug", "logging", False)),
        html_403=get_config_value(args, config, "html_403", "files", "assets/403.html"),
        shortcuts=config.get("options", {}).get("shortcuts", {}),
        custom_header=config.get("options", {}).get("custom_header", {}),
        authorized_ips=config.get("options", {}).get("authorized_ips", []),
    )

    monitoring_config = ProxyConfigMonitoring(
        flask_port=get_config_value(args, config, "flask_port", "monitoring", 5000),
        flask_pass=get_config_value(args, config, "flask_pass", "monitoring", "password"),
    )

    proxy_config = ProxyConfigProxy(
        enable=str_to_bool(get_config_value(args, config, "proxy_enable", "proxy", False)),
        host=get_config_value(args, config, "proxy_host", "proxy", "127.0.0.1"),
        port=get_config_value(args, config, "proxy_port", "proxy", 8081),
    )

    console_format = config.get("logging", {}).get("console_format")
    access_log_format = config.get("logging", {}).get("access_log_format")
    block_log_format = config.get("logging", {}).get("block_log_format")
    datefmt = config.get("logging", {}).get("datefmt")

    logger_config = ProxyConfigLogger(
        access_log=get_config_value(args, config, "access_log", "logging", "logs/access.log"),
        block_log=get_config_value(args, config, "block_log", "logging", "logs/block.log"),
        no_logging_access=str_to_bool(
            get_config_value(args, config, "no_logging_access", "logging", False)
        ),
        no_logging_block=str_to_bool(
            get_config_value(args, config, "no_logging_block", "logging", False)
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
        no_filter=str_to_bool(get_config_value(args, config, "no_filter", "filtering", False)),
        filter_mode=get_config_value(args, config, "filter_mode", "filtering", "local"),
        blocked_sites=config.get("filtering", {}).get("blocked_sites", []),
        blocked_url=config.get("filtering", {}).get("blocked_url", []),
    )

    ssl_config = ProxyConfigSSL(
        ssl_inspect=str_to_bool(get_config_value(args, config, "ssl_inspect", "security", False)),
        inspect_ca_cert=get_config_value(
            args, config, "inspect_ca_cert", "security", "certs/ca/cert.pem"
        ),
        inspect_ca_key=get_config_value(
            args, config, "inspect_ca_key", "security", "certs/ca/key.pem"
        ),
        inspect_certs_folder=get_config_value(
            args, config, "inspect_certs_folder", "security", "certs/"
        ),
        cancel_inspect=config.get("security", {}).get("cancel_inspect", []),
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

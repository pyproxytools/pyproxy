"""
pyproxy.utils.args.py

This module allows you to read the program configuration file and return the values.
"""

import configparser
import argparse
import os
from rich_argparse import MetavarTypeRichHelpFormatter
from pyproxy import __version__


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments and returns the parsed arguments as an object.

    Args:
        None

    Returns:
        argparse.Namespace: The object containing parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Lightweight and fast python web proxy",
        formatter_class=MetavarTypeRichHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=__version__, help="Show version"
    )  # noqa: E501
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-H", "--host", type=str, help="IP address to listen on")
    parser.add_argument("-P", "--port", type=int, help="Port to listen on")
    parser.add_argument(
        "-f",
        "--config-file",
        type=str,
        default="./config.ini",
        help="Path to config.ini file",
    )  # noqa: E501
    parser.add_argument("--access-log", type=str, help="Path to the access log file")
    parser.add_argument("--block-log", type=str, help="Path to the block log file")
    parser.add_argument("--html-403", type=str, help="Path to the custom 403 Forbidden HTML page")
    parser.add_argument("--no-filter", action="store_true", help="Disable URL and domain filtering")
    parser.add_argument(
        "--filter-mode", type=str, choices=["local", "http"], help="Filter list mode"
    )  # noqa: E501
    parser.add_argument(
        "--blocked-sites",
        type=str,
        help="Path to the text file containing the list of sites to block",
    )  # noqa: E501
    parser.add_argument(
        "--blocked-url",
        type=str,
        help="Path to the text file containing the list of URLs to block",
    )  # noqa: E501
    parser.add_argument(
        "--shortcuts",
        type=str,
        help="Path to the text file containing the list of shortcuts",
    )  # noqa: E501
    parser.add_argument(
        "--custom-header",
        type=str,
        help="Path to the json file containing the list of custom headers",
    )  # noqa: E501
    parser.add_argument(
        "--authorized-ips",
        type=str,
        help="Path to the txt file containing the list of authorized ips",
    )  # noqa: E501
    parser.add_argument("--no-logging-access", action="store_true", help="Disable access logging")
    parser.add_argument("--no-logging-block", action="store_true", help="Disable block logging")
    parser.add_argument("--ssl-inspect", action="store_true", help="Enable SSL inspection")
    parser.add_argument("--inspect-ca-cert", type=str, help="Path to the CA certificate")
    parser.add_argument("--inspect-ca-key", type=str, help="Path to the CA key")
    parser.add_argument(
        "--inspect-certs-folder",
        type=str,
        help="Path to the generated certificates folder",
    )  # noqa: E501
    parser.add_argument(
        "--cancel-inspect",
        type=str,
        help="Path to the text file containing the list of URLs without ssl inspection",
    )  # noqa: E501
    parser.add_argument("--flask-port", type=int, help="Port to listen on for monitoring interface")
    parser.add_argument("--flask-pass", type=int, help="Default password to Flask interface")
    parser.add_argument("--proxy-enable", action="store_true", help="Enable proxy after PyProxy")
    parser.add_argument("--proxy-host", type=str, help="Proxy IP to use after PyProxy")
    parser.add_argument("--proxy-port", type=int, help="Proxy Port to use after PyProxy")

    return parser.parse_args()


def load_config(config_path: str) -> configparser.ConfigParser:
    """
    Loads the configuration file and returns the parsed config object.

    Args:
        config_path (str): The path to the configuration file to load.

    Returns:
        configparser.ConfigParser: The parsed configuration object.
    """
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path)
    return config


def get_config_value(
    args: argparse.Namespace,
    config: configparser.ConfigParser,
    arg_name: str,
    section: str,
    fallback_value: str,
) -> str:
    """
    Retrieves the configuration value, either from the command-line
                        arguments or from the config file.

    Args:
        args (argparse.Namespace): The parsed command-line arguments object.
        config (configparser.ConfigParser): The parsed configuration object.
        arg_name (str): The name of the command-line argument.
        section (str): The section in the config file where the value is located.
        fallback_value (str): The fallback value to return if neither
                        argument nor config has a value.

    Returns:
        str: The final value, either from command-line arguments, config file, or fallback.
    """
    arg_value = getattr(args, arg_name, None)
    if arg_value:
        return arg_value

    env_var_name = f"PYPROXY_{arg_name.upper().replace('-', '_')}"
    env_value = os.getenv(env_var_name)
    if env_value:
        return env_value

    return config.get(section, arg_name, fallback=fallback_value)


def str_to_bool(value: str) -> bool:
    """
    Converts a string representation of truth to a boolean value.

    Args:
        value (str): The value to convert (e.g., "true", "1", "yes").

    Returns:
        bool: True if the string represents a true value, False otherwise.
    """
    return str(value).lower() in ("yes", "true", "t", "1")

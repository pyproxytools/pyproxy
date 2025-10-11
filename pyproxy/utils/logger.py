"""
pyproxy.utils.logger.py

This module contains functions to configure and return loggers for both console and file output.
"""

import logging
import os
import colorlog


class SafeFormatter(logging.Formatter):
    def format(self, record):
        if self._fmt:
            for key in self._fmt.split("%("):
                if ")" in key:
                    var = key.split(")")[0]
                    if not hasattr(record, var):
                        setattr(record, var, "")
                    else:
                        val = getattr(record, var)
                        if isinstance(val, str):
                            setattr(record, var, val.replace("\n", "").replace("\r", ""))
        return super().format(record)


def configure_console_logger(logger_config) -> logging.Logger:
    """
    Configures and returns a logger that outputs log messages to the console.

    Returns:
        logging.Logger: A logger instance that writes logs to the console.
    """
    console_logger = logging.getLogger("ConsoleLogger")
    console_logger.setLevel(logging.INFO)

    if "%(log_color)s" not in logger_config.console_format:
        fmt = "%(log_color)s" + logger_config.console_format
    else:
        fmt = logger_config.console_format

    formatter = colorlog.ColoredFormatter(
        fmt,
        datefmt=logger_config.datefmt,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_logger.addHandler(console_handler)
    return console_logger


def configure_file_logger(
    log_path: str, name: str, log_format: str, datefmt: str
) -> logging.Logger:
    """
    Configures and returns a logger that writes log messages to a specified file.

    Args:
        log_path (str): The path where the log file will be created or appended to.
        name (str): Logger's name.
        log_format (str): The format string for log messages
                    (e.g., with fields like %(ip_src)s, %(method)s).
        datefmt (str): The format string for timestamps (e.g., "%d/%m/%Y %H:%M:%S").

    Returns:
        logging.Logger: A logger instance that writes to the specified log file.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    file_logger = logging.getLogger(name)
    file_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(SafeFormatter(log_format, datefmt=datefmt))
    file_logger.addHandler(file_handler)
    return file_logger

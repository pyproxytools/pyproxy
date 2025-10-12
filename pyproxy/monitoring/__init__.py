"""
pyproxy.monitoring.__init__.py

Provides a monitoring system for the ProxyServer, exposing information about
processes, threads, active connections, and subprocesses. Implements an HTTP
server using Flask to provide monitoring endpoints.
"""

import logging
from flask import Flask, request
from flask_babel import Babel
from .monitor import ProxyMonitor
from .auth import create_basic_auth
from .routes import register_routes


def start_flask_server(proxy_server, flask_port, flask_pass, debug) -> None:
    """
    Launches a Flask HTTP server to monitor the ProxyServer.

    The server exposes endpoints that provide status information about
    the proxy server, including process details, thread information,
    subprocess statuses, and active connections.

    Args:
        proxy_server (ProxyServer): The ProxyServer instance to monitor.
        flask_port (int): The port number on which the Flask server will listen.
        flask_pass (str): The password used for basic HTTP authentication.
        debug (bool): Flag to enable or disable Flask debug mode.
    """
    auth = create_basic_auth(flask_pass)

    app = Flask(__name__, static_folder="static")
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    app.config["BABEL_SUPPORTED_LOCALES"] = ["fr", "en"]
    app.config["BABEL_DEFAULT_TIMEZONE"] = "Europe/London"

    def select_locale():
        lang = request.args.get("lang")
        if lang in app.config["BABEL_SUPPORTED_LOCALES"]:
            return lang
        return request.accept_languages.best_match(app.config["BABEL_SUPPORTED_LOCALES"])

    Babel(app, locale_selector=select_locale)

    @app.context_processor
    def inject_globals():
        from flask_babel import get_locale

        return {"get_locale": get_locale}

    if not debug:
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

    register_routes(app, auth, proxy_server, ProxyMonitor)
    app.run(host="0.0.0.0", port=flask_port)  # noqa: S104

"""
pyproxy.monitoring.routes.py

Defines and registers monitoring-related routes for the Flask application,
including endpoints for system information, configuration, and a secured
HTML-based index page.
"""

from flask import jsonify, render_template, request
from flask_babel import _


def register_routes(app, auth, proxy_server, ProxyMonitor):
    """
    Registers the monitoring routes to the Flask app, secured with HTTP Basic Auth.

    Args:
        app (Flask): The Flask application instance.
        auth (HTTPBasicAuth): The HTTP Basic Auth instance used to secure routes.
        proxy_server (ProxyServer): The running ProxyServer instance to monitor.
        ProxyMonitor (class): The monitoring class used to gather runtime information.
    """

    @app.route("/")
    @auth.login_required
    def index():
        """
        Serves the main index HTML page for the monitoring dashboard.

        Returns:
            Response: Rendered HTML page.
        """
        translations = {
            "Next refresh in:": _("Next refresh in:"),
            "Loading...": _("Loading..."),
            "Main Process": _("Main Process"),
            "Subprocesses": _("Subprocesses"),
            "Status": _("Status"),
            "Configuration": _("Configuration"),
            "Active Connections": _("Active Connections"),
            "Search client or target...": _("Search client or target..."),
            "Blocked sites": _("Blocked sites"),
            "Blocked URLs": _("Blocked URLs"),
            "Add": _("Add"),
            "Add a domain or URL to block": _("Add a domain or URL to block"),
            "Domain": _("Domain"),
            "URL": _("URL"),
            "Value :": _("Value :"),
            "Filtering": _("Filtering"),
            "No active connections.": _("No active connections."),
            "No blocked sites.": _("No blocked sites."),
            "No URLs blocked.": _("No URLs blocked."),
            "Error while deleting :": _("Error while deleting :"),
            "Error adding :": _("Error adding :"),
            "Please enter a value to block.": _("Please enter a value to block."),
            "Network error": _("Network error"),
            "Error loading data:": _("Error loading data:"),
            "Name:": _("Name:"),
            "PID:": _("PID:"),
            "Status:": _("Status:"),
            "Start Time:": _("Start Time:"),
            "Client": _("Client"),
            "Target": _("Target"),
            "Sent": _("Sent"),
            "Received": _("Received"),
            "bytes": _("bytes"),
            "Port:": _("Port:"),
            "Flask Port:": _("Flask Port:"),
            "HTML 403:": _("HTML 403:"),
            "Filter Configuration": _("Filter Configuration"),
            "Blocked Sites File:": _("Blocked Sites File:"),
            "Blocked URL File:": _("Blocked URL File:"),
            "Filter Mode:": _("Filter Mode:"),
            "Logger Configuration": _("Logger Configuration"),
            "Access Log:": _("Access Log:"),
            "Block Log:": _("Block Log:"),
            "SSL Inspection": _("SSL Inspection"),
            "Inspect CA Cert:": _("Inspect CA Cert:"),
            "Inspect CA Key:": _("Inspect CA Key:"),
            "Inspect certs folder:": _("Inspect certs folder:"),
            "Cancel inspect:": _("Cancel inspect:"),
            "Action": _("Action"),
            "Unblock": _("Unblock"),
            "Network error:": _("Network error"),
        }
        return render_template("index.html", translations=translations)

    @app.route("/api/status", methods=["GET"])
    @auth.login_required
    def monitoring():
        """
        Provides real-time monitoring information about the ProxyServer,
        including process, thread, and connection status.

        Returns:
            Response: JSON object containing monitoring data.
        """
        monitor = ProxyMonitor(proxy_server)
        return jsonify(monitor.get_process_info())

    @app.route("/api/settings", methods=["GET"])
    @auth.login_required
    def config():
        """
        Returns the current configuration of the ProxyServer.

        The configuration includes:
            - Host and port
            - Debug mode
            - 403 HTML page usage
            - Logger configuration (if present)
            - Filter configuration (if present)
            - SSL configuration (if present)
            - Flask monitoring port

        Returns:
            Response: JSON object containing configuration data.
        """
        config_data = {
            "host": proxy_server.host_port[0],
            "port": proxy_server.host_port[1],
            "debug": proxy_server.debug,
            "html_403": proxy_server.html_403,
            "logger_config": (
                proxy_server.logger_config.to_dict() if proxy_server.logger_config else None
            ),
            "filter_config": (
                proxy_server.filter_config.to_dict() if proxy_server.filter_config else None
            ),
            "ssl_config": (proxy_server.ssl_config.to_dict() if proxy_server.ssl_config else None),
            "flask_port": proxy_server.monitoring_config.flask_port,
        }
        return jsonify(config_data)

    @app.route("/api/filtering", methods=["GET", "POST", "DELETE"])
    @auth.login_required
    def blocked():
        """
        Manages the blocked sites and URLs list.

        GET:
            Reads and returns the current blocked domains and URLs from the corresponding files.
            Returns:
                Response: JSON object with 'blocked_sites' and 'blocked_url' lists.

        POST:
            Adds a new domain or URL to the blocked lists based on
                        'type' and 'value' from JSON input.
            Request JSON:
                {
                    "type": "domain" | "url",
                    "value": "<value_to_block>"
                }
            Returns:
                201: Successfully added.
                400: Invalid input.
                409: Value already blocked.

        DELETE:
            Removes a domain or URL from the blocked lists based on
                        'type' and 'value' from JSON input.
            Request JSON:
                {
                    "type": "domain" | "url",
                    "value": "<value_to_unblock>"
                }
            Returns:
                200: Successfully removed.
                400: Invalid input.
                404: Value not found.
                500: Server error.
        """
        if request.method == "GET":
            blocked_sites_content = ""
            blocked_url_content = ""

            with open(proxy_server.filter_config.blocked_sites, "r", encoding="utf-8") as f:
                blocked_sites_content = [line.strip() for line in f if line.strip()]
            with open(proxy_server.filter_config.blocked_url, "r", encoding="utf-8") as f:
                blocked_url_content = [line.strip() for line in f if line.strip()]

            blocked_data = {
                "blocked_sites": blocked_sites_content,
                "blocked_url": blocked_url_content,
            }
            return jsonify(blocked_data)

        elif request.method == "POST":
            data = request.get_json()
            typ = data.get("type")
            val = data.get("value", "").strip()
            if not val or typ not in ["domain", "url"]:
                return jsonify({"error": "Invalid input"}), 400

            filename = (
                proxy_server.filter_config.blocked_sites
                if typ == "domain"
                else proxy_server.filter_config.blocked_url
            )

            with open(filename, "r+", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                if val in lines:
                    return jsonify({"message": "Already blocked"}), 409
                lines.append(val)
                f.seek(0)
                f.truncate()
                f.write("\n".join(lines) + "\n")
            return jsonify({"message": "Added successfully"}), 201

        elif request.method == "DELETE":
            data = request.get_json()
            if not data or "type" not in data or "value" not in data:
                return (
                    jsonify({"error": "Missing 'type' or 'value' in request body"}),
                    400,
                )

            block_type = data["type"]
            value = data["value"].strip()

            if block_type == "domain":
                filepath = proxy_server.filter_config.blocked_sites
            elif block_type == "url":
                filepath = proxy_server.filter_config.blocked_url
            else:
                return (
                    jsonify({"error": "Invalid type, must be 'domain' or 'url'"}),
                    400,
                )

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]

                if value not in lines:
                    return (
                        jsonify({"error": f"{value} not found in {block_type} list"}),
                        404,
                    )

                lines = [line for line in lines if line != value]

                with open(filepath, "w", encoding="utf-8") as f:
                    for line in lines:
                        f.write(line + "\n")

                return (
                    jsonify({"message": f"{block_type} '{value}' removed successfully"}),
                    200,
                )
            except Exception as e:
                return jsonify({"error": f"Server error: {str(e)}"}), 500

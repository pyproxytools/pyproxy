"""
pyproxy.monitoring.routes.py

Defines and registers monitoring-related routes for the Flask application,
including endpoints for system information, configuration, and a secured
HTML-based index page.
"""

from flask import jsonify, render_template, request


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
        return render_template("index.html")

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

"""Base handler class for Vercel Python serverless functions."""

import json
from http.server import BaseHTTPRequestHandler


class VercelHandler(BaseHTTPRequestHandler):
    """
    Base class for all Vercel Python handlers.
    Provides JSON request/response helpers.
    """

    # ── Response helpers ──────────────────────────────────────────────

    def send_json(self, data, status=200):
        """Write a JSON response."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        """Write a JSON error response."""
        self.send_json({"error": message}, status)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, OPTIONS",
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization",
        )

    # ── Request helpers ───────────────────────────────────────────────

    def json_body(self):
        """Parse JSON request body. Returns {} on failure."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, ValueError):
            return {}

    def path_id(self):
        """Extract the last path segment (e.g. UUID) from the URL."""
        return self.path.rstrip("/").split("/")[-1]

    # ── CORS preflight ────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ── Logging (suppress Vercel noise) ──────────────────────────────

    def log_message(self, fmt, *args):  # noqa: D102
        pass

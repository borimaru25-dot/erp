"""Base handler class for Vercel Python serverless functions."""

import json
import os
from http.server import BaseHTTPRequestHandler
from jose import jwt, JWTError


class VercelHandler(BaseHTTPRequestHandler):
    """
    Base class for all Vercel Python handlers.
    Provides JSON request/response helpers and JWT auth.
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

    # ── Auth helper ───────────────────────────────────────────────────

    def get_user(self):
        """
        Verify Bearer JWT and return payload dict.
        Returns None and sends 401 if invalid.
        """
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self.send_error_json("Unauthorized", 401)
            return None

        token = auth[7:]
        secret = os.environ.get("JWT_SECRET", "")
        try:
            return jwt.decode(token, secret, algorithms=["HS256"])
        except JWTError:
            self.send_error_json("Invalid token", 401)
            return None

    # ── Logging (suppress Vercel noise) ──────────────────────────────

    def log_message(self, fmt, *args):  # noqa: D102
        pass

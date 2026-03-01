"""Common JSON response helpers for Vercel serverless functions."""

import json


def json_response(data, status=200):
    """Return a JSON response dict for Vercel."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(data, ensure_ascii=False),
    }


def json_error(message, status=400):
    """Return a JSON error response."""
    return json_response({"error": message}, status)


def handle_cors(request):
    """Handle CORS preflight requests."""
    if request.method == "OPTIONS":
        return json_response({}, 204)
    return None

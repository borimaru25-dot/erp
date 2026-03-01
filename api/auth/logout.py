"""POST /api/auth/logout — Sign out user."""

from api._lib.response import json_response, json_error, handle_cors


def handler(request):
    cors = handle_cors(request)
    if cors:
        return cors

    if request.method != "POST":
        return json_error("Method not allowed", 405)

    return json_response({"message": "Logged out successfully"})

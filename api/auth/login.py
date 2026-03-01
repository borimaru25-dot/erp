"""POST /api/auth/login — Authenticate user via Supabase Auth."""

import json
from api._lib.response import json_response, json_error, handle_cors
from api._lib.supabase_client import get_supabase


def handler(request):
    cors = handle_cors(request)
    if cors:
        return cors

    if request.method != "POST":
        return json_error("Method not allowed", 405)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return json_error("Invalid JSON body")

    email = body.get("email", "")
    password = body.get("password", "")

    if not email or not password:
        return json_error("Email and password are required")

    try:
        supabase = get_supabase()
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        session = result.session
        return json_response({
            "token": session.access_token,
            "user": {
                "id": result.user.id,
                "email": result.user.email,
            },
        })
    except Exception as e:
        return json_error(f"Login failed: {str(e)}", 401)

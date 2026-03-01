"""JWT verification middleware decorator."""

import os
import functools
from jose import jwt, JWTError
from api._lib.response import json_error


def require_auth(handler_func):
    """Decorator that verifies JWT token from Authorization header."""

    @functools.wraps(handler_func)
    def wrapper(request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return json_error("Unauthorized", 401)

        token = auth_header[7:]
        secret = os.environ.get("JWT_SECRET", "")

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            request.user = payload
        except JWTError:
            return json_error("Invalid token", 401)

        return handler_func(request)

    return wrapper

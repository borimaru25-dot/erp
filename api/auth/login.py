"""POST /api/auth/login"""

from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase


class handler(VercelHandler):
    def do_POST(self):
        body = self.json_body()
        email = body.get("email", "")
        password = body.get("password", "")
        if not email or not password:
            return self.send_error_json("Email and password are required")
        try:
            sb = get_supabase()
            res = sb.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            self.send_json({
                "token": res.session.access_token,
                "user": {"id": res.user.id, "email": res.user.email},
            })
        except Exception as e:
            self.send_error_json(f"Login failed: {e}", 401)

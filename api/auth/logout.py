"""POST /api/auth/logout"""

from api._lib.vercel_handler import VercelHandler


class handler(VercelHandler):
    def do_POST(self):
        self.send_json({"message": "Logged out successfully"})

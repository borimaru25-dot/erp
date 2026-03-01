"""GET /api/files/final-list"""

from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase


class handler(VercelHandler):
    def do_GET(self):
        try:
            sb = get_supabase()
            result = (
                sb.table("file_management")
                .select("id, name, created_at, updated_at")
                .order("created_at", desc=True)
                .execute()
            )
            self.send_json({"files": result.data})
        except Exception as e:
            self.send_error_json(f"Failed to list files: {e}", 500)

"""GET / DELETE /api/files/final/{id}"""

from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase


class handler(VercelHandler):
    def do_GET(self):
        file_id = self.path_id()
        try:
            sb = get_supabase()
            result = (
                sb.table("file_contents")
                .select("row_index, data")
                .eq("file_id", file_id)
                .order("row_index")
                .execute()
            )
            rows_data = result.data
            if not rows_data:
                return self.send_error_json("File content not found", 404)
            headers = list(rows_data[0]["data"].keys())
            rows = [
                [rec["data"].get(h, "") for h in headers]
                for rec in rows_data
            ]
            self.send_json({"headers": headers, "rows": rows})
        except Exception as e:
            self.send_error_json(f"Failed to load file: {e}", 500)

    def do_DELETE(self):
        file_id = self.path_id()
        try:
            sb = get_supabase()
            result = (
                sb.table("file_management")
                .select("storage_path")
                .eq("id", file_id)
                .single()
                .execute()
            )
            rec = result.data
            if rec and rec.get("storage_path"):
                sb.storage.from_("files").remove([rec["storage_path"]])
            sb.table("file_contents").delete().eq("file_id", file_id).execute()
            sb.table("file_management").delete().eq("id", file_id).execute()
            self.send_json({"message": "Final file deleted"})
        except Exception as e:
            self.send_error_json(f"Delete failed: {e}", 500)

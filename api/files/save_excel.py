"""POST /api/files/save-excel — Get signed download URL for final file."""

from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase


class handler(VercelHandler):
    def do_POST(self):
        body = self.json_body()
        file_id = body.get("file_id")
        if not file_id:
            return self.send_error_json("file_id is required")

        try:
            sb = get_supabase()
            rec = (
                sb.table("file_management")
                .select("name, storage_path")
                .eq("id", file_id).single().execute()
            ).data
            if not rec:
                return self.send_error_json("File not found", 404)

            signed = sb.storage.from_("files").create_signed_url(
                rec["storage_path"], 3600
            )
            self.send_json({
                "download_url": signed.get("signedURL", ""),
                "filename": rec["name"],
            })
        except Exception as e:
            self.send_error_json(f"Save failed: {e}", 500)

"""GET /api/files/temp-list — List all temp-stored files."""

from api._lib.response import json_response, json_error, handle_cors
from api._lib.supabase_client import get_supabase


def handler(request):
    cors = handle_cors(request)
    if cors:
        return cors

    if request.method != "GET":
        return json_error("Method not allowed", 405)

    try:
        supabase = get_supabase()
        result = (
            supabase.table("temp_files")
            .select("id, name, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return json_response({"files": result.data})
    except Exception as e:
        return json_error(f"Failed to list files: {str(e)}", 500)

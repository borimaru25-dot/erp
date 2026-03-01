"""DELETE /api/files/temp/{id} — Delete a temp file."""

from api._lib.response import json_response, json_error, handle_cors
from api._lib.supabase_client import get_supabase


def handler(request):
    cors = handle_cors(request)
    if cors:
        return cors

    if request.method != "DELETE":
        return json_error("Method not allowed", 405)

    path = request.url.split("/")
    file_id = path[-1] if path else None

    if not file_id:
        return json_error("File ID is required")

    try:
        supabase = get_supabase()

        # Get file record to find storage path
        result = (
            supabase.table("temp_files")
            .select("storage_path")
            .eq("id", file_id)
            .single()
            .execute()
        )
        file_record = result.data

        if file_record and file_record.get("storage_path"):
            # Delete from storage
            supabase.storage.from_("files").remove(
                [file_record["storage_path"]]
            )

        # Delete record from DB
        supabase.table("temp_files").delete().eq("id", file_id).execute()

        return json_response({"message": "File deleted"})
    except Exception as e:
        return json_error(f"Delete failed: {str(e)}", 500)

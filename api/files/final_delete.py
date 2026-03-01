"""DELETE /api/files/final/{id} — Delete a final version file."""

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

        # Get file record
        result = (
            supabase.table("file_management")
            .select("storage_path")
            .eq("id", file_id)
            .single()
            .execute()
        )
        file_record = result.data

        if file_record and file_record.get("storage_path"):
            supabase.storage.from_("files").remove(
                [file_record["storage_path"]]
            )

        # Delete contents
        supabase.table("file_contents").delete().eq(
            "file_id", file_id
        ).execute()

        # Delete management record
        supabase.table("file_management").delete().eq(
            "id", file_id
        ).execute()

        return json_response({"message": "Final file deleted"})
    except Exception as e:
        return json_error(f"Delete failed: {str(e)}", 500)

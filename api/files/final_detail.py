"""GET/DELETE /api/files/final/{id} — Get or delete final file."""

from api._lib.response import json_response, json_error, handle_cors
from api._lib.supabase_client import get_supabase


def handler(request):
    cors = handle_cors(request)
    if cors:
        return cors

    path = request.url.split("/")
    file_id = path[-1] if path else None

    if not file_id:
        return json_error("File ID is required")

    if request.method == "DELETE":
        return handle_delete(file_id)
    if request.method != "GET":
        return json_error("Method not allowed", 405)

    try:
        supabase = get_supabase()

        # Get file contents from file_contents table
        result = (
            supabase.table("file_contents")
            .select("row_index, data")
            .eq("file_id", file_id)
            .order("row_index")
            .execute()
        )

        rows_data = result.data
        if not rows_data:
            return json_error("File content not found", 404)

        # Reconstruct headers and rows from stored data
        headers = list(rows_data[0]["data"].keys()) if rows_data else []
        rows = []
        for record in rows_data:
            row = [record["data"].get(h, "") for h in headers]
            rows.append(row)

        return json_response({"headers": headers, "rows": rows})
    except Exception as e:
        return json_error(f"Failed to load file: {str(e)}", 500)


def handle_delete(file_id):
    """Delete a final file, its contents, and storage."""
    try:
        supabase = get_supabase()
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
        supabase.table("file_contents").delete().eq(
            "file_id", file_id
        ).execute()
        supabase.table("file_management").delete().eq(
            "id", file_id
        ).execute()
        return json_response({"message": "Final file deleted"})
    except Exception as e:
        return json_error(f"Delete failed: {str(e)}", 500)
